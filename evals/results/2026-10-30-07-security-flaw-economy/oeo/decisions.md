# Decisions log
| date | decision | options | rationale | by |
|---|---|---|---|---|
| 2026-10-30 | Scope = delete() authorization only (AC 1-4) | (a) BA's full list incl. validation + complete() errors; (b) authz only | Smallest sufficient change; other findings recorded as risks for separate Class B tickets | orchestrator as Business Owner proxy (demo run; real runs ask the user) |
| 2026-10-30 | Denial returns False (no exception) | raise PermissionError vs return False | Matches existing bool contract of delete(); does not reveal whether the id exists | orchestrator (Tech Lead, implementation-approach) |
