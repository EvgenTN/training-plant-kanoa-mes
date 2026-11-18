---
description: "Task list for the Receive Material work order editor refactor"
---

# Tasks: Receive Material Work Order Editor Refactor

**Input**: Design documents from `specs/003-receive-material-woeditor-ui/`

**Prerequisites**: `plan.md`, `spec.md`, `research.md`, `data-model.md`, `contracts/`, `quickstart.md`

**Tests**: No automated test suite is requested by the feature specification. The verification tasks
below are manual Gateway acceptance checks from `quickstart.md`; they are not optional for release.

**Organization**: Tasks are grouped by user story so each story can be implemented and validated
independently. All three stories are Priority P1.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependency on an incomplete task)
- **[Story]**: `US1`, `US2`, or `US3`
- Every task includes an exact repository path

## Path Conventions

This repository is not a `src/` application. Runtime paths are Ignition project exports:

```text
services/ignition/projects/kanoaMES/com.inductiveautomation.perspective/views/training/receiveMaterial/view.json
services/ignition/projects/kanoaMES/com.inductiveautomation.perspective/views/training/receivingOrdersSchedule/view.json
```

`kanoaAPP` and `KANOA_SCRIPTS` are read-only reference/inheritance paths for this feature.

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Confirm the native-first scope and establish a comparison baseline before editing.

- [X] T001 Confirm the Principle VI gate in `specs/003-receive-material-woeditor-ui/plan.md` and `specs/003-receive-material-woeditor-ui/contracts/component-contracts.md`: verify that `kanoa/core/templates/selectors/tree/selector`, `kanoa/core/templates/inputs/confirm`, `kanoa/core/templates/displays/progressBar`, `ia.display.label`, `ia.input.numeric-entry-field`, and `ia.input.button` cover every requirement. If a native gap is found, stop and add the approval request to `plan.md` before writing code. Do not create a component or method.
- [X] T002 [P] Capture baseline evidence for visual comparison: open the current `training/receiveMaterial` and reference `kanoa/mes/workOrders/woEditor` in the local Gateway, and record screenshots/notes for the six order rows, selector presentation, and action styling. Record the result with the evidence described in `specs/003-receive-material-woeditor-ui/quickstart.md`.
- [X] T003 [P] Validate the baseline resources parse and exist: run `python3 -m json.tool` on `services/ignition/projects/kanoaMES/com.inductiveautomation.perspective/views/training/receiveMaterial/view.json` and `.../receivingOrdersSchedule/view.json`, and confirm the inherited templates referenced in `plan.md` exist under `services/ignition/projects/kanoaAPP/com.inductiveautomation.perspective/views/kanoa/`.

**Checkpoint**: Native-first scope is confirmed and the baseline is recorded.

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Rebuild the shared screen shell and load pipeline that every story uses.

**⚠️ CRITICAL**: No user story work can begin until this phase is complete. All tasks in this phase
edit the same file and must run sequentially.

- [X] T004 In `services/ignition/projects/kanoaMES/com.inductiveautomation.perspective/views/training/receiveMaterial/view.json`, rebuild the root `ia.container.flex` to the reference geometry: direction `column`, style classes `kanoa/container kanoa/font/default`, `gap: 5`, `padding: 5`, `overflow: hidden`. Retain the `Receive Material` heading (`lblTitle`, `kanoa/font/titleLarge`) and a slim status row containing the existing `evProgressBar` and `lblNoOrder` components. Create named 30 px row containers with `shrink: 0`, `gap: 5`, `overflow: hidden`: `flxCntOrder`, `flxCntTitle`, `flxCntTarget`, `flxCntSchedule`, `flxCntStatus`, `flxCntNotes`, `flxCntTruck`, `flxCntTank`, `flxCntQty`, `flxCntActions`.
- [X] T005 In the same `receiveMaterial/view.json`, normalize the custom state to the contract in `specs/003-receive-material-woeditor-ui/data-model.md` §2: keep `order`, `receivedQtyKg`, `actualQtyKg`, `truckAssetId`, `truckPath`, `tankAssetId`, `tankPath`, `loading`, `submitting`, `errorMessage`, `result`, `truckOptions`, `tankOptions`; add `scheduledStart` and `orderNotes`, both initialized to `null`. Do not delete the existing `errorMessage`/`result` change scripts or the `confirmReceiveOrder` message handler yet.
- [X] T006 In the same `receiveMaterial/view.json`, rewrite `root.events.component.onStartup` as the shared load pipeline: read `self.view.params.value`, resolve `workOrderId`, load the order with the existing `kanoaScripts.custom.ops.receiving.getReceivingOrder` when no order object was passed, set `view.custom.order`, set `view.custom.scheduledStart` from `params.get('scheduledStart')`, load truck/tank lists with the existing `getReceivingAssets` into `truckOptions`/`tankOptions`, load cumulative kg with `getReceivedQtyForOrder` into `receivedQtyKg`, preserve the existing actionable error messages, and always clear `loading` in `finally`. Do not implement the notes fallback or the actual-quantity default here; those belong to US1 and US3.
- [X] T007 In the same `receiveMaterial/view.json`, verify all retained component names and event references still resolve after the restructure; remove only obsolete read-only label components (`lblOrderNumber`, `lblDescription`, `lblMaterial`, `lblTarget`, `lblUnit`, `lblReceived`) whose replacements are added in US1. Confirm the file parses with `python3 -m json.tool` before starting US1.

**Checkpoint**: The shared shell, state, and load pipeline are ready; user stories can now add their rows.

---

## Phase 3: User Story 1 — Review order information in the work order editor style (Priority: P1) 🎯

**Goal**: Show order number, title, target quantity, schedule date, status, and notes as read-only
Kanoa-styled values with the `woEditor` row geometry.

**Independent Test**: Open Receive Material for a scheduled order and compare it with the work order
editor; verify all six values match the canonical order, cannot be edited, and handle empty title,
empty notes, and missing schedule date per `quickstart.md` §1.

### Implementation for User Story 1

Tasks T008–T014 edit the same file and must run sequentially. T015 edits a different file and may run
in parallel.

- [X] T008 [US1] In `services/ignition/projects/kanoaMES/com.inductiveautomation.perspective/views/training/receiveMaterial/view.json`, add the `Order #` row inside `flxCntOrder`: a 65 px right-aligned `ia.display.label` with `kanoa/font/default`, plus a 200 px `grow: 1` `ia.display.label` bound to `view.custom.order.orderNumber` and rendering `"—"` when the value is null or empty. Do not use an input component.
- [X] T009 [US1] In the same `receiveMaterial/view.json`, add the `Title` row inside `flxCntTitle` with the same label/value geometry, binding the value to `view.custom.order.description`. Do not add new fallback logic: `getReceivingOrder` already returns `workOrderTitle or itemDescription`.
- [X] T010 [US1] In the same `receiveMaterial/view.json`, add the `Target Qty` row inside `flxCntTarget`, binding the value to `view.custom.order.targetQty` with Kanoa number formatting `#,##0.###` and appending `view.custom.order.unitName`; render `"Unavailable"` when the quantity is null.
- [X] T011 [US1] In the same `receiveMaterial/view.json`, add the `Schedule Date` row inside `flxCntSchedule`, binding the value to `view.custom.scheduledStart` and formatting it as a Kanoa date/time (`MM/dd/yyyy HH:mm`); render `"Unavailable"` when the value is null.
- [X] T012 [US1] In the same `receiveMaterial/view.json`, add the `Status` row inside `flxCntStatus`, binding the value to `view.custom.order.status` and rendering `"—"` when the value is null or empty.
- [X] T013 [US1] In the same `receiveMaterial/view.json`, add the `Notes` row inside `flxCntNotes`: label aligned top with `marginTop: 5px`; value is a multi-line `ia.display.label` with `overflowWrap: break-word` and `whiteSpace: normal`, bound to `view.custom.orderNotes`, rendering `"—"` when null or empty. Let the row grow so long notes remain readable.
- [X] T014 [US1] In the same `receiveMaterial/view.json`, add the notes fallback to `onStartup`: set `view.custom.orderNotes` from `params.get('orderNotes')` when present; otherwise, when `workOrderId` is available, call the native `system.kanoa.order.getProductionOrders({'workOrderId': workOrderId, 'ignoreActualQty': True})` and extract the `note` column with `system.kanoa.utilities.getFieldValue`. Leave errors non-blocking for the other fields but keep them out of the receipt path.
- [X] T015 [P] [US1] In `services/ignition/projects/kanoaMES/com.inductiveautomation.perspective/views/training/receivingOrdersSchedule/view.json`, update the existing confirm/navigate `onActionPerformed` script to add `'scheduledStart': selected.get('startDate')` (falling back to `selected.get('scheduledStart')`) and `'orderNotes': selected.get('note')` to the `params={'value': {...}}` dictionary passed to `system.perspective.navigate(view='training/receiveMaterial', ...)`. Do not change the order-eligibility call.
- [X] T016 [US1] Validate US1 in the local Gateway per `quickstart.md` §1: all six fields match the canonical order, are read-only, title falls back to the item description, empty notes show `"—"`, and a missing schedule date shows `"Unavailable"`. Record the evidence.

**Checkpoint**: User Story 1 is independently demonstrable on the refactored shell.

---

## Phase 4: User Story 2 — Select the truck and destination tank with the standard asset selector (Priority: P1)

**Goal**: Replace the dropdowns with the `woEditor`-style tree selector, scoped to enabled Storage
Locations in the Receiving and Bulk Storage areas.

**Independent Test**: Open each selector, browse/search, select a valid asset, clear it, and attempt a
folder/missing/out-of-area selection; verify only enabled Storage Locations in the correct area are
accepted and the selected path is visible (per `quickstart.md` §2).

### Implementation for User Story 2

Tasks T017–T021 edit the same file and must run sequentially.

- [X] T017 [US2] In `services/ignition/projects/kanoaMES/com.inductiveautomation.perspective/views/training/receiveMaterial/view.json`, add the `Receiving Truck` row label (65 px, right-aligned, `kanoa/font/default`) and the truck selector as an `ia.display.view` inside `flxCntTruck` with `props.path = "kanoa/core/templates/selectors/tree/selector"` and `props.params.values` set to: `msgHandler: "receivingTruckSelected"`, `options: {dragDrop: False, expand: False, multiSelect: False, showBreadcrumb: True, showClear: True, showSelectedPath: False}`, `selection: []`, `treePath: null`, and `style: {iconColor: "", iconPath: null, tooltip: null}`. Bind `props.params.values.data` with expression `1` plus a script transform returning `system.kanoa.asset.getAssets({'assetPath': 'Training Plant\\Receiving\\%', 'assetTypeName': 'Storage Location', 'enabled': True})`. Bind `props.params.values.path` to `view.custom.truckPath`.
- [X] T018 [US2] In the same `receiveMaterial/view.json`, add the `Destination Tank` row label (same geometry as T017) and the tank selector inside `flxCntTank` using the same component and option contract as T017, with `msgHandler: "receivingTankSelected"`, data from `system.kanoa.asset.getAssets({'assetPath': 'Training Plant\\Bulk Storage\\%', 'assetTypeName': 'Storage Location', 'enabled': True})`, and `props.params.values.path` bound to `view.custom.tankPath`.
- [X] T019 [US2] In the same `receiveMaterial/view.json`, add view/page-scope message handlers `receivingTruckSelected` and `receivingTankSelected` under `root.scripts.messageHandlers`. Each handler: clears the matching `*AssetId` and `*Path` when `payload['selection']` is empty; otherwise reads `payload['selection'][0]['value']`; rejects a synthetic folder node with no `assetId` by clearing the selection and setting an actionable `errorMessage`; otherwise sets `*AssetId` from `assetId` and `*Path` from `path` or `assetPath`.
- [X] T020 [US2] In the same `receiveMaterial/view.json`, add per-selector empty-state labels under `flxCntTruck` and `flxCntTank`, visible when `len(view.custom.truckOptions) == 0` or `len(view.custom.tankOptions) == 0`, explaining that no eligible assets were found and that an administrator must configure enabled Storage Locations in the area. Keep the existing `getReceivingAssets` call as the source for these lists.
- [X] T021 [US2] In the same `receiveMaterial/view.json`, remove the obsolete `evTruck` and `evTank` `assetDropdownSelector` embeds and their `props.params.selectedPath` bindings, plus any now-unused `lblTruck`/`lblTank` children that conflict with the new row composition. Do not remove `truckOptions`/`tankOptions` state or the `getReceivingAssets` load.
- [X] T022 [US2] Validate US2 in the local Gateway per `quickstart.md` §2: hierarchy/search/clear/single-select work like `woEditor`; only the correct area is offered; folder selections are rejected; selected paths are visible; empty areas show guidance; a disabled/moved asset is rejected at confirmation. Record the evidence.

**Checkpoint**: User Story 2 is independently demonstrable with the existing order display.

---

## Phase 5: User Story 3 — Enter the actual quantity and confirm or go back (Priority: P1)

**Goal**: Provide the kg quantity with an outstanding-quantity default, keep the existing receipt and
transfer behavior, and expose only Confirm and Back.

**Independent Test**: Open a new order and a partially received order, verify both quantity defaults,
test invalid and valid quantities, double-submit, transfer-pending messaging, and Back, per
`quickstart.md` §3–§8.

### Implementation for User Story 3

Tasks T023–T027 edit the same file and must run sequentially.

- [X] T023 [US3] In `services/ignition/projects/kanoaMES/com.inductiveautomation.perspective/views/training/receiveMaterial/view.json`, add the `Actual Qty` row inside `flxCntQty`: a 65 px right-aligned `kanoa/font/default` label, an `ia.input.numeric-entry-field` with `kanoa/font/default` and `props.value` bound bidirectionally to `view.custom.actualQtyKg`, and a static `kg` label. Disable the field when `view.custom.order.targetQty` is null, not greater than zero, or `view.custom.receivedQtyKg >= view.custom.order.targetQty`, and expose the reason through the existing `errorMessage` feedback.
- [X] T024 [US3] In the same `receiveMaterial/view.json`, extend `onStartup` after a successful `getReceivedQtyForOrder` to set `view.custom.actualQtyKg = max(0, float(view.custom.order.targetQty) - float(view.custom.receivedQtyKg))`. If the target is unavailable or not greater than zero, or the receipt-history read fails, leave the quantity null, disable Confirm, and show an explanation. Apply the default only on startup so an operator edit is not overwritten by later re-renders.
- [X] T025 [US3] In the same `receiveMaterial/view.json`, rebuild the actions in `flxCntActions`: a `Confirm` `ia.input.button` with `kanoa/button/filled` and a `Back` `ia.input.button` with `kanoa/button/outlined`, centered with `gap: 5` and `padding: 5`. Remove the `btnPending` and `btnRetryTransfer` components and their events. Bind Back to `system.perspective.navigate(view='training/receivingOrdersSchedule')` with no writes.
- [X] T026 [US3] In the same `receiveMaterial/view.json`, update the Confirm event and `confirmReceiveOrder` handler: block when `submitting` is true or `actualQtyKg`, `truckAssetId`, or `tankAssetId` is missing; open `kanoa/core/templates/inputs/confirm` with the order number and quantity; keep the handler calling the existing `kanoaScripts.custom.ops.receiving.receiveOrder(workOrderId, actualQtyKg, truckAssetId, tankAssetId, session user)` exactly once. Bind `props.enabled` on Confirm to `not view.custom.submitting`.
- [X] T027 [US3] In the same `receiveMaterial/view.json`, update the existing `custom.result` / `custom.errorMessage` feedback scripts: success identifies order, lot, quantity, truck, and tank; `TRANSFER_PENDING` states that material remains at the truck and directs the operator to the separate `training/pendingTransfers` screen; validation/reconciliation failures are actionable and never invite a blind retry. Keep `system.kanoa.toast.show` and `kanoa/core/templates/displays/messagePopup` for feedback.
- [ ] T028 [US3] Validate US3 in the local Gateway per `quickstart.md` §3–§8: new-order and partial-order defaults, invalid quantity/asset rejection, exactly one receipt and transfer for a valid confirmation, duplicate-submit guard, transfer-pending hand-off, and Back with no writes. Record the evidence.

**Checkpoint**: All three user stories are independently functional and the screen is usable for receiving.

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Prove the refactor is structurally sound, Kanoa-first, and regression-free.

- [X] T029 [P] Run `python3 -m json.tool` on both changed files: `services/ignition/projects/kanoaMES/com.inductiveautomation.perspective/views/training/receiveMaterial/view.json` and `.../receivingOrdersSchedule/view.json`. Confirm both parse with no output.
- [X] T030 [P] Run `git diff --name-only | grep -E 'kanoaAPP|KANOA_SCRIPTS' || true` and confirm it prints nothing. Confirm no file under `services/ignition/projects/kanoaAPP/` or `services/ignition/projects/KANOA_SCRIPTS/` changed.
- [X] T031 Run the theme and constrained-width checks in `quickstart.md` §9: all fields, selectors, quantity input, and actions remain readable and reachable in every supported Kanoa theme and at a constrained browser width; notes wrap without breaking the layout.
- [ ] T032 Run the feature 001 regression subset in `quickstart.md` §10: eligibility, cumulative target enforcement, concurrent submissions, pending-transfer recovery on its own screen, and uncertain-outcome handling.
- [X] T033 Audit the final diff for Principle VI and record release evidence per `quickstart.md` "Release Evidence": no new Perspective view, template, function, module, helper, wrapper, table, or SQL; only the two named view files changed; record order IDs, lot/event IDs, quantities, paths, screenshots, and test outcomes in the pull request's Testing section.

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies; T001 is the approval gate.
- **Foundational (Phase 2)**: Depends on T001–T003; blocks all user stories.
- **User Stories (Phase 3–5)**: Depend on Phase 2. Because all three edit the same `receiveMaterial`
  file, they must be applied sequentially in priority order: US1 → US2 → US3.
- **Polish (Phase 6)**: Depends on all three stories being complete.

### User Story Dependencies

- **US1 (P1)**: No dependency on US2/US3. Adds the read-only order rows and the schedule/notes
  plumbing.
- **US2 (P1)**: Depends on Phase 2 only. Its selectors are independent of the order rows, but its
  edits share the same file and follow US1.
- **US3 (P1)**: Depends on Phase 2 and reuses `view.custom.order`, `receivedQtyKg`, and the selector
  asset IDs. It follows US2 so the confirm action has both selectors available.
- **Minimum releasable increment**: all three P1 stories. US1 alone is a demonstrable layout
  increment, but the screen is not usable for receiving until US3 is complete.

### Within Each User Story

- Apply JSON structure edits in the order listed; re-parse `view.json` after each logical group.
- Complete the story's Gateway validation task before starting the next story, so a regression is
  attributable to one story.
- Do not create automated test files; the manual acceptance tasks are the required verification.

### Parallel Opportunities

- T002 and T003 can run in parallel (read-only baseline checks).
- T015 edits `receivingOrdersSchedule/view.json` and can run in parallel with the US1 edits to
  `receiveMaterial/view.json`, provided the `scheduledStart`/`orderNotes` parameter names are fixed
  first.
- T029 and T030 can run in parallel after implementation.
- No two tasks that edit `receiveMaterial/view.json` may run in parallel; they conflict on one file.

---

## Parallel Example: User Story 1

```text
# These touch different files and can run together after Phase 2:
T008–T014  receiveMaterial/view.json read-only rows and notes fallback
T015       receivingOrdersSchedule/view.json navigation parameters
```

## Parallel Example: Polish

```text
T029  python3 -m json.tool on both view exports
T030  git diff scope check for kanoaAPP / KANOA_SCRIPTS
```

---

## Implementation Strategy

### MVP First (US1)

1. Complete Phase 1 (native-first gate) and Phase 2 (shared shell).
2. Complete US1 and run `quickstart.md` §1.
3. Stop and review the read-only order presentation against `woEditor` before adding interactions.

### Incremental Delivery

1. US1 → read-only order information; validate §1.
2. US2 → standard asset selectors; validate §2.
3. US3 → quantity default, Confirm/Back, and preserved receipt behavior; validate §3–§8.
4. Phase 6 → structural, theme, width, and feature 001 regression checks; record release evidence.

Because all three stories are P1, do not release a build that stops before US3.

### Parallel Team Strategy

Not recommended for this feature: all implementation tasks edit the same Perspective view export.
Keep one implementer on `receiveMaterial/view.json`; a second person may update
`receivingOrdersSchedule/view.json` (T015) and run independent validation/evidence capture.

---

## Notes

- Every task follows the required checklist format: checkbox, sequential ID, optional `[P]`, story
  label only in user-story phases, and an exact file path.
- `kanoaAPP` and `KANOA_SCRIPTS` are read-only. If a task appears to require editing them, stop: the
  design is wrong or a Principle VI approval is required.
- Do not replace the read-only labels with disabled inputs; FR-002 requires no editable control.
- Do not reintroduce Pending or Retry actions on this screen.
- Commit after each story checkpoint so a regression can be isolated.

## Gateway Validation Outcome (2026-11-18)

- **T028 remains open.** Valid receipt, duplicate guard, invalid input matrix, Back, and the
  transfer-pending presentation passed. The partial-receipt default did **not** pass because the
  installed Kanoa `getLotEvents` fails against `mes.vwLotEvent` with `Invalid column name 'enabled'`.
  A real post-receipt transfer failure could not be simulated because the implementation documents
  no non-destructive simulation method.
- **T032 remains open.** Two-session concurrency produced two successful 7,000 kg receipts for
  order 4 (14,000 kg total against a 12,000 kg target). Pending-transfer recovery was not exercised
  because no stranded lot could be created safely. Uncertain-outcome feedback was verified from the
  view path and Gateway logs, but not from a real write timeout.
- Full details and evidence paths are in
  `specs/003-receive-material-woeditor-ui/evidence/acceptance-notes.md`.
- **Release status: blocked.** The vendor/shared-script prerequisite defect and the resulting
  over-receipt must be resolved before operator registration.
