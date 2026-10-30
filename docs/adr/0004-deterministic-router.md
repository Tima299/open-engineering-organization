# 0004. Deterministic, data-driven Stage 0 router in stdlib Python

- Status: Accepted
- Date: 2026-10-30

## Context
Proportionality ("a typo never activates the company") must be testable. If the model both
classifies and activates roles from prose, results drift and cannot be evaluated in CI.

## Options
1. Prose instructions only: zero code, untestable, inconsistent.
2. **The model reports facts (type, domains, signals, size); a pure function applies rules from
   `org/routing.yaml` and returns class, roles, skills, gates and budget.**
3. A classifier model call: costs tokens on every request and is non-deterministic.

## Decision
Option 2, in `scripts/oeo.py route`, standard library only so it runs wherever the plugin is
installed. YAML sources are compiled to `org/org.lock.json` by `oeo build` (PyYAML is a
development dependency only).

## Consequences
Classification quality now depends on honest fact reporting by the orchestrator (the router
refuses Class A without a size estimate and rejects unknown vocabulary). Policy changes are
reviewable data diffs with eval scenarios. The lock file must be rebuilt after edits (CI checks).

## Revisit when
Eval runs show systematic misreporting of facts that a different input design would avoid.
