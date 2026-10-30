"""Regression tests for defects found by the independent code review of v0.2.0."""
import copy
import json
import os
import unittest
from unittest import mock

from tests._common import ROOT, IsolatedTestCase, oeo


class ProjectRootTests(IsolatedTestCase):
    def test_walks_up_to_the_directory_holding_oeo_or_git(self):
        (self.tmp / ".git").mkdir()
        sub = self.tmp / "src" / "app"
        sub.mkdir(parents=True)
        with mock.patch.dict(os.environ):
            os.environ.pop("CLAUDE_PROJECT_DIR", None)
            self.assertEqual(oeo.project_dir(sub), self.tmp.resolve())
        self.assertEqual(oeo.project_dir(sub), self.tmp)  # the env var wins when set

    def test_log_refuses_to_follow_a_symlinked_file(self):
        (self.tmp / ".oeo").mkdir()
        victim = self.tmp / "victim"
        victim.write_text("", encoding="utf-8")
        (self.tmp / ".oeo" / "activation-log.jsonl").symlink_to(victim)
        code, _, _ = self.run_cli("route", "--type", "trivial", "--files", "1", "--lines", "1", "--log")
        self.assertIn("not logged", str(code))
        self.assertEqual(victim.read_text(encoding="utf-8"), "")


class CostLatestPlanTests(IsolatedTestCase):
    def test_retriage_in_a_session_counts_only_the_latest_plan(self):
        (self.tmp / ".oeo").mkdir()
        plans = [{"session": "s1", "class": "B", "estimate_tokens": 120000, "budget_tokens": 300000, "roles": []},
                 {"session": "s1", "class": "C", "estimate_tokens": 240000, "budget_tokens": 900000, "roles": []}]
        (self.tmp / ".oeo" / "activation-log.jsonl").write_text("\n".join(map(json.dumps, plans)) + "\n")
        (self.tmp / ".oeo" / "finops.jsonl").write_text(json.dumps(
            {"session_id": "s1", "agent_type": "oeo:qa-verifier", "input_tokens": 10, "output_tokens": 5}) + "\n")
        _, out, _ = self.run_cli("cost", "--session", "s1")
        self.assertIn("planned 240,000; class budget 900,000", out)


class GeneratedFilesIgnoreRouterProfileTests(IsolatedTestCase):
    def test_build_outputs_do_not_follow_oeo_model_profile(self):
        src = oeo.load_sources()
        default = oeo.build_outputs(copy.deepcopy(src))
        with mock.patch.dict(os.environ, {"OEO_MODEL_PROFILE": "economy"}):
            self.assertEqual(oeo.build_outputs(copy.deepcopy(src)), default)


class ClassificationValidationTests(IsolatedTestCase):
    def errors_after(self, mutate):
        src = copy.deepcopy(oeo.load_sources())
        mutate(src["routing"]["classification"])
        return oeo.validate_sources(src)

    def test_unknown_condition_type_and_missing_catch_all_are_reported(self):
        def typo(rules):
            rules[4]["when"]["files_gtt"] = rules[4]["when"].pop("files_gt")
        self.assertTrue(any("unknown condition 'files_gtt'" in e for e in self.errors_after(typo)))
        self.assertTrue(any("unknown type 'incidnt'" in e for e in self.errors_after(
            lambda r: r[1]["when"]["types_any"].append("incidnt"))))
        self.assertTrue(any("catch-all" in e for e in self.errors_after(lambda r: r.pop())))


class HookConfigTests(unittest.TestCase):
    def test_every_hook_command_points_at_an_existing_script(self):
        config = json.loads((ROOT / "hooks" / "hooks.json").read_text(encoding="utf-8"))
        commands = [h["command"] for groups in config["hooks"].values() for g in groups for h in g["hooks"]]
        self.assertTrue(commands)
        for command in commands:
            script = command.split('"${CLAUDE_PLUGIN_ROOT}/', 1)[1].split('"', 1)[0]
            with self.subTest(script=script):
                self.assertTrue((ROOT / script).is_file(), script)


if __name__ == "__main__":
    unittest.main()


class RatingTwoRegressionTests(IsolatedTestCase):
    """Defects found by the second independent rating."""

    def test_retriage_that_drops_facts_is_flagged_and_logged(self):
        base = ("route", "--engagement", "auth-fix", "--log", "--files", "2", "--lines", "30")
        self.run_cli(*base, "--type", "bugfix", "--touches", "auth,database")
        _, _, err = self.run_cli(*base, "--type", "bugfix", "--touches", "auth")
        self.assertIn("re-triage dropped database", err)
        last = json.loads((self.tmp / ".oeo" / "activation-log.jsonl").read_text().splitlines()[-1])
        self.assertEqual(last["dropped_facts"], ["database"])

    def test_mixed_case_template_slots_are_must_fix_but_links_are_not(self):
        import checks  # noqa: PLC0415
        self.assertTrue(any(f["severity"] == "must-fix" for f in checks.copy_lint("See [repository URL].")))
        self.assertTrue(any(f["severity"] == "must-fix" for f in checks.copy_lint("File it at [Issues link].")))
        self.assertEqual(checks.copy_lint("Read the [docs](https://example.org); the [API] is stable."), [])
