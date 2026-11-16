# Database seed command

Run from the repository root:

```sh
./seed --dry-run
./seed
```

The command reads `importfiles/assets.json` and `importfiles/items.json`, then
applies missing asset classes, items and assets to SQL Server through the
Compose `db` container. It uses the Kanoa table names, insert fields, hierarchy
procedures and SYSTEM audit user from the installed Kanoa module. Existing
records are matched by their full paths and skipped, so rerunning the command
does not duplicate them. The export's numeric IDs are deliberately ignored;
the destination gateway resolves its own parent records and asset types.

Direct database writes bypass `system.kanoa` method validation and any other
side effects outside the database. This seeder is limited to the asset and item
fields present in these exports; it does not import asset rates, states,
attributes or item attributes.
