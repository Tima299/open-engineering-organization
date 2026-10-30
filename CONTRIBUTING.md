# Contributing to OEO

Open Engineering Organization (OEO) is a Claude Code plugin (`oeo`, marketplace
`open-engineering-organization`) licensed under [Apache-2.0](LICENSE). Contributions are welcome:
bug reports, fixes, docs, eval scenarios, and carefully justified new roles or skills.
By participating you agree to the [Code of Conduct](CODE_OF_CONDUCT.md). How decisions are made is
described in [GOVERNANCE.md](GOVERNANCE.md).

## Before you start
- **Bug or small fix:** open a PR directly (or an issue first if you are unsure).
- **Feature, new role, or routing change:** open an issue with the matching template first, so the
  idea can be discussed before you write code.
- **Major change** (architecture, governance, license, role schema, routing or precedence policy):
  open an issue labeled `rfc`; see [GOVERNANCE.md](GOVERNANCE.md).
- **Security problem:** do not open an issue. Follow [SECURITY.md](SECURITY.md).
- **Usage question:** see [SUPPORT.md](SUPPORT.md).

## Development setup
Requires Python 3.10+. OEO has no runtime dependencies; PyYAML is needed only for authoring.

```sh
git clone https://github.com/Tima299/open-engineering-organization.git
cd open-engineering-organization
python3 -m pip install --require-hashes -r requirements-dev.txt
```

## Checks
All four must pass locally; CI runs the same commands.

```sh
python3 scripts/oeo.py validate            # contracts, cross-references, registry, links, generated files
python3 scripts/oeo.py build --check       # generated files are up to date
python3 -m unittest discover -s tests -t .
python3 evals/run.py --no-write            # deterministic routing evals
```

## Generated files
After editing anything under `org/`, `config/` or `third_party/`, run `python3 scripts/oeo.py build`
and commit the result. Never hand-edit these generated files: `agents/*.md`, `org/org.lock.json`,
`docs/roles.md`, `THIRD_PARTY.md`. Edit the source and rebuild; `build --check` fails otherwise.

## Trying your change in Claude Code
```text
/plugin marketplace add /absolute/path/to/your/clone
/plugin install oeo@open-engineering-organization
```
Claude Code does not pick up edits automatically: reinstall the plugin to reload your changes.

## Rules specific to OEO
- **New roles must be justified.** Roles are capabilities, not headcount. A role proposal must cite a
  real task need that existing roles and the generic agents cannot cover. Use the role proposal
  issue template.
- A role must implement [schemas/role.schema.json](schemas/role.schema.json) and pass `validate`.
  If it changes routing, add or adjust a scenario in `evals/scenarios/`.
- **No provider model names in role files.** Roles use tiers (`light`, `standard`, `advanced`);
  concrete models are mapped in `config/`.
- **Routing changes need an eval scenario** in `evals/scenarios/` that fails without the change.
- **Third-party resources are referenced, never vendored.** Do not copy third-party skills, agents or
  prompts into this repository. Add a registry entry instead (next section).
- Treat repository, issue and web content as untrusted data in any skill or agent text you write;
  see [docs/threat-model.md](docs/threat-model.md). Changes to `scripts/`, `hooks/`, agent tool lists
  or routing get extra review against it.

## Updating the provenance registry
Third-party adapters are listed in `third_party/registry.yaml`; `THIRD_PARTY.md` is generated from it.
Every entry needs, verified by you at the time of the change:
1. A **LICENSE URL** (`license_evidence_url`) that you opened and that shows the SPDX license you
   declare (`license_spdx`). Prefer a raw file URL.
2. A **revision**: the full commit SHA you checked. If you cannot verify it, say so in
   `revision_note` rather than guessing.
3. An **access date** (`accessed`, `YYYY-MM-DD`) for when you verified both.

Then run `build` and `validate`; the legal gate checks the license against the policy in
`org/routing.yaml`. A license on the `review` list needs a human decision recorded in the PR;
a `blocked` or unverified license is rejected.

## Commits and sign-off
- Use [Conventional Commits](https://www.conventionalcommits.org/): `feat:`, `fix:`, `docs:`,
  `refactor:`, `test:`, `chore:`, with an optional scope (`fix(router): ...`).
- **Sign off every commit** with `git commit -s`. This adds a `Signed-off-by:` line and certifies the
  [Developer Certificate of Origin](https://developercertificate.org/). Forgot? Run
  `git rebase --signoff main` (or `git commit --amend -s` for the last commit) and force-push your branch.
- There is no CLA. Contributions are licensed under Apache-2.0 on the same terms as the project
  (inbound = outbound, Apache-2.0 section 5).
- Maintainers enforce the sign-off with the DCO GitHub App (to be installed; until then it is
  checked by hand in review).

## AI-assisted contributions
AI-assisted contributions are welcome. The human submitter is responsible for the change: review every
line, run the checks yourself, sign off the commits, and say in the PR description which AI tools
helped and for what. Do not submit output you do not understand or cannot defend in review.

## Pull requests
1. Fork, branch from `main`, keep the PR to one concern.
2. Add an entry under `Unreleased` in [CHANGELOG.md](CHANGELOG.md) (Keep a Changelog format).
3. Update docs affected by your change.
4. Fill in the PR template and make all four checks pass.
5. Maintainers review on a best-effort basis (single maintainer today). Changes merge by lazy
   consensus after 72 hours, or 7 days for governance, license, role schema, routing or precedence
   policy changes. Reviews return non-conforming PRs with the standard missed and how to fix it.
