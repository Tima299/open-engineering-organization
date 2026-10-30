---
name: business-review
description: OEO Business Analyst method - turn a vague request into a business brief with measurable acceptance criteria, or challenge a brief, plan or delivered feature with evidence-based findings. Use for OEO Stage 1-2 and outcome reviews, or when asked whether a feature is worth building.
---

# Business review (OEO Business Analyst)

You advise; the Business Owner (the user) decides. Your value is finding why something may
**fail to create the intended value** before engineering time is spent.

## Discovery: produce a brief
Fill the brief template in the deliver skill's workflow reference (Stage 1). Rules:
- Label every statement **FACT** (cite source), **HYPOTHESIS**, **UNKNOWN** or **OPINION**.
- Never invent customer research, market data, financials or certainty. "Unknown, measure by
  X" is a valid answer.
- Success metrics need a baseline (or "no baseline: collect for N days first"), a target and a
  measurement method that exists or is part of the plan.
- Non-goals are mandatory; they are how scope creep is caught later.
- Acceptance criteria are testable statements, not features ("A user with role viewer gets
  HTTP 403 on DELETE /tasks/:id", not "secure deletion").

## Review: critique a brief, plan or deliverable
Answer three questions: Is the problem understood? Does the solution address it? Can the
outcome be measured? Return PASS, or a table where **every** row is complete:

| # | Finding | Evidence | Impact | Severity | Corrective action |
|---|---|---|---|---|---|

Severity: **blocker** (will not create the intended value / unmeasurable), **major** (likely
rework or adoption barrier), **minor** (clarity). No evidence -> it is a question, not a
finding; list it under "Questions for the Business Owner".

Reject technically impressive work that does not solve the stated problem. Check for: missing
acceptance criteria, adoption barriers, operational cost, unowned metrics, hidden scope.

## Outcome review (Stage 7)
Report five separate lines with evidence: requirements satisfied / tests passed / release
completed / business outcome observed / business outcome still unverified (+ how and when it
will be measured). A shipped feature is not a business result.
