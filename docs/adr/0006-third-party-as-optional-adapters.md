# 0006. Third-party skills are referenced adapters, never vendored

- Status: Accepted
- Date: 2026-10-30

## Context
Useful skill projects exist (Superpowers, Ponytail, frontend-design, Impeccable, UI UX Pro Max,
Taste, Emil Kowalski's skills, ECC). Licenses vary per repo and sometimes per skill; contents
change upstream; some install hooks or download binaries.

## Options
1. Vendor copies: offline and pinned, but redistribution obligations, staleness, and silent
   inclusion of hooks/binaries.
2. **Reference them in `third_party/registry.yaml` (license verified from upstream LICENSE,
   revision, install command, limitations); the router suggests them only if already installed.**
3. Ignore them: duplicates work the community already did well.

## Decision
Option 2. OEO's core works with zero adapters. ECC is evaluated but not routed (size conflicts
with the context-budget principle).

## Consequences
Users install adapters through upstream installers under upstream licenses. Registry entries need
periodic re-verification; commit SHAs are `UNVERIFIED` where they could not be confirmed.

## Revisit when
An adapter becomes essential to a gate, or the host offers dependency pinning between plugins.
