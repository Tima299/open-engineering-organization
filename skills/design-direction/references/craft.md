# Craft rules and anti-slop checklist

Brand-agnostic rules; DESIGN.md tokens decide the specifics.

## Craft
- Type: 6-8 sizes on a 1.2-1.25 ratio. Body text 16px or larger on the web. Line length 45-80
  characters. ALL CAPS labels tracked at 0.06em or more. Use longer leading for CJK scripts.
- Color: neutrals carry the layout. The accent appears at most twice per screen. Semantic colors
  (success/warning/danger) are never used decoratively.
- Space: one spacing scale. Group by proximity before adding borders or boxes.
- Hierarchy: one primary action per view, and the most important number is the largest.
- Data: tables align numbers right with tabular figures; charts start at zero for bars, label
  axes and units, and offer a table alternative.

## Scoring anchors (each lens, 0-10)
| Score | Meaning |
|---|---|
| 10 | Every visual acceptance criterion met with evidence. No must-fix or should-fix items. A deliberate distinctive move. |
| 8 | All criteria met. No must-fix items. At most 2 should-fix items, each with a reason. **Ship threshold.** |
| 5 | Works, but generic or inconsistent: 3+ should-fix items, or a criterion only partly met. |
| 2 | A must-fix item is open, or a primary state (empty, error, loading) is missing. |
| 0 | The screen fails its primary task, or an AA contrast or keyboard failure blocks use. |

Score each lens (design, critic, brand fit, accessibility, copy) by the lowest row whose
condition is true, and cite the evidence (screenshot path or snapshot line) for every point lost.
Run `oeo copy-lint` on visible copy for the copy lens.

## Anti-slop tiers (critic lens)
**Must fix (blocks shipping):**
- Default framework accent (stock indigo/violet) used as the brand color without a decision.
- Two-stop "hero gradient" or glow blobs added as decoration.
- Emoji used as icons, or mixed icon sets.
- Cards with a colored left border used as the main visual device.
- Invented metrics, logos, testimonials or user counts.
- Filler copy (lorem ipsum, "Lorem dashboard", "Welcome back, User!") in a shipped state.
- Missing focus-visible styles, or contrast below AA.

**Should fix:**
- Stock section order (hero → three features → testimonials → pricing) with no reason.
- Placeholder image CDNs.
- Raw hex values that bypass tokens.
- Inconsistent radii or shadows.
- Hover-only affordances.

**Polish:** optical alignment, number formatting, empty-state illustration or copy, skeleton
loaders matching the final layout, transitions on state change.

Ideas adapted from nexu-io/open-design (Apache-2.0); see THIRD_PARTY.md.
