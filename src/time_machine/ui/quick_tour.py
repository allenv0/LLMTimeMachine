"""Quick three-era tour: progress-arc helpers and rendering."""

from __future__ import annotations

from time_machine.domain import ModelRun, ModelSpec

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
    st.subheader("Progress arc")
    st.markdown(f"**Base {ARROW} Instruction {ARROW} Chat**")
    st.caption(
        "Same prompt · different historical interfaces. "
        "Newer is not always better — look at honesty and usefulness."
    )

    cols = st.columns(len(arc_models))
    for col, spec in zip(cols, arc_models):
        run = run_by_id.get(spec.id)
        with col:
            st.markdown(f"**{spec.display_year} · {spec.display_name}**")
            st.markdown(f"`{_mode_badge(spec.mode)}`")
            st.caption(MODE_ARC_NOTES.get(spec.mode, ""))
            if run is None:
                st.info("Not in this trip.")
                continue
            if run.status == "completed":
                text = outputs.get(spec.id) or ""
                preview = text.strip()
                if len(preview) > 420:
                    preview = preview[:420].rstrip() + "…"
                if preview:
                    st.markdown(preview)
                else:
                    st.write("(empty output)")
                st.caption(
                    f"Status: completed · gen {run.generation_seconds:.1f}s"
                )
            else:
                st.error(f"{run.status}: {run.error_code or 'error'}")

    notes = []
    for spec in arc_models:
        run = run_by_id.get(spec.id)
        state = run.status if run else "missing"
        notes.append(f"{spec.display_year} {_mode_badge(spec.mode)} ({state})")
    st.caption(" · ".join(notes))
