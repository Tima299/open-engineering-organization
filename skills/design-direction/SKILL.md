---
name: design-direction
description: OEO design workflow for user-facing UI - set design direction, interaction states, responsive layout, accessibility requirements and visual acceptance criteria before frontend implementation, then review the result against them. Use when an OEO task touches frontend/ui, or when asked to design a dashboard, page or component properly.
---

# Design direction (OEO Design Lead + Frontend)

Beautiful screenshots are not proof of a working product; working code is not proof of good UX.
Output a short **design spec** before code, and review the build against it.

## 1. Inspect first
Existing design system, tokens, component library, CSS approach, breakpoints, icon set,
dark mode, i18n. Reuse them. A new visual language needs Design Lead approval (decision matrix:
ux-visual-direction).

## 2. Design spec (write to `.oeo/design.md`, keep it under ~60 lines)
- **Users and primary task**: who, what decision the screen supports, top 3 questions it answers.
- **Information architecture**: sections in priority order; what is above the fold at 1280px
  and at 375px.
- **Components**: reuse list; new components with props and states.
- **States** for every data view: loading, empty, error, partial, success, permission-denied.
- **Interaction**: keyboard path, focus order, hover/press feedback, motion (respect
  `prefers-reduced-motion`; animations under 300ms and purposeful).
- **Accessibility**: WCAG 2.2 AA - contrast >= 4.5:1 text / 3:1 UI, labels for all inputs,
  semantic landmarks/headings, charts with text alternatives or data tables, no color-only meaning.
- **Responsive**: breakpoints, what collapses or reorders, no horizontal scroll at 320px.
- **Visual acceptance criteria**: 5-10 checkable statements ("KPI tiles show value, delta and
  period; delta color is paired with an arrow and sign").

## 3. Optional design adapters
If installed in this session (check the available skills list; never install them yourself):
`frontend-design` or `taste-skill` for aesthetic direction, `impeccable` for anti-pattern
review, `ui-ux-pro-max` for palettes/type pairings, `emil-kowalski-skills` for motion detail.
They inform the spec; the spec's acceptance criteria and a11y rules remain the gate.

## 4. Review the built UI
Check every visual acceptance criterion and state with evidence (screenshot path, test, or DOM
query). Run available tooling (axe, Lighthouse, Playwright, the project's visual tests) when the
project has it. Report findings in the verify format (file:line, evidence, severity, fix).
