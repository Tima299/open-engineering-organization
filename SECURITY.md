# Security Policy

## Supported versions
OEO is pre-1.0. Only the latest `0.x` minor release receives security fixes.

| Version | Supported |
|---|---|
| 0.1.x | Yes (current) |
| Older | No |

## Reporting a vulnerability
**Do not open a public issue, discussion or PR for a vulnerability.**

Use GitHub private vulnerability reporting: open the repository's **Security** tab and choose
**Report a vulnerability**
([direct link](https://github.com/Tima299/open-engineering-organization/security/advisories/new)).
If that option is unavailable, open a public issue that says only that you need a private security
contact, with no technical details, and the maintainer will arrange a private channel.

Please include:
- affected version (`version` in `.claude-plugin/plugin.json`) and Claude Code version;
- the file or component (for example `scripts/guard.py`, a hook, an agent's `tools:` list, a skill);
- steps to reproduce or a proof of concept, and the impact you expect;
- whether you want to be credited, and under what name.

Never include real secrets, tokens or private data in a report.

## What to expect
OEO has a single maintainer, so these are best-effort targets, not guarantees:

| Step | Target |
|---|---|
| Acknowledge your report | within 7 days |
| Initial assessment (accepted, needs info, or declined, with reasons) | within 14 days |
| Coordinated disclosure | fix and advisory within 90 days of the report |

If a fix needs longer, the maintainer will tell you why and agree a new date with you. Fixes ship as a
patch release with a GitHub security advisory; reporters are credited unless they ask not to be.
Security fixes are exempt from the public review windows in [GOVERNANCE.md](GOVERNANCE.md).

## Scope
In scope:
- `scripts/` (including `oeo.py`, `guard.py`, `finops_hook.py`) and `hooks/`;
- agent tool permissions (generated `tools:` lists exceeding what a role contract grants);
- routing or policy that could let a change bypass required human approval;
- prompt-injection weaknesses in skills or agents that let untrusted repository, issue or web content
  act as instructions or trigger consequential actions.

Out of scope (report upstream instead):
- Claude Code itself and the model providers;
- third-party adapters listed in [THIRD_PARTY.md](THIRD_PARTY.md), which OEO references but does not ship;
- the target repositories OEO is used on.

Residual risks the project already documents, such as the command guard being a defense-in-depth
pattern match and not a sandbox, are listed in [docs/threat-model.md](docs/threat-model.md). A new
bypass of a documented mitigation is still welcome as a report.

## Hardening
Mitigations are tracked in [docs/threat-model.md](docs/threat-model.md): zero runtime dependencies, a
single dev dependency pinned with hashes, GitHub Actions pinned by SHA, `CODEOWNERS` on policy and script
paths, and signed release tags where signing is available (see [docs/RELEASING.md](docs/RELEASING.md)).
OEO's scripts and hooks add no network calls and no telemetry; the `research` skill uses Claude Code's
web tools only when you ask for research (threat model T12-T14).
