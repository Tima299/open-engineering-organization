---
name: launch
description: OEO go-to-market - positioning, a provable-copy gate, and a launch plan with owned/borrowed/rented channels. Use for marketing work, landing-page copy, or a public launch announcement.
---

# Launch (OEO Product Marketer + Developer Advocate)

Technical release mechanics (version, changelog, tag, rollback) belong to `oeo:release`. This skill
owns **why anyone should care**, and it never invents numbers, customers or claims.

## 1. One shared context file first
Create or refresh `.oeo/product-marketing.md` before writing any copy; every later step reads it.
Draft it from `.oeo/<engagement>/brief.md` (if present) and the repository (README, docs, changelog, issues),
then list what is wrong or missing; the orchestrator asks the user. Competitor facts come from an
`oeo:research` ledger, not from guesses. Sections: category · ideal customer · job to be done (push, pull, habit, anxiety) ·
alternatives (direct, adjacent, do-nothing) · customer phrases (verbatim, with source) ·
objections + answers · proof points (each with evidence) · voice table · **learnings log**.

- **Voice table**: `| attribute | means | does not mean | example line |`, plus one row per
  context (docs, launch post, error message, social).
- **Learnings log**: `| date | lesson (1 sentence) | evidence + sample size | applies to | active/watch/retired |`.
  Only tested results or repeated user corrections earn a row. Retire rows; never delete them.

## 2. Positioning (one paragraph, then test it)
For [customer] who [job/pain], [product] is a [category] that [key benefit]. Unlike
[main alternative], it [differentiator backed by a proof point]. If a claim has no proof
point, drop it or name the evidence that would unlock it.

## 3. Copy gate (every headline and claim)
Run `python3 "${CLAUDE_PLUGIN_ROOT}/scripts/oeo.py" copy-lint <file>` on every draft. Must-fix
findings block the copy. Should-fix findings are fixed or justified in one line each.
Load [copy rules](references/copy.md). First diagnose the input: blank, existing real voice, or
a point edit. The diagnosis caps how much you may change. Each line must pass three questions.
Can the reader picture it? Could it be proven false? Could a competitor say it word for word?
Revert any edit you cannot justify.

## 4. Launch plan
- **Readiness gate first**: is it simple to try, lovable for the core job, and complete for that
  job? If not, say so; do not polish forever either.
- **Phases**: internal dogfood → private beta → public launch → follow-up (week 1) → steady state.
  Each phase has an owner, an exit signal and a metric.
- **Channels**: owned (docs, site, repo, newsletter) > borrowed (partners, guests, communities) >
  rented (social, ads, marketplaces). Every rented or borrowed touch points back to an owned one.
- Open-source launches: README quickstart under 15 minutes, honest limitations, a contribution
  path, and labelled `good first issue`s before announcing.

## 5. Recurring loops (optional)
For a recurring check (e.g. weekly metrics or community questions), write down:
- the check cadence, kept separate from the act-when condition;
- the state kept between runs, so actions are idempotent;
- the stop condition;
- the human approval point before anything is published.

Output: positioning, channel plan with owners and metrics, and copy drafts that passed the gate.
Publishing anything needs explicit user approval.
