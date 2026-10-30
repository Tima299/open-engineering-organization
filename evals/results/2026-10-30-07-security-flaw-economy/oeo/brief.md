# Brief: TaskStore security review before HTTP exposure  (class C, owner: business-analyst)
Produced by oeo:business-analyst (haiku/medium, economy profile). Condensed by the orchestrator; full text in the demo record.
Users & problem: FACT owners keep private task lists; `owner` is caller-supplied (store.py:10). FACT no HTTP/identity code exists.
Desired outcome: every TaskStore mutation enforces owner isolation with a defined result.
Metric: successful cross-owner mutations; baseline 1 (probe: ben deleted ana's task -> True); target 0; measured by unit tests.
Non-goals: HTTP layer, authn/identity, input validation, reporting.py, migrations, README typo, new dependencies.
Evidence: FACT delete() ignores `requester`; SQL has no owner predicate (store.py:32-35). FACT complete() on missing id -> TypeError (store.py:27-30).
Approved acceptance criteria (Business Owner proxy, see decisions.md):
1. delete("ben", <ana's task id>) returns False and ana's task is still listed.
2. Owner can still delete their own task (existing behavior preserved).
3. A regression test for (1) fails on the base commit and passes after the fix; the existing 10 tests pass.
4. Diff limited to taskboard/store.py and tests/test_store.py; no string-built SQL; no new dependency.
