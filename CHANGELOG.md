# Changelog

All notable changes to this project are documented here. Format:
[Keep a Changelog](https://keepachangelog.com/en/1.1.0/); versioning: [SemVer](https://semver.org/).
While the version is 0.x, minor releases may contain breaking changes (called out under **Changed**).

## [Unreleased]

## [0.2.0] - 2026-10-30

### Added
- Skills `research` (feature/competitor/recency research from public or authorized evidence),
  `chief-of-staff` (cross-engagement brief, issue triage, decision meetings) and `launch`
  (positioning, copy gate, launch plan).
- Roles `market-researcher` and `product-marketer` (Tier 3, run by the generic advisor agent);
  task type `marketing`, signal `external-research`.
- Ideas adapted from 12 more projects (rea, Paperclip, chief-of-staff skills, last30days,
  I Have ADHD, pm-skills, marketingskills, Awesome Design, Open Design, Firecrawl, Playwright CLI,
  playwright-skill), credited in THIRD_PARTY.md; ADR 0008.

### Changed
- `design-direction`: question-first direction, DESIGN.md capture, craft rules, anti-slop tiers,
  scored review panel. `verify`: real-browser UI evidence; regression proof in a git worktree.
  `business-review`: lean PRD, red-team, pre-mortem, assumption triage. `deliver`: goal chain,
  single task owner, status words, budget tiers. `finops`: 80%/100% tiers and paid-credit rules.
- Shared agent output style: verdict first, at most 5 items per list, stop after 3 failed fixes.
- Plugin author, marketplace owner and copyright holder: Tima299.

## [0.1.0] - 2026-10-30

### Added
- Claude Code plugin `oeo` with a self-hosted marketplace (`open-engineering-organization`).
- 35 role contracts in three tiers, a JSON Schema for them, and a decision-rights matrix with
  vetoes, fallbacks and escalation rules.
- Deterministic Stage 0 router (`scripts/oeo.py route`): Class A-D triage, role/skill/gate
  activation with logged reasons, model routing by tier and profile, token estimates and budgets.
- Skills: `deliver`, `business-review`, `verify` (security and simplicity checklists),
  `design-direction`, `release`, `finops`.
- Generated agents: 9 dedicated roles plus generic `specialist` and `advisor`.
- Hooks: PreToolUse confirmation guard for destructive/publishing commands and likely secrets;
  SubagentStop token logging to `.oeo/finops.jsonl`.
- Legal gate (`oeo license`), provenance registry for 8 third-party projects, SBOM.
- Evaluation suite: deterministic routing scenarios run in CI, agentic scenario specs and a
  fixture project (`examples/taskboard`).
- Community health files, governance, threat model, ADRs 0001-0007, CI.

[Unreleased]: https://github.com/Tima299/open-engineering-organization/compare/v0.2.0...HEAD
[0.2.0]: https://github.com/Tima299/open-engineering-organization/compare/v0.1.0...v0.2.0
[0.1.0]: https://github.com/Tima299/open-engineering-organization/releases/tag/v0.1.0
