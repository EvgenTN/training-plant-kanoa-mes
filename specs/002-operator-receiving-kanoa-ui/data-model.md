# Data Model: Kanoa UI Alignment for Operator Receiving

This feature introduces no MES data entities and no schema changes. It defines the UI structure,
bindings, and presentation states used by the three receiving screens. The business entities shown
on those screens (Receiving Order, Schedule Block, Receipt Lot, Receiving Asset/Tank, Transfer, and
Pending Transfer) remain defined in `specs/001-operator-receiving/data-model.md` and are not
redefined here.

## Entities

### Receiving Page

The single Perspective page that hosts the receiving flow and its Kanoa shell.

| Attribute | Meaning | Validation / use |
|---|---|---|
| Page ID | `/receiving` | Must be the page opened by direct address or by the Receiving navigation entry |
| Root view | `training/receivingOrdersSchedule` | Initial screen of the receiving flow |
| Docks | Header, navigation sidebar, options dock | Must match the dock views/settings used by the `/` page; must be present on `/receiving` |
| Title | Operator-facing page title | Should identify the Receiving area |

Relationship: all three receiving screens are shown as views on this page. Because in-flow
navigation uses `navigate(view=...)`, the page and its docks stay constant while the root view
changes.

### Dock Set

The reused Kanoa shell components attached to `Receiving Page`.

| Dock | Reused view | Behavior implied by the standard configuration |
|---|---|---|
| Left / NavBar | `kanoa/core/docks/navigation/navigation` | `onDemand`, fixed, auto-hide at 480px, pushes content |
| Top / header | `kanoa/core/docks/header/header` | Fixed, visible, pushes content, 50px |
| Right / options | `kanoa/core/docks/options` | `onDemand`, fixed, hides at 480px, pushes content |

Rule: dock entries are copied from the `/` page definition; values are not re-invented for receiving.
Marquee pages keep no docks.

### Receiving Screen

One of the three operator surfaces. Each screen has the same shell and a consistent Kanoa layout
(title, instructions/filter or read-only summary, primary content, actions, feedback).

| Screen | Role | Primary Kanoa content |
|---|---|---|
| Receiving Orders Schedule | Select an eligible order | `dateRangeSelectorCompact`, configured table, secondary/primary buttons |
| Receive Material | Enter and confirm the receipt | read-only `valueWithLabel`/`numLabel` or Kanoa font classes, `numberInput`, `assetDropdownSelector`, `filled`/`outlined` buttons |
| Pending Transfers | Retry a failed transfer | configured table, `assetDropdownSelector`, `filled`/`outlined` buttons |

Rule: a screen MUST NOT introduce a control that duplicates an established Kanoa template or style
class, and MUST NOT change the business behavior defined in the 001 feature.

### Component Binding

Describes how a reused Kanoa control is connected to the screen's existing view state.

| Attribute | Meaning | Validation / use |
|---|---|---|
| Role | What the control does (date range, quantity, truck, tank, table, action, feedback) | One mapping per control role; consistent across screens |
| Kanoa component | Template view path or style class used | Must exist in inherited `kanoaAPP` resources |
| Parameters | Declared inputs of the template | Must be bound to the view state the receiving scripts already consume |
| Direction | Input only or bidirectional | Bidirectional for user-editable values such as dates, quantity, and selected asset path |
| States | Default/focus/disabled/invalid/read-only | Must use the component's own state presentation, not local styling |

### Receiving UI State

Non-persistent view state that drives component presentation. It mirrors the data from the 001
feature but is not a new source of truth.

| Field | Meaning | Used by |
|---|---|---|
| `startDate`, `endDate` | Selected schedule window | Date range selector; schedule refresh |
| `orders` | Eligible scheduled orders | Orders table; empty-state detection |
| `selectedOrder` | Confirmed order summary | Receive Material read-only fields and receipt script |
| `actualQty` | Operator-entered quantity in kg | Quantity input; validation |
| `truckPath`, `tankPath` | Selected asset paths from scoped selectors | Asset resolution in existing receiving scripts |
| `pendingTransfers` | Lots with quantity remaining at receiving trucks | Pending transfers table |
| `loading`, `errorMessage`, `resultMessage` | Presentation state | Progress bar, toast/popup, and result presentation |

Rule: component bindings update this state; the state is then passed to the unchanged receiving
script functions. No data field is added to Kanoa storage.

### Presentation State

The visible state of a receiving screen.

| State | Meaning | Required presentation |
|---|---|---|
| Loading | A read or write is in progress | Kanoa progress bar indicator; controls disabled as appropriate |
| Empty | No orders or pending transfers are available | Kanoa-styled empty message with explanation |
| Ready | Data is available for operator input | Standard Kanoa controls and enabled actions |
| Invalid | Validation failed before a write | Kanoa error toast/popup; actionable message; no business write |
| Success | Receipt or transfer completed | Kanoa success toast with order, lot, quantity, and locations |
| Pending recovery | Receipt succeeded but transfer failed | Standard result message and transfer retry/pending-transfer entry |
| Unavailable | Navigation or session context is not ready | Shell degrades without hiding receiving content or blocking navigation |

### Navigation Entry

A Kanoa application configuration record (not a checked-in view file).

| Attribute | Meaning | Validation / use |
|---|---|---|
| Parent | Receiving group in the navigation tree | Groups the three screens |
| Name | Operator-facing label | Receiving, Order Schedule, Receive Material, Pending Transfers |
| Project | `kanoaMES` | Required for the views to resolve |
| Type | View | Uses `navigate(view=...)` semantics and keeps the current page |
| Path | `training/receivingOrdersSchedule`, `training/receiveMaterial`, `training/pendingTransfers` | Must match the exported view paths |
| Enabled / Roles | Availability to receiving operators | Must match the 001 feature's access assumptions |

## Screen Composition Map

| Screen | Current pattern | Target Kanoa pattern |
|---|---|---|
| All three | Bare view with `kanoa/container` root and body-medium title | `/receiving` page with standard docks; heading-level Kanoa title; Kanoa containers/borders |
| Schedule date filter | Two raw date-time inputs | `dateRangeSelectorCompact` with bidirectional `startDate`/`endDate` |
| Schedule / pending tables | Raw table with `kanoa/font/default` only | Kanoa-style table: explicit columns, compact cells, sort/filter/selection conventions from `kanoa/mes/lots/lotTable` |
| Quantity entry | Raw numeric field | `inputs/numberInput` with `label`, `units=kg`, bidirectional `value` |
| Truck/tank selection | Raw dropdowns | `assetDropdownSelector` with scoped `parentPath`, `selectedPath`, selectable asset options |
| Read-only order data | Body-medium labels | Kanoa label/value views or Kanoa heading/label classes; visibly non-editable |
| Buttons | `kanoa/button/flat` and invalid `kanoa/button/primary` | `kanoa/button/filled` for primary actions; `outlined`/`flat` for secondary actions |
| Loading / messages | Inline labels | `progressBar` template, `system.kanoa.toast.show`, `messagePopup`/`confirm` where blocking |
| Small display | No verified behavior | Dock auto-hide at 480px; wrapping content and scrollable tables |

## Validation Rules

- Every receiving screen MUST display the header and navigation sidebar from the `/receiving` page.
- Every control on a receiving screen MUST map to a Kanoa template or an installed Kanoa style
  class; classes not present in `kanoaAPP` (for example `kanoa/button/primary`) MUST be replaced.
- Bindings for editable reused controls MUST be bidirectional so operator input updates the state
  consumed by the existing receiving scripts.
- Selectable assets MUST remain scoped to the Training Plant Receiving and Bulk Storage paths; the
  UI alignment MUST not relax the 001 asset validation.
- Feedback MUST use the Kanoa channel appropriate to severity; success/error messages MUST include
  the identifiers operators need to reconcile a receipt.
- No new write path, no new table, and no change to receipt/transfer idempotency behavior.

## State Transitions

```text
Open /receiving (shell present)
    └─> Schedule loading ──> Empty schedule        (empty message)
                          └─> Orders available      (ready table)
                                 │ confirm order
                                 ▼
                          Receive Material (ready, read-only order info)
                                 │ validate + submit
                     ┌───────────┼────────────────┐
                     ▼           ▼                ▼
                  Invalid     Success        Pending recovery
                  (toast)   (success toast)  (message + retry)
                                 │ transfer failed
                                 ▼
                       Pending Transfers (ready table)
                                 │ select lot + tank, retry
                                 ▼
                          Success or Invalid
```

The shell and its navigation remain available in every state. Navigating to another Kanoa area and
returning re-enters the flow at the schedule.
