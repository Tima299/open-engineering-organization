# Architecture Decision Records

Significant decisions, with alternatives and trade-offs. New ADR: copy
[0000-template.md](0000-template.md), take the next number, open a PR labeled `rfc`.
ADRs are superseded explicitly (new ADR + status update), never silently edited.

| # | Decision | Status |
|---|---|---|
| [0001](0001-claude-code-plugin-distribution.md) | Ship as a Claude Code plugin with a self-hosted marketplace | Accepted |
| [0002](0002-contracts-as-source-of-truth.md) | Role contracts are the source of truth; few generated agents | Accepted |
| [0003](0003-model-agnostic-tier-routing.md) | Model routing by tiers and profiles, not model names | Accepted |
| [0004](0004-deterministic-router.md) | Deterministic, data-driven Stage 0 router in stdlib Python | Accepted |
| [0005](0005-apache-2-and-dco.md) | Apache-2.0 license with DCO sign-off | Accepted |
| [0006](0006-third-party-as-optional-adapters.md) | Third-party skills are referenced adapters, never vendored | Accepted |
| [0007](0007-naming.md) | Name: Open Engineering Organization, namespace `oeo` | Accepted |
| [0008](0008-one-owner-per-capability.md) | One owner per capability: adapt ideas, keep skills few | Accepted |
| [0009](0009-engagement-folders-and-deterministic-checks.md) | Engagement folders and deterministic checks behind skills | Accepted |
