# 0009. Engagement folders and deterministic checks behind skills

- Status: Accepted
- Date: 2026-10-30
- Deciders: maintainer (@Tima299)

## Context
A self-review of v0.2 rated the skills 72/100. The weakest scores came from skills whose
quality rested only on model judgement over thin data:
- `chief-of-staff` (62) had one brief and one plan file for all work, so it could not see
  across engagements.
- `finops` (58) did not count the orchestrator's own tokens.
- `launch` (66) and `research` (70) had rules but no mechanical check of them.

## Options
1. Longer skill instructions: more context cost, still unverifiable.
2. **Small stdlib checks that the skills call, plus a per-engagement memory layout they can read.**
3. A database or service: heavy, against the zero-runtime-dependency rule.

## Decision
Option 2:
- `.oeo/<engagement>/` holds the brief, plan, risks, verification, screen spec and evidence;
  the decisions log, activation log, token logs and research stay global.
- `oeo status` turns those files into the brief data.
- `oeo copy-lint` and `oeo ledger-check` encode the copy gate and the research-ledger rules.
- A Stop hook snapshots main-session tokens.
- The checks live in `scripts/checks.py` and are unit-tested.

## Consequences
- Skills cite a command instead of restating rules; judgement is added on top of facts.
- Status parsing depends on the plan's `status` column and the verification `gate | ... | result`
  table; the `deliver` reference defines both.
- Regex copy rules give false positives and negatives. They flag; the human or reviewer decides
  on should-fix items.

## Revisit when
Agentic eval runs show the checks being skipped or misleading, or projects need a different
memory layout.
