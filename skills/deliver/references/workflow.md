# OEO workflow reference

Load only the section for the stage you are in. Stage definitions, gates and memory
ownership are data in `org/workflow.yaml`; this file says how to execute them.

## 1 Business Discovery (B: lite, C: full)
Class B: write acceptance criteria directly (Given/When/Then or checklist), plus one line of
desired outcome. Class C: delegate to `oeo:business-analyst` with the request and any evidence
the user gave; it returns the brief (template and PRD depth: `oeo:business-review`) and you save
it as `.oeo/<engagement>/brief.md`. The user (Business Owner) approves or changes it.

## 2 Independent Business Review (C)
A **fresh** `oeo:business-analyst` invocation, given only the brief and the plan (not the
discovery conversation), returns PASS or a critique:
`| # | finding | evidence | impact | severity | corrective action |`. Loop until PASS or the
user accepts a named residual risk (append to `.oeo/decisions.md`).

## 3 Planning (B: inline, C: `.oeo/<engagement>/plan.md`)
```
# Plan: <title>   class: <X>   owner: project-manager
Deliverables -> acceptance criteria:
Tasks: | id | goal (AC #) | owner role | files in scope | depends on | status |
File-ownership partition (parallel work only):
Test strategy (what fails before the change):
Risks: | risk | likelihood | impact | mitigation | owner |
Definition of Done: router gates + acceptance criteria mapped to evidence
```

## 4 Architecture review (C, when structure/contracts change)
Delegate to `oeo:technical-architect`. Apply the CTO checklist yourself (contract `cto`):
no new service/queue/cache/dependency without demonstrated need; existing API contracts,
auth, tenant isolation, data integrity and backward compatibility preserved unless the
approved brief says otherwise. ADR goes to `docs/adr/NNNN-title.md`:
`Status / Context / Options (>=2, with trade-offs) / Decision / Consequences / Revisit when`.

## 5 Implementation
- Delegate per task with: objective, acceptance criteria, files in scope, test command,
  constraints, HANDOFF format. Test-first for business logic, bug fixes, authz, data handling.
- UI work: `oeo:design-direction` first (design acceptance criteria), then implementation.
- Two agents never edit the same file concurrently. Sequential handoffs are the default.

## 6 Independent verification
Delegate to `oeo:qa-verifier` with: the diff (or changed files), acceptance criteria, gate list,
and repository check commands. Activated domain reviewers (security, database, a11y, ...) run in
parallel only if they read and do not write. Record in `.oeo/<engagement>/verification.md`:
`| gate | command / method | result | evidence |`. Findings go back to the implementer.

## 7 Release & outcome
Release: `oeo:release` skill (SemVer, CHANGELOG, notes, tag, rollback plan; human authorizes).
Outcome review: as defined in `oeo:business-review` (Outcome review section).

## 8 Community loop (D)
Triage inbound feedback with the `oeo:chief-of-staff` rubric. Defects re-enter Stage 0,
product gaps Stage 1.

## Checklist roles (applied by the orchestrator; record PASS / FAIL / N/A: reason)
| Role | Class B | Class C |
|---|---|---|
| cto | no new dependency, service or abstraction without need; API, auth and data compatibility unchanged | same + ADR exists for structural change; veto grounds written if used |
| business-analyst | 3-5 testable criteria + one outcome line exist before coding | (runs as a subagent in C) |
| oss-maintainer | CHANGELOG updated if the repo keeps one; license gate if a dependency was added; else N/A | same + public docs updated for user-visible change |
| Tier 3 checklist advisors | their contract's `acceptance_criteria`, only for the trigger that activated them | same |

## Memory hygiene
`.oeo/` holds one current brief, plan, risk list and verification file per engagement; replace
stale content instead of appending contradictions. Decisions log is append-only. Owners and
paths: `org/workflow.yaml` `memory`. Suggested `.gitignore` (same list as the README):
`.oeo/*.jsonl`, `.oeo/<engagement>/evidence/`, `.oeo/research/*/raw/`. Commit briefs, plans and ADRs if the
team wants them public.

## Delegation
- Delegate only across a real boundary: a different role, an independent review, truly parallel
  output, or context isolation (research). Otherwise do it yourself, in the same pass; do not stop
  at a plan unless a plan was asked for.
- Each task carries its goal chain (`brief outcome -> acceptance criterion -> task`) and has one
  owner; nobody picks up a task someone else holds. Parallel agents need a written file partition.
- Agent call: the router's `agent`, with its `model` alias as the Agent tool `model` parameter.
  The prompt starts with `OEO plugin root: <path>`. Then give: the role id and contract path
  (generic agents); objective; acceptance criteria; files in scope; constraints; and the HANDOFF
  return format. Pass paths and facts, not your context.
- Read-only roles (business analyst, reviewers) return file content in their HANDOFF; you save it
  to the `.oeo/<engagement>/` path named in `org/workflow.yaml`.
- Status words (the only set; `oeo:chief-of-staff` and `oeo status` read them from the plan's
  `status` column): backlog, todo, in_progress, in_review (waiting on a human), blocked (name the
  blocker and its owner), done, cancelled.

## Gate rules
- N/A is allowed only for a gate that cannot apply: `adr-recorded` without a structural change,
  `regression-test` without a code change. Write `N/A: <reason>` and pass it to the verifier.
  `domain-reviews-passed`, `license-gate` and `rollback-plan` are never N/A without the user's
  written OK.
- Business Analyst critiques (Class C) loop until resolved, or until the user accepts the residual
  risk in `.oeo/decisions.md`.
- Hard calls that span roles: score them with `oeo:chief-of-staff`; a score of 4+ gets a decision
  meeting.
