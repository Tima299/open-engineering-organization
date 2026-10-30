---
name: design-direction
description: OEO UI design - lock a visual direction, capture it in DESIGN.md, specify states, a11y and visual acceptance criteria before frontend code, then run an independent scored review of the build.
---

# Design direction (OEO Design Lead + Frontend)

Beautiful screenshots are not proof of a working product; working code is not proof of good UX.

## 1. Inspect, then ask before generating
Inspect the existing design system first: tokens, component library, CSS approach, breakpoints,
icons, dark mode, i18n. Reuse it. If the project has a `DESIGN.md`, it is the source of truth.
If direction is open, ask **one short question form** and lock the answers before any design:
audience and primary task · tone (2-3 adjectives) · reference products (if any) · density ·
light/dark · brand assets. Without a brand, propose 2-3 named directions and let the user pick.

## 2. Capture the direction as `DESIGN.md` (project root)
Use the [DESIGN.md skeleton](references/design-md.md): theme, color roles, type scale,
components with states, spacing, elevation, motion, do/don't with reasons, responsive table,
agent prompt guide. "Make it look like <site>": ask the orchestrator for an `oeo:research` capture of the reference
(screenshots, computed styles), then label each value **extracted**, **estimated** or
**proposed**. Copy structure, not brand assets or proprietary fonts; name deliberate fallbacks.

## 3. Screen spec (`.oeo/<engagement>/screen-spec.md`, under ~60 lines)
- **Users and primary task**: top 3 questions the screen answers; above the fold at 1280px and 375px.
- **Components**: reuse list; new ones with props and states.
- **States** for every data view: loading, empty, error, partial, success, permission-denied.
- **Interaction**: keyboard path, focus order, feedback, motion under 300ms, respects `prefers-reduced-motion`.
- **Accessibility**: WCAG 2.2 AA. Contrast is at least 4.5:1 for text and 3:1 for UI. Every
  input has a label; landmarks and headings are used; charts have a table or text alternative;
  color is never the only signal.
- **Visual acceptance criteria**: 5-10 checkable statements.
- **One distinctive move**: about 80% proven patterns and 20% product-specific character. That
  means one bold visual choice, sharp microcopy and one memorable detail, not five.

## 4. Review the built UI (scored panel)
Evidence comes from `oeo:verify` (browser snapshots, emulation, screenshots). A reviewer that did
not build the UI (`oeo:design-lead` or `oeo:qa-verifier`) scores each lens 0-10 against the spec
and the [craft rules](references/craft.md): **design**, **critic** (anti-slop), **brand fit**,
**accessibility**, **copy**. Ship at 8/10 or more with no must-fix item open. Each round returns
findings (file:line, evidence, fix). Revisions use the normal retry budget (2). If a must-fix item
or an AA failure is still open after that, do not ship: escalate to the user with options. Only
should-fix and polish items may ship as a listed backlog.

## Optional adapters
Use these only if installed in the session; never install them yourself:
- `frontend-design`, `taste-skill` or `open-design`: direction.
- `impeccable`: anti-pattern review.
- `ui-ux-pro-max`: palettes and type pairings.
- `emil-kowalski-skills`: motion.
- `awesome-design-md`: reference DESIGN.md files, read for structure and not redistributed.

The spec, DESIGN.md and the gates above stay authoritative.
