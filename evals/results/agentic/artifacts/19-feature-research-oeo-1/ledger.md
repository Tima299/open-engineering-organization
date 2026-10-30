# Finding ledger: how Todoist implements recurring tasks

Access date for every row: 2026-10-30. The tag column uses the research skill tags (observed / inferred / unknown). The label column is Observed (read in a primary file), Documented (quoted text we read directly), Inferred, or Gap.

Search snippets are WebSearch summaries, not fetched pages and not verbatim Todoist text. Any row resting on one is tagged inferred.

**Source outcome states**
- todoist.com help center: **failed**, egress proxy `connect_rejected` (403). Policy denial, not retried.
- developer.todoist.com (REST v2, Sync v9, v1): **failed**, same denial.
- WebFetch on any host: **failed**, "proxy refused the connection".
- registry.npmjs.org `@doist/todoist-sdk` 15.10.0 (Doist's official SDK): **ok**, read directly. Strongest primary evidence available.
- WebSearch (6 queries): **ok**, summaries only; no engagement ranking.
- Reddit pages cited below are **non-canonical mirrors** (redlib, birdcat, belloworld). Community signal only, not Todoist statements.

## Findings

| # | claim | observed / inferred / unknown | label | evidence (URL or file + access date) | search boundary |
|---|---|---|---|---|---|
| 1 | Due object fields: `isRecurring` (bool), `string` (text), `date` (YYYY-MM-DD), optional `datetime`, `timezone`, `lang`; `due` is nullable on Task | observed | Observed | https://registry.npmjs.org/@doist/todoist-sdk/-/todoist-sdk-15.10.0.tgz, file `package/dist/types/types/tasks/types.d.ts:2-9,105-112` (accessed 2026-10-30) | n/a |
| 2 | The same due shape appears in Sync responses and webhooks | observed | Observed | https://registry.npmjs.org/@doist/todoist-sdk/-/todoist-sdk-15.10.0.tgz, `dist/types/types/sync/response.d.ts:87-94`, `dist/types/types/webhooks/types.d.ts:87` (accessed 2026-10-30) | n/a |
| 3 | Wire JSON is snake_case (`is_recurring`); the SDK converts it to camelCase | inferred | Inferred from SDK case converter | https://registry.npmjs.org/@doist/todoist-sdk/-/todoist-sdk-15.10.0.tgz, `dist/esm/utils/case-conversion.js` (accessed 2026-10-30). Inferred from the converter, not from traffic. | Wire names not seen directly. No live traffic. |
| 4 | Recurrence is created with a natural-language `dueString` on add and update; `"no date"` clears the due date | observed | Observed | https://registry.npmjs.org/@doist/todoist-sdk/-/todoist-sdk-15.10.0.tgz, `dist/types/types/tasks/requests.d.ts:17` (add), `:122-126` (update) (accessed 2026-10-30) | n/a |
| 5 | `dueDate` and `dueDatetime` are mutually exclusive; `dueString` is a separate input | observed | Observed | https://registry.npmjs.org/@doist/todoist-sdk/-/todoist-sdk-15.10.0.tgz, `dist/types/types/tasks/requests.d.ts:22-25`, `:136-139` (accessed 2026-10-30) | n/a |
| 6 | Exact string format for `every!` in `due.string`, and whether it is returned verbatim | unknown | Gap | no source: gap. SDK documents natural-language input only; checked https://registry.npmjs.org/@doist/todoist-sdk/-/todoist-sdk-15.10.0.tgz 2026-10-30, no sample payload | Official API doc not readable. No sample payload in SDK. |
| 7 | Completing a recurring task reportedly reschedules it instead of closing it | inferred | Inferred from SDK webhook enum and close endpoint | https://registry.npmjs.org/@doist/todoist-sdk/-/todoist-sdk-15.10.0.tgz, `dist/esm/types/webhooks/tasks.js:31-40,50-54` (`item_completed` intent; "recurring-task completions" comment), `dist/esm/consts/endpoints.js`, `dist/esm/clients/task-client.js:225-231` (`POST .../close`) (accessed 2026-10-30) | No doc text confirms reschedule for the close call. Not tested on an own account. |
| 8 | Closing a non-recurring task marks it complete and moves it to history, with its subtasks | unknown | Gap | no source: gap. Only a search summary of a third-party connector doc mentioned this, with no URL identified (accessed 2026-10-30). | Connector page not identified; official close docs not readable. |
| 9 | Completed items can be queried by completion date and due date, and all completed tasks can be listed | observed | Observed | https://registry.npmjs.org/@doist/todoist-sdk/-/todoist-sdk-15.10.0.tgz, `dist/types/clients/task-client.d.ts:13-16`, `dist/types/types/tasks/requests.d.ts:53-73,169-172` (accessed 2026-10-30) | Whether each recurring occurrence is its own history row: unknown. |
| 10 | `every` schedules the next occurrence from the scheduled (due) date; `every!` from the completion date | inferred | Inferred from search summary | WebSearch "Todoist help recurring due dates every vs every! complete task reschedule" (2026-10-30), summary of https://todoist.com/help/articles/360000636289 (page not fetched; summary is not verbatim) | Official text not read. |
| 11 | Missed occurrence on completion: the next future occurrence is scheduled. Example: `every Sunday` completed on Wednesday recurs the following Sunday; `every! Sunday` recurs the following Wednesday | inferred | Secondhand Reddit quote | https://redlib.belloworld.it/r/todoist/comments/1g7ebju/every_week_vs_every_week (non-canonical Reddit mirror; a user quoting Todoist docs; accessed 2026-10-30) | Quote not checked against the help text. Not verified. |
| 12 | Rescheduling a recurring task and then completing it sets the next occurrence from the completion date; occurrences between the original due date and the new date are skipped | inferred | Inferred from search summary | WebSearch 'Todoist "Complete forever" recurring task help article skip' (2026-10-30), summary of https://www.todoist.com/help/articles/complete-a-task-with-a-recurring-date-dmI6SVqdP (page not fetched; summary is not verbatim) | Official page text not read. |
| 13 | "Complete forever" (task menu) completes the recurring task permanently and ends the recurrence; on a parent it also completes subtasks | inferred | Inferred from search summary | WebSearch 'Todoist "Complete forever" recurring task help article skip' (2026-10-30), summary of https://www.todoist.com/help/articles/complete-a-task-with-a-recurring-date-dmI6SVqdP (not fetched; not verbatim) | Official page text not read. |
| 14 | "Complete forever" sends one final completion to an integrated Beeminder goal; deleting the task removes that data | inferred | Single user's report (one Beeminder forum user) | WebSearch 'Todoist "Complete forever" recurring task help article skip' (2026-10-30), https://forum.beeminder.com/t/avoiding-sudden-todoist-caused-derails/11215 (accessed 2026-10-30) | One user's report, not a Todoist statement. Not verified. |
| 15 | No dedicated "skip" action was found; the closest is reschedule then complete | unknown | Gap | no source: gap. Query 'Todoist "Complete forever" recurring task help article skip' (2026-10-30) returned no skip action. A third-party guide's "Skip" mention is unsourced. | Official article not readable; app menus not checked (no own account used). |
| 16 | A recurrence can have an end date, or be ongoing | inferred | Inferred from search summary | WebSearch 'Todoist recurring task "until" end date "for 5 times" recurrence natural language' (2026-10-30), summary of https://todoist.com/help/articles/set-a-recurring-due-date (not fetched; not verbatim) | Official text not read. |
| 17 | Count-limited recurrence ("for N times") exists | unknown | Gap | no source: gap. Query 'Todoist recurring task "until" end date "for 5 times" recurrence natural language' (2026-10-30) returned no count syntax. | Search snippets only. Official help page not readable. |
| 18 | Natural-language end syntax such as `until <date>` is accepted | unknown | Gap | no source: gap. Example from a search summary of a third-party guide (`every 14 days 7am from nov 1 until dec 15`); page not identified (2026-10-30). | Not verified against Todoist. |
| 19 | Due times are floating by default; a fixed time is tied to a time zone and moves with it | inferred | Inferred from search summary | WebSearch 'Todoist recurring tasks time of day timezone floating due date help article "every day at"' (2026-10-30), summary of https://todoist.com/help/articles/360001450039 (not fetched; not verbatim) | Summary only. |
| 20 | Recurring tasks with a set time of day, and their DST behavior | unknown | Gap | no source: gap. Same query as row 19 (2026-10-30) found no Todoist documentation. Toodledo forum posts about time-zone shifts concern a different product and are excluded. | Search summaries only. |
| 21 | `every week` shifts with the completion or scheduled date, while `every Monday` stays on Monday | inferred | Inferred from a third-party guide and a user thread | Third-party guide and a 2022 r/todoist thread in search results (accessed 2026-10-30). Community reports only. | Not checked against official text. |
| 22 | A user reports that dragging a recurring task removes its recurrence (May 2025; web app, not iOS for some users) | inferred | Inferred from one user report | https://axebps-redlib.hf.space/r/todoist/comments/1ke1i6f/dragging_a_recurring_task_removes_the_recurrence (non-canonical Reddit mirror; accessed 2026-10-30) | One thread, May 2025, outside the last 30 days. Vote counts not visible. Not reproduced by us. |
| 23 | An overdue recurring task's due time can trail the completion time of its last occurrence | unknown | Gap | single unconfirmed question post: https://reddit.birdcat.cafe/r/todoist/comments/1jkshj6/recurring_task_due_date_time_is_broken_it_appears (non-canonical Reddit mirror; accessed 2026-10-30) | Post not fetched (WebFetch refused). No confirmed reply found. |
| 24a | `resetRecurringSubtasks` is a user setting in the SDK | observed | Observed | https://registry.npmjs.org/@doist/todoist-sdk/-/todoist-sdk-15.10.0.tgz, `dist/esm/types/sync/resources/user-settings.js:27` (accessed 2026-10-30) | Setting exists. Its effect in the app not tested. |
| 24b | Subtasks of a recurring task stay completed across occurrences unless the "reset sub-tasks" setting is on | inferred | Inferred from search summaries | WebSearch 'Todoist "Complete forever" recurring task help article skip' (2026-10-30): summary of https://todoist.com/help/articles/6819183940124 (not fetched). WebSearch 'Todoist recurring task complaint reddit reschedule breaks recurrence due date changed timezone' (2026-10-30): non-canonical mirror https://reddit.birdcat.cafe/r/todoist/comments/1jeoc2u/behavior_of_subtasks_of_recurring_tasks (not fetched). | Behavior not tested. Summaries only. |
| 25 | Floating versus fixed time appears in the due object only through `timezone` and `datetime` | inferred | Inferred from SDK types and search summary (row 19) | https://registry.npmjs.org/@doist/todoist-sdk/-/todoist-sdk-15.10.0.tgz, `dist/types/types/tasks/types.d.ts:105-112` (accessed 2026-10-30) | No live payload seen. Whether `timezone` is null for floating tasks: unknown. |
| 26 | Official REST v2, Sync v9 and v1 pages describe completion, the due object, and recurrence rules | unknown | Gap | source: https://developer.todoist.com/rest/v2/ and https://developer.todoist.com/sync/v9/ (blocked, egress 403; accessed 2026-10-30). Gap, not retried per policy. | Must be re-checked from an allowed network or by the user. |
| 27 | Community complaints cluster around reschedule breaking the repeat, every vs every! confusion, and overdue drift | inferred | Inferred from rows 11, 21, 22, 23 | Non-canonical Reddit mirrors and search summaries, 2022 to 2025 (accessed 2026-10-30) | Four threads only. Not a count of all posts. No engagement ranking. |

## Question status

| question | status | rows |
|---|---|---|
| Natural-language recurrence strings | partial | 4, 6, 18 |
| every vs every! | partial (inferred from snippets) | 10, 11 |
| Behavior on completion (reschedule, history) | partial | 7, 8, 9, 12 |
| End conditions (until, for N times) | partial | 16, 17, 18 |
| Times, time zones, floating | partial | 19, 20, 25 |
| Skipping and ending a recurrence | partial | 13, 14, 15 |
| Data model in the API | partial | 1, 2, 3, 5, 24a, 26 |
| Known edge cases and complaints | partial (community, unverified) | 21, 22, 23, 24b, 27 |

## Gaps (not fetched, not guessed)
1. Todoist help center pages (todoist.com, get.todoist.help): egress 403, not retried.
2. developer.todoist.com REST v2, Sync v9 and v1 reference: egress 403, not retried.
3. Reddit and blog pages: WebFetch refused. Only search summaries were read. Reddit mirrors are non-canonical.
4. Live own-account walkthrough: not done. It needs a user-owned account, which was not requested.
