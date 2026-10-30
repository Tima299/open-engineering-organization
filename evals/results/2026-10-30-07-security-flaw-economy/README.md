# Agentic run: 07-security-flaw (OEO arm, economy profile)

```
scenario: 07-security-flaw   date: 2026-10-30   profile: economy   oeo version: 0.1.0 (pre-release)
arm: oeo (no baseline run yet)   fixture: examples/taskboard at the commit that added it
```

**This is one run: an anecdote, not a benchmark.** Raw artifacts are in this folder:
[`change.patch`](change.patch) is the final diff, and [`oeo/`](oeo/) holds the brief, plan,
decisions, risks and activation log.

## How it was run (deviations from a real install)
- The plugin was **not installed** in the recording environment, so the orchestrator (the main
  session) ran each role as a general-purpose subagent. Each subagent was told to read its
  generated file in `agents/` as its role definition. The models followed the router's `economy`
  plan: business-analyst=haiku, senior-developer=sonnet, security-engineer=sonnet, qa-verifier=haiku.
- Because the agents were general-purpose, **the tool restrictions in agent frontmatter were not
  enforced**. Read-only roles were told to stay read-only, and they complied: no file in the
  target repo changed apart from the developer's two files.
- **Business Owner approval was given by the orchestrator as a proxy**, recorded in
  `oeo/decisions.md`. A real run asks the user.
- The SubagentStop FinOps hook did not run. Token numbers below come from the host's
  per-subagent task notifications.

## Flow observed
Stage 0 `oeo route` gave Class C (rule `risky-domain`), 10 roles activated, 25 not activated
(`oeo/activation-log.jsonl`). Stage 1: the BA brief found the flaw by reproduction (ben deleted
ana's task and got `True`) plus 7 more findings. Its contract mismatch ("eight sections") was later
fixed upstream. The orchestrator narrowed scope to delete() authorization and deferred 5 findings
to `oeo/risks.md`. Stage 5: the senior developer worked test-first (2 new tests FAILED, then fix,
then 12 OK). Stage 6: security review and QA ran in parallel, read-only, and both returned PASS
with independent fail-before/pass-after evidence. No gate failed, so the correction loop was
**not exercised** in this run (scenario 18 covers it; not yet run).

## Scored success criteria
| # | Criterion (abridged from the scenario) | Result | Evidence |
|---|---|---|---|
| 1 | Flaw identified with reproduction and output | PASS | BA probe F1; security probes |
| 2 | Regression test fails before and passes after, shown by the verifier | PASS | QA base worktree: `FAILED (failures=2)`; fixed tree: `Ran 12 tests ... OK` |
| 3 | Explicit, documented denial that does not leak; owner can still delete | PASS | returns False (docstring + decisions.md); equality test with unknown id; existing owner test passes |
| 4 | Security engineer gives a verdict with evidence and is not the implementer | PASS | separate agent, PASS, injection and case-variant probes |
| 5 | complete() reviewed; its crash reported as out of scope, not silently fixed | PASS | BA F5, security observation, QA finding 4; diff does not touch complete() |
| 6 | Diff limited to 2 files, no dependency; report lists what is unverified | PASS | `change.patch` (2 files, +16/-2); HTTP identity listed as a blocker before exposure |

## Measures
| Agent (model) | Tokens (host-reported) | Router estimate | Tool calls | Wall time |
|---|---|---|---|---|
| business-analyst (haiku) | 100,018 | 60,000 | 11 | 160 s |
| senior-developer (sonnet) | 62,347 | 60,000 | 9 | 34 s |
| security-engineer (sonnet) | 64,116 | 60,000 | 10 | 66 s |
| qa-verifier (haiku) | 93,368 | 60,000 | 13 | 124 s |
| **Subagents total** | **319,849** | **240,000** | 43 | ~6.4 min (QA and security ran in parallel) |

- Class C budget is 900,000, so the run was within budget. Two agents went **over estimate**:
  the read-heavy Haiku roles (BA and QA). Per-invocation estimates need recalibrating, and
  reviewer roles likely need a higher estimate than implementers.
- Orchestrator (main-session) tokens were not measured.
- Agents invoked: 4. Agents whose output changed the outcome: 4. The BA set the scope and
  the risks, the developer made the fix, and security and QA supplied gate evidence. QA's
  "stage only two files" finding was applied.
- Files changed: 2. Gate failures: 0. Retries: 0.

## Not verified by this run
Baseline (single agent without OEO) comparison; repeat runs; the installed-plugin path (hooks,
frontmatter tool limits, `oeo:` agent names); the correction loop; Class A/B/D agentic runs.
