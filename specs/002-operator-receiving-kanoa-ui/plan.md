# Implementation Plan: Kanoa UI Alignment for Operator Receiving

**Branch**: `002-operator-receiving-kanoa-ui` | **Date**: 2026-11-17 | **Spec**: [spec.md](spec.md)

**Input**: Feature specification from `specs/002-operator-receiving-kanoa-ui/spec.md`

## Summary

Host all three operator receiving screens in the standard Kanoa application shell and rebuild their
presentation from Kanoa's existing UI building blocks, without changing receiving behavior. The
change is deliberately narrow: add the standard header/navigation/options docks to the `/receiving`
Perspective page, keep the existing in-flow view navigation so every step stays on that docked page,
replace screen-specific controls and styles with established Kanoa templates, style classes, tables,
and feedback patterns, and verify the result in the supported themes and at a constrained width.

The receiving business logic and Kanoa API calls from `001-operator-receiving` remain unchanged. The
only scripts expected to change are view-level event scripts for feedback calls and navigation
consistency; all data reads and writes still go through the existing shared receiving script module.

## Technical Context

**Language/Version**: Ignition 8.3.10 Perspective view exports (JSON resources); Jython 2.7 for any
Perspective event script changes. No new Gateway script language or runtime.

**Primary Dependencies**: KanoaMES 1.15.11; `kanoaAPP` Kanoa template views and style classes
(`kanoa/core/templates/*`, `kanoa/font/*`, `kanoa/button/*`, `kanoa/container`, `kanoa/border`);
Kanoa dock views (`kanoa/core/docks/header/header`, `kanoa/core/docks/navigation/navigation`,
`kanoa/core/docks/options`); `system.kanoa.toast.show` for feedback; the existing
`KANOA_SCRIPTS/.../ops/receiving` script package for all MES operations.

**Storage**: No new tables or schema changes. The only persisted changes are the version-controlled
`kanoaMES` page-config and view JSON exports plus Kanoa Navigation configuration, which is
database-backed application configuration (export procedure still to be recorded, as in the 001
feature).

**Testing**: Manual acceptance against the running local Gateway. Structural JSON checks on changed
exports, visual comparison with a reference Kanoa screen, dock/navigation checks, theme checks,
constrained-width checks, and a rerun of the 001 receiving acceptance scenarios to prove no
functional regression.

**Target Platform**: Browser-based Ignition Perspective client for the Training Plant local Gateway
(`http://localhost:8088` or the configured Traefik host).

**Project Type**: Internal MES operator UI alignment (Perspective views, page configuration, and
Kanoa application navigation configuration).

**Performance Goals**: No new throughput target. An operator must still complete a standard receipt
in under 2 minutes (SC-001 of the 001 feature), and must be able to enter and leave the receiving
screens via the sidebar without address entry.

**Constraints**: Do not modify vendor-managed `kanoaAPP`. Keep all MES data access in the existing
`system.kanoa.*` receiving scripts. Do not change receiving validation, idempotency, or transfer
recovery rules. Do not hard-code colors or duplicate Kanoa components locally. Keep marquee pages
undocked. All runtime artifacts changed by this feature must remain reproducible from the repository,
except Kanoa Navigation records, whose export/reproduction must be explicitly documented.

**Scale/Scope**: Three receiving views (`receivingOrdersSchedule`, `receiveMaterial`,
`pendingTransfers`), one docked Perspective page (`/receiving`), and the existing navigation entries
for those views. Training Plant scope remains two receiving trucks and three bulk-storage tanks.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

### Initial Gate

- **I. Version-Controlled Gateway State — PASS WITH DEPLOYMENT GATE**: Page-config and view changes
  are committed under `services/ignition/projects/kanoaMES/`. Navigation registration is stored in
  Kanoa application configuration rather than a checked-in file; the exact Gateway export/backup
  artifact must be recorded in the implementation evidence, matching the 001 feature. No image,
  module, or database configuration changes.
- **II. Respect Ignition Project Boundaries — PASS**: All edits are in the runnable `kanoaMES`
  project. No `kanoaAPP` edits, no duplicated inherited views, and no vendor module changes. If a
  component gap appears, the reusable addition goes in `KANOA_SCRIPTS` Perspective views, which are
  inherited by `kanoaMES` through `kanoaAPP`.
- **III. Jython 2.7 and Ignition API Compatibility — PASS**: Only small Perspective event scripts
  are expected, using tabs, lowerCamelCase functions, and documented `system.perspective` /
  `system.kanoa.toast` calls compatible with Jython 2.7.
- **IV. API-First, Idempotent Data Operations — PASS (NO DATA ACCESS CHANGE)**: This feature changes
  presentation and page hosting only. All existing receipt/transfer reads and writes remain in the
  shared receiving script module; no direct SQL, no new tables, and no retry logic changes.
- **V. Verifiable, Observable Changes — PASS**: `quickstart.md` defines manual Gateway checks, a
  component/theme/width audit, and a rerun of the 001 acceptance scenarios. Any new scripts follow
  the existing logging and result conventions; no silent failures.

No constitution violation is proposed. The navigation export gap is a verification gate, not an
exception.

## Research Summary

See [research.md](research.md) for the full findings and alternatives. Principal decisions:

- Add the standard dock set explicitly to `/receiving`; keep in-flow navigation on
  `navigate(view=...)`, which does not change the page and therefore keeps the docks. Do not use
  `sharedDocks` because the marquee pages must remain full-screen.
- Reuse Kanoa templates where one exists (`numberInput`, `assetDropdownSelector`,
  `dateRangeSelectorCompact`, `progressBar`, `messagePopup`, `confirm`). Follow Kanoa's own
  primitive-plus-style-class pattern for labels, text fields, tables, and buttons.
- Replace the invalid `kanoa/button/primary` class with the installed `kanoa/button/filled` class,
  and use Kanoa heading classes for screen titles.
- Use `system.kanoa.toast.show` for transient feedback and Kanoa popup templates for blocking
  messages/confirmations, matching other Kanoa screens.
- Register receiving views through Kanoa Configuration → Application → Navigation; treat
  reproducibility of those records as a deployment gate.

## Constitution Check (Post-Design)

- **I. Version-Controlled Gateway State — PASS WITH DEPLOYMENT GATE**: Designed file changes are
  limited to `page-config/config.json`, three `view.json` files, and this feature's documentation.
  Navigation records remain a Kanoa configuration artifact; the quickstart requires recording the
  export/backup proof before release.
- **II. Respect Ignition Project Boundaries — PASS**: The design reuses inherited Kanoa views and
  classes without editing `kanoaAPP`, and requires any new shared view to live in `KANOA_SCRIPTS`.
- **III. Jython 2.7 and Ignition API Compatibility — PASS**: Event scripts stay minimal and use
  only documented APIs. No Python 3 syntax or unsupported libraries.
- **IV. API-First, Idempotent Data Operations — PASS**: No MES data operation is added or moved;
  [contracts/component-contracts.md](contracts/component-contracts.md) binds reused controls to the
  same view custom state that feeds the existing receiving scripts.
- **V. Verifiable, Observable Changes — PASS**: [quickstart.md](quickstart.md) gives explicit
  checks for shell, components, themes, width, navigation, and regression of 001 scenarios.

## Phase 0 — Outline & Research

All technical unknowns were resolved with repository evidence; the specification has no open
clarifications. Research tasks covered: shell attachment, navigation registration and active highlighting,
component reuse mapping, feedback patterns, invalid style classes, theme/responsive behavior, and
project boundaries. Output: [research.md](research.md).

## Phase 1 — Design & Contracts

- [data-model.md](data-model.md) describes the UI state and entities the screens present, including
  component bindings, presentation states, and validation rules.
- `contracts/` defines the page/navigation contract and the reusable component/feedback contracts.
- [quickstart.md](quickstart.md) is the validation guide for the running Gateway.

## Project Structure

### Documentation (this feature)

```text
specs/002-operator-receiving-kanoa-ui/
├── plan.md                       # This file (/speckit.plan output)
├── research.md                   # Phase 0 output
├── data-model.md                 # Phase 1 output
├── quickstart.md                 # Phase 1 output
├── contracts/
│   ├── page-and-navigation.md    # Page config + Kanoa Navigation contract
│   └── component-contracts.md    # Reused Kanoa component and feedback contracts
├── checklists/requirements.md    # Specification quality checklist
└── tasks.md                      # Later output of /speckit.tasks (not created here)
```

### Source Code (repository root)

```text
services/ignition/projects/
├── kanoaMES/
│   ├── com.inductiveautomation.perspective/
│   │   ├── page-config/
│   │   │   ├── config.json                 # Add docks to /receiving
│   │   │   └── resource.json               # Unchanged unless Designer re-export requires it
│   │   └── views/training/
│   │       ├── receivingOrdersSchedule/
│   │       │   ├── view.json               # Kanoa date range, table, labels, actions
│   │       │   └── resource.json
│   │       ├── receiveMaterial/
│   │       │   ├── view.json               # Kanoa read-only values, number input, selectors
│   │       │   └── resource.json
│   │       └── pendingTransfers/
│   │           ├── view.json               # Kanoa table, tank selector, actions
│   │           └── resource.json
│   └── ignition/                           # Unchanged by this feature
├── KANOA_SCRIPTS/
│   ├── com.inductiveautomation.perspective/views/   # Only if a shared component gap is found
│   └── ignition/script-python/kanoaScripts/custom/ops/receiving/
│                                                   # Existing 001 logic; unchanged
└── kanoaAPP/                                        # Vendor-managed; read-only reference
```

**Structure Decision**: Keep all feature edits in `kanoaMES`, because the receiving views and the
`/receiving` page already live there. Use inherited resources from `kanoaAPP` for Kanoa templates,
docks, themes, and style classes. Add shared reusable views only to `KANOA_SCRIPTS` if an audit
finds a genuine gap, and only when the same view can be used by more than one receiving screen.
Do not introduce a new project, a local component library, or a separate navigation mechanism.

## Complexity Tracking

No constitution violations are proposed; no exceptions table is required.

The Kanoa Navigation export mechanism remains a deployment verification gate inherited from
`001-operator-receiving`. It is handled by documenting the Gateway export/backup evidence in
`quickstart.md`, not by bypassing the governance rule.
