---
name: finops
description: OEO FinOps / cost governance - report token usage per agent against the class budget, flag overruns, and recommend cheaper routing. Use for multi-agent or long-running OEO engagements, or when asked how much an OEO task cost.
---

# FinOps (OEO Cost Controller)

1. Report actuals vs plan for the current project (and session, if known):
   ```bash
   python3 "${CLAUDE_PLUGIN_ROOT}/scripts/oeo.py" cost --session "${CLAUDE_SESSION_ID}"
   ```
   Data comes from `.oeo/activation-log.jsonl` (router estimates) and `.oeo/finops.jsonl`
   (the SubagentStop hook's best-effort token counts; transcript format is not a stable API,
   so treat numbers as estimates and say so). Main-session tokens are not included.
2. Flag: any agent OVER ESTIMATE, any unplanned agent, class budget exceeded, any role run at
   a higher tier or effort than its contract without a recorded reason.
3. Recommend, in order: fewer agents (one specialist instead of several), smaller prompts (paths
   instead of pasted files), lower tier for bounded tasks, the `economy` profile
   (`OEO_MODEL_PROFILE=economy`). Never recommend skipping a quality gate to save cost.
4. Overruns need a one-line justification in `.oeo/decisions.md`.

Coordination overhead is a first-class metric: report agents invoked vs agents whose output
changed the result (from the handoffs). More agents is not more productivity.
