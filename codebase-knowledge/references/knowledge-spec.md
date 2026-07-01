# Codebase Knowledge Specification (OKF v0.1 conformant)

The complete content specification for a codebase knowledge base, shipped as an **Open Knowledge Format (OKF) v0.1** bundle. The SKILL.md defines the workflows (generate / update / validate / visualize) and universal rules; this file defines exactly what each document must contain and how it maps onto OKF. Follow it precisely.

This spec distinguishes:
- **OKF-mandated** — required by OKF v0.1 itself (SPEC.md at github.com/GoogleCloudPlatform/knowledge-catalog). A bundle missing these is non-conformant.
- **OKF-recommended** — recommended by OKF v0.1 but not required. Always filled in here.
- **Skill extension** — custom fields/conventions this skill adds on top of OKF. OKF requires consumers to tolerate and preserve unknown frontmatter keys and body sections, so these are safe, but a strict OKF consumer will ignore them.

## Table of contents

- Folder structure
- YAML frontmatter schema
- `index.md` format (reserved)
- `log.md` format (reserved)
- Confidence scale (skill extension)
- Citations format
- File-by-file content requirements
- Business rule format
- ADR format
- Mermaid diagram rules
- Cross-linking
- Index completeness checklist

---

## Folder structure

Generate this tree. Create additional subdirectories only when the codebase clearly warrants them. Every subdirectory gets its own `index.md`. `index.md` and `log.md` are OKF-reserved filenames — never use them for concept documents.

```
knowledge/
  index.md                    (reserved — bundle root index)
  log.md                      (reserved — change history)
  project_inventory.md
  ai_context.md
  onboarding.md
  dependency_graph.md
  todos.md
  code_health.md
  technical_debt.md

  adr/
    index.md
    ADR-001-<topic>.md
    ADR-002-<topic>.md

  architecture/
    index.md
    overview.md
    frontend.md
    backend.md
    infrastructure.md
    deployment.md

  modules/
    index.md
    <one file per module>.md

  database/
    index.md
    <one file per table or entity>.md

  api/
    index.md
    <one file per controller or route group>.md

  business/
    index.md
    rules.md

  authentication/
    index.md
    overview.md

  authorization/
    index.md
    overview.md

  integrations/
    index.md
    <one file per external service>.md

  events/
    index.md
    overview.md

  automation/
    index.md
    overview.md

  testing/
    index.md
    overview.md

  deployment/
    index.md
    overview.md

  troubleshooting/
    index.md
    overview.md

  glossary/
    index.md
    terms.md
```

---

## YAML frontmatter schema

Every concept document (every `.md` except `index.md` and `log.md`) must begin with this block:

```yaml
---
type: <see per-directory type values below>          # OKF-mandated. Never empty.
title: <Human-readable title>                          # OKF-recommended
description: <one-sentence summary, for index entries> # OKF-recommended
resource: <repo-relative path to the primary source>   # OKF-recommended — this skill's convention: a repo-relative
                                                          # path (there is no cloud console URL for local code)
tags:                                                   # OKF-recommended
  - <relevant tag>
timestamp: <ISO 8601 datetime, e.g. 2026-07-01T00:00:00Z>  # OKF-recommended — last meaningful change to this doc
confidence: <High | Medium | Low>                       # Skill extension
generated_from:                                         # Skill extension
  - <source file or folder path, one per line>
version: <integer, incremented each regeneration>        # Skill extension
---
```

`type` values used by this skill (producers may choose descriptive strings freely per OKF — these are this skill's conventions, not an OKF-registered list): `Project Inventory`, `AI Context`, `Onboarding Guide`, `Dependency Graph`, `TODO Ledger`, `Code Health Report`, `Technical Debt Report`, `ADR`, `Architecture Overview`, `Module`, `Database Table`, `API Endpoint Group`, `Business Rules`, `Authentication Overview`, `Authorization Overview`, `Integration`, `Event System Overview`, `Automation Overview`, `Testing Overview`, `Deployment Overview`, `Troubleshooting Overview`, `Glossary`.

Files that are safe to hand-edit and should be regenerated only on demand may include `<!-- AUTO-GENERATED -->` as the first body line (after frontmatter) to opt into automatic overwrite during updates. Files without that marker are treated as human-protected.

---

## `index.md` format (reserved)

Per OKF, `index.md` files carry **no frontmatter**. Every directory (including the bundle root) gets one. Use OKF's section + bullet-list form for navigation, and it is fine to add extra body content below (diagrams, checklists) since OKF permits arbitrary body content in non-frontmatter files:

```markdown
# Modules

* [Billing](billing.md) - Subscription and invoice lifecycle.
* [Auth](auth.md) - Login, session, and token issuance.
```

The bundle-root `knowledge/index.md` additionally includes: project name + one-sentence summary + tech stack at a glance; a top-level architecture diagram (Mermaid); known limitations/gaps; and the completeness checklist (see below), below the standard section/bullet-list navigation.

---

## `log.md` format (reserved)

Per OKF, newest entries first, ISO 8601 date headings, prose bullets:

```markdown
## 2026-07-01
* **Generate**: Full bundle generated from source. 42 modules, 18 database tables, 30 API endpoints, 6 integrations documented. Confidence: 61 High / 22 Medium / 7 Low.
* **Assumptions**: Treated `packages/shared` as a module boundary though it has no route/controller of its own.
* **Skipped**: `legacy/` excluded — appears unused, not imported anywhere detected, left undocumented rather than guessed at.
* **Known gaps**: No test coverage data available (no coverage config found).

## 2026-06-14
* **Update**: Regenerated `modules/billing.md` and `api/billing.md` after `src/billing/*.ts` changed. Preserved 11 human-edited files (no `<!-- AUTO-GENERATED -->` marker).
```

One entry per generate/update run. Fold assumptions, skipped files, preserved files, and known gaps into bullets within that run's entry rather than a separate document.

---

## Confidence scale (skill extension)

- `High` — directly readable from source code with no inference
- `Medium` — inferred from patterns, naming conventions, or partial evidence
- `Low` — assumed from context; treat with caution

---

## Citations format

OKF's body convention for external sources is a `# Citations` heading with a numbered list. This skill reuses it for internal source-file evidence — reference inline by number, and never fabricate line numbers:

```markdown
Authentication uses JWT [1][2].

# Citations

[1] [src/auth/auth.service.ts](../../../src/auth/auth.service.ts) — `login()`, lines 42–88
[2] [src/auth/jwt.strategy.ts](../../../src/auth/jwt.strategy.ts)
```

If a claim cannot be backed by a citation, mark it `confidence: Low` or write `> Unknown from source code.` in place of the claim.

---

## File-by-file content requirements

### project_inventory.md
`type: Project Inventory`. The authoritative checklist for everything that must be documented. List every detected: language, framework, dependency (with version), module, database table/entity, API/route group, background job, cron job, event system, environment variable, integration, Docker service, CI/CD workflow.

### ai_context.md (read-first file for coding agents)
`type: AI Context`. Single dense, actionable file an agent reads before editing code. Include verbatim near the top:

```
Before modifying code:
1. Read ai_context.md.
2. Read the affected module documentation in modules/.
3. Read related API documentation in api/.
4. Read related database documentation in database/.
5. Follow existing architectural patterns.
6. Update the relevant knowledge documentation if behavior changes.
```

Then cover: project summary; coding standards (from lint/format config); naming conventions; folder conventions; preferred patterns; common utilities and where to find them; how to add a new feature (based on existing patterns); how APIs are organized; testing expectations; deployment expectations. Back conventions with citations; mark inferred ones `confidence: Medium`.

### onboarding.md
`type: Onboarding Guide`. Answer "I cloned the repo. Now what?" using exact commands from package.json/README/Dockerfiles/scripts: prerequisites, install, env setup, running locally, DB setup + migrations + seeds, first login/user, running tests, debugging tips, deploy procedure.

### dependency_graph.md
`type: Dependency Graph`. Module-to-module and module-to-infrastructure dependencies, as both arrow-text and a Mermaid graph. Flag circular dependencies explicitly.

### todos.md
`type: TODO Ledger`. Scan for `TODO`, `FIXME`, `XXX`, `HACK`. Table: File:Line | Marker | Priority | Comment. Write `> None found.` if empty.

### code_health.md
`type: Code Health Report`. **Potentially unused code.** Identify candidates from static evidence only. Static analysis cannot prove code is unused (entrypoints, reflection, dynamic imports, runtime wiring hide usage) — frame everything as a candidate, not a fact. Look for: modules with no detectable importers, routes with no detectable references, DTOs/types with no detectable usage, apparent duplicate logic, orphaned files. Rules: do not state code is unused unless proven; prefer "no references found via static analysis"; cite the specific evidence; mark `confidence: Low` unless directly verified. Explicit duplication may use higher confidence.

### technical_debt.md
`type: Technical Debt Report`. Identify with evidence: oversized controllers/services, circular dependencies, duplicated validation, repeated raw SQL, magic numbers/hardcoded values, deep nesting. Table: Issue | Location | Severity | Why it matters.

### adr/ADR-NNN-<topic>.md
`type: ADR`. One reverse-engineered Architecture Decision Record per significant choice (framework, database, cache, queue, ORM, auth strategy). See ADR format below.

### architecture/overview.md
`type: Architecture Overview`. Architecture style (with citations); tech stack table (Layer → Technology → Version); top-level folder structure with purpose; request lifecycle (Mermaid sequence); data flow diagram (Mermaid); key design patterns (with citations); link to `../dependency_graph.md`.

### architecture/frontend.md, backend.md, infrastructure.md, deployment.md
`type: Architecture Overview`. Frontend: framework + version, routing, state management, component structure, API layer, build tooling. Backend: framework + version, middleware chain, layer structure, ORM, background jobs, error handling. Infrastructure: hosting, containerization, reverse proxy/load balancer, env var management, secrets strategy. Deployment: CI/CD pipeline (steps, triggers, tools), deployment targets, environment promotion flow, rollback strategy.

### modules/<module-name>.md (one per module)
`type: Module`. Purpose, responsibilities, controllers, services, repositories, DTOs/schemas; entities (link to `../database/`), events (link to `../events/index.md`), permissions (link to `../authorization/overview.md`), business rules (link to `../business/rules.md`), external dependencies, related docs.

### database/<table-name>.md (one per table/entity)
`type: Database Table`. Purpose; columns table (Column | Type | Nullable | Default | Description); indexes; constraints; relations; ORM model; migration history. ER diagram (Mermaid) required for any table with 3+ relations.

### api/<controller-name>.md (one per controller/route group)
`type: API Endpoint Group`. Per endpoint: method + path; auth required (guard/role); request body (fields, types, required/optional, validation); response body + status codes; error responses (code + condition); rate limiting; a concrete curl example.

### business/rules.md
`type: Business Rules`. Extract rules from conditional logic; state in plain English, never quote code. Format below.

### authentication/overview.md
`type: Authentication Overview`. Strategy, login flow (Mermaid sequence), token structure (claims, expiry, signing algo), refresh strategy, guards/middleware (names + paths), session storage, OAuth providers — all with citations.

### authorization/overview.md
`type: Authorization Overview`. Model (RBAC/ABAC/policy), roles + capabilities, permissions assignment/checking, guard/decorator usage, resource-level access control.

### integrations/<service-name>.md (one per external service)
`type: Integration`. Purpose, SDK/client + version, required env vars (names only, never values), credentials expected, usage (which modules call it), retry/error strategy, webhook handling.

### events/overview.md
`type: Event System Overview`. Event system in use; catalog table (Event | Emitter | Consumers | Payload | Purpose); sequence diagrams for critical flows.

### automation/overview.md
`type: Automation Overview`. Cron jobs (name, schedule, action, owner), background queues (name, processor, retry config), scheduled scripts.

### testing/overview.md
`type: Testing Overview`. Frameworks + versions, test types, exact run commands, coverage tooling + threshold, mocking strategy, fixtures, coverage gaps.

### deployment/overview.md
`type: Deployment Overview`. Required env vars table (Variable | Purpose | Required | Example non-secret value), infrastructure diagram, deployment steps, health checks, migration procedure.

### troubleshooting/overview.md
`type: Troubleshooting Overview`. Per failure mode: symptom, likely cause, resolution, related files. Cover at minimum: DB connection failures, missing env vars, migration failures, auth failures, Docker startup failures.

### glossary/terms.md
`type: Glossary`. Define every domain term (entities, status enums, event names, roles, config keys). Format:

```
**<Term>**
Definition: <plain English>
Used in: <module or file references>
```

---

## Business rule format

```
RULE-001: Billing — Invoices can only be refunded after their status is "paid".

# Citations
[1] [billing.service.ts](../../src/billing/billing.service.ts) — `refundInvoice()`

Confidence: High
```

---

## ADR format

```
# ADR-001: Use of NestJS

Status: Inferred (reverse-engineered from code, not an original decision record)
Context: <problem this choice addresses>
Decision: <what was chosen>

# Citations
[1] [package.json](../../package.json)

Consequences: <observable trade-offs in the codebase>
```

Mark `confidence: Medium` unless intent is explicitly documented somewhere in the repo.

---

## Mermaid diagram rules

Generate a diagram when:
- Documenting request lifecycle (sequence)
- Any table with 3+ relations (ER)
- Event flows with 2+ consumers (sequence)
- Deployment topology (graph)
- Auth login flow (sequence)
- Module dependency graph with 4+ modules (graph)

Do not generate one when a single sentence would do.

---

## Cross-linking

Use OKF's recommended absolute (bundle-relative) link form for stability, e.g. `/modules/billing.md` when the bundle root is `knowledge/`, or the equivalent relative path from the current file. Every concept document ends with a `## Related` section:

```markdown
## Related

- [`../database/users.md`](../database/users.md) — Users entity
- [`../api/auth.md`](../api/auth.md) — Auth endpoints
- [`../ai_context.md`](../ai_context.md) — Coding agent context
```

Every new document must also be linked from its directory's `index.md`. Per OKF, consumers must tolerate broken links (they represent not-yet-written knowledge) — but this skill still treats a broken link as a Validate-time finding to flag to the user.

---

## Index completeness checklist

Fill this in inside the root `index.md`, cross-checked against `project_inventory.md`, below the standard navigation section:

```markdown
## Documentation Completeness

| Category | Status | Notes |
|----------|--------|-------|
| All inventory items documented | ✓ / ✗ | |
| All modules documented | ✓ / ✗ | |
| All database entities documented | ✓ / ✗ | |
| All API controllers documented | ✓ / ✗ | |
| All integrations documented | ✓ / ✗ | |
| All environment variables listed | ✓ / ✗ | |
| All directories have an index.md | ✓ / ✗ | |
| All concept documents have OKF frontmatter with a non-empty `type` | ✓ / ✗ | |
| Business rules extracted | ✓ / ✗ | |
| Mermaid diagrams generated | ✓ / ✗ | |
| ai_context.md complete | ✓ / ✗ | |
| ADRs generated | ✓ / ✗ | |
| TODOs scanned | ✓ / ✗ | |
| No hallucinated information | ✓ / ✗ | |
```

If any row is ✗, add a note explaining what is missing and why.
