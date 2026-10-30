# Model and effort routing

Routing is **policy**: OEO says which model tier and effort each role should use; the host
decides what actually runs. This page explains the policy, how to change it, and how to check
what really ran. Decision record: [ADR 0003](adr/0003-model-agnostic-tier-routing.md).

## Policy layers
1. **Role contract** (`org/roles/<id>.yaml` → `model_routing`): tier `light|standard|advanced`,
   effort `low|medium|high`, and `escalate_to` (tier or `human`) after the retry budget.
2. **Profile** (`config/models.yaml` → `profiles`): maps each tier to a `model_id` (API name) and a
   `host_alias` (what Claude Code accepts in agent files and the Agent tool).
   - `default`: the requested initial table (Sonnet for junior/middle/BA/PM/QA/advisors, Opus for
     senior/lead/architect/principal/CTO/security).
   - `economy`: one step cheaper everywhere.
3. **Overrides** (`config/models.yaml` → `overrides`): per role, for all profiles or one profile.
4. **Selection**: `OEO_MODEL_PROFILE=economy` (router output) or `python3 scripts/oeo.py build
   --profile economy` (agent frontmatter). Show the effective table: `python3 scripts/oeo.py models`.

Escalation is never the default: after 2 failed attempts at a gate, raise effort one step; if that
fails, move to `escalate_to`; if that is `human`, stop and ask with options.

## How Claude Code resolves the model (docs accessed 2026-10-30)
- Generated agents carry `model:` and `effort:` frontmatter from the build profile.
- The orchestrator passes the router's alias as the Agent tool `model` parameter (aliases only).
- Precedence (Claude Code v2.1.251+): per-call parameter > agent frontmatter >
  `CLAUDE_CODE_SUBAGENT_MODEL` > main-session model. `CLAUDE_CODE_SUBAGENT_MODEL_FORCE=1` makes the
  environment variable win for every subagent. `CLAUDE_CODE_EFFORT_LEVEL` overrides agent effort.
- Aliases differ by provider: on Bedrock/Vertex `sonnet` and `haiku` resolve to older models than
  on the Anthropic API. Add a provider-specific profile instead of editing contracts.

## Verify what ran
- The SubagentStop hook records the `models` seen in each subagent transcript in
  `.oeo/finops.jsonl` (best effort: the transcript format is internal to Claude Code).
- `/agents` in Claude Code shows each agent's configured model.
- If the recorded model differs from the router's plan, report it; do not assume the plan held.

## Porting to another provider or host
Add a profile with that provider's model IDs and aliases; contracts do not change. A different
host needs an adapter equivalent to `HOST_TOOLS` and `render_agent()` in `scripts/oeo.py`
(capabilities → tool names, frontmatter format). None besides Claude Code exists yet.

## Known limitations
- No guarantee: user settings, environment variables or org policy can override the plan.
- Effort support depends on model and Claude Code version; unsupported levels fall back.
- Main-session tokens are not attributed to roles; only subagents are measured.
- Budgets in `config/models.yaml` are initial guesses until calibrated from real logs.
