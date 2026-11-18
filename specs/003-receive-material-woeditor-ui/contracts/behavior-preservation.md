# Contract: Receiving Behavior Preservation

**Feature**: `specs/003-receive-material-woeditor-ui/`
**Source of truth**: `specs/001-operator-receiving/spec.md` and the shared receiving module
`services/ignition/projects/KANOA_SCRIPTS/ignition/script-python/kanoaScripts/custom/ops/receiving/code.py`

## Purpose

This refactor changes presentation and navigation parameters only. This contract records the
behavior that must remain identical, the integration points that must not move, and the evidence
required to prove no regression.

## Frozen Integration Points

| Capability | Existing entry point | Change allowed |
|---|---|---|
| Load/refresh order and eligibility | `kanoaScripts.custom.ops.receiving.getReceivingOrder` | None |
| Load truck/tank lists | `kanoaScripts.custom.ops.receiving.getReceivingAssets` | None |
| Cumulative received kg | `kanoaScripts.custom.ops.receiving.getReceivedQtyForOrder` | None |
| Confirm receipt + transfer | `kanoaScripts.custom.ops.receiving.receiveOrder` | None |
| Receipt confirmation popup | `kanoa/core/templates/inputs/confirm` + `confirmReceiveOrder` handler | Reused as-is; message text may name the order/quantity |
| Pending transfer list and retry | `getPendingTransfers` / `retryTransfer` + `training/pendingTransfers` | None on this screen |
| Kanoa shell | `/receiving` page docks from feature 002 | None |

No edit is permitted in `KANOA_SCRIPTS` or `kanoaAPP` for this feature. The receiving module's
method signatures and result statuses are the contract.

## Frozen Rules

1. **Eligibility** — Only orders with status `Scheduled` or `In Progress` may be received. The order
   is reloaded immediately before the write.
2. **Unit** — The order's `itemUnitName` must be `kg`. Receipt history containing any other unit
   blocks receiving.
3. **Quantity** — The actual quantity must be finite, greater than zero, and no greater than
   `targetQty − cumulative received kg`. No over-receipt tolerance.
4. **Assets** — The truck must be an enabled `Storage Location` under `Training Plant\Receiving`; the
   tank must be an enabled `Storage Location` under `Training Plant\Bulk Storage`. Both are reloaded
   and revalidated at confirmation.
5. **Receipt** — Exactly one `Receive` output lot event is created for the entered quantity, at the
   selected truck, with a Kanoa-allocated lot name.
6. **Transfer** — The receipted lot is transferred from the truck to the selected tank. If the
   transfer fails, the receipt is preserved and the lot remains at the truck.
7. **Idempotency** — Repeated activation, slow responses, retries, and concurrent attempts must not
   create a second receipt. The screen prevents duplicate submission; the API also locks per order
   and reconciles uncertain outcomes.
8. **Uncertain outcomes** — An uncertain receipt or transfer returns a reconciliation status and an
   actionable message; the screen must not invite a blind retry.
9. **Recovery** — Pending transfers are recovered only on `training/pendingTransfers`, never on this
   screen.
10. **Back** — Leaving the screen creates, changes, and transfers nothing.

## Screen Behavior Contract

| Scenario | Required result |
|---|---|
| Open with no order | Clear message plus a Back path to the schedule; Confirm disabled. |
| Open a new order | Six fields populate; actual quantity equals the full target. |
| Open a partially received order | Actual quantity equals the outstanding quantity. |
| Order becomes ineligible while open | Confirmation is rejected with an actionable message; no write. |
| Quantity missing, zero, negative, non-numeric, or over remaining | Blocked before any write; actionable message. |
| Truck or tank missing | Blocked before any write; actionable message. |
| Truck or tank disabled/moved before confirmation | `receiveOrder` rejects; no write; operator reselects. |
| Valid confirmation | One receipt and one transfer; success identifies order, lot, quantity, truck, and tank. |
| Double-click / repeated Confirm | One receipt and one transfer only. |
| Transfer fails after receipt | Receipt preserved; message states material remains at the truck and points to Pending Transfers. |
| Back | Returns to `training/receivingOrdersSchedule`; no record created or changed. |
| Long notes / missing notes | Long notes wrap without breaking layout; missing notes show an explicit empty value. |
| Missing schedule date | Field shows `"Unavailable"`. |

## Acceptance Mapping

| Requirement | Contract section | Evidence |
|---|---|---|
| FR-001–FR-006 | Component contract: read-only field contract, presentation acceptance | Visual review against `woEditor` |
| FR-007–FR-009, FR-013 | Selector contract; frozen rules 4 | Selector walkthrough and invalid-selection tests |
| FR-010–FR-012, FR-014 | Actual quantity contract; frozen rules 2–3 | New/partial/invalid quantity tests |
| FR-015–FR-019 | Frozen rules 5–8 | Receipt, duplicate, and transfer-failure tests |
| FR-020–FR-022 | Action contract; frozen rules 9–10 | Button audit, Back test, 001 regression pass |
| FR-023–FR-025 | Kanoa-first declaration; frozen integration points | File diff review and kg unit check |

## Verification Gate

The change is not complete until `quickstart.md` scenarios pass on the running Gateway and the diff
confirms that no file under `kanoaAPP` or `KANOA_SCRIPTS` changed. Any discovered need to modify a
shared method or add a component requires renewed Principle VI approval before implementation
continues.
