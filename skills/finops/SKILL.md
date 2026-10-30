---
name: finops
description: OEO cost governance - token use per agent vs. estimate and class budget, 80%/100% budget tiers, paid-tool credits, cheaper-routing advice. Use for multi-agent or long-running work or "what did it cost?"
---

# FinOps (OEO Cost Controller)

1. Report actuals vs plan for the current project (and session, if known):
   ```bash
   python3 "${CLAUDE_PLUGIN_ROOT}/scripts/oeo.py" cost --session "${CLAUDE_SESSION_ID}"
   ```
   Data comes from three logs:
   - `.oeo/activation-log.jsonl`: router estimates.
   - `.oeo/finops.jsonl`: per-subagent tokens, written by the SubagentStop hook.
   - `.oeo/sessions/<id>.json`: the orchestrator's own tokens, written by the Stop hook.
   Both hooks parse Claude Code's internal transcript format, so call the numbers estimates.
   `oeo cost` reports subagents, the main session and the all-in total separately.
   `oeo cost --check` exits 1 at 80% of the class budget and 2 at 100%. `oeo:deliver` runs it
   before each subagent call; the tier rules are below.
2. Flag: any agent OVER ESTIMATE, any unplanned agent, class budget exceeded, any role run at
   a higher tier or effort than its contract without a recorded reason.
3. Recommend, in order: fewer agents (one specialist instead of several), smaller prompts (paths
   instead of pasted files), lower tier for bounded tasks, the `economy` profile
   (`OEO_MODEL_PROFILE=economy`). Never recommend skipping a quality gate to save cost.
4. Overruns need a one-line justification in `.oeo/decisions.md`.

## Budget tiers (per engagement; per agent when estimates exist)
| Spend vs budget | Rule |
|---|---|
| < 80% | normal |
| 80-100% | warn the user; critical-path work only |
| >= 100% | pause and ask; continue only with a recorded human override |

**Paid external tools** (Firecrawl, scraping APIs, paid model endpoints) count too. Log credits used
in `.oeo/decisions.md`, and honor the user's cap. If usage cannot be measured, report it as
unknown and stop paid collection; never guess.

Coordination overhead is a first-class metric: report agents invoked vs agents whose output
changed the result (from the handoffs). More agents is not more productivity.
