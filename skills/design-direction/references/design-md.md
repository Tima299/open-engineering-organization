# DESIGN.md skeleton

DESIGN.md is to visual design what AGENTS.md / CLAUDE.md is to code: one file at the project root
that every design or frontend agent reads first. Keep it under ~250 lines and tokenized.

```markdown
# DESIGN.md - <product>
Status: <date> · source: <existing system | extracted from <url> on <date> | proposed>

## 1. Theme & atmosphere
2-3 sentences: mood, density, what the UI should feel like and must never feel like.

## 2. Color roles
| Role | Token | Light | Dark | Use for |
|---|---|---|---|---|
| primary | --color-primary | #... | #... | one filled CTA per section |
| surface / surface-raised / border / text / text-muted / success / warning / danger / focus |

## 3. Typography
Families (+ fallback for any proprietary font) · scale ratio 1.2-1.25, 6-8 sizes max.
| Style | Size/line-height | Weight | Tracking | Use |

## 4. Spacing, radii, elevation, motion
Spacing scale (e.g. 4px base) · radii set · shadow levels with when-to-use · motion durations
and easing; reduced-motion behavior.

## 5. Components
Per component: anatomy, variants, states (default, hover, focus-visible, active, disabled,
loading, error), and the tokens it uses.

## 6. Do / don't (each with a reason)
- Do: <rule> because <reason>. Don't: <rule> because <reason>.

## 7. Responsive
| Breakpoint | Width | What changes | Touch target | Images |

## 8. Agent prompt guide
How an agent should apply this file; 2-3 ready-to-use prompts; how to propose changes.
```

Optional: `design-preview.html` that renders swatches, type scale, buttons and cards (light and
dark) so a human can check the file against the product or the reference site.

Value provenance labels when extracting from a reference: **extracted** (read from CSS or
computed style), **estimated** (judged from a screenshot), **proposed** (new decision).

Ideas adapted from VoltAgent/awesome-design-md (MIT), nexu-io/open-design (Apache-2.0) and the
Firecrawl design workflow (MIT); see THIRD_PARTY.md.
