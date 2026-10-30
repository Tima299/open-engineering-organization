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


def parse_trace(stream_out):
    """stream-json -> (result event, compact tool trace). Main-session entries have main=True."""
    events, trace = [], []
    for line in stream_out.splitlines():
        if line.strip().startswith("{"):
            try:
                events.append(json.loads(line))
            except json.JSONDecodeError:
                continue
    result = next((e for e in reversed(events) if e.get("type") == "result"), {})
    for e in events:
        if e.get("type") != "assistant":
            continue
        for c in (e.get("message") or {}).get("content") or []:
            if isinstance(c, dict) and c.get("type") == "tool_use":
                inp = c.get("input") or {}
                trace.append({"tool": c.get("name"), "main": e.get("parent_tool_use_id") is None,
                              "agent": inp.get("subagent_type"), "skill": inp.get("skill"),
                              "cmd": (inp.get("command") or "")[:200] if c.get("name") == "Bash" else None,
                              "file": inp.get("file_path")})
    return result, trace


def score(auto, work, arm, final="", trace=None):
    results = []
    trace = trace or []

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
    for path in auto.get("unchanged", []):
        add(f"unchanged {path}", path not in files)
    for pattern in auto.get("exists_glob", []):
        if arm == "oeo" or not pattern.startswith(".oeo"):  # .oeo/ artifacts are OEO-only
            add(f"exists {pattern}", bool(glob.glob(str(work / pattern))))
    for s in auto.get("diff_contains", []):
        add(f"diff_contains {s!r}", s in added)
    for s in auto.get("diff_not_contains", []):
        add(f"diff_not_contains {s!r}", s not in added)
    if auto.get("tests_pass"):
        code, out, err = sh([sys.executable, "-m", "unittest", "discover", "-s", "tests"], work)
        add("tests_pass", code == 0, (err or out).strip().splitlines()[-1:] or "")
    for probe in auto.get("probes", []):
        code, out, err = sh([sys.executable, "-c", probe["code"]], work)
        expected = probe.get("expect_any") or [probe["expect"]]
        add(f"probe {probe['name']}", any(e in out for e in expected), (out + err).strip()[-200:])
    for s in auto.get("final_contains", []):
        add(f"final_contains {s!r}", s.lower() in final.lower())
    if auto.get("copy_lint_glob"):
        hits = sorted({f for pattern in auto["copy_lint_glob"]
                       for f in glob.glob(str(work / pattern), recursive=True, include_hidden=True) if os.path.isfile(f)})
        must = [f"{Path(f).name}:{x['line']} {x['rule']}" for f in hits
                for x in checks.copy_lint(Path(f).read_text(encoding="utf-8", errors="replace")) if x["severity"] == "must-fix"]
        add("copy_lint (no must-fix in the copy files)", hits and not must, must or [Path(f).name for f in hits] or "no copy files found")
    for chk in auto.get("oeo_checks", []):  # run an `oeo` checker on a file the run produced
        files = sorted(glob.glob(str(work / chk["glob"]), include_hidden=True))
        code = sh([sys.executable, str(ROOT / "scripts" / "oeo.py"), chk["cmd"], files[0]], work)[0] if files else None
        add(f"oeo {chk['cmd']} {chk['glob']}", code == 0, "no file" if not files else f"exit {code}")
    if auto.get("no_git_tags"):
        tags = sh(["git", "tag"], work)[1].split()
        add("no_git_tags", not tags, tags)
    for name in auto.get("skill_used", []) if arm == "oeo" else []:
        used = {x["skill"] for x in trace if x["skill"]} | {x["agent"] for x in trace if x["agent"]}
        add(f"skill_used {name}", any(name in (u or "") for u in used), sorted(u for u in used if u))
    for sub_cmd in auto.get("oeo_command_used", []) if arm == "oeo" else []:
        cmds = [x["cmd"] for x in trace if x["cmd"] and "oeo.py" in x["cmd"]]
        add(f"oeo_command_used {sub_cmd}", any(f"oeo.py\" {sub_cmd}" in c or f"oeo.py {sub_cmd}" in c for c in cmds),
            [c[-60:] for c in cmds][:6])
    if auto.get("reverify_after_edit") and arm == "oeo":
        idx = lambda pred: max([i for i, x in enumerate(trace) if pred(x)], default=-1)  # noqa: E731
        last_edit = idx(lambda x: x["main"] and x["tool"] in ("Edit", "Write", "MultiEdit")
                        and not str(x["file"] or "").count("/.oeo/"))
        last_qa = idx(lambda x: x["main"] and x["tool"] in ("Agent", "Task") and "qa-verifier" in str(x["agent"]))
        add("reverified_after_last_main_edit", last_edit < last_qa or last_qa == -1 and last_edit == -1,
            f"last main-session edit #{last_edit}, last qa-verifier call #{last_qa}")
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
    cmd = ["claude", "-p", prompt, "--output-format", "stream-json", "--verbose", "--model", model, "--session-id", session,
           "--permission-mode", "acceptEdits", "--allowedTools", *TOOLS, "--max-budget-usd", str(budget)]
    if arm == "oeo":
        cmd += ["--plugin-dir", str(ROOT)]
    started = dt.datetime.now(dt.timezone.utc)
    code, out, err = sh(cmd, work, timeout=timeout, env=env)
    result, trace = parse_trace(out)
    if not result:
        result = {"is_error": True, "result": (out or err)[-2000:]}
    sh(["git", "add", "-A", "--intent-to-add", "--", ".", ":!.oeo"], work)  # new files appear in diffs
    checks_ = score(ag.get("auto") or {}, work, arm, result.get("result") or "", trace)
    subagents = checks.read_jsonl(work / ".oeo" / "finops.jsonl")
    record = {
        "scenario": scenario["id"], "arm": arm, "model": model, "profile": profile if arm == "oeo" else None,
        "date": started.date().isoformat(), "claude_code": sh(["claude", "--version"], work)[1].strip(),
        "oeo_commit": commit,
        "exit_code": code, "is_error": result.get("is_error"), "cost_usd": result.get("total_cost_usd"),
        "duration_s": round((result.get("duration_ms") or 0) / 1000, 1), "num_turns": result.get("num_turns"),
        "wall_s": round((dt.datetime.now(dt.timezone.utc) - started).total_seconds()),
        "usage": result.get("usage"), "subagents": [{k: s.get(k) for k in ("agent_type", "models", "input_tokens",
                                                     "output_tokens", "cache_write_tokens")} for s in subagents],
        "activation": checks.read_jsonl(work / ".oeo" / "activation-log.jsonl")[-1:] if arm == "oeo" else None,
        "files_changed": changed_files(work), "checks": checks_, "workdir": str(work),
        "trace_summary": {"tools": {k: sum(1 for x in trace if x["tool"] == k) for k in sorted({x["tool"] for x in trace})},
                          "skills": sorted({x["skill"] for x in trace if x["skill"]}),
                          "agents": [x["agent"] for x in trace if x["agent"]],
                          "oeo_commands": [x["cmd"].split("oeo.py", 1)[1][:80] for x in trace
                                           if x["cmd"] and "oeo.py" in x["cmd"]][:30]},
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


def rescore(json_path, workdir=None):
    """Re-run the scenario's current auto checks against a finished run's workdir (kept in /tmp)."""
    yaml = oeo._yaml()
    path = Path(json_path)
    record = json.loads(path.read_text(encoding="utf-8"))
    work = Path(workdir or record.get("workdir") or "")
    if not work.is_dir():
        sys.exit(f"workdir {work} is gone; re-run the scenario instead")
    scen = yaml.safe_load(next((ROOT / "evals" / "scenarios").glob(f"{record['scenario']}*.yaml")).read_text())
    old = record["checks_passed"]
    record["checks"] = score(scen["agentic"].get("auto") or {}, work, record["arm"], record.get("final_message") or "")
    record["checks_passed"] = f"{sum(c['pass'] for c in record['checks'])}/{len(record['checks'])}"
    record["rescored"] = {"date": dt.date.today().isoformat(), "previous": old,
                          "reason": "scenario checks corrected after the run (see NOTES.md)"}
    path.write_text(json.dumps(record, indent=1) + "\n", encoding="utf-8")
    print(f"{path.name}: {old} -> {record['checks_passed']}")


def summary():
    files = sorted(OUT.glob("*.json"))
    lines = ["# Agentic eval results", "", "Raw JSON and diffs for every run are in this folder. Main session: "
             "`sonnet`; OEO subagents: `economy` profile.", "",
             "| Run | OEO commit | Checks | Cost USD | Wall s | Subagents | Class |", "|---|---|---|---|---|---|---|"]
    for f in files:
        r = json.loads(f.read_text(encoding="utf-8"))
        cls = (r.get("activation") or [{}])[0].get("class", "") if r.get("activation") else "-"
        cost = f"{r['cost_usd']:.2f}" if isinstance(r.get("cost_usd"), (int, float)) else "?"
        lines.append(f"| [{f.stem}]({f.name}) | {r.get('oeo_commit') or '-'} | {r['checks_passed']} | {cost} | "
                     f"{r.get('wall_s', 'n/a')} | {len(r.get('subagents') or [])} | {cls} |")
    notes = OUT / "NOTES.md"
    lines += ["", "One run per arm is an anecdote, not a benchmark. Failed checks are listed per run in the JSON "
              "files" + (f"; scoring corrections and findings are in [NOTES.md](NOTES.md)." if notes.exists() else ".")]
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
    ap.add_argument("--rescore", metavar="RESULT_JSON", help="re-run current auto checks on a finished run")
    ap.add_argument("--workdir", help="workdir for --rescore (older records do not store it)")
    a = ap.parse_args()
    if a.summary:
        return summary()
    if a.rescore:
        return rescore(a.rescore, a.workdir)
    if not a.scenario:
        ap.error("scenario id required")
    run(a.scenario, a.arm, a.model, a.profile, a.timeout, a.max_budget_usd)


if __name__ == "__main__":
    main()
