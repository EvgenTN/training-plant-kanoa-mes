# Implementation Plan: Receive Material Work Order Editor Refactor

**Branch**: `003-receive-material-woeditor-ui` | **Date**: 2026-11-18 | **Spec**: [spec.md](spec.md)

**Input**: Feature specification from `specs/003-receive-material-woeditor-ui/spec.md`

## Summary

Rebuild the `training/receiveMaterial` Perspective screen so it uses the layout, component
primitives, style classes, and selector pattern of the Kanoa work order editor
(`kanoa/mes/workOrders/woEditor`) while preserving every receiving rule from feature 001 and the
Kanoa shell alignment from feature 002.

The screen will show six order fields — order number, title, target quantity, schedule date, status,
and notes — as non-editable Kanoa-styled values; replace the current asset dropdowns with the
`kanoa/core/templates/selectors/tree/selector` used by `woEditor`, scoped to enabled Storage
Locations under `Training Plant\Receiving` (truck) and `Training Plant\Bulk Storage` (tank); use a
native numeric entry field for actual quantity defaulting to the outstanding kg quantity; and expose
only Confirm and Back. Pending-transfer recovery stays on the existing Pending Transfers screen.

The change is confined to the `kanoaMES` view export, the schedule screen's navigation parameters,
and feature documentation. No new custom component, method, table, or vendor resource is introduced.
The schedule date and order notes come from the schedule row the operator already selected (the
schedule table is fed by `system.kanoa.order.getProductionOrders` and exposes `startDate` and `note`);
when the screen is opened without those parameters, notes fall back to a native
`system.kanoa.order.getProductionOrders` read. The shared receiving script module is not extended.

## Technical Context

**Language/Version**: Ignition 8.3.10 Perspective view exports (JSON resources); Jython 2.7 for
inline Perspective event scripts and binding transforms. No standalone Python is added.

**Primary Dependencies**: KanoaMES 1.15.11; inherited `kanoaAPP` resources
(`kanoa/core/templates/selectors/tree/selector`, `kanoa/core/templates/inputs/confirm`,
`kanoa/core/templates/displays/messagePopup`, `kanoa/font/*`, `kanoa/button/*`, `kanoa/container`,
`kanoa/border`); native Perspective components (`ia.display.label`, `ia.input.numeric-entry-field`,
`ia.input.button`); `system.kanoa.asset.getAssets`, `system.kanoa.order.getProductionOrders`,
`system.kanoa.utilities.getFieldValue`, `system.kanoa.toast.show`; the existing
`KANOA_SCRIPTS/.../ops/receiving` package (`getReceivingOrder`, `getReceivingAssets`,
`getReceivedQtyForOrder`, `receiveOrder`) and the existing `confirmReceiveOrder` popup handler.

**Storage**: No new tables or schema changes. The persisted changes are the version-controlled
`kanoaMES` Perspective view exports for `training/receiveMaterial` and
`training/receivingOrdersSchedule`.

**Testing**: Manual acceptance against the running local Gateway, plus structural JSON checks on the
changed view exports. Validation covers: six read-only fields against canonical order values;
selector scope and selection behavior; default-quantity cases (new order vs. partial receipt);
invalid quantity/asset rejection; duplicate-submit prevention; Back with no writes; transfer-failure
messaging and hand-off to Pending Transfers; theme and constrained-width rendering; and a rerun of
the feature 001 acceptance scenarios. See [quickstart.md](quickstart.md).

**Target Platform**: Browser-based Ignition Perspective client for the local Training Plant Gateway
(`http://localhost:8088` or the configured Traefik host).

**Project Type**: Internal MES operator UI refactor (Perspective view JSON plus minimal inline event
scripts).

**Performance Goals**: No new throughput target. The screen must load the order, both asset
hierarchies, and receipt history once on open, and an operator must complete a standard receipt in
under 2 minutes (SC-001).

**Constraints**: Do not modify vendor-managed `kanoaAPP`. Do not add custom components or methods.
Do not change receiving validation, idempotency, unit handling, or transfer recovery rules. Do not
duplicate inherited Kanoa views locally. Actual quantity remains kg. The Pending Transfers screen is
the only recovery surface.

**Scale/Scope**: One receiving view (`training/receiveMaterial`) and one navigation script change in
`training/receivingOrdersSchedule`. Training Plant scope remains two receiving trucks and three
bulk-storage tanks.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

### Initial Gate

- **I. Version-Controlled Gateway State — PASS**: All changes are committed Perspective JSON exports
  under `services/ignition/projects/kanoaMES/`. No image, module, database, or generated runtime
  state changes.
- **II. Respect Ignition Project Boundaries — PASS**: All edits are in the runnable `kanoaMES`
  project. `kanoaAPP` templates are referenced in place and not edited or copied. No
  `KANOA_SCRIPTS` change is planned, so the inherited script module is untouched.
- **III. Jython 2.7 and Ignition API Compatibility — PASS**: Inline scripts use tab indentation,
  Jython-safe syntax, and documented `system.perspective`, `system.kanoa.*`, and dataset APIs. No
  Python 3 syntax, `pip`, or third-party libraries.
- **IV. API-First, Idempotent Data Operations — PASS (NO DATA OPERATION CHANGE)**: All receipt and
  transfer writes continue through `kanoaScripts.custom.ops.receiving.receiveOrder`, which already
  validates, locks per order, and preserves idempotency. Order notes and asset hierarchies are read
  with native `system.kanoa.*` APIs. No direct SQL and no new writes.
- **V. Verifiable, Observable Changes — PASS**: [quickstart.md](quickstart.md) defines Gateway checks
  for every acceptance scenario, structural JSON validation, and a feature 001 regression pass. No
  new logging is required because no new mutating code is added.
- **VI. Kanoa-First: No Custom Components or Methods — PASS**: No new Perspective view, template,
  Vision window, script function, module, helper, or wrapper is introduced.
  - Read-only values use the native `ia.display.label` primitive with existing `kanoa/font/*`
    classes; no custom display view is created.
  - The asset selector is the existing inherited
    `kanoa/core/templates/selectors/tree/selector`, the same template `woEditor` embeds, fed by the
    native `system.kanoa.asset.getAssets` API.
  - The actual-quantity control is the native `ia.input.numeric-entry-field`, the same primitive
    `woEditor` uses.
  - Notes and schedule date come from the selected schedule row (`note`, `startDate`), with a native
    `system.kanoa.order.getProductionOrders` fallback for notes when the screen is opened directly;
    the existing `_orderSummary` method in `KANOA_SCRIPTS` is deliberately left unchanged.
  - Inline scripts are limited to bindings, selection hand-off, navigation, and calls to existing
    Kanoa APIs. No reusable business logic is placed in event scripts.
  - If implementation discovers that native capability cannot satisfy a requirement, work stops and
    an approval request is recorded in this plan before any custom component or method is written.

No constitution violation is proposed, so Complexity Tracking is empty.

## Project Structure

### Documentation (this feature)

```text
specs/003-receive-material-woeditor-ui/
├── plan.md              # This file (/speckit.plan command output)
├── research.md          # Phase 0 output (/speckit.plan command)
├── data-model.md        # Phase 1 output (/speckit.plan command)
├── quickstart.md        # Phase 1 output (/speckit.plan command)
├── contracts/           # Phase 1 output (/speckit.plan command)
│   ├── component-contracts.md
│   └── behavior-preservation.md
└── tasks.md             # Phase 2 output (/speckit.tasks command - NOT created by /speckit.plan)
```

### Source Code (repository root)

```text
services/ignition/projects/
├── kanoaMES/com.inductiveautomation.perspective/views/training/
│   ├── receiveMaterial/view.json          # Refactored screen
│   └── receivingOrdersSchedule/view.json  # Pass schedule date in navigation params
├── kanoaAPP/com.inductiveautomation.perspective/views/kanoa/
│   ├── mes/workOrders/woEditor/view.json  # Visual/interaction reference (read-only)
│   └── core/templates/                    # Reused templates (read-only)
│       ├── selectors/tree/selector/
│       ├── inputs/confirm/
│       └── displays/messagePopup/
└── KANOA_SCRIPTS/ignition/script-python/kanoaScripts/custom/ops/receiving/
    └── code.py                            # Existing receiving APIs (unchanged)
```

**Structure Decision**: This is an Ignition Perspective feature in the runnable `kanoaMES` project.
The only edited runtime resources are `training/receiveMaterial/view.json` and the navigation script
in `training/receivingOrdersSchedule/view.json`. All reusable views, styles, and receiving APIs are
inherited from `kanoaAPP` and `KANOA_SCRIPTS` and remain unmodified.

## Complexity Tracking

> **Fill ONLY if Constitution Check has violations that must be justified**

No violations. No custom component or method is proposed, so no approval entry is required.

## Constitution Check (Post-Design)

Re-evaluated after [research.md](research.md), [data-model.md](data-model.md),
[contracts/](contracts/), and [quickstart.md](quickstart.md) were produced.

- **I. Version-Controlled Gateway State — PASS**: Design edits remain two committed Perspective view
  files under `kanoaMES`. No navigation, module, database, or environment change is part of this
  feature (navigation was established by feature 002).
- **II. Respect Ignition Project Boundaries — PASS**: All design references to `kanoaAPP` and
  `KANOA_SCRIPTS` are read-only. The behavior-preservation contract explicitly gates the diff on
  proving neither project changed.
- **III. Jython 2.7 and Ignition API Compatibility — PASS**: The designed inline scripts use only
  `system.perspective`, `system.kanoa.*`, and dataset/JSON access in Jython-safe form. No new module
  or Python 3 syntax is introduced.
- **IV. API-First, Idempotent Data Operations — PASS**: The design delegates every read and write to
  existing native or receiving APIs. The only additional read is the native
  `system.kanoa.order.getProductionOrders` fallback for notes on direct open; the normal path reuses
  the schedule row. No SQL, schema, or write path is added.
- **V. Verifiable, Observable Changes — PASS**: [quickstart.md](quickstart.md) defines structural,
  functional, regression, theme, and width checks, and requires recording proof that vendor/shared
  projects were untouched.
- **VI. Kanoa-First: No Custom Components or Methods — PASS**: The design uses
  `kanoa/core/templates/selectors/tree/selector`, `kanoa/core/templates/inputs/confirm`,
  `kanoa/core/templates/displays/messagePopup`, `ia.display.label`,
  `ia.input.numeric-entry-field`, and `ia.input.button` with existing Kanoa style classes. It creates
  no view, template, function, module, helper, or wrapper, and it deliberately leaves
  `_orderSummary` and every other shared receiving method unchanged. The approval gate remains in
  force if implementation finds a native gap.

No new violation surfaced during design; Complexity Tracking remains empty.
