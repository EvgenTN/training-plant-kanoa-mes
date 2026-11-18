# Quickstart: Validate the Receive Material Refactor

**Feature**: `specs/003-receive-material-woeditor-ui/`
**Scope**: Local Training Plant Ignition Gateway only. Do not run this against production or a
seeded/reset database.

This is a validation guide. Component and binding details live in
[contracts/component-contracts.md](contracts/component-contracts.md); receiving rules live in
[contracts/behavior-preservation.md](contracts/behavior-preservation.md); display fields and state
live in [data-model.md](data-model.md).

## Prerequisites

- Docker Compose stack and local Ignition Gateway are running (`docker compose ps`).
- `kanoaMES` is loaded by the Gateway and the edited `training/receiveMaterial` view is saved and
  deployed through the normal Ignition project workflow.
- The feature 001 navigation entries exist and an operator account can open
  **Receiving → Receive Material**.
- At least one order is `Scheduled` or `In Progress` with an item, a target quantity in kg, and a
  schedule entry.
- The Training Plant hierarchy contains enabled `Storage Location` assets under
  `Training Plant\Receiving` and `Training Plant\Bulk Storage`.
- Kanoa receiving configuration is intact: `Receive` and `Transfer` operations, initial lot state,
  kg item unit, and lot serial.
- An order with a prior partial receipt is available (or create one with a small first receipt) to
  test the outstanding-quantity default.

Do not restart, reseed, or reset the stack for this validation. Use existing data where possible.

## 0. Structural Checks

From the repository root:

```bash
python3 -m json.tool \
  services/ignition/projects/kanoaMES/com.inductiveautomation.perspective/views/training/receiveMaterial/view.json \
  > /dev/null

python3 -m json.tool \
  services/ignition/projects/kanoaMES/com.inductiveautomation.perspective/views/training/receivingOrdersSchedule/view.json \
  > /dev/null

git diff --name-only | grep -E 'kanoaAPP|KANOA_SCRIPTS' || true
```

**Expected**: Both JSON files parse. The last command prints nothing, proving no vendor or shared
script file changed.

Confirm the screen exports contain no new view resources and the changed paths are limited to the two
files above:

```bash
git status --porcelain
```

## 1. Order Fields Are Read-Only and Canonical

1. Open **Receiving Orders Schedule**, select an eligible order, and continue to Receive Material.
2. Compare the six fields with the canonical order in Kanoa (or with `woEditor` opened on the same
   order):
   - Order #
   - Title
   - Target Qty (with `kg`)
   - Schedule Date
   - Status
   - Notes
3. Try to type in, focus, or otherwise edit each value.

**Expected**: All six values match the canonical order. None accepts focus or editing, and no edit
action is present. Layout labels are right-aligned and rows are evenly spaced like `woEditor`.

4. Repeat with an order whose title is empty and an order whose notes are empty.

**Expected**: Title shows the item description; empty notes show `"—"`. No field shows a blank that
could be mistaken for missing data.

5. Open an order whose schedule date is unavailable (for example by opening the view directly with
   only `workOrderId`).

**Expected**: Schedule Date shows `"Unavailable"`.

## 2. Asset Selectors

1. Open the truck selector.
2. Browse and search the hierarchy, select a truck, clear it, and select again.
3. Open the tank selector and repeat.

**Expected**:

- Both selectors use the same hierarchy popup, breadcrumb, search, clear, and single-select
  interaction as the `woEditor` item selector.
- The truck selector only offers assets under `Training Plant\Receiving`; the tank selector only
  offers assets under `Training Plant\Bulk Storage`.
- Only enabled `Storage Location` leaves are selectable. Selecting a folder (area/site) is discarded
  with an actionable message.
- The selected path is visible in the control.

4. If an area has no eligible assets, open its selector.

**Expected**: The screen shows an explanation that no eligible assets are available rather than a
silent empty list.

5. Select a truck and tank, then disable or move one of them in Kanoa before confirming.

**Expected**: Confirmation is rejected with an actionable message and no receipt is created.

## 3. Actual Quantity Default

1. Open an order with no prior receipts.

**Expected**: Actual quantity equals the full target quantity.

2. Open an order that already has a partial receipt.

**Expected**: Actual quantity equals `target − cumulative received kg`.

3. Edit the quantity, then cause the screen to re-render (for example resize the browser).

**Expected**: The operator's edit is preserved; the default is only applied on startup.

## 4. Invalid Quantity and Selection

Submit each of the following:

- Quantity blank
- Quantity `0`
- Negative quantity
- Non-numeric text (if the field accepts it)
- Quantity greater than the outstanding quantity
- No truck selected
- No tank selected

**Expected**: Each attempt shows an actionable Kanoa message and creates no lot, Receive event, or
Transfer. The Confirm action is disabled while a submission is in progress.

## 5. Valid Confirmation

1. Select a valid order, truck, tank, and a quantity within the outstanding amount.
2. Press Confirm and accept the confirmation dialog.
3. Inspect the result message and Kanoa lot history / Lot Manager.

**Expected**:

- Exactly one new lot and Receive output event are associated with the order and truck.
- A Transfer moves the same lot and quantity to the selected tank.
- The result identifies the order, lot, quantity, truck, and tank.
- No Pending or Retry button exists on this screen.

4. Return to the same order and confirm the outstanding quantity reflects the receipt.

## 6. Duplicate-Submission Guard

1. Press Confirm and double-click the confirmation action, or submit twice in quick succession on a
   slow response.
2. Inspect Kanoa lot history for the order.

**Expected**: Only one receipt and one transfer are recorded. Subsequent feedback explains that the
submission was already handled or reloads the outstanding quantity.

## 7. Transfer Failure Hand-off

Use the documented non-destructive simulation to force a transfer failure after the receipt succeeds.

**Expected**:

- The receipt remains recorded; the lot remains at the truck.
- The message states that the material remains at the truck and directs the operator to the
  **Pending Transfers** screen.
- No Retry action exists on Receive Material.
- Opening **Pending Transfers** shows the stranded lot and allows recovery there.

## 8. Back Behavior

1. Change the quantity and select different assets.
2. Press Back.

**Expected**: The Receiving Orders Schedule opens. No receipt, lot, event, or transfer was created or
changed.

## 9. Theme and Width

1. Open the screen in each supported Kanoa theme.
2. Reduce the browser width until the layout is constrained.

**Expected**: All six fields, both selectors, the quantity input, and both actions remain readable
and reachable. Notes wrap without breaking the layout. No hard-coded color appears.

## 10. Feature 001 Regression

Rerun the acceptance scenarios from `specs/001-operator-receiving/quickstart.md` that apply to
receiving, especially:

- Eligible-order filtering and refusal of ineligible orders.
- Cumulative target enforcement (no over-receipt).
- Concurrent submission behavior.
- Pending transfer recovery on its own screen.
- Uncertain-outcome handling and logs.

**Expected**: All previously passing behavior still passes. Any regression is a release blocker for
this feature.

## Release Evidence

Record:

- Gateway build/version and operator role.
- Order ID and canonical values for the six fields.
- Default quantity for both a new and a partially received order.
- Selected truck/tank paths and the rejected out-of-area attempt.
- Lot name, Receive event, Transfer event, quantity, and result message for the valid receipt.
- Duplicate-submission outcome.
- Transfer-failure message and Pending Transfers recovery evidence.
- `git diff --name-only` proof that `kanoaAPP` and `KANOA_SCRIPTS` were not modified.

Leave the feature unregistered for operators until all scenarios above pass on the running Gateway.
