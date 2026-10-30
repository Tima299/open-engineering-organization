"""Verification, brief and release checks (scripts/checks.py) with their CLI commands, `oeo cost --check`
exit codes, and the trace-based parts of the agentic eval harness (evals/agentic.py).

Nothing here writes inside the repository: every project and git repo lives under the per-test temp dir.
A test marked expectedFailure documents a real bug (see the "# Regression (fixed):" comment above it); the day the code
is fixed, the test starts to "unexpectedly succeed" and the marker should be removed.
"""
import importlib.util
import json
import os
import subprocess
import sys
import unittest

from ._common import ROOT, IsolatedTestCase

import checks  # noqa: E402  (scripts/ is put on sys.path by ._common)


def _load_agentic():
    """evals/ is not a package; load the harness by path (it adds scripts/ to sys.path itself)."""
    spec = importlib.util.spec_from_file_location("oeo_evals_agentic", ROOT / "evals" / "agentic.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


agentic = _load_agentic()


def gate_table(rows, header=("gate", "method", "result", "evidence")):
    lines = ["| " + " | ".join(header) + " |", "|" + "|".join("---" for _ in header) + "|"]
    lines += ["| " + " | ".join(row) + " |" for row in rows]
    return "\n".join(lines) + "\n"


def jsonl(rows):
    return "".join(json.dumps(r) + "\n" for r in rows)


class ProjectCase(IsolatedTestCase):
    """A project root (the temp dir) with helpers to write files under it."""

    def put(self, rel, text):
        path = self.tmp / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8")
        return path


# --------------------------------------------------------------------------- verification_check
OK_GATES = [
    ("tests-pass", "pytest", "PASS", "42 passed"),
    ("`lint`", "ruff", "pass", "clean"),
    ("regression-test", "n/a", "N/A: docs only", ""),
]


class VerificationCheckTests(unittest.TestCase):
    @staticmethod
    def check(rows, required=(), **kw):
        return checks.verification_check(gate_table(rows, **kw), required)

    def test_ok_table_has_no_problems(self):
        self.assertEqual(self.check(OK_GATES), [])
        self.assertEqual(self.check(OK_GATES, required=["tests-pass", "lint", "regression-test"]), [])  # backticks stripped
        # a table without an evidence column cannot demand evidence; column order is free
        self.assertEqual(checks.verification_check(gate_table([("g", "PASS")], header=("gate", "result"))), [])
        self.assertEqual(self.check([("PASS", "ok", "g")], header=("verdict", "evidence", "gate")), [])

    def test_pass_without_evidence_is_reported(self):
        self.assertEqual(self.check([("tests-pass", "pytest", "PASS", "")]), ["tests-pass: PASS without evidence"])
        self.assertEqual(self.check([("a", "x", "PASS", ""), ("b", "x", "PASS", "log"), ("c", "x", "pass", "")]),
                         ["a: PASS without evidence", "c: PASS without evidence"])

    def test_na_requires_a_reason(self):
        for result in ("N/A", "n/a", "N/A:", "N/A: no"):
            with self.subTest(result=result):
                self.assertEqual(self.check([("g", "x", result, "")]), ["g: N/A needs a reason"])
        for result in ("N/A: docs only", "N/A (docs only)", "N/A: not applicable here"):
            with self.subTest(result=result):
                self.assertEqual(self.check([("g", "x", result, "")]), [])

    # Regression (fixed): checks.py:301 the reason pattern `N/A\s*:?\s*\S{3,}` needs the FIRST word after the colon to have 3+ characters, so
    # "N/A: no structural change" (the documented example), "N/A: ui only" and "N/A - docs only" are rejected as "needs a reason".
    def test_na_reason_starting_with_a_short_word_is_accepted(self):
        for result in ("N/A: no structural change", "N/A: ui only", "N/A - docs only"):
            with self.subTest(result=result):
                self.assertEqual(self.check([("g", "x", result, "")]), [])

    # Regression (fixed): checks.py:303 after the N/A (or PASS) branch passes, `"FAIL" in up` is tested on the whole result text, so a valid
    # reason that merely contains "fail" ("failover", "fail-safe") is reported as a FAIL.
    def test_na_reason_containing_the_letters_fail_is_not_a_failure(self):
        self.assertEqual(self.check([("g", "x", "N/A: docs only, failover untouched", "")]), [])

    def test_fail_and_not_run_are_reported_with_the_result_text(self):
        problems = self.check([("tests-pass", "pytest", "FAIL: 2 broken", "log"), ("lint", "ruff", "NOT RUN", ""),
                               ("sec", "scan", "not run yet", ""), ("ok", "x", "PASS", "fine")])
        self.assertEqual(problems, ["tests-pass: FAIL: 2 broken", "lint: NOT RUN", "sec: not run yet"])

    def test_unknown_or_empty_result_word_is_reported(self):
        for result in ("MAYBE", "green", ""):
            with self.subTest(result=result):
                self.assertEqual(self.check([("g", "x", result, "log")]),
                                 [f"g: result must be PASS, FAIL or N/A: <reason>, got '{result}'"])

    def test_missing_required_gate_is_reported_after_row_problems(self):
        problems = self.check([("tests-pass", "pytest", "PASS", "42 passed"), ("lint", "ruff", "FAIL", "")],
                              required=["tests-pass", "license-gate", "security-review"])
        self.assertEqual(problems, ["lint: FAIL", "license-gate: required gate missing", "security-review: required gate missing"])
        self.assertEqual(self.check(OK_GATES, required=("tests-pass",)), [])

    def test_no_gate_table_is_one_problem_plus_the_missing_required_gates(self):
        no_table = "no gate table found (| gate | method | result | evidence |)"
        for text in ("", "Everything passed, trust me.\n", gate_table([("a", "b")], header=("gate", "method")),
                     gate_table([("T1", "PASS")], header=("task", "status"))):
            with self.subTest(text=text[:30]):
                self.assertEqual(checks.verification_check(text), [no_table])
        self.assertEqual(checks.verification_check("", ["tests-pass"]), [no_table, "tests-pass: required gate missing"])


class VerificationCheckCliTests(ProjectCase):
    def setUp(self):
        super().setUp()
        self.gates = ["tests-pass", "license-gate"]
        self.put(".oeo/activation-log.jsonl", jsonl([{"engagement": "eng1", "gates": self.gates, "class": "B"}]))

    def verify(self, rows, *argv, rel=".oeo/eng1/verification.md"):
        path = self.put(rel, gate_table(rows))
        code, out, _ = self.run_cli("verification-check", str(path), *argv)
        return code, out, path

    def test_required_gates_are_read_from_the_engagements_logged_plan(self):
        code, out, path = self.verify([("tests-pass", "pytest", "PASS", "42 passed")])
        self.assertEqual(code, 1)
        self.assertIn(f"{path}: license-gate: required gate missing", out)
        self.assertNotIn("tests-pass: required", out)
        self.assertIn("verification: FAIL (1 problem(s))", out)
        code, out, _ = self.verify([("tests-pass", "pytest", "PASS", "42 passed"), ("license-gate", "oeo license", "PASS", "MIT")])
        self.assertEqual((code, out.strip()), (0, "verification: OK"))

    def test_only_the_latest_plan_of_that_engagement_counts(self):
        self.put(".oeo/activation-log.jsonl", jsonl([
            {"engagement": "eng1", "gates": ["tests-pass", "license-gate", "security-review"]},
            {"engagement": "eng2", "gates": ["other-gate"]},
            {"engagement": "eng1", "gates": ["tests-pass"]},          # re-triage: this plan supersedes the first
            {"engagement": "eng3", "gates": ["later-gate"]},
        ]))
        code, out, _ = self.verify([("tests-pass", "pytest", "PASS", "42 passed")])
        self.assertEqual((code, out.strip()), (0, "verification: OK"))

    def test_explicit_gates_override_the_logged_ones(self):
        rows = [("tests-pass", "pytest", "PASS", "42 passed")]
        code, out, _ = self.verify(rows, "--gates", "tests-pass")
        self.assertEqual((code, out.strip()), (0, "verification: OK"))      # license-gate (logged) is no longer required
        code, out, path = self.verify(rows, "--gates", "tests-pass,security-review")
        self.assertEqual(code, 1)
        self.assertIn(f"{path}: security-review: required gate missing", out)
        self.assertNotIn("license-gate", out)

    # Regression (fixed): oeo.py:828 `args.gates.split(",")` does not strip, so `--gates "tests-pass, license-gate"` requires a gate named
    # " license-gate" and reports it missing even though the table has it (cmd_route's own comma lists are stripped).
    def test_explicit_gates_may_have_spaces_after_the_commas(self):
        code, out, _ = self.verify([("tests-pass", "pytest", "PASS", "42 passed"), ("license-gate", "x", "PASS", "MIT")],
                                   "--gates", "tests-pass, license-gate")
        self.assertEqual((code, out.strip()), (0, "verification: OK"))

    def test_no_required_gates_when_the_file_is_not_in_a_logged_engagement_folder(self):
        rows = [("tests-pass", "pytest", "PASS", "42 passed")]
        self.put("activation-log.jsonl", jsonl([{"engagement": "eng1", "gates": self.gates}]))
        code, out, _ = self.verify(rows, rel="elsewhere/verification.md")   # parent folder name is not an engagement
        self.assertEqual((code, out.strip()), (0, "verification: OK"))
        (self.tmp / ".oeo" / "activation-log.jsonl").unlink()                # no log at all
        code, out, _ = self.verify(rows)
        self.assertEqual((code, out.strip()), (0, "verification: OK"))

    def test_exit_code_is_1_with_one_line_per_problem(self):
        code, out, path = self.verify([("tests-pass", "pytest", "FAIL: 2 broken", "log"), ("license-gate", "x", "PASS", ""),
                                       ("extra", "x", "MAYBE", "")])
        self.assertEqual(code, 1)
        self.assertEqual(out.splitlines(), [f"{path}: tests-pass: FAIL: 2 broken",
                                            f"{path}: license-gate: PASS without evidence",
                                            f"{path}: extra: result must be PASS, FAIL or N/A: <reason>, got 'MAYBE'",
                                            "verification: FAIL (3 problem(s))"])


# --------------------------------------------------------------------------- brief_check
BRIEF_PARTS = {
    "users": "## Users\nFACT: small shop owners ship weekly (five interviews).\n",
    "outcome": "## Outcome\nOrders are exported in one click.\n",
    "metric": "## Metric\nHYPOTHESIS: export takes under 5 minutes.\n",
    "non-goal": "## Non-goals\nInvoicing is out of scope.\n",
    "acceptance criteria": "## Acceptance criteria\n1. Export succeeds for 1,000 orders.\n2. A failed export shows an error message.\n",
}


def brief(omit=(), replace=None, extra=""):
    parts = {**BRIEF_PARTS, **(replace or {})}
    return "# Brief: order export\n\n" + "\n".join(v for k, v in parts.items() if k not in omit) + extra


class BriefCheckTests(ProjectCase):
    def test_complete_brief_passes(self):
        self.assertEqual(set(checks.BRIEF_SECTIONS), set(BRIEF_PARTS))      # a new required section needs a part here
        self.assertEqual(checks.brief_check(brief()), [])
        self.assertEqual(checks.brief_check(brief().upper()), [])           # section names are matched case-insensitively
        self.assertEqual(checks.brief_check(brief().lower().replace("fact", "FACT")), [])

    def test_each_missing_section_is_reported(self):
        for section in checks.BRIEF_SECTIONS:
            with self.subTest(section=section):
                problems = checks.brief_check(brief(omit=[section]))
                expected = [f"missing section: {section}"]
                if section == "acceptance criteria":     # no heading means no criteria list either
                    expected.append("no numbered or bulleted acceptance criteria")
                self.assertEqual(problems, expected)
        empty = checks.brief_check("# empty\n")      # every section, plus the labels and the criteria list
        self.assertEqual(len(empty), len(checks.BRIEF_SECTIONS) + 2)

    def test_tbd_is_rejected_as_a_word(self):
        for extra in ("\nPricing: TBD\n", "\n(TBD)\n", "\n- TBD\n"):
            with self.subTest(extra=extra):
                problems = checks.brief_check(brief(extra=extra))
                self.assertEqual(problems, ["contains TBD: move unknowns to assumptions / open questions"])
        self.assertEqual(checks.brief_check(brief(extra="\nThe TBDs are listed elsewhere.\n")), [])   # whole word only

    def test_missing_evidence_labels_are_reported_and_any_one_label_satisfies(self):
        bare = brief().replace("FACT: ", "").replace("HYPOTHESIS: ", "")
        self.assertEqual(checks.brief_check(bare), ["no evidence labels (FACT / HYPOTHESIS / UNKNOWN / OPINION)"])
        for label in ("FACT", "HYPOTHESIS", "UNKNOWN", "OPINION"):
            with self.subTest(label=label):
                self.assertEqual(checks.brief_check(bare + f"\n{label}: something.\n"), [])

    def test_criteria_must_be_a_numbered_or_bulleted_list(self):
        problem = ["no numbered or bulleted acceptance criteria"]
        prose = {"acceptance criteria": "## Acceptance criteria\nIt should feel fast and look good.\n"}
        self.assertEqual(checks.brief_check(brief(replace=prose)), problem)
        # bullets in an earlier section do not stand in for the criteria list
        early = {"users": "## Users\nFACT: owners.\n- bullet one\n- bullet two\n"}
        self.assertEqual(checks.brief_check(brief(replace={**prose, **early})), problem)
        for first in ("1. Export works", "2) Export works", "- Export works", "* Export works", "  - Export works"):
            with self.subTest(first=first):
                crit = {"acceptance criteria": f"## Acceptance criteria\n{first}\n"}
                self.assertEqual(checks.brief_check(brief(replace=crit)), [])

    # Regression (fixed): checks.py:324 `re.split(r"acceptance criteria", ...)[-1]` takes the text after the LAST mention of the phrase, so a
    # later sentence such as "See the acceptance criteria above." hides a perfectly good criteria list (false "no numbered or
    # bulleted acceptance criteria"); the text after the heading, not after the last mention, should be checked.
    def test_a_later_mention_of_acceptance_criteria_does_not_hide_the_list(self):
        self.assertEqual(checks.brief_check(brief(extra="\n## Open questions\nSee the acceptance criteria above.\n")), [])

    def test_cli_exit_codes_and_problem_lines(self):
        good = self.put("good.md", brief())
        code, out, _ = self.run_cli("brief-check", str(good))
        self.assertEqual((code, out.strip()), (0, "brief: OK"))
        bad = self.put("bad.md", brief(omit=["users", "non-goal"], extra="\nTBD\n"))
        code, out, _ = self.run_cli("brief-check", str(bad))
        self.assertEqual(code, 1)
        self.assertEqual(out.splitlines(), [f"{bad}: missing section: users", f"{bad}: missing section: non-goal",
                                            f"{bad}: contains TBD: move unknowns to assumptions / open questions",
                                            "brief: FAIL (3 problem(s))"])


# --------------------------------------------------------------------------- release_check
CHANGELOG = """# Changelog

## [Unreleased]

## [1.2.0] - 2026-10-30

### Added
- Release check.

## [1.1.0] - 2026-09-01

### Fixed
- A bug.
"""
SOURCES_120 = [("plugin.json", '{"name": "oeo", "version": "1.2.0"}'), ("README.md", "Current release: 1.2.0\n")]


class ReleaseCheckTests(ProjectCase):
    def test_valid_changelog_and_sources_pass(self):
        self.assertEqual(checks.release_check(CHANGELOG, "1.2.0", SOURCES_120), [])
        self.assertEqual(checks.release_check(CHANGELOG, "1.1.0"), [])                  # an older dated section is fine too
        rc = CHANGELOG.replace("## [1.2.0] - 2026-10-30", "## [1.3.0-rc.1] - 2026-11-02")
        self.assertEqual(checks.release_check(rc, "1.3.0-rc.1", [("plugin.json", "1.3.0-rc.1")]), [])   # pre-release, escaped dots

    def test_non_semver_versions_are_rejected(self):
        for version in ("1.2", "v1.2.0", "1.2.0.1", "1.2.x", "latest", "1.2.0-", ""):
            with self.subTest(version=version):
                self.assertEqual(checks.release_check(CHANGELOG, version)[0], f"'{version}' is not a SemVer version")

    def test_a_missing_or_undated_version_section_is_reported(self):
        missing = "CHANGELOG has no '## [{}] - YYYY-MM-DD' section"
        self.assertEqual(checks.release_check(CHANGELOG, "1.3.0"), [missing.format("1.3.0")])
        for variant in ("## [1.2.0]", "## [1.2.0] - 30-10-2026", "[1.2.0] - 2026-10-30", "### [1.2.0] - 2026-10-30"):
            with self.subTest(heading=variant):
                self.assertEqual(checks.release_check(CHANGELOG.replace("## [1.2.0] - 2026-10-30", variant), "1.2.0"),
                                 [missing.format("1.2.0")])

    def test_a_version_section_needs_its_own_keep_a_changelog_subsection(self):
        problem = ["the 1.3.0 section has no Keep a Changelog subsection"]
        newer = "## [1.3.0] - 2026-11-01\n\n{}\n\n## [1.2.0] - 2026-10-30"
        for body in ("- a loose bullet", "### Notes\n- not a Keep a Changelog heading", ""):
            with self.subTest(body=body):
                text = CHANGELOG.replace("## [1.2.0] - 2026-10-30", newer.format(body))
                self.assertEqual(checks.release_check(text, "1.3.0"), problem)   # the older sections' headings do not count
        for heading in ("Added", "Changed", "Deprecated", "Removed", "Fixed", "Security"):
            with self.subTest(heading=heading):
                text = CHANGELOG.replace("## [1.2.0] - 2026-10-30", newer.format(f"### {heading}\n- x"))
                self.assertEqual(checks.release_check(text, "1.3.0"), [])
        last = "# Changelog\n\n## [Unreleased]\n\n## [1.3.0] - 2026-11-01\n### Fixed\n- x"     # last section, no trailing newline
        self.assertEqual(checks.release_check(last, "1.3.0"), [])

    def test_a_lost_unreleased_section_is_reported(self):
        lost = CHANGELOG.replace("## [Unreleased]\n\n", "")
        self.assertEqual(checks.release_check(lost, "1.2.0"), ["CHANGELOG lost its '## [Unreleased]' section"])
        self.assertEqual(checks.release_check(lost.replace("## [1.2.0]", "## Unreleased\n\n## [1.2.0]"), "1.2.0"),
                         ["CHANGELOG lost its '## [Unreleased]' section"])

    def test_a_source_without_the_version_is_reported_by_name(self):
        sources = [("plugin.json", '{"version": "1.1.0"}'), ("README.md", "Release 1.2.0"), ("marketplace.json", "")]
        self.assertEqual(checks.release_check(CHANGELOG, "1.2.0", sources),
                         ["plugin.json does not contain version 1.2.0", "marketplace.json does not contain version 1.2.0"])

    # Regression (fixed): checks.py:349 `version not in text` is a plain substring test, so a source still on "21.2.0" or "1.2.05" counts as
    # containing "1.2.0"; the version has to match as a whole token (docstring: "every version source equal to `version`").
    def test_a_source_with_a_longer_version_that_embeds_the_release_does_not_pass(self):
        for text in ('{"version": "21.2.0"}', '{"version": "1.2.05"}'):
            with self.subTest(text=text):
                self.assertEqual(checks.release_check(CHANGELOG, "1.2.0", [("plugin.json", text)]),
                                 ["plugin.json does not contain version 1.2.0"])

    # Regression (fixed): checks.py:330 SEMVER `\d+` accepts leading zeros ("01.2.0", "1.02.0"), which SemVer 2.0.0 section 2 forbids
    # ("numeric identifiers MUST NOT include leading zeroes").
    def test_leading_zeros_are_not_semver(self):
        for version in ("01.2.0", "1.02.0", "1.2.00"):
            with self.subTest(version=version):
                text = CHANGELOG.replace("## [1.2.0]", f"## [{version}]")
                self.assertIn(f"'{version}' is not a SemVer version", checks.release_check(text, version))

    def test_cli_with_source_files(self):
        changelog = self.put("CHANGELOG.md", CHANGELOG)
        plugin = self.put("plugin.json", SOURCES_120[0][1])
        readme = self.put("README.md", SOURCES_120[1][1])
        base = ("release-check", "--changelog", str(changelog), "--source", str(plugin), "--source", str(readme))
        code, out, _ = self.run_cli(*base, "--version", "1.2.0")
        self.assertEqual((code, out.strip()), (0, "release: OK"))
        code, out, _ = self.run_cli(*base, "--version", "1.3.0")
        self.assertEqual(code, 1)
        self.assertEqual(out.splitlines(), ["CHANGELOG has no '## [1.3.0] - YYYY-MM-DD' section",
                                            f"{plugin} does not contain version 1.3.0",
                                            f"{readme} does not contain version 1.3.0",
                                            "release: FAIL (3 problem(s))"])
        code, out, _ = self.run_cli("release-check", "--changelog", str(changelog), "--version", "v1.2.0")   # no --source
        self.assertEqual(code, 1)
        self.assertEqual(out.splitlines()[0], "'v1.2.0' is not a SemVer version")


# --------------------------------------------------------------------------- cost --check
class CostCheckTests(ProjectCase):
    def seed(self, used, budget=1000, plans=None):
        """One plan (budget 1000) and subagent usage totalling `used` tokens (cache reads are huge and must not count)."""
        plans = plans or [{"session": "s1", "engagement": "e1", "estimate_tokens": 500, "budget_tokens": budget, "roles": []}]
        self.put(".oeo/activation-log.jsonl", jsonl(plans))
        self.put(".oeo/finops.jsonl", jsonl([{"session_id": "s1", "agent_type": "oeo:qa-verifier", "input_tokens": used - 30,
                                              "output_tokens": 20, "cache_write_tokens": 10, "cache_read_tokens": 10**6}]))

    def test_50_percent_of_the_budget_exits_0(self):
        self.seed(500)
        code, out, _ = self.run_cli("cost", "--check")
        self.assertIsNone(code)
        self.assertIn("cost check: 50% of budget: OK", out)
        self.assertIn("Total subagent tokens (input+output+cache writes): 500;", out)    # cache reads excluded
        self.assertNotIn("BUDGET EXCEEDED", out)

    def test_85_percent_of_the_budget_exits_1(self):
        self.seed(850)
        code, out, _ = self.run_cli("cost", "--check")
        self.assertEqual(code, 1)
        self.assertIn("cost check: 85% of budget: critical-path work only; tell the user", out)
        self.assertNotIn("BUDGET EXCEEDED", out)

    def test_120_percent_of_the_budget_exits_2_and_pauses(self):
        self.seed(1200)
        code, out, _ = self.run_cli("cost", "--check")
        self.assertEqual(code, 2)
        self.assertIn("cost check: 120% of budget: PAUSE and ask the user before more subagent work", out)
        self.assertIn("BUDGET EXCEEDED", out)

    def test_threshold_boundaries_are_80_and_100_percent_inclusive(self):
        for used, expected in ((799, None), (800, 1), (999, 1), (1000, 2)):
            with self.subTest(used=used):
                self.seed(used)
                self.assertEqual(self.run_cli("cost", "--check")[0], expected)

    def test_without_check_the_report_never_fails_and_the_latest_plan_sets_the_budget(self):
        self.seed(1200)
        code, out, _ = self.run_cli("cost")                   # report only: no exit code, no cost check line
        self.assertIsNone(code)
        self.assertNotIn("cost check:", out)
        first = {"session": "s1", "engagement": "e1", "estimate_tokens": 500, "budget_tokens": 1000, "roles": []}
        retriage = {**first, "estimate_tokens": 4000, "budget_tokens": 10000}
        self.seed(850, plans=[first, retriage])               # the re-triage of e1 supersedes the 1,000 budget
        code, out, _ = self.run_cli("cost", "--check")
        self.assertIsNone(code)
        self.assertIn("cost check: 8% of budget: OK", out)    # 850 / 10,000 -> 8.5% rounds to even
        self.seed(850, plans=[retriage, first])               # ...and the LAST entry wins, whatever its size
        self.assertEqual(self.run_cli("cost", "--check")[0], 1)


# --------------------------------------------------------------------------- evals/agentic.py: parse_trace
def tool_use(name, **tool_input):
    return {"type": "tool_use", "id": "toolu_" + name.lower(), "name": name, "input": tool_input}


def assistant_line(*blocks, parent=None):
    return json.dumps({"type": "assistant", "parent_tool_use_id": parent, "message": {"role": "assistant", "content": list(blocks)}})


ROUTE_CMD = 'python3 "${CLAUDE_PLUGIN_ROOT}/scripts/oeo.py" route --type feature --files 3 --lines 80 --log'


class ParseTraceTests(unittest.TestCase):
    STREAM = "\n".join([
        json.dumps({"type": "system", "subtype": "init", "session_id": "abc"}),
        assistant_line({"type": "text", "text": "Triage first."}, tool_use("Bash", command=ROUTE_CMD, description="triage")),
        "this line is garbage",
        "{broken json",
        "",
        "   ",
        "[1, 2, 3]",
        json.dumps({"type": "user", "message": {"content": [{"type": "tool_result", "content": "ok"}]}}),
        assistant_line(tool_use("Skill", skill="oeo:deliver")),
        assistant_line(tool_use("Agent", subagent_type="oeo:qa-verifier", prompt="verify")),
        assistant_line(tool_use("Edit", file_path="/work/app.py", old_string="a", new_string="b")),
        assistant_line(tool_use("Bash", command="python3 -m unittest"), parent="toolu_agent"),
        json.dumps({"type": "result", "subtype": "success", "is_error": False, "result": "All gates PASS.",
                    "total_cost_usd": 0.42, "num_turns": 6}),
    ])

    def test_result_event_and_compact_tool_trace(self):
        result, trace = agentic.parse_trace(self.STREAM)
        self.assertEqual((result["result"], result["total_cost_usd"], result["num_turns"], result["is_error"]),
                         ("All gates PASS.", 0.42, 6, False))
        blank = {"tool": None, "main": True, "agent": None, "skill": None, "cmd": None, "file": None}
        self.assertEqual(trace, [
            {**blank, "tool": "Bash", "cmd": ROUTE_CMD},
            {**blank, "tool": "Skill", "skill": "oeo:deliver"},
            {**blank, "tool": "Agent", "agent": "oeo:qa-verifier"},
            {**blank, "tool": "Edit", "file": "/work/app.py"},
            {**blank, "tool": "Bash", "cmd": "python3 -m unittest", "main": False},    # parent_tool_use_id set: a subagent
        ])

    def test_the_last_result_event_wins_and_a_stream_without_one_gives_an_empty_result(self):
        two = "\n".join([json.dumps({"type": "result", "result": "first"}), assistant_line(tool_use("Read", file_path="/a")),
                         json.dumps({"type": "result", "result": "second"})])
        self.assertEqual(agentic.parse_trace(two)[0], {"type": "result", "result": "second"})
        result, trace = agentic.parse_trace(assistant_line(tool_use("Read", file_path="/a")))
        self.assertEqual((result, [t["tool"] for t in trace]), ({}, ["Read"]))
        self.assertEqual(agentic.parse_trace(""), ({}, []))
        self.assertEqual(agentic.parse_trace("garbage\n{nope\n"), ({}, []))

    def test_commands_are_cut_to_200_characters_and_only_bash_has_one(self):
        stream = "\n".join([assistant_line(tool_use("Bash", command="echo " + "x" * 300)),
                            assistant_line(tool_use("Grep", command="not a shell command", pattern="p")),
                            assistant_line(tool_use("Write", file_path="/w/notes.md", content="..."))])
        _, trace = agentic.parse_trace(stream)
        self.assertEqual(len(trace[0]["cmd"]), 200)
        self.assertTrue(trace[0]["cmd"].startswith("echo xxx"))
        self.assertEqual([t["cmd"] for t in trace[1:]], [None, None])
        self.assertEqual(trace[2]["file"], "/w/notes.md")

    def test_odd_assistant_events_are_skipped_without_crashing(self):
        stream = "\n".join([
            json.dumps({"type": "assistant"}),
            json.dumps({"type": "assistant", "message": None}),
            json.dumps({"type": "assistant", "message": {"content": "plain text, not blocks"}}),
            json.dumps({"type": "assistant", "message": {"content": ["text", None, 3, {"type": "text", "text": "hi"}]}}),
            json.dumps({"type": "assistant", "message": {"content": [{"type": "tool_use", "name": "Edit", "input": None}]}}),
        ])
        _, trace = agentic.parse_trace(stream)
        self.assertEqual(trace, [{"tool": "Edit", "main": True, "agent": None, "skill": None, "cmd": None, "file": None}])


# --------------------------------------------------------------------------- evals/agentic.py: score (trace-based checks)
def call(tool, main=True, agent=None, skill=None, cmd=None, file=None):
    return {"tool": tool, "main": main, "agent": agent, "skill": skill, "cmd": cmd, "file": file}


def edit(file="/work/app.py", main=True, tool="Edit"):
    return call(tool, main=main, file=file)


def qa(main=True, tool="Agent", agent="oeo:qa-verifier"):
    return call(tool, main=main, agent=agent)


class AgenticScoreTests(IsolatedTestCase):
    def setUp(self):
        super().setUp()
        os.environ.update(PYTHONDONTWRITEBYTECODE="1", GIT_CONFIG_GLOBAL=os.devnull, GIT_CONFIG_NOSYSTEM="1")
        self.work = self.tmp / "repo"
        self.work.mkdir()
        (self.work / "app.py").write_text("print('hello')\n", encoding="utf-8")
        for argv in (["init", "-q"], ["add", "-A"], ["-c", "user.name=test", "-c", "user.email=test@example.invalid",
                                                    "-c", "commit.gpgsign=false", "commit", "-qm", "base"]):
            subprocess.run(["git", *argv], cwd=self.work, check=True, capture_output=True)

    def score(self, auto, trace=(), final="", arm="oeo"):
        """{check name: result dict} for the scenario `auto` block."""
        return {r["check"]: r for r in agentic.score(auto, self.work, arm, final, list(trace))}

    def passed(self, auto, trace=(), final="", arm="oeo"):
        return {name: r["pass"] for name, r in self.score(auto, trace, final, arm).items()}

    def test_skill_used_matches_skills_and_subagent_types_by_substring_in_the_oeo_arm_only(self):
        trace = [call("Skill", skill="oeo:deliver"), call("Agent", agent="oeo:qa-verifier"), call("Read", file="/w/a")]
        auto = {"skill_used": ["deliver", "oeo:verify", "qa-verifier"]}
        self.assertEqual(self.passed(auto, trace), {"skill_used deliver": True, "skill_used oeo:verify": False,
                                                    "skill_used qa-verifier": True})
        self.assertEqual(self.score(auto, trace)["skill_used oeo:verify"]["detail"], "['oeo:deliver', 'oeo:qa-verifier']")
        self.assertEqual(self.passed(auto, [], arm="oeo"), {f"skill_used {n}": False for n in auto["skill_used"]})
        self.assertEqual(self.passed(auto, trace, arm="baseline"), {})      # the baseline arm has no OEO skills to check

    def test_oeo_command_used_needs_the_subcommand_right_after_oeo_py(self):
        trace = [call("Bash", cmd=ROUTE_CMD), call("Bash", cmd="python3 scripts/oeo.py cost --check"),
                 call("Bash", cmd="python3 scripts/other.py validate"), call("Bash", cmd="pytest oeo.py_notes validate"),
                 call("Read", file="/w/scripts/oeo.py")]
        auto = {"oeo_command_used": ["route", "cost", "validate", "status"]}
        self.assertEqual(self.passed(auto, trace), {"oeo_command_used route": True, "oeo_command_used cost": True,
                                                    "oeo_command_used validate": False, "oeo_command_used status": False})
        self.assertEqual(self.passed({"oeo_command_used": ["route"]}, [], arm="oeo"), {"oeo_command_used route": False})
        self.assertEqual(self.passed(auto, trace, arm="baseline"), {})

    def test_reverify_passes_when_qa_ran_after_the_last_main_edit_and_fails_otherwise(self):
        auto, name = {"reverify_after_edit": True}, "reverified_after_last_main_edit"
        cases = [
            ("edit then QA", [edit(), qa()], True),
            ("edit, QA, edit again", [edit(), qa(), edit("/work/b.py")], False),
            ("QA, edit, QA", [qa(), edit(), qa()], True),
            ("edit and no QA at all", [edit()], False),
            ("no edits and no QA", [call("Read", file="/work/app.py")], True),
            ("QA without any edit", [qa()], True),
            ("empty trace", [], True),
        ]
        for label, trace, expected in cases:
            with self.subTest(label):
                self.assertEqual(self.passed(auto, trace), {name: expected})
        self.assertIn("last main-session edit #2, last qa-verifier call #1", self.score(auto, cases[1][1])[name]["detail"])
        self.assertEqual(self.passed(auto, cases[3][1], arm="baseline"), {})      # OEO arm only
        self.assertEqual(self.passed({}, cases[3][1]), {})                          # not requested by the scenario

    def test_reverify_only_counts_main_session_code_edits_and_main_session_qa(self):
        auto, name = {"reverify_after_edit": True}, "reverified_after_last_main_edit"
        cases = [
            ("write counts as an edit", [edit(tool="Write")], False),
            ("multiedit counts as an edit", [edit(tool="MultiEdit")], False),
            ("a subagent's edit is not a main-session edit", [edit(main=False)], True),
            ("edits under .oeo/ are notes, not code", [edit("/work/.oeo/e1/plan.md")], True),
            ("Task is the same as Agent", [edit(), qa(tool="Task")], True),
            ("a QA call made by a subagent does not re-verify", [edit(), qa(main=False)], False),
            ("another agent is not the verifier", [edit(), qa(agent="oeo:architect")], False),
            ("Bash is not a verifier", [edit(), call("Bash", cmd="python3 -m unittest")], False),
        ]
        for label, trace, expected in cases:
            with self.subTest(label):
                self.assertEqual(self.passed(auto, trace), {name: expected})

    def test_final_contains_is_case_insensitive_and_applies_to_both_arms(self):
        auto = {"final_contains": ["all gates pass", "Rollback", "missing phrase"]}
        final = "ALL GATES PASS. The rollback plan is in notes."
        expected = {"final_contains 'all gates pass'": True, "final_contains 'Rollback'": True,
                    "final_contains 'missing phrase'": False}
        for arm in ("oeo", "baseline"):
            with self.subTest(arm=arm):
                self.assertEqual(self.passed(auto, final=final, arm=arm), expected)
        self.assertEqual(self.passed({"final_contains": ["x"]}), {"final_contains 'x'": False})   # default final is empty

    def test_no_git_tags_fails_once_the_run_has_tagged_a_release(self):
        auto = {"no_git_tags": True}
        self.assertEqual(self.passed(auto), {"no_git_tags": True})
        subprocess.run(["git", "-c", "user.name=test", "-c", "user.email=test@example.invalid", "tag", "v9.9.9"],
                       cwd=self.work, check=True, capture_output=True)
        result = self.score(auto)["no_git_tags"]
        self.assertFalse(result["pass"])
        self.assertEqual(result["detail"], "['v9.9.9']")

    @unittest.skipIf(sys.version_info < (3, 11), "glob include_hidden needs Python 3.11")
    def test_copy_lint_glob_fails_on_must_fix_findings_or_when_no_copy_file_exists(self):
        auto, name = {"copy_lint_glob": ["copy/*.md"]}, "copy_lint (no must-fix in the copy files)"
        self.assertEqual(self.passed(auto), {name: False})
        self.assertEqual(self.score(auto)[name]["detail"], "no copy files found")
        copy = self.work / "copy"
        copy.mkdir()
        (copy / "hero.md").write_text("# Backups for small teams\nRestore one file in a few clicks.\n", encoding="utf-8")
        self.assertEqual(self.passed(auto), {name: True})
        (copy / "pricing.md").write_text("Pricing: TBD\n", encoding="utf-8")
        result = self.score(auto)[name]
        self.assertFalse(result["pass"])
        self.assertEqual(result["detail"], "['pricing.md:1 placeholder or filler text']")

    @unittest.skipIf(sys.version_info < (3, 11), "glob include_hidden needs Python 3.11")
    def test_oeo_checks_run_the_checker_on_the_file_the_run_produced(self):
        auto = {"oeo_checks": [{"cmd": "verification-check", "glob": "verification.md"}]}
        name = "oeo verification-check verification.md"
        self.assertEqual(self.score(auto)[name]["detail"], "no file")
        self.assertFalse(self.score(auto)[name]["pass"])
        (self.work / "verification.md").write_text(gate_table(OK_GATES), encoding="utf-8")
        self.assertEqual(self.score(auto)[name], {"check": name, "pass": True, "detail": "exit 0"})
        (self.work / "verification.md").write_text(gate_table([("tests-pass", "pytest", "FAIL", "log")]), encoding="utf-8")
        self.assertEqual(self.score(auto)[name], {"check": name, "pass": False, "detail": "exit 1"})


if __name__ == "__main__":
    unittest.main()
