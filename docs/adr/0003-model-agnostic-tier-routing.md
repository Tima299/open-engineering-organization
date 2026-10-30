# 0003. Model routing by tiers and profiles, not model names

- Status: Accepted
- Date: 2026-10-30

## Context
The spec's routing table names Sonnet/Opus, but also forbids hard-coding provider model names
in role definitions and requires portability. Claude Code (docs accessed 2026-10-30) accepts
`model` and `effort` in agent frontmatter; the Agent tool's per-call `model` takes aliases only;
per-call model > frontmatter > `CLAUDE_CODE_SUBAGENT_MODEL` (v2.1.251+).

## Options
1. Model IDs in each contract: simple, but every model release touches 35 files.
2. **Contracts name a tier (`light`/`standard`/`advanced`) + effort; `config/models.yaml` maps tiers
   to `model_id` (API) and `host_alias` (Claude Code) per profile; per-role overrides; selection by
   `OEO_MODEL_PROFILE`.**
3. Runtime auto-selection by a model: opaque and itself costly.

## Decision
Option 2. `oeo validate` rejects provider model names in contracts.

## Consequences
New model = one config line + `oeo build`. Routing is policy, not a guarantee: users or env vars
can override the model at runtime; `docs/model-routing.md` explains how to verify what ran.

## Revisit when
The host offers verifiable per-agent routing, or a second provider profile is contributed.
