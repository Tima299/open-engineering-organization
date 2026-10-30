# Product methods

## Lean PRD (1-2 pages; extends `.oeo/brief.md`)
Complete means no gap blocks a first-version decision. Never write "TBD": move each unknown to
**Assumptions & open questions**, with how and when it will be resolved.
1. Segment: who exactly, in what situation.
2. Value proposition, as one chain: who · why now · what they do today · how we help · what
   changes after · alternatives they would use instead.
3. Solution: scope, non-goals, key flows (numbered).
4. Success metrics: baseline, target, measurement, owner. They must follow from step 2.
5. Acceptance criteria (testable) · risks · assumptions & open questions · rollout.

## Strategy red-team (before committing significant effort)
1. List the plan's claims and keep the load-bearing ones.
2. For each one, steelman it, then attack it. Write the failure as **"Fails if ..."**.
3. Rank failures by impact × likelihood × how cheap they are to test.
4. For the top 3, give: evidence to get this week · kill criterion · cheapest test.
5. Also state what is well reasoned and what could not be assessed.

## Pre-mortem ("it is 6 months later and this failed: why?")
| Class | Meaning | Action |
|---|---|---|
| Tiger | real, evidenced threat | mitigation with owner and date |
| Paper tiger | looks scary, evidence says it is not | note why, drop it |
| Elephant | doubt nobody has said out loud | name it, assign someone to test it |

## Assumption triage
Score each assumption: **impact** (1-5) and **risk** = (1 - confidence) × effort to reverse.
High impact and high risk: design an experiment that observes **behavior**, not opinions
(fake-door, concierge, prototype task, usage data) before building. Low risk: accept it and log it.

Ideas adapted from phuryn/pm-skills (MIT); see THIRD_PARTY.md.
