# Research: Operator Bulk Receiving

## Decision 1: Build a dedicated receiving order schedule

**Decision**: Provide a Receiving Orders Schedule view that lists schedule blocks for the selected date range, lets an operator confirm an order, and passes its `workOrderId` to the receiving view. Reload the selected order from the canonical order API before display and again before posting.

**Rationale**: The built-in Kanoa Operations Schedule calls `system.kanoa.schedule.getCalendarEvents(...)` with `scheduleType: 'operation'`, a date range, and an optional asset path. This is the data source that matches the calendar events operators see; raw `getScheduleBlocks(...)` did not return the order shown in the UI during implementation validation. The receiving schedule queries operation events without an asset-path restriction, then `system.kanoa.order.getProductionOrders(...)` reloads the canonical order by `workOrderId`. Kanoa does not document a selected-event action for launching a custom view, so the feature uses a dedicated receiving schedule with an explicit confirmation step.

**Alternatives considered**:

- Add an action to the built-in Operations Schedule: not selected because the local docs do not establish a supported extension hook, and client-specific edits to vendor-managed `kanoaAPP` are prohibited.
- Select an order from an unfiltered order list: not selected because the agreed workflow starts with a scheduled receiving order.

**Sources**: `../../../kanoa-docs/docs.kanoa.ai/systemFunctions/schedule/getCalendarEvents.md`; `../../../kanoa-docs/docs.kanoa.ai/systemFunctions/schedule/getScheduleBlocks.md`; `../../../kanoa-docs/docs.kanoa.ai/systemFunctions/order/getProductionOrders.md`; `../../../kanoa-docs/docs.kanoa.ai/kanoa-ops/schedule-operations.md`; `../../../kanoa-docs/docs.kanoa.ai/configuration/navigation.md`; `services/ignition/projects/kanoaAPP/com.inductiveautomation.perspective/views/kanoa/scheduler/operations/view.json` (built-in event query).

## Decision 2: Use Kanoa lot APIs for receipt and transfer

**Decision**: Use configured serialization to generate a lot name, then create the new lot and its `Receive` operation event together through `executeLotOperation` using a no-input/one-output event. The output event carries lot name, item, kg unit, quantity, order, truck, state, source, and timestamp. Execute a separate `Transfer` with the existing lot as input at the truck and output at the destination tank. Use the authenticated Perspective session user for the Kanoa user ID.

**Rationale**: Kanoa's `executeLotOperation` reference documents that an output event may identify a new lot by `lotName` and that `itemId` is required when the lot is new. It describes the function as writing an operation event with its input and output events together. Creating by output therefore keeps lot creation and receipt within one operation call. The custom lot screen guide instead demonstrates serial → `addLot` → `executeLotOperation`; that is the fallback only if the pinned runtime does not support creating a lot from the output event. The transfer example uses `getLotActivity` and a `Transfer` operation. The project constitution requires Kanoa APIs, authenticated audit identity, and mutation logging.

**Alternatives considered**:

- Write inventory directly or create custom inventory records: rejected because Kanoa APIs are supported and constitutionally required where available.
- Receive directly into the tank: rejected because the agreed physical process receives to a selected truck first and records a subsequent movement to the selected tank.
- Combine receipt and transfer in one operation: rejected because the lot history must show both the receiving location and the tank movement as distinct events.
- Use the published serial → `addLot` → `Receive` sequence unconditionally: retained as a fallback if runtime verification shows that new lots cannot be created from an operation output event; the separate calls otherwise leave a lot without a Receive event if the second call fails.
- Copy the published sample without adaptation: rejected because it hard-codes CoreForge items/assets and omits the receiving order association.

**Sources**: `../../../kanoa-docs/docs.kanoa.ai/training/training-trace/lot-screens/custom-lot-screens.md`; `../../../kanoa-docs/docs.kanoa.ai/training/training-trace/lot-screens/lot-functions.md`; `../../../kanoa-docs/docs.kanoa.ai/systemFunctions/lot/executeLotOperation.md`; `../../../kanoa-docs/docs.kanoa.ai/systemFunctions/lot/addLot.md`; `../../../kanoa-docs/docs.kanoa.ai/systemFunctions/serial/getNextSerialNumber.md`.

## Decision 3: Calculate received quantity from Receive output events

**Decision**: Sum enabled Kanoa lot events filtered by the selected `workOrderId`, `Receive` operation, and `output` source. Normalize event quantities to the order's target unit before comparing with the target. Do not use production `actualQty` as a proxy for material receipt.

**Rationale**: Kanoa documents event filters for work order, operation, item source, and enabled state. The production order API's `actualQty` is documented as production against the order and is slower to compute; it is not documented as inbound material quantity. The local solution design establishes kg as the bulk receiving unit.

**Alternatives considered**:

- Sum current inventory by order: not selected because material may move to another asset or be consumed; current location quantity is not total received history.
- Use order `actualQty`: not selected because the docs describe actual production, not raw-material receiving.
- Permit a tolerance: not selected because the user decided cumulative actual receipts may not exceed the order target.

**Runtime check**: Verify new-lot creation from `executeLotOperation` output fields, returned event fields, and UOM representation on KanoaMES 1.15.11. If direct creation is unsupported, use the documented serial/`addLot`/Receive fallback with explicit recovery for a created lot whose Receive event failed. If a valid conversion cannot be found for an order, fail closed rather than compare unlike units.

**Sources**: `../../../kanoa-docs/docs.kanoa.ai/systemFunctions/lot/getLotEvents.md`; `../../../kanoa-docs/docs.kanoa.ai/systemFunctions/order/getProductionOrders.md`; `../../docs/solution-design.md`.

## Decision 4: Reconstruct pending transfers from current truck inventory

**Decision**: On the receiving workflow, query current lot activity for enabled Receiving truck assets and list lots with positive quantity still at those trucks. An operator selects a lot and a destination tank to retry. Re-selecting the destination after reopening is required because the intended tank is not recorded until the transfer succeeds.

**Rationale**: `getLotActivity` supports asset, work-order, lot, and `hasQty` filters and reports current quantities by location. The docs do not describe a native pending-transfer state. This avoids a custom tracking table and makes recovery available after a session ends.

**Alternatives considered**:

- Keep retry information only in Perspective session/view state: rejected because it is lost when the session ends.
- Add custom pending-transfer tables: rejected because lot activity already provides current inventory and the constitution disallows taking ownership of inventory data without need.
- Treat every lot at a truck as a failed transfer automatically: rejected; the UI must label these as lots at trucks/pending movement and require operator selection so unrelated truck stock is not moved accidentally.

**Sources**: `../../../kanoa-docs/docs.kanoa.ai/systemFunctions/lot/getLotActivity.md`; `../../../kanoa-docs/docs.kanoa.ai/training/training-trace/lot-screens/lot-functions.md`.

## Decision 5: Keep custom code within existing Ignition ownership boundaries

**Decision**: Put Perspective views in runnable `kanoaMES`; put reusable client-specific Gateway functions in `KANOA_SCRIPTS`; register views through Kanoa's Application Navigation configuration with project/role scoping.

**Rationale**: Kanoa's custom lot screen guide imports views into `kanoaMES` and registers them through the Navigation screen. The project constitution assigns shared/client logic to `KANOA_SCRIPTS` and prohibits client changes in `kanoaAPP`. Existing script packages use a `code.py` and `resource.json` structure.

**Alternatives considered**:

- Edit `kanoaAPP` screens: rejected because it is vendor-managed and must not be patched.
- Place all receiving business logic in view event handlers: rejected because the same validation and operation handling is needed by schedule, receipt, and recovery actions; keep handlers focused on user interaction and call reusable functions.

**Sources**: `../../.specify/memory/constitution.md`; `../../../kanoa-docs/docs.kanoa.ai/training/training-trace/lot-screens/custom-lot-screens.md`; `../../../kanoa-docs/docs.kanoa.ai/configuration/navigation.md`; `../../services/ignition/projects/KANOA_SCRIPTS/ignition/script-python/kanoaScripts/custom/ops/lots/resource.json`.

## Decisions carried as implementation gates

- Confirm exact order description and target quantity fields and status values from the pinned KanoaMES order query; API documentation does not enumerate its return columns.
- Confirm schedule blocks intended for receiving can be distinguished from other scheduled activities in local order/config data.
- Confirm the lot event UOM fields and whether all eligible receiving orders use kg. No supported conversion function was found in the local API references reviewed.
- Confirm the selected order remains eligible and cumulative quantity is checked safely when two receiving sessions submit concurrently. This plan uses the recommended policy: recheck at commit time and reject the stale submission. Serialize the critical section per `workOrderId` within the Gateway receiving flow; verify scope and failure behavior before implementing. External writes outside this flow must be restricted or treated as a remaining limitation.
- Confirm `getLotActivity` results can be queried across each enabled truck and identify order/material/quantity fields needed by the recovery list.
- Confirm navigation configuration can be reproduced/exported under the repository's configuration source-of-truth rules.

No unresolved product requirement is intentionally changed by these checks; they validate the installed API and runtime behavior before implementation.
