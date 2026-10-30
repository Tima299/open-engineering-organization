## Summary
<!-- What does this change and why? One or two sentences. -->

## Linked issue
<!-- Closes #123. Features, roles and routing changes should have an issue first. -->

## Type of change
<!-- Keep the ones that apply. -->
- [ ] Bug fix
- [ ] Feature or skill
- [ ] Role, routing or policy change
- [ ] Docs only
- [ ] Third-party registry entry
- [ ] CI, tooling or dependencies

## Checklist
- [ ] `python3 scripts/oeo.py validate` passes
- [ ] `python3 scripts/oeo.py build --check` passes
- [ ] `python3 -m unittest discover -s tests -t .` passes
- [ ] `python3 evals/run.py --no-write` passes
- [ ] If I changed `org/`, `config/` or `third_party/`, I ran `python3 scripts/oeo.py build` and committed the generated files (and did not hand-edit `agents/*.md`, `org/org.lock.json`, `docs/roles.md` or `THIRD_PARTY.md`)
- [ ] `CHANGELOG.md` has an entry under `Unreleased`
- [ ] Docs are updated for any user-visible change
- [ ] Routing changes include a new or adjusted eval scenario in `evals/scenarios/` (or N/A)
- [ ] No secrets, tokens or private data in the diff, commit messages or this description
- [ ] Every commit is signed off (`git commit -s`) per the [DCO](https://developercertificate.org/)
- [ ] AI-assistance disclosure below is filled in

## AI assistance
<!-- Required. Write "None" or name the tool and what it did. The human submitter is responsible for the change. -->
