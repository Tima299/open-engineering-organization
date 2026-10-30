# Research methods

## Source decision table
| Question type | First source | Tool | Then |
|---|---|---|---|
| What the feature does, limits, settings | help center, docs, API reference | web search + fetch (Firecrawl at scale) | own-account walkthrough |
| How the flow feels, UI states, copy | live product, own account | browser (Playwright CLI) screenshots + snapshots | DESIGN.md capture via `oeo:design-direction` |
| What changed recently, roadmap signals | changelog, release notes, blog | fetch; map the changelog section | community posts |
| What users love or hate, now | Reddit, HN, GitHub issues, X, YouTube (last 30 days) | `last30days` if installed, else web search with date filters | rank by engagement |
| Data model, API shape | public API docs, SDKs, open-source clients | fetch; read SDK code | own-session traffic (HAR) only if authorized |
| Internals of an installed app | **authorized** reverse engineering only | `rea` | never copy code or assets |
| Pricing and packaging | pricing page, plan comparison, docs on limits | fetch with date stamp | archived snapshots for history |

## Retrieval ladder (stop at the first rung that answers the question)
1. **Search** for the exact page.
2. **Fetch / scrape** a known URL. Extract only the fields needed.
3. **Map** a site to find the right subpage.
4. **Crawl** one section (bounded page count).
5. **Interact** with a browser only when the static fetch falls short.
6. **Monitor** for changes only when the user asks for ongoing tracking.

Each step has a done-when check. Expand only for gaps that could change the answer. Report
truncated reads as partial coverage, and keep quoted excerpts separate from summaries.

## Recency research (last 30 days)
- Pass the resolved handles, subreddits, repo and site into every query.
- Before running, check for keyword traps such as ambiguous names or common words. Reframe, or
  ask one clarifying question.
- Group results by story; a story seen in several sources outranks a single viral post.
- Quote at least two attributed community voices with links; never invent or composite quotes.

## Cost and safety
- Paid tools (Firecrawl, scraping APIs) count against `oeo:finops`. Honor the user's credit cap.
  If usage cannot be measured, say "unknown" and stop paid collection.
- Auth, credit or quota errors are terminal: check status once, report, stop.
- Quote URLs in shell commands. Store no cookies or credentials in `.oeo/`.
- Suggested `.gitignore`: `.oeo/*/raw/`.

Ideas adapted from morluto/rea, mvanhorn/last30days-skill and firecrawl/firecrawl-claude-plugin
(all MIT); see THIRD_PARTY.md.
