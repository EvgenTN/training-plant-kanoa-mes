# Quickstart: Validate Kanoa UI Alignment for Operator Receiving

This guide validates the presentation and hosting changes in
`specs/002-operator-receiving-kanoa-ui/spec.md`. It does not replace the functional acceptance run
in `specs/001-operator-receiving/quickstart.md`; run both before release. Use only the local
Training Plant environment and a non-production database. Do not reset or reseed the database.

## Prerequisites

- Docker Compose stack is running and the KanoaMES project is loaded by the Gateway
  (`docker compose ps`, then `docker compose logs -f kanoa` if needed).
- Gateway is reachable at <http://localhost:8088> or the configured Traefik host.
- An operator account with the 001 receiving role scope can sign in.
- At least one eligible scheduled order exists, plus enabled Receiving trucks and Bulk Storage
  tanks, so the real controls and feedback can be exercised.
- The 001 receiving views and shared script package are present under `services/ignition/projects/`.

## 1. Offline structural checks

Run from the repository root.

1. Validate the changed JSON exports parse cleanly:

   ```bash
   python3 -m json.tool services/ignition/projects/kanoaMES/com.inductiveautomation.perspective/page-config/config.json >/dev/null
   python3 -m json.tool services/ignition/projects/kanoaMES/com.inductiveautomation.perspective/views/training/receivingOrdersSchedule/view.json >/dev/null
   python3 -m json.tool services/ignition/projects/kanoaMES/com.inductiveautomation.perspective/views/training/receiveMaterial/view.json >/dev/null
   python3 -m json.tool services/ignition/projects/kanoaMES/com.inductiveautomation.perspective/views/training/pendingTransfers/view.json >/dev/null
   ```

2. Confirm `/receiving` has a docks block and that the marquee pages do not:

   ```bash
   python3 - <<'PY'
   import json
   p = 'services/ignition/projects/kanoaMES/com.inductiveautomation.perspective/page-config/config.json'
   c = json.load(open(p))
   assert 'docks' in c['pages']['/receiving'], 'receiving page has no docks'
   assert set(c['pages']['/receiving']['docks']) >= {'left', 'top', 'right'}
   assert all('docks' not in v for k, v in c['pages'].items() if k.startswith('/marquee'))
   print('page dock contract OK')
   PY
   ```

3. Confirm no forbidden style class remains in the receiving views:

   ```bash
   grep -R 'kanoa/button/primary' services/ignition/projects/kanoaMES/com.inductiveautomation.perspective/views/training || echo 'no invalid primary class'
   ```

4. Compare each class and template used by the views with the installed Kanoa resources in
   `services/ignition/projects/kanoaAPP/com.inductiveautomation.perspective/`
   (`style-classes/` and `views/kanoa/core/templates/`). See
   [contracts/component-contracts.md](contracts/component-contracts.md) for the required matrix.

**Expected**: all JSON parses, receiving has the three docks, marquee pages remain undocked, and no
class or template reference is missing.

**Evidence captured for this implementation**: the pre-change baseline is the `HEAD` version of
the three `view.json` exports and the `/receiving` page config, recoverable with `git diff` (no
separate snapshot artifact was created); the four `python3 -m json.tool` checks passed; the
dock assertion and the `kanoa/button/primary` absence check passed; every `kanoa/font/*`,
`kanoa/button/*`, and embedded `kanoa/core/templates/*` reference in the three receiving views
was checked against the installed `kanoaAPP` resources and resolved. All 42 event scripts and
binding transforms in the three views were also syntax-checked. Gateway-dependent steps in
sections 2–6 were not run in the environment where these changes were made (no Docker/Gateway
access) and remain validation gates.

## 2. Deploy and navigation setup

1. Save/import the exported `kanoaMES` project resources through the normal Ignition project
   workflow. Mounting the directory alone does not prove the Gateway loaded the changes.
2. Confirm or register the Receiving navigation entries in Kanoa
   **Configuration → Application → Navigation** for project `kanoaMES`, using the names, view paths,
   type, and role scope in [contracts/page-and-navigation.md](contracts/page-and-navigation.md).
3. Record the Gateway export/backup artifact that contains these navigation records. If no supported
   export mechanism exists, report the unresolved deployment gate in the change evidence.
4. Reload the Perspective session (or open a fresh tab) and sign in as a receiving operator.

## 3. Shell and navigation acceptance

1. Open `/receiving` directly in the browser.
2. Confirm the standard Kanoa header across the top and the navigation sidebar on the left. Open the
   options dock and confirm it behaves as on the home page.
3. In the sidebar, confirm the Receiving group and its three entries are visible and that the active
   entry is identifiable.
4. Use the sidebar to go to another Kanoa area and back to the order schedule without typing an
   address.
5. Move through the in-flow actions: **Confirm order** → **Back to schedule** / **Pending transfers**
   → **Receiving schedule**. Confirm the header and sidebar stay visible throughout.
6. Open a configured marquee page and confirm it remains full-screen without header or sidebar.

**Expected**: FR-001 through FR-004 and SC-001/SC-008 are satisfied; no receiving view renders its
own copy of the shell.

## 4. Component and feedback acceptance

Work through the component roles in
[contracts/component-contracts.md](contracts/component-contracts.md) on each screen.

1. **Schedule**: confirm the date range control, table, labels and buttons match a reference Kanoa
   screen. Trigger refresh with no matching orders and confirm a Kanoa-style empty state.
2. **Receive Material**: confirm order details are read-only and clearly non-editable, quantity is
   entered through the Kanoa numeric input in kg, and truck/tank use scoped Kanoa asset selectors.
   Confirm primary and secondary actions use installed Kanoa button classes.
3. **Feedback**: submit a missing or non-positive quantity and a missing/ineligible asset. Confirm
   Kanoa error feedback appears and no receipt is written. Complete a valid receipt and confirm the
   Kanoa success toast includes order, lot, quantity, truck and tank.
4. **Pending Transfers**: use the documented non-destructive transfer failure simulation from the
   001 feature, then confirm the pending table, tank selector, retry action, and feedback follow the
   same Kanoa conventions.

**Expected**: zero screen-specific look-alike controls; all default/focus/disabled/invalid/read-only
states follow the reused components; success and error messages use the Kanoa feedback channels.

## 5. Theme and constrained-width acceptance

1. Switch through each Kanoa theme available in the session. On every receiving screen, confirm text,
   controls, table rows, and messages remain readable and no hard-coded color clashes appear.
2. Narrow the browser to a constrained width (for example, below the configured 480px breakpoint,
   or use browser device tooling). Confirm the sidebar collapses/hides as elsewhere, the receiving
   content remains usable, tables scroll or wrap, and all required actions are reachable.
3. Return to normal width and confirm the layout restores without a session reload.

**Expected**: FR-011/FR-012 and SC-004/SC-005 are satisfied.

## 6. Functional regression gate

1. Rerun the 001 receiving acceptance scenarios, including quantity enforcement, stale order
   checks, invalid asset checks, transfer failure/retry, and uncertain-result reconciliation.
2. Confirm that no step requires Lot Manager and that all 001 outcomes are unchanged by the UI work.

**Expected**: SC-006 passes with zero functional regressions. If a receiving rule changes, stop and
treat it as a defect in this feature.

## Evidence to record

- Commands run and their observed output for the offline checks.
- Screenshots or screen recordings of each receiving screen with the shell, in each theme, and at a
  constrained width.
- The navigation configuration export/backup artifact reference.
- Results of the 001 functional regression run, including any simulated failure steps.
- Any unresolved deviations from the contracts, with justification.

**Deployment gate (unresolved in this environment)**: the Receiving navigation tree
(`contracts/page-and-navigation.md`) is Kanoa application configuration, not a checked-in view
export. No Gateway or supported navigation export/backup artifact was available here, so the
navigation registration and its artifact reference must be recorded by the deployer before US1
can be marked fully verified.
