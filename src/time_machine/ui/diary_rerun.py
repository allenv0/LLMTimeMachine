"""Diary re-run + first-solved timeline UI (local-v3)."""

from __future__ import annotations

from time_machine.diary import DiaryStore
from time_machine.diary_rerun import DiaryRerunService


def render_diary_rerun(st, rerun: DiaryRerunService, diary: DiaryStore) -> None:
    st.subheader("Diary re-run")
    st.caption(
        "Explicit replay when a new cohort/year slot lands. **Not calendar time.** "
        "Each re-run creates a new trip and links it to the entry. Email is cloud-only; "
        "download an .ics reminder instead."
    )
    entries = diary.list()
    if not entries:
        st.info("Register diary prompts first.")
        return

    labels = [f"{e.preview or e.entry_id} · {len(e.trips)} trip(s)" for e in entries]
    idx = st.selectbox("Entry to re-run", range(len(entries)), format_func=lambda i: labels[i])
    entry = entries[idx]
    mode = st.radio("Re-run mode", ["tour", "full"], horizontal=True)
    plan = rerun.plan(entry.entry_id, mode=mode)
    st.write(
        f"Plan: `{plan['cohort_id']}` · {len(plan['model_ids'])} models "
        f"({min(plan['years'] or [0])}–{max(plan['years'] or [0])}) · "
        f"existing trips {plan['n_existing_trips']} · reruns {plan['n_existing_reruns']}"
    )
    if st.button("Re-run diary entry now", key="diary-rerun-btn"):
        with st.spinner("Re-running…"):
            try:
                manifest = rerun.rerun_entry(entry.entry_id, mode=mode)
                st.success(f"Re-run trip `{manifest.trip_id}` linked to `{entry.entry_id}`.")
            except Exception as exc:
                st.error(f"Re-run failed: {exc}")

    if st.button("Download .ics re-run reminder (local stub)", key="diary-ics"):
        text = rerun.ics_reminder_stub(entry.entry_id)
        st.download_button(
            "Save ICS",
            data=text,
            file_name=f"tm-diary-{entry.entry_id}.ics",
            mime="text/calendar",
        )


def render_first_solved_timeline(st, rows: list[dict]) -> None:
    st.subheader("First-solved timeline")
    st.caption(
        "When each pre-registered prompt was first marked solved. "
        "User (or opt-in judge) marks — not automatic ground truth. Gaps stay gaps."
    )
    if not rows:
        st.info("No diary entries yet.")
        return
    for row in rows:
        mark = row.get("solved_mark") or "unset"
        year = row.get("first_solved_year")
        year_s = f"{year}" if year is not None else "?"
        if mark == "unset":
            st.write(f"`{year_s}` · **{row['preview'] or row['entry_id']}** · not solved yet")
        else:
            st.write(
                f"`{year_s}` · **{row['preview'] or row['entry_id']}** · "
                f"SOLVED by `{row.get('first_solved_model_id')}` ({mark})"
            )
        st.caption(
            f"entry `{row['entry_id']}` · trips {row['n_trips']} · reruns {row['n_reruns']}"
        )
