# Feature Specification: Kanoa UI Alignment for Operator Receiving

**Feature Branch**: `002-operator-receiving-kanoa-ui`

**Created**: 2026-11-17

**Status**: Draft

**Input**: User description: "operator-receiving feature (kanoaMES -> Perspective -> Views -> training) should use (reuse) already existed kanoa components (for inputs, labels, buttons, dropdowns etc).The receiving screens (kanoaMES -> Perspective -> Views -> training) should include kanoa layout ( side bar, header etc)."

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Work inside the standard Kanoa application shell (Priority: P1)

As a receiving operator, I want the receiving screens to open inside the same Kanoa application shell I use for every other MES screen, with the standard header and navigation sidebar, so that I can orient myself, see my session context, and move between areas without learning a different screen frame.

**Why this priority**: The receiving workflow is currently a standalone screen without the product's shell. Without the shell, operators lose familiar navigation, identity/session context, and consistency with the rest of the MES, which undermines day-to-day usability more than any single control styling issue.

**Independent Test**: Open each receiving screen directly and from the main navigation, and verify that the Kanoa header and sidebar are present, the current page is identifiable in navigation, and the operator can leave the receiving area using the sidebar alone.

**Acceptance Scenarios**:

1. **Given** a receiving operator is signed in, **When** the operator opens the Receiving Orders Schedule, the Receive Material form, or the Pending Transfers list, **Then** each screen renders inside the standard Kanoa shell with the global header and navigation sidebar visible.
2. **Given** the operator is on any receiving screen, **When** the operator inspects the header, **Then** the header shows the same session-related information and actions as on other Kanoa MES screens.
3. **Given** the operator is on a receiving screen, **When** the operator selects another area from the sidebar, **Then** navigation works as it does elsewhere and the operator can return to the receiving screens.
4. **Given** the operator is on a receiving screen, **When** the current page is shown in navigation, **Then** the receiving entry is identifiable as the active location.

---

### User Story 2 - Use familiar Kanoa inputs and actions on the receiving forms (Priority: P1)

As a receiving operator, I want the receiving forms to use the same Kanoa labels, text and number inputs, dropdowns, date selectors, tables, and buttons that other Kanoa screens use, so that the controls look and behave predictably and I can apply knowledge from the rest of the MES.

**Why this priority**: The receiving workflow depends on date selection, order selection, quantity entry, asset dropdowns, and confirmation actions. Inconsistent controls cause hesitation and entry errors in the core receiving task.

**Independent Test**: Walk through the full receiving flow (schedule selection, quantity and asset entry, confirmation, retry of a pending transfer) and compare every control against an established Kanoa screen; verify that labels, inputs, dropdowns, selectors, and buttons match the Kanoa component set in appearance and interaction states.

**Acceptance Scenarios**:

1. **Given** the operator opens a receiving screen, **When** the screen displays labels, inputs, dropdowns, date selectors, or buttons, **Then** each control uses the established Kanoa component for that purpose rather than a screen-specific look-alike.
2. **Given** an input or selection is required, **When** it is empty, invalid, or awaiting data, **Then** the control shows the same default, focus, disabled, and invalid states as the equivalent Kanoa component elsewhere.
3. **Given** an operator must choose a date range, order, truck, or tank, **When** the operator interacts with the selector, **Then** the selection experience matches the equivalent Kanoa selector used on other screens.
4. **Given** the operator must confirm, cancel, or retry an action, **When** the action is presented, **Then** it uses the standard Kanoa action component and its standard emphasis and disabled behavior.
5. **Given** read-only order information is shown on the receiving form, **When** the operator views it, **Then** it is clearly presented as non-editable and visually consistent with read-only information elsewhere in Kanoa.

---

### User Story 3 - See consistent Kanoa feedback and states (Priority: P2)

As a receiving operator, I want loading, empty, success, validation, and error feedback on receiving screens to follow the same Kanoa patterns as other MES screens, so that messages are recognizable, appear in expected places, and clearly tell me what to do next.

**Why this priority**: Receiving involves validation failures, uncertain receipts, and pending transfers. Inconsistent or ad-hoc messaging makes recovery harder, but the core flow can still function without this refinement.

**Independent Test**: Trigger loading, an empty schedule, a validation failure, a successful receipt, and a failed transfer on the receiving screens, and verify that each state uses the established Kanoa presentation and wording pattern.

**Acceptance Scenarios**:

1. **Given** data is loading on a receiving screen, **When** the screen is waiting, **Then** the operator sees the standard Kanoa loading indication rather than a blank or partially rendered screen.
2. **Given** no orders, lots, or pending transfers are available, **When** the list is empty, **Then** the operator sees a Kanoa-style empty state that explains the situation.
3. **Given** a validation or receipt/transfer error occurs, **When** it is reported, **Then** the message uses the Kanoa presentation for that severity, is readable in the active theme, and states the required next action.
4. **Given** a receipt or transfer succeeds, **When** the result is shown, **Then** the success presentation follows the Kanoa pattern used elsewhere.

---

### User Story 4 - Keep all receiving screens consistent across themes and screen sizes (Priority: P3)

As a receiving operator, I want every receiving screen to remain usable and visually consistent in the available theme and on the devices used at the plant, so that the screens are equally usable at a workstation and on a smaller display.

**Why this priority**: Consistency across the three receiving screens, themes, and display sizes protects the value of the alignment work, but it is secondary to adopting the shell and standard controls.

**Independent Test**: Display all three receiving screens in each supported Kanoa theme at workstation and constrained widths, and verify that the shell adapts, content remains readable, and no control is clipped or unreachable.

**Acceptance Scenarios**:

1. **Given** the operator is using any supported Kanoa theme, **When** a receiving screen is displayed, **Then** all text, controls, and messages meet the theme's normal readability expectations.
2. **Given** the display is narrower than a workstation, **When** a receiving screen is displayed, **Then** the shell collapses or hides navigation as it does elsewhere and the receiving content remains usable.
3. **Given** the operator moves between the three receiving screens, **When** screens are compared, **Then** labels, spacing, control sizing, and action placement follow the same Kanoa conventions.

### Edge Cases

- The receiving screens are opened by direct address rather than through navigation; the shell must still render with the correct active navigation location.
- The operator's session context (user, site, or notifications) is unavailable while the header loads; the header must degrade gracefully without breaking the receiving content.
- A required Kanoa component does not yet support a receiving need (for example, a specialized selector or validation state); the screen must not fall back to an unrelated custom style, and the gap must be handled deliberately and consistently.
- The navigation sidebar is collapsed, auto-hidden, or temporarily unavailable; the receiving content must remain usable and a clear way to reopen navigation must exist.
- The active theme changes while a receiving form is open; all controls and messages must remain readable and consistent without a reload.
- A control is disabled because data is still loading or an order is ineligible; the disabled state must be visually distinguishable from an editable state.
- Success, error, or validation feedback is longer than the available space; the message must remain complete and readable rather than being clipped.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: Every receiving screen (Receiving Orders Schedule, Receive Material, and Pending Transfers) MUST render inside the standard Kanoa application shell, including the global header and navigation sidebar.
- **FR-002**: The Kanoa shell MUST present the same session-related information and actions on receiving screens as it does on other Kanoa MES screens.
- **FR-003**: Navigation from the shell MUST allow the operator to leave and return to the receiving screens without entering addresses manually.
- **FR-004**: The active receiving location MUST be identifiable in the navigation while any receiving screen is open.
- **FR-005**: Receiving screens MUST reuse the established Kanoa components for labels, text inputs, number inputs, date inputs, dropdowns/selectors, tables, and action buttons wherever an equivalent component exists.
- **FR-006**: Receiving screens MUST NOT introduce screen-specific look-alike controls when an established Kanoa component provides the same purpose.
- **FR-007**: Reused controls MUST preserve their standard interaction states, including default, focus, disabled, invalid, and read-only presentation.
- **FR-008**: Read-only receiving information MUST be visually distinguishable from editable fields and MUST match Kanoa read-only presentation conventions.
- **FR-009**: Confirmation, cancellation, retry, and navigation actions on receiving screens MUST use the standard Kanoa action component with its standard emphasis and disabled behavior.
- **FR-010**: Loading, empty, success, validation, and error states on receiving screens MUST use the established Kanoa feedback patterns and placements.
- **FR-011**: All receiving screens MUST remain readable and operable in every supported Kanoa theme.
- **FR-012**: The Kanoa shell and receiving content MUST adapt to constrained display widths in the same way as other Kanoa MES screens, keeping all required controls reachable.
- **FR-013**: The three receiving screens MUST apply a consistent layout, spacing, control sizing, and action placement convention.
- **FR-014**: The UI alignment MUST preserve all existing receiving behavior defined for the Operator Receiving feature, including order selection, quantity validation, receipt creation, and pending-transfer recovery.
- **FR-015**: Where an existing Kanoa component cannot meet a receiving need, the gap MUST be resolved in a shared, reusable way that follows the existing Kanoa design conventions, and it MUST be reused consistently across the receiving screens.
- **FR-016**: Any shared component or shell behavior introduced for receiving MUST be usable by other screens without duplicating its definition.
- **FR-017**: The receiving screens MUST NOT alter or extend vendor-managed Kanoa resources in order to achieve visual consistency.

### Key Entities *(include if data involved)*

- **Receiving Screen**: One of the three operator receiving surfaces (schedule, receipt entry, pending transfers) that must be hosted in the Kanoa application shell and use Kanoa components.
- **Application Shell**: The global frame shared by Kanoa MES screens, comprising the header and navigation sidebar, including active-location and session context presentation.
- **Kanoa Component**: An established, reusable Kanoa UI building block with defined appearance and interaction states, such as a label, input, selector, table, button, or feedback element.
- **Shared Extension**: A reusable component or shell behavior added to satisfy a receiving need when no existing Kanoa component suffices, available for reuse by other screens.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: 100% of receiving screens display the standard Kanoa header and navigation sidebar when opened, whether by navigation or direct address.
- **SC-002**: An audit of the three receiving screens finds zero interactive controls that have an equivalent established Kanoa component but do not use it.
- **SC-003**: 100% of controls on receiving screens exhibit the standard Kanoa default, focus, disabled, invalid, and read-only states when those states are triggered.
- **SC-004**: All three receiving screens remain fully readable and operable in 100% of supported Kanoa themes in the acceptance review.
- **SC-005**: The receiving workflow can be completed at a constrained display width without any required control becoming unreachable or clipped.
- **SC-006**: All existing Operator Receiving acceptance scenarios continue to pass after the UI alignment, with zero functional regressions.
- **SC-007**: A visual consistency review finds zero unapproved deviations in control appearance, spacing, or feedback presentation across the three receiving screens.
- **SC-008**: An operator who knows the standard Kanoa shell can reach the Receiving Orders Schedule from the main screen without assistance or address entry.

## Assumptions

- The existing Kanoa component set (for example, core template inputs, selectors, tables, buttons, and feedback views) is the authoritative design system for this work; alignment means adoption and reuse, not redesign.
- The Kanoa application shell used by other MES pages (header, navigation sidebar, options area) is the target shell for the receiving screens.
- The Operator Receiving feature (spec `001-operator-receiving`) remains the source of truth for business behavior; this feature changes presentation and hosting only, not the receiving rules.
- Receiving screens are reachable through the product's existing navigation configuration, and any navigation entry needed for them is part of this feature's scope.
- Supported themes and target display sizes follow the existing Kanoa MES defaults; no new theme or device class is introduced by this feature.
- If a receiving need exposes a gap in the Kanoa component set, a shared reusable addition is acceptable, but it must follow existing conventions and must not modify vendor-managed resources.
- The receiving screens are operated by authenticated users under the site's existing access controls.

## Dependencies

- Operator Receiving feature (`specs/001-operator-receiving`) for the receiving workflow, screens, and validation rules.
- The Kanoa MES application shell and Kanoa component library as delivered in the current project baseline.
- Existing navigation configuration that determines how receiving screens are reached and highlighted.
