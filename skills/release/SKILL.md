---
name: release
description: OEO release checklist - SemVer bump, changelog entry, release notes, license gate, signed tag and written rollback plan; nothing published without human approval. Use to cut or roll back a release.
---

# Release (OEO Release Manager)

Nothing is published, pushed, tagged remotely or deployed without explicit user approval.

## Prepare
1. **Gates**: all class gates PASS in `.oeo/verification.md` (QA or Security may veto).
2. **Version**: SemVer from the change set since the last tag (`git log <last-tag>..HEAD`):
   breaking -> MAJOR (MINOR while 0.x), feature -> MINOR, fix -> PATCH. Update every version
   source the repo has (package manifest, plugin.json, etc.).
3. **CHANGELOG.md** (Keep a Changelog): move `Unreleased` items under `## [x.y.z] - YYYY-MM-DD`
   in Added / Changed / Deprecated / Removed / Fixed / Security; update compare links.
4. **License gate**: every new or upgraded dependency passes
   `python3 "${CLAUDE_PLUGIN_ROOT}/scripts/oeo.py" license <SPDX...>`; provenance updated.
5. **Release notes**: user-facing summary, upgrade steps for breaking changes, known issues.
6. **Rollback plan** (written before release): how to revert (previous tag/artifact, feature
   flag, migration down/forward-fix), who decides, and the signal that triggers it.

## Publish (only after the user says so)
Signed tag where supported: `git tag -s vX.Y.Z -m "vX.Y.Z"` (fall back to annotated `-a` and
say so). Push and create the release only with explicit approval; the OEO guard hook will ask.

## Failed release / rollback (incident path)
1. Stop the rollout; announce status. 2. Execute the written rollback plan; verify with the
same checks as the release. 3. Record a timeline in `.oeo/decisions.md`. 4. Open a defect that
re-enters Stage 0 with a regression test requirement. 5. Patch release with changelog entry.

## Report
Version, changelog excerpt, gates with evidence, rollback plan, what was published (or "not
published, awaiting approval").
