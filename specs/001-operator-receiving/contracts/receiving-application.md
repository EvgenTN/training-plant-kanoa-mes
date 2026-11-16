# Receiving Application Contract

This is an internal contract between Perspective views in `kanoaMES` and reusable Gateway functions in `KANOA_SCRIPTS`; it is not an external HTTP API. Names below are proposed function boundaries, not existing code. Confirm exact result fields against the pinned KanoaMES release during the API spike.

## Shared Result Shape

Gateway calls return a serializable dictionary:

| Field | Meaning |
|---|---|
| `status` | `SUCCESS`, `VALIDATION_ERROR`, `NOT_ELIGIBLE`, `RECEIPT_FAILED`, `TRANSFER_PENDING`, `TRANSFER_FAILED`, or `RECONCILIATION_REQUIRED` |
| `message` | Operator-safe explanation of outcome or next action |
| `data` | Action-specific display and recovery fields; empty when not applicable |

Do not pass Java datasets, exception objects, or internal stack traces directly to Perspective components. Query results are shaped into the minimum display/action fields. Gateway logs hold diagnostic detail.

## Read Operations

### `getScheduledReceivingOrders(startDate, endDate)`

Returns scheduled blocks in the requested date range whose linked canonical order is eligible. Each row includes schedule block ID, work order ID/name, scheduled start/end, material, and target quantity/unit when available. Use the stable work order ID for navigation; reload canonical order data after the operator confirms selection.

### `getReceivingOrder(workOrderId)`

Returns canonical order values: ID, number/name, status, description, item/material identity, target quantity and unit, cumulative received quantity, and remaining quantity. Description is the order description or item description fallback. If the order is no longer `Scheduled` or `In Progress`, return `NOT_ELIGIBLE` and a user-facing reason.

### `getReceivingAssets()`

Returns enabled Storage Locations under `Training Plant\\Receiving` as trucks and under `Training Plant\\Bulk Storage` as tanks. Each option includes ID, display name, and full path. Mutations revalidate each selection.

### `getPendingTransfers()`

Returns lots with positive current quantity at configured Receiving truck assets, from Kanoa lot activity. Each row includes lot ID/name, item/material, work order when present, available quantity/unit, and current truck. This is current inventory, not a persisted pending state. The operator must select a destination tank before a retry.

## Write Operations

### `receiveOrder(workOrderId, actualQtyKg, truckAssetId, tankAssetId, authUser)`

Revalidates the order, assets, item, unit, serial and operation configuration; obtains the authenticated Kanoa user ID; serializes receiving submissions for the same work order within the receiving flow; recalculates cumulative Receive output quantity; and rejects stale or over-target quantities before writes. It obtains the next configured serial and uses the output event's new `lotName` and `itemId` fields to create the lot and record a no-input/one-output Receive at the selected truck in one `executeLotOperation` call. It then records a separate Transfer to the selected tank. Verify each returned operation ID/message and current location before reporting success. Confirm new-lot output support on KanoaMES 1.15.11 before implementation; if unavailable, use the documented `addLot` then Receive sequence and add explicit orphan-lot recovery.

Result `data` on success includes order number, lot ID/name, quantity, truck, tank, and Receive/Transfer event IDs. If Receive succeeds but Transfer does not, return `TRANSFER_PENDING` with the existing lot and truck; do not hide the committed receipt or automatically create a second one.

### `retryTransfer(lotId, tankAssetId, authUser)`

Revalidates positive available quantity at a Receiving truck and the selected tank, then transfers only the existing lot. It never allocates a serial, adds a lot, or repeats Receive. Success includes lot, quantity, source truck, destination tank, and Transfer event ID. Failure leaves the lot available at the truck for later recovery.

## Interaction Rules

- Order details are read-only once selected.
- Disable confirmation while a write is in flight.
- Distinguish `RECEIPT_FAILED`, `TRANSFER_PENDING`, full `SUCCESS`, and `RECONCILIATION_REQUIRED` outcomes.
- A retry after reopening reloads current Kanoa activity; destination tank must be selected again.
- An ambiguous write is checked against Kanoa history/activity. If state is inconclusive, stop and request reconciliation rather than replaying receipt.
