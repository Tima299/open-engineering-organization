# Notes on the agentic runs (2026-10-30)

Each finding below changed OEO or the harness; the commit is named so it can be audited.

| Run | Finding | Change |
|---|---|---|
| 11-oeo-1 | Router planned Haiku, subagents ran Sonnet: the "pass the routed model" rule sat in a reference Class A never loads. A fix subagent cost more than the fix ($0.29 vs $0.05 baseline). | Rule back in `deliver`; Class A fixes inline, verifier stays independent (e78f253). Run 11-oeo-2: $0.13, Haiku as planned. |
| 07-oeo-1 | 5/5 checks; independent security review, fail-before regression proof, three extra findings the baseline did not report. Orchestrator skipped the BA for an already-scoped request. | Explicit, auditable rule for fully specified Class C requests (24d4316). |
| 06-oeo-1 | Triaged Class B: no `new-surface` signal reported, so no design lead, no screen spec, no design tokens. Its escaping test used a different payload than the check's literal string. | Signal checklist at triage (deliver); check now accepts any `<script>alert(` payload. Not re-scored: run 06-oeo-2 tests the fix. |
| 06-baseline-1 | Built the dashboard with design tokens, but wrote no escaping test. | Scored with the stricter literal check; it fails under the looser check too. |
| 19-oeo-1 | QA rejected overclaims three times; escalation to a stronger tier passed. Ledger saved in the engagement folder, so the old `.oeo/research/*` path check failed; re-checked by hand: `oeo ledger-check` = OK, 29 claims (7 observed, 14 inferred, 8 unknown). Cost $0.71 (8 subagents) vs $0.11 baseline. | Research files now live in `.oeo/<engagement>/` (8d48158); researcher gets its own token estimate. |
| all | `duration_s` from the CLI excludes subagent time. | Harness records `wall_s` from the next run on. |
