"""Decade walk UI: one year at a time with a reflection pause."""

from __future__ import annotations

from llm_time_machine.decade_walk import walk_models, walk_script
from llm_time_machine.diary import DiaryStore
from llm_time_machine.ui import theme


def render_decade_walk(
    st,
    *,
    cohort,
    diary: DiaryStore,
    controller,
    hardware_summary: dict | None = None,
    entry_id: str | None = None,
) -> None:
    theme.inject(st)
    st.markdown(theme.section("Decade walk", "one stop at a time · simulated lived time"), unsafe_allow_html=True)
    st.caption(
        "Reveal one year at a time and leave a reflection. "
        "This is theater over real checkpoints — not calendar time. Newer is not always better."
    )

    models = walk_models(cohort)
    script = walk_script(cohort)
    with st.expander("Walk script (years in this cohort)", expanded=False):
        for row in script:
            st.write(f"{row['year']} · {row['name']} · `{row['mode']}`")

    state = st.session_state
    if "walk_step" not in state:
        state["walk_step"] = 0
    if "walk_results" not in state:
        state["walk_results"] = []
    if "walk_prompt" not in state:
        state["walk_prompt"] = ""

    prompt = st.text_area(
        "Prompt for the walk",
        value=state.get("walk_prompt") or "",
        key="walk-prompt-input",
        height=100,
    )
    crit = st.text_input("Success criterion (optional)", key="walk-crit")

    col_a, col_b, col_c = st.columns(3)
    if col_a.button("Start / restart walk", type="primary"):
        state["walk_step"] = 0
        state["walk_results"] = []
        state["walk_prompt"] = prompt
        st.rerun()
    if col_b.button("Reset walk"):
        state["walk_step"] = 0
        state["walk_results"] = []
        st.rerun()

    step = int(state["walk_step"])
    results = list(state.get("walk_results") or [])

    # show past years
    for item in results:
        with st.container(border=True):
            st.markdown(f"**{item['year']} · {item['name']}** · `{item['mode']}`")
            st.markdown(item.get("output") or "_(no output)_")
            if item.get("reflection"):
                st.caption(f"Your reflection ({item['year']}): {item['reflection']}")
            if item.get("trip_id"):
                st.caption(f"Trip: `{item['trip_id']}`")

    if step >= len(models):
        st.success("Walk complete. You lived the (simulated) decade.")
        if entry_id:
            st.caption(f"Reflections can be saved to diary entry `{entry_id}` from the Diary panel.")
        return

    spec = models[step]
    st.markdown(f"### Next: **{spec.display_year} · {spec.display_name}**")
    st.caption("Limitations: " + "; ".join(spec.limitations))
    ready_to_run = bool((prompt or state.get("walk_prompt") or "").strip())

    if col_c.button("Reveal this year", disabled=not ready_to_run or bool(state.get("walk_running"))):
        use_prompt = (prompt or state.get("walk_prompt") or "").strip()
        state["walk_prompt"] = use_prompt
        state["walk_running"] = True
        try:
            trip_id = f"walk-{spec.display_year}-{spec.id}"
            # avoid collision on restart
            existing = []
            try:
                existing = controller.store.list_trips()
            except Exception:
                existing = []
            if trip_id in existing:
                trip_id = f"{trip_id}-{step}"
            manifest = controller.run_trip(
                use_prompt,
                success_criterion=crit or "",
                trip_id=trip_id,
                models=[spec],
                hardware_summary=hardware_summary,
                block_network_during_trip=getattr(controller, "runner_kind", "fake") != "fake",
            )
            output = ""
            try:
                output = controller.store.read_output(manifest.trip_id, spec.id)
            except Exception:
                output = ""
            results.append(
                {
                    "year": spec.display_year,
                    "name": spec.display_name,
                    "mode": spec.mode,
                    "model_id": spec.id,
                    "trip_id": manifest.trip_id,
                    "output": output,
                    "status": manifest.runs[0].status if manifest.runs else "unknown",
                    "reflection": "",
                }
            )
            state["walk_results"] = results
            state["walk_step"] = step + 1
        except Exception as exc:
            st.error(f"Walk step failed: {exc}")
        finally:
            state["walk_running"] = False
        st.rerun()

    # reflection for the year just revealed
    if results and step > 0:
        last = results[-1]
        note = st.text_area(
            f"Reflection after {last['year']} — would you have believed this?",
            key=f"walk-refl-{last['year']}-{step}",
            height=80,
        )
        if st.button("Save reflection to diary", key=f"walk-refl-save-{step}"):
            last["reflection"] = note.strip()
            state["walk_results"] = results
            if entry_id and note.strip():
                diary.set_reflection(entry_id, last["year"], note.strip())
                st.success("Saved to diary.")
            elif note.strip():
                st.success("Kept in this walk session (register a diary entry to persist).")
            st.rerun()
