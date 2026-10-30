"""Command-line interface: route (+ --log), cost, license, models, validate, build --check."""
import json
import os
import subprocess
import sys
import unittest
from datetime import datetime

from ._common import IsolatedTestCase, SCRIPTS, oeo, subprocess_env


class RouteCommandTests(IsolatedTestCase):
    def test_json_and_text_output_and_invalid_input(self):
        code, out, _ = self.run_cli("route", "--type", "trivial", "--files", "1", "--lines", "5", "--json",
                                    "--touches", "docs, ui", "--signals", "")
        self.assertIsNone(code)
        plan = json.loads(out)
        self.assertEqual(plan["class"], "A")
        self.assertEqual(plan["inputs"]["touches"], ["docs", "ui"])  # comma list is split and trimmed
        self.assertEqual({r["id"] for r in plan["roles"]}, {"junior-developer", "qa-verifier"})
        _, out, _ = self.run_cli("route", "--type", "feature", "--touches", "auth", "--profile", "economy")
        self.assertIn("OEO triage: Class C (Significant)  rule=risky-domain  profile=economy", out)
        self.assertIn("security-engineer", out)
        self.assertEqual(list(self.tmp.iterdir()), [])  # no --log: nothing written
        code, _, _ = self.run_cli("route", "--type", "nonsense")
        self.assertIn("unknown type 'nonsense'", str(code))
        code, _, _ = self.run_cli("route", "--type", "feature", "--profile", "nope")
        self.assertIn("unknown model profile 'nope'", str(code))

    def test_log_appends_a_json_line_to_the_project_oeo_directory(self):
        argv = ("route", "--type", "trivial", "--files", "1", "--lines", "2", "--log",
                "--session", "s1", "--summary", "fix typo")
        code, out, err = self.run_cli(*argv)
        self.assertIsNone(code)
        log = self.tmp / ".oeo" / "activation-log.jsonl"
        self.assertIn(f"(logged to {log})", err)  # stderr, so `--json --log` stdout stays valid JSON
        self.assertNotIn("logged to", out)
        entry = json.loads(log.read_text(encoding="utf-8").splitlines()[0])
        self.assertEqual((entry["session"], entry["summary"], entry["class"], entry["rule"]),
                         ("s1", "fix typo", "A", "trivial-change"))
        self.assertEqual({r["id"] for r in entry["roles"]}, {"junior-developer", "qa-verifier"})
        junior = next(r for r in entry["roles"] if r["id"] == "junior-developer")
        self.assertEqual(sorted(junior), sorted(["id", "mode", "reason", "agent", "model", "effort", "estimate_tokens"]))
        self.assertEqual(junior["agent"], "oeo:junior-developer")
        self.assertEqual(entry["inputs"], {"type": "trivial", "touches": [], "signals": [], "files": 1, "lines": 2})
        self.assertGreater(entry["estimate_tokens"], 0)
        self.assertEqual(entry["budget_tokens"], 100000)
        datetime.fromisoformat(entry["ts"])
        self.run_cli(*argv)
        self.assertEqual(len(log.read_text(encoding="utf-8").splitlines()), 2)


class CostCommandTests(IsolatedTestCase):
    def setUp(self):
        super().setUp()
        self.oeo_dir = self.tmp / ".oeo"

    def write_jsonl(self, name, rows, garbage=False):
        self.oeo_dir.mkdir(exist_ok=True)
        lines = [json.dumps(r) for r in rows] + (["{not json", ""] if garbage else [])
        (self.oeo_dir / name).write_text("\n".join(lines) + "\n", encoding="utf-8")

    @staticmethod
    def use(agent, session="s1", inp=0, out=0, cache_read=0, cache_write=0):
        return {"session_id": session, "agent_type": agent, "input_tokens": inp, "output_tokens": out,
                "cache_read_tokens": cache_read, "cache_write_tokens": cache_write}

    @staticmethod
    def row(out, agent):
        return next(line for line in out.splitlines() if line.startswith(agent))

    def test_no_data_prints_the_no_finops_data_message(self):
        code, out, _ = self.run_cli("cost")
        self.assertIsNone(code)
        self.assertIn(f"No FinOps data in {self.oeo_dir}", out)
        self.write_jsonl("finops.jsonl", [self.use("oeo:qa-verifier", session="other", inp=5)])
        self.assertIn("No FinOps data", self.run_cli("cost", "--session", "s1")[1])  # filtered away

    def test_report_flags_over_estimate_unplanned_and_excludes_cache_reads(self):
        self.run_cli("route", "--type", "trivial", "--files", "1", "--lines", "1", "--log", "--session", "s1")
        plan = json.loads((self.oeo_dir / "activation-log.jsonl").read_text(encoding="utf-8"))
        junior_estimate = next(r for r in plan["roles"] if r["id"] == "junior-developer")["estimate_tokens"]
        self.write_jsonl("finops.jsonl", [
            self.use("oeo:junior-developer", inp=junior_estimate, out=1000, cache_read=900000),   # over estimate
            self.use("oeo:qa-verifier", inp=1000, out=500),                                      # within estimate
            self.use("oeo:security-engineer", inp=100),                                          # not in the plan
            self.use("oeo:senior-developer", session="s2", inp=999999),                          # other session
        ], garbage=True)
        code, out, _ = self.run_cli("cost", "--session", "s1")
        self.assertIsNone(code)
        self.assertIn("OVER ESTIMATE", self.row(out, "oeo:junior-developer"))
        self.assertNotIn("OVER ESTIMATE", self.row(out, "oeo:qa-verifier"))
        self.assertIn("unplanned", self.row(out, "oeo:security-engineer"))
        self.assertNotIn("oeo:senior-developer", out)
        total = junior_estimate + 1000 + 1000 + 500 + 100   # input + output + cache writes; cache reads excluded
        self.assertIn(f"Total subagent tokens (input+output+cache writes): {total:,}; "
                      f"planned {plan['estimate_tokens']:,}; class budget {plan['budget_tokens']:,}", out)
        self.assertNotIn("BUDGET EXCEEDED", out)
        self.assertIn("3 distinct agent types, 3 runs", out)

    def test_budget_exceeded_warning(self):
        self.write_jsonl("activation-log.jsonl", [{"session": "s1", "roles": [], "estimate_tokens": 10, "budget_tokens": 100}])
        self.write_jsonl("finops.jsonl", [self.use("oeo:qa-verifier", inp=400, out=100)])
        self.assertIn("BUDGET EXCEEDED", self.run_cli("cost", "--session", "s1")[1])

    def test_usage_without_any_plan_is_reported_without_flags(self):
        self.write_jsonl("finops.jsonl", [self.use("oeo:qa-verifier", inp=7, out=3), self.use("oeo:qa-verifier", inp=1)])
        _, out, _ = self.run_cli("cost")
        self.assertIn("Coordination: 1 distinct agent types, 2 runs", out)
        self.assertNotIn("unplanned", out)
        self.assertNotIn("OVER ESTIMATE", out)


class LicenseTests(IsolatedTestCase):
    @classmethod
    def setUpClass(cls):
        cls.policy = oeo.load_lock()["routing"]["licenses"]

    def test_verdicts_and_fail_closed_default(self):
        expected = {"MIT": "allowed", "Apache-2.0": "allowed", "MPL-2.0": "review", "LGPL-3.0-only": "review",
                    "GPL-3.0-only": "blocked", "AGPL-3.0-or-later": "blocked", "NOASSERTION": "blocked",
                    "Foo-1.0": "blocked", "": "blocked", None: "blocked",
                    # case-insensitive ids and SPDX expressions (OR = best option, AND = worst, WITH = base id)
                    "mit": "allowed", "MIT ": "allowed", "Apache-2.0 OR MIT": "allowed",
                    "GPL-3.0-only OR MIT": "allowed", "MIT AND GPL-3.0-only": "blocked",
                    "MIT AND MPL-2.0": "review", "Apache-2.0 WITH LLVM-exception": "allowed",
                    # nested expressions are judged by the worst license named (fail safe)
                    "(MIT OR GPL-3.0-only) AND MPL-2.0": "blocked"}
        for spdx, verdict in expected.items():
            with self.subTest(spdx=spdx):
                self.assertEqual(oeo.license_verdict(spdx, self.policy), verdict)

    def test_cli_exit_codes(self):
        cases = [(["MIT"], 0), (["MIT", "Apache-2.0"], 0), (["MPL-2.0"], 3), (["MIT", "MPL-2.0"], 3),
                 (["GPL-3.0-only"], 1), (["Foo-1.0"], 1), (["MPL-2.0", "GPL-3.0-only"], 1),
                 (["GPL-3.0-only", "MPL-2.0"], 1)]
        for spdx, expected in cases:
            with self.subTest(spdx=spdx):
                code, _, _ = self.run_cli("license", *spdx)
                self.assertEqual(code, expected)

    def test_cli_output_names_each_verdict(self):
        _, out, _ = self.run_cli("license", "MIT", "MPL-2.0", "GPL-3.0-only")
        self.assertIn("MIT: ALLOWED", out)
        self.assertIn("MPL-2.0: REVIEW (human decision required", out)
        self.assertIn("GPL-3.0-only: BLOCKED (incompatible with project policy Apache-2.0)", out)


class OtherCommandTests(IsolatedTestCase):
    def test_models_lists_every_role_for_the_chosen_profile(self):
        lock = oeo.load_lock()
        _, out, _ = self.run_cli("models")
        self.assertIn("profile=default provider=anthropic", out)
        for rid in lock["roles"]:
            self.assertIn(f" {rid} ", out)
        qa = next(line for line in out.splitlines() if " qa-verifier " in line)
        self.assertIn("claude-sonnet-5-5", qa)
        os.environ["OEO_MODEL_PROFILE"] = "economy"
        _, out, _ = self.run_cli("models")
        self.assertIn("profile=economy", out)
        self.assertIn("claude-haiku-5-5", next(line for line in out.splitlines() if " qa-verifier " in line))

    def test_validate_and_build_check_succeed_on_the_repository(self):
        code, out, _ = self.run_cli("validate")
        self.assertIsNone(code)
        self.assertTrue(out.startswith("OK: "))
        code, out, _ = self.run_cli("build", "--check")  # --check never writes
        self.assertIsNone(code)
        self.assertIn("build check OK", out)

    def test_script_entry_point_and_exit_codes(self):
        def run(*args):
            return subprocess.run([sys.executable, "-I", "-B", str(SCRIPTS / "oeo.py"), *args], text=True,
                                  capture_output=True, timeout=60, env=subprocess_env(CLAUDE_PROJECT_DIR=str(self.tmp)))
        self.assertEqual(run("license", "MIT").returncode, 0)
        self.assertEqual(run("license", "MPL-2.0").returncode, 3)
        self.assertEqual(run("license", "GPL-3.0-only").returncode, 1)
        ok = run("route", "--type", "trivial", "--files", "1", "--lines", "1")
        self.assertEqual(ok.returncode, 0)
        self.assertIn("Class A", ok.stdout)
        bad = run("route", "--type", "nonsense")
        self.assertEqual(bad.returncode, 1)
        self.assertIn("unknown type 'nonsense'", bad.stderr)
        self.assertEqual(list(self.tmp.iterdir()), [])


if __name__ == "__main__":
    unittest.main()
