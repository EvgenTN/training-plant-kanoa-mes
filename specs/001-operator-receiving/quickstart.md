# Quickstart: Validate Operator Bulk Receiving

This guide describes the Gateway acceptance run for the feature. Perform it only against the local Training Plant environment and a non-production database. Do not reset/reseed the database as part of validation.

## Current Implementation Status

The repository contains the three Perspective view exports under `services/ignition/projects/kanoaMES/com.inductiveautomation.perspective/views/training/` and the shared script module under `services/ignition/projects/KANOA_SCRIPTS/ignition/script-python/kanoaScripts/custom/ops/receiving/`. The view and script resources have only received offline structural/syntax checks. They have not been imported, exercised, or verified by the Gateway.

The current development session has no eligible receiving orders, so the receipt write, quantity enforcement, concurrency behavior, and transfer recovery cannot yet be accepted end to end. The user has confirmed that the Gateway page loads after login and shows no visible errors; that confirms access to the page, not that these new exports are loaded or that receipt behavior works. No navigation registration has been confirmed.

## Import and Navigation Setup

1. Confirm the view resources are in the runnable `kanoaMES` project under `training/` and save/deploy that project using the repository's normal Ignition project workflow. Keep the shared `receiving` script package in inheritable `KANOA_SCRIPTS`; do not put these resources in vendor-managed `kanoaAPP`. This repository mounts `services/ignition/projects` into the Gateway container, but that alone does not prove that the running Gateway has loaded these exports.
2. In Kanoa, open **Configuration → Application → Navigation**. Add a parent item named **Receiving**, set **Project** to `kanoaMES`, **Enabled** on, and **Roles** to the intended receiving operator role(s). Leave its **Type** unset if the editor supports a folder-only parent; otherwise use the editor's supported parent setup and record the resulting configuration.
3. Add child items under **Receiving** with **Type = View** and these view paths: `training/receivingOrdersSchedule` (name **Order Schedule**), `training/receiveMaterial` (name **Receive Material**), and `training/pendingTransfers` (name **Pending Transfers**). Apply the same project and role scope and save each item before making another edit.
4. Open the KanoaMES application as an operator and confirm all three items open. Record the Gateway export/backup artifact that captures the Navigation configuration; Kanoa stores it through its application configuration, not as one of the checked-in Perspective view files.

Kanoa's local docs describe Navigation fields for Name, Project, Roles, Type, Icon, Sort Order, and Enabled, and demonstrate adding a parent with custom view children. They do not provide a repository export format for these navigation records, so the exact export/restore mechanism must be recorded from the installed Gateway before release.

## Prerequisites

- Docker Compose stack and local Ignition Gateway are available.
- The KanoaMES 1.15.11 project is connected to the `kanoa` database.
- The Training Plant asset hierarchy contains enabled Storage Locations under `Training Plant\\Receiving` and `Training Plant\\Bulk Storage`.
- Kanoa has a receiving `Receive` operation, `Transfer` operation, an initial lot state, kg item unit, and a configured lot serial.
- At least one order is scheduled and in `Scheduled` or `In Progress` state, with an item and target quantity in kg.
- A receiving operator account can access the Receiving navigation item.

Use the already running local Gateway where available. Do not restart or reseed it just to run this acceptance procedure. Open the KanoaMES Perspective application and log in with an account authorized for the receiving workflow.

## Acceptance Run

### 1. Select and inspect an order

1. Open **Receiving Orders Schedule**.
2. Confirm that only scheduled orders in Scheduled or In Progress status are offered.
3. Select an order and confirm it.
4. Verify order number, description (or item description fallback), material, and target quantity are correct and read-only.

**Expected**: The receiving form reflects canonical order data; schedule display values cannot be edited or used to change the selected order.

### 2. Receive and transfer a valid partial quantity

1. Enter a positive quantity smaller than the remaining target.
2. Select an enabled truck under Receiving and an enabled tank under Bulk Storage.
3. Review and confirm.
4. Inspect the receipt result and Kanoa lot history/Lot Manager.

**Expected**: Exactly one new lot and Receive event are associated with the selected work order and truck. A separate Transfer event moves that same lot and quantity to the selected tank. The UI reports the lot number and both locations.

### 3. Validate cumulative target enforcement

1. Return to the same order and verify its remaining quantity reflects the successful partial receipt.
2. Attempt a quantity equal to the remainder; confirm it succeeds if the order remains eligible.
3. Attempt any additional positive quantity.

**Expected**: The final receipt up to target is allowed; any receipt beyond target is rejected before lot creation. Order totals match the sum of Receive output events, not production actual quantity.

### 4. Validate invalid/stale selections

Try zero, negative, and missing quantities; missing truck/tank; a disabled/out-of-area asset ID; and an order that has become ineligible since selection.

**Expected**: Each invalid submission shows an actionable message and creates no new lot or operation event.

### 5. Validate concurrent submissions

Use two operator sessions against an order with a small remaining quantity. Submit quantities whose combined total would exceed the remainder at nearly the same time.

**Expected**: The receiving flow serializes/rechecks the submissions; at most one is accepted and the stale submission is rejected without a lot or Receive event. If the pinned runtime cannot guarantee this, treat it as a release blocker rather than claiming the no-over-receipt criterion passes.

### 6. Validate transfer recovery

In an isolated test session, use the implementation's documented non-destructive failure simulation to force a transfer error after the Receive succeeds.

**Expected**: The UI says the lot remains at the truck. Retry on the current screen moves the existing lot only. After reopening the workflow, the pending-transfer list finds the lot from current truck inventory; the operator selects the lot and destination tank again. Exactly one Receive exists and one successful Transfer is added.

### 7. Validate uncertain outcomes and logs

Simulate a response timeout at each write boundary using the non-destructive test method documented by the implementation. Review the operator result and named Gateway log.

**Expected**: The system checks Kanoa lot/order events and current activity before allowing a retry. If the committed state cannot be determined, it requests reconciliation and does not blindly repeat receipt. Logs identify order, lot when known, operation, affected assets, and failure cause without secrets.

## Release Evidence

Record the Gateway build/version, user role, order ID, operation event IDs, lot name, actual quantity, truck/tank paths, each scenario's outcome, and the log entries for recoverable failures. Verify exported `resource.json`, Perspective `view.json`, and script-package resources are present in the correct project paths. Document Kanoa Application Navigation registration and its reproducible configuration/export procedure.

Before operator release, also confirm that the project resources are imported/loaded by the Gateway, that Navigation entries open the views from `kanoaMES` for the intended roles, and that the actual Gateway-scoped serialization behavior passes the concurrent-submission scenario. Leave the feature unregistered for operators until these gates pass.
