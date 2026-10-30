# 0008. One owner per capability: adapt ideas, keep skills few

- Status: Accepted (extends 0006)
- Date: 2026-10-30
- Deciders: maintainer (@Tima299)

## Context
Twelve more community projects were evaluated: rea, Paperclip, two chief-of-staff skills,
last30days, I Have ADHD, pm-skills, marketingskills, Awesome Design, Open Design, Firecrawl and
Playwright. Together they hold well over 500 skills, tools and agents, and they overlap heavily.
Three of them cover competitor research, three cover design-system capture, two cover browser
automation, and three cover status reporting. Loading all of them burns context and gives
conflicting instructions. Some carry costs: paid APIs, telemetry on by default, hooks, or legal
risk (reverse engineering).

## Options
1. Bundle or route every project's skills: maximum coverage; bloat, duplication, conflicts.
2. **Each capability has exactly one OEO skill. The best ideas from each project are re-expressed
   in OEO's own words inside that skill. Upstreams stay optional adapters only where they add
   real power (tools, data, catalogs).**
3. Ignore them: loses proven methods.

## Decision
Option 2. Skills go from 6 to 9. Ownership:

| Capability | OEO owner | Ideas adapted from | Optional adapter (if installed) |
|---|---|---|---|
| External / competitor / feature research | `research` (new) | rea, last30days, Firecrawl | last30days, firecrawl, playwright-cli, rea (authorized use only) |
| Cross-engagement status, triage, decisions | `chief-of-staff` (new) | chief-of-staff (alirezarezvani, ECC), Paperclip | none |
| Positioning, copy, launch | `launch` (new) | marketingskills | marketing-skills |
| Brief, PRD, red-team, pre-mortem | `business-review` | pm-skills | pm-skills (new-product) |
| Visual direction, DESIGN.md, anti-slop | `design-direction` | Awesome Design, Open Design, Firecrawl design | open-design, awesome-design-md, ... |
| UI evidence in a real browser | `verify` | Playwright CLI, playwright-skill | playwright-cli |
| Goal chain, ownership, status words | `deliver` | Paperclip | none |
| Budget tiers, paid-credit discipline | `finops` | Paperclip, Firecrawl | none |
| Output style (action first, at most 5 items) | shared agent preamble | I Have ADHD | none |

Duplicates removed: no second competitor-research method in `launch`, which reads `research`
output. No second status format in `deliver`, which links to `chief-of-staff`. No separate
ADHD skill: one output style for every agent. Two Tier 3 roles were added (market-researcher,
product-marketer), both run by the generic `advisor` agent, so the agent count is unchanged.

## Consequences
- Attribution: every adapted idea is listed per upstream in THIRD_PARTY.md ("Ideas adapted into
  OEO"); no upstream text, brand assets or DESIGN.md files are copied.
- Research defaults to public evidence; reverse engineering requires the user's authorization.
- Context cost grows by 3 skill descriptions (about 150 tokens per session); method detail is in
  references loaded only when used.

## Revisit when
A capability's activation logs show the OEO skill is routinely bypassed in favor of an adapter
(promote the adapter), or a skill is never activated (merge or remove it).
