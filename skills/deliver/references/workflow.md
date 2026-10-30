# OEO workflow reference

Load only the section for the stage you are in. Stage definitions, gates and memory
ownership are data in `org/workflow.yaml`; this file says how to execute them.

## 1 Business Discovery (B: lite, C: full)
Product depth (lean PRD, red-team, pre-mortem): `oeo:business-review`.
Class B: write acceptance criteria directly (Given/When/Then or checklist), plus one line of
desired outcome. Class C: delegate to `oeo:business-analyst` with the request and any evidence
the user gave. Output `.oeo/brief.md`:

```
# Brief: <title>
Users & problem:      Current workflow & limits:
Desired outcome:      Success metric + how measured:
Scope / non-goals:    Constraints & assumptions (mark ASSUMPTION):
Evidence (fact/hypothesis/unknown):    Business risks:
Acceptance criteria:  1. ... (testable)
```
The user (Business Owner) approves the brief or changes it. Never invent research or numbers.

## 2 Independent Business Review (C)
`oeo:business-analyst` reviews the brief/plan and returns PASS or a critique:
`| # | finding | evidence | impact | severity | corrective action |`. Loop until PASS or the
user accepts a named residual risk (append to `.oeo/decisions.md`).

## 3 Planning (B: inline, C: `.oeo/plan.md`)
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
parallel only if they read and do not write. Record in `.oeo/verification.md`:
`| gate | command / method | result | evidence |`. Findings go back to the implementer.

## 7 Release & outcome
Release: `oeo:release` skill (SemVer, CHANGELOG, notes, tag, rollback plan; human authorizes).
Outcome review (BA lens): requirements satisfied / tests passed / released / outcome observed /
outcome unverified, each with evidence. A shipped feature is not a business result.

## 8 Community loop (D)
Feedback -> reproducible, labeled issue. Defects re-enter Stage 0, product gaps Stage 1.

## Memory hygiene
`.oeo/` holds one current brief, plan, risk list and verification file per engagement; replace
stale content instead of appending contradictions. Decisions log is append-only. Suggested
`.gitignore`: `.oeo/*.jsonl` (logs); commit briefs/plans/ADRs if the team wants them public.
