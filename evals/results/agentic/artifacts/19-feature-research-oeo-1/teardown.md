# Teardown: Todoist recurring tasks

Evidence: `ledger.md` here (accessed 2026-10-30). Official Todoist help and API pages were **not readable** (egress denied). Behavior rests on search summaries (inferred) and Doist's official SDK source (observed). Re-check the live help center before relying on any inferred row.

**What it does:** a to-do app. A repeating due is set from natural-language text (row 4, observed). Completing an occurrence is reported to reschedule it rather than close it (row 7, inferred).

**Syntax note:** observed: recurrence is set via a natural-language `dueString` in the SDK (row 4). Gap: the exact syntax, the `every!` string format, and whether the returned `string` carries it (row 6). The `every` vs `every!` basis difference is a search snippet only (row 10, inferred).

**User flow (from SDK source and search summaries, not walked through)**
1. Set a due from natural-language text (row 4, observed; exact syntax unverified, row 6).
2. Two modes are reported: `every` counts from the scheduled date, `every!` from the completion date (row 10, inferred).
3. Complete the task: it reportedly reschedules to the next occurrence (row 7, inferred).
4. "Complete forever" is reported to stop the series (row 13, inferred). Reschedule then complete is reported to skip ahead (row 12, inferred).
5. Optional end date, or ongoing (row 16, inferred). No count limit found (row 17, gap).

**Data and behavior model**
- Due object: `isRecurring`, `string`, `date`, optional `datetime`, `timezone`, `lang` (row 1, observed in SDK types).
- Setting `resetRecurringSubtasks` exists in the SDK user settings (row 24a, observed).
- Times are reported as floating by default; fixed times tie to a zone (row 19, inferred). Recurring time-of-day and DST: gap (row 20).
- The SDK exposes completed-item query parameters (row 9, observed in SDK types); server behavior not verified. Per-occurrence history: unknown.

**Strengths (inferred)**
- The SDK accepts `dueString` on add and update (row 4, observed). Whether the app UI uses the same input is unverified.
- Two reported bases: scheduled date vs completion date (row 10, inferred).
- "Complete forever" appears to be a dedicated stop action (rows 13, 14, inferred).

**Weaknesses and complaints (community, unverified; non-canonical Reddit mirrors)**
- A user reports that drag-to-reschedule removed the repeat (row 22, inferred from one report).
- Users reportedly confuse the two bases (row 27, inferred).
- A question post asks whether overdue due times trail completion time; unconfirmed (row 23, gap).
- Users report subtasks stay completed unless "reset sub-tasks" is on (row 24b, inferred).

**Adopt / avoid / differentiate**
- Adopt, if verified against the live help center: two bases (scheduled vs completion date); completion reschedules rather than closes; an explicit stop action.
- Avoid: natural-language parsing in v1; time of day and time zones; drag that reportedly drops the repeat (row 22, one report).
- Differentiate: a small, explicit, date-only rule that is easy to read in SQLite and the store API.

**Open unknowns:** packaging and pricing (not researched); official text for close, history and skip; count-limited recurrence; whether `until` is a real end form; per-occurrence history; whether missed occurrences are skipped (see decision 5 below).

## Implications for taskboard

**Minimal data model (one forward-only migration in `taskboard/db.py`)**
`due` stays the current occurrence (ISO date). Add four columns:
```
ALTER TABLE tasks ADD COLUMN recur_every INTEGER CHECK (recur_every IS NULL OR recur_every >= 1);
ALTER TABLE tasks ADD COLUMN recur_unit TEXT CHECK (recur_unit IN ('day','week','month','year'));
ALTER TABLE tasks ADD COLUMN recur_basis TEXT NOT NULL DEFAULT 'due' CHECK (recur_basis IN ('due','completed'));
ALTER TABLE tasks ADD COLUMN recur_until TEXT;  -- optional ISO date; drop if out of scope
```
`recur_every IS NULL` means not recurring. Intended: existing rows stay non-recurring (verify with a migration test).

**Completion semantics (store `complete`)**
1. Not recurring: set `done = 1`, as today.
2. Recurring, `basis = 'completed'`: next = today + interval.
3. Recurring, `basis = 'due'`: next = due + interval. Whether to skip missed occurrences to the next future one is a **decision for the user**: a user quote reports Todoist does this, but it is not verified (row 11). Until decided, implement the simpler form (next = due + interval, one step per completion) and flag it.
4. If `recur_until` is set and next is after it: `done = 1`. Else `due = next`, `done = 0`.
5. Month arithmetic: our design choice is to clamp to month end (not sourced from Todoist; test it). No history table in v1.

**Explicitly leave out:** natural-language parsing; times, time zones, DST (date-only, matching ISO `due`); count limits; a separate skip action (reschedule by editing `due`); weekday anchoring; sub-task reset; undo; completion history.

**Open questions for the user**
1. Do we need both bases (scheduled and completion date), or is one enough for v1?
2. Is date-only acceptable?
3. Is `until` in v1, or deferred?
4. Store API: structured arguments, or one parsed string?
5. Decision needed: should missed occurrences skip to the next future one? A user quote reports this Todoist behavior (row 11, not verified). Options: (a) skip missed occurrences (matches the reported behavior, unverified); (b) generate one step per completion (simpler, predictable). Recommendation: (b) until verified.
6. Is completion history needed now? It adds a table.
