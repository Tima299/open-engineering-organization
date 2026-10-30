#!/usr/bin/env python3
# SPDX-License-Identifier: Apache-2.0
"""Run the deterministic part of the OEO evaluation suite.

Each scenario in evals/scenarios/*.yaml states router inputs and expected activation
(class, roles that must / must not activate, gates, license verdicts). This runner checks
them against the real router and writes raw results to evals/results/. The agentic part of
each scenario (`agentic:`) is run by humans or CI with model access; see evals/README.md.
"""
import argparse
import datetime as dt
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))
import oeo  # noqa: E402


def check(scenario, lock):
    exp, inp = scenario["expect"], scenario.get("router_input")
    failures = []
    plan = None
    if inp:
        plan = oeo.route(lock, inp["type"], inp.get("touches", []), inp.get("signals", []),
                         inp.get("files"), inp.get("lines"), inp.get("profile"))
        ids = {r["id"] for r in plan["roles"]}
        gates = {g["id"] for g in plan["gates"]}
        if "class" in exp and plan["class"] != exp["class"]:
            failures.append(f"class {plan['class']} != expected {exp['class']} (rule {plan['rule']})")
        failures += [f"missing role {r}" for r in exp.get("roles_include", []) if r not in ids]
        failures += [f"unexpected role {r}" for r in exp.get("roles_exclude", []) if r in ids]
        if "max_roles" in exp and len(ids) > exp["max_roles"]:
            failures.append(f"{len(ids)} roles activated > max {exp['max_roles']}")
        if "max_tier3" in exp:
            t3 = sorted(r["id"] for r in plan["roles"] if r["tier"] == 3)
            if len(t3) > exp["max_tier3"]:
                failures.append(f"tier 3 over-activated: {t3}")
        failures += [f"missing gate {g}" for g in exp.get("gates_include", []) if g not in gates]
        failures += [f"unexpected gate {g}" for g in exp.get("gates_exclude", []) if g in gates]
        failures += [f"missing skill {s}" for s in exp.get("skills_include", []) if s not in plan["skills"]]
        failures += [f"missing adapter {a}" for a in exp.get("adapters_include", []) if a not in plan["optional_adapters"]]
        for rid, mode in (exp.get("modes") or {}).items():
            got = next((r["mode"] for r in plan["roles"] if r["id"] == rid), None)
            if got != mode:
                failures.append(f"{rid} mode {got} != {mode}")
        if "within_budget" in exp and (plan["estimate_tokens"] <= plan["budget_tokens"]) != exp["within_budget"]:
            failures.append(f"estimate {plan['estimate_tokens']} vs budget {plan['budget_tokens']}")
    for spdx, verdict in (exp.get("license") or {}).items():
        got = oeo.license_verdict(spdx, lock["routing"]["licenses"])
        if got != verdict:
            failures.append(f"license {spdx}: {got} != {verdict}")
    if exp.get("router_rejects"):
        bad = scenario["router_rejects_input"]
        try:
            oeo.route(lock, bad["type"], bad.get("touches", []), bad.get("signals", []))
            failures.append("router accepted invalid input")
        except ValueError:
            pass
    return failures, plan


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--no-write", action="store_true", help="do not write evals/results/")
    args = ap.parse_args(argv)
    yaml = oeo._yaml()
    lock = oeo.load_lock()
    results, failed = [], 0
    for path in sorted((ROOT / "evals" / "scenarios").glob("*.yaml")):
        scenario = yaml.safe_load(path.read_text(encoding="utf-8"))
        failures, plan = check(scenario, lock)
        failed += bool(failures)
        status = "FAIL" if failures else "PASS"
        print(f"{status}  {scenario['id']:<34} {scenario['title']}")
        for f in failures:
            print(f"        - {f}")
        results.append({"id": scenario["id"], "status": status, "failures": failures,
                        "class": plan and plan["class"], "roles": plan and [r["id"] for r in plan["roles"]],
                        "estimate_tokens": plan and plan["estimate_tokens"]})
    print(f"\n{len(results) - failed}/{len(results)} deterministic scenarios passed")
    if not args.no_write:
        out = ROOT / "evals" / "results" / "router-latest.json"
        out.write_text(json.dumps({"generated": dt.date.today().isoformat(), "kind": "deterministic-router",
                                   "results": results}, indent=1) + "\n", encoding="utf-8")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
