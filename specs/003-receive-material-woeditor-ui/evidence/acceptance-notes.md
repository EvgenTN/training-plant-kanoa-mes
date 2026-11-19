# Gateway Acceptance Evidence — Spec 003

**Run dates**: 2026-11-18 (initial) and 2026-11-19 (post-fix revalidation)
**Gateway**: Ignition Standard `8.3.10 (b2026100610)`, local project `kanoaMES`
**Session**: Perspective admin session; Kanoa user `admin` with Administrator role
**Loading**: Gateway Projects → **Scan File System**, plus two restarts of only
`training-plant-kanoa-mes_kanoa_1` (explicitly approved) because file scanning alone did not
reload Perspective view definitions. The database was not reseeded or reset. The trial timer was
renewed through the Gateway **Reset Trial** UI.
**Runtime prerequisite**: Kanoa Serialization UI gained enabled serial definition `Receiving`,
prefix `RCV`, zfill `4` (runtime configuration only; no repository diff).

## Scope and structural audit

- `python3 -m json.tool` passed on both changed view exports.
- All embedded `script`/`code` strings compile as Python when wrapped in a function body: 8 scripts
  in `receiveMaterial/view.json`, 22 in `receivingOrdersSchedule/view.json`.
- `python3 -m py_compile` passed on the edited
  `services/ignition/projects/KANOA_SCRIPTS/ignition/script-python/kanoaScripts/custom/ops/receiving/code.py`.
- Two approved changes sit outside the two view files:
  - `'enabled': True` was removed from the two `system.kanoa.lot.getLotEvents` calls in
    `KANOA_SCRIPTS/.../custom/ops/receiving/code.py` (`getReceivedQtyForOrder` and
    `checkReceiptAttempt`).
  - The Ignition `lastModificationSignature` in `receiveMaterial/resource.json` was recomputed so
    the edited view definition is reloadable.
  No other `kanoaAPP`/`KANOA_SCRIPTS` file changed.
- No new Perspective view, template, function, module, helper, wrapper, table, or SQL was added.
- Unrelated working-tree changes were left untouched:
  `.specify/scripts/python/__pycache__/common.cpython-315.pyc`, `docker-compose.yaml`,
  `services/ignition/config/resources/core/ignition/tag-provider/kanoaMES/config.json`,
  `.../resource.json`, `services/ignition/config/resources/core/ignition/translations/resource.json`,
  and untracked `services/ignition/config/ignition/`.

## US1 — Canonical read-only order fields

- Evidence: `us1-order-fields.png`, `reference-wo-editor.png`.
- Order 1 canonical values: `RCV000001`, `RCV Corn Syrup`, `20,000 kg`,
  `11/18/2026 10:00`, `Scheduled`, and supplied note text.
- All six fields rendered as `ia.display.label` values; no input accepted focus or editing.
- Empty notes rendered as `—`; a direct open with no schedule date rendered `Unavailable`.
- Title fallback and status rendering matched `kanoa/mes/workOrders/woEditor`.
- Ineligible/nonexistent order 999 produced:
  `This receiving order no longer exists. Refresh the schedule.`; Confirm was disabled.

## US2 — Native Kanoa tree selectors

- Truck options: `TRUCK01` id `15`, `TRUCK02` id `16`, under
  `Training Plant\Receiving`.
- Tank options: `TK101` id `12`, `TK102` id `13`, `TK103` id `14`, under
  `Training Plant\Bulk Storage`.
- Browse, expand, search, clear, single-select, breadcrumb, and selected-path display were
  exercised in the inherited `kanoa/core/templates/selectors/tree/selector` popup.
- Folder selection was rejected with `Select a Storage Location, not a folder.`
- Selecting a tank id as the truck was rejected with a validation message.
- A stale truck asset id `9999` was rejected with:
  `The selected truck or tank is no longer eligible. Refresh the asset lists.`
  Order 4 remained at 6 lot events after the attempt, proving no write.

## US3 — Quantity, validation, receipt, duplicate guard, hand-off

- In this headless client, `ia.input.numeric-entry-field` renders the same read-only DOM as the
  `woEditor` reference. Operator-entered values were therefore exercised through the bound
  `view.custom.actualQtyKg` property, which is the same value the bidirectional binding writes.
- New-order default: order 1 → `20,000`.
- Partial-receipt default after the fixes: order 3 (target `11,000`) showed `receivedQtyKg: 100`,
  `actualQtyKg: 10,900`, `errorMessage: ''`; after the valid `100 kg` receipt below it showed
  `receivedQtyKg: 200`, `actualQtyKg: 10,800`.
- Edit preservation: setting order 3 to `1,234`, then forcing re-render/resize, retained `1,234`.
- Invalid matrix against the real Confirm path produced no DB writes:
  - blank → client-side "Enter an actual quantity and select a receiving truck and destination tank."
  - `0` and negative → `Actual quantity must be greater than zero kg.`
  - nonnumeric → `Enter a positive receipt quantity and select an order, truck, and tank.`
  - over outstanding → `Quantity exceeds the remaining order target of 20000.0 kg.`
  - missing truck or tank → client-side selection message.
  - stale/wrong-area asset → `VALIDATION_ERROR`.
- Valid confirmation on order 3 (`100 kg`, truck `TRUCK01` id `15`, tank `TK101` id `12`):
  result `SUCCESS` / `Transfer completed.`; lot `RCV0009`, lotId `8`,
  receiveOperationEventId `15`, transferOperationEventId `16`, DB lotEventIds `22`/`23`/`24`.
- Over-receipt rejection on order 3: attempting `11,000 kg` against a `10,800 kg` remainder returned
  `VALIDATION_ERROR`: `Quantity exceeds the remaining order target of 10800.0 kg.` The DB event
  count stayed at 6, proving no write.
- The duplicate guard is implemented in the existing `confirmReceiveOrder` handler in the allowed
  view file: a per-session/per-view `RLock` from `system.util.getGlobals()` plus a terminal-result
  guard for `SUCCESS`/`TRANSFER_PENDING`. A valid double-clicked confirmation earlier produced
  exactly one receipt and transfer pair (lot `RCV0006`, lotId `5`, `100 kg`, truck `TRUCK01`,
  tank `TK101`, lotEventIds `13`/`14`/`15`). The handler is byte-for-byte unchanged by the
  2026-11-19 startup-event relocation (confirmed by `git diff`), so this evidence still applies.
- Pre-fix duplicate tests (before the guard) created two receipts on order 1 (`RCV0002`,
  `RCV0003`, lotEventIds `1`–`6`) and order 2 (`RCV0004`, `RCV0005`, lotEventIds `7`–`12`).
  These remain in the local database as test evidence and were not cleaned.
- Back: changing quantity/assets and pressing Back navigated to
  `training/receivingOrdersSchedule`; no lot was added and no event changed.
- Synthetic `TRANSFER_PENDING` result: warning stated that the lot remains at the truck and
  directed the operator to Pending Transfers. No Retry or Pending button exists on Receive
  Material. Evidence: `us3-transfer-pending.png`.
- Pending Transfers opens as its own view with its own Refresh, "Transfer selected lot", and
  "Receiving schedule" controls. Evidence: `pending-transfers-open.png`.
- Synthetic uncertain-outcome error opened the Kanoa message popup with the supervisor/reconcile
  text and no blind retry action.

## Theme and constrained width

- All six supported themes were checked: `kanoa-light`, `kanoa-dark`, `kanoa-light-forest`,
  `kanoa-light-firetruck`, `kanoa-light-orange`, `kanoa-light-grape`.
- In every theme, all six order rows, both selector rows, quantity row, Confirm, and Back were
  visible; `document.body.scrollWidth` stayed equal to the 1440 px viewport.
- Computed theme backgrounds changed (for example light `rgb(252,252,255)` and dark
  `rgb(26,28,30)`), while the view JSON contains only Kanoa font/container/button classes and no
  hard-coded color. Evidence: `theme-*.png`.
- At a 600 px viewport, all rows and both buttons remained visible, `scrollWidth` stayed 600 px,
  and the long note wrapped (`white-space: normal`, `overflow-wrap: break-word`). Evidence:
  `constrained-width.png`.

## Resolved defects

### 1. `getLotEvents(enabled=True)` against `mes.vwLotEvent`

The installed Kanoa `system.kanoa.lot.getLotEvents` appends `AND enabled = 1`, but `mes.vwLotEvent`
has no `enabled` column. The original error is saved in `vendor-getlotevents-error.txt`:

```text
FROM [mes].[vwLotEvent]
WHERE 1 = 1
AND enabled = 1
AND itemSourceName = 'output'
...
com.microsoft.sqlserver.jdbc.SQLServerException: Invalid column name 'enabled'.
```

**Resolution**: with approval, `'enabled': True` was removed from the two calls in the shared
receiving script. The installed vendor function and `vwLotEvent` were left untouched. After a
Gateway restart, a direct `getLotEvents` call with only `workOrderId`, `lotOperationName`, and
`itemSourceName` returned the expected Receive event for order 3, and
`getReceivedQtyForOrder(3)` returned `100.0` (matching the database).

### 2. Startup script was attached to a non-firing component event

The full load pipeline had been placed in `root.events.component.onStartup`, which does not fire
for this view. Diagnostics showed `receivedQtyKg: 0`, empty error text, and no pipeline execution
even though the shared script was fixed. The pipeline was moved to the view-level
`events.system.onStartup`, rewritten to use `self.` instead of `self.view.`, and given `.get`
guards for partial params. The dead root event was removed. After a Gateway restart, opening
order 3 from the schedule produced the correct order, `receivedQtyKg: 100`, `actualQtyKg: 10,900`.

### 3. Two-session concurrency over-receipt

The pre-fix concurrent test on order 4 (`RCV000003`, target `12,000 kg`) recorded two successful
`7,000 kg` receipts (`RCV0008` and `RCV0007`, DB lotEventIds `19`–`21` and `16`–`18`), for a
`14,000 kg` total. This was a symptom of defect 1 and 2: both sessions saw a zero prior-received
value and therefore the full target as remaining.

**Resolution**: post-fix, two clean Perspective sessions opened order 2 (`RCV000002`, target
`30,000 kg`, prior received `200 kg`) and each submitted `20,000 kg` at the same time. One returned
`SUCCESS` (lot `RCV0010`, lotId `9`, receiveOperationEventId `17`, transferOperationEventId `18`,
DB lotEventIds `25`/`26`/`27`, truck `TRUCK02`, tank `TK102`); the other returned
`VALIDATION_ERROR` with `Quantity exceeds the remaining order target of 9800.0 kg.` The database
total is `20,200 kg` against the `30,000 kg` target — no over-receipt. Evidence:
`concurrent-session-a.png`, `concurrent-session-b.png`.

## Out of scope for this user story

The following paths were intentionally not revalidated with a real failure. The user confirmed
that the **Transfer operation feature is not part of the current user story**, so no runtime
Transfer-operation configuration was changed and no further simulation was attempted.

- **Real transfer failure → Pending Transfers recovery**: there is no built-in non-destructive
  simulation hook, and no real stranded lot was created. The UI hand-off message and the separate
  `training/pendingTransfers` screen were verified synthetically only. This is not a blocker for
  the current user story.
- **Real uncertain write-timeout**: verified only at the view-feedback/log level, not from an
  actual timed-out write.

## Test data left in the local database

| Order | Target | Received | Note |
| --- | --- | --- | --- |
| 1 `RCV000001` | 20,000 | 200 | pre-fix duplicate tests |
| 2 `RCV000002` | 30,000 | 20,200 | includes post-fix concurrency success |
| 3 `RCV000005` | 11,000 | 200 | includes post-fix valid `100 kg` receipt |
| 4 `RCV000003` | 12,000 | 14,000 | pre-fix concurrency over-receipt; do not reuse |

## Release recommendation

**In-scope acceptance passes.** US1, US2, and US3 are demonstrated; the `getLotEvents` defect, the
startup-event placement defect, and the concurrency over-receipt are resolved and revalidated.
No new component, method, table, or SQL was introduced. The Transfer-operation/Pending-Transfers
recovery path and the real write-timeout path are explicitly out of scope for this user story and
do not block it. The operator path is already implemented: an operator selects an order on
`training/receivingOrdersSchedule` and presses Confirm to open `training/receiveMaterial`. No
separate feature-registration step exists for this user story.
