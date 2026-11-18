# Gateway Acceptance Evidence — Spec 003

**Run date**: 2026-11-18
**Gateway**: Ignition Standard `8.3.10 (b2026100610)`, local project `kanoaMES`
**Session**: Perspective admin session; Kanoa user `admin` with Administrator role
**Loading**: Final files loaded with Gateway Projects → **Scan File System**. The stack was not
restarted, reseeded, or reset. The trial timer was renewed through the Gateway **Reset Trial** UI.
**Runtime prerequisite**: Kanoa Serialization UI gained enabled serial definition `Receiving`,
prefix `RCV`, zfill `4` (runtime configuration only; no repository diff).

## Scope and structural audit

- `python3 -m json.tool` passed on both changed view exports.
- All 72 embedded `script`/`code` strings in the two changed files compile as Python when wrapped
  in a function body.
- `git diff --name-only | grep -E 'kanoaAPP|KANOA_SCRIPTS'` printed nothing.
- `git status --porcelain services/ignition/projects/kanoaMES/com.inductiveautomation.perspective/views`
  showed only:
  - `views/training/receiveMaterial/view.json`
  - `views/training/receivingOrdersSchedule/view.json`
- No new Perspective view, template, function, module, helper, wrapper, table, or SQL was added.
- Unrelated working-tree changes were left untouched: `.specify/memory/constitution.md`,
  `.specify/scripts/python/__pycache__/common.cpython-315.pyc`,
  `services/ignition/config/resources/core/ignition/tag-provider/kanoaMES/config.json`, and
  `services/ignition/config/resources/core/ignition/translations/resource.json`.

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
- New-order default: order 1 → `20,000`; order 3 initially → `11,000`.
- Edit preservation: setting order 3 to `1,234`, then forcing re-render/resize, retained `1,234`.
- Invalid matrix against the real Confirm path produced no DB writes:
  - blank → client-side "Enter an actual quantity and select a receiving truck and destination tank."
  - `0` and negative → `Actual quantity must be greater than zero kg.`
  - nonnumeric → `Enter a positive receipt quantity and select an order, truck, and tank.`
  - over outstanding → `Quantity exceeds the remaining order target of 20000.0 kg.`
  - missing truck or tank → client-side selection message.
  - stale/wrong-area asset → `VALIDATION_ERROR`.
- Valid, double-clicked confirmation on order 3 produced exactly one receipt and transfer pair:
  lot `RCV0006`, lotId `5`, `100 kg`, truck `TRUCK01` id `15`, tank `TK101` id `12`,
  result `SUCCESS` / `Transfer completed.`, DB lotEventIds `13`/`14`/`15`
  (receiveOperationEventId `9`, transferOperationEventId `10`).
- The duplicate guard is implemented in the existing `confirmReceiveOrder` handler in the allowed
  view file: a per-session/per-view `RLock` from `system.util.getGlobals()` plus a terminal-result
  guard for `SUCCESS`/`TRANSFER_PENDING`. Reopening order 3 after receipt still showed the full
  `11,000` default because of the vendor defect below; that is not a guard regression.
- Pre-fix duplicate tests (before the guard) created two receipts on order 1 (`RCV0002`,
  `RCV0003`, lotEventIds `1`–`6`) and order 2 (`RCV0004`, `RCV0005`, lotEventIds `7`–`12`).
  These remain in the local database as test evidence and were not cleaned.
- Back: changing quantity/assets and pressing Back navigated to
  `training/receivingOrdersSchedule`; order 4 stayed at 0 events at that time and no lot was added.
- Synthetic `TRANSFER_PENDING` result: warning stated that lot `RCV0006` remains at `TRUCK01` and
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

## Release blockers

### 1. Installed Kanoa view is incompatible with `getLotEvents(enabled=True)`

The shared receiving API calls `system.kanoa.lot.getLotEvents` with `enabled: True`. The installed
Kanoa function generates `AND enabled = 1` against `mes.vwLotEvent`, which has no `enabled`
column. Gateway log excerpt is saved in `vendor-getlotevents-error.txt`:

```text
com.kanoa.mes.GatewayOpsLotModule - getLotEvents exception:
...
FROM [mes].[vwLotEvent]
WHERE 1 = 1
AND enabled = 1
AND itemSourceName = 'output'
AND workOrderId = 3
AND lotOperationName LIKE ?
...
com.microsoft.sqlserver.jdbc.SQLServerException: Invalid column name 'enabled'.
```

Consequences:

- `getReceivedQtyForOrder` returns `0` for orders 1, 2, and 3 even though their Receive events
  exist in `mes.vwLotEvent`.
- Partial-receipt default is wrong: order 3 reopened with `11,000` instead of `10,900`.
- Cumulative target enforcement cannot see prior receipts.
- This defect lives in the installed Kanoa function/view and the unchanged shared script filter.
  Fixing it would require a vendor/shared-script change, which is outside this feature's allowed
  scope.

### 2. Two-session concurrency over-receives

Two clean Perspective sessions submitted `7,000 kg` each against order 4 (`RCV000003`, target
`12,000 kg`) at the same time. Both returned `SUCCESS`:

- Session A: lot `RCV0008`, lotId `7`, receiveOperationEventId `13`,
  transferOperationEventId `14`, DB lotEventIds `19`/`20`/`21`, truck `TRUCK01`, tank `TK101`.
- Session B: lot `RCV0007`, lotId `6`, receiveOperationEventId `11`,
  transferOperationEventId `12`, DB lotEventIds `16`/`17`/`18`, truck `TRUCK02`, tank `TK102`.

Database total for order 4 is `14,000 kg` against `12,000 kg` target. Evidence:
`concurrent-session-a.png`, `concurrent-session-b.png`.

### 3. Transfer-failure and pending-recovery scenarios not executed

No documented non-destructive transfer-failure simulation exists in `KANOA_SCRIPTS` receiving code
or the feature docs, and no safe real scenario was found without editing configuration/data beyond
this feature's scope. The UI presentation was verified synthetically and Pending Transfers was
confirmed to open, but the stranded-lot recovery path remains unverified. Uncertain write-timeout
behavior was likewise verified only at the view-feedback/log level.

## Release recommendation

**Blocked.** The refactor itself is Kanoa-first and structurally clean, and US1/US2 plus most of US3
pass. Resolve the Kanoa `getLotEvents`/`vwLotEvent` prerequisite and re-run cumulative default,
over-receipt, and two-session concurrency before registering the feature for operators. Then supply
or document a safe transfer-failure simulation and complete pending-transfer recovery.
