# Feature Specification: Operator Bulk Receiving

**Feature Branch**: `001-operator-receiving`

**Created**: 2026-11-13

**Status**: Draft

**Input**: User discussion: provide an operator-friendly bulk receiving process that starts from a scheduled receiving order, captures actual delivery quantity and locations, creates a traceable lot, and transfers it into a selected tank.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Receive a scheduled order (Priority: P1)

As a receiving operator, I want to select and confirm a scheduled receiving order, review its details, enter the delivered quantity, and choose the truck and destination tank so that material can be received and traced without using the general-purpose lot manager.

**Why this priority**: This is the core receiving task and delivers the main operator benefit.

**Independent Test**: Select an eligible scheduled order, confirm its details, enter a valid quantity, choose a receiving truck and bulk storage tank, complete receipt, and verify the lot is recorded at the tank with its order association.

**Acceptance Scenarios**:

1. **Given** eligible orders are scheduled, **When** the operator opens the Receiving Orders Schedule, **Then** the operator can review and select an order by its number and scheduled information.
2. **Given** an order is selected, **When** the operator confirms that selection, **Then** the receiving screen shows order number, description, material, and target quantity as read-only information.
3. **Given** an eligible order and available receiving assets, **When** the operator enters a valid actual quantity, selects a truck and tank, reviews the summary, and confirms, **Then** one receipt lot is created, linked to the order, and located in the selected tank.

---

### User Story 2 - Record partial deliveries safely (Priority: P1)

As a receiving operator, I want to record partial deliveries against an order while preventing total receipts from exceeding the target quantity so that each delivery is recorded accurately.

**Why this priority**: Bulk orders may arrive in multiple deliveries; quantity control protects inventory and order accuracy.

**Independent Test**: Record a partial receipt, confirm the remaining quantity is updated, then attempt a receipt that would exceed the order target and verify it is rejected without creating a lot.

**Acceptance Scenarios**:

1. **Given** an order has remaining quantity, **When** the operator records a positive receipt smaller than or equal to the remaining quantity, **Then** the receipt is accepted and the remaining quantity is shown.
2. **Given** prior receipts have reached the target, **When** the operator attempts another receipt, **Then** the system rejects it and creates no additional receipt lot.
3. **Given** the entered quantity is zero, negative, missing, or not expressed in kg, **When** the operator submits, **Then** the system explains the validation error and records no receipt.

---

### User Story 3 - Recover a transfer that did not complete (Priority: P2)

As a receiving operator, I want to retry moving a received lot from its truck to a tank after a transfer failure, including after reopening the receiving workflow, so that I can complete the move without recording the delivery twice.

**Why this priority**: Receipt and transfer are separate recorded actions; a recoverable state prevents duplicate inventory and helps operators finish interrupted work.

**Independent Test**: Cause or simulate a transfer failure after a successful receipt, reopen the workflow, find the pending lot, retry its transfer, and verify there is one receipt and one successful transfer.

**Acceptance Scenarios**:

1. **Given** receipt succeeded but transfer failed, **When** the failure is reported, **Then** the operator is told that the lot remains at the truck and can retry the transfer.
2. **Given** a lot remains at a receiving truck after the operator reopens the workflow, **When** the operator views pending transfers, **Then** the lot, quantity, order, and current truck are shown for selection.
3. **Given** the operator retries a pending transfer, **When** the transfer succeeds, **Then** the existing lot is moved to the selected tank without creating another lot or receipt.
4. **Given** the result of a receipt request is uncertain, **When** the operator retries or checks status, **Then** the system checks the recorded result and does not blindly create a second receipt.

### Edge Cases

- The selected order is no longer eligible or has been changed before the operator submits; the system refreshes the order and blocks receipt with a clear explanation.
- A selected truck or tank has been disabled or no longer belongs to the receiving or bulk storage area; submission is rejected.
- A scheduled order has no description; the item description is shown as the description fallback.
- A receipt is accepted but the tank transfer fails or the session closes; the lot remains visible as pending at its truck and can be recovered later.
- An order has multiple partial receipts; cumulative received quantity is recalculated before each receipt to prevent over-receiving.
- A network or service error leaves the receipt outcome uncertain; the operator is directed to reconcile the recorded order and lot history before retrying.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The system MUST provide a Receiving Orders Schedule that lists orders with a scheduled receiving activity and an eligible status of Scheduled or In Progress.
- **FR-002**: The system MUST require the operator to select and confirm an order before opening its receiving form.
- **FR-003**: The receiving form MUST display order number, description, material, and target quantity as read-only fields. If the order description is absent, the item description MUST be displayed.
- **FR-004**: The system MUST allow an operator to enter the actual received quantity in kg and select a truck from enabled Receiving assets and a destination tank from enabled Bulk Storage assets.
- **FR-005**: The system MUST reject missing, zero, or negative actual quantities and missing or ineligible asset selections before recording a receipt.
- **FR-006**: The system MUST allow partial and multiple receipts for an order while ensuring cumulative receipt quantity does not exceed the order target. No over-receipt tolerance is allowed in this feature.
- **FR-007**: After operator confirmation, the system MUST create one traceable lot for the actual quantity, associate it with the selected order, record receipt at the selected truck, and transfer it to the selected tank.
- **FR-008**: The system MUST preserve lot identity and order traceability when material moves from the truck to the tank.
- **FR-009**: If receipt succeeds and transfer fails, the system MUST inform the operator that the lot remains at the truck and offer an immediate transfer retry.
- **FR-010**: The system MUST provide a pending-transfer list after the workflow is reopened, showing lots with remaining quantity at receiving trucks and enough information to select and retry the transfer.
- **FR-011**: Retrying a pending transfer MUST move the existing lot and MUST NOT create another lot or receipt.
- **FR-012**: The system MUST check recorded lot/order history before retrying an uncertain receipt and MUST direct unresolved outcomes to reconciliation rather than blindly re-submit.
- **FR-013**: The system MUST show a clear success result with order number, lot number, actual quantity, truck, and destination tank, or an actionable explanation of what remains to be completed.

### Key Entities *(include if feature involves data)*

- **Receiving Order**: A scheduled business order identifying the material and target quantity; may have one or more partial receipts and has an eligibility status.
- **Receipt**: An operator-confirmed delivery quantity recorded against one receiving order and one receiving truck.
- **Lot**: The traceable inventory identity created for a receipt, retaining its material, quantity, state, order association, and movement history.
- **Receiving Asset**: An enabled truck location where the receipt is first recorded.
- **Destination Tank**: An enabled bulk storage location that receives the lot from the truck.
- **Transfer**: The recorded movement of the received lot from its truck to its destination tank; may remain pending after a successful receipt.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: An operator can complete a standard receipt from order selection through confirmation in under 2 minutes when the order and assets are available.
- **SC-002**: In acceptance scenarios, 100% of selected order details displayed on the receiving form match the confirmed order, and none can be edited on that form.
- **SC-003**: In acceptance scenarios, no receipt is recorded when the proposed quantity would make cumulative received quantity exceed the order target.
- **SC-004**: For every simulated transfer failure after receipt, the lot remains identifiable at the truck and can be transferred after reopening without a duplicate receipt.
- **SC-005**: Operators can complete the routine receiving flow without opening Lot Manager.

## Assumptions

- Operators are authenticated users who are permitted to perform receiving work under the site's existing access controls.
- Only orders in Scheduled or In Progress status are eligible, and the Receiving Orders Schedule lists scheduled orders only.
- Partial deliveries are permitted; cumulative received quantity cannot exceed the order target and no over-receipt tolerance applies.
- The target quantity and actual quantity are compared in kg. If an order uses another unit, the system must use a valid conversion before applying the quantity rule.
- Order description is preferred; item description is the fallback when the order description is blank.
- Receipt at the truck and transfer to a tank are separate operational events. Transfer failure does not undo a successfully recorded receipt.
- Manual scale entry is in scope; automated scale integration, supplier management, quality inspection, COA handling, and ERP integration remain out of scope.
