# Roadmap

Honest status labels: **Works** (implemented and tested), **Experimental** (implemented, little
real-world evidence), **Planned** (not built). Updated with every release.

## Status of v0.1.0
| Capability | Status | Evidence / gap |
|---|---|---|
| Role contracts, schema, decision matrix, validation in CI | Works | `oeo validate`, unit tests |
| Stage 0 router: classes, activation, gates, budgets | Works | unit tests + deterministic eval scenarios |
| Generated agents and model/effort routing policy | Works (policy) | build check in CI; actual model per run only visible via FinOps log |
| Guard hook (ask before destructive/publishing actions, secrets) | Experimental | unit-tested patterns; bypassable by design (defense in depth) |
| FinOps token logging and `oeo cost` | Experimental | depends on Claude Code's internal transcript format |
| Skills (`deliver`, `verify`, ...) end-to-end quality | Experimental | one recorded demo run; no statistically meaningful benchmark yet |
| Agentic eval harness with baseline comparison | Planned | scenario specs exist; automated runner with model access does not |
| Second host adapter (non-Claude-Code) | Planned | contracts are host-neutral; no adapter yet |

## Next (priority order)
1. Recruit a second maintainer (bus factor is 1).
2. Agentic eval runner (`claude -p` on `examples/taskboard`) with raw results and a single-agent
   baseline; calibrate token budgets from the data.
3. Install the DCO GitHub App; sign release tags.
4. Re-verify third-party revisions (commit SHAs) and add a scheduled registry check.
5. Measure activation discipline on real projects; prune or merge roles that never change outcomes.
