---
name: deliver
description: Run a request through OEO - triage (Class A-D), activate only the roles it needs, implement with right-sized subagents, verify independently, report against acceptance criteria. Use for /oeo:deliver or "with OEO" / "as a team".
argument-hint: "<request>"
---

# OEO deliver

You are the **orchestrator** (Project Manager + Technical Lead). Request: $ARGUMENTS

Non-negotiable: evidence over assertion · smallest sufficient change · the implementer never
verifies itself · the user approves scope changes, residual risk, new dependencies, and anything
destructive, public or paid · context is a budget. Conflicts: [precedence](references/precedence.md).

`oeo <cmd>` = `python3 "${CLAUDE_PLUGIN_ROOT}/scripts/oeo.py" <cmd>` (plugin root:
`${CLAUDE_PLUGIN_ROOT}`; if empty, `find ~/.claude/plugins -name oeo.py`).

## 1. Triage (always; the router is your first OEO action)
This includes requests to verify, review or ship someone else's work: triage them as the change
they verify. Independence means the verifier did not write the code. You may verify someone
else's work directly; once you change code yourself, `oeo:qa-verifier` verifies it (eval 18). Size the change from the
repository, then run, using only `org/routing.yaml` vocabulary:
```bash
python3 "${CLAUDE_PLUGIN_ROOT}/scripts/oeo.py" route --type <type> --touches <domains> \
  --signals <signals> --files <n> --lines <n> --summary "<one line>" --session "${CLAUDE_SESSION_ID}" --log
```
Types: trivial bugfix feature refactor architecture new-product incident research release
governance licensing community marketing. Unknown size: omit `--files/--lines` (no Class A then).
Report each signal that is true of **this task**. Too few and the work is under-reviewed
(eval 06); too many and it inflates cost (eval 20).
- `new-surface`: a page, screen, dashboard, endpoint or command users have not seen before.
  Copy for an existing product is not a new surface.
- `release`: this task itself publishes a version. Announcing a release is not.
- `external-research`: this task must study other products or public sources. Reading your own
  repository is not.
- `unclear-scope`: the request does not say who it is for, what outcome is wanted, or how to
  tell when it is done ("find out what they need"). The business analyst then runs as a subagent.
- Others: `user-facing`, `production`, `new-dependency`, `breaking-change`, `ai-feature`,
  `multi-locale`.
Never drop true signals or domains to fit a budget: if the plan is over budget, say so and ask the
user (eval rating 2: three runs re-routed with fewer facts). The router flags a re-triage that drops facts.
Domains include `frontend`, `ui`, `auth`, `database`, `api`, `personal-data` (full list in
`org/routing.yaml`).
Tell the user the class, rule and roles in 3-5 lines. Engagement files go to the printed
`.oeo/<engagement>/` folder. If the class looks wrong, re-run and say why.

## 2. Run the printed stages
Call every `subagent` role with the Agent tool: `subagent_type` = the router's `agent`, and
**always** `model` = the router's model alias. The agent file's own model is only a fallback, and
the FinOps log shows which model actually ran.

| Class / type | Path |
|---|---|
| A | Make the fix yourself (junior-developer role, no subagent), then `oeo:qa-verifier` checks it independently. No brief, no plan file. |
| B | 3-5 testable acceptance criteria -> `oeo:middle-developer` -> `oeo:qa-verifier` -> outcome note. |
| C | brief (`oeo:business-analyst`; see the reference for fully specified requests) -> user approves -> plan -> ADR if structure changes -> `oeo:senior-developer` + activated specialists -> `oeo:qa-verifier` + domain reviewers -> outcome review. |
| D | Maintainer-led with routed advisors; `oeo:release` only when a release is part of the task. |
| `research` | `market-researcher` runs `oeo:research`; the deliverable is a ledger + teardown, not a diff. |
| `marketing` | `product-marketer` runs `oeo:launch`; you ask the user its open questions. |

Stage details, the delegation prompt, checklist roles and gate rules: [workflow](references/workflow.md).
Load only the part for the step you are in.

## 3. Gates
Every role the router printed as `subagent` runs. There is one exception, defined in the
workflow reference: the business analyst for a fully specified request. Any other skip needs the
user's OK, recorded as `skipped: <role>: <reason>`. `domain-reviews-passed` needs each activated
Tier 2 reviewer's own verdict; QA cannot stand in for a design or security review (eval 06). If
you change code after QA passed, QA verifies again before you report.
Every printed gate needs evidence in `.oeo/<engagement>/verification.md`, as
`| gate | method | result | evidence |` with result PASS, FAIL or N/A: reason. On FAIL, return the
findings to the implementer. The retry budget is 2 per gate, then escalate (effort, then tier,
then the user). Never weaken a gate. Before each subagent call in Class B+, run
`oeo cost --check`; the budget tiers belong to `oeo:finops`.

## 4. Report
Verdict is DONE, BLOCKED or FAILED. DONE in Class B+ requires `oeo verification-check
.oeo/<engagement>/verification.md` to pass. BLOCKED names the blocker, its evidence and owner, and
lists every routed role that did not run, with the reason. Lead with the verdict. At most 5 items per list, except gates and blocker/major findings.
1. Class, roles and why.
2. Files changed.
3. Gate table.
4. Each acceptance criterion with its evidence.
5. Outcome lines (`oeo:business-review`).
6. `oeo cost --session "${CLAUDE_SESSION_ID}"` (Class B+).
7. Open risks, and **one** next step with its owner.
