# Tasks: Operator Bulk Receiving

**Input**: Design documents from `specs/001-operator-receiving/`

**Prerequisites**: `plan.md`, `spec.md`, `research.md`, `data-model.md`, `contracts/`, `quickstart.md`

**Tests**: No automated test-suite tasks are included. The constitution requires manual Gateway validation of Ignition changes and mutation retry behavior; these acceptance checks are scheduled in the final phase.

**Organization**: Tasks are grouped by user story. Implementation extends existing `kanoaMES` and `KANOA_SCRIPTS`; no new Ignition project is created and vendor `kanoaAPP` is not edited.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: May be done in parallel because it changes a different file and has no dependency on an incomplete task.
- **[Story]**: User story from `spec.md` (`US1`, `US2`, `US3`).
- Every task names its target file or Kanoa configuration location.

## Phase 1: Setup — Confirm Runtime Design Gates

**Purpose**: Verify the Kanoa 1.15.11 behaviors that affect safe implementation before creating operator views.

- [ ] T001 In an isolated local test session, verify `getNextSerialNumber` followed by a no-input/one-output `executeLotOperation` with a new `lotName`, `itemId`, and `itemUnitId` creates one lot and one Receive event; record exact payload fields and return values in `specs/001-operator-receiving/research.md`.
- [ ] T002 Inspect a representative eligible order and its history using Kanoa APIs; record canonical order description/target/UOM fields, status values, Receive output event quantity/UOM fields, and whether all target comparisons can be made in kg in `specs/001-operator-receiving/research.md`.
- [ ] T003 Verify the supported Gateway-scoped per-`workOrderId` serialization approach for check-and-post, document how concurrent submissions fail closed, and confirm Kanoa Navigation/project export reproduction steps in `specs/001-operator-receiving/plan.md`.

**Checkpoint**: The current view exports are draft resources only. Do not import/activate them for operators or enable the write workflow until lot creation, quantity fields/UOM, and concurrency control are confirmed. If a gate cannot be satisfied, update the plan/spec before release.

---

## Phase 2: Foundational — Shared Ignition Receiving Module

**Purpose**: Establish client-owned Gateway code in the correct inheritable project before story work.

- [X] T004 Create the `receiving` Ignition script package with `code.py` and `resource.json` under `services/ignition/projects/KANOA_SCRIPTS/ignition/script-python/kanoaScripts/custom/ops/receiving/`, matching neighboring package metadata and Jython 2.7 conventions.
- [X] T005 Add shared receiving result/status helpers, a named `system.util.getLogger` logger, and authenticated Kanoa user-ID mapping to `services/ignition/projects/KANOA_SCRIPTS/ignition/script-python/kanoaScripts/custom/ops/receiving/code.py`; use `system.kanoa.security.getIDPUserId` on the authenticated Perspective user and never a fixed `SYSTEM` user.
- [X] T006 Add reusable Kanoa lookups for enabled `Receive`/`Transfer` operations, lot state, item sources, kg unit, and configured serial definition to `services/ignition/projects/KANOA_SCRIPTS/ignition/script-python/kanoaScripts/custom/ops/receiving/code.py`; resolve IDs at runtime and return actionable errors when configuration is missing.

**Checkpoint**: Shared code loads in the Gateway and has no dependency on edits to `kanoaAPP` or custom database tables.

---

## Phase 3: User Story 1 — Receive a Scheduled Order (Priority: P1) 🎯 MVP

**Goal**: Let an operator select an order, review locked order details, enter actual quantity, choose truck/tank, and record receipt plus transfer.

**Independent Test**: Complete one valid receipt from the dedicated schedule and verify one lot is associated with the selected order, first recorded at the chosen truck, then moved to the chosen tank.

### Implementation for User Story 1

- [X] T007 [P] [US1] Create the Receiving Orders Schedule Perspective view and `resource.json` at `services/ignition/projects/kanoaMES/com.inductiveautomation.perspective/views/training/receivingOrdersSchedule/`; display date-range schedule rows and preserve `scheduleBlockId` and `workOrderId` for selection.
- [X] T008 [P] [US1] Create the receiving form Perspective view and `resource.json` at `services/ignition/projects/kanoaMES/com.inductiveautomation.perspective/views/training/receiveMaterial/`; include read-only order number/description/material/target fields, actual kg entry, truck/tank selectors, confirmation summary, and loading/empty/error/result states.
- [X] T009 [US1] Implement `getScheduledReceivingOrders(startDate, endDate)`, `getReceivingOrder(workOrderId)`, and `getReceivingAssets()` in `services/ignition/projects/KANOA_SCRIPTS/ignition/script-python/kanoaScripts/custom/ops/receiving/code.py`; filter canonical orders to Scheduled or In Progress and scope enabled Storage Locations to the Receiving and Bulk Storage areas.
- [ ] T010 [US1] Implement `receiveOrder(...)` in `services/ignition/projects/KANOA_SCRIPTS/ignition/script-python/kanoaScripts/custom/ops/receiving/code.py`; revalidate order and assets, allocate a Kanoa serial, create the lot and Receive output through the runtime-verified `executeLotOperation` payload, then Transfer the same lot from the selected truck to the selected tank; check both API outcomes and return distinct full-success/receipt-only/failure/reconciliation results.
- [X] T011 [US1] Wire schedule selection and explicit order confirmation to the receiving view, reload canonical read-only order data, and connect form confirmation/result handling in `services/ignition/projects/kanoaMES/com.inductiveautomation.perspective/views/training/receivingOrdersSchedule/view.json` and `services/ignition/projects/kanoaMES/com.inductiveautomation.perspective/views/training/receiveMaterial/view.json`.
- [ ] T012 [US1] Register the schedule and receiving views through Kanoa **Configuration → Application → Navigation**, scoped to runnable project `kanoaMES` and receiving operator roles; record the exact reproducible navigation/export procedure in `specs/001-operator-receiving/quickstart.md`.

**Checkpoint**: A valid order can be received without Lot Manager; the UI distinguishes receipt at the truck from a completed tank transfer.

---

## Phase 4: User Story 2 — Record Partial Deliveries Safely (Priority: P1)

**Goal**: Permit partial receipts while preventing cumulative receipt quantity from exceeding the order target, including concurrent submissions through this receiving workflow.

**Independent Test**: Record partial quantities up to the target, then submit an over-target and simultaneous stale quantity; each rejected attempt must create no additional lot or Receive event.

### Implementation for User Story 2

- [X] T013 [US2] Implement `getReceivedQtyForOrder(workOrderId)` in `services/ignition/projects/KANOA_SCRIPTS/ignition/script-python/kanoaScripts/custom/ops/receiving/code.py` using enabled Kanoa lot events filtered to the `Receive` operation and `output` source; normalize event quantities to kg using only a verified conversion and fail closed when units are incomparable.
- [ ] T014 [US2] Wrap the final order reload, cumulative quantity read, validation, and Receive write in the verified per-`workOrderId` Gateway serialization guard in `services/ignition/projects/KANOA_SCRIPTS/ignition/script-python/kanoaScripts/custom/ops/receiving/code.py`; recheck status and reject stale/over-target submissions before serial allocation or lot/event writes.
- [ ] T015 [US2] Update the receiving form bindings in `services/ignition/projects/kanoaMES/com.inductiveautomation.perspective/views/training/receiveMaterial/view.json` to show received-to-date, remaining target, and post-receipt balance; disable invalid submits and show clear errors without writing.

**Checkpoint**: Partial quantities are accepted only when the recalculated cumulative total remains at or below target; simultaneous stale submissions are rejected.

---

## Phase 5: User Story 3 — Recover a Transfer That Did Not Complete (Priority: P2)

**Goal**: Let operators retry a truck-to-tank transfer immediately or after reopening, without repeating receipt.

**Independent Test**: Leave a successfully received lot at a truck after a transfer failure, reopen the workflow, select that lot and a destination tank, and verify only one additional Transfer is recorded.

### Implementation for User Story 3

- [X] T016 [US3] Implement `getPendingTransfers()` in `services/ignition/projects/KANOA_SCRIPTS/ignition/script-python/kanoaScripts/custom/ops/receiving/code.py` by querying current lot activity for each enabled Receiving truck with positive quantity; return lot, material, order, quantity/UOM, and current truck fields and revalidate list rows before transfer.
- [X] T017 [US3] Implement `retryTransfer(lotId, tankAssetId)` in `services/ignition/projects/KANOA_SCRIPTS/ignition/script-python/kanoaScripts/custom/ops/receiving/code.py`; validate current source quantity and destination, execute only the Transfer operation using the existing lot, and never allocate a serial, create a lot, or repeat Receive.
- [X] T018 [P] [US3] Create the pending-transfer Perspective view and `resource.json` at `services/ignition/projects/kanoaMES/com.inductiveautomation.perspective/views/training/pendingTransfers/`; show lot/order/material/quantity/truck and require the operator to select a destination tank again after reopening.
- [X] T019 [US3] Wire immediate retry after a transfer failure and pending-transfer refresh/retry after reopening in `services/ignition/projects/kanoaMES/com.inductiveautomation.perspective/views/training/receiveMaterial/view.json` and `services/ignition/projects/kanoaMES/com.inductiveautomation.perspective/views/training/pendingTransfers/view.json`; report pending/complete outcomes and never invoke `receiveOrder` from retry.
- [ ] T020 [US3] Register the pending-transfer view in Kanoa **Configuration → Application → Navigation** for `kanoaMES` and the authorized operator role; update the navigation steps in `specs/001-operator-receiving/quickstart.md`.

**Checkpoint**: A lot with quantity still at a Receiving truck can be identified from Kanoa activity and moved to a selected tank without a duplicate receipt.

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Verify the integrated workflow, versioned project resources, operational recovery, and documentation.

- [ ] T021 Exercise all scenarios in `specs/001-operator-receiving/quickstart.md` on the local KanoaMES 1.15.11 Gateway, including valid receipt, quantity boundaries, concurrent submissions, stale order/assets, transfer failure/retry, and uncertain write reconciliation; record observed results and operation IDs in the quickstart evidence section.
- [ ] T022 Verify exported `code.py`, script `resource.json`, all Perspective `view.json`/`resource.json` files, project ownership, and Navigation reproduction steps against `.specify/memory/constitution.md`; record any deployment limitation in `specs/001-operator-receiving/quickstart.md`.
- [X] T023 Update `docs/solution-design.md` sections 19–22 to describe the implemented schedule, operator fields, receipt/transfer sequence, pending-transfer recovery, and any runtime-verified limits; keep asset/item facts aligned with repository exports.

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: Confirm Kanoa API semantics, field mapping, concurrency protection, and navigation/export before importing or activating the draft operator views.
- **Foundational (Phase 2)**: Depends on Phase 1; establishes the reusable script package and shared API/error/audit helpers.
- **US1 (Phase 3)**: Depends on Phase 2; delivers the MVP receiving flow.
- **US2 (Phase 4)**: Depends on US1 receipt path and Phase 1 concurrency/UOM gates; adds cumulative receipt protection.
- **US3 (Phase 5)**: Depends on US1 lot/transfer outcome contract; adds current-stock recovery and transfer-only retry.
- **Polish (Phase 6)**: Depends on the desired stories being complete.

### User Story Dependencies

- **US1 (P1)**: Depends on shared foundation; no other story dependency.
- **US2 (P1)**: Extends the US1 submit path; cannot be delivered before US1's receipt function exists.
- **US3 (P2)**: Extends the US1 receipt/transfer outcome and lot identity; cannot be delivered before US1.
- US2 and US3 are logically independent after US1, but their service tasks touch the same `receiving/code.py`; execute those file edits sequentially to avoid conflicts.

### Parallel Opportunities

- T007 and T008 can be implemented in parallel after the view contract is agreed; they modify separate Perspective view resources.
- T018 can be built in parallel with T016/T017 after the recovery result fields are agreed; it uses a separate Perspective view resource.
- No automated test implementation tasks are included; manual Gateway validation is required in T021 by the project constitution.

### Parallel Execution Examples

**US1 after T004–T006**:

```text
Work item A: T007 — Receiving Orders Schedule view
Work item B: T008 — Receiving form view
```

They create separate view resources. T011 wires them after T009/T010 define the data and mutation behavior.

**US3 after US1**:

```text
Work item A: T016 and T017 — pending/retry functions in KANOA_SCRIPTS
Work item B: T018 — pending-transfer view in kanoaMES
```

The two work items touch different project resources; T019 connects them after their fields and result contract are agreed.

---

## Implementation Strategy

### MVP First (US1 plus required quantity safety)

1. Complete runtime gates (Phase 1) and shared module setup (Phase 2).
2. Deliver US1 schedule selection, read-only order details, and receipt/transfer flow.
3. Complete US2 cumulative quantity enforcement before enabling receiving for operators; it is a required safety rule even though US1 is the first demonstrable workflow.
4. Validate the P1 flow with the local Gateway before starting recovery UI.

### Incremental Delivery

1. Establish Kanoa API behavior and the shared script package.
2. Deliver scheduled-order receipt with over-target protection.
3. Add pending-transfer discovery and transfer-only recovery.
4. Complete runtime evidence, export checks, navigation reproduction, and solution-design update.
