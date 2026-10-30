# Governance

This document describes how OEO is run today, not how we hope it will be run later.

## Model
OEO uses a **benevolent-maintainer** model. There is one maintainer, GitHub
[@Tima299](https://github.com/Tima299), who has final say on every decision. Decisions are made in
public, by **lazy consensus**: a proposal is accepted if nobody raises a blocking objection within the
review window. When the project has **three or more maintainers**, it will move to a maintainer council;
that change is itself a governance change and follows the 7-day process below.

## Decision process
| Change | Review window |
|---|---|
| Normal changes (fixes, docs, new skills, roles within the existing schema) | 72 hours |
| Governance, license, role schema, routing policy, precedence policy | 7 days |

- The window starts when the PR or issue is ready for review. The maintainer applies the same windows to
  their own changes so that others have a chance to object.
- A blocking objection must say what is wrong and what would resolve it. If it stays unresolved, the
  maintainer decides and records the reason in the thread.
- Security fixes are handled privately under [SECURITY.md](SECURITY.md) and are exempt from the windows;
  they are disclosed in the release notes and advisory.

## Major changes: RFC and ADR
Major changes (architecture, governance, license, role schema, routing or precedence policy, anything
that breaks existing users) start as a public issue labeled `rfc` describing the problem, the proposal,
alternatives and impact. Once accepted, the decision is recorded as an Architecture Decision Record in
[docs/adr/](docs/adr/) so the rationale survives the thread.

## Contributor ladder
| Level | How you get there | What you can do |
|---|---|---|
| Contributor | Anyone who opens an issue, PR, or review | Participate under the [Code of Conduct](CODE_OF_CONDUCT.md) |
| Regular contributor | 3 or more merged PRs | No extra permissions; the usual pool for triager invitations |
| Triager | Invited by a maintainer | Apply labels, close duplicates, reproduce and confirm bugs (GitHub Triage permission) |
| Maintainer | Sustained, high-quality contributions; nominated by a maintainer; lazy consensus of the maintainers | Merge, release, administer the repository, enforce the Code of Conduct |

Today the only maintainer is @Tima299, so "consensus of the maintainers" means that person's decision.
A maintainer can step down at any time by saying so in an issue.

## Working in public
Discussion, decisions, and the plan happen in public issues, pull requests, ADRs, and the
[ROADMAP.md](ROADMAP.md). Private channels are used only for security reports and conduct reports.
Conduct reports about the maintainer cannot be handled by the maintainer; in that case use GitHub's
"Report content" feature, as listed in the [Code of Conduct](CODE_OF_CONDUCT.md).

## Bus factor
**The project currently has a bus factor of 1.** If the maintainer becomes unavailable, nobody else can
merge, release, or administer the repository. What reduces the damage:
- The release procedure is written down in [docs/RELEASING.md](docs/RELEASING.md) so another maintainer
  can follow it without tribal knowledge.
- CI needs no secrets, so there are no credentials that could be lost with one person.
- Recruiting a second maintainer is a stated priority in [ROADMAP.md](ROADMAP.md).
- The code is Apache-2.0, so anyone can fork and continue the project.

What does not reduce it: repository admin recovery depends on GitHub account recovery of @Tima299.
Until there is a second maintainer, that dependency stands.

## Changing this document
Edit via PR. Changes follow the 7-day governance window and are recorded in
[CHANGELOG.md](CHANGELOG.md).
