# Feature Specification: Receive Material Work Order Editor Refactor

**Feature Branch**: `003-receive-material-woeditor-ui`

**Created**: 2026-11-18

**Status**: Draft

**Input**: User description: "Refactor (KanoaMES)training/receiveMaterial screen with styles and components from (KanoaAPP)kanoa/mes/workOrders/woEditor.

The screen should contain
	Read only text fields (order information): Order number, Title, Target quantity, Schedule date, Status, Notes

	Operator should select Truck station from Receiving Area of Assets (component type as in (KanoaAPP)kanoa/mes/workOrders/woEditor/root/fixItem)
	Operator should select Destination tank from Bulk Storage Area of Assets (component type as in (KanoaAPP)kanoa/mes/workOrders/woEditor/root/fixItem)

	Operator should set Actual quantity (by default it equals target quantity value) (component input numeric)

	Buttons Confirm and back "

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Review order information in the work order editor style (Priority: P1)

As a receiving operator, I want the Receive Material screen to present the selected order's key information in the same layout, typography, and styling as the work order editor, so that I can verify what I am about to receive and trust that the screen belongs to the standard Kanoa experience.

**Why this priority**: The operator must confirm the correct order and quantity before any material is recorded. Presenting the information in a proven Kanoa screen style reduces hesitation and entry mistakes in the core receiving task.

**Independent Test**: Open the Receive Material screen for a scheduled order and compare it with the work order editor; verify that all six required order fields are visible, read-only, and visually consistent with the reference screen.

**Acceptance Scenarios**:

1. **Given** an eligible order has been selected, **When** the Receive Material screen opens, **Then** it shows order number, title, target quantity, schedule date, status, and notes as read-only fields.
2. **Given** the order information is displayed, **When** the operator interacts with any of the six fields, **Then** the values cannot be edited and no edit affordance is presented.
3. **Given** the order has no notes, **When** the screen displays the notes field, **Then** the field shows an explicit empty presentation consistent with Kanoa read-only conventions.
4. **Given** the order has no title, **When** the screen displays the title field, **Then** the item description is shown as the fallback value.
5. **Given** the screen is compared with the work order editor, **When** labels, field spacing, grouping, and action placement are reviewed, **Then** they follow the same visual conventions rather than a screen-specific design.

---

### User Story 2 - Select the truck and destination tank with the standard asset selector (Priority: P1)

As a receiving operator, I want to choose the receiving truck from the Receiving area and the destination tank from the Bulk Storage area using the same selector experience as the work order editor's item field, so that I can find assets by their place in the hierarchy and avoid choosing the wrong location.

**Why this priority**: Receipt and transfer locations determine inventory accuracy. An inconsistent or free-text location choice would allow material to be recorded at the wrong asset.

**Independent Test**: Open each selector, browse or search the asset hierarchy, choose a truck under Receiving and a tank under Bulk Storage, and verify that only enabled Storage Locations from the correct area can be selected and that the chosen path is visible.

**Acceptance Scenarios**:

1. **Given** the operator opens the truck selector, **When** the hierarchy is shown, **Then** selectable entries are limited to enabled Storage Locations in the Receiving area.
2. **Given** the operator opens the destination tank selector, **When** the hierarchy is shown, **Then** selectable entries are limited to enabled Storage Locations in the Bulk Storage area.
3. **Given** the selector is open, **When** the operator searches, expands, selects, or clears a selection, **Then** the interaction matches the asset selector used in the work order editor, including showing the selected path.
4. **Given** a selected asset is disabled or no longer belongs to the required area before confirmation, **When** the operator confirms, **Then** the receipt is blocked with an actionable message and no record is created.
5. **Given** no eligible assets exist in an area, **When** the selector is opened, **Then** the operator sees an explanation instead of an empty list with no guidance.

---

### User Story 3 - Enter the actual quantity and confirm or go back (Priority: P1)

As a receiving operator, I want the actual quantity to be prefilled with the outstanding quantity and to confirm or leave the screen with clear actions, so that I can record a delivery quickly while retaining control over the amount and the workflow.

**Why this priority**: Quantity entry and confirmation are the actions that create inventory. Prefilling the expected amount speeds up the common full-delivery case, while validation prevents over-receipt.

**Independent Test**: Open the screen for a new order and for an order with a prior partial receipt, verify the default quantity in both cases, confirm a valid receipt, test an invalid quantity, and use Back to leave without recording anything.

**Acceptance Scenarios**:

1. **Given** an order has no prior receipts, **When** the screen opens, **Then** the actual quantity defaults to the full target quantity.
2. **Given** an order already has partial receipts, **When** the screen opens, **Then** the actual quantity defaults to the remaining quantity rather than the full target.
3. **Given** the operator changes the quantity, **When** the operator confirms, **Then** the entered value is used and the receipt is limited to the remaining quantity.
4. **Given** the quantity is missing, zero, negative, non-numeric, or greater than the remaining quantity, **When** the operator confirms, **Then** the receipt is blocked with an actionable explanation and no record is created.
5. **Given** valid order, quantity, truck, and tank values, **When** the operator confirms, **Then** one receipt is recorded, the material is transferred to the selected tank, and the success result identifies the order, lot, quantity, truck, and tank.
6. **Given** a confirmation is in progress, **When** the operator looks at the actions, **Then** Confirm is disabled and repeated activation cannot create a duplicate receipt.
7. **Given** the operator chooses Back, **When** the schedule screen is shown, **Then** no receipt or transfer has been created and unsaved input is discarded.
8. **Given** the receipt succeeds but the tank transfer fails, **When** the result is shown, **Then** the operator is told that the material remains at the truck and is directed to the separate Pending Transfers screen to complete recovery.

### Edge Cases

- The screen is opened with no selected order: the operator sees a clear message and a way back to the schedule.
- The selected order becomes ineligible or its remaining quantity changes before confirmation: the order is reloaded and the submission is blocked with an explanation.
- The order's notes are long: the full notes remain readable without breaking the layout.
- The target quantity or remaining quantity is zero or unavailable: the quantity field and Confirm are disabled with an explanation.
- A truck or tank is removed, disabled, or moved out of its area after being selected: confirmation is rejected and the operator must reselect.
- The operator double-clicks Confirm or retries after a slow response: only one receipt and one transfer are recorded.
- The operator tries to leave while confirmation is in progress: navigation is prevented until the outcome is known.
- The session closes after receipt but before transfer: the receipt remains recorded and recovery is available from the Pending Transfers screen.
- The schedule date is unavailable for the selected order: the field shows an explicit unavailable value rather than a blank that looks like missing data.
- The screen is used in any supported Kanoa theme or at a constrained display width: all required fields and actions remain readable and reachable.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The Receive Material screen MUST display order number, title, target quantity, schedule date, status, and notes for the selected order.
- **FR-002**: All six order information fields MUST be read-only, with no editable control or edit action on this screen.
- **FR-003**: When the order title is empty, the title field MUST display the item description as its fallback value.
- **FR-004**: The schedule date field MUST show the date associated with the selected scheduled order; when no date is available, it MUST show an explicit unavailable value.
- **FR-005**: When the order notes are empty, the notes field MUST show an explicit empty presentation consistent with Kanoa read-only conventions.
- **FR-006**: The screen's labels, field alignment, spacing, grouping, typography, and action placement MUST follow the work order editor's established visual conventions and existing Kanoa styles.
- **FR-007**: The truck selector MUST allow selection only from enabled Storage Locations in the Receiving area.
- **FR-008**: The destination tank selector MUST allow selection only from enabled Storage Locations in the Bulk Storage area.
- **FR-009**: Both asset selectors MUST provide the same interaction as the work order editor's item selector, including hierarchy browsing, search or expand, single selection, clear selection, and display of the selected path.
- **FR-010**: The actual quantity MUST be entered through a numeric input and MUST default to the outstanding quantity: the target quantity when no receipts exist, otherwise the remaining quantity.
- **FR-011**: The operator MUST be able to replace the default actual quantity before confirming.
- **FR-012**: The system MUST reject a missing, zero, negative, non-numeric, or over-remaining actual quantity before creating any record.
- **FR-013**: The system MUST reject confirmation when the truck or tank selection is missing, disabled, or outside its required area.
- **FR-014**: Before writing, the system MUST reload the order's eligibility and remaining quantity, and MUST revalidate both selected assets.
- **FR-015**: Confirmation MUST create exactly one receipt for the entered quantity and transfer the material to the selected destination tank, preserving the existing receiving rules.
- **FR-016**: While confirmation is in progress, Confirm MUST be disabled and duplicate submissions MUST be prevented.
- **FR-017**: A successful confirmation MUST present a Kanoa-consistent result identifying the order, lot, quantity, truck, and destination tank.
- **FR-018**: A failed or invalid confirmation MUST present an actionable Kanoa-consistent message and MUST NOT create a partial or duplicate receipt.
- **FR-019**: When receipt succeeds but the tank transfer fails, the system MUST preserve the receipt, explain that material remains at the truck, and direct the operator to the separate Pending Transfers screen.
- **FR-020**: This screen MUST expose only the Confirm and Back actions; pending-transfer recovery MUST remain on the separate Pending Transfers screen.
- **FR-021**: Back MUST return the operator to the Receiving Orders Schedule without creating, changing, or transferring any record.
- **FR-022**: This feature MUST preserve all existing Operator Receiving behavior and MUST retain the standard Kanoa application shell and navigation established for the receiving screens.
- **FR-023**: The screen MUST NOT alter or extend vendor-managed Kanoa resources.
- **FR-024**: The feature MUST reuse existing Kanoa components, styles, and screen logic. Creating a new custom component or method is prohibited without explicit prior approval recorded in the plan or pull request, in accordance with the project constitution.
- **FR-025**: Actual quantity MUST be expressed in kilograms, consistent with the existing receiving rules.

### Key Entities *(include if feature involves data)*

- **Receiving Order**: The scheduled business order being received; carries the order number, title, target quantity, schedule date, status, and notes shown on this screen.
- **Receiving Asset**: An enabled Storage Location in the Receiving area, representing the truck station where the receipt is first recorded.
- **Destination Tank**: An enabled Storage Location in the Bulk Storage area, representing where the received material is transferred.
- **Receipt**: The operator-confirmed actual quantity recorded against one order and one receiving truck.
- **Lot**: The traceable inventory identity created for the receipt; retains its identity when moved to the tank.
- **Transfer**: The recorded movement of the received lot from the truck to the destination tank.
- **Pending Transfer**: A received lot that remains at a truck after a failed transfer; recovered on the separate Pending Transfers screen, not on this screen.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: An operator can complete a standard receipt from opening the screen through confirmation in under 2 minutes when the order and assets are available.
- **SC-002**: In acceptance review, 100% of the six required order fields match the canonical order values and cannot be edited on the screen.
- **SC-003**: A visual review finds zero unapproved deviations from the work order editor reference in label alignment, typography, spacing, grouping, selector presentation, and action emphasis.
- **SC-004**: 100% of tested invalid quantities and invalid asset selections are blocked with no receipt created.
- **SC-005**: In 100% of tested cases, the default actual quantity equals the outstanding quantity: the full target for a new order and the remaining quantity after partial receipts.
- **SC-006**: 100% of valid confirmations create exactly one receipt and one transfer; repeated activation or retry produces no duplicate receipt.
- **SC-007**: All Operator Receiving acceptance scenarios continue to pass after the refactor, with zero functional regressions.
- **SC-008**: All required fields and actions remain readable and reachable in 100% of supported themes and at a constrained display width.
- **SC-009**: The change introduces zero new custom components or methods without a recorded prior approval.

## Assumptions

- This is a presentation and interaction refactor; the receiving rules, validation, idempotency, and transfer recovery behavior from the Operator Receiving feature remain unchanged.
- "Title" refers to the order title; when it is empty, the item description is the fallback, consistent with the existing receiving information rules.
- The schedule date is taken from the scheduled entry used to select the order; if no date is available, the field states that explicitly.
- Notes are order-level notes and are displayed as entered.
- Actual quantity remains in kilograms and is compared with the order target in the same unit, consistent with the existing receiving feature.
- Partial deliveries are still permitted; the default reflects the outstanding quantity so a full delivery does not exceed the order target.
- Pending-transfer recovery remains available on the existing separate Pending Transfers screen; this screen intentionally exposes only Confirm and Back.
- Back discards unsaved input and does not prompt, because no receiving work has been committed at that point.
- Operators are authenticated users operating under the site's existing access controls.
- The work order editor and its asset selector are the authoritative visual and interaction reference; the Kanoa component set remains the design system, and no new custom component or method is introduced without explicit approval.

## Dependencies

- Operator Receiving feature (`specs/001-operator-receiving`) for order eligibility, quantity rules, receipt creation, transfer, and recovery behavior.
- Kanoa UI alignment feature (`specs/002-operator-receiving-kanoa-ui`) for the standard Kanoa application shell, navigation, themes, and feedback patterns.
- The work order editor screen as the visual and interaction reference for labels, fields, selectors, and actions.
- Existing Kanoa components and styles, the separate Pending Transfers screen, and the configured Receiving and Bulk Storage asset hierarchies.
