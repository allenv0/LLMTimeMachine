# lifeline-rail — React upgrade path for the hero rail

Portable Lifeline-style rail for LLMTimeMachine. MIT port of
[`evilrabbit/lifeline`](https://github.com/evilrabbit/lifeline) rail logic
(intro draw, staggered markers, sticky label shield, embed wheel handoff,
hover preview, reduced-motion) skinned to the repo's newsprint design system
(tokens in `tokens.ts`, mirrored in `src/llm_time_machine/ui/theme.py`).

## Data contract (single source of truth)

Python owns the timeline. React never invents years:

```python
from llm_time_machine.ui.timeline import lifeline_markers
markers = lifeline_markers(cohort, statuses=statuses, walk_step=walk_step)
# JSON-serializable list[dict] — POST/props it to <LifelineRail markers={...} />
```

Rules enforced on both sides (Streamlit iframe rail + this component):

- `hole` → dashed, never model text. `gap` (no model, no declared hole) → faint, empty.
- `substitute` → ochre label + `stands_for` line. Never rename a sub into a frontier claim.
- status-quo / FUTURE are endpoints beyond the rail, never year stops.
- Gaps are never zero-filled into fake models or fake scores.

## Use

```tsx
import { LifelineRail } from "./LifelineRail";

<LifelineRail
  markers={markersFromPython}
  mode="walk"               // "walk" (walk-first default) | "full"
  activeYear={2019}         // optional playhead override
  intro                     // rail draw + stagger; auto-skipped under reduced motion
  onSelectYear={(year, id) => scrollToDispatch(year, id)}
/>
```

Today the Streamlit app renders the zero-dependency iframe rail
(`timeline.py::render_hero_rail`) so there is no Node build step. When you
want true scrub physics, live departure-dot sync, and auto-resize:

1. `npm install && npm run build` here, or wrap with
   `streamlit-component-lib` (`Streamlit.setComponentValue` on stop select).
2. Feed it the same `lifeline_markers()` JSON — no shape change needed.
3. Keep `tokens.ts` and `theme.py::LIFELINE_ISLAND_CSS` in sync; the iframe
   is the visual fallback if the component fails to load.

## Attribution

Rail motion + layout logic: `evilrabbit/lifeline` (MIT).
Newsprint shell, honesty encoding, and cohort data: this repo.
