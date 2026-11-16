#!/usr/bin/env python3
"""Idempotently seed Kanoa assets, item classes and items into SQL Server."""

import argparse
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys


ROOT = Path(__file__).resolve().parent.parent


def sql_string(value):
    if value is None:
        return "NULL"
    if isinstance(value, bool):
        return "1" if value else "0"
    if isinstance(value, (int, float)):
        return str(value)
    return "N'{}'".format(str(value).replace("'", "''"))


def build_sql(assets_export, items_export, database):
    if not re.fullmatch(r"[A-Za-z0-9_]+", database):
        raise ValueError("DB_NAME may contain only letters, digits and underscores")

    assets = assets_export["data"]["assets"]
    exported_classes = items_export["data"]["itemClasses"]
    classes_by_path = {row["path"]: row for row in exported_classes}
    # Some Kanoa exports omit ancestors that were already present in their
    # source database. Recreate those path segments as plain item classes.
    for row in list(exported_classes):
        parts = row["path"].split("\\")
        for index in range(1, len(parts)):
            path = "\\".join(parts[:index])
            if path not in classes_by_path:
                classes_by_path[path] = {
                    "path": path,
                    "itemClassName": parts[index - 1],
                    "itemClassDescription": None,
                    "itemClassColor": None,
                    "enabled": True,
                }
    classes = list(classes_by_path.values())
    items = items_export["data"]["items"]
    out = [
        "SET NOCOUNT ON;",
        "SET XACT_ABORT ON;",
        "USE [{}];".format(database),
        "BEGIN TRY",
        "  BEGIN TRANSACTION;",
        "  DECLARE @seedUserId int, @adminRoleId int, @id int, @parentId int, @typeId int;",
        "  SELECT @seedUserId = userId FROM sec.[user] WHERE userName = N'SYSTEM';",
        "  IF @seedUserId IS NULL THROW 51000, 'Kanoa SYSTEM user was not found in sec.user', 1;",
        "  SELECT @adminRoleId = roleId FROM sec.[role] WHERE roleName = N'Administrator';",
        "  IF @adminRoleId IS NULL THROW 51001, 'Kanoa Administrator role was not found', 1;",
    ]

    for row in sorted(classes, key=lambda x: (x["path"].count("\\"), x["path"].lower())):
        path = row["path"]
        parent_path = path.rsplit("\\", 1)[0] if "\\" in path else None
        out += [
            "  SET @id = NULL;",
            "  SELECT TOP (1) @id = itemClassId FROM mes.vwItemClass WHERE [path] = {};".format(sql_string(path)),
            "  IF @id IS NULL",
            "  BEGIN",
        ]
        if parent_path is None:
            out.append("    SET @parentId = NULL;")
        else:
            out += [
                "    SET @parentId = NULL;",
                "    SELECT TOP (1) @parentId = itemClassId FROM mes.vwItemClass WHERE [path] = {};".format(sql_string(parent_path)),
                "    IF @parentId IS NULL THROW 51002, 'Missing item class parent: {}', 1;".format(path.replace("'", "''")),
            ]
        out += [
            "    INSERT INTO mes.[itemClass] (itemClassName, parentId, itemClassDescription, itemClassColor, enabled, createdBy, createdDate)",
            "    VALUES ({}, @parentId, {}, {}, {}, @seedUserId, GETDATE());".format(
                sql_string(row["itemClassName"]), sql_string(row.get("itemClassDescription")),
                sql_string(row.get("itemClassColor")), sql_string(row.get("enabled", True))),
            "    EXEC mes.spPopulateItemClassHierarchy;",
            "    SET @id = CONVERT(int, SCOPE_IDENTITY());",
            "    PRINT N'Added item class: {}';".format(path.replace("'", "''")),
            "  END ELSE PRINT N'Exists, skipped item class: {}';".format(path.replace("'", "''")),
        ]

    for row in items:
        item_path = row.get("itemPath") or row["path"]
        class_path = row.get("itemClassPath")
        out += [
            "  IF NOT EXISTS (SELECT 1 FROM mes.vwItem WHERE [path] = {})".format(sql_string(item_path)),
            "  BEGIN",
        ]
        if class_path:
            out += [
                "    SET @parentId = NULL;",
                "    SELECT TOP (1) @parentId = itemClassId FROM mes.vwItemClass WHERE [path] = {};".format(sql_string(class_path)),
                "    IF @parentId IS NULL THROW 51003, 'Missing item class: {}', 1;".format(class_path.replace("'", "''")),
            ]
        else:
            out.append("    SET @parentId = NULL;")
        out += [
            "    INSERT INTO mes.[item] (itemName, itemDescription, itemClassId, itemColor, enabled, createdBy, createdDate)",
            "    VALUES ({}, {}, @parentId, {}, {}, @seedUserId, GETDATE());".format(
                sql_string(row["itemName"]), sql_string(row.get("itemDescription")),
                sql_string(row.get("itemColor")), sql_string(row.get("enabled", True))),
            "    PRINT N'Added item: {}';".format(item_path.replace("'", "''")),
            "  END ELSE PRINT N'Exists, skipped item: {}';".format(item_path.replace("'", "''")),
        ]

    for row in sorted(assets, key=lambda x: (x["assetPath"].count("\\"), x["assetPath"].lower())):
        path = row["assetPath"]
        parent_path = path.rsplit("\\", 1)[0] if "\\" in path else None
        out += [
            "  SET @id = NULL;",
            "  SELECT TOP (1) @id = assetId FROM mes.vwAsset WHERE assetPath = {};".format(sql_string(path)),
            "  IF @id IS NULL",
            "  BEGIN",
        ]
        if parent_path is None:
            out.append("    SET @parentId = NULL;")
        else:
            out += [
                "    SET @parentId = NULL;",
                "    SELECT TOP (1) @parentId = assetId FROM mes.vwAsset WHERE assetPath = {};".format(sql_string(parent_path)),
                "    IF @parentId IS NULL THROW 51004, 'Missing asset parent: {}', 1;".format(parent_path.replace("'", "''")),
            ]
        out += [
            "    SET @typeId = NULL;",
            "    SELECT TOP (1) @typeId = assetTypeId FROM mes.vwAssetType WHERE assetTypePath = {};".format(sql_string(row["assetTypePath"])),
            "    IF @typeId IS NULL THROW 51005, 'Missing asset type: {}', 1;".format(row["assetTypePath"].replace("'", "''")),
            "    INSERT INTO mes.[asset] (assetName, parentId, assetTypeId, assetGroupId, processTypeId, oeeEnabled, timezone, sortOrder, enabled, createdBy, createdDate)",
            "    VALUES ({}, @parentId, @typeId, NULL, {}, {}, {}, {}, {}, @seedUserId, GETDATE());".format(
                sql_string(row["assetName"]), sql_string(row.get("processTypeId")),
                sql_string(row.get("oeeEnabled", False)), sql_string(row.get("timeZone") if parent_path is None else None),
                sql_string(row.get("sortOrder")), sql_string(row.get("enabled", True))),
            "    SET @id = CONVERT(int, SCOPE_IDENTITY());",
            "    EXEC mes.spPopulateAssetHierarchy;",
            "    IF NOT EXISTS (SELECT 1 FROM sec.vwUserAssetRole WHERE userId = @seedUserId AND roleId = @adminRoleId AND assetPath IS NOT NULL AND {} LIKE assetPath + N'%')".format(sql_string(path)),
            "      INSERT INTO sec.[userAssetRole] (roleId, userId, assetId, createdBy, createdDate) VALUES (@adminRoleId, @seedUserId, @id, @seedUserId, GETDATE());",
            "    PRINT N'Added asset: {}';".format(path.replace("'", "''")),
            "  END ELSE PRINT N'Exists, skipped asset: {}';".format(path.replace("'", "''")),
        ]

    out += [
        "  COMMIT TRANSACTION;",
        "  PRINT N'Seed completed.';",
        "END TRY",
        "BEGIN CATCH",
        "  IF @@TRANCOUNT > 0 ROLLBACK TRANSACTION;",
        "  THROW;",
        "END CATCH;",
    ]
    return "\n".join(out) + "\n"


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dry-run", action="store_true", help="print SQL without applying it")
    args = parser.parse_args()

    database = os.environ.get("DB_NAME", "kanoa")
    env_file = ROOT / ".env"
    if "DB_NAME" not in os.environ and env_file.exists():
        for line in env_file.read_text().splitlines():
            match = re.match(r"\s*DB_NAME\s*=\s*([^#\s]+)", line)
            if match:
                database = match.group(1).strip('"\'')

    assets = json.loads((ROOT / "importfiles/assets.json").read_text())
    items = json.loads((ROOT / "importfiles/items.json").read_text())
    if assets.get("exportType") != "assetInfo" or items.get("exportType") != "itemInfo":
        raise SystemExit("Unexpected Kanoa export type in importfiles")
    script = build_sql(assets, items, database)

    if args.dry_run:
        sys.stdout.write(script)
        return 0

    sqlcmd = 'exec /opt/mssql-tools18/bin/sqlcmd -C -S localhost -U sa -P "$SA_PASSWORD" -d master -b -i /dev/stdin -W'
    if os.environ.get("SEED_COMPOSE_COMMAND"):
        compose = os.environ["SEED_COMPOSE_COMMAND"].split()
    elif shutil.which("podman-compose"):
        compose = ["podman-compose"]
    elif shutil.which("podman"):
        compose = ["podman", "compose"]
    elif shutil.which("docker"):
        compose = ["docker", "compose"]
    else:
        print("Install Podman Compose (preferred) or Docker Compose to reach SQL Server.", file=sys.stderr)
        return 2
    command = compose + ["exec", "-T", "db", "bash", "-lc", sqlcmd]
    try:
        result = subprocess.run(command, input=script, text=True, check=False)
    except FileNotFoundError:
        print("Could not run %s; start the Compose stack and check its installation." % compose[0], file=sys.stderr)
        return 2
    return result.returncode


if __name__ == "__main__":
    sys.exit(main())
