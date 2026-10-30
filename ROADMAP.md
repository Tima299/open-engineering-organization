# Roadmap

Honest status labels: **Works** (implemented and tested), **Experimental** (implemented, little
real-world evidence), **Planned** (not built). Updated with every release.

## Status (main, after v0.2.0)
| Capability | Status | Evidence / gap |
|---|---|---|
| Role contracts, schema, decision matrix, validation in CI | Works | `oeo validate`, unit tests, CI on Linux and macOS |
| Stage 0 router: classes, activation, gates, budgets | Works | unit tests, 23 deterministic scenarios; in real runs triage matched the expected class except 06-oeo-1 (under-reported signal, fixed) |
| Model/effort routing | Works | real runs ran the routed model after one fix (11-oeo-1 planned Haiku, ran Sonnet); escalation to a stronger tier observed in eval 19 |
| Installed plugin end to end (`/oeo:deliver`) | Experimental | [real runs](evals/results/agentic/SUMMARY.md) on 7 scenarios with baseline arms, 1-3 runs per arm, `economy` profile only; latest fixes not all re-run |
| Independent verification and correction loop | Experimental | eval 19: QA rejected overclaims 3 times; eval 07: fail-before proof; gaps: orchestrator edited after QA without re-verification (06-oeo-1/2) |
| `research` ledger + `oeo ledger-check` | Experimental | eval 19: the harness path check failed; the committed ledger passes `oeo ledger-check` on re-check (29 claims) |
| `chief-of-staff` (`oeo status`), `launch` (`oeo copy-lint`), `release` | Experimental | one run per arm each (evals 20-22); `business-review` has no installed-plugin run yet |
| FinOps (`oeo cost`, subagent + main-session hooks) | Works, best effort | real runs logged subagents and main session; parses Claude Code's internal transcript format |
| Guard hook | Experimental | unit-tested patterns incl. review bypasses; defense in depth, not a sandbox |
| Second host adapter (non-Claude-Code) | Planned | contracts are host-neutral; no adapter yet |

## Next (priority order)
1. Recruit a second maintainer (bus factor is 1).
2. Repeat agentic runs (5 per arm per scenario) for medians; add runs for launch, chief-of-staff
   and a Class D release.
3. Install the DCO GitHub App; sign release tags.
4. Re-verify third-party revisions (commit SHAs) and add a scheduled registry check.
5. Measure activation discipline on real projects; prune or merge roles that never change outcomes.
