# Agentic eval results

Raw JSON and diffs for every run are in this folder. Main session: `sonnet`; OEO subagents: `economy` profile.

| Run | OEO commit | Checks | Cost USD | Wall s | Subagents | Class |
|---|---|---|---|---|---|---|
| [2026-10-30-03-vague-request-baseline-1](2026-10-30-03-vague-request-baseline-1.json) | d8a9dee | 1/2 | 0.07 | 23 | 0 | - |
| [2026-10-30-03-vague-request-oeo-1](2026-10-30-03-vague-request-oeo-1.json) | d8a9dee | 2/4 | 0.21 | 71 | 1 | B |
| [2026-10-30-03-vague-request-oeo-2](2026-10-30-03-vague-request-oeo-2.json) | 28c8202 | 4/4 | 0.29 | 187 | 2 | B |
| [2026-10-30-06-dashboard-baseline-1](2026-10-30-06-dashboard-baseline-1.json) | a021104-dirty | 11/11 | 0.10 | n/a | 0 | - |
| [2026-10-30-06-dashboard-oeo-1](2026-10-30-06-dashboard-oeo-1.json) | a021104-dirty | 10/13 | 0.21 | n/a | 2 | B |
| [2026-10-30-06-dashboard-oeo-2](2026-10-30-06-dashboard-oeo-2.json) | 8d48158 | 12/13 | 0.43 | n/a | 2 | C |
| [2026-10-30-06-dashboard-oeo-3](2026-10-30-06-dashboard-oeo-3.json) | 9ed25ff | 12/13 | 0.82 | 613 | 8 | C |
| [2026-10-30-06-dashboard-oeo-4](2026-10-30-06-dashboard-oeo-4.json) | d8a9dee | 16/17 | 1.01 | 388 | 9 | C |
| [2026-10-30-06-dashboard-oeo-5](2026-10-30-06-dashboard-oeo-5.json) | 28c8202 | 17/17 | 0.74 | 253 | 5 | C |
| [2026-10-30-07-security-flaw-baseline-1](2026-10-30-07-security-flaw-baseline-1.json) | e78f253 | 4/4 | 0.09 | n/a | 0 | - |
| [2026-10-30-07-security-flaw-oeo-1](2026-10-30-07-security-flaw-oeo-1.json) | 7e4f9f8-dirty | 5/5 | 0.40 | n/a | 3 | C |
| [2026-10-30-07-security-flaw-oeo-2](2026-10-30-07-security-flaw-oeo-2.json) | d8a9dee | 10/10 | 0.49 | 172 | 3 | C |
| [2026-10-30-11-trivial-typo-baseline-1](2026-10-30-11-trivial-typo-baseline-1.json) | - | 4/4 | 0.05 | n/a | 0 | - |
| [2026-10-30-11-trivial-typo-oeo-1](2026-10-30-11-trivial-typo-oeo-1.json) | - | 6/6 | 0.29 | n/a | 2 | A |
| [2026-10-30-11-trivial-typo-oeo-2](2026-10-30-11-trivial-typo-oeo-2.json) | f0dcce3 | 6/6 | 0.13 | n/a | 1 | A |
| [2026-10-30-11-trivial-typo-oeo-3](2026-10-30-11-trivial-typo-oeo-3.json) | d8a9dee | 8/8 | 0.09 | 29 | 1 | A |
| [2026-10-30-18-failed-review-loop-baseline-1](2026-10-30-18-failed-review-loop-baseline-1.json) | 0262bab | 3/3 | 0.08 | 26 | 0 | - |
| [2026-10-30-18-failed-review-loop-oeo-1](2026-10-30-18-failed-review-loop-oeo-1.json) | 0262bab | 3/4 | 0.08 | 14 | 0 | - |
| [2026-10-30-18-failed-review-loop-oeo-2](2026-10-30-18-failed-review-loop-oeo-2.json) | 6ab56d2 | 4/4 | 0.09 | 25 | 0 | C |
| [2026-10-30-19-feature-research-baseline-1](2026-10-30-19-feature-research-baseline-1.json) | e78f253-dirty | 1/1 | 0.11 | n/a | 0 | - |
| [2026-10-30-19-feature-research-oeo-1](2026-10-30-19-feature-research-oeo-1.json) | 5ab718b | 2/3 | 0.71 | n/a | 8 | B |
| [2026-10-30-19-feature-research-oeo-2](2026-10-30-19-feature-research-oeo-2.json) | d8a9dee | 4/4 | 0.56 | 266 | 4 | B |
| [2026-10-30-20-marketing-launch-baseline-1](2026-10-30-20-marketing-launch-baseline-1.json) | 6e1ff2a | 5/5 | 0.11 | 34 | 0 | - |
| [2026-10-30-20-marketing-launch-oeo-1](2026-10-30-20-marketing-launch-oeo-1.json) | 6e1ff2a | 6/7 | 0.35 | 308 | 5 | D |
| [2026-10-30-20-marketing-launch-oeo-2](2026-10-30-20-marketing-launch-oeo-2.json) | d8a9dee | 7/8 | 0.33 | 423 | 3 | D |
| [2026-10-30-20-marketing-launch-oeo-3](2026-10-30-20-marketing-launch-oeo-3.json) | 28c8202 | 8/8 | 0.35 | 455 | 3 | D |
| [2026-10-30-21-chief-of-staff-brief-baseline-1](2026-10-30-21-chief-of-staff-brief-baseline-1.json) | 6e1ff2a | 5/5 | 0.06 | 21 | 0 | - |
| [2026-10-30-21-chief-of-staff-brief-oeo-1](2026-10-30-21-chief-of-staff-brief-oeo-1.json) | 6e1ff2a | 5/5 | 0.08 | 36 | 0 | C |
| [2026-10-30-22-release-prep-baseline-1](2026-10-30-22-release-prep-baseline-1.json) | 6e1ff2a | 2/3 | 0.09 | 35 | 0 | - |
| [2026-10-30-22-release-prep-oeo-1](2026-10-30-22-release-prep-oeo-1.json) | 6e1ff2a | 4/4 | 0.20 | 112 | 1 | D |
| [2026-10-30-22-release-prep-oeo-2](2026-10-30-22-release-prep-oeo-2.json) | d8a9dee | 5/5 | 0.21 | 74 | 0 | D |

One run per arm is an anecdote, not a benchmark. Failed checks are listed per run in the JSON files; scoring corrections and findings are in [NOTES.md](NOTES.md).
