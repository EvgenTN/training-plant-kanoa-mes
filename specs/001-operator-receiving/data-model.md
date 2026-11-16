# Data Model: Operator Bulk Receiving

This feature uses Kanoa-managed orders, schedule blocks, lots, lot events, operations, assets, items, serial definitions, and item units. It adds no inventory tables or independent lot records.

## Entities

### Receiving Order

Represents the scheduled request to receive a raw material.

| Attribute | Meaning | Validation / use |
|---|---|---|
| Work order ID | Stable identity used to reload and associate the receipt | Required; selected from a scheduled block; reloaded immediately before posting |
| Order number | Operator-facing business identifier | Read-only |
| Status | Order lifecycle state | Only `Scheduled` or `In Progress` is eligible |
| Description | Order-level explanation | Read-only; fallback to item description if empty |
| Item/material | Material being received | Read-only; lot item must match |
| Target quantity and unit | Planned amount | Read-only; eligible order must be comparable to kg |

Relationship: one receiving order may have multiple partial receipt lots. Cumulative `Receive` output quantity for its work order must not exceed target.

### Schedule Block

Represents the time-window entry used to offer the order for selection.

| Attribute | Meaning | Validation / use |
|---|---|---|
| Schedule block ID | Identity for the scheduled entry | Retained to identify the selected entry |
| Work order ID/name | Associated receiving order | Required to open the order; the order is reloaded canonically |
| Start/end time | Scheduled window | Used for schedule display and filtering |
| Item and scheduled quantity | Summary information | May be used in the schedule row; receipt form uses reloaded order data |

### Receipt Lot

Represents one inbound delivery and its traceable inventory identity.

| Attribute | Meaning | Validation / use |
|---|---|---|
| Lot ID/name | Unique Kanoa lot identity | Generated using the configured serial; stable across transfer retry |
| Item ID | Material identity | Must equal the selected order item |
| Quantity/unit | Actual delivery quantity | Positive; recorded in kg; included in cumulative order receipt check |
| Work order ID | Receiving order association | Required on the Receive event |
| State | Inventory state at receipt | Use configured initial receiving state (`OK` in current solution design) |
| Receive event | Receipt operation output event | Output at selected receiving truck; keeps order association |

### Receiving Asset and Destination Tank

Both are enabled Kanoa Storage Locations, scoped by the exported Training Plant hierarchy.

| Entity | Allowed path scope | Use |
|---|---|---|
| Receiving truck | `Training Plant\\Receiving\\*` | Location where the Receive output is recorded |
| Destination tank | `Training Plant\\Bulk Storage\\*` | Location where the Transfer output is recorded |

Asset names are display values. Resolve current asset IDs from the configured hierarchy and revalidate path, type, and enabled state before writes.

### Transfer

Represents moving the same receipt lot from the selected truck to the chosen tank.

| Attribute | Meaning | Validation / use |
|---|---|---|
| Lot ID | Existing receipt lot being moved | Must already have positive quantity at the selected truck |
| Input location/quantity | Quantity consumed from truck | Must not exceed available quantity |
| Output location/quantity | Quantity added to tank | Same lot and quantity for this simple transfer |
| Work order ID | Business order association | Preserve from the receipt lot/event |
| Operation outcome | Completion or failure of movement | Transfer failure leaves the lot at the truck for recovery |

### Pending Transfer (derived view state)

Not a separate Kanoa entity. It is a lot with positive current quantity at a Receiving truck, offered for operator review and movement to a tank. It may include material that has not yet been transferred as part of this workflow; the screen must show the current truck and ask the operator to select/confirm the destination. On reopening, destination tank is selected again because the failed transfer never recorded it.

## State Transitions

```text
Scheduled / In Progress Order
          │ operator confirms selection
          ▼
       Selected Order
          │ quantity and assets validated; Receive succeeds
          ▼
    Lot at Receiving Truck
       │              │
       │ Transfer      │ transfer failure/session closes
       ▼              ▼
   Lot at Tank    Pending Transfer
                      │ operator selects lot and tank; retry Transfer
                      └──────────────────────────────► Lot at Tank
```

Before transitioning from selected order to a new receipt, recompute the total of enabled Receive output events for the work order, normalize units, and ensure `prior received + proposed actual <= target`. The per-order receive critical section must serialize simultaneous submissions from this workflow. A transfer retry uses the existing lot and does not repeat lot creation or Receive.

## Data Integrity Rules

1. Canonical order status, item, quantity, and unit are reloaded before writes; schedule-row display values are not trusted for posting.
2. Lot name/serial, item, unit, order, truck, quantity, and initial state are validated before the receipt is written.
3. Receive and Transfer are separate committed operations. Their returned IDs/messages and resulting lot location must be checked independently.
4. Failed or uncertain calls must not be blindly replayed. Reconcile using Kanoa lot events and current lot activity; if outcome cannot be established, require operator/admin reconciliation.
5. Lot activity at trucks is a derived recovery list, not an explicit pending state. List items must be refreshed before transfer and validated against current availability.
