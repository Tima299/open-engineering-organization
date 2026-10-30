# Evaluation suite

OEO is judged by outcomes, not by how its roles sound. Each scenario in `scenarios/` has two parts:

| Part | What it checks | How it runs | Status |
|---|---|---|---|
| `router_input` + `expect` | Triage class, roles activated / not activated, gates, license verdicts, budget | `python3 evals/run.py` (CI, every PR) | **Automated** |
| `agentic` | Real behavior of skills + agents on `examples/taskboard` | Manual or scripted `claude -p` run, results committed | **Automated** with `agentic.py` (real `claude -p`, costs money); [results](results/agentic/SUMMARY.md) |

Spec coverage: tasks 1-14 of Section 11 (`01`-`14`, with `12a`/`12b`), plus negative tests
`15` prompt injection in repository content, `16` unknown vocabulary rejected, `17` unavailable
adapter, `18` failed review loop; and v0.2 capabilities `19` feature research from public evidence
and `20` marketing launch without release gates.

## Run the deterministic suite
```bash
python3 -m pip install --require-hashes -r requirements-dev.txt
python3 evals/run.py            # writes results/router-latest.json
python3 evals/run.py --no-write # CI mode
```

## Run an agentic scenario (automated)
```bash
python3 evals/agentic.py 11 --arm oeo        # OEO plugin loaded with --plugin-dir
python3 evals/agentic.py 11 --arm baseline   # same request, plain Claude Code
python3 evals/agentic.py --summary           # writes results/agentic/SUMMARY.md
```
Each run uses a fresh copy of the fixture, real `claude -p` (costs money; `--max-budget-usd`
caps it), scores the scenario's `agentic.auto` checks (changed files, tests, probes, triage class,
subagent count, ledger rules), and writes raw JSON plus the diff to `results/agentic/`. Main
session model defaults to `sonnet` for both arms; OEO subagents use the `economy` profile.

## Run an agentic scenario (manual)
1. Copy the fixture so runs never share state: `cp -r examples/taskboard /tmp/tb && cd /tmp/tb && git init -q && git add -A && git commit -qm base`.
   If the scenario has `agentic.setup`, apply it to the copy first: create each `files` entry
   (path + content), apply each `edits` entry once (replace `old` with `new` in `path`), and export
   the `environment` variables. `run.py` ignores `setup`; it only matters for agentic runs.
2. Install the plugin (README quickstart) and run the scenario's `agentic.prompt` in Claude Code
   in that directory (interactive, or `claude -p "<prompt>"` for scripted runs).
3. Score each `success_criteria` item PASS/FAIL **from evidence** (diff, test output, `.oeo/` files).
4. Record `measure` values: total tokens (`python3 <plugin>/scripts/oeo.py cost` for subagents
   plus the session's own usage), agents invoked vs agents whose output changed the result,
   wall time, files changed, gate failures and retries.
5. Commit raw results as `results/<date>-<scenario>-<model-profile>.md` (template below). Publish
   failures too.

**Baseline:** run the same prompt without OEO (plugin disabled, same model, same fixture copy)
and score the same criteria. Report both; do not claim an improvement from a single run.

```
scenario: 07-security-flaw   date:   profile:   claude-code version:   oeo version:
arm: oeo | baseline
criteria: | # | criterion | PASS/FAIL | evidence |
measures: tokens_total= subagent_tokens= agents_invoked= agents_that_changed_outcome= wall_s= files_changed= gate_failures= retries=
notes / anomalies:
```

## Interpreting results
- One run per arm is an anecdote. Treat results as initial benchmarks until each scenario has
  at least 5 runs per arm; report medians and spread, not just the best run.
- Token budgets in `config/models.yaml` are uncalibrated until recalibrated from these results.
