#!/usr/bin/env python3
# SPDX-License-Identifier: Apache-2.0
"""Run the agentic part of an OEO eval scenario with the real Claude Code CLI.

    python3 evals/agentic.py <scenario-id> --arm oeo|baseline [--model sonnet] [--profile economy]
    python3 evals/agentic.py --summary

Each run copies examples/taskboard to a fresh git repo, applies the scenario's `agentic.setup`,
runs `claude -p` headless (the oeo arm loads this repository with --plugin-dir; the baseline arm
gets the same request without OEO), then scores the scenario's `agentic.auto` checks and writes
raw results to evals/results/agentic/. Costs real money: every run prints its USD cost.
Tool permissions in the copy: edits accepted, Bash allowed (the copy is a throwaway repo with no
remote); the OEO guard hook still asks, and an unanswered ask is denied in headless mode.
"""
import argparse
import datetime as dt
import glob
import json
import os
import shutil
import subprocess
import sys
import tempfile
import uuid
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))
import checks  # noqa: E402
import oeo  # noqa: E402

OUT = ROOT / "evals" / "results" / "agentic"
TOOLS = ["Read", "Grep", "Glob", "Edit", "Write", "Bash", "Agent", "Task", "Skill", "TodoWrite",
         "WebSearch", "WebFetch"]


def sh(cmd, cwd, timeout=600, env=None):
    p = subprocess.run(cmd, cwd=cwd, capture_output=True, text=True, timeout=timeout, env=env)
    return p.returncode, p.stdout, p.stderr


def prepare(scenario, work):
    shutil.copytree(ROOT / scenario["agentic"].get("fixture", "examples/taskboard"), work,
                    ignore=shutil.ignore_patterns("__pycache__"))
    setup = scenario["agentic"].get("setup") or {}
    for f in setup.get("files", []):
        (work / f["path"]).parent.mkdir(parents=True, exist_ok=True)
        (work / f["path"]).write_text(f["content"], encoding="utf-8")
    for e in setup.get("edits", []):
        p = work / e["path"]
        p.write_text(p.read_text(encoding="utf-8").replace(e["old"], e["new"], 1), encoding="utf-8")
    for cmd in (["git", "init", "-q"], ["git", "add", "-A"],
                ["git", "-c", "user.name=eval", "-c", "user.email=eval@example.invalid", "commit", "-qm", "base"]):
        sh(cmd, work)
    return {k: str(v) for k, v in (setup.get("environment") or {}).items()}


def changed_files(work):
    _, out, _ = sh(["git", "status", "--porcelain", "--untracked-files=all"], work)
    files = [line[3:].strip() for line in out.splitlines() if line.strip()]
    return sorted(f for f in files if not f.startswith(".oeo/") and "__pycache__" not in f)


def score(auto, work, arm):
    results = []

    def add(name, ok, detail=""):
        results.append({"check": name, "pass": bool(ok), "detail": str(detail)[:300]})

    files = changed_files(work)
    _, diff, _ = sh(["git", "diff", "HEAD"], work)
    added = "\n".join(l[1:] for l in diff.splitlines() if l.startswith("+") and not l.startswith("+++"))
    for f in files:  # untracked files count as added text too
        if not (work / f).is_dir() and f not in diff:
            added += "\n" + (work / f).read_text(encoding="utf-8", errors="replace")
    if "max_files_changed" in auto:
        add("max_files_changed", len(files) <= auto["max_files_changed"], files)
    if "files_changed_subset" in auto:
        extra = [f for f in files if f not in auto["files_changed_subset"]]
        add("files_changed_subset", not extra, extra or files)
    for s in auto.get("diff_contains", []):
        add(f"diff_contains {s!r}", s in added)
    for s in auto.get("diff_not_contains", []):
        add(f"diff_not_contains {s!r}", s not in added)
    if auto.get("tests_pass"):
        code, out, err = sh([sys.executable, "-m", "unittest", "discover", "-s", "tests"], work)
        add("tests_pass", code == 0, (err or out).strip().splitlines()[-1:] or "")
    for probe in auto.get("probes", []):
        code, out, err = sh([sys.executable, "-c", probe["code"]], work)
        add(f"probe {probe['name']}", probe["expect"] in out, (out + err).strip()[-200:])
    if arm == "oeo":
        plans = checks.read_jsonl(work / ".oeo" / "activation-log.jsonl")
        if "oeo_class" in auto:
            add("oeo_class", plans and plans[-1].get("class") == auto["oeo_class"],
                plans[-1].get("class") if plans else "no triage logged")
        subagents = checks.read_jsonl(work / ".oeo" / "finops.jsonl")
        if "max_subagents" in auto:
            add("max_subagents", len(subagents) <= auto["max_subagents"], [s.get("agent_type") for s in subagents])
        if "ledger_glob" in auto:
            ledgers = glob.glob(str(work / auto["ledger_glob"]))
            problems = checks.ledger_check(Path(ledgers[0]).read_text(encoding="utf-8")) if ledgers else ["no ledger"]
            add("ledger_check", not problems, problems[:3])
    return results


def run(scenario_id, arm, model, profile, timeout, budget):
    yaml = oeo._yaml()
    path = next((ROOT / "evals" / "scenarios").glob(f"{scenario_id}*.yaml"))
    scenario = yaml.safe_load(path.read_text(encoding="utf-8"))
    ag = scenario["agentic"]
    prompt = ag["prompt"] if arm == "oeo" else ag.get("baseline_prompt") or ag["prompt"].replace("/oeo:deliver ", "")
    work = Path(tempfile.mkdtemp(prefix=f"oeo-eval-{scenario['id']}-{arm}-")) / "repo"
    extra_env = prepare(scenario, work)
    env = {k: v for k, v in os.environ.items() if k not in ("CLAUDE_CODE_SESSION_ID", "CLAUDE_PROJECT_DIR")}
    env.update(extra_env, OEO_MODEL_PROFILE=profile)
    session = str(uuid.uuid4())
    commit = sh(["git", "rev-parse", "--short", "HEAD"], ROOT)[1].strip() + \
        ("-dirty" if sh(["git", "status", "--porcelain", "--untracked-files=no"], ROOT)[1].strip() else "")
    cmd = ["claude", "-p", prompt, "--output-format", "json", "--model", model, "--session-id", session,
           "--permission-mode", "acceptEdits", "--allowedTools", *TOOLS, "--max-budget-usd", str(budget)]
    if arm == "oeo":
        cmd += ["--plugin-dir", str(ROOT)]
    started = dt.datetime.now(dt.timezone.utc)
    code, out, err = sh(cmd, work, timeout=timeout, env=env)
    try:
        result = json.loads(out)
    except json.JSONDecodeError:
        result = {"is_error": True, "result": (out or err)[-2000:]}
    checks_ = score(ag.get("auto") or {}, work, arm)
    subagents = checks.read_jsonl(work / ".oeo" / "finops.jsonl")
    record = {
        "scenario": scenario["id"], "arm": arm, "model": model, "profile": profile if arm == "oeo" else None,
        "date": started.date().isoformat(), "claude_code": sh(["claude", "--version"], work)[1].strip(),
        "oeo_commit": commit,
        "exit_code": code, "is_error": result.get("is_error"), "cost_usd": result.get("total_cost_usd"),
        "duration_s": round((result.get("duration_ms") or 0) / 1000, 1), "num_turns": result.get("num_turns"),
        "usage": result.get("usage"), "subagents": [{k: s.get(k) for k in ("agent_type", "models", "input_tokens",
                                                     "output_tokens", "cache_write_tokens")} for s in subagents],
        "activation": checks.read_jsonl(work / ".oeo" / "activation-log.jsonl")[-1:] if arm == "oeo" else None,
        "files_changed": changed_files(work), "checks": checks_,
        "checks_passed": f"{sum(c['pass'] for c in checks_)}/{len(checks_)}",
        "final_message": (result.get("result") or "")[:4000],
    }
    OUT.mkdir(parents=True, exist_ok=True)
    n = 1 + len(list(OUT.glob(f"{record['date']}-{scenario['id']}-{arm}-*.json")))
    stem = f"{record['date']}-{scenario['id']}-{arm}-{n}"
    (OUT / f"{stem}.json").write_text(json.dumps(record, indent=1) + "\n", encoding="utf-8")
    _, diff, _ = sh(["git", "diff", "HEAD"], work)
    (OUT / f"{stem}.patch").write_text(diff, encoding="utf-8")
    print(f"{stem}: checks {record['checks_passed']}, cost ${record['cost_usd']}, {record['duration_s']}s, "
          f"turns {record['num_turns']}, subagents {len(subagents)}, workdir {work}")
    return record


def summary():
    rows = [json.loads(p.read_text(encoding="utf-8")) for p in sorted(OUT.glob("*.json"))]
    lines = ["# Agentic eval results (raw data in this folder)", "",
             "| Scenario | Arm | Model / profile | Checks | Cost USD | Time s | Turns | Subagents | Class |",
             "|---|---|---|---|---|---|---|---|---|"]
    for r in rows:
        cls = (r.get("activation") or [{}])[0].get("class", "") if r.get("activation") else ""
        lines.append(f"| {r['scenario']} | {r['arm']} | {r['model']}{' / ' + r['profile'] if r.get('profile') else ''} | "
                     f"{r['checks_passed']} | {r['cost_usd']} | {r['duration_s']} | {r['num_turns']} | "
                     f"{len(r.get('subagents') or [])} | {cls} |")
    lines += ["", "One run per arm is an anecdote, not a benchmark. Failed checks are listed per run in the JSON files."]
    (OUT / "SUMMARY.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print("\n".join(lines))


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("scenario", nargs="?")
    ap.add_argument("--arm", choices=["oeo", "baseline"], default="oeo")
    ap.add_argument("--model", default="sonnet", help="main-session model for both arms")
    ap.add_argument("--profile", default="economy", help="OEO model profile for subagents (oeo arm)")
    ap.add_argument("--timeout", type=int, default=1800)
    ap.add_argument("--max-budget-usd", type=float, default=5.0)
    ap.add_argument("--summary", action="store_true")
    a = ap.parse_args()
    if a.summary:
        return summary()
    if not a.scenario:
        ap.error("scenario id required")
    run(a.scenario, a.arm, a.model, a.profile, a.timeout, a.max_budget_usd)


if __name__ == "__main__":
    main()
