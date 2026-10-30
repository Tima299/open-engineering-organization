# Agentic eval results (raw data in this folder)

| Scenario | Arm | Model / profile | Checks | Cost USD | Time s | Turns | Subagents | Class |
|---|---|---|---|---|---|---|---|---|
| 06-dashboard | baseline | sonnet | 10/11 | 0.09661549999999999 | 25.3 | 4 | 0 |  |
| 06-dashboard | oeo | sonnet / economy | 9/13 | 0.21465697499999997 | 21.9 | 3 | 2 | B |
| 07-security-flaw | baseline | sonnet | 4/4 | 0.0886264 | 23.9 | 5 | 0 |  |
| 07-security-flaw | oeo | sonnet / economy | 5/5 | 0.40410193499999997 | 19.6 | 2 | 3 | C |
| 11-trivial-typo | baseline | sonnet | 4/4 | 0.052071299999999994 | 12.0 | 3 | 0 |  |
| 11-trivial-typo | oeo | sonnet / economy | 6/6 | 0.2864516 | 56.0 | 6 | 2 | A |
| 11-trivial-typo | oeo | sonnet / economy | 6/6 | 0.13018938 | 13.2 | 2 | 1 | A |
| 19-feature-research | baseline | sonnet | 1/1 | 0.10828379999999999 | 28.9 | 6 | 0 |  |
| 19-feature-research | oeo | sonnet / economy | 2/3 | 0.7094863199999998 | 19.7 | 3 | 8 | B |

One run per arm is an anecdote, not a benchmark. Failed checks are listed per run in the JSON files.
