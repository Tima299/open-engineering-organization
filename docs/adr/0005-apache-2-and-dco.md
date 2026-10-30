# 0005. Apache-2.0 license with DCO sign-off

- Status: Accepted
- Date: 2026-10-30

## Context
The project should be embeddable in commercial products, accept outside contributions with
low friction, and be clear about patents.

## Options
1. MIT: shortest, most common in the skill ecosystem; no explicit patent grant.
2. **Apache-2.0: permissive, commercial-friendly, explicit patent grant and termination, and
   section 5 makes "inbound = outbound" the default for contributions.**
3. Copyleft (GPL/AGPL): forces downstream openness; blocks many commercial embeddings.
Contribution model: CLA (heavy, needs legal entity) vs **DCO** (`git commit -s`, lightweight).

## Decision
Apache-2.0 with a NOTICE file and SPDX headers in source files; DCO sign-off for contributions.

## Consequences
Downstream users must keep LICENSE/NOTICE. MIT/BSD/Apache dependencies are compatible; GPL-family
dependencies are blocked by the legal gate (`org/routing.yaml` `licenses`).

## Revisit when
A foundation adopts the project and requires a different contribution agreement.
