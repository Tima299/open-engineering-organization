# 0007. Name: Open Engineering Organization, namespace `oeo`

- Status: Accepted
- Date: 2026-10-30

## Context
Working title from the brief. Checks on 2026-10-30: GitHub repo `Tima299/open-engineering-organization`
exists (ours). PyPI and npm: `open-engineering-organization` unused (HTTP 404); `oeo` is taken on
both by unrelated packages. Claude Code rejects plugin names starting with `claude-`/`anthropic-`.
Trademark databases were **not** searched (no access); this is an open risk.

## Options
1. **Plugin `oeo`, marketplace `open-engineering-organization`**: short skill namespace (`/oeo:deliver`).
2. Plugin `open-engineering-organization`: unambiguous, long to type in every command.

## Decision
Option 1. We do not publish to PyPI/npm, so the `oeo` package-name collision does not apply; if we
ever do, use `open-engineering-organization`.

## Consequences
Possible confusion with unrelated `oeo` packages; mitigated by always pairing with the full name.

## Revisit when
A trademark conflict is found or a package registry release is planned.
