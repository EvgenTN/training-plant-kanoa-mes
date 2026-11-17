# Contract: Reused Kanoa Components and Feedback

## Purpose

Defines which inherited Kanoa building blocks the receiving screens use, their parameter contracts,
and the presentation rules that make the three screens visually consistent. All components are
referenced from `kanoaAPP` (inherited by `kanoaMES`); none are copied or edited.

## Component Reuse Matrix

| Screen role | Kanoa component | Parameters / bindings | Presentation states |
|---|---|---|---|
| Screen title | `kanoa/font/titleLarge` (or nearest installed heading class) | `props.textStyle.classes` | Read-only; one title per screen |
| Section/instructions label | `kanoa/font/bodyMedium`, `kanoa/font/labelMedium` | `props.textStyle.classes` | Read-only |
| Read-only order value | `kanoa/core/templates/displays/valueWithLabel` or `numLabel`, or label with Kanoa font class | `params.value.label`, `params.value.value`; optional `params.value.units` | Read-only, visually non-editable, no input affordance |
| Date range | `kanoa/core/templates/selectors/date/dateRangeSelectorCompact` | Bidirectional `params.startDate`, `params.endDate`; optional `params.selectedRange`, `params.enabled` | Enabled/disabled; invalid range reported through feedback channel |
| Quantity in kg | `kanoa/core/templates/inputs/numberInput` | `params.label`, `params.units='kg'`, `params.enabled`, bidirectional `params.value` | Default, focus, disabled, invalid via Kanoa component |
| Truck / tank selection | `kanoa/core/templates/selectors/assetDropdownSelector` | `params.value.parentPath` scoped to Receiving/Bulk Storage, `params.value.showPath`, `params.value.options.selectable`, bidirectional `params.selectedPath` | Default, disabled while loading, invalid selection reported through feedback channel |
| Orders / pending table | Configured `ia.display.table` following `kanoa/mes/lots/lotTable` | Explicit columns, `cells.style.fontSize`, header titles, sortable/filterable flags, selection data | Empty state, loading state, selected row clearly indicated |
| Primary action | `ia.input.button` with `kanoa/button/filled` | `props.text`, `props.enabled`, event script | Enabled/disabled; one primary action per screen |
| Secondary action | `ia.input.button` with `kanoa/button/outlined` or `kanoa/button/flat` | Same as primary | Enabled/disabled; visually subordinate |
| Icon-only action | `ia.input.button` with `kanoa/button/flatIcon` | Icon path, tooltip, enabled | Enabled/disabled |
| Waiting state | `kanoa/core/templates/displays/progressBar` | `params.values.showBar`, `params.values.type`, `params.values.text`, `params.values.textColor` | Visible only while loading/submitting |
| Containers / grouping | `kanoa/container`, `kanoa/border`, `kanoa/containerVariant` | `props.style.classes` | Theme-driven; no hard-coded color values |

**Forbidden classes**: `kanoa/button/primary` and other class names not present under
`services/ignition/projects/kanoaAPP/com.inductiveautomation.perspective/style-classes/`.
The installed button classes are `filled`, `outlined`, `flat`, `flatIcon`, and `text`.

## Binding Contract

1. User-editable reused controls bind bidirectionally to the receiving view's existing custom state
   (`startDate`, `endDate`, `actualQty`, `truckPath`, `tankPath`).
2. The receiving scripts continue to read the same fields they read before this feature; component
   adoption MUST NOT require changes to API calls, operation payloads, or validation rules.
3. Selection changes that require derived IDs (for example, asset path → asset ID) use existing Kanoa
   utilities in the view's binding/event scripts, consistent with other Kanoa screens.
4. Read-only values are bound one-way from the confirmed order/receipt result.

## Feedback Contract

| Situation | Kanoa mechanism | Requirement |
|---|---|---|
| Transient success | `system.kanoa.toast.show({'type': 'success', 'message': ...})` | Includes order number, lot number, quantity, truck and tank where applicable |
| Validation or operation error | `system.kanoa.toast.show({'type': 'error' or 'warning', 'message': ...})` | States the next action; no silent failure |
| Blocking detail message | Popup `kanoa/core/templates/displays/messagePopup` with `params.text` | Named, modal popup; close action available |
| Confirmation of a significant action | Popup `kanoa/core/templates/inputs/confirm` with `params.text`, `params.messageHandler`, optional `params.inputPayload` | Confirms or cancels before acting |
| Waiting | `kanoa/core/templates/displays/progressBar` | Shown while a read/write is in progress |

No new custom message component, custom toast renderer, or hard-coded color message is permitted.

## Layout and Theme Contract

- One title area, one content area, and one action area per screen; spacing and control sizing follow
  the reference Kanoa screens rather than screen-local values.
- All styling comes from inherited Kanoa templates/style classes, so switching among configured
  Kanoa themes does not require screen changes.
- At constrained widths, the shell auto-hides navigation as configured; receiving content wraps or
  scrolls and no required control becomes unreachable.
- The root of each receiving view remains a Kanoa-styled container; no inline presentation colors
  are introduced.

## Behavior Preservation Contract

- Receipt, transfer, quantity validation, over-receipt prevention, stale-order checks, and pending
  transfer recovery behave exactly as defined by `specs/001-operator-receiving`.
- Feedback changes only presentation text/placement; success, failure, and pending-recovery outcomes
  remain distinguishable.
- Internal navigation remains view-based within `/receiving`; no new page routes are required.
