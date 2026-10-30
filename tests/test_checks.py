"""Deterministic checks (scripts/checks.py), the CLI commands built on them, the Stop-event
FinOps snapshot, and the main-session lines of `oeo cost`.

Nothing here writes inside the repository: every project lives under the per-test temp dir.
"""
import datetime
import json
import os
import tempfile
import unittest
from pathlib import Path
from datetime import datetime as _datetime

from ._common import IsolatedTestCase, finops_hook

import checks  # noqa: E402  (scripts/ is put on sys.path by ._common)

TODAY = datetime.date(2026, 10, 30)
DASH = "—"        # em dash
APOS = "’"        # typographic apostrophe


def md_table(header, rows):
    """A markdown pipe table: header cells, then one tuple per row."""
    lines = ["| " + " | ".join(header) + " |", "|" + "|".join("---" for _ in header) + "|"]
    lines += ["| " + " | ".join(str(c) for c in row) + " |" for row in rows]
    return "\n".join(lines) + "\n"


def jsonl(rows, garbage=False):
    return "".join(json.dumps(r) + "\n" for r in rows) + ("{not json\n\n" if garbage else "")


# --------------------------------------------------------------------------- engagement ids
class EngagementIdTests(unittest.TestCase):
    def test_explicit_id_wins_and_is_slugified(self):
        eid = checks.engagement_id("Ignored summary", explicit="Checkout Redesign!", today=TODAY)
        self.assertEqual(eid, "checkout-redesign")  # no date prefix, summary unused
        self.assertEqual(checks.engagement_id("s", explicit="../../etc/passwd", today=TODAY), "etc-passwd")
        self.assertEqual(checks.engagement_id("s", explicit="a" * 100, today=TODAY), "a" * 60)  # explicit limit is 60

    def test_default_is_date_then_slug_of_summary_or_engagement_when_empty(self):
        self.assertEqual(checks.engagement_id("Fix the Login bug!", today=TODAY), "20261030-fix-the-login-bug")
        self.assertEqual(checks.engagement_id("Fix the Login bug!", explicit="", today=TODAY), "20261030-fix-the-login-bug")
        # same request, same day -> same folder; another day -> another folder
        self.assertEqual(checks.engagement_id("Ship it", today=TODAY), checks.engagement_id("Ship it", today=TODAY))
        self.assertEqual(checks.engagement_id("Ship it", today=datetime.date(2027, 1, 2)), "20270102-ship-it")
        self.assertRegex(checks.engagement_id("Ship it"), r"^\d{8}-ship-it$")  # today defaults to the real date
        for summary in ("", None, "   ", "!!! ???", "日本語"):
            with self.subTest(summary=summary):
                self.assertEqual(checks.engagement_id(summary, today=TODAY), "20261030-engagement")
        self.assertEqual(checks.slugify(""), "engagement")   # empty summary -> "<date>-engagement"

    def test_slug_is_limited_and_never_ends_with_a_hyphen(self):
        self.assertEqual(checks.slugify("a" * 100), "a" * 40)
        self.assertEqual(checks.slugify("a" * 39 + "-bcd"), "a" * 39)  # cut lands right after the hyphen
        self.assertEqual(checks.slugify("one two three", limit=7), "one-two")
        self.assertEqual(checks.slugify("  Hello,   World!! "), "hello-world")
        eid = checks.engagement_id("word " * 40, today=TODAY)
        self.assertLessEqual(len(eid), len("20261030-") + 40)
        self.assertFalse(eid.endswith("-"))


# --------------------------------------------------------------------------- markdown helpers
class MarkdownTableTests(unittest.TestCase):
    def test_md_tables_and_column_lookup(self):
        text = "\n".join([
            "Intro | not a table",
            "| A | B |",
            "|:--|--:|",
            "| 1 | two |",
            "| 3 | four |",
            "",
            "random line with | a pipe",
            "| no | separator |",
            "| x | y |",
            "",
            "| Gate | Result |",
            "| --- | --- |",
            "|  `x`  | PASS |",          # last line, no trailing newline
        ])
        tables = list(checks.md_tables(text))
        self.assertEqual(tables, [(["a", "b"], [["1", "two"], ["3", "four"]]),
                                  (["gate", "result"], [["`x`", "PASS"]])])
        self.assertEqual(list(checks.md_tables("no tables here\n")), [])
        header = ["id", "task", "owner", "status"]
        self.assertEqual(checks.column(header, "id"), 0)
        self.assertEqual(checks.column(header, "task", "id"), 1)      # earlier name wins, not earlier column
        self.assertEqual(checks.column(header, "stat"), 3)            # substring
        self.assertIsNone(checks.column(header, "missing"))
        self.assertIsNone(checks.column([], "id"))


# --------------------------------------------------------------------------- route --log --engagement
class RouteEngagementTests(IsolatedTestCase):
    def route(self, *extra):
        code, out, err = self.run_cli("route", "--type", "trivial", "--files", "1", "--lines", "1", "--log",
                                      "--session", "s1", *extra)
        self.assertIsNone(code)
        return out, err

    def entries(self):
        log = self.tmp / ".oeo" / "activation-log.jsonl"
        return [json.loads(line) for line in log.read_text(encoding="utf-8").splitlines()]

    def test_explicit_engagement_creates_its_folder_and_is_logged(self):
        _, err = self.route("--engagement", "Checkout Redesign!", "--summary", "something else")
        self.assertTrue((self.tmp / ".oeo" / "checkout-redesign").is_dir())
        self.assertEqual(self.entries()[0]["engagement"], "checkout-redesign")
        self.assertIn(".oeo/checkout-redesign/", err)

    def test_engagement_defaults_to_date_and_slug_of_the_summary_and_retriage_reuses_it(self):
        before = datetime.date.today()
        self.route("--summary", "Fix the login bug")
        self.route("--summary", "")
        self.route("--summary", "Fix the login bug")      # re-triage of the same request
        after = datetime.date.today()
        first, second, third = (e["engagement"] for e in self.entries())
        days = {before, after}
        self.assertIn(first, {f"{d:%Y%m%d}-fix-the-login-bug" for d in days})
        self.assertIn(second, {f"{d:%Y%m%d}-engagement" for d in days})
        if before == after:                               # (a midnight rollover mid-test is legitimately a new id)
            self.assertEqual(third, first)
            self.assertEqual(sorted(p.name for p in (self.tmp / ".oeo").iterdir() if p.is_dir()), sorted({first, second}))
        for eid in (first, second):
            self.assertTrue((self.tmp / ".oeo" / eid).is_dir())

    def test_engagement_cannot_escape_the_oeo_directory(self):
        self.route("--engagement", "../../escape")
        self.assertEqual([p.name for p in self.tmp.iterdir()], [".oeo"])
        self.assertEqual(sorted(p.name for p in (self.tmp / ".oeo").iterdir()), ["activation-log.jsonl", "escape"])


# --------------------------------------------------------------------------- status
ALPHA, BETA = "20261001-alpha-api", "20261015-beta-site"


class OeoProject(IsolatedTestCase):
    """A project root (the temp dir) with helpers to write `.oeo/` files."""

    def setUp(self):
        super().setUp()
        self.oeo = self.tmp / ".oeo"

    def fresh(self):
        """Point `self.oeo` at a new, empty project (for subTests that each need their own .oeo)."""
        self.oeo = Path(tempfile.mkdtemp(dir=self.tmp)) / ".oeo"

    def put(self, rel, text):
        path = self.oeo / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8")
        return path

    def put_jsonl(self, rel, rows, garbage=False):
        return self.put(rel, jsonl(rows, garbage))

    def build_realistic_oeo(self):
        """Two engagements (alpha re-triaged once), plans, gates, decisions, subagent and main-session usage."""
        self.put_jsonl("activation-log.jsonl", [
            {"ts": "2026-10-01T09:00:00+00:00", "session": "sess-a", "engagement": ALPHA, "summary": "Alpha API",
             "class": "B", "budget_tokens": 10000, "estimate_tokens": 5000},
            {"ts": "2026-10-02T09:00:00+00:00", "session": "sess-a", "engagement": ALPHA, "summary": "Alpha API v2",
             "class": "C", "budget_tokens": 10000, "estimate_tokens": 6000},
            {"ts": "2026-10-15T09:00:00+00:00", "session": "sess-b", "engagement": BETA, "summary": "Beta site",
             "class": "A", "budget_tokens": 50000, "estimate_tokens": 2000},
        ], garbage=True)
        self.put(f"{ALPHA}/plan.md", "# Plan\n\n" + md_table(("risk", "mitigation"), [("slow", "cache")]) + "\n" + md_table(
            ("id", "task", "owner", "status"), [
                ("T1", "Schema", "junior-developer", "done"),
                ("T2", "Endpoints", "senior-developer", "`in_progress`"),
                ("T3", "Release notes", "project-manager", "in_review"),
                ("T4", "Deploy", "devops", "blocked: waiting on infra owner"),
                ("T5", "Old idea", "project-manager", "cancelled"),
                ("T6", "Load test", "qa-verifier", "todo"),
            ]))
        self.put(f"{ALPHA}/verification.md", md_table(("gate", "command", "result", "evidence"), [
            ("tests-pass", "pytest", "PASS", "42 passed"),
            ("security-review", "manual", "FAIL", "open finding S1"),
            ("regression-test", "n/a", "N/A: no code change", ""),
            ("license-gate", "oeo license", "NOT RUN", ""),
        ]))
        self.put(f"{BETA}/plan.md", md_table(("id", "task", "status"), [("T1", "Page", "done"), ("T2", "Copy", "done")]))
        self.put(f"{BETA}/verification.md", md_table(("gate", "result"), [("`tests-pass`", "PASS"), ("license-gate", "PASS")]))
        self.put("decisions.md", md_table(("date", "decision", "options", "rationale", "by", "review_by"), [
            ("2026-09-01", "Use SQLite for v1", "SQLite, Postgres", "simple", "pm", "2020-01-01"),
            ("2026-10-10", "Adopt a monorepo", "yes, no", "speed", "cto", "2999-12-31"),
            ("2026-10-12", "Pick a logo", "a, b", "taste", "user", ""),
        ]))
        self.put_jsonl("finops.jsonl", [
            {"session_id": "sess-a", "agent_type": "oeo:junior-developer", "input_tokens": 4000, "output_tokens": 1500,
             "cache_read_tokens": 90000, "cache_write_tokens": 500},      # 6,000 (cache reads are excluded)
            {"session_id": "sess-a", "agent_type": "oeo:qa-verifier", "input_tokens": 2000, "output_tokens": 500,
             "cache_read_tokens": 0, "cache_write_tokens": 0},            # 2,500
            {"session_id": "sess-b", "agent_type": "oeo:qa-verifier", "input_tokens": 700, "output_tokens": 300},
            {"session_id": "sess-x", "agent_type": "oeo:qa-verifier", "input_tokens": 99999},   # no engagement
        ], garbage=True)
        # tied by the session_id inside the snapshot, not by the file name
        self.put("sessions/first.json", json.dumps({"session_id": "sess-a", "total_tokens": 7000}))
        self.put("sessions/sess-b.json", json.dumps({"session_id": "sess-b", "total_tokens": 3000}))
        self.put("sessions/stranger.json", json.dumps({"session_id": "sess-z", "total_tokens": 99999}))
        self.put("sessions/broken.json", "{not json")

    def one_engagement(self, statuses=(), gates=(), decisions=(), budget=0, spent=0):
        """A single engagement `e1` (session `s1`) built from task statuses, (gate, result) pairs, ..."""
        self.put_jsonl("activation-log.jsonl", [{"session": "s1", "engagement": "e1", "class": "B",
                                                 "ts": "2026-10-01T00:00:00+00:00", "budget_tokens": budget}])
        if statuses:
            self.put("e1/plan.md", md_table(("id", "status"), [(f"T{i}", s) for i, s in enumerate(statuses, 1)]))
        if gates:
            self.put("e1/verification.md", md_table(("gate", "result"), gates))
        if decisions:
            self.put("decisions.md", md_table(("decision", "review_by"), decisions))
        if spent:
            self.put_jsonl("finops.jsonl", [{"session_id": "s1", "agent_type": "oeo:qa-verifier", "input_tokens": spent}])
        return checks.status(self.oeo, TODAY)


class StatusTests(OeoProject):
    def engagement(self, data, eid):
        return next(e for e in data["engagements"] if e["engagement"] == eid)

    def test_needs_you_has_the_in_review_task_and_only_the_past_due_decision_and_blocked_lists_the_blocker(self):
        self.build_realistic_oeo()
        data = checks.status(self.oeo, TODAY)
        self.assertEqual(data["needs_you"], [f"{ALPHA}: T3: waiting on a human",
                                             "review due 2020-01-01: Use SQLite for v1"])
        text = "\n".join(data["needs_you"])
        self.assertNotIn("monorepo", text)   # review_by in the future
        self.assertNotIn("logo", text)       # no review_by at all
        self.assertEqual(data["blocked"], [f"{ALPHA}: T4: blocked: waiting on infra owner"])

    def test_per_engagement_task_counts_gates_latest_plan_and_token_totals(self):
        self.build_realistic_oeo()
        data = checks.status(self.oeo, TODAY)
        self.assertEqual([e["engagement"] for e in data["engagements"]], [ALPHA, BETA])  # re-triage does not duplicate
        alpha, beta = (self.engagement(data, x) for x in (ALPHA, BETA))
        self.assertEqual(alpha["tasks"], {"backlog": 0, "todo": 1, "in_progress": 1, "in_review": 1,
                                          "blocked": 1, "done": 1, "cancelled": 1})
        self.assertEqual(alpha["gates"], {"tests-pass": "PASS", "security-review": "FAIL",
                                          "regression-test": "N/A", "license-gate": "NOT RUN"})
        self.assertEqual(alpha["failing_gates"], ["security-review", "license-gate"])  # FAIL and NOT RUN, not N/A
        self.assertEqual((alpha["class"], alpha["summary"], alpha["last_activity"]), ("C", "Alpha API v2", "2026-10-02"))
        self.assertEqual(beta["tasks"]["done"], 2)
        self.assertEqual(beta["gates"], {"tests-pass": "PASS", "license-gate": "PASS"})  # backticks stripped
        self.assertEqual((beta["failing_gates"], beta["class"], beta["last_activity"]), ([], "A", "2026-10-15"))
        # input + output + cache writes; cache reads, other sessions and unreadable snapshots are left out
        self.assertEqual((alpha["subagent_tokens"], alpha["main_session_tokens"], alpha["budget_tokens"]), (8500, 7000, 10000))
        self.assertEqual((beta["subagent_tokens"], beta["main_session_tokens"], beta["budget_tokens"]), (1000, 3000, 50000))

    def test_next_action_prefers_a_failing_gate_then_needs_you_then_blocked(self):
        self.build_realistic_oeo()
        data = checks.status(self.oeo, TODAY)
        self.assertTrue(data["needs_you"] and data["blocked"])   # there is plenty else waiting
        self.assertEqual(data["next_action"], f"{ALPHA}: resolve gate security-review")
        cases = [
            ("a NOT RUN gate counts as failing", dict(gates=[("tests", "PASS"), ("lic", "NOT RUN")], statuses=["in_review"]),
             "e1: resolve gate lic"),
            ("in_review beats blocked", dict(statuses=["blocked: legal", "in_review"], gates=[("tests", "PASS")]),
             "e1: T2: waiting on a human"),
            ("a due decision beats blocked", dict(statuses=["blocked: legal"], decisions=[("Pick a vendor", "2026-10-01")]),
             "review due 2026-10-01: Pick a vendor"),
            ("blocked only", dict(statuses=["blocked: waits on legal", "done"]), "unblock e1: T1: blocked: waits on legal"),
            ("N/A and PASS gates need nothing", dict(statuses=["done"], gates=[("tests", "PASS"), ("a11y", "N/A")]),
             "nothing waiting on you"),
        ]
        for label, kwargs, expected in cases:
            with self.subTest(label):
                self.fresh()
                self.assertEqual(self.one_engagement(**kwargs)["next_action"], expected)

    def test_over_80_percent_budget_is_strictly_greater_than_80_percent(self):
        for spent, budget, expected in ((8000, 10000, []), (8001, 10000, ["e1"]), (10**9, 0, [])):
            with self.subTest(spent=spent, budget=budget):
                self.fresh()
                self.assertEqual(self.one_engagement(spent=spent, budget=budget)["over_80_percent_budget"], expected)
        self.fresh()
        self.build_realistic_oeo()
        self.assertEqual(checks.status(self.oeo, TODAY)["over_80_percent_budget"], [ALPHA])   # 8,500 of 10,000

    def test_decisions_due_today_count_and_rows_without_a_date_are_ignored(self):
        data = self.one_engagement(decisions=[("Due today", "2026-10-30"), ("Due tomorrow", "2026-10-31"),
                                              ("Free text", "TBD"), ("Blank", ""), ("Embedded", "revisit by 2026-01-05 (q1)")])
        self.assertEqual(data["needs_you"], ["review due 2026-10-30: Due today",
                                             "review due 2026-01-05: Embedded"])

    # Regression (fixed): checks.py:121 `dt.date.fromisoformat` raises ValueError for a well-shaped but impossible date, so one
    # typo in decisions.md ("2026-13-45") crashes the whole `oeo status` brief instead of skipping the row.
    def test_a_malformed_review_by_date_does_not_crash_the_brief(self):
        data = self.one_engagement(decisions=[("Typo", "2026-13-45"), ("Fine", "2026-01-01")])
        self.assertIn("review due 2026-01-01: Fine", data["needs_you"])

    # Regression (fixed): checks.py:77 `column(header, "id", "task")` matches by substring, so the "Evidence" column ("evIDence")
    # is taken as the task label before the "Task" column is considered.
    def test_tasks_are_labelled_by_the_task_column_even_if_another_header_contains_id(self):
        self.put_jsonl("activation-log.jsonl", [{"session": "s1", "engagement": "e1", "class": "B"}])
        self.put("e1/plan.md", md_table(("task", "status", "evidence"), [("Deploy", "blocked: waiting on infra", "runbook")]))
        self.assertEqual(checks.status(self.oeo, TODAY)["blocked"], ["e1: Deploy: blocked: waiting on infra"])

    def test_log_entries_without_an_engagement_fall_back_to_session_then_default(self):
        self.put_jsonl("activation-log.jsonl", [{"session": "legacy-1", "class": "A", "ts": "2026-09-01T00:00:00+00:00"},
                                                {"class": "A"}])
        self.put("legacy-1/plan.md", md_table(("id", "status"), [("T1", "done")]))
        self.put_jsonl("finops.jsonl", [{"session_id": "legacy-1", "input_tokens": 10}])
        data = checks.status(self.oeo, TODAY)
        self.assertEqual([e["engagement"] for e in data["engagements"]], ["legacy-1", "default"])
        legacy, default = data["engagements"]
        self.assertEqual((legacy["tasks"]["done"], legacy["subagent_tokens"]), (1, 10))
        self.assertEqual((default["tasks"], default["gates"], default["subagent_tokens"]), (None, {}, 0))
        self.assertIn("default: class A · no plan · no gates yet", checks.format_status(data))

    def test_format_status_prints_every_section_and_one_next_action(self):
        self.build_realistic_oeo()
        text = checks.format_status(checks.status(self.oeo, TODAY))
        lines = text.splitlines()
        self.assertEqual([x for x in lines if x.endswith(":") and not x.startswith(" ")],
                         ["Needs you:", "Blocked:", "Status:", "Budget:"])
        self.assertIn(f"  - {ALPHA}: T3: waiting on a human", lines)
        self.assertIn("  - review due 2020-01-01: Use SQLite for v1", lines)
        self.assertIn(f"  - {ALPHA}: T4: blocked: waiting on infra owner", lines)
        self.assertIn(f"  - {ALPHA}: class C · tasks 1/5 done · gates 1 pass, 2 failing · last 2026-10-02", lines)
        self.assertIn(f"  - {BETA}: class A · tasks 2/2 done · gates 2 pass · last 2026-10-15", lines)
        self.assertIn(f"  - {ALPHA}: subagents 8,500 + main 7,000 of 10,000 subagent budget", lines)
        self.assertIn(f"  - over 80%: {ALPHA}", lines)
        self.assertEqual(lines[-1], f"One next action: {ALPHA}: resolve gate security-review")
        self.assertEqual(sum(x.startswith("One next action") for x in lines), 1)

    def test_format_status_caps_each_section_at_five_items(self):
        def brief(n_needs, n_blocked):
            return {"needs_you": [f"need-{i}" for i in range(n_needs)], "blocked": [f"block-{i}" for i in range(n_blocked)],
                    "engagements": [], "over_80_percent_budget": [], "next_action": "x"}
        lines = checks.format_status(brief(7, 6)).splitlines()
        for i in range(5):
            self.assertIn(f"  - need-{i}", lines)
            self.assertIn(f"  - block-{i}", lines)
        self.assertNotIn("  - need-5", lines)
        self.assertNotIn("  - block-5", lines)
        self.assertIn("  - ... and 2 more", lines)
        self.assertIn("  - ... and 1 more", lines)
        exactly_five = checks.format_status(brief(5, 0))
        self.assertNotIn("more", exactly_five)
        self.assertIn("  - need-4", exactly_five)

    def test_an_empty_oeo_directory_gives_none_everywhere(self):
        for label, prepare in (("no .oeo at all", lambda: None), ("empty .oeo", lambda: self.oeo.mkdir())):
            with self.subTest(label):
                prepare()
                data = checks.status(self.oeo, TODAY)
                self.assertEqual(data, {"needs_you": [], "blocked": [], "engagements": [], "over_80_percent_budget": [],
                                        "next_action": "nothing waiting on you"})
                self.assertEqual(checks.format_status(data), "\n".join([
                    "Needs you:", "  - none", "Blocked:", "  - none", "Status:", "  - none", "Budget:", "  - none",
                    "One next action: nothing waiting on you"]))

    def test_cli_status_prints_the_brief_and_json_is_valid(self):
        code, out, _ = self.run_cli("status")          # a project without .oeo: nothing to report, nothing created
        self.assertIsNone(code)
        self.assertIn("Needs you:\n  - none", out)
        self.assertIn("One next action: nothing waiting on you", out)
        self.assertEqual(json.loads(self.run_cli("status", "--json")[1])["engagements"], [])
        self.assertFalse(self.oeo.exists())
        self.build_realistic_oeo()
        code, out, _ = self.run_cli("status")
        self.assertIsNone(code)
        self.assertEqual(out.rstrip("\n"), checks.format_status(checks.status(self.oeo, TODAY)))
        self.assertIn(f"One next action: {ALPHA}: resolve gate security-review", out)
        code, out, _ = self.run_cli("status", "--json")
        self.assertIsNone(code)
        data = json.loads(out)
        self.assertEqual(data, checks.status(self.oeo, TODAY))
        self.assertEqual(set(data), {"needs_you", "blocked", "engagements", "over_80_percent_budget", "next_action"})


# --------------------------------------------------------------------------- copy lint
RULE_SAMPLES = {
    "unfilled template slot": ["Install from [REPOSITORY URL].", "Star us at {{repo_url}}"],
    "placeholder or filler text": ["Lorem ipsum dolor sit amet", "Pricing: TBD", "TODO write the intro",
                                   "Hello [insert customer name]", "Replace this placeholder image"],
    "testimonial or customer claim without a source": ["Trusted by 10,000+ teams", "Loved by 2.5k developers",
                                                       "Used by 300 companies"],
    "stock opener or hype word": ["In today's fast-paced world, teams struggle.", "Unlock your potential",
                                  "Supercharge your workflow", "Seamlessly connect your tools", "A game-changer for ops",
                                  "We revolutionize testing", "We revolutionise testing", "Cutting-edge tooling",
                                  "A next-gen platform", "World-class support", "Leverage our API",
                                  "We empower every team"],
    "contrast reveal (\"not X. It's Y\")": ["It is not just a tool. It is a teammate.",
                                            "It's not a dashboard. It's a decision engine.",
                                            "We are not a vendor! We are your partner."],
    "stacked negation list": ["No setup. No lock-in. No surprises.", "No cost to try! No card needed. No catch."],
    "number or percentage without a source on the line": ["Cuts costs by 40%", "Builds are 10x faster",
                                                          "Over 100+ integrations", "Uptime of 99.9%"],
    "vague call to action": ["Learn more", "Click here", "Read more →"],
    "intensifier": ["It is very fast", "Truly simple", "Really good", "Super easy"],
}
NUMBER_RULE = "number or percentage without a source on the line"
CLEAN_COPY = """# Backups for small teams
Store every backup in two regions and restore a single file in a few clicks.
Pricing is listed on the pricing page. No sales call is required.
Start a free trial
"""


class CopyLintTests(IsolatedTestCase):
    @staticmethod
    def rules(text):
        return [(f["severity"], f["rule"]) for f in checks.copy_lint(text)]

    def test_every_rule_has_a_positive_case_with_its_severity(self):
        self.assertEqual(set(RULE_SAMPLES), {what for _, what, _ in checks.COPY_RULES})  # a new rule needs a sample here
        severity = {what: sev for sev, what, _ in checks.COPY_RULES}
        for what, samples in RULE_SAMPLES.items():
            for text in samples:
                with self.subTest(rule=what, text=text):
                    self.assertIn((severity[what], what), self.rules(text))
        # the two-sentence contrast reveal is exactly one should-fix finding
        self.assertEqual(self.rules("It is not just a tool. It is a teammate."),
                         [("should-fix", "contrast reveal (\"not X. It's Y\")")])

    def test_clean_copy_has_no_findings_and_findings_carry_line_severity_rule_and_text(self):
        self.assertEqual(checks.copy_lint(CLEAN_COPY), [])
        self.assertEqual(checks.copy_lint(""), [])
        self.assertEqual(checks.copy_lint("\n  \n"), [])
        findings = checks.copy_lint("Fine opening line.\n\n\nWe leverage synergy.\nAll good here.\nTODO: add pricing\n")
        self.assertEqual(findings, [
            {"line": 4, "severity": "should-fix", "rule": "stock opener or hype word", "text": "leverage"},
            {"line": 6, "severity": "must-fix", "rule": "placeholder or filler text", "text": "TODO"},
        ])

    def test_code_fences_are_ignored(self):
        text = "\n".join(["Intro line.", "```", "TODO inside code", "Unlock the secret", "```",
                          "Outro with TODO.", "```python", "# TODO: more code", "```"])
        self.assertEqual([(f["line"], f["text"]) for f in checks.copy_lint(text)], [(6, "TODO")])

    def test_em_dash_is_flagged_only_in_short_lines(self):
        rule = "em dash in short-form copy"
        self.assertEqual(self.rules(f"Fast {DASH} and simple"), [("should-fix", rule)])
        self.assertEqual(self.rules("a" * 89 + DASH), [("should-fix", rule)])          # 90 characters: still short
        self.assertEqual(self.rules("   " + "a" * 89 + DASH + "  "), [("should-fix", rule)])   # measured stripped
        self.assertEqual(self.rules("a" * 90 + DASH), [])                                # 91 characters: long-form prose
        long_line = ("Our backups run every night and are stored in two regions " + DASH + " restores take minutes, not hours.")
        self.assertGreater(len(long_line), 90)
        self.assertEqual(self.rules(long_line), [])
        self.assertEqual(self.rules("Fast – and simple, or fast - and simple"), [])   # en dash and hyphen are fine

    def test_a_number_with_a_source_marker_on_the_same_line_is_not_flagged(self):
        unsourced = ["Builds are 40% faster", "Builds are 40% faster than before", "Over 100+ integrations"]
        sourced = [
            "Builds are 40% faster (source: internal benchmark, Sept 2026)",
            "Builds are 40% faster, [measured on our CI](https://example.com/bench).",
            "Builds are 40% faster.[^1]",
            "Over 100+ integrations, see the [full list](https://example.com/integrations)",
        ]
        for text in unsourced:
            with self.subTest(text=text):
                self.assertIn(NUMBER_RULE, [r for _, r in self.rules(text)])
        for text in sourced:
            with self.subTest(text=text):
                self.assertNotIn(NUMBER_RULE, [r for _, r in self.rules(text)])
        # the marker has to be on the same line as the number
        self.assertEqual([f["line"] for f in checks.copy_lint("Builds are 40% faster\n(source: internal benchmark)")], [1])

    # Regression (fixed): checks.py:209 the source-marker lookahead only scans the text AFTER the number, so a source named
    # earlier on the same line ("[Benchmark](https://...): builds are 40% faster") is not recognised.
    def test_a_source_marker_before_the_number_on_the_same_line_also_counts(self):
        self.assertNotIn(NUMBER_RULE, [r for _, r in self.rules("[Benchmark](https://example.com/b): builds are 40% faster.")])

    # Regression (fixed): checks.py:203-206 the patterns only know the ASCII apostrophe; typographic copy ("It’s", "today’s",
    # as written by every word processor) slips past the contrast-reveal and stock-opener rules.
    def test_typographic_apostrophes_are_linted_like_ascii_ones(self):
        self.assertIn("stock opener or hype word", [r for _, r in self.rules(f"In today{APOS}s fast-paced world")])
        self.assertTrue(self.rules(f"It{APOS}s not just a tool. It{APOS}s a teammate."))

    # Regression (fixed): checks.py:201 the testimonial pattern only accepts a bare k/m suffix, so "2 million developers" (and
    # "2 million users") produce no finding at all.
    def test_a_spelled_out_million_customer_claim_is_must_fix(self):
        self.assertIn(("must-fix", "testimonial or customer claim without a source"),
                      self.rules("Trusted by 2 million developers worldwide."))

    def test_cli_exits_1_only_when_a_must_fix_finding_exists(self):
        def lint(*texts):
            paths = []
            for i, text in enumerate(texts):
                path = self.tmp / f"copy{i}.md"
                path.write_text(text, encoding="utf-8")
                paths.append(str(path))
            code, out, _ = self.run_cli("copy-lint", *paths)
            return code, out, paths

        code, out, paths = lint("# Pricing\nTODO: fill in the plan table\n")
        self.assertEqual(code, 1)
        self.assertIn(f"{paths[0]}:2: must-fix: placeholder or filler text: 'TODO'", out)
        self.assertIn("copy gate: FAIL (must-fix findings)", out)

        code, out, paths = lint("Unlock your team's potential.\n")                  # should-fix only
        self.assertEqual(code, 0)
        self.assertIn(f"{paths[0]}:1: should-fix: stock opener or hype word: 'Unlock'", out)
        self.assertIn("copy gate: fix or justify the findings", out)

        code, out, _ = lint("We are very careful with backups.\n")                   # polish only
        self.assertEqual(code, 0)
        self.assertIn("polish: intensifier", out)

        code, out, _ = lint(CLEAN_COPY)
        self.assertEqual((code, out.strip()), (0, "copy gate: no findings"))

        code, out, _ = lint(CLEAN_COPY, "Lorem ipsum\n", "Learn more\n")             # one bad file fails the run
        self.assertEqual(code, 1)
        self.assertIn("copy1.md:1: must-fix", out)
        self.assertIn("copy2.md:1: should-fix: vague call to action", out)


# --------------------------------------------------------------------------- ledger check
LEDGER_HEADER = ("| # | claim | observed / inferred / unknown | evidence (URL or file + access date) | search boundary |\n"
                 "|---|---|---|---|---|\n")


def ledger(*rows):
    """rows: (claim, tag, evidence, boundary)"""
    return LEDGER_HEADER + "".join("| " + " | ".join((str(i),) + tuple(r)) + " |\n" for i, r in enumerate(rows, 1))


VALID_LEDGER = ledger(
    ("Pricing starts at 10 USD", "observed", "https://example.com/pricing (accessed 2026-10-01)", ""),
    ("SSO is likely on higher plans", "inferred", "pricing page lists SAML under Enterprise", ""),
    ("There is no public API", "unknown", "", "searched docs, changelog and GitHub on 2026-10-01"),
    ("Home page layout", "**Observed**", "./shots/home.png 2026-10-02", ""),
    ("Raw page saved", "`observed`", ".oeo/research/x/raw/page.md, 2026-10-02", ""),
    ("Linked evidence", "observed", "[docs](https://example.com/docs) 2026-10-03", ""),
)


class LedgerCheckTests(IsolatedTestCase):
    def test_valid_ledger_passes(self):
        self.assertEqual(checks.ledger_check(VALID_LEDGER), [])
        # unrelated tables around the ledger are ignored
        self.assertEqual(checks.ledger_check(md_table(("risk", "fix"), [("a", "b")]) + "\n" + VALID_LEDGER), [])

    def test_each_rule_violation_is_reported(self):
        cases = [
            ("bad tag", ("c", "guess", "https://example.com/p 2026-10-01", ""), "tag 'guess' must be observed, inferred or unknown"),
            ("empty tag", ("c", "", "https://example.com/p 2026-10-01", ""), "tag '' must be observed, inferred or unknown"),
            ("observed without URL or file", ("c", "observed", "saw it on the pricing page 2026-10-01", ""),
             "observed claims need a URL or file and an access date"),
            ("observed without access date", ("c", "observed", "https://example.com/pricing", ""),
             "observed claims need a URL or file and an access date"),
            ("observed with only a date", ("c", "observed", "2026-10-01", ""),
             "observed claims need a URL or file and an access date"),
            ("observed with no evidence", ("c", "observed", "", ""),
             "observed claims need a URL or file and an access date"),
            ("inferred without evidence", ("c", "inferred", "", ""),
             "inferred claims must say what they are inferred from"),
            ("unknown without boundary", ("c", "unknown", "", ""), "unknown claims must state the search boundary"),
            ("unknown with evidence but no boundary", ("c", "unknown", "looked at the docs", ""),
             "unknown claims must state the search boundary"),
        ]
        for label, row, message in cases:
            with self.subTest(label):
                problems = checks.ledger_check(ledger(row))
                self.assertEqual(len(problems), 1, problems)
                self.assertEqual(problems[0], f"row 1 (c): {message}")

    def test_problems_name_the_row_and_truncate_the_claim_to_50_characters(self):
        claim = "x" * 80
        problems = checks.ledger_check(ledger(
            ("fine", "inferred", "from the docs", ""),
            (claim, "unknown", "", ""),
            ("third", "guess", "", ""),
        ))
        self.assertEqual(problems, [f"row 2 ({'x' * 50}): unknown claims must state the search boundary",
                                    "row 3 (third): tag 'guess' must be observed, inferred or unknown"])

    def test_a_missing_or_unusable_table_is_a_problem(self):
        texts = [
            "",
            "just prose, no table\n",
            md_table(("risk", "mitigation"), [("slow", "cache")]),                       # a table, but not a ledger
            md_table(("claim", "observed / inferred / unknown"), [("a", "observed")]),   # no evidence column
            LEDGER_HEADER,                                                               # header only: zero rows
        ]
        for text in texts:
            with self.subTest(text=text[:40]):
                problems = checks.ledger_check(text)
                self.assertEqual(len(problems), 1)
                self.assertTrue(problems[0].startswith("no ledger table found"), problems)

    def test_cli_exit_codes(self):
        good, bad = self.tmp / "good.md", self.tmp / "bad.md"
        good.write_text(VALID_LEDGER, encoding="utf-8")
        bad.write_text(ledger(("a", "guess", "", ""), ("b", "unknown", "", "")), encoding="utf-8")
        code, out, _ = self.run_cli("ledger-check", str(good))
        self.assertEqual((code, out.strip()), (0, "ledger: OK"))
        code, out, _ = self.run_cli("ledger-check", str(bad))
        self.assertEqual(code, 1)
        self.assertIn(f"{bad}: row 1 (a): tag 'guess' must be observed, inferred or unknown", out)
        self.assertIn(f"{bad}: row 2 (b): unknown claims must state the search boundary", out)
        self.assertIn("ledger: FAIL (2 problem(s))", out)
        empty = self.tmp / "empty.md"
        empty.write_text("nothing here\n", encoding="utf-8")
        self.assertEqual(self.run_cli("ledger-check", str(empty))[0], 1)


# --------------------------------------------------------------------------- Stop hook: main-session snapshot
def assistant(msg_id, model, inp=0, out=0, cache_read=0, cache_write=0):
    usage = {"input_tokens": inp, "output_tokens": out,
             "cache_read_input_tokens": cache_read, "cache_creation_input_tokens": cache_write}
    return json.dumps({"type": "assistant", "uuid": f"uuid-{msg_id}",
                       "message": {"id": msg_id, "model": model, "usage": usage}})


# m1 is streamed twice (the later copy has grown); noise lines are skipped.
MAIN_TRANSCRIPT = [
    assistant("m1", "model-a", inp=10, out=5, cache_read=1000, cache_write=2),
    "this is not json",
    assistant("m1", "model-a", inp=10, out=50, cache_read=1000, cache_write=2),
    assistant("m2", "model-b", inp=3, out=4, cache_write=6),
]


class StopSnapshotTests(IsolatedTestCase):
    def setUp(self):
        super().setUp()
        self.project = self.tmp / "project"
        self.project.mkdir()
        os.environ["CLAUDE_PROJECT_DIR"] = str(self.project)
        self.transcript = self.tmp / "main.jsonl"
        self.transcript.write_text("\n".join(MAIN_TRANSCRIPT) + "\n", encoding="utf-8")
        self.sessions = self.project / ".oeo" / "sessions"

    def stop(self, **over):
        payload = {"hook_event_name": "Stop", "session_id": "sess-1", "transcript_path": str(self.transcript)}
        payload.update(over)
        return self.run_hook(finops_hook, json.dumps(payload))

    def snapshot(self, name="sess-1"):
        return json.loads((self.sessions / f"{name}.json").read_text(encoding="utf-8"))

    def test_stop_writes_a_snapshot_with_total_tokens_excluding_cache_reads(self):
        (self.project / ".oeo").mkdir()
        self.assertEqual(self.stop(), (0, ""))
        snap = self.snapshot()
        self.assertEqual((snap["session_id"], snap["models"], snap["api_responses"]), ("sess-1", ["model-a", "model-b"], 2))
        self.assertEqual((snap["input_tokens"], snap["output_tokens"], snap["cache_read_tokens"], snap["cache_write_tokens"]),
                         (13, 54, 1000, 8))
        self.assertEqual(snap["total_tokens"], 13 + 54 + 8)    # input + output + cache writes
        _datetime.fromisoformat(snap["ts"])
        self.assertFalse((self.project / ".oeo" / "finops.jsonl").exists())   # Stop never logs a subagent record

    def test_a_second_stop_overwrites_the_snapshot_instead_of_accumulating(self):
        (self.project / ".oeo").mkdir()
        self.stop()
        self.stop()
        self.assertEqual(self.snapshot()["total_tokens"], 75)            # idempotent
        with open(self.transcript, "a", encoding="utf-8") as fh:
            fh.write(assistant("m3", "model-b", inp=100, out=1) + "\n")
        self.stop()
        snap = self.snapshot()
        self.assertEqual((snap["input_tokens"], snap["output_tokens"], snap["api_responses"]), (113, 55, 3))
        self.assertEqual(snap["total_tokens"], 113 + 55 + 8)             # the transcript total, not 75 + 176
        self.assertEqual([p.name for p in self.sessions.iterdir()], ["sess-1.json"])   # one file, no temp leftovers

    def test_odd_session_ids_are_sanitized_and_cannot_escape_the_sessions_folder(self):
        (self.project / ".oeo").mkdir()
        names = {"../../escape": "escape", "a b/c\\d:e": "abcde", "///": "session", "x" * 200: "x" * 80,
                 "sess_1-ok": "sess_1-ok"}
        for sid, name in names.items():
            with self.subTest(sid=sid[:20]):
                self.assertEqual(self.stop(session_id=sid), (0, ""))
                self.assertEqual(self.snapshot(name)["session_id"], sid)   # the raw id is kept inside the file
        self.assertEqual(sorted(p.name for p in self.sessions.iterdir()), sorted(f"{n}.json" for n in names.values()))
        self.assertEqual([p.name for p in self.project.iterdir()], [".oeo"])
        self.assertEqual(sorted(p.name for p in self.tmp.iterdir()), ["main.jsonl", "project"])

    def test_writes_nothing_without_oeo_when_opted_out_or_with_an_unusable_payload(self):
        self.assertEqual(self.stop(), (0, ""))                           # no .oeo directory in the project
        self.assertEqual(list(self.project.iterdir()), [])
        (self.project / ".oeo").mkdir()
        for value in ("off", "OFF", "0", "false"):                       # OEO_FINOPS opt-out
            with self.subTest(value=value):
                os.environ["OEO_FINOPS"] = value
                self.assertEqual(self.stop(), (0, ""))
                self.assertFalse(self.sessions.exists())
        del os.environ["OEO_FINOPS"]
        a_directory = self.tmp / "a-directory"
        a_directory.mkdir()
        bad = [{"transcript_path": None}, {"transcript_path": str(self.tmp / "missing.jsonl")},
               {"transcript_path": str(a_directory)}, {"session_id": ""}, {"session_id": None}, {"session_id": 0}]
        for over in bad:
            with self.subTest(over=str(over)[:60]):
                self.assertEqual(self.stop(**over), (0, ""))
                self.assertFalse(self.sessions.exists())
        payload = {"hook_event_name": "Stop", "transcript_path": str(self.transcript)}   # no session_id key at all
        self.assertEqual(self.run_hook(finops_hook, json.dumps(payload)), (0, ""))
        self.assertFalse(self.sessions.exists())

    def test_a_symlinked_oeo_directory_is_never_written_through(self):
        elsewhere = self.tmp / "elsewhere"
        elsewhere.mkdir()
        try:
            os.symlink(elsewhere, self.project / ".oeo", target_is_directory=True)
        except (OSError, NotImplementedError):
            self.skipTest("symlinks unavailable")
        self.assertEqual(self.stop(), (0, ""))
        self.assertEqual(list(elsewhere.iterdir()), [])

    # Regression (fixed): finops_hook.py:54-55,61 only checks `.oeo` and the final file for symlinks; a planted `.oeo/sessions`
    # symlink is followed, so the snapshot is written outside the project (append_jsonl refuses the same case
    # for finops.jsonl).
    def test_a_symlinked_sessions_directory_is_never_written_through(self):
        (self.project / ".oeo").mkdir()
        elsewhere = self.tmp / "elsewhere"
        elsewhere.mkdir()
        try:
            os.symlink(elsewhere, self.sessions, target_is_directory=True)
        except (OSError, NotImplementedError):
            self.skipTest("symlinks unavailable")
        self.assertEqual(self.stop(), (0, ""))
        self.assertEqual(list(elsewhere.iterdir()), [])


# --------------------------------------------------------------------------- cost: main session + latest plan
class CostMainSessionTests(OeoProject):
    @staticmethod
    def usage(session="s1", agent="oeo:qa-verifier", inp=400, out=100, cache_read=99999, cache_write=50):
        return {"session_id": session, "agent_type": agent, "input_tokens": inp, "output_tokens": out,
                "cache_read_tokens": cache_read, "cache_write_tokens": cache_write}

    def plan(self, session, engagement, estimate, budget, role_estimate=None):
        roles = [{"id": "qa-verifier", "agent": "oeo:qa-verifier", "estimate_tokens": role_estimate}] if role_estimate else []
        row = {"session": session, "estimate_tokens": estimate, "budget_tokens": budget, "roles": roles}
        if engagement:
            row["engagement"] = engagement
        return row

    def test_main_session_tokens_and_the_all_in_total_are_reported(self):
        self.put_jsonl("activation-log.jsonl", [self.plan("s1", "E1", 1000, 5000)])
        self.put_jsonl("finops.jsonl", [self.usage()])
        self.assertNotIn("Main session", self.run_cli("cost")[1])      # no snapshot yet: no such line
        self.put("sessions/s1.json", json.dumps({"session_id": "s1", "total_tokens": 2000}))
        self.put("sessions/s2.json", json.dumps({"session_id": "s2", "total_tokens": 500}))
        code, out, _ = self.run_cli("cost")
        self.assertIsNone(code)
        self.assertIn("Total subagent tokens (input+output+cache writes): 550; planned 1,000; class budget 5,000", out)
        self.assertIn("Main session (orchestrator) tokens: 2,500 over 2 session(s); all-in total 3,050", out)
        out = self.run_cli("cost", "--session", "s1")[1]               # --session narrows the snapshots too
        self.assertIn("Main session (orchestrator) tokens: 2,000 over 1 session(s); all-in total 2,550", out)

    def test_a_retriage_counts_only_the_latest_plan_of_the_engagement(self):
        self.put_jsonl("activation-log.jsonl", [
            self.plan("s1", "E1", 1000, 5000, role_estimate=700),
            self.plan("s1", "E1", 2000, 6000, role_estimate=900),     # supersedes the first plan of E1
            self.plan("s1", "E2", 300, 400),
        ])
        self.put_jsonl("finops.jsonl", [self.usage()])
        out = self.run_cli("cost")[1]
        self.assertIn("planned 2,300; class budget 6,400", out)        # 2,000 + 300 and 6,000 + 400
        row = next(x for x in out.splitlines() if x.startswith("oeo:qa-verifier")).split()
        self.assertEqual(row[5], "900")                                # per-agent estimate: latest plan only
        self.assertNotIn("OVER ESTIMATE", out)
        # entries without an engagement (older logs) are superseded per session instead
        self.put_jsonl("activation-log.jsonl", [self.plan("s7", None, 100, 1000), self.plan("s7", None, 30, 40),
                                                self.plan("s8", None, 5, 6)])
        self.assertIn("planned 35; class budget 46", self.run_cli("cost")[1])

    # Regression (fixed): oeo.py:772 `json.loads` on every sessions/*.json is unguarded, so one unreadable snapshot makes
    # `oeo cost` raise JSONDecodeError (finops.jsonl lines and `oeo status` both skip bad data).
    def test_an_unreadable_session_snapshot_is_skipped(self):
        self.put_jsonl("activation-log.jsonl", [self.plan("s1", "E1", 1000, 5000)])
        self.put("sessions/bad.json", "{not json")
        self.put("sessions/s1.json", json.dumps({"session_id": "s1", "total_tokens": 2000}))
        code, out, _ = self.run_cli("cost")
        self.assertIsNone(code)
        self.assertIn("Main session (orchestrator) tokens: 2,000 over 1 session(s)", out)


if __name__ == "__main__":
    unittest.main()


class TemplateSlotTests(unittest.TestCase):
    def test_unfilled_template_slots_are_must_fix(self):
        # Regression (eval 20, OEO run): "[REPOSITORY URL]" slots reached the copy; QA caught them, the linter did not.
        for text in ("Install from [REPOSITORY URL].", "Star us at {{repo_url}}", "See <CHANGELOG LINK>."):
            with self.subTest(text=text):
                self.assertIn("must-fix", {f["severity"] for f in checks.copy_lint(text)})
        self.assertEqual(checks.copy_lint("Read the [docs](https://example.org) and [API] notes."), [])
