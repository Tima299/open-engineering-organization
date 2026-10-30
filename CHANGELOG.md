# Changelog

All notable changes to this project are documented here. Format:
[Keep a Changelog](https://keepachangelog.com/en/1.1.0/); versioning: [SemVer](https://semver.org/).
While the version is 0.x, minor releases may contain breaking changes (called out under **Changed**).

## [Unreleased]

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

[Unreleased]: https://github.com/Tima299/open-engineering-organization/compare/v0.1.0...HEAD
[0.1.0]: https://github.com/Tima299/open-engineering-organization/releases/tag/v0.1.0
