# Roadmap

Honest status labels: **Works** (implemented and tested), **Experimental** (implemented, little
real-world evidence), **Planned** (not built). Updated with every release.

## Status (main, after v0.2.0)
| Capability | Status | Evidence / gap |
|---|---|---|
| Role contracts, schema, decision matrix, validation in CI | Works | `oeo validate`, unit tests, CI on Linux and macOS |
| Stage 0 router: classes, activation, gates, budgets | Works (router); Experimental (triage by the model) | unit tests, 23 deterministic scenarios. Real runs show triage errors: 06-oeo-1 under-reported a signal; 18-oeo-1 skipped triage; 03-oeo-2, 07-oeo-2 and 22-oeo-2 re-routed with fewer facts after a budget warning |
| Model/effort routing | Works | real runs ran the routed model after one fix (11-oeo-1 planned Haiku, ran Sonnet); escalation to a stronger tier observed in eval 19 |
| Installed plugin end to end (`/oeo:deliver`) | Experimental | [real runs](evals/results/agentic/SUMMARY.md) on 9 scenarios, 1-5 OEO runs and 1 baseline each, `economy` profile only; later `deliver` edits not all re-run; 14 of 23 scenarios never run for real |
| Independent verification and correction loop | Experimental | eval 19: QA rejected overclaims 3 times; eval 07: fail-before proof; gaps: orchestrator edited after QA without re-verification (06-oeo-1/2) |
| `research` ledger + `oeo ledger-check` | Experimental | eval 19 run 2 passes the harness ledger check; run 1's committed ledger (28 rows: 6 observed, 14 inferred, 8 unknown) passes on re-check; egress to the vendor's site was blocked |
| `chief-of-staff` (`oeo status`), `launch` (`oeo copy-lint`), `release`, `business-review` (`oeo brief-check`) | Experimental | 1-3 OEO runs each with baselines (evals 03, 20-22); latest runs pass all checks |
| FinOps (`oeo cost`, subagent + main-session hooks) | Works, best effort | real runs logged subagents and main session; parses Claude Code's internal transcript format |
| Guard hook | Experimental | unit-tested patterns incl. review bypasses; defense in depth, not a sandbox |
| Second host adapter (non-Claude-Code) | Planned | contracts are host-neutral; no adapter yet |

## Next (priority order)
1. Recruit a second maintainer (bus factor is 1).
2. Credible evaluation: held-out scenarios not used for tuning, n>=3 per arm, blinded grading by a
   separate model with a rubric, interactive runs that exercise the human-approval steps.
3. Install the DCO GitHub App; sign release tags.
4. Re-verify third-party revisions (commit SHAs) and add a scheduled registry check.
5. Measure activation discipline on real projects; prune or merge roles that never change outcomes.
