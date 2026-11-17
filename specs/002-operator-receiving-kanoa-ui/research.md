# Research: Kanoa UI Alignment for Operator Receiving

**Feature**: `specs/002-operator-receiving-kanoa-ui/spec.md`
**Date**: 2026-11-17

Research was performed against the checked-in Ignition exports under
`services/ignition/projects/`, the project constitution, the Ignition 8.1
`system.perspective.navigate` documentation (applicable to the pinned 8.3 runtime),
and the existing Operator Receiving plan in `specs/001-operator-receiving/`.

## R1 — How the Kanoa shell is attached to screens

**Question**: Why do the `training` screens lack the header and sidebar, and what is the
narrowest way to add them?

**Decision**: Add the standard dock set as an explicit `docks` block on the `/receiving`
Perspective page in `kanoaMES/com.inductiveautomation.perspective/page-config/config.json`,
reusing the same dock views and settings as the `/` page. Keep the in-screen receiving
navigation on `system.perspective.navigate(view=...)` so the operator stays on that one
page and keeps its docks. Do not put the docks in `sharedDocks`, and do not change the
vendor dock views.

**Rationale**:
- The current `/receiving` page has only `title` and `viewPath`; `/` has `left` (NavBar),
  `right` (options), and `top` (header) docks. Pages `/marquee/...` intentionally have no
  docks, so a global `sharedDocks` change would put a header/sidebar on full-screen
  marquee displays.
- `kanoaMobile` uses `sharedDocks` for all docks, which shows the mechanism exists, but
  no project with both shell and full-screen pages uses it globally.
- Ignition documents that `navigate(view=...)` changes the current view without changing
  the browser address. The receiving views already use view-based navigation between
  schedule, receipt, and pending transfers, so one page with docks covers all three.
- `navigate(page=...)` changes the URL/page and would require additional configured pages
  for each receiving step; it is unnecessary for the existing flow.

**Alternatives considered**:
- Copy docks into `sharedDocks`: rejected because marquee pages must stay undocked.
- Configure separate docked page routes for all three receiving views: rejected as more
  configuration and a change to established in-flow navigation.
- Embed header/sidebar views directly into each receiving view: rejected because it
  duplicates vendor shell behavior and breaks standard dock handling.

## R2 — Navigation registration and active-location display

**Decision**: Treat Kanoa Navigation registration as a required deployment step and
verification gate, not as a file edit. Register (or confirm) the three receiving views
under a Receiving parent through **Configuration → Application → Navigation** with the
`kanoaMES` project and the operator roles from the 001 feature. Verify that the sidebar
shows the Receiving entry and highlights the active entry while moving through the flow.

**Rationale**:
- The navigation sidebar builds its tree from `system.kanoa.config.getNavigation(...)`,
  which is Kanoa application configuration (database-backed), not a checked-in view JSON.
- The 001 quickstart already identifies navigation registration as unconfirmed and
  records the same export-reproducibility gap for navigation records.
- `kanoa/core/docks/navigation/menu` maps navigation paths and page history to sidebar
  selection, so correctly registered View-type entries are required for active highlighting.

**Alternatives considered**:
- Hand-editing Kanoa navigation data: rejected until a supported export/import procedure
  is documented, per constitution Principle I and the 001 plan.
- Adding a client-owned navigation system: rejected; duplicates Kanoa configuration.

## R3 — What "reuse Kanoa components" means in this codebase

**Decision**: Use a reuse matrix rather than wrapping every control:
- Use Kanoa template views where one exists for the exact purpose.
- Where Kanoa itself uses a primitive Perspective control with Kanoa style classes, use
  the primitive with those same classes and property conventions.
- Never introduce a new local look-alike of an existing Kanoa template or class.

**Rationale**: Inspection of Kanoa's own `kanoa/mes/lots/lotExecutor/receiveLot` shows raw
labels, text field, numeric field, and dropdowns combined with
`kanoa/button/filled`/`outlined`, while `kanoa/mes/lots/lotTable` embeds
`kanoa/core/templates/selectors/date/dateRangeSelectorCompact`,
`kanoa/core/templates/selectors/assetSelector`, and
`kanoa/core/templates/displays/progressBar`. Both patterns are "Kanoa components".

**Component findings**:
- Labels and read-only values: `kanoa/font/*` classes; `displays/valueWithLabel`,
  `displays/numLabel`, and `displays/valueDisplay` are available for label/value pairs.
- Quantity entry: `kanoa/core/templates/inputs/numberInput` with
  `params.label`, `params.units`, `params.enabled`, and bidirectional `params.value`.
- Asset selection (truck/tank): `kanoa/core/templates/selectors/assetDropdownSelector`
  with `value.parentPath`, `value.options.selectable`, `value.showPath`, and bidirectional
  `selectedPath`. `assetSelector` is available for tree selection.
- Date range: `kanoa/core/templates/selectors/date/dateRangeSelectorCompact` with
  bidirectional `startDate`/`endDate` and optional `selectedRange`/`enabled`.
  `dateSelector` is more coupled to session asset/date-range state and is not required.
- Buttons: `ia.input.button` with `kanoa/button/filled` for primary actions,
  `kanoa/button/outlined` or `kanoa/button/flat` for secondary actions,
  `kanoa/button/flatIcon` for icon-only actions.
- Tables: no generic Kanoa table template exists; Kanoa screens use a configured
  `ia.display.table` with `kanoa/font/default` and explicit column definitions,
  sort/filter/selection settings, and compact cell font sizes.
- Containers: `kanoa/container`, `kanoa/border`, `kanoa/containerVariant`,
  `kanoa/popup` style classes are used in Kanoa screens for grouping.
- Loading: `kanoa/core/templates/displays/progressBar` with
  `values.showBar`, `values.type`, `values.text`, and `values.textColor`.

**Alternatives considered**:
- Replacing all primitives with wrapper views: rejected because Kanoa's own editor and
  operator views use primitives with style classes; wrapping them would add maintenance.
- Keeping the current screen styling and only adding fonts: rejected because it does not
  satisfy FR-005/FR-006 of the spec.

## R4 — Feedback and confirmation patterns

**Decision**: Use `system.kanoa.toast.show({'type': ..., 'message': ...})` for transient
success/error/warning/info feedback, `kanoa/core/templates/displays/messagePopup` opened
as a named modal popup for blocking messages, and
`kanoa/core/templates/inputs/confirm` for destructive or ambiguous confirmations.
Use `kanoa/core/templates/displays/progressBar` for waiting states.

**Rationale**: These exact calls are the established pattern throughout `kanoaAPP`
(for example, `cmms/config/procedures/procedureManager` and `mes/lots/lotExecutor/
lotOperationExecutor`). The toast dock already relays legacy toast messages through
`system.kanoa.toast.show`, so this is the current supported feedback channel.

**Alternatives considered**:
- Plain labels for all messages: rejected; the current views already show the problem.
- Custom popup views: rejected because Kanoa templates exist.

## R5 — Existing class defects in the receiving views

**Decision**: During implementation, audit all style classes used by the three receiving
views and replace classes that do not exist in `kanoaAPP/com.inductiveautomation.
perspective/style-classes` with valid Kanoa classes.

**Rationale**: The views use `kanoa/button/primary` on primary actions, but the
installed style classes include `kanoa/button/filled`, `outlined`, `flat`, `flatIcon`,
and `text` — no `primary`. Titles currently use `kanoa/font/bodyMedium` where Kanoa
screens use larger heading classes. These are concrete, verifiable deviations from the
Kanoa component conventions.

**Alternatives considered**:
- Adding a `kanoa/button/primary` class: rejected because it would modify vendor-managed
  `kanoaAPP` resources and duplicate an existing equivalent.
- Leaving the class as-is: rejected because SC-007 requires zero unapproved deviations.

## R6 — Theme and constrained-width behavior

**Decision**: Use only inherited Kanoa style classes and templates (no hard-coded colors
or one-off styling), and rely on the dock `autoBreakpoint: 480` settings already present
on `/`. Verify the three screens in every configured Kanoa theme and at a constrained
width. Make receiving content containers wrap and let tables scroll rather than clip.

**Rationale**: The Kanoa themes are Gateway-level resources; component styling is driven
by style classes and templates. Hard-coded colors would break theme switching. The
standard dock definitions already specify `autoBreakpoint: 480`.

**Alternatives considered**:
- Adding a receiving-specific stylesheet or theme: rejected as out of scope and a
  violation of the reuse goal.
- Hiding the sidebar permanently on small screens: rejected; the standard dock behavior
  must be retained.

## R7 — Shared additions and project boundaries

**Decision**: No new shared component is expected. If a receiving need cannot be met by
an existing Kanoa template or style class, add the smallest reusable view under
`services/ignition/projects/KANOA_SCRIPTS/com.inductiveautomation.perspective/views/`
and reference it from all receiving screens. Do not edit `kanoaAPP`.

**Rationale**: Project inheritance is `kanoaMES` → `kanoaAPP` → `KANOA_SCRIPTS` (verified
in each `project.json`), so views in `KANOA_SCRIPTS` are inherited by `kanoaMES`. The
constitution's Principle II forbids vendor edits and requires shared/client-specific
assets in the appropriate project.

**Alternatives considered**:
- Defining a local copy of a missing component in each receiving view: rejected by
  FR-015/FR-016 and the constitution.
- Adding a new inheritable project: rejected; no need.

**Implementation outcome**: No shared component required. All receiving needs were met by
inherited `kanoaAPP` templates and style classes. Two implementation details are worth recording:
`assetDropdownSelector` is scoped to `Training Plant\\Receiving` / `Training Plant\\Bulk Storage`
and selects the `Storage Location` asset type used by the seeded trucks and tanks; the
selected path is resolved back to the existing `truckAssetId` / `tankAssetId` view state in the
embedded view's `onChange` script so the 001 receiving scripts are unchanged. Transient feedback
is emitted from view-level `propConfig.custom.<name>.onChange` scripts, which keeps the existing
business scripts and their result state intact while switching presentation to Kanoa toasts,
message popups, and the receipt confirmation popup.

## Resolved clarifications

The feature specification contained no open clarification requests. All
technical unknowns above were resolved with repository evidence; the remaining
deployment gate (navigation configuration export reproducibility) is carried forward
from the 001 feature and documented in `quickstart.md`.
