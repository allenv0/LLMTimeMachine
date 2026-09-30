"""Quick three-era tour: travel-stage plates (Base → Instruction → Chat)."""

from __future__ import annotations

from html import escape

from llm_time_machine.domain import ModelRun, ModelSpec
from llm_time_machine.ui import theme

SCOPE_FULL = "full"
SCOPE_TOUR = "tour"

MODE_LABELS = {
    "base_continuation": "Base",
    "instruction": "Instruction",
    "chat": "Chat",
}

MODE_ARC_NOTES = {
    "base_continuation": "Continues your text. No chat interface yet.",
    "instruction": "Follows instructions. Short, direct answers.",
    "chat": "Chat-style replies with context and structure.",
}

ARROW = "→"


def pick_arc_models(
    models: list[ModelSpec], tour_ids: list[str] | None = None
) -> list[ModelSpec]:
    """Select models that show the base → instruction → chat arc."""
    by_id = {m.id: m for m in models}
    if tour_ids:
        picked = [by_id[i] for i in tour_ids if i in by_id]
        if picked:
            return sorted(picked, key=lambda m: (m.display_year, m.id))

    ordered = sorted(models, key=lambda m: (m.display_year, m.id))
    if len(ordered) <= 3:
        return ordered

    by_mode: dict[str, list[ModelSpec]] = {}
    for m in ordered:
        by_mode.setdefault(m.mode, []).append(m)
    picked = []
    for mode in ("base_continuation", "instruction", "chat"):
        pool = by_mode.get(mode) or []
        if not pool:
            continue
        if mode == "base_continuation":
            picked.append(pool[0])
        elif mode == "chat":
            picked.append(pool[-1])
        else:
            picked.append(pool[len(pool) // 2])
    if len(picked) >= 2:
        picked.sort(key=lambda m: (m.display_year, m.id))
        return picked
    return [ordered[0], ordered[len(ordered) // 2], ordered[-1]]


def _mode_badge(mode: str) -> str:
    return MODE_LABELS.get(mode, mode)


def _stage_plate(spec: ModelSpec, run: ModelRun | None, text: str) -> str:
    label = _mode_badge(spec.mode).upper()
    if run is None:
        body = '<div class="tm-stage-note">Not in this trip.</div>'
        status = theme.badge("skip", "hole")
    elif run.status == "completed":
        preview = escape((text or "").strip())
        if len(preview) > 360:
            preview = preview[:360].rstrip() + "…"
        body = (
            f'<div class="tm-stage-body">{preview or "(empty output)"}</div>'
            f'<div class="tm-stage-note">completed · gen {run.generation_seconds:.1f}s</div>'
        )
        status = theme.badge("arrived", "ok")
    else:
        body = f'<div class="tm-stage-note">{run.status}: {run.error_code or "error"}</div>'
        status = theme.badge("delayed", "danger")

    return (
        '<div class="tm-stage">'
        f'<div class="tm-stage-label">{label}</div>'
        f'<div class="tm-stage-year">{spec.display_year}</div>'
        f'<div class="tm-stage-name">{spec.display_name}</div>'
        f'<div class="tm-stage-note">{MODE_ARC_NOTES.get(spec.mode, "")}</div>'
        f"{body}"
        f'<div style="margin-top:0.35rem">{status}</div>'
        "</div>"
    )


def render_progress_arc(
    st,
    models: list[ModelSpec],
    runs: list[ModelRun],
    outputs: dict[str, str],
) -> None:
    """Surface base → instruction → chat for one prompt (the demo moment)."""
    arc_models = pick_arc_models(models)
    if len(arc_models) < 2:
        return

    run_by_id = {r.model_id: r for r in runs}
    theme.inject(st)
    st.markdown(
        theme.section("Progress arc", "Base → Instruction → Chat"),
        unsafe_allow_html=True,
    )
    st.caption(
        "Same prompt · three stations in time. "
        "Newer is not always better — look at honesty and usefulness."
    )

    plates = []
    for i, spec in enumerate(arc_models):
        if i:
            plates.append('<div class="tm-arrow" aria-hidden="true">→</div>')
        run = run_by_id.get(spec.id)
        text = outputs.get(spec.id) if run else ""
        plates.append(_stage_plate(spec, run, text or ""))
    # pad to full grid if only two stages
    while len(plates) < 5:
        if len(plates) % 2 == 0:
            plates.append('<div class="tm-arrow" aria-hidden="true"></div>')
        else:
            plates.append('<div class="tm-stage" style="opacity:0.35;border-style:dashed"></div>')

    st.markdown(f'<div class="tm-stages tm-fade">{"".join(plates)}</div>', unsafe_allow_html=True)

    notes = []
    for spec in arc_models:
        run = run_by_id.get(spec.id)
        state = run.status if run else "missing"
        notes.append(f"{spec.display_year} {_mode_badge(spec.mode)} ({state})")
    st.caption(" · ".join(notes))
    st.markdown(
        theme.figure_caption(
            1,
            "Three stations on one prompt. Compare honesty and usefulness — newer is not always better.",
        ),
        unsafe_allow_html=True,
    )
