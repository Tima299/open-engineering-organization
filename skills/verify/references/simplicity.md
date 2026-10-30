# Simplicity checklist

Complexity must be earned by demonstrated need. For each item answer YES/NO with evidence.

- [ ] Every new abstraction (interface, base class, factory, plugin point) has 2+ real callers today.
- [ ] Every new dependency replaces more code than it adds risk; a stdlib/existing option was considered.
- [ ] No new service, queue, cache or datastore without a measured problem it solves.
- [ ] No configuration option without a current user who needs a different value.
- [ ] No dead code, speculative parameters, or "for future use" branches.
- [ ] The diff follows existing patterns; a new pattern is justified in the PR/ADR.
- [ ] A smaller diff achieving the same acceptance criteria does not obviously exist.

Finding format: what to remove or inline, why it is not needed now, the simpler alternative.
Simplicity never justifies removing validation, security checks, accessibility, error handling
or tests (see the precedence policy). If Ponytail is installed, its review may be used as a
second opinion; this checklist remains the gate.
