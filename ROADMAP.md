# Roadmap

Honest status labels: **Works** (implemented and tested), **Experimental** (implemented, little
real-world evidence), **Planned** (not built). Updated with every release.

## Status (main, after v0.2.0)
| Capability | Status | Evidence / gap |
|---|---|---|
| Role contracts, schema, decision matrix, validation in CI | Works | `oeo validate`, unit tests, CI on Linux and macOS |
| Stage 0 router: classes, activation, gates, budgets | Works | unit tests, 21 deterministic scenarios, 7 real runs triaged as planned |
| Model/effort routing | Works | real runs: the routed model ran (Haiku/Sonnet, as planned); escalation to a stronger tier observed in eval 19 |
| Installed plugin end to end (`/oeo:deliver`) | Works, early | [real runs](evals/results/agentic/SUMMARY.md) on scenarios 06, 07, 11, 19 with baseline arms; one run per arm |
| Independent verification and correction loop | Works, early | eval 19: QA rejected overclaims 3 times, passed after escalation; eval 07: fail-before regression proof |
| `research` ledger + `oeo ledger-check` | Works, early | eval 19: 29-claim ledger passes the checker |
| `chief-of-staff` via `oeo status`, `launch` via `oeo copy-lint` | Experimental | deterministic commands unit-tested; no agentic run of these skills yet |
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
