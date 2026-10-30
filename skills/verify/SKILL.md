---
name: verify
description: OEO independent verification - check a change against its acceptance criteria and quality gates with real command output, and return actionable PASS/FAIL findings. Use for OEO Stage 6, before declaring any change done, or when asked to review/verify work you did not write.
---

# Independent verification

You did not write this change, and you do not fix it: you produce evidence and findings.

## Procedure
1. Collect: acceptance criteria, gate list (from `oeo route`), changed files (`git diff --stat`,
   `git diff`), and the repository's own check commands (README, CONTRIBUTING, package
   scripts, Makefile, CI config). Use the project's commands; do not invent new tooling.
2. Run what applies and record each: `| gate | command / method | result | evidence |`.
   - Functional correctness: exercise each acceptance criterion (test, script, or request).
   - Regression: the new test fails without the change. Prove it in a temporary
     `git worktree add <tmp> HEAD` with only the new tests copied in; never stash or check out
     in the working tree (other reviewers may be reading it). Remove the worktree afterwards.
   - Tests, type-check, lint, build: full output tail on failure.
   - Error handling and edge cases: empty, invalid, boundary, concurrent, unauthorized inputs.
   - Security and data: if auth, input handling, secrets, queries or migrations changed, load
     [security checklist](references/security.md).
   - UI: responsive behavior, keyboard access, contrast, states (loading/empty/error); load
     [browser verification](references/browser.md) to collect evidence in a real browser.
   - Simplicity: load [simplicity checklist](references/simplicity.md) when the diff adds
     abstractions, dependencies or more than ~200 lines.
3. Verdict: **PASS** only if every applicable gate passed with evidence. Anything not run is
   "NOT RUN: reason" and makes the verdict FAIL unless the orchestrator marked it not applicable.

## Findings
Numbered, each with: location (file:line), evidence, impact, severity (blocker/major/minor),
concrete fix. No vague advice ("improve error handling"). End with the HANDOFF block.

Never report success you did not observe. Never weaken a gate to reach PASS.
