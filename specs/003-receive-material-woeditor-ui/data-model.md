# Data Model: Receive Material Work Order Editor Refactor

**Feature**: `specs/003-receive-material-woeditor-ui/spec.md`
**Date**: 2026-11-18

This is a presentation refactor. It adds no tables, columns, or persisted entities. The model below
describes (a) the display projection the screen renders, (b) the view-local state that drives the
controls, and (c) the existing receiving entities whose rules must be preserved. Source paths are
shown so implementation can bind directly to the existing APIs.

## 1. Receiving Order (display projection)

The canonical Kanoa production order, projected for read-only display. Source:
`system.kanoa.order.getProductionOrders({'workOrderId': <id>, 'ignoreActualQty': True})`, plus the
existing `getReceivingOrder` summary.

| Field | Source column / expression | Screen label | Rules |
|---|---|---|---|
| `workOrderId` | `workOrderId` | — | Required to load the order; never displayed. |
| `orderNumber` | `workOrderName` | Order # | Required; empty renders as `"—"`. |
| `title` | `workOrderTitle`, fallback `itemDescription` | Title | FR-003 fallback; empty renders as `"—"`. |
| `targetQty` | `reqdQty` | Target Qty | Numeric; must be > 0 for receiving; displayed with `kg` unit from `itemUnitName`. |
| `scheduledStart` | schedule row `startDate` (fallback `scheduledStart`), passed in navigation params | Schedule Date | FR-004; null renders as `"Unavailable"`. |
| `status` | `workOrderStatusName` | Status | Must be `Scheduled` or `In Progress`; otherwise the order is not eligible. |
| `notes` | schedule row `note`, passed as `orderNotes`; native `getProductionOrders` fallback on direct open | Notes | FR-005; null/empty renders as `"—"`; long text wraps. |

Validation rules:

- The order must still exist and be `Scheduled` or `In Progress` when the screen loads and again
  immediately before the receipt is written (enforced by `receiveOrder`).
- `itemUnitName` must be `kg`; otherwise receiving is blocked (enforced by
  `getReceivedQtyForOrder` / `receiveOrder`).
- `targetQty` must be finite and greater than zero; otherwise the quantity field and Confirm are
  disabled with an explanation.
- No field in this projection is writable from this screen.

## 2. View-Local State (`training/receiveMaterial` custom properties)

| Property | Type | Initial | Purpose |
|---|---|---|---|
| `order` | object | `null` | Display projection from `getReceivingOrder` / navigation params. |
| `scheduledStart` | datetime | `null` | Schedule date passed from the schedule screen (`startDate`). |
| `orderNotes` | string | `null` | Order notes passed from the schedule row, with native `getProductionOrders` fallback. |
| `receivedQtyKg` | number | `0` | Cumulative kg received from `getReceivedQtyForOrder`. |
| `actualQtyKg` | number | `null` | Outstanding quantity by default; operator-editable. |
| `truckAssetId` | integer | `null` | Selected Receiving Storage Location ID. |
| `truckPath` | string | `null` | Selected truck path, bound to the selector. |
| `tankAssetId` | integer | `null` | Selected Bulk Storage Storage Location ID. |
| `tankPath` | string | `null` | Selected tank path, bound to the selector. |
| `truckOptions` | array | `[]` | Existing `getReceivingAssets` truck list; drives the empty-state message. |
| `tankOptions` | array | `[]` | Existing `getReceivingAssets` tank list; drives the empty-state message. |
| `loading` | boolean | `false` | Blocks interaction while loading/submitting. |
| `submitting` | boolean | `false` | Prevents duplicate Confirm submissions. |
| `errorMessage` | string | `""` | Drives the error toast/popup. |
| `result` | object | `null` | Drives success/pending feedback. |

State transitions:

```text
idle
  -> loading                     (onStartup)
  -> ready                       (order, assets, history loaded; actualQtyKg defaulted)
  -> ready-with-error            (any load failure; Confirm disabled where applicable)
  -> confirming                  (Confirm pressed; submitting = true)
  -> success                     (receipt + transfer recorded)
  -> transfer-pending            (receipt recorded, lot remains at truck)
  -> ready                       (validation or receipt failure; operator may correct)
```

The screen never returns from `success` to an editable state; the operator leaves via Back or the
Kanoa navigation. `transfer-pending` is terminal for this screen and directs the operator to
`training/pendingTransfers`.

## 3. Receiving Asset (truck station)

An enabled Kanoa asset of type `Storage Location` under `Training Plant\Receiving`. Source:
`system.kanoa.asset.getAssets({'assetPath': 'Training Plant\\Receiving\\%',
'assetTypeName': 'Storage Location', 'enabled': True})`.

| Field | Use |
|---|---|
| `assetId` | Stored in `view.custom.truckAssetId`; passed to `receiveOrder`. |
| `assetName` | Display/tooltip only. |
| `assetPath` / `path` | Tree hierarchy key; bound to `view.custom.truckPath`; shown as selected path. |
| `enabled` | Must remain `True` at confirmation. |
| `assetTypeName` | Must remain `Storage Location`. |

Rules:

- FR-007: only enabled Storage Locations in the Receiving area may be selected.
- A synthetic tree branch/folder selection (no `assetId`) is rejected on the screen.
- `receiveOrder` reloads the asset and re-checks `enabled`, `assetTypeName`, and base path
  `Training Plant\Receiving` before writing.

## 4. Destination Tank

An enabled Kanoa asset of type `Storage Location` under `Training Plant\Bulk Storage`. Source:
`system.kanoa.asset.getAssets({'assetPath': 'Training Plant\\Bulk Storage\\%',
'assetTypeName': 'Storage Location', 'enabled': True})`.

Fields and rules mirror §3 with base path `Training Plant\Bulk Storage`, stored in
`view.custom.tankAssetId` / `tankPath`, and revalidated by `receiveOrder` (FR-008, FR-013).

## 5. Receipt

The operator-confirmed kg quantity recorded against one order at one truck. Created only by
`kanoaScripts.custom.ops.receiving.receiveOrder`, using
`system.kanoa.lot.executeLotOperation` with a `Receive` output event.

| Attribute | Rule |
|---|---|
| `workOrderId` | Must be an eligible order. |
| `qtyKg` | Finite, > 0, and ≤ `targetQty − receivedQtyKg` (FR-012, FR-014). |
| `truckAssetId` | Must be an enabled Receiving Storage Location. |
| `tankAssetId` | Must be an enabled Bulk Storage Storage Location; used by the transfer. |
| `lotName` | Allocated by `system.kanoa.serial.getNextSerialNumber`. |
| `userId` | Authenticated session user's Kanoa user ID. |

Exactly one receipt is created per successful confirmation. Duplicate activation is prevented on the
screen (`submitting`) and in the API (per-order lock plus reconciliation checks) — FR-016, SC-006.

## 6. Lot

The traceable inventory identity created for the receipt. The lot is created at the truck, retains
its identity through the transfer, and carries the received kg quantity. If the transfer fails, the
lot remains at the truck and appears on the Pending Transfers screen. The screen never edits lot
attributes.

## 7. Transfer

The movement of the received lot from the truck to the destination tank. Performed inside
`receiveOrder` through the existing transfer helper and Kanoa lot APIs.

| Outcome | Meaning | Screen behavior |
|---|---|---|
| `SUCCESS` | Lot moved to the tank. | Show success toast/result identifying order, lot, quantity, truck, and tank (FR-017). |
| `TRANSFER_PENDING` | Receipt recorded; lot remains at the truck. | Explain that material remains at the truck and direct the operator to Pending Transfers (FR-019). |
| Validation / reconciliation error | No transfer, or outcome uncertain. | Show an actionable message; never create a second receipt (FR-018). |

## 8. Pending Transfer

A received lot that remains at a Receiving truck after a failed transfer. It is read by
`getPendingTransfers` and recovered on `training/pendingTransfers`; this feature does not expose a
Pending or Retry action on the Receive Material screen (FR-020).

| Attribute | Use |
|---|---|
| `lotId` / `lotName` | Identifies the stranded lot. |
| `assetId` / `assetPath` | Shows the truck holding the material. |
| Quantity at truck | Determines transferable quantity. |
| Destination tank | Selected on the Pending Transfers screen. |

## Relationships

```text
Receiving Order 1 ── * Receipt
Receipt         1 ── 1 Lot
Lot             1 ── 0..1 Transfer
Transfer        0..1 Pending Transfer   (when the transfer has not completed)

Receiving Asset (truck) 1 ── * Receipt
Destination Tank        1 ── * Transfer
```

## Invariants

1. No write occurs from this screen except through `receiveOrder`.
2. Displayed order fields are never writable.
3. `actualQtyKg` is always expressed in kg and cannot exceed the outstanding quantity.
4. A truck and tank must come from their required areas and remain enabled at confirmation.
5. One confirmation produces at most one receipt and one transfer.
6. A failed transfer never deletes the receipt; recovery happens only on Pending Transfers.
