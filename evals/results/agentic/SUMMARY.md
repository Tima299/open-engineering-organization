# Agentic eval results

Raw JSON and diffs for every run are in this folder. Main session: `sonnet`; OEO subagents: `economy` profile.

| Run | OEO commit | Checks | Cost USD | Wall s | Subagents | Class |
|---|---|---|---|---|---|---|
| [2026-10-30-06-dashboard-baseline-1](2026-10-30-06-dashboard-baseline-1.json) | a021104-dirty | 10/11 | 0.10 | n/a | 0 | - |
| [2026-10-30-06-dashboard-oeo-1](2026-10-30-06-dashboard-oeo-1.json) | a021104-dirty | 9/13 | 0.21 | n/a | 2 | B |
| [2026-10-30-06-dashboard-oeo-2](2026-10-30-06-dashboard-oeo-2.json) | 8d48158 | 12/13 | 0.43 | n/a | 2 | C |
| [2026-10-30-06-dashboard-oeo-3](2026-10-30-06-dashboard-oeo-3.json) | 9ed25ff | 12/13 | 0.82 | 613 | 8 | C |
| [2026-10-30-07-security-flaw-baseline-1](2026-10-30-07-security-flaw-baseline-1.json) | e78f253 | 4/4 | 0.09 | n/a | 0 | - |
| [2026-10-30-07-security-flaw-oeo-1](2026-10-30-07-security-flaw-oeo-1.json) | 7e4f9f8-dirty | 5/5 | 0.40 | n/a | 3 | C |
| [2026-10-30-11-trivial-typo-baseline-1](2026-10-30-11-trivial-typo-baseline-1.json) | - | 4/4 | 0.05 | n/a | 0 | - |
| [2026-10-30-11-trivial-typo-oeo-1](2026-10-30-11-trivial-typo-oeo-1.json) | - | 6/6 | 0.29 | n/a | 2 | A |
| [2026-10-30-11-trivial-typo-oeo-2](2026-10-30-11-trivial-typo-oeo-2.json) | f0dcce3 | 6/6 | 0.13 | n/a | 1 | A |
| [2026-10-30-19-feature-research-baseline-1](2026-10-30-19-feature-research-baseline-1.json) | e78f253-dirty | 1/1 | 0.11 | n/a | 0 | - |
| [2026-10-30-19-feature-research-oeo-1](2026-10-30-19-feature-research-oeo-1.json) | 5ab718b | 2/3 | 0.71 | n/a | 8 | B |

One run per arm is an anecdote, not a benchmark. Failed checks are listed per run in the JSON files; scoring corrections and findings are in [NOTES.md](NOTES.md).
