---
description: "Task list for Kanoa UI Alignment for Operator Receiving"
---

# Tasks: Kanoa UI Alignment for Operator Receiving

**Input**: Design documents from `/specs/002-operator-receiving-kanoa-ui/`

**Prerequisites**: [plan.md](plan.md), [spec.md](spec.md), [research.md](research.md),
[data-model.md](data-model.md), [contracts/](contracts/), [quickstart.md](quickstart.md),
`.specify/memory/constitution.md`

**Tests**: No automated test tasks are included. The feature specification does not request tests;
validation is performed through manual Gateway checks in [quickstart.md](quickstart.md) and offline
structural checks. Constitution Principle V requires recording that evidence.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing.
US2, US3, and US4 all edit the same three `view.json` exports, so they are independently testable
but must be executed sequentially unless separate worktrees are used.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (US1–US4)
- Include exact file paths in descriptions

## Path Conventions

- Receiving page config: `services/ignition/projects/kanoaMES/com.inductiveautomation.perspective/page-config/config.json`
- Receiving views: `services/ignition/projects/kanoaMES/com.inductiveautomation.perspective/views/training/<screen>/view.json`
- Inherited Kanoa resources (read-only): `services/ignition/projects/kanoaAPP/com.inductiveautomation.perspective/`
- Shared client scripts/views (normally unchanged): `services/ignition/projects/KANOA_SCRIPTS/`

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Confirm the workspace, design inputs, and local runtime are ready.

- [X] T001 Review feature design inputs before editing: [spec.md](spec.md), [plan.md](plan.md), [data-model.md](data-model.md), [contracts/component-contracts.md](contracts/component-contracts.md), and [contracts/page-and-navigation.md](contracts/page-and-navigation.md)
- [X] T002 Validate current JSON exports parse with `python3 -m json.tool` for `services/ignition/projects/kanoaMES/com.inductiveautomation.perspective/page-config/config.json` and all three `services/ignition/projects/kanoaMES/com.inductiveautomation.perspective/views/training/*/view.json` files
- [ ] T003 Confirm the local stack is running and the gateway is reachable as documented in `docker-compose.yaml` and [quickstart.md](quickstart.md) (`docker compose ps`; do not reset or reseed volumes)

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Establish the component inventory, baseline, and deployment gates before changing any screen.

**⚠️ CRITICAL**: No user story work can begin until this phase is complete.

- [X] T004 [P] Audit available Kanoa templates and style classes under `services/ignition/projects/kanoaAPP/com.inductiveautomation.perspective/views/kanoa/core/templates/` and `services/ignition/projects/kanoaAPP/com.inductiveautomation.perspective/style-classes/`; record any component that is missing versus [contracts/component-contracts.md](contracts/component-contracts.md)
- [X] T005 [P] Confirm the inheritance chain in `services/ignition/projects/kanoaMES/project.json`, `services/ignition/projects/kanoaAPP/project.json`, and `services/ignition/projects/KANOA_SCRIPTS/project.json`; do not edit `kanoaAPP`
- [X] T006 Snapshot the current three receiving screens and the current Receiving navigation tree as the visual/configuration baseline, following [quickstart.md](quickstart.md); record the snapshot location in the pull request Testing section
- [X] T007 If T004 finds a genuine component gap, add one reusable view under `services/ignition/projects/KANOA_SCRIPTS/com.inductiveautomation.perspective/views/` and reference it from all receiving screens; if no gap exists, record "no shared component required" in [research.md](research.md) R7
- [X] T008 Confirm no MES data or receiving-rule change is planned: the shared script package in `services/ignition/projects/KANOA_SCRIPTS/ignition/script-python/kanoaScripts/custom/ops/receiving/` and the API contract in `specs/001-operator-receiving/contracts/receiving-application.md` remain the source of truth

**Checkpoint**: Component inventory, baseline, and project boundaries confirmed; user story work can begin.

---

## Phase 3: User Story 1 - Work inside the standard Kanoa application shell (Priority: P1) 🎯 MVP

**Goal**: All three receiving screens render inside the Kanoa header and navigation sidebar, with working navigation and active-location indication.

**Independent Test**: Open `/receiving` directly, confirm header and sidebar render, move through schedule → receipt → pending transfers and back, navigate away and return using the sidebar only, and confirm marquee pages remain undocked.

- [X] T009 [US1] Add a `docks` block to the `/receiving` page in `services/ignition/projects/kanoaMES/com.inductiveautomation.perspective/page-config/config.json` by copying the `left` (NavBar), `top` (header), and `right` (options) dock entries from the `/` page exactly, including `autoBreakpoint: 480` and `push` content
- [X] T010 [US1] Set the `/receiving` page title and confirm its `viewPath` remains `training/receivingOrdersSchedule` in `services/ignition/projects/kanoaMES/com.inductiveautomation.perspective/page-config/config.json`
- [X] T011 [P] [US1] Confirm in-flow navigation in `services/ignition/projects/kanoaMES/com.inductiveautomation.perspective/views/training/receivingOrdersSchedule/view.json` still uses `system.perspective.navigate(view=...)` so the root view changes without changing the docked page
- [X] T012 [P] [US1] Confirm in-flow navigation in `services/ignition/projects/kanoaMES/com.inductiveautomation.perspective/views/training/receiveMaterial/view.json` still uses `system.perspective.navigate(view=...)` and does not add a local header/sidebar
- [X] T013 [P] [US1] Confirm in-flow navigation in `services/ignition/projects/kanoaMES/com.inductiveautomation.perspective/views/training/pendingTransfers/view.json` still uses `system.perspective.navigate(view=...)` and does not add a local header/sidebar
- [ ] T014 [US1] Register or confirm the Receiving parent and the three View-type entries (`training/receivingOrdersSchedule`, `training/receiveMaterial`, `training/pendingTransfers`) in Kanoa Configuration → Application → Navigation for project `kanoaMES`, following [contracts/page-and-navigation.md](contracts/page-and-navigation.md)
- [X] T015 [US1] Record the navigation configuration export/backup artifact reference in [quickstart.md](quickstart.md) under "Evidence to record"; report an unresolved deployment gate if no supported export exists
- [ ] T016 [US1] Verify US1 independently: direct URL `/receiving`, all three docks visible, active Receiving entry identifiable, in-flow navigation keeps the shell, sidebar navigation away/back works, and `/marquee/*` pages remain undocked (checks in [quickstart.md](quickstart.md) §3)

**Checkpoint**: US1 is functional and testable on its own; the MVP shell is in place.

---

## Phase 4: User Story 2 - Use familiar Kanoa inputs and actions on the receiving forms (Priority: P1)

**Goal**: Every receiving control uses an established Kanoa template, style class, or configured table convention, with correct bindings and states.

**Independent Test**: Compare each control on all three screens against a reference Kanoa screen; verify date range, quantity, truck/tank selectors, tables, read-only values, and primary/secondary buttons match the component matrix, and confirm a full receipt can still be entered and submitted.

- [X] T017 [P] [US2] Replace raw `dtStart`/`dtEnd` inputs in `services/ignition/projects/kanoaMES/com.inductiveautomation.perspective/views/training/receivingOrdersSchedule/view.json` with `kanoa/core/templates/selectors/date/dateRangeSelectorCompact`, binding `props.params.startDate` and `props.params.endDate` bidirectionally to `view.custom.startDate` / `view.custom.endDate`
- [X] T018 [US2] Rework `tblOrders` in `services/ignition/projects/kanoaMES/com.inductiveautomation.perspective/views/training/receivingOrdersSchedule/view.json` to Kanoa table conventions (explicit columns, `cells.style.fontSize`, header titles, sort/filter/selection settings) per [contracts/component-contracts.md](contracts/component-contracts.md)
- [X] T019 [US2] Replace `kanoa/font/bodyMedium` screen title and flat/primary buttons in `services/ignition/projects/kanoaMES/com.inductiveautomation.perspective/views/training/receivingOrdersSchedule/view.json` with a Kanoa heading class and `kanoa/button/filled` / `kanoa/button/outlined` classes; remove every non-existent class such as `kanoa/button/primary`
- [X] T020 [P] [US2] Replace raw `numActualQty` numeric entry in `services/ignition/projects/kanoaMES/com.inductiveautomation.perspective/views/training/receiveMaterial/view.json` with `kanoa/core/templates/inputs/numberInput`, binding `props.params.value` bidirectionally to `view.custom.actualQty` and setting `label` and `units` to `kg`
- [X] T021 [US2] Replace raw `ddTruck` and `ddTank` dropdowns in `services/ignition/projects/kanoaMES/com.inductiveautomation.perspective/views/training/receiveMaterial/view.json` with `kanoa/core/templates/selectors/assetDropdownSelector`, binding `props.params.selectedPath` bidirectionally to `view.custom.truckPath` / `view.custom.tankPath` and setting scoped `props.params.value.parentPath` for `Training Plant\\Receiving` and `Training Plant\\Bulk Storage`
- [X] T022 [US2] Present read-only order fields in `services/ignition/projects/kanoaMES/com.inductiveautomation.perspective/views/training/receiveMaterial/view.json` using `kanoa/core/templates/displays/valueWithLabel` or `numLabel`, or Kanoa font classes with no input affordance, per [data-model.md](data-model.md)
- [X] T023 [US2] Fix title, section labels, and action buttons in `services/ignition/projects/kanoaMES/com.inductiveautomation.perspective/views/training/receiveMaterial/view.json`: `kanoa/button/filled` for Confirm receipt / Retry transfer, `outlined` or `flat` for Back / Pending transfers, no `kanoa/button/primary`
- [X] T024 [P] [US2] Replace raw `ddTank` dropdown in `services/ignition/projects/kanoaMES/com.inductiveautomation.perspective/views/training/pendingTransfers/view.json` with `kanoa/core/templates/selectors/assetDropdownSelector`, binding `selectedPath` bidirectionally to the selected tank path with Bulk Storage scoping
- [X] T025 [US2] Rework `tblPendingTransfers` in `services/ignition/projects/kanoaMES/com.inductiveautomation.perspective/views/training/pendingTransfers/view.json` to Kanoa table conventions for lot, quantity, order, and current truck columns
- [X] T026 [US2] Fix title, labels, and buttons in `services/ignition/projects/kanoaMES/com.inductiveautomation.perspective/views/training/pendingTransfers/view.json`: `filled` for Retry, `flat`/`outlined` for Refresh and Back, and a Kanoa heading class for the title
- [ ] T027 [US2] Verify US2 independently by auditing the three view exports against the matrix in [contracts/component-contracts.md](contracts/component-contracts.md) and completing one valid receipt, confirming every control keeps the same view custom state used by the unchanged receiving scripts

**Checkpoint**: All receiving controls use Kanoa components; US1 still passes.

---

## Phase 5: User Story 3 - See consistent Kanoa feedback and states (Priority: P2)

**Goal**: Loading, empty, success, validation, and error states use Kanoa feedback patterns and remain actionable.

**Independent Test**: Trigger loading, empty schedule, invalid quantity/asset, successful receipt, and failed transfer; confirm each state uses the Kanoa progress bar, empty state, toast, or popup pattern from [contracts/component-contracts.md](contracts/component-contracts.md).

- [X] T028 [P] [US3] Add `kanoa/core/templates/displays/progressBar` and a Kanoa-styled empty state to `services/ignition/projects/kanoaMES/com.inductiveautomation.perspective/views/training/receivingOrdersSchedule/view.json`, driven by `view.custom.loading` and an empty `view.custom.orders`
- [X] T029 [US3] Replace inline `lblError`/`lblResult` labels in `services/ignition/projects/kanoaMES/com.inductiveautomation.perspective/views/training/receivingOrdersSchedule/view.json` with `system.kanoa.toast.show` calls (`error`/`warning`/`success`) and a `kanoa/core/templates/displays/messagePopup` for blocking details
- [X] T030 [P] [US3] Add waiting indication and validation feedback to `services/ignition/projects/kanoaMES/com.inductiveautomation.perspective/views/training/receiveMaterial/view.json` using `progressBar` and the `numberInput`/selector components' invalid states
- [X] T031 [US3] Replace inline `lblError`/`lblResult`/`lblConfirmation` labels in `services/ignition/projects/kanoaMES/com.inductiveautomation.perspective/views/training/receiveMaterial/view.json` with `system.kanoa.toast.show` for success/error and `kanoa/core/templates/inputs/confirm` for receipt confirmation, preserving the exact success identifiers required by FR-013
- [X] T032 [P] [US3] Add loading indication and an empty pending list state to `services/ignition/projects/kanoaMES/com.inductiveautomation.perspective/views/training/pendingTransfers/view.json` using `progressBar` and Kanoa-styled empty messaging
- [X] T033 [US3] Replace inline `lblError`/`lblResult` labels in `services/ignition/projects/kanoaMES/com.inductiveautomation.perspective/views/training/pendingTransfers/view.json` with `system.kanoa.toast.show` and `kanoa/core/templates/displays/messagePopup`, preserving the pending-recovery message that the lot remains at the truck
- [ ] T034 [US3] Verify US3 independently by running the feedback scenarios in [quickstart.md](quickstart.md) §4, including the non-destructive transfer-failure simulation from `specs/001-operator-receiving/quickstart.md`

**Checkpoint**: All receiving screens provide Kanoa feedback in every presentation state; US1 and US2 still pass.

---

## Phase 6: User Story 4 - Keep all receiving screens consistent across themes and screen sizes (Priority: P3)

**Goal**: The three screens remain readable and operable in every supported Kanoa theme and at constrained widths.

**Independent Test**: Display all three screens in each configured theme and at a constrained width; confirm no clipping, hard-coded color clashes, or unreachable controls.

- [X] T035 [P] [US4] Adjust root and content flex containers in `services/ignition/projects/kanoaMES/com.inductiveautomation.perspective/views/training/receivingOrdersSchedule/view.json` so the date range, table, and actions wrap/scroll at constrained widths without custom colors
- [X] T036 [P] [US4] Adjust root and content flex containers in `services/ignition/projects/kanoaMES/com.inductiveautomation.perspective/views/training/receiveMaterial/view.json` so read-only summary, quantity input, selectors, and action row remain reachable at constrained widths
- [X] T037 [P] [US4] Adjust root and content flex containers in `services/ignition/projects/kanoaMES/com.inductiveautomation.perspective/views/training/pendingTransfers/view.json` so the table and tank/action row remain reachable at constrained widths
- [X] T038 [US4] Audit every class and template reference in the three receiving `view.json` files against `services/ignition/projects/kanoaAPP/com.inductiveautomation.perspective/style-classes/` and `views/kanoa/core/templates/`, and remove any hard-coded presentation color introduced during US2/US3
- [ ] T039 [US4] Verify US4 independently by running theme and constrained-width checks in [quickstart.md](quickstart.md) §5 on all three screens

**Checkpoint**: All four user stories are independently functional and visually consistent.

---

## Phase 7: Polish & Cross-Cutting Concerns

**Purpose**: Final evidence, documentation, and regression gate.

- [X] T040 [P] Update the receiving section of `docs/solution-design.md` to note that receiving screens use the Kanoa shell and inherited Kanoa components, without changing the 001 business rules
- [X] T041 [P] Re-run the offline structural checks in [quickstart.md](quickstart.md) §1, including the docks assertion and the `kanoa/button/primary` absence check, on the final exports
- [ ] T042 Re-run the complete [quickstart.md](quickstart.md) validation and the 001 receiving acceptance scenarios in `specs/001-operator-receiving/quickstart.md`; record results, screenshots, and any deviations under "Evidence to record"
- [X] T043 Review the final diff for constitution compliance: no `kanoaAPP` edits, no new MES tables or direct SQL, no image/module/version changes, no secrets, and all changed Ignition resources exported completely

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies; start immediately.
- **Foundational (Phase 2)**: Depends on Setup; **blocks all user stories**.
- **User Stories (Phases 3–6)**: US1 → US2 → US3 → US4 recommended. US2, US3, and US4 are logically independent in acceptance terms, but all edit the same three `view.json` files and must therefore run sequentially in one workspace.
- **Polish (Phase 7)**: Depends on all desired user stories being complete.

### User Story Dependencies

- **US1 (P1)**: After Foundational. No dependency on other stories. MVP increment.
- **US2 (P1)**: After US1 in a single workspace because it edits view files that US1 inspects; independently testable against the component matrix.
- **US3 (P2)**: After US2 in a single workspace because it edits the same view files; independently testable through the feedback scenarios.
- **US4 (P3)**: After US3 in a single workspace because it edits the same view files; independently testable through theme/width checks.

### Within Each User Story

- Complete structural checks before Gateway verification for that story.
- Reuse inherited resources; do not copy vendor views locally.
- Run the story's independent test before moving to the next story.
- Record evidence after each checkpoint (constitution Principle V).

### Parallel Opportunities

- T004/T005 can run in parallel; T028/T030/T032 (progress-bar edits) and T035/T036/T037 (responsive edits) touch different files.
- US2 date-range, quantity, and tank-selector replacements (T017, T020, T024) touch different files and can run in parallel.
- Within one file, tasks are sequential because they share `view.json`.

## Parallel Example: User Story 1

```bash
# After T010, verify the three view files in parallel:
Task: "Confirm view-based navigation in .../training/receivingOrdersSchedule/view.json"  # T011
Task: "Confirm view-based navigation in .../training/receiveMaterial/view.json"          # T012
Task: "Confirm view-based navigation in .../training/pendingTransfers/view.json"         # T013
```

## Parallel Example: User Story 2

```bash
# Different files, no shared state:
Task: "Replace date inputs in receivingOrdersSchedule/view.json"  # T017
Task: "Replace quantity input in receiveMaterial/view.json"       # T020
Task: "Replace tank selector in pendingTransfers/view.json"       # T024
```

## Parallel Example: User Story 3

```bash
# Different files, no shared state:
Task: "Add progress/empty states to receivingOrdersSchedule/view.json"  # T028
Task: "Add waiting/validation feedback to receiveMaterial/view.json"    # T030
Task: "Add loading/empty states to pendingTransfers/view.json"          # T032
```

## Parallel Example: User Story 4

```bash
# Different files, no shared state:
Task: "Responsive containers in receivingOrdersSchedule/view.json"  # T035
Task: "Responsive containers in receiveMaterial/view.json"          # T036
Task: "Responsive containers in pendingTransfers/view.json"         # T037
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1 and Phase 2 (foundation blocks all stories).
2. Complete Phase 3 (US1 shell and navigation).
3. **STOP and VALIDATE**: run the US1 independent test; confirm docks on `/receiving`, working sidebar navigation, and unchanged marquee pages.
4. Deploy/demo the shell increment before restyling controls.

### Incremental Delivery

1. Setup + Foundational → foundation ready.
2. US1 → shell visible → test independently → deploy/demo (MVP).
3. US2 → Kanoa controls on all screens → test independently → deploy/demo.
4. US3 → Kanoa feedback states → test independently → deploy/demo.
5. US4 → theme and width consistency → test independently → deploy/demo.
6. Polish → full validation and evidence.

### Parallel Team Strategy

With multiple developers and separate worktrees, US2/US3/US4 could be assigned to different developers,
but each worktree must be rebased before merging because all three touch the same view exports. In a
single workspace, follow the sequential US1 → US2 → US3 → US4 order.

---

## Notes

- [P] tasks use different files and have no dependencies on incomplete tasks.
- [Story] maps each task to the user stories in [spec.md](spec.md).
- Gateway-only steps (navigation registration, visual checks) reference their contract or validation
  guide file so every task has a concrete path.
- Do not modify vendor-managed `kanoaAPP` or the 001 receiving business logic.
- Commit after each task or logical group; evidence must be recorded before claiming completion.

## Implementation Status

36 of 43 tasks are complete. The following tasks remain open because this environment has no
Docker/Gateway/database access and no Kanoa Navigation export artifact; they are deployment-time
validation gates, not missing source changes:

- **T003** — confirm the local stack is reachable (`docker compose ps`; Docker is unavailable here).
- **T014** — register/confirm the three Receiving navigation entries in Kanoa Configuration.
- **T016** — US1 browser verification of docks, shell persistence, and marquee behavior.
- **T027** — US2 browser verification, including one valid end-to-end receipt.
- **T034** — US3 feedback scenarios, including the 001 transfer-failure simulation.
- **T039** — US4 theme and constrained-width browser checks.
- **T042** — full quickstart run plus the 001 functional regression acceptance run.

All offline source checks pass: see the evidence note in [quickstart.md](quickstart.md) §1.
