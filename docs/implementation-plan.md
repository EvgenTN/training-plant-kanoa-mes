# Operator Receiving Screen Implementation Plan

**Status:** Proposed  
**Design basis:** [Bulk Receiving Solution Design](solution-design.md), section 20  
**Scope:** A focused operator workflow for selecting a scheduled receiving order, recording the received quantity, and putting the resulting lot into a selected bulk storage tank.

## 1. Goal

Implement a Perspective application flow that replaces operator use of Lot Manager for routine bulk receiving. The screen will use Kanoa orders, assets, serialization, lot operations, and inventory as the source of truth. It will not introduce custom inventory tables or bypass Kanoa MES APIs.

## 2. User Flow

1. Operator opens the Receiving Orders Schedule.
2. Operator selects a scheduled order and confirms the selection.
3. The Receiving screen reloads the order by `workOrderId` and displays order number, description, material, and target quantity as read-only fields.
4. Operator enters actual quantity in `kg`, selects a Receiving truck, selects a Bulk Storage tank, and reviews the receipt summary.
5. Operator confirms once. The system receives the lot at the selected truck, then transfers that lot to the selected tank.
6. The screen reports the outcome and lot number. If receipt succeeds but transfer fails, it identifies the lot still at the truck and offers a transfer retry without repeating receipt.

## 3. Proposed Technical Design

### Schedule and order selection

- Build a dedicated Receiving Orders Schedule view in the runnable `kanoaMES` project, following Kanoa's custom-lot-screen example. Query Kanoa schedule blocks for the selected date range and show the linked order number, planned time, material, and target quantity.
- Use `system.kanoa.schedule.getCalendarEvents(...)` with `scheduleType: 'operation'` to match Kanoa's Operations Schedule rows. Each row must retain the stable `workOrderId` and schedule event identifier as internal values.
- On confirmation, navigate to the Receiving view with `workOrderId`; reload canonical order data using `system.kanoa.order.getProductionOrders({'workOrderId': ...})`.
- Filter to orders in configured receivable statuses and define how unscheduled orders are handled. Initial scope should display scheduled orders only. Read order/item values from the canonical order record, not only from a potentially stale schedule block.
- **Decision: use a dedicated Receiving Orders Schedule view.** Kanoa's available docs establish schedule-block queries but not a supported native schedule action that launches a custom receiving view with the selected order.

### Receiving form and asset choices

- Display read-only: order number, description (order description, falling back to item description), material, and target quantity with unit.
- Retrieve eligible trucks from enabled Storage Locations under `Training Plant\\Receiving` and tanks from enabled Storage Locations under `Training Plant\\Bulk Storage`, using `system.kanoa.asset.getAssets(...)` and validate paths/types server-side before writing.
- Require positive actual quantity and both asset selections. Allow partial receipts; before posting, sum the order's prior `Receive` output events with `system.kanoa.lot.getLotEvents(...)` and reject if the new cumulative receipt would exceed target. Show remaining target quantity and post-receipt balance.
- Lock the selected order fields for the receipt. Changing orders returns to the schedule and requires confirmation.

### Posting and traceability

- Resolve operation IDs, lot state, item sources, units, and serialization IDs by Kanoa API lookups at runtime; never hard-code database IDs. Use the authenticated Perspective user's Kanoa user ID for audit fields, not a fixed `SYSTEM` identity.
- Follow Kanoa's documented custom receiving pattern: call `system.kanoa.serial.getNextSerialNumber(...)`, create the lot with `system.kanoa.lot.addLot(...)` using the order's item and kg unit, then record the no-input/one-output `Receive` with `system.kanoa.lot.executeLotOperation(...)`. The output event carries the actual quantity, truck asset ID, selected `workOrderId`, `output` item source, initial state, and timestamp.
- Transfer the received lot using a separate `Transfer` call to `executeLotOperation(...)`, with the selected truck as the input location and the destination tank as the output location. Preserve the same lot and order association through the transfer.
- Treat receipt and transfer as two committed Kanoa operations, not one transaction. On transfer failure, leave the successfully received lot visible at the truck and provide **Retry transfer now**. Also show a pending-transfer list when the workflow is reopened, populated from Kanoa lot activity for enabled Receiving trucks and filtered to lots with quantity remaining there; retry only the `Transfer` for the operator-selected lot.
- Prevent duplicate operator submissions in the Perspective session and make the result of each Kanoa call explicit. Before claiming cross-session retry idempotency, confirm a durable Kanoa-supported receipt key or recovery lookup; view/session state alone is not durable. Do not add a custom inventory table for this.
- Keep event handlers thin: validate form state, call reusable functions, and render returned status. Put shared Kanoa API orchestration in the client script package under `KANOA_SCRIPTS`; return structured results and log mutation start/outcome with operation, order, lot, and asset identifiers. Show operators actionable messages without internal exceptions or secrets.

## 4. Implementation Phases

### Phase A — Configuration and API spike

1. Confirm the installed Kanoa system function signatures and returned fields using the local function reference and Kanoa's sample `tracePerspectiveViews.zip`: orders, schedule blocks, assets, items, units, lot states, serial definitions, operations, and item sources.
2. Confirm target quantity field and UOM mapping. Apply the decided policy: allow partial receipts, but reject a receipt that would make cumulative `Receive` output quantity exceed the order target. Permit only `Scheduled` or `In Progress` orders.
3. Confirm `getNextSerialNumber`, `addLot`, and `executeLotOperation` behavior on the pinned Kanoa version, including which failure cases can leave an unused serial or an unreceived lot.
4. Confirm `Receive` can be executed at a truck Storage Location and the `Transfer` payload moves the same lot from the truck asset to the tank asset.
5. Exercise the native API sequence with a representative order and verify the authenticated operator, lot, work order, and both storage locations appear correctly in Kanoa history.
6. Record any API/version-specific findings in this plan before building the views.

**Exit criteria:** Required order and operation payloads are confirmed on the installed runtime; unresolved business rules have named owners and approved defaults.

### Phase B — Reusable receiving service

1. Implement client-specific functions in `services/ignition/projects/KANOA_SCRIPTS/ignition/script-python/kanoaScripts/custom/ops/receiving/code.py` with its Ignition `resource.json`, matching neighboring script-package resources and the repository's Jython 2.7 naming/docstring conventions.
2. Add read functions for scheduled blocks, canonical order details, and scoped truck/tank choices. Keep returned data to the fields needed by the Perspective views.
3. Add a preflight function that reloads the order and validates status, item, kg unit, quantity, assets, and required Kanoa configuration before creating a lot.
4. Add separate `receiveMaterial(...)` and `transferReceivedLot(...)` operations. The receive function resolves a serial, calls `addLot`, then calls `executeLotOperation`; the transfer function consumes/outputs the same lot through a `Transfer` operation.
5. Return the lot name/ID and operation event IDs after each committed step. A transfer recovery lookup must use `system.kanoa.lot.getLotActivity(...)` against the Receiving truck assets to find lots still having quantity there; it must never call the receive function again.
6. Make duplicate handling explicit: block repeat clicks in the session. Use Kanoa's lot event/history lookup to resolve a completed receive and its lot before offering recovery. If an ambiguous timeout cannot be resolved from Kanoa data, surface the case for reconciliation rather than silently retrying the receive.

**Exit criteria:** Service methods reject invalid input without writes, return actionable results, and make receipt/transfer state unambiguous.

### Phase C — Perspective schedule and receiving views

1. Create client-owned Perspective views in `services/ignition/projects/kanoaMES/com.inductiveautomation.perspective/views/`, consistent with Kanoa's documented procedure for importing custom trace views into `kanoaMES`. Do not edit vendor-managed `kanoaAPP` resources or duplicate inherited vendor views.
2. Implement the Receiving Orders Schedule with date/status filtering, order selection, a visible confirmation step, and empty/loading/error states.
3. Implement the Receiving form with locked order fields, actual quantity input, truck/tank selectors, target variance display, and a final confirmation summary.
4. Wire events to the reusable service; disable submission while posting and display distinct statuses for received-and-transferred, received-but-transfer-pending, and failed-before-receipt. Add a pending-transfer list that can be reloaded from Kanoa lot activity rather than depending on session state.
5. Register the schedule and receiving views through **Configuration → Application → Navigation**, assigning the runnable project and operator roles as appropriate. Do not hand-edit Kanoa-managed navigation data unless its supported configuration API is established.

**Exit criteria:** An operator can move from schedule selection to receipt without opening Lot Manager, and all view resources are exported into the correct owning project.

### Phase D — Runtime verification and release

1. Verify that the dedicated schedule lists the intended `Scheduled` and `In Progress` orders and passes the stable `workOrderId`.
2. Verify order values are read-only and match the canonical Kanoa order, including target quantity and UOM.
3. Verify only the configured trucks and tanks appear and disabled/out-of-area assets are rejected at submission.
4. Run a successful receipt and inspect Lot Manager/lot trace to confirm actual quantity, item, unit, state, order association, truck receipt, and tank transfer.
5. Exercise invalid quantity, missing selections, stale/closed order, double-click, Kanoa API error, and transfer failure/retry. Confirm no duplicate lots or receive events.
6. Record exact Gateway/UI steps, observed results, and any known limitations in the change review. Do not reset or reseed the database as part of verification.

**Exit criteria:** All acceptance criteria below pass on the running local Gateway, and the exported project resources are reproducible from version control.

## 5. Acceptance Criteria

- Operator can select and confirm an order from the Receiving Orders Schedule.
- Receiving screen shows order number, order description (fall back to item description), material, and target quantity as read-only values loaded from Kanoa.
- Actual quantity is required, positive, expressed in kg, and validated against the approved receiving rule.
- Truck choices are limited to enabled Storage Locations under `Training Plant\\Receiving`; tank choices are limited to enabled Storage Locations under `Training Plant\\Bulk Storage`.
- A successful confirmation creates one Kanoa lot via `Receive`, associates the receive event with the selected order, and transfers the lot from truck to tank.
- A transfer retry after partial success does not create another lot or receive event; operators can recover it immediately or after reopening the application from the pending-transfer list.
- Operator receives a clear outcome and can identify the lot and final or pending location.
- Custom scripts use Kanoa APIs, are Jython 2.7 compatible, use the authenticated user's Kanoa ID, log mutation outcomes, and reside in `KANOA_SCRIPTS` outside vendor-managed `kanoaAPP`.

## 6. Decisions Required Before or During Phase A

| Decision | Proposed starting point | Why confirmation is needed |
|---|---|---|
| Which order states are receivable? | **Decided:** `Scheduled` or `In Progress` | Confirm exact status names against the installed configuration. |
| Can one order have multiple deliveries? | **Decided:** Yes, partial and multiple receipts are allowed. | Recalculate cumulative receipts from Kanoa `Receive` output events before each post. |
| Over-receipt tolerance | **Decided:** None; reject if cumulative received quantity would exceed target. | Compare in a consistent UOM and validate conversions to kg before posting. |
| Description field | **Decided:** Use order description, falling back to item description. | Confirm actual order/item API fields during implementation. |
| Schedule entry point | **Decided:** Dedicated Receiving Orders Schedule view. | Native Operations Schedule custom launch support is not established by available docs. |
| Transfer recovery | **Decided:** Offer immediate retry and a pending-transfer list on reopen. | Reconstruct pending lots from Kanoa `getLotActivity` at Receiving trucks; no view/session-only state. |
| Lot creation sequence | `getNextSerialNumber` → `addLot` → `Receive` operation | This is the sequence in Kanoa's published custom Receive Lot view; verify failure/retry handling on the pinned release. |

## 7. Project Boundaries and Risks

- Keep reusable client scripts in `KANOA_SCRIPTS`; keep client-owned Perspective views/navigation in the runnable project approved for operator UI. Never modify `kanoaAPP` vendor resources for this feature.
- Use only `system.kanoa.*` for MES reads and writes. No direct SQL or custom inventory records.
- Follow the Kanoa custom lot screen sample for serialization, lot creation, and `executeLotOperation`; adapt its hard-coded CoreForge item and asset choices to the Training Plant order and asset hierarchy.
- Receive and Transfer are separate Kanoa operations. A failure between them can leave inventory on a truck; make this state visible and recoverable.
- Order/quantity field names, serialization behavior, operation linking, and native schedule extension behavior need runtime confirmation against pinned KanoaMES 1.15.11.
- Preserve unrelated workspace changes while exporting or editing Ignition resources.
