# Taskboard

Taskboard is a tiny per-user to-do service: each owner has their own task list, stored in SQLite
(in memory by default). It is **the fixture project for the Open Engineering Organization (OEO)
evaluations** and for the plugin quickstart. It is small on purpose, and it contains seeded defects
(listed below) so that agentic runs have something real to find and fix.

Python 3 standard library only; no installation step.

## Quickstart

```bash
cd examples/taskboard
python3 -m unittest discover -s tests
```

```python
from taskboard import TaskStore

store = TaskStore()                                  # or TaskStore("tasks.db")
task_id = store.add("ana", "write the release notes", due="2030-01-31")
store.complete("ana", task_id)
print(store.list("ana"))
```

## Layout

- `taskboard/store.py` - `TaskStore`: `add`, `list`, `complete`, `delete`.
- `taskboard/db.py` - schema creation and the forward-only `MIGRATIONS` list (version table).
- `taskboard/reporting.py` - open-task counts per owner.
- `tests/` - happy-path unit tests (they pass today, and they deliberately do not cover the defects below).

Reports recieve their rows straight from the store, so there is no caching layer to invalidate.

## Seeded defects (for OEO evals)

Do not fix these in this repository; evaluation runs fix them in a scratch copy.

- `TaskStore.complete()` fails badly for an id that does not exist (scenarios 02, 10, 12a, 15, 16, 18).
- `TaskStore.delete()` has an authorization gap between users (scenario 07).
- `reporting.py` is far heavier than the job it does (scenario 09).
- `tasks` has no `priority` column yet; adding one without losing data is the migration exercise (scenario 08).
- This README contains one deliberate typo (scenario 11).
