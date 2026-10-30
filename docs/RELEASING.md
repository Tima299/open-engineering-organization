# Releasing OEO

Maintainer procedure for releasing OEO itself. Releases are manual and need no CI secrets.
Versions follow [SemVer](https://semver.org/); while pre-1.0, only the latest `0.x` minor is supported
([SECURITY.md](../SECURITY.md)).

Replace `X.Y.Z` below with the new version.

## Checklist
1. **Checks are green** on the commit to release, locally and in CI:
   ```sh
   python3 scripts/oeo.py validate
   python3 scripts/oeo.py build --check
   python3 -m unittest discover -s tests -t .
   python3 evals/run.py --no-write
   ```
2. **Bump the version**: set `"version"` in `.claude-plugin/plugin.json` to `X.Y.Z`.
   Breaking change to roles, routing or hooks: bump the minor while pre-1.0, the major after.
3. **Update the changelog**: in [CHANGELOG.md](../CHANGELOG.md), move the `Unreleased` entries into a
   new `## [X.Y.Z] - YYYY-MM-DD` section ([Keep a Changelog](https://keepachangelog.com/)) and leave an
   empty `Unreleased` heading.
4. **Rebuild**: `python3 scripts/oeo.py build`, then rerun step 1 so generated files match.
5. **Commit**: `git commit -s -m "chore(release): vX.Y.Z"` and merge it to `main` through the normal
   review path.
6. **Tag** the merge commit with a signed tag:
   ```sh
   git tag -s vX.Y.Z -m "OEO vX.Y.Z"
   ```
   If signing is unavailable, use an annotated tag (`git tag -a vX.Y.Z -m "OEO vX.Y.Z"`) and say in the
   release notes that the tag is unsigned.
7. **Push the tag**: `git push origin vX.Y.Z`.
8. **Publish a GitHub release** for the tag, using the `X.Y.Z` changelog section as the notes.
9. **Verify install** from the tag in a clean Claude Code session:
   `/plugin marketplace add Tima299/open-engineering-organization#vX.Y.Z`, then
   `/plugin install oeo@open-engineering-organization`.
10. **Announce**: the GitHub release is the announcement. If GitHub Discussions is enabled, link it there.

## Rollback
Never move or delete a published tag; users may be pinned to it with
`/plugin marketplace add Tima299/open-engineering-organization#vX.Y.Z`.
To undo a bad release, revert the change on `main`, then publish a **patch release** (the next patch
version, for example `0.1.1`) with the steps above and a changelog entry that names the problem.
Edit the bad release's notes to point to the fix.

## Security releases
Prepare the fix privately (GitHub security advisory), release it as a patch, and publish the advisory
with the release. See [SECURITY.md](../SECURITY.md).
