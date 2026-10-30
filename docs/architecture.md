# Architecture

OEO is a Claude Code plugin made of **data** (contracts and policy), **generated host files**
(agents) and three **small stdlib scripts**. Decisions: [docs/adr/](adr/README.md).

```mermaid
flowchart LR
  U[User request] --> D["/oeo:deliver skill<br/>(orchestrator = PM + Tech Lead)"]
  D -->|facts: type, domains,<br/>signals, size| R["oeo.py route<br/>(pure function)"]
  L[(org/org.lock.json)] --> R
  R -->|class, roles, models,<br/>skills, gates, budget| D
  D -->|subagent roles| A["agents/*.md<br/>BA, architect, devs, QA,<br/>security, design, specialist, advisor"]
  D -->|checklist roles| C[org/roles/*.yaml]
  A -->|HANDOFF + evidence| D
  D --> G{Gates PASS?}
  G -- no, within retry budget --> A
  G -- yes --> O[Report: criteria to evidence,<br/>outcome vs unverified]
  H1[[guard.py PreToolUse]] -.asks human.-> D
  H2[[finops_hook.py SubagentStop]] -.tokens.-> F[(.oeo/finops.jsonl)]
  R -.--log.-> AL[(.oeo/activation-log.jsonl)]
```

## Components
| Path | Kind | Purpose |
|---|---|---|
| `org/roles/*.yaml` | source | 37 role contracts ([catalog](roles.md)), schema `schemas/role.schema.json` |
| `org/routing.yaml` | source | vocabulary, Stage 0 rules, class role sets, skills, generic agents, license policy |
| `org/workflow.yaml` | source | stages 0-8, gates, memory artifacts, handoff fields |
| `org/decision-rights.yaml` | source | decision matrix (decides / consulted / veto / informed / fallback) |
| `config/models.yaml` | source | tier → model profiles, overrides, budgets |
| `third_party/registry.yaml` | source | provenance registry → `THIRD_PARTY.md` |
| `org/org.lock.json`, `agents/*.md`, `docs/roles.md`, `THIRD_PARTY.md` | generated | `oeo build`; CI fails on drift |
| `skills/*/SKILL.md` | host | `deliver`, `business-review`, `research`, `design-direction`, `verify`, `release`, `launch`, `finops`, `chief-of-staff` ([ADR 0008](adr/0008-one-owner-per-capability.md)) |
| `scripts/oeo.py`, `scripts/checks.py` | tool | validate, build, route, license, cost, models; status, copy-lint, ledger-check ([ADR 0009](adr/0009-engagement-folders-and-deterministic-checks.md)) |
| `scripts/guard.py`, `scripts/finops_hook.py` | hooks | confirmation guard; token logging |
| `evals/` | tests | deterministic routing scenarios (`run.py`, CI) and real Claude Code runs vs. a baseline (`agentic.py`) |

## Runtime flow
1. **Triage**: the orchestrator inspects the repo, reports facts, runs `route`. Unknown vocabulary
   is rejected; Class A requires a size estimate.
2. **Activation**: class core roles + Tier 2 by touched facts (Class C only) + Tier 3 by explicit
   triggers. Every activation has a logged reason; everything else is listed as not activated.
3. **Execution**: `subagent` roles run as isolated agents with least-privilege tools and the
   routed model; `checklist` roles are applied by the orchestrator from the contract; `human`
   roles are questions to the user.
4. **Gates**: evidence-based; implementer never self-verifies; failures loop within the retry
   budget, then escalate (effort → tier → human).
5. **Memory**: `.oeo/` in the target project (brief, plan, decisions, risks, verification, logs),
   each with an owner and freshness rule (`org/workflow.yaml`).

## Single-agent and multi-agent operation
Class A runs two short subagents; Class B runs two to three; Class C fans out only to activated
specialists. A user may run everything in one session by treating `subagent` roles as
`checklist` roles; independence of verification is then lost, and the report must say so.

## Security
[Threat model](threat-model.md) · [verification checklist](../skills/verify/references/security.md)
· [precedence policy](../skills/deliver/references/precedence.md).
