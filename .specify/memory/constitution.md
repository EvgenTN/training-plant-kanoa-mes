<!--
Sync Impact Report:
- Version change: none → 1.0.0
- Modified principles: N/A (initial adoption)
- Added principles:
  - I. Version-Controlled Gateway State
  - II. Respect Ignition Project Boundaries
  - III. Jython 2.7 and Ignition API Compatibility
  - IV. API-First, Idempotent Data Operations
  - V. Verifiable, Observable Changes (NON-NEGOTIABLE)
- Added sections:
  - Technology & Environment Constraints
  - Development Workflow & Quality Gates
- Removed sections: N/A
- Templates requiring updates: none; dependent templates resolve this constitution at runtime.
- Follow-up TODOs: none.
-->

# Training Plant Kanoa MES Constitution

## Core Principles

### I. Version-Controlled Gateway State

The repository is the source of truth for every runtime artifact: `docker-compose.yaml`,
`services/ignition/config`, `services/ignition/projects`, pinned module files, and import/seed
inputs. Changes made in Ignition Designer MUST be exported to the mounted project and config
directories and committed. A clean checkout MUST reproduce the documented local stack without
manual Designer-only edits. Container image tags and third-party module versions MUST remain
pinned; upgrades MUST update the pin and include verification evidence. Generated runtime state,
including `.env`, logs, database volumes, and local overrides, MUST NOT be committed.

**Rationale**: Reproducibility and reviewability depend on treating the Gateway, database, and
modules as versioned code rather than opaque local state.

### II. Respect Ignition Project Boundaries

`KANOA_SCRIPTS` is the shared inheritable project for reusable and client-specific scripts.
`kanoaAPP` is vendor-managed and explicitly marked "Do not edit this project"; client-specific
behavior MUST be implemented in `KANOA_SCRIPTS` or in a runnable child project unless an explicit,
documented exception is approved. The runnable projects `kanoaMES`, `kanoaMobile`, `kanoaTablet`,
and `kanoaMarquee` inherit from `kanoaAPP`; inherited resources MUST NOT be duplicated. WebDev
resources MUST enable only the HTTP methods they implement, and any unauthenticated or non-HTTPS
access MUST be justified in the change description. Third-party modules MUST be treated as
dependencies; vendor module contents MUST NOT be patched in this repository.

**Rationale**: Project inheritance and vendor-managed resources are part of the product
architecture. Breaking those boundaries makes module upgrades unsafe and creates conflicting
customizations.

### III. Jython 2.7 and Ignition API Compatibility

All Python executed inside Ignition MUST run under Jython 2.7 in the pinned Ignition 8.3 runtime.
Gateway code MUST NOT use Python 3-only syntax, `pip`, native CPython packages, or unsupported
third-party libraries. Code MUST use Ignition and Java APIs, including `system.*`, `java.*`, and
KanoaMES `system.kanoa.*` modules. Standalone tooling outside the Gateway MUST state its runtime
and MUST be validated with that runtime. Ignition code MUST follow the existing conventions:
tab indentation, lowerCamelCase function names, docstrings with `Args`, `Returns`, and `Updated`
sections where applicable, and explicit handling of Gateway versus Designer scope.

**Rationale**: Ignition executes scripts in a constrained Jython environment. CPython habits and
unstated runtime assumptions produce failures that syntax checks alone cannot detect.

### IV. API-First, Idempotent Data Operations

Application logic MUST use KanoaMES `system.kanoa.*` APIs for MES reads and writes. Direct SQL is
permitted only when no supported API exists, and then it MUST be parameterized, documented, and
reviewed for schema compatibility. Scripts that mutate MES data MUST be idempotent: they MUST
look up existing records by stable business keys before inserting, skip or update existing
records, and preserve case-insensitive path and name matching where the Kanoa APIs require it.
Required inputs MUST be validated before any write. Exceptions MUST NOT be silently swallowed;
failures MUST return an actionable result and MUST preserve enough context for diagnosis. Schema
changes MUST be additive or migration-safe and MUST NOT take ownership of vendor-managed tables.

**Rationale**: Duplicate assets, lots, items, and events corrupt MES reporting. API-first and
idempotent operations keep data consistent and make reruns safe.

### V. Verifiable, Observable Changes (NON-NEGOTIABLE)

No change is complete without a verification path. Every pull request MUST describe how the change
was verified in the Testing section, including exact commands or Gateway steps and the expected
result. Standalone Python MUST pass a syntax check such as `python3 -m py_compile`; Ignition
changes MUST be exercised against the running local Gateway or a documented mock. Mutating
operations SHOULD be rerun to prove idempotency. Where an automated test harness exists, relevant
tests MUST pass. Mutating scripts MUST log start and outcome through a named
`system.util.getLogger` logger, and error logs MUST include the operation, affected identifiers,
and cause without exposing secrets. Changes that cannot be verified MUST NOT be merged.

**Rationale**: The repository has limited automated coverage. Explicit verification and logging
are the minimum controls that prevent unobserved data corruption and unreproducible fixes.

## Technology & Environment Constraints

- Runtime baseline: Ignition `8.3.10`, KanoaMES `1.15.11`, Embr Charts `6.0.1`, SQL Server `2022`
  Developer edition, and Jython 2.7 inside the Gateway.
- The Docker Compose stack is for local development only. Deploying it as-is to production
  violates Microsoft SQL Server licensing terms and is prohibited.
- `SA_PASSWORD` MUST come from the environment or `.env`; `.env` MUST remain gitignored. Secrets,
  customer data, and production credentials MUST NOT be committed to the repository.
- The application database defaults to `kanoa`, and the Ignition connection is `kanoaCore`.
  Changing `DB_NAME` requires a matching change to
  `services/ignition/config/resources/core/ignition/database-connection/kanoaCore/config.json`.
- Gateway access uses port `8088` or the external Traefik proxy. Database port `1433` MUST be
  exposed only when local tooling requires it.
- Third-party `.modl` files and container image versions MUST remain pinned. Upgrades are explicit
  changes with compatibility and regression verification.
- Destructive operations, including `docker compose down -v`, database resets, and bulk data
  imports or seeds, MUST be run only with explicit intent and a stated recovery plan.
- Docker Compose is the documented interface. Podman Compose is acceptable where Docker is
  unavailable, but behavior and validation MUST match the documented Compose workflow.

## Development Workflow & Quality Gates

1. Before implementation, identify the owning Ignition project, the runtime scope (Gateway,
   Designer, Perspective session, WebDev, or standalone), and the data impact.
2. Implement reusable or client-specific logic in `KANOA_SCRIPTS`. Do not modify `kanoaAPP` for
   client-specific behavior without the documented exception required by Principle II.
3. Export Designer changes completely, including `resource.json`, `config.json`, project metadata,
   and any changed scripts. Do not commit unrelated Designer re-exports.
4. Validate scripts with the appropriate runtime check, then exercise the change against the
   running stack. For data mutations, verify both the first run and a rerun.
5. Record verification commands, observed results, and any manual Gateway checks in the pull
   request Testing section. If the existing checklist item "Tests pass" is not applicable, state
   why and provide the manual evidence instead.
6. Reviewers MUST verify constitution compliance, secret safety, pinned versions, project
   boundaries, idempotency, error handling, logging, and rollback or migration notes for breaking
   changes.
7. Feature plans MUST include a Constitution Check against these principles. Any violation MUST be
   recorded with its justification and the simpler alternative that was rejected.
8. Update `README.md`, `.env.example`, or operational documentation whenever configuration,
   startup behavior, access methods, or required environment variables change.

## Governance

This constitution supersedes conflicting local practices. When a documented procedure, template,
or habit conflicts with these principles, the constitution takes precedence unless an approved
amendment changes it.

Amendments require a pull request that states the motivation, the affected principles or sections,
and any migration impact. The author MUST update the Sync Impact Report, version line, and dates in
the same change. At least one repository maintainer MUST approve the amendment before merge.
Clarifications that do not change meaning are PATCH updates; new principles or materially expanded
guidance are MINOR updates; incompatible removals or redefinitions are MAJOR updates. The initial
adoption is version `1.0.0`.

All pull requests and reviews MUST verify compliance with this constitution. Complexity or
deviations MUST be justified in the pull request or in the plan's Complexity Tracking section.
Runtime procedures belong in `README.md` and `.env.example`; this document defines governance and
non-negotiable engineering standards.

**Version**: 1.0.0 | **Ratified**: 2026-11-13 | **Last Amended**: 2026-11-13
