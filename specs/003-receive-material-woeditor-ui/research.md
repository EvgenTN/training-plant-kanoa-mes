# Research: Receive Material Refactored to the Work Order Editor Pattern

**Feature**: `specs/003-receive-material-woeditor-ui/spec.md`
**Date**: 2026-11-18

Research was performed against the checked-in Ignition exports under
`services/ignition/projects/`, the receiving script package, the Kanoa documentation under
`/home/yehor/Projects/ignition-kanoa/kanoa-docs/`, and the constitution in
`.specify/memory/constitution.md` (v1.1.0).

The governing constraint is Principle VI: use native KanoaMES and Ignition capability, and do not
create a custom component or method. Every decision below was chosen to avoid new components and
new script functions.

## R1 — How should the six order fields be rendered as read-only?

**Decision**: Render each value with the native `ia.display.label` primitive, using the existing
`kanoa/font/default` style class, and place it in the same flex row structure as `woEditor`. Give the
value label a Kanoa surface/background treatment so it reads as a field while remaining a label, not
an input. Use a multi-line label for notes.

**Rationale**: `FR-002` requires read-only fields with no editable control or edit action. An
`ia.input.text-field` is an editable control even when disabled, and Inspector exports show no
`readOnly` property in this Perspective version. `ia.display.label` is the native read-only display
primitive, is used throughout Kanoa screens, and carries no edit affordance. It is not a custom
component, so it satisfies Principle VI.

**Alternatives considered**:

- `ia.input.text-field` with animation/edit disabled: rejected because a disabled input is still an
  editable control and does not satisfy "no editable control".
- `kanoa/core/templates/displays/valueWithLabel`: rejected because its centered headline layout and
  72 px default height do not match the `woEditor` row geometry; using it would introduce visible
  deviations from the requested reference.
- A new read-only field view: rejected by Principle VI; no approval exists.

## R2 — How should the truck and tank selectors be built?

**Decision**: Embed two instances of the inherited
`kanoa/core/templates/selectors/tree/selector`, exactly as `woEditor` does for its item selector.
Bind each selector's `props.params.values.data` to the native asset API through an expression binding
whose script transform returns:

```python
system.kanoa.asset.getAssets({
    'assetPath': 'Training Plant\\Receiving\\%',
    'assetTypeName': 'Storage Location',
    'enabled': True
})
```

and the Bulk Storage equivalent for the tank. Keep `treePath` at its default (`path`) because
`system.kanoa.asset.getAssets` returns the `path` column. Configure
`options` as `{dragDrop: False, expand: False, multiSelect: False, showBreadcrumb: True,
showClear: True, showSelectedPath: False}`, matching `woEditor`.

**Rationale**: This is literally the component type the user referenced in `woEditor` (the current
export names it `evTreeSelector` under `flxItems`). It provides hierarchy browsing, search,
single-select, clear, breadcrumb, and selected-path display. `getAssets` is the native KanoaMES read
API and already supports path scoping, asset-type filtering, and `enabled`. No new component or
method is required.

**Alternatives considered**:

- Keep `kanoa/core/templates/selectors/assetDropdownSelector`: rejected because the user explicitly
  asked for the `woEditor` selector experience and a flat dropdown does not provide hierarchy
  browsing.
- Build a dataset in a script helper: rejected because a direct native API call in a binding is
  simpler and does not add a method.
- Use `assetTypeName` alone without a path: rejected because it would expose Storage Locations from
  every area, violating FR-007/FR-008.

## R3 — How are selector choices converted to asset IDs?

**Decision**: Give each selector a unique `msgHandler` (`receivingTruckSelected` and
`receivingTankSelected`) and register root-scope message handlers on the screen. Read the selected
row from `payload['selection'][0]['value']`, then set `view.custom.truckAssetId` /
`view.custom.tankAssetId` from its `assetId`, and mirror its `path` into `view.custom.truckPath` /
`view.custom.tankPath`. Bind each selector's `props.params.values.path` to the matching
`view.custom.*Path` property so the selected path can be restored. On an empty selection, clear both
the ID and the path. If a selected payload has no `assetId` (a synthetic branch/folder node),
discard it and set an actionable error message.

**Rationale**: The selector emits
`{activity: 'nodeSelected', selection: [{value: <row dict>}], msgHandler, selectorId}`. Asset rows
include `assetId`, `assetPath`, and `path`, so the ID is available without a second lookup. This
matches the `woEditor` handler pattern (`payload['selection'][0]['value'][...]`) and keeps the
script as configuration. The shared `receiveOrder` API still reloads both assets and re-validates
enabled state and the allowed base path, so the screen cannot bypass area rules.

**Alternatives considered**:

- Resolve the ID with a second `getAssets({'assetPath': selectedPath})` call, as the current dropdown
  does: unnecessary because the selector payload already carries `assetId`.
- Trust branch-node selections: rejected because synthetic folder nodes have no `assetId` and would
  fail later with a less actionable error.

## R4 — Where does the schedule date come from?

**Decision**: Read the schedule start date from the row the operator selected and pass it to the
receive screen as `scheduledStart` in the existing navigation parameters. The schedule table is bound
to `system.kanoa.order.getProductionOrders` and exposes `startDate` / `endDate`, so use
`selected.get('startDate')`, falling back to `selected.get('scheduledStart')` if an older schedule
shape is present. In `receiveMaterial`, expose it as `view.custom.scheduledStart` and format it with a
label expression. When the value is null, show `"Unavailable"` explicitly.

**Rationale**: FR-004 defines the schedule date as the date associated with the selected scheduled
order. The selected row already contains the start date used by the schedule display, so this is a
one-line navigation-parameter addition and a display binding. It does not extend any receiving
method and does not add a query.

**Alternatives considered**:

- Use `dueDate` from the order row: rejected because the spec explicitly says the selected schedule
  entry, and due date can differ from the scheduled start.
- Extend `getReceivingOrder` / `_orderSummary` to return the schedule date: rejected because that
  changes an existing shared custom method and would need Constitution Principle VI approval;
  the value is already available at the navigation source.
- Re-query the schedule from the receive screen: rejected as extra coupling and a new query path.

## R5 — Where do the order notes come from without changing `_orderSummary`?

**Decision**: Pass the selected schedule row's `note` value to the receive screen as `orderNotes` in
the existing navigation parameters. In `receiveMaterial`, initialize `view.custom.orderNotes` from
that parameter. If the screen is opened without it (for example directly by view path with only a
`workOrderId`), fall back to a native
`system.kanoa.order.getProductionOrders({'workOrderId': <id>, 'ignoreActualQty': True})` read in
`onStartup` and extract the `note` column. Display the value in the notes label; when it is null or
empty, show an explicit `"—"` placeholder consistent with read-only Kanoa display.

**Rationale**: The schedule table is already fed by `getProductionOrders`, which returns `note`, so
the normal flow needs no extra query. The fallback keeps the screen usable on direct navigation. The
shared receiving `_orderSummary` stays unchanged, satisfying both Principle IV (API-first) and
Principle VI (no new or extended method), and the notes are the same order-level notes `woEditor`
shows.

**Alternatives considered**:

- Always call `getProductionOrders` from the receive screen: works, but duplicates a read the
  schedule already performed; keep it only as the direct-open fallback.
- Extend `_orderSummary` to include `note`: technically a change to an existing, approved custom
  method, and therefore subject to the Principle VI approval gate. Not needed for a display-only
  field.
- Read notes from the schedule event instead of the order: rejected because the spec says notes are
  order-level notes.

## R6 — How is the actual quantity defaulted and entered?

**Decision**: Use the native `ia.input.numeric-entry-field`, matching `woEditor`'s quantity control,
with a static `kg` label beside it. Bind its value bidirectionally to `view.custom.actualQtyKg`. On
screen startup, after `getReceivedQtyForOrder` succeeds, set

```python
remaining = max(0, float(order['targetQty']) - float(receivedQtyKg))
view.custom.actualQtyKg = remaining
```

so a new order defaults to the full target and a partially received order defaults to the
outstanding quantity. Do not reset the value on later re-renders, so an operator edit is preserved.
Disable Confirm and show an explanation when target or remaining quantity is zero or unavailable.

**Rationale**: FR-010 and SC-005 require the outstanding quantity. `getReceivedQtyForOrder` already
computes cumulative kg received and rejects non-kg history, so the screen only needs one subtraction
inside the existing startup event. The numeric field is a native Ignition primitive, not a new
component, and the kg unit stays consistent with the receiving rules.

**Alternatives considered**:

- Keep `kanoa/core/templates/inputs/numberInput`: valid Kanoa, but the user asked for the `woEditor`
  component type; `woEditor` uses `ia.input.numeric-entry-field`. The native field also gives
  clearer numeric validation.
- Default to the full target always: rejected by the clarified spec (remaining quantity).
- Put the subtraction in a new helper method: rejected by Principle VI; it is a single inline
  expression in an existing event.

## R7 — How is the `woEditor` layout replicated?

**Decision**: Copy the reference geometry and styles:

- Root: `ia.container.flex`, direction `column`, classes `kanoa/container kanoa/font/default`,
  `gap: 5`, `padding: 5`, `overflow: hidden`.
- Field rows: `ia.container.flex`, `basis: 30px`, `shrink: 0`, style
  `{gap: 5, overflow: hidden}`.
- Row labels: `ia.display.label`, `basis: 65px`, `shrink: 0`, classes `kanoa/font/default`,
  `textAlign: right`.
- Row values: `basis: 200px`, `grow: 1`, `shrink: 0`, classes `kanoa/font/default`.
- Notes row: label aligned top with `marginTop: 5px`; value uses `overflowWrap: break-word` and
  `whiteSpace: normal`; row `basis: 30px`, `grow: 1`.
- Selector rows: label `basis: 65px`; selector view `grow: 1` inside the row.
- Actions row: `justify: center`, `gap: 5`, `padding: 5`; Confirm uses `kanoa/button/filled` and
  Back uses `kanoa/button/outlined`, matching `btnSave` / `btnClose`.

**Rationale**: FR-006 and SC-003 require matching the reference. These are the measured properties
from the checked-in `woEditor` export, so reproducing them is a configuration exercise, not a new
design. All classes are existing Kanoa style classes.

**Alternatives considered**: Introducing screen-specific CSS/classes or a new container view;
rejected by FR-006 and Principle VI.

## R8 — Which feedback and confirmation patterns are reused?

**Decision**: Keep the existing confirmation flow: Confirm opens
`kanoa/core/templates/inputs/confirm` with message handler `confirmReceiveOrder`; the handler calls
the existing `kanoaScripts.custom.ops.receiving.receiveOrder`. Keep the existing `result` and
`errorMessage` change scripts, which use `system.kanoa.toast.show` and
`kanoa/core/templates/displays/messagePopup`. Remove the Pending and Retry buttons from this screen;
keep only Confirm and Back. When `receiveOrder` returns `TRANSFER_PENDING`, the result handler's
message must direct the operator to the separate Pending Transfers screen.

**Rationale**: FR-017–FR-021 and feature 002 already established these Kanoa feedback patterns. The
receiving API already distinguishes success, validation failure, and transfer-pending outcomes, and
its receipt is preserved when the transfer fails. Reusing the existing templates and handlers adds
no component or method.

**Alternatives considered**:

- Inline a new success/error panel: rejected because the Kanoa toast and message popup already cover
  it and a new panel would be a custom component.
- Keep Pending/Retry on this screen: rejected by the clarified spec (FR-020).

## R9 — How is the change kept within the Kanoa-first principle?

**Decision**: The implementation changes only
`kanoaMES/.../views/training/receiveMaterial/view.json` and the navigation script in
`kanoaMES/.../views/training/receivingOrdersSchedule/view.json`. No file under `kanoaAPP` and no file
under `KANOA_SCRIPTS` is edited. No new view, function, module, or SQL is added. Inline scripts are
limited to bindings, selection state, navigation, and calls to existing Kanoa APIs and the existing
receiving methods. If a native gap appears during implementation, work stops and an approval request
is added to `plan.md` before code is written.

**Rationale**: This is the narrowest possible change that satisfies the spec and directly implements
Constitution Principle VI and the approval gate. It also preserves Principles I–V: resources stay
version-controlled, project boundaries are respected, scripts remain Jython 2.7, data operations
stay API-first and idempotent, and the result is verifiable through the quickstart.

**Alternatives considered**:

- Extend the shared receiving module, create a read-only display template, or create a dedicated
  asset-tree wrapper: all would require prior explicit approval under Principle VI and are
  unnecessary for this presentation refactor.
