# Contract: Receive Material Components and Bindings

**Feature**: `specs/003-receive-material-woeditor-ui/`
**Scope**: The `training/receiveMaterial` Perspective view and the navigation parameters that open it.

## Purpose

Define the reused Kanoa/Ignition building blocks, their parameter and binding contracts, and the
presentation rules that make the refactored screen match `kanoa/mes/workOrders/woEditor`. Every
component listed here already exists in `kanoaAPP` or is a native Perspective primitive. No component
is copied, forked, or created.

## Kanoa-First Declaration

| Question | Answer |
|---|---|
| New Perspective views / embeddable views? | None. |
| New Vision windows / templates? | None. |
| New script functions / modules? | None. |
| New SQL or tables? | None. |
| Files edited | `kanoaMES/.../views/training/receiveMaterial/view.json`; navigation script in `kanoaMES/.../views/training/receivingOrdersSchedule/view.json`. |
| Files referenced but not edited | `kanoaAPP` templates and styles; `KANOA_SCRIPTS/.../ops/receiving`. |

If native capability proves insufficient during implementation, stop and record the required
approval (requirement, native assets evaluated, proposed name/location, maintenance cost) in
`plan.md` before writing code.

## Screen Composition

Top-to-bottom row order, following the reference screen's field/action placement:

0. Retained screen heading `Receive Material` (`kanoa/font/titleLarge`) and a status row that keeps
   the existing `kanoa/core/templates/displays/progressBar` and no-order message.
1. Order #
2. Title
3. Target Qty (with `kg`)
4. Schedule Date
5. Status
6. Notes (grows; wraps)
7. Receiving Truck (tree selector)
8. Destination Tank (tree selector)
9. Actual Qty (numeric entry with fixed `kg`)
10. Actions: Confirm (filled), Back (outlined), centered

## Component Reuse Matrix

| Screen role | Component / style | Source | Contract |
|---|---|---|---|
| Screen container | `ia.container.flex` with `kanoa/container kanoa/font/default` | Native + Kanoa classes | Column, `gap: 5`, `padding: 5`, `overflow: hidden`. |
| Field row | `ia.container.flex` | Native | `basis: 30px`, `shrink: 0`, `style: {gap: 5, overflow: hidden}`. |
| Row label | `ia.display.label` with `kanoa/font/default` | Native + Kanoa class | `basis: 65px`, `shrink: 0`, `textAlign: right`. |
| Read-only value | `ia.display.label` with `kanoa/font/default` | Native + Kanoa class | `basis: 200px`, `grow: 1`, `shrink: 0`; no input, no edit affordance. |
| Long notes value | `ia.display.label` | Native | `overflowWrap: break-word`, `whiteSpace: normal`; row grows. |
| Asset selector | `kanoa/core/templates/selectors/tree/selector` | `kanoaAPP` | One instance for the truck, one for the tank; see selector contract below. |
| Actual quantity | `ia.input.numeric-entry-field` with `kanoa/font/default` | Native + Kanoa class | Bidirectional binding to `view.custom.actualQtyKg`; fixed `kg` label beside it. |
| Confirm | `ia.input.button` with `kanoa/button/filled` | Native + Kanoa class | Enabled only when `submitting` is false and required inputs are valid. |
| Back | `ia.input.button` with `kanoa/button/outlined` | Native + Kanoa class | Navigates to `training/receivingOrdersSchedule`; no writes. |
| Confirmation dialog | `kanoa/core/templates/inputs/confirm` | `kanoaAPP` | Popup title `Confirm receipt`; message handler `confirmReceiveOrder`. |
| Error detail | `kanoa/core/templates/displays/messagePopup` | `kanoaAPP` | Opened only for uncertain/critical messages, as today. |
| Transient feedback | `system.kanoa.toast.show` | Kanoa API | Success, warning, and error toasts. |

## Selector Parameter Contract

Both selector instances use `props.path = "kanoa/core/templates/selectors/tree/selector"` and the
following `props.params.values`:

| Key | Truck value | Tank value |
|---|---|---|
| `data` | Expression binding `1` + script transform returning `system.kanoa.asset.getAssets({'assetPath': 'Training Plant\\Receiving\\%', 'assetTypeName': 'Storage Location', 'enabled': True})` | Same with `'Training Plant\\Bulk Storage\\%'` |
| `msgHandler` | `receivingTruckSelected` | `receivingTankSelected` |
| `options` | `{dragDrop: False, expand: False, multiSelect: False, showBreadcrumb: True, showClear: True, showSelectedPath: False}` | Same |
| `path` | Property binding to `view.custom.truckPath` | Property binding to `view.custom.tankPath` |
| `selection` | `[]` | `[]` |
| `treePath` | `null` (selector defaults to `path`) | `null` |
| `style` | `{iconColor: '', iconPath: null, tooltip: null}` | Same |

The dataset returned by `getAssets` includes `assetId`, `assetName`, `assetPath`, `path`, and
`enabled`, so no separate lookup is needed to resolve the chosen asset.

## Selection Message Contract

The selector emits a page-scope message to the configured `msgHandler` with this shape:

```text
{
  "activity": "nodeSelected",
  "selection": [{"value": {<asset row columns>}}],
  "msgHandler": "<configured handler>",
  "selectorId": "<selector instance id>"
}
```

Handler behavior (root-scope message handlers on the view):

1. If `selection` is empty: set the matching `*AssetId` and `*Path` custom properties to `None`.
2. Else read `value = payload['selection'][0]['value']`.
3. If `value.get('assetId')` is `None` or empty (synthetic folder node): clear the selection and set
   an actionable `errorMessage` such as `Select a Storage Location, not a folder.` Do not set an ID.
4. Else set `*AssetId = value['assetId']` and `*Path = value.get('path') or value.get('assetPath')`.

The screen never trusts these values for data integrity: `receiveOrder` reloads both assets and
re-validates enabled state, type, and area before writing.

## Read-Only Field Contract

| Display row | Value binding | Empty presentation |
|---|---|---|
| Order # | `view.custom.order.orderNumber` | `"—"` |
| Title | `view.custom.order.description` (already applies title → item description fallback) | `"—"` |
| Target Qty | `view.custom.order.targetQty` formatted with `view.custom.order.unitName` | `"Unavailable"` |
| Schedule Date | `view.custom.scheduledStart` formatted as a Kanoa date/time | `"Unavailable"` |
| Status | `view.custom.order.status` | `"—"` |
| Notes | `view.custom.orderNotes` | `"—"` |

All six are `ia.display.label` values. None may be replaced by an editable input, and none may expose
an edit action.

## Actual Quantity Default Contract

On `onStartup`, after a successful `getReceivedQtyForOrder`:

```text
remaining = max(0, targetQty - receivedQtyKg)
view.custom.actualQtyKg = remaining
```

| Order state | Default |
|---|---|
| No prior receipts | Full target quantity. |
| Partial receipts | Target minus cumulative received kg. |
| Received ≥ target, or target unavailable | `0` / disabled with an explanation. |

Operator edits after startup are never overwritten by the screen.

## Action Contract

| Action | Preconditions | Effect |
|---|---|---|
| Confirm | `submitting` false; order eligible; `actualQtyKg > 0` and ≤ remaining; truck and tank IDs set. | Opens `confirm` popup; the handler calls `receiveOrder` once. |
| Back | Always available unless a confirmation is in flight. | `system.perspective.navigate(view='training/receivingOrdersSchedule')`; no data write. |

This screen exposes no Pending Transfers or Retry action. When `receiveOrder` returns
`TRANSFER_PENDING`, the result feedback directs the operator to `training/pendingTransfers`.

## Presentation Acceptance

- Labels are right-aligned at a 65 px basis; values start at a 200 px basis and grow.
- Rows are 30 px tall with a 5 px gap, matching `woEditor`.
- Notes wrap and never break the layout.
- Confirm uses the filled button style; Back uses outlined, mirroring `btnSave` / `btnClose`.
- No hard-coded colors are introduced; only existing Kanoa classes and CSS variables are used.
- The screen renders in every supported Kanoa theme and remains usable at a constrained width.
