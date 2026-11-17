# Training Plant Kanoa MES

# Bulk Receiving Solution Design

Version: 1.0

Status: Baseline Approved

---

# 1\. Purpose

The purpose of this project is to design and implement a Bulk Receiving process using Kanoa MES and Ignition.

The project is being developed as a training and reference implementation that can later be extended into a production\-grade MES solution.

The primary business objective is to manage the receipt of raw materials delivered by truck while maintaining inventory visibility and material traceability.

---

# 2\. Technology Platform

## MES Platform

Kanoa MES

## Runtime Platform

Ignition

## Environment Setup

Kanoa is installed and started using the [Kanoa Docker Template](https://github.com/PorubaimikhYehor/kanoa-docker-template).

## Design Principle

Use standard Kanoa functionality whenever possible.

Custom development should be limited to operator\-facing workflows and user experience.

Core MES functionality should remain based on native Kanoa objects and operations.

## Configuration Source of Truth

The repository exports are authoritative for the configured Training Plant assets and items:

- `assets.json` is the source of truth for the asset hierarchy and asset types.
- `items.json` is the source of truth for the item-class hierarchy and configured items.

This document describes the intended process and design rationale. Descriptions of configured assets and items must match the exports. When configuration changes in Kanoa, refresh the corresponding export and align this document; do not treat lists or trees copied here as an independent configuration source.

---

# 3\. Business Problem

A manufacturing site receives raw materials delivered by truck.

The receiving process must:

- record inbound deliveries;
- create inventory records;
- create traceable lots;
- store material in tanks;
- maintain the relationship between inventory and receiving orders;
- support future genealogy and production processes.

---

# 4\. Business Scenario

Example delivery:

Order:

PO000001

Material:

Corn Syrup

Quantity:

25,000 kg

Expected process:

Order

↓

Receive Material

↓

Create Lot

↓

Store Material

↓

Transfer To Tank

↓

Maintain Traceability

---

# 5\. Scope

## Included

- Receiving Orders
- Raw Materials
- Lots
- Storage Locations
- Inventory Tracking
- Material Transfers
- Traceability

## Excluded

- ERP Integration
- Supplier Management
- Quality Management
- COA Management
- Automated Scale Integration
- Production Processes

---

# 6\. Asset Model

## Decision

The Training Plant asset hierarchy, as exported in `assets.json`, is:

Training Plant

├── Receiving

│   ├── TRUCK01

│   └── TRUCK02

│

└── Bulk Storage

    ├── TK101

    ├── TK102

    └── TK103

## Reason

The structure represents the physical material flow.

Material is first received from a truck and later transferred into a storage tank.

The structure separates receiving activities from storage activities.

---

# 7\. Asset Types

## Decision

The Kanoa asset types, as exported in `assets.json`, are:

Training Plant = Site

Receiving = Area

Bulk Storage = Area

TRUCK01 = Storage Location

TRUCK02 = Storage Location

TK101 = Storage Location

TK102 = Storage Location

TK103 = Storage Location

## Reason

Receive and Transfer operations work natively with Storage Locations.

No custom inventory objects are required.

---

# 8\. Item Model

## Decision

The item-class hierarchy exported in `items.json` is:

Training Plant

├── RM

│   ├── Liquid
│   ├── Dry Bulk
│   └── Chemical

## Reason

The configured item classes are Raw Materials (`RM`) and its Liquid, Dry Bulk, and Chemical subclasses.

---

# 9\. Raw Materials

Configured item paths in `items.json`:

- `Training Plant\RM\Liquid\Corn Syrup`
- `Training Plant\RM\Liquid\Sugar Syrup`
- `Training Plant\RM\Liquid\Vegetable Oil`
- `Training Plant\RM\Dry Bulk\Sugar`
- `Training Plant\RM\Chemical\Caustic`

Additional materials may be added as required.

---

# 10\. Unit of Measure

## Decision

The standard unit of measure for bulk receiving is:

kg

## Reason

Bulk materials are tracked by weight.

The unit has been validated in Kanoa receiving operations.

---

# 11\. Inventory Model

## Decision

Inventory shall be Lot\-Centric.

## Reason

Lots are the primary traceability object within Kanoa.

Lot\-centric inventory supports:

- inventory visibility;
- traceability;
- genealogy;
- future production tracking.

---

# 12\. Receiving Order Model

## Decision

Receiving shall be performed against an Order.

## Reason

Receiving without an Order does not provide sufficient business context.

Orders provide:

- delivery reference;
- planning reference;
- traceability reference.

---

# 13\. Lot Model

## Decision

Lots shall be created during the Receive operation.

Each lot contains:

Lot Number

Item

Quantity

UOM

Location

State

Order

## Reason

These fields are natively supported by Kanoa.

No custom lot implementation is required.

---

# 14\. Lot States

## Decision

The standard Kanoa lot states shall be used.

Hold

OK

Scrap

## Reason

The states already exist within Kanoa and support future quality workflows.

---

# 15\. Storage Model

## Decision

Storage Locations may contain multiple Lots simultaneously.

## Reason

The capability has been validated in Kanoa.

Example:

TRUCK02

Lot A

Lot B

No lot merging is required.

---

# 16\. Material Movement Model

## Decision

Material movement shall use standard Kanoa operations.

Receive

Transfer

## Reason

The operations already provide:

- inventory movement;
- traceability;
- history tracking.

No custom movement engine is required.

---

# 17\. Traceability Model

## Decision

Traceability shall be based on Lot history.

## Reason

Kanoa automatically records operational events against Lots.

The system maintains visibility of:

Receive

Transfer

Current Location

Associated Order

throughout the lifecycle of the Lot.

---

# 18\. Receiving Process

## Current Process Model

Order

↓

Receive

↓

Lot

↓

TRUCK01 / TRUCK02

↓

Transfer

↓

TK101 / TK102 / TK103

Example:

PO000001

↓

Receive

↓

RM000003

↓

TRUCK02

↓

Transfer

↓

TK101

---

# 19\. Operator Experience

## Current State

The receiving process can be executed using standard Kanoa interfaces:

- Receive
- Transfer
- Lot Manager

The operator receiving feature has been exported as client-owned Perspective resources in `kanoaMES`, with shared orchestration code in `KANOA_SCRIPTS`. These resources are present in the repository; they are not yet verified on the live Gateway or registered in Kanoa Navigation.

## Limitation

The current workflow is suitable for validation and administration.

It is not suitable as the final operator workflow.

Kanoa's Lot Manager is a general-purpose interface that can run lot operations across different lots and assets. Operators receiving a delivery should instead use a focused Perspective workflow that shows the selected order and only the fields needed to receive it.

---

# 20\. Operator Receiving Experience

## Feasibility

A dedicated operator receiving screen is feasible using the existing Kanoa MES system functions and Ignition Perspective. Kanoa's documentation includes example custom Perspective Receive Lot and Transfer Lot views. It describes a receiving screen as a `Receive` operation with no input lots and one output lot, and documents `system.kanoa.lot.executeLotOperation` as the supported function for writing the operation and its lot events together. This lets the operator flow avoid Lot Manager while keeping inventory and genealogy in Kanoa's native lot model.

The relevant documented functions are:

- `system.kanoa.order.getProductionOrders(...)` to retrieve receiving orders and their item/order fields.
- `system.kanoa.schedule.getCalendarEvents(...)` with `scheduleType: 'operation'` and a date range to retrieve operation-calendar events shown by Kanoa's Operations Schedule, including work-order identifiers and schedule dates.
- `system.kanoa.asset.getAssets(...)` to retrieve enabled assets by path, parent, or asset type.
- `system.kanoa.lot.executeLotOperation(...)` to create a `Receive` operation event and output lot event. The output event supports `itemId`, `lotEventQty`, `itemUnitId`, `workOrderId`, `assetId`, `lotStateId`, and `tStamp`; here `assetId` is the selected truck Storage Location and `workOrderId` links the received lot to the selected order.

Research references in the adjacent Kanoa documentation checkout: `training/training-trace/lot-screens/custom-lot-screens.md`, `training/training-trace/lot-screens/lot-functions.md`, `systemFunctions/lot/executeLotOperation.md`, `systemFunctions/order/getProductionOrders.md`, `systemFunctions/schedule/getCalendarEvents.md`, `systemFunctions/schedule/getScheduleBlocks.md`, and `systemFunctions/asset/getAssets.md`.

The repo's asset export confirms that `Training Plant\\Receiving\\TRUCK01`, `Training Plant\\Receiving\\TRUCK02`, and `Training Plant\\Bulk Storage\\TK101` through `TK103` are enabled Storage Locations. These paths can scope the truck and tank choices without hard-coding individual asset IDs. The receive operation places the output lot at one asset, so this design receives into the selected truck and then transfers the same lot to the chosen tank using a standard `Transfer` operation. The lot remains linked to the order through its receive event and retains history through the transfer.

### Order Schedule Selection

Kanoa's Operations Schedule renders operation-calendar events. Its implementation calls `system.kanoa.schedule.getCalendarEvents` with `scheduleType: 'operation'`, a date range, and an asset path; it expands and timezone-adjusts events for calendar use. The dedicated receiving schedule uses the same API without an asset-path restriction so it can list scheduled orders across the Training Plant, then reloads the canonical order by `workOrderId` before passing the selection to the receiving view. Raw `getScheduleBlocks` is not an equivalent source for reproducing the built-in calendar rows.

The local Kanoa documentation establishes the data and operation APIs, but does not document a supported extension hook for adding a custom action to a selected event in the built-in Operations Schedule. The dedicated receiving schedule therefore uses `getCalendarEvents` and an explicit **Confirm order** action, without modifying vendor-managed schedule views.

### Operator Screen

After selecting an order, show these order details as read-only:

| Field | Source |
|---|---|
| Order number | Production order name (`workOrderName`) |
| Description | Production order description (`workOrderTitle`), falling back to item description |
| Material | Item name/path on the production order |
| Target quantity | Planned order quantity, displayed in `kg` |

The operator enters the actual received quantity in `kg`, selects a truck from `Training Plant\\Receiving`, and selects a destination tank from `Training Plant\\Bulk Storage`. Choices include only enabled Storage Locations below the respective areas. The order fields remain locked after selection; changing orders returns the operator to the schedule and requires confirmation of the new selection.

### Exported Receipt Workflow (Gateway validation pending)

Target workflow:

Open Receiving Orders Schedule

↓

Select order and confirm selection

↓

Review read-only order details

↓

Enter actual quantity in kg, select a Receiving truck, and select a Bulk Storage tank

↓

Review and confirm receipt

↓

Create lot through Kanoa `Receive` operation at selected truck

↓

Transfer lot from selected truck to selected tank

↓

Show outcome; if transfer remains pending, offer immediate retry and a Pending Transfers list on reopen

### Kanoa UI Alignment

The three receiving views are hosted on the single `/receiving` Perspective page, which carries
the standard Kanoa left navigation, top header, and right options docks copied from the home page.
In-flow actions change the current view (`system.perspective.navigate(view=...)`) rather than the
page, so the shell stays visible across the schedule, receipt, and pending-transfer screens;
marquee pages remain undocked.

The screens reuse inherited `kanoaAPP` resources rather than local look-alikes: the compact date
range selector, numeric input, and asset dropdown selector templates; configured Kanoa tables and
`kanoa/font/*` / `kanoa/button/{filled,outlined,flat}` style classes; and the progress bar,
toast, message popup, and confirmation popup for feedback and waiting states. Read-only order
fields remain labels with Kanoa font classes. No MES table, operation payload, receiving rule, or
vendor resource was changed; the shared `KANOA_SCRIPTS` receiving package remains the source of
truth for the business logic. Navigation registration and all Gateway/theme checks remain
deployment-time validation gates.

### Processing and Validation Rules

1. Validate that the order still exists and is eligible for receiving immediately before posting. Do not rely on stale schedule data.
2. Require an actual quantity greater than zero, in `kg`. Partial receipts are allowed; reject a receipt that would take cumulative Receive output quantity above target. This implementation assumes order target and receipt quantities are in kg and fails closed otherwise.
3. Require a truck and tank selection. Resolve each selection to the current asset ID and verify it remains enabled and under the expected area.
4. Generate the lot number using the configured Kanoa serialization, use the order's material and `kg` unit, and apply the configured initial lot state (baseline: `OK`). Link the receive event to the selected `workOrderId`.
5. Execute the receive and transfer as distinct Kanoa operations. If transfer fails after receipt succeeds, report that the lot was received on the truck and provide a safe retry path; do not create a second receipt when retrying the transfer.
6. Serialize submissions by work order in the shared Gateway script module, re-read current order/receipt data before writing, and reconcile uncertain Receive outcomes by lot name and order history. Gateway concurrency behavior still requires runtime verification.

The script resolves operations, sources, state, kg unit, and configured serialization at runtime. If serial configuration is ambiguous or required configuration is missing, it fails closed. This runtime lookup and operation payload remain subject to validation on the installed Kanoa Gateway before operator use.

## Recommendation

Keep custom views in `kanoaMES` and the shared script in `KANOA_SCRIPTS`; do not modify vendor-managed `kanoaAPP` or introduce custom database tables. Register the schedule, receipt, and pending-transfer views through Kanoa Configuration → Application → Navigation after confirming role and project settings in the Gateway. Treat the workflow as unavailable to operators until registration and the acceptance run in `specs/001-operator-receiving/quickstart.md` pass.

---

# 21\. Validated Functionality

The following baseline functionality was validated within Training Plant before this feature:

- Receive Operation
- Transfer Operation
- Lot Creation
- Lot Traceability
- Multi\-Lot Storage
- Order Assignment
- Order Persistence
- Storage Locations
- kg Unit Of Measure

The new operator screens, lot-creation payload, per-order serialization, event reconciliation, and transfer retry have not yet been runtime-validated. The baseline list above is not acceptance evidence for the new workflow.

---

# 22\. Architecture Baseline

The operator workflow follows this architecture:

Scheduled order selection → canonical order and quantity validation → `Receive` creates a lot at the selected truck → `Transfer` moves the same lot to the selected tank. Current truck inventory supplies pending-transfer recovery. Kanoa remains the source of truth for orders, operations, lots, assets, and inventory.

This is an exported implementation baseline, not runtime acceptance evidence. See the feature quickstart for the outstanding Gateway checks.

