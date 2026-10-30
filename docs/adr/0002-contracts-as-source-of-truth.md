# 0002. Role contracts are the source of truth; few generated agents

- Status: Accepted
- Date: 2026-10-30

## Context
The spec defines 35 roles. Every installed subagent adds its description to every session's
context, and most roles are perspectives, not separate workers. Anti-bloat rule: roles are
capabilities, not headcount.

## Options
1. One subagent file per role (35 agents): simple mapping, permanent context cost, persona bloat.
2. **Contracts in `org/roles/*.yaml`; materialize only roles that need isolation or a different
   model; generic `specialist`/`advisor` agents run any Tier 2/3 contract on demand.**
3. No agents, everything in the main session: cheapest, but no independent verification.

## Decision
Option 2. Each contract declares `execution`: `human`, `orchestrator`, `checklist` or
`subagent`. `scripts/oeo.py build` generates 9 dedicated + 2 generic agents from contracts and
`config/models.yaml`; CI fails if generated files drift.

## Consequences
Independence where it matters (business analyst, verifier, security, architect) at ~11 agent
descriptions of context. Generic agents share one tool set (documented residual risk T5).
Editing an agent means editing its contract and rebuilding.

## Revisit when
Activation logs show a generic-agent contract invoked often enough to deserve its own agent,
or a dedicated agent that is rarely invoked.
