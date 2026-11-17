# Contract: Receiving Page and Navigation

## Purpose

Defines the externally visible hosting contract for the operator receiving screens: the page that
provides the Kanoa shell, the dock set it must use, and the Kanoa Navigation entries that make the
screens reachable and identifiable.

## Page Contract

**Page ID**: `/receiving`
**Project**: `kanoaMES`
**Root view**: `training/receivingOrdersSchedule`

The page MUST declare a `docks` object equivalent to the `/` page definition in
`services/ignition/projects/kanoaMES/com.inductiveautomation.perspective/page-config/config.json`:

| Dock position | ID | viewPath | show | handle | autoBreakpoint | size |
|---|---|---|---|---|---|---|
| left | `NavBar` | `kanoa/core/docks/navigation/navigation` | `onDemand` | `autoHide` | 480 | 260 |
| top | (empty, as in `/`) | `kanoa/core/docks/header/header` | `visible` | `hide` | 480 | 50 |
| right | `options` | `kanoa/core/docks/options` | `onDemand` | `hide` | 480 | 200 |

Anchor `fixed`, content `push`, `modal` false, `resizable` false, and empty `viewParams` MUST be
retained for each dock. The `cornerPriority: top-bottom` setting in `sharedDocks` is unchanged.

### Invariants

1. All three receiving views are opened as views on this page via `system.perspective.navigate(view=...)`;
   view navigation does not change the page or browser address, so the docks persist.
2. No receiving view embeds a header or sidebar of its own.
3. The `/marquee/*` pages MUST NOT gain docks; `sharedDocks` MUST NOT be used for the shell.
4. Direct URL access to `/receiving` MUST render the shell even if the operator did not come from
   the home page.

## Navigation Contract

Navigation records are Kanoa application configuration, not repository view files. The following
entries MUST be confirmed or created in **Configuration → Application → Navigation** for project
`kanoaMES` and the operator roles used by the 001 feature:

| Parent | Entry name | Type | Path | Enabled |
|---|---|---|---|---|
| Receiving | Order Schedule | View | `training/receivingOrdersSchedule` | yes |
| Receiving | Receive Material | View | `training/receiveMaterial` | yes |
| Receiving | Pending Transfers | View | `training/pendingTransfers` | yes |

### Invariants

1. Sidebar navigation opens each receiving view without manual URL entry.
2. The active receiving entry is identifiable in the sidebar while its view is displayed.
3. Receiving entries use the same project and role scope as the 001 receiving workflow.
4. The Gateway export/backup artifact that contains these navigation records MUST be identified and
   recorded in the implementation evidence so the configuration can be reproduced. If no supported
   export mechanism exists, the deployment gate remains unresolved and must be reported, not
   silently accepted.

## Verification Hooks

- Compare the `/receiving` `docks` block with the `/` `docks` block for structural equivalence.
- Open `/receiving` directly and confirm all three docks render.
- Move through schedule → receipt → pending transfer → schedule and confirm the shell remains.
- Open the sidebar and navigate away and back without typing an address.
- Confirm marquee pages remain full-screen with no header/sidebar.
