"""Schema subset validator, source validation, registry/legal gate, and the generated outputs."""
import copy
import json
import unittest

from ._common import IsolatedTestCase, ROOT, oeo


def role(src, role_id):
    return src["roles"][role_id]["role"]


class SchemaErrorsTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.schema = json.loads((ROOT / "schemas" / "role.schema.json").read_text(encoding="utf-8"))
        cls.doc = oeo.load_sources()["roles"]["qa-verifier"]

    def errors(self, mutate):
        doc = copy.deepcopy(self.doc)
        mutate(doc["role"])
        return oeo.schema_errors(doc, self.schema)

    def test_valid_contract_and_empty_schema_have_no_errors(self):
        self.assertEqual(oeo.schema_errors(self.doc, self.schema), [])
        self.assertEqual(oeo.schema_errors({"a": [1, "x", None]}, {}), [])

    def test_missing_required_and_unexpected_keys(self):
        self.assertEqual(self.errors(lambda r: r.pop("purpose")), ["$.role: missing 'purpose'"])
        self.assertEqual(oeo.schema_errors({}, self.schema), ["$: missing 'role'"])
        self.assertEqual(self.errors(lambda r: r.update(bogus=1)), ["$.role: unexpected key 'bogus'"])
        self.assertEqual(self.errors(lambda r: r["model_routing"].update(bogus=1)),
                         ["$.role.model_routing: unexpected key 'bogus'"])
        self.assertEqual(oeo.schema_errors({"role": self.doc["role"], "x": 1}, self.schema),
                         ["$: unexpected key 'x'"])

    def test_enum_and_pattern_violations(self):
        self.assertEqual(self.errors(lambda r: r.update(tier=4)), ["$.role.tier: 4 not in [1, 2, 3]"])
        errs = self.errors(lambda r: r["model_routing"].update(effort="extreme"))
        self.assertEqual(len(errs), 1)
        self.assertTrue(errs[0].startswith("$.role.model_routing.effort: 'extreme' not in"))
        errs = self.errors(lambda r: r.update(id="Bad_ID"))
        self.assertEqual(len(errs), 1)
        self.assertIn("$.role.id: 'Bad_ID' does not match", errs[0])
        errs = self.errors(lambda r: r.update(consults=["ok-role", "Not A Role"]))
        self.assertTrue(errs and errs[0].startswith("$.role.consults[1]: 'Not A Role' does not match"))

    def test_wrong_types(self):
        for value in ("2", 2.0, True):  # a bool is not an integer
            with self.subTest(tier=value):
                self.assertEqual(self.errors(lambda r: r.update(tier=value)), ["$.role.tier: expected integer"])
        self.assertEqual(self.errors(lambda r: r.update(responsibilities="text")),
                         ["$.role.responsibilities: expected array"])
        self.assertEqual(self.errors(lambda r: r.update(id=5)), ["$.role.id: expected string"])
        self.assertEqual(oeo.schema_errors({"role": []}, self.schema), ["$.role: expected object"])

    def test_min_items_and_string_length_bounds_with_nested_paths(self):
        self.assertEqual(self.errors(lambda r: r.update(responsibilities=["only one item"])),
                         ["$.role.responsibilities: needs at least 2 items"])
        self.assertEqual(self.errors(lambda r: r.update(inputs=[])), ["$.role.inputs: needs at least 1 items"])
        self.assertEqual(self.errors(lambda r: r.update(purpose="too short")), ["$.role.purpose: shorter than 20"])
        self.assertEqual(self.errors(lambda r: r.update(purpose="x" * 301)), ["$.role.purpose: longer than 300"])
        errs = self.errors(lambda r: r["responsibilities"].__setitem__(1, "abc"))
        self.assertEqual(errs, ["$.role.responsibilities[1]: shorter than 5"])


class ValidateSourcesTests(IsolatedTestCase):
    @classmethod
    def setUpClass(cls):
        cls.src = oeo.load_sources()

    def test_repository_validates_cleanly(self):
        self.assertEqual(oeo.validate_sources(self.src), [])

    def test_each_mutation_produces_its_specific_error(self):
        def first_veto_category(s):
            return next(c for c in s["decisions"]["categories"] if c["veto"])

        mutations = [
            ("unknown consults ref", lambda s: role(s, "cto")["consults"].append("ghost-role"),
             "org/roles/cto.yaml: consults references unknown or self role 'ghost-role'"),
            ("self informs", lambda s: role(s, "cto")["informs"].append("cto"),
             "informs references unknown or self role 'cto'"),
            ("tier 3 without triggers", lambda s: role(s, "release-manager").update(activation={}),
             "org/roles/release-manager.yaml: Tier 3 roles need activation.triggers"),
            ("tier 2 without domains", lambda s: role(s, "security-engineer").update(activation={}),
             "Tier 2 roles need activation.domains or activation.delegated_by"),
            ("tier 1 with activation", lambda s: role(s, "cto").update(activation={"domains": ["auth"]}),
             "org/roles/cto.yaml: Tier 1 roles are activated by class, not by 'activation'"),
            ("unknown activation domain", lambda s: role(s, "security-engineer")["activation"]["domains"].append("nowhere"),
             "activation key 'nowhere' is not a type, domain or signal"),
            ("unknown part of a compound trigger", lambda s: role(s, "release-manager").update(
                activation={"triggers": ["release+nonsense"]}), "activation key 'nonsense'"),
            ("unknown delegator", lambda s: role(s, "junior-frontend-engineer")["activation"].update(delegated_by="nobody"),
             "delegated_by 'nobody' is not a role"),
            ("subagent without agent", lambda s: role(s, "qa-verifier").pop("agent"),
             "org/roles/qa-verifier.yaml: subagent roles must name an agent"),
            ("unknown generic agent", lambda s: role(s, "ux-researcher").update(agent="wizard"),
             "agent 'wizard' must be the role id (dedicated) or a generic agent"),
            ("id differs from file name", lambda s: role(s, "cto").update(id="cto2"),
             "id 'cto2' must match file name"),
            ("unknown relevant skill", lambda s: role(s, "cto")["relevant_skills"].append("oeo:nonexistent"),
             "relevant skill 'oeo:nonexistent' is neither an oeo skill nor a registered adapter"),
            ("schema violation is path-prefixed", lambda s: role(s, "cto").update(tier=9),
             "org/roles/cto.yaml: $.role.tier: 9 not in [1, 2, 3]"),
            ("class references unknown role", lambda s: s["routing"]["classes"]["B"]["roles"].update(ghost="subagent"),
             "org/routing.yaml classes.B: unknown role 'ghost'"),
            ("class role with bad mode", lambda s: s["routing"]["classes"]["A"]["roles"].update({"junior-developer": "wizard"}),
             "classes.A: bad mode 'wizard'"),
            ("class references unknown stage and gate", lambda s: (
                s["routing"]["classes"]["A"]["stages"].append("no-stage"),
                s["routing"]["classes"]["A"]["gates"].append("no-gate")), "unknown stage 'no-stage'"),
            ("fact rule for an unknown fact", lambda s: s["routing"]["fact_rules"].update(bogus={"gates": []}),
             "fact_rules: 'bogus' is not a type, domain or signal"),
            ("fact rule with unknown gate", lambda s: s["routing"]["fact_rules"]["release"]["gates"].append("no-gate"),
             "fact_rules.release: unknown gate 'no-gate'"),
            ("fact rule with unknown stage", lambda s: s["routing"]["fact_rules"]["release"]["stages"].append("no-stage"),
             "fact_rules.release: unknown stage 'no-stage'"),
            ("rule targets unknown class", lambda s: s["routing"]["classification"][0].update({"class": "Z"}),
             "targets unknown class"),
            ("developer_by_class unknown role", lambda s: s["routing"]["developer_by_class"].update(B="ghost"),
             "developer_by_class.B: unknown role 'ghost'"),
            ("unknown oeo skill in routing", lambda s: s["routing"]["skills"]["by_class"]["A"].append("oeo:nonexistent"),
             "skills.by_class.A: unknown skill 'oeo:nonexistent'"),
            ("adapter not in registry", lambda s: s["routing"]["skills"]["adapters"]["by_type"]["bugfix"].append("unregistered"),
             "'unregistered' not in third_party/registry.yaml"),
            ("workflow stage owner is not a role", lambda s: s["workflow"]["stages"][0].update(owner="ghost"),
             "owner 'ghost' is not a role"),
            ("decision category with unknown role", lambda s: s["decisions"]["categories"][0].update(decides="ghost"),
             "org/decision-rights.yaml business-scope: unknown role 'ghost'"),
            ("decision category with unknown group", lambda s: s["decisions"]["categories"][0]["informed"].append("@nogroup"),
             "unknown group '@nogroup'"),
            ("duplicate decision category", lambda s: s["decisions"]["categories"].append(
                copy.deepcopy(s["decisions"]["categories"][0])), "business-scope: duplicate category"),
            ("veto without grounds", lambda s: first_veto_category(s)["veto"][0].update(grounds=""),
             "every veto needs written grounds"),
            ("decision group with unknown member", lambda s: s["decisions"]["groups"]["leads"].append("ghost"),
             "groups.leads: unknown role 'ghost'"),
            ("model profile missing a tier", lambda s: s["models"]["profiles"]["economy"]["tiers"].pop("light"),
             "profile 'economy': missing tiers ['light']"),
            ("model override for unknown role / bad tier", lambda s: s["models"].update(
                overrides={"all": {"ghost": {"preferred_model": "mega"}}}), "overrides.all: unknown role 'ghost'"),
            ("registry: blocked license vendored", lambda s: s["registry"]["resources"][0].update(
                license_spdx="GPL-3.0-only", distribution="vendored"),
             "blocked license 'GPL-3.0-only' cannot be vendored (legal gate)"),
        ]
        for name, mutate, expected in mutations:
            with self.subTest(mutation=name):
                src = copy.deepcopy(self.src)
                mutate(src)
                errors = oeo.validate_sources(src)
                self.assertTrue(any(expected in e for e in errors), f"{expected!r} not in {errors}")
        self.assertEqual(oeo.validate_sources(self.src), [])  # the shared fixture was never mutated

    def test_text_patterns_used_by_validation(self):
        # validate_sources scans role YAML text on disk, so exercise the pattern it uses
        for text in ("runs on claude-sonnet-5-5", "use Opus here", "gpt-4o", "gemini-2.5-pro", "a haiku"):
            with self.subTest(provider_name=text):
                self.assertIsNotNone(oeo.PROVIDER_NAMES.search(text))
        for text in ("tier standard, effort medium", "advanced reasoning", "opusculum is not a model"):
            with self.subTest(not_a_provider_name=text):
                self.assertIsNone(oeo.PROVIDER_NAMES.search(text))
        links = "[a](docs/x.md) [b](https://e.org) [c](#frag) [d](mailto:x@y.z) [e](../y.md#sec)"
        self.assertEqual(oeo.LINK.findall(links), ["docs/x.md", "../y.md#sec"])  # only relative links are checked


class RegistryTests(unittest.TestCase):
    POLICY = {"allowed": ["MIT", "Apache-2.0"], "review": ["MPL-2.0"], "blocked": ["GPL-3.0-only"]}

    def entry(self, **over):
        base = {f: "x" for f in oeo.REGISTRY_FIELDS}
        base.update(id="thing", license_spdx="MIT", distribution="reference-only", status="partially-verified")
        base.update(over)
        return base

    def errors(self, **over):
        return oeo.validate_registry({"resources": [self.entry(**over)]}, self.POLICY)

    def test_clean_entry_and_reference_only_exception(self):
        self.assertEqual(self.errors(), [])
        # reference-only never redistributes anything, so even a blocked license is fine
        self.assertEqual(self.errors(license_spdx="GPL-3.0-only"), [])

    def test_blocked_review_and_unknown_licenses_cannot_be_vendored_or_depended_on(self):
        for spdx, verdict in [("GPL-3.0-only", "blocked"), ("MPL-2.0", "review"), ("Foo-1.0", "blocked")]:
            for dist in ("vendored", "dependency"):
                with self.subTest(spdx=spdx, distribution=dist):
                    self.assertEqual(self.errors(license_spdx=spdx, distribution=dist),
                                     [f"third_party/registry.yaml thing: {verdict} license '{spdx}' cannot be {dist} (legal gate)"])
        self.assertEqual(self.errors(license_spdx="Apache-2.0", distribution="vendored"), [])

    def test_missing_fields_bad_distribution_and_unevidenced_verified_status(self):
        entry = self.entry()
        del entry["rationale"]
        errs = oeo.validate_registry({"resources": [entry]}, self.POLICY)
        self.assertEqual(errs, ["third_party/registry.yaml thing: missing 'rationale'"])
        self.assertIn("distribution must be reference-only, vendored or dependency", self.errors(distribution="copied")[0])
        self.assertEqual(self.errors(status="verified"),
                         ["third_party/registry.yaml thing: verified entries need license_evidence_url"])
        self.assertEqual(self.errors(status="verified", license_evidence_url="https://example.org/LICENSE"), [])


class BuildOutputsTests(IsolatedTestCase):
    @classmethod
    def setUpClass(cls):
        cls.src = oeo.load_sources()

    def test_generated_files_on_disk_are_fresh(self):
        outputs = oeo.build_outputs(self.src)
        self.assertIn("org/org.lock.json", outputs)
        self.assertIn("docs/roles.md", outputs)
        self.assertIn("THIRD_PARTY.md", outputs)
        for rel, content in outputs.items():
            with self.subTest(file=rel):
                self.assertEqual((ROOT / rel).read_text(encoding="utf-8"), content,
                                 f"{rel} is stale: run `python3 scripts/oeo.py build`")
        expected_agents = {rel for rel in outputs if rel.startswith("agents/")}
        on_disk = {str(p.relative_to(ROOT)) for p in (ROOT / "agents").glob("*.md")}
        self.assertEqual(on_disk, expected_agents)  # no missing and no orphaned agent files

    def test_build_is_deterministic_and_profile_only_changes_model_frontmatter(self):
        default = oeo.build_outputs(self.src)
        self.assertEqual(default, oeo.build_outputs(copy.deepcopy(self.src)))
        economy = oeo.build_outputs(self.src, "economy")
        self.assertIn("model: opus\n", default["agents/security-engineer.md"])
        self.assertIn("model: sonnet\n", economy["agents/security-engineer.md"])
        self.assertEqual(default["org/org.lock.json"], economy["org/org.lock.json"])
        lock = json.loads(default["org/org.lock.json"])
        self.assertEqual(set(lock["roles"]), set(self.src["roles"]))

    def test_render_agent_dedupes_tools_and_marks_the_file_generated(self):
        text = oeo.render_agent("demo", "A \"quoted\" description", ["read", "search", "edit", "read"],
                                "haiku", "low", "blue", "Body text.\n\n", "org/roles/demo.yaml")
        lines = text.splitlines()
        self.assertEqual(lines[0], "---")
        self.assertIn('description: "A \\"quoted\\" description"', lines)
        self.assertIn("tools: Read, Grep, Glob, Edit, Write", lines)
        self.assertIn("model: haiku", lines)
        self.assertIn("GENERATED by scripts/oeo.py build from org/roles/demo.yaml", text)
        self.assertTrue(text.endswith("Body text.\n"))


class KnownBugTests(IsolatedTestCase):
    """Genuine defects found by the suite (found by this suite and fixed; kept as regression tests)."""

    # Regression (fixed): scripts/oeo.py:422-427 - overrides scopes are never checked against "all" or a defined
    # profile, so a typo such as `overrides.ecnomy` validates cleanly and is silently never applied.
    def test_bug_override_scope_must_be_all_or_a_known_profile(self):
        src = copy.deepcopy(oeo.load_sources())
        src["models"]["overrides"]["ecnomy"] = {"qa-verifier": {"preferred_model": "advanced", "effort": "high"}}
        self.assertTrue(oeo.validate_sources(src), "unknown override scope 'ecnomy' was accepted")


if __name__ == "__main__":
    unittest.main()
