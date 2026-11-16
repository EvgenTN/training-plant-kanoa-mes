# Implementation Plan: Operator Bulk Receiving

**Branch**: `001-operator-receiving` | **Date**: 2026-11-13 | **Spec**: [spec.md](spec.md)

**Input**: Feature specification from `specs/001-operator-receiving/spec.md`

## Summary

Provide an operator-focused receiving workflow that selects an eligible scheduled order, displays its canonical details read-only, accepts actual quantity and truck/tank selections, creates traceable Kanoa lot history, and lets operators recover a transfer that remains at a truck. Use the Kanoa MES APIs and the existing Ignition project boundaries. Build the order schedule and receiving views in the runnable `kanoaMES` project; keep reusable service logic in `KANOA_SCRIPTS`.

The selected quantity policy is partial receipts with no over-receipt tolerance. Recalculate prior Receive output events for the order immediately before posting and reject a quantity that would exceed the current remainder. This plan assumes the receive check-and-post path is serialized per order within the receiving application; confirm the guard on the pinned single-Gateway runtime before importing or activating the operator views. The current exports are draft resources only. If the guard cannot be guaranteed, fail closed and surface the concurrency limitation before release.

## Technical Context

**Language/Version**: Jython 2.7 for Ignition Gateway scripts; Ignition Perspective view resources use the exported Ignition JSON format.

**Primary Dependencies**: Ignition 8.3.10; KanoaMES 1.15.11; existing `system.kanoa.*` APIs; Perspective module.

**Storage**: Existing Kanoa-managed order, lot, operation, serial, asset, and item records in the `kanoa` database. No custom inventory tables or schema changes.

**Testing**: Manual acceptance against the running local Gateway and Kanoa MES. Verify first-run and retry outcomes, including history in Kanoa Lot Manager. Validate standalone script syntax with a Jython-compatible check if available; do not treat CPython parsing as sufficient for runtime correctness.

**Target Platform**: Browser-based Ignition Perspective operator application on the existing Training Plant local Gateway.

**Project Type**: Internal MES operator application with Perspective views and shared Gateway scripts.

**Performance Goals**: An operator completes a standard receipt in under 2 minutes after selecting an order. Schedule, asset, and pending-transfer lists must be usable for the Training Plant scope (2 trucks and 3 tanks); no broader throughput target is specified.

**Constraints**: Respect `KANOA_SCRIPTS`/`kanoaMES`/vendor-managed `kanoaAPP` boundaries. Use only documented Kanoa APIs for MES reads/writes. Use the authenticated Perspective user's Kanoa user ID. Keep receipt and transfer outcomes distinguishable because they are separate operations. Do not blindly retry a receipt with an uncertain result. Use only kg unless an order-unit conversion is verified.

**Scale/Scope**: Single Training Plant, scheduled orders, two configured Receiving truck Storage Locations and three Bulk Storage tank Storage Locations. Manual quantity entry only. ERP, supplier, automated scale, COA, and quality inspection workflows are out of scope.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

### Initial Gate

- **I. Version-Controlled Gateway State — PASS**: All new Perspective and script resources will be exported under the repository's Ignition project directories. Kanoa Navigation registration must be recorded as a deployment/configuration step and its reproducible export path confirmed during implementation.
- **II. Respect Ignition Project Boundaries — PASS**: Client scripts belong in `KANOA_SCRIPTS`; custom operator views belong in runnable `kanoaMES`; no `kanoaAPP` edits or duplicated inherited views.
- **III. Jython 2.7 and Ignition API Compatibility — PASS**: Gateway logic will use Jython 2.7-compatible syntax and Kanoa/Ignition APIs.
- **IV. API-First, Idempotent Data Operations — DESIGN GATE PENDING**: The draft uses Kanoa APIs, preflight validation, lot/order event lookup, and per-order serialization. Confirm safe handling of ambiguous writes and concurrent receipt submissions before importing or activating the views. No direct SQL or custom inventory tables.
- **V. Verifiable, Observable Changes — PASS**: Include manual Gateway acceptance scenarios, operation-level logs, actionable outcomes, and first-run/retry verification.

No constitution violation is proposed. The idempotency/concurrency gate is a required design condition, not an exception to the principle.

## Research Summary

See [research.md](research.md) for API and project-boundary findings. Main design choices:

- Use a dedicated Receiving Orders Schedule view because available Kanoa docs do not establish a supported selected-event action on the built-in Operations Schedule.
- Query schedule blocks for the selected window, then reload each selected order from canonical order data and filter to `Scheduled` or `In Progress`.
- Sum Kanoa `Receive` output lot events by work order for cumulative quantity; do not assume production `actualQty` represents raw-material receipts.
- Allocate a configured serial, then create the lot and its no-input/one-output Receive event together through `executeLotOperation`, using the new lot name and item/unit in the output event. The Kanoa API reference supports new lots in operation output events; verify this on the pinned release. This avoids the separate `addLot`-then-Receive partial-write window.
- Execute the transfer as a separate Transfer operation on the same lot. Build the pending-transfer list from current lot activity at Receiving trucks; this is current stock at trucks, not a native Kanoa pending-transfer status.
- On recovery after reopening, require the operator to select a destination tank again. The intended tank is not recorded by the receipt event; it only becomes part of lot history when the transfer succeeds.

## Constitution Check (Post-Design)

- **I. Version-Controlled Gateway State — PASS WITH DEPLOYMENT CHECK**: Project resource paths are defined below. Include navigation setup and its export/reproduction procedure in the implementation evidence.
- **II. Respect Ignition Project Boundaries — PASS**: No client-specific changes to `kanoaAPP`; shared Python in `KANOA_SCRIPTS`, views in `kanoaMES`.
- **III. Jython 2.7 and Ignition API Compatibility — PASS**: Service functions use compatible syntax, lowerCamelCase, tabs, and documented docstrings; use explicit Gateway execution scope.
- **IV. API-First, Idempotent Data Operations — DESIGN GATE PENDING**: Draft code validates canonical order/asset/config before mutation; serializes same-order submissions in the shared script module; and uses Kanoa event/activity history for retry/reconciliation. Confirm ambiguity handling on the pinned runtime before import/activation. Direct SQL and custom MES tables are excluded.
- **V. Verifiable, Observable Changes — PASS**: Runtime steps and expected outcomes are specified in [quickstart.md](quickstart.md). Named logger and identifiers required for mutations.

## Project Structure

### Documentation (this feature)

```text
specs/001-operator-receiving/
├── plan.md
├── research.md
├── data-model.md
├── quickstart.md
├── contracts/
│   └── receiving-application.md
└── tasks.md                 # Later output of $speckit-tasks
```

### Source Code (repository root)

```text
services/ignition/projects/
├── KANOA_SCRIPTS/
│   └── ignition/script-python/kanoaScripts/custom/ops/receiving/
│       ├── code.py
│       └── resource.json
└── kanoaMES/
    └── com.inductiveautomation.perspective/views/training/
        ├── receivingOrdersSchedule/
        │   ├── view.json
        │   └── resource.json
        ├── receiveMaterial/
        │   ├── view.json
        │   └── resource.json
        └── pendingTransfers/
            ├── view.json
            └── resource.json
```

**Structure Decision**: Kanoa's own custom lot-screen guide imports custom views into the runnable `kanoaMES` project and registers them through **Configuration → Application → Navigation**. The project constitution assigns shared/client-specific Gateway scripts to `KANOA_SCRIPTS`. Follow those established boundaries. Use Kanoa Navigation configuration for menu registration rather than inventing a parallel navigation system; confirm the project export/reproduction mechanism as part of release verification.

## Complexity Tracking

No constitution violations or additional projects are proposed. Same-order serialization is required to make cumulative quantity validation safe under simultaneous operator submissions; use the narrowest Gateway-scoped mechanism that can be proven on the pinned runtime. If Kanoa activity outside this receiving flow can create receipts concurrently and cannot be controlled, document and resolve that gap before claiming a global no-over-receipt guarantee.
