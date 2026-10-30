"""Stage 0 router (oeo.route), model resolution (oeo.effective_model / profile_name)."""
import copy
import json
import unittest

from ._common import IsolatedTestCase, oeo

CLASS_A_ROLES = {"junior-developer", "qa-verifier"}
CLASS_B_CORE = {"business-owner", "business-analyst", "project-manager", "cto",
                "technical-lead", "middle-developer", "qa-verifier", "oss-maintainer"}


class RouterTestCase(IsolatedTestCase):
    @classmethod
    def setUpClass(cls):
        cls.lock = oeo.load_lock()

    def route(self, task_type, **kwargs):
        return oeo.route(self.lock, task_type, **kwargs)

    @staticmethod
    def ids(plan, *tiers):
        return {r["id"] for r in plan["roles"] if not tiers or r["tier"] in tiers}

    @staticmethod
    def entry(plan, role_id):
        return next(r for r in plan["roles"] if r["id"] == role_id)


class ClassificationTests(RouterTestCase):
    def test_class_a_is_one_junior_developer_plus_one_verifier(self):
        plan = self.route("trivial", touches=["frontend", "ui", "docs"], files=1, lines=1)
        self.assertEqual((plan["class"], plan["rule"]), ("A", "trivial-change"))
        self.assertEqual(self.ids(plan), CLASS_A_ROLES)  # no Tier 2 even though ui domains are touched
        self.assertEqual({r["mode"] for r in plan["roles"]}, {"subagent"})
        self.assertEqual([g["id"] for g in plan["gates"]], ["diff-reviewed", "checks-pass"])
        self.assertLessEqual(plan["estimate_tokens"], plan["budget_tokens"])

    def test_class_a_is_refused_when_size_unknown_too_big_risky_or_triggered(self):
        cases = [
            ({"files": 2, "lines": 20}, "A"), ({"files": 0, "lines": 0}, "A"),   # inclusive boundaries
            ({"files": 3, "lines": 20}, "B"), ({"files": 2, "lines": 21}, "B"),
            ({}, "B"), ({"files": 1}, "B"), ({"lines": 5}, "B"),                  # size omitted -> not trivial
            ({"files": 1, "lines": 5, "signals": ["new-dependency"]}, "B"),       # a Tier 3 trigger fires
            ({"files": 1, "lines": 5, "touches": ["auth"]}, "C"),                 # risky domain wins
        ]
        for kwargs, expected in cases:
            with self.subTest(**kwargs):
                self.assertEqual(self.route("trivial", **kwargs)["class"], expected)
        plan = self.route("trivial", files=1, lines=5, signals=["new-dependency"])
        self.assertEqual(self.entry(plan, "legal-advisor")["reason"], "trigger: new-dependency")
        self.assertEqual(self.route("trivial")["rule"], "standard-default")

    def test_class_b_is_the_default_core_without_tier2(self):
        plan = self.route("feature")
        self.assertEqual((plan["class"], plan["rule"]), ("B", "standard-default"))
        self.assertEqual(self.ids(plan), CLASS_B_CORE)
        domains = ["frontend", "ui", "backend", "docs", "tests", "ci", "performance", "analytics", "i18n"]
        touched = self.route("bugfix", touches=domains)
        self.assertEqual(touched["class"], "B")
        self.assertEqual(self.ids(touched, 2), set())  # Tier 2 is a Class C feature
        self.assertEqual(self.entry(self.route("feature", signals=["production"]), "sre")["reason"],
                         "trigger: production")  # Tier 3 advisors still apply in B

    def test_class_c_triggers(self):
        for domain, spec in self.lock["routing"]["domains"].items():
            with self.subTest(domain=domain):
                plan = self.route("feature", touches=[domain])
                if spec["risky"]:
                    self.assertEqual((plan["class"], plan["rule"]), ("C", "risky-domain"))
                else:
                    self.assertEqual(plan["class"], "B")
        for signal in ["new-surface", "breaking-change", "high-risk", "ai-feature"]:
            with self.subTest(signal=signal):
                self.assertEqual(self.route("feature", signals=[signal])["rule"], "risk-signal")
        self.assertEqual(self.route("feature", signals=["user-facing"])["class"], "B")
        for task_type in ["architecture", "new-product", "incident"]:
            with self.subTest(type=task_type):
                self.assertEqual(self.route(task_type)["rule"], "significant-type")
        self.assertEqual(self.route("feature", files=16)["rule"], "large-change")
        self.assertEqual(self.route("feature", files=15)["class"], "B")

    def test_class_c_core_is_the_full_workflow(self):
        plan = self.route("feature", files=20)
        self.assertEqual(self.entry(plan, "senior-developer")["mode"], "subagent")
        self.assertEqual(self.entry(plan, "business-analyst")["mode"], "subagent")
        self.assertNotIn("middle-developer", self.ids(plan))
        gates = {g["id"] for g in plan["gates"]}
        self.assertTrue({"adr-recorded", "domain-reviews-passed", "business-review-passed"} <= gates)

    def test_class_d_for_organizational_types(self):
        # Release and licensing work always pass the legal gate; governance, community and
        # marketing edits do not (proportionality: no release gates without a release).
        for task_type, license_gates in [("release", 1), ("licensing", 1), ("governance", 0),
                                         ("community", 0), ("marketing", 0)]:
            with self.subTest(type=task_type):
                plan = self.route(task_type)
                self.assertEqual((plan["class"], plan["rule"]), ("D", "organizational-work"))
                self.assertTrue({"business-owner", "project-manager", "oss-maintainer", "qa-verifier"} <= self.ids(plan))
                gates = [g["id"] for g in plan["gates"]]
                self.assertEqual(gates.count("license-gate"), license_gates)
                self.assertEqual("rollback-plan" in gates, task_type == "release")
        plan = self.route("release", touches=["auth", "database"], files=40)  # D outranks risky domain / size
        self.assertEqual(plan["class"], "D")
        self.assertEqual(self.ids(plan, 2), set())


class ActivationTests(RouterTestCase):
    def test_research_type_drops_developers_and_code_gates(self):
        # Regression (fixed): found by content review - research requests were sent to a code developer.
        plan = self.route("research", signals=["external-research"])
        self.assertFalse({"junior-developer", "middle-developer", "senior-developer"} & self.ids(plan))
        self.assertIn("market-researcher", self.ids(plan, 3))
        self.assertEqual(self.entry(plan, "market-researcher")["agent"], "oeo:researcher")
        gates = {g["id"] for g in plan["gates"]}
        self.assertFalse({"diff-reviewed", "checks-pass", "regression-test"} & gates)
        self.assertNotIn("5 Design & Implementation", plan["stages"])

    def test_tier2_activation_by_domain_in_class_c(self):
        cases = [
            (["auth"], {}, "security-engineer", "domain: auth"),
            (["payments"], {}, "security-engineer", "domain: payments"),
            (["database"], {}, "database-engineer", "domain: database"),
            (["api"], {}, "api-designer", "domain: api"),
            (["infra"], {}, "platform-engineer", "domain: infra"),
            (["infra"], {}, "technical-architect", "domain: infra"),
            (["frontend"], {"files": 16}, "senior-frontend-engineer", "domain: frontend"),
            (["docs"], {"files": 16}, "technical-writer", "domain: docs"),
            (["performance"], {"files": 16}, "performance-engineer", "domain: performance"),
        ]
        for touches, extra, role, reason in cases:
            with self.subTest(role=role, touches=touches):
                plan = self.route("feature", touches=touches, **extra)
                self.assertEqual(plan["class"], "C")
                self.assertEqual(self.entry(plan, role)["reason"], reason)

    def test_tier2_edge_cases(self):
        # signals and types count as activation keys, not only domains
        self.assertIn("principal-engineer", self.ids(self.route("feature", signals=["breaking-change"])))
        self.assertIn("design-lead", self.ids(self.route("feature", signals=["new-surface"])))
        self.assertIn("technical-architect", self.ids(self.route("new-product")))
        # Class C without a matching domain gets no Tier 2
        large = self.route("feature", files=20)
        self.assertEqual((large["class"], self.ids(large, 2)), ("C", set()))
        # roles delegated by the senior frontend engineer are never routed directly
        everything = self.route("architecture", touches=list(self.lock["routing"]["domains"]),
                                signals=list(self.lock["routing"]["signals"]))
        self.assertIn("senior-frontend-engineer", self.ids(everything))
        self.assertTrue({"junior-frontend-engineer", "middle-frontend-engineer"}.isdisjoint(self.ids(everything)))

    def test_tier3_triggers_compound_type_and_unless(self):
        for signals, expected in [(["user-facing"], False), (["release"], False), (["user-facing", "release"], True)]:
            with self.subTest(signals=signals):  # 'user-facing+release' needs both
                self.assertEqual("a11y-auditor" in self.ids(self.route("feature", signals=signals)), expected)
        both = self.route("feature", signals=["user-facing", "release"])
        self.assertEqual(self.entry(both, "a11y-auditor")["reason"], "trigger: user-facing+release")
        for task_type, role in [("incident", "incident-commander"), ("release", "release-manager"),
                                ("licensing", "legal-advisor"), ("community", "developer-advocate")]:
            with self.subTest(type=task_type):  # a task type can be the trigger
                self.assertIn(role, self.ids(self.route(task_type)))
        plain = self.route("feature", signals=["new-surface"])
        researched = self.route("feature", signals=["new-surface", "research-exists"])
        self.assertIn("ux-researcher", self.ids(plain))
        self.assertNotIn("ux-researcher", self.ids(researched))      # `unless` suppresses the advisor
        self.assertIn("design-lead", self.ids(researched))            # the Tier 2 designer is unaffected

    def test_derived_multi_agent_signal_activates_finops_only_in_class_c(self):
        plan_c = self.route("feature", touches=["auth"])
        self.assertEqual(self.entry(plan_c, "finops-controller")["reason"], "trigger: multi-agent")
        self.assertIn("oeo:finops", plan_c["skills"])
        for label, plan in [("A", self.route("trivial", files=1, lines=1)), ("B", self.route("feature")),
                            ("D", self.route("release"))]:
            with self.subTest(cls=label):
                self.assertNotIn("finops-controller", self.ids(plan))
        # an explicit signal is honoured wherever Tier 3 is enabled
        self.assertIn("finops-controller", self.ids(self.route("feature", signals=["multi-agent"])))

    def test_license_gate_follows_every_legal_advisor_trigger(self):
        routing = self.lock["routing"]
        triggers = self.lock["roles"]["legal-advisor"]["activation"]["triggers"]
        self.assertTrue(triggers)
        for trigger in triggers:
            with self.subTest(trigger=trigger):
                if trigger in routing["types"]:
                    plan = self.route(trigger)
                else:
                    plan = self.route("feature", signals=[trigger])
                self.assertIn("legal-advisor", self.ids(plan))
                gates = [g["id"] for g in plan["gates"]]
                self.assertEqual(gates.count("license-gate"), 1)
                self.assertTrue(all(g["check"] for g in plan["gates"]))
        self.assertNotIn("license-gate", [g["id"] for g in self.route("feature")["gates"]])

    def test_fact_rules_add_release_gates_and_stage_outside_class_a(self):
        # a failed-release incident is Class C but still needs rollback plan, changelog and version
        incident = self.route("incident", signals=["release"])
        self.assertEqual(incident["class"], "C")
        gates = [g["id"] for g in incident["gates"]]
        for gate in ("changelog-entry", "version-bump", "rollback-plan"):
            self.assertEqual(gates.count(gate), 1)
        names = [s.split(" ", 1)[1] for s in incident["stages"]]
        self.assertIn("Release", names)
        workflow_order = [s["name"] for s in self.lock["workflow"]["stages"]]
        self.assertEqual(names, sorted(names, key=workflow_order.index))  # stages stay in workflow order
        self.assertLess(names.index("Release"), names.index("Business Outcome Review"))
        feature = self.route("feature", signals=["release"])
        self.assertEqual(feature["class"], "B")
        self.assertIn("rollback-plan", [g["id"] for g in feature["gates"]])
        self.assertNotIn("rollback-plan", [g["id"] for g in self.route("feature")["gates"]])
        class_d = self.route("release")  # already has these gates and stage: no duplicates
        self.assertEqual(len(class_d["stages"]), len(set(class_d["stages"])))


class ValidationAndShapeTests(RouterTestCase):
    def test_unknown_type_domain_or_signal_raises_value_error(self):
        cases = [
            ({"task_type": "bogus"}, ["type 'bogus'"]),
            ({"task_type": "feature", "touches": ["bogus"]}, ["domain 'bogus'"]),
            ({"task_type": "feature", "signals": ["bogus"]}, ["signal 'bogus'"]),
            ({"task_type": "feature", "touches": ["feature"]}, ["domain 'feature'"]),  # a type is not a domain
            ({"task_type": "auth"}, ["type 'auth'"]),                                   # a domain is not a type
            ({"task_type": "nope", "touches": ["x"], "signals": ["y"]}, ["type 'nope'", "domain 'x'", "signal 'y'"]),
        ]
        for kwargs, fragments in cases:
            with self.subTest(kwargs=kwargs):
                with self.assertRaises(ValueError) as ctx:
                    self.route(**kwargs)
                for fragment in fragments:
                    self.assertIn(fragment, str(ctx.exception))

    def test_subagent_entries_carry_agent_model_and_estimate(self):
        plan = self.route("feature", touches=["auth", "database"], signals=["new-surface"])
        budgets = self.lock["models"]["budgets"]["per_invocation_tokens"]
        total = 0
        for r in plan["roles"]:
            if r["mode"] == "subagent":
                contract = self.lock["roles"][r["id"]]
                self.assertEqual(r["agent"], f"oeo:{contract['agent']}")
                self.assertIn(r["model"], {"haiku", "sonnet", "opus"})
                self.assertEqual(r["estimate_tokens"], budgets[r["effort"]])
                total += r["estimate_tokens"]
            else:
                for key in ("agent", "model", "estimate_tokens"):
                    self.assertNotIn(key, r)
        self.assertEqual(plan["estimate_tokens"], total)
        self.assertEqual(self.entry(plan, "security-engineer")["agent"], "oeo:security-engineer")
        self.assertEqual(self.entry(plan, "database-engineer")["agent"], "oeo:specialist")
        self.assertEqual(self.entry(plan, "ux-researcher")["agent"], "oeo:advisor")
        self.assertEqual(self.entry(plan, "senior-developer")["model"], "opus")
        self.assertEqual(self.entry(plan, "qa-verifier")["model"], "sonnet")

    def test_economy_profile_downshifts_one_tier(self):
        default = self.route("feature", touches=["auth"], profile="default")
        economy = self.route("feature", touches=["auth"], profile="economy")
        self.assertEqual((default["profile"], economy["profile"]), ("default", "economy"))
        self.assertEqual(self.entry(default, "senior-developer")["model"], "opus")      # advanced
        self.assertEqual(self.entry(economy, "senior-developer")["model"], "sonnet")    # advanced -> sonnet
        self.assertEqual(self.entry(default, "qa-verifier")["model"], "sonnet")         # standard
        self.assertEqual(self.entry(economy, "qa-verifier")["model"], "haiku")          # standard -> haiku
        self.assertEqual(self.entry(economy, "qa-verifier")["model_id"],
                         self.lock["models"]["profiles"]["economy"]["tiers"]["standard"]["model_id"])
        self.assertEqual(self.ids(default), self.ids(economy))
        self.assertEqual(default["estimate_tokens"], economy["estimate_tokens"])

    def test_profile_env_var_is_honoured_and_unknown_profile_exits(self):
        import os
        os.environ["OEO_MODEL_PROFILE"] = "economy"
        plan = self.route("feature")
        self.assertEqual(plan["profile"], "economy")
        self.assertEqual(self.entry(plan, "middle-developer")["model"], "haiku")
        self.assertEqual(self.route("feature", profile="default")["profile"], "default")  # explicit wins
        with self.assertRaises(SystemExit) as ctx:
            self.route("feature", profile="nope")
        self.assertIn("unknown model profile 'nope'", str(ctx.exception.code))
        os.environ["OEO_MODEL_PROFILE"] = "also-nope"
        with self.assertRaises(SystemExit):
            self.route("feature")

    def test_routing_is_deterministic_pure_and_order_independent(self):
        lock_before = copy.deepcopy(self.lock)
        kwargs = dict(touches=["database", "auth", "frontend"], signals=["new-dependency", "multi-agent", "release"],
                      files=3, lines=10)
        first, second = self.route("feature", **kwargs), self.route("feature", **kwargs)
        self.assertEqual(json.dumps(first), json.dumps(second))
        shuffled = dict(kwargs, touches=list(reversed(kwargs["touches"])), signals=list(reversed(kwargs["signals"])))
        self.assertEqual(self.route("feature", **shuffled), first)
        self.assertEqual(self.lock, lock_before)  # route() must not mutate the lock

    def test_plan_invariants_over_an_input_matrix(self):
        all_roles = set(self.lock["roles"])
        for task_type in self.lock["routing"]["types"]:
            for touches in ([], ["auth"], ["frontend", "docs"]):
                for signals in ([], ["new-dependency", "user-facing"]):
                    with self.subTest(type=task_type, touches=touches, signals=signals):
                        plan = self.route(task_type, touches=touches, signals=signals)
                        active = self.ids(plan)
                        self.assertIn(plan["class"], "ABCD")
                        self.assertEqual(active | set(plan["not_activated"]), all_roles)
                        self.assertTrue(active.isdisjoint(plan["not_activated"]))
                        keys = [(r["tier"], r["id"]) for r in plan["roles"]]
                        self.assertEqual(keys, sorted(keys))
                        gate_ids = [g["id"] for g in plan["gates"]]
                        self.assertEqual(len(gate_ids), len(set(gate_ids)))
                        if "legal-advisor" in active:
                            self.assertIn("license-gate", gate_ids)
                        self.assertEqual(len(plan["stages"]), len(set(plan["stages"])))
                        self.assertIn("qa-verifier", active)
                        self.assertEqual(plan["estimate_tokens"],
                                         sum(r.get("estimate_tokens", 0) for r in plan["roles"]))
                        json.dumps(plan)  # must be serialisable

    def test_skills_adapters_and_text_rendering(self):
        class_a = self.route("trivial", touches=["frontend"], files=1, lines=1)
        self.assertEqual(class_a["optional_adapters"], [])  # no third-party suggestions for trivial work
        self.assertIn("oeo:design-direction", class_a["skills"])
        plan = self.route("bugfix", touches=["frontend", "ui"])
        self.assertTrue({"frontend-design", "impeccable", "superpowers"} <= set(plan["optional_adapters"]))
        self.assertEqual(len(plan["optional_adapters"]), len(set(plan["optional_adapters"])))
        with_release = self.route("feature", signals=["release"])
        self.assertIn("oeo:release", with_release["skills"])
        self.assertEqual(len(with_release["skills"]), len(set(with_release["skills"])))
        text = oeo.format_plan(class_a)
        self.assertIn("OEO triage: Class A (Trivial)", text)
        self.assertIn("oeo:junior-developer", text)
        self.assertIn(f"est {class_a['estimate_tokens']:,} subagent tokens of {class_a['budget_tokens']:,}", text)


class EffectiveModelTests(unittest.TestCase):
    MODELS = {
        "default_profile": "p1",
        "profiles": {
            "p1": {"tiers": {"light": {"model_id": "m-l", "host_alias": "l"},
                             "standard": {"model_id": "m-s", "host_alias": "s"},
                             "advanced": {"model_id": "m-a", "host_alias": "a"}}},
            "p2": {"tiers": {"light": {"model_id": "n-l", "host_alias": "nl"},
                             "standard": {"model_id": "n-s", "host_alias": "ns"},
                             "advanced": {"model_id": "n-a", "host_alias": "na"}}},
        },
        "overrides": {"all": {"r": {"effort": "high"}}, "p1": {"r": {"preferred_model": "advanced"}}},
    }
    CONTRACT = {"preferred_model": "light", "effort": "low", "escalate_to": "human"}

    def test_contract_values_and_override_merging(self):
        got = oeo.effective_model(self.CONTRACT, "other-role", self.MODELS, "p1")
        self.assertEqual((got["tier"], got["effort"], got["host_alias"], got["model_id"], got["escalate_to"]),
                         ("light", "low", "l", "m-l", "human"))
        p1 = oeo.effective_model(self.CONTRACT, "r", self.MODELS, "p1")  # "all" + profile override, profile wins
        self.assertEqual((p1["tier"], p1["effort"], p1["host_alias"]), ("advanced", "high", "a"))
        p2 = oeo.effective_model(self.CONTRACT, "r", self.MODELS, "p2")  # only the "all" override applies
        self.assertEqual((p2["tier"], p2["effort"], p2["host_alias"]), ("light", "high", "nl"))
        for overrides in (None, {}, {"all": None}, {"p1": None}):
            with self.subTest(overrides=overrides):
                models = dict(self.MODELS, overrides=overrides)
                self.assertEqual(oeo.effective_model(self.CONTRACT, "r", models, "p1")["tier"], "light")

    def test_profile_name_precedence(self):
        import os
        from unittest import mock
        with mock.patch.dict(os.environ, {"OEO_MODEL_PROFILE": "p2"}):
            self.assertEqual(oeo.profile_name(self.MODELS), "p2")
            self.assertEqual(oeo.profile_name(self.MODELS, "p1"), "p1")
        with mock.patch.dict(os.environ):
            os.environ.pop("OEO_MODEL_PROFILE", None)
            self.assertEqual(oeo.profile_name(self.MODELS), "p1")
            with self.assertRaises(SystemExit):
                oeo.profile_name(self.MODELS, "missing")


if __name__ == "__main__":
    unittest.main()
