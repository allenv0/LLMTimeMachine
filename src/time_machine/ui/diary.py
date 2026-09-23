"""Prompt diary UI: register, list, first-solved, link trips."""

from __future__ import annotations

from time_machine.diary import DiaryStore
from time_machine.domain import PromptDiaryEntry
from time_machine.trip_utils import hash_prompt


def render_diary_panel(st, diary: DiaryStore, *, active_trip_id: str | None = None, raw_prompt: str = "") -> str | None:
    """Sidebar/main diary panel. Returns selected entry_id or None."""
    st.subheader("Prompt diary")
    st.caption(
        "Pre-register private weird prompts and revisit them over time. "
        "Local only. Full text stays on disk under local-data/diary/."
    )

    entries = diary.list()
    selected: str | None = None

    if entries:
        labels = [
            f"{e.preview or e.entry_id}  ·  {len(e.trips)} trip(s)"
            + ("  ·  SOLVED" if e.solved_mark != "unset" else "")
            for e in entries
        ]
        idx = st.selectbox("Diary entries", range(len(entries)), format_func=lambda i: labels[i])
        selected = entries[idx].entry_id
        entry = entries[idx]
        st.write(f"Created `{entry.created_at}`")
        if entry.tags:
            st.write("Tags: " + ", ".join(entry.tags))
        if entry.success_criterion:
            st.caption(f"Criterion: {entry.success_criterion}")
        if entry.solved_mark != "unset":
            st.success(
                f"First solved by `{entry.first_solved_model_id}` "
                f"({entry.solved_mark}) in trip `{entry.first_solved_trip_id}`"
            )
        else:
            st.info("Not marked solved yet.")
        st.write(f"Linked trips: {', '.join(t.trip_id for t in entry.trips) or '—'}")
    else:
        st.write("No diary entries yet.")

    st.markdown("**Register a prompt**")
    prompt = st.text_area(
        "Prompt to pre-register",
        value=raw_prompt if raw_prompt else "",
        key="diary-new-prompt",
        height=100,
    )
    crit = st.text_input("Success criterion (optional)", key="diary-new-crit")
    tags_raw = st.text_input("Tags (comma-separated)", key="diary-new-tags")
    if st.button("Register in diary", key="diary-register"):
        if not prompt.strip():
            st.error("Prompt must not be empty.")
        else:
            tags = [t.strip() for t in tags_raw.split(",") if t.strip()]
            trip_link = None
            if active_trip_id and raw_prompt and hash_prompt(prompt) == hash_prompt(raw_prompt):
                trip_link = active_trip_id
            entry = diary.register(prompt, success_criterion=crit, tags=tags, trip_id=trip_link)
            st.success(f"Registered `{entry.entry_id}`")
            st.rerun()

    if selected:
        entry = diary.get(selected)
        st.markdown("**First-solved**")
        solved_models = []
        # user types model id or we leave free text for flexibility
        model_id = st.text_input(
            "Model id that first solved this",
            value=entry.first_solved_model_id or "",
            key=f"fs-model-{selected}",
        )
        trip_id = st.text_input(
            "Trip id",
            value=entry.first_solved_trip_id or (entry.trips[-1].trip_id if entry.trips else ""),
            key=f"fs-trip-{selected}",
        )
        c1, c2, c3 = st.columns(3)
        if c1.button("Mark solved (user)", key=f"fs-set-{selected}"):
            if model_id.strip() and trip_id.strip():
                diary.mark_first_solved(selected, model_id.strip(), trip_id.strip(), mark="user")
                st.rerun()
            else:
                st.error("Need model id and trip id.")
        if c2.button("Clear solved", key=f"fs-clear-{selected}"):
            diary.clear_first_solved(selected)
            st.rerun()
        if active_trip_id and c3.button("Link current trip", key=f"link-{selected}"):
            diary.link_trip(selected, active_trip_id)
            st.rerun()

        st.markdown("**Decade-walk reflections**")
        year = st.text_input("Year", key=f"refl-year-{selected}")
        note = st.text_area("Reflection note (local)", key=f"refl-note-{selected}", height=80)
        if st.button("Save reflection", key=f"refl-save-{selected}"):
            if year.strip():
                diary.set_reflection(selected, year.strip(), note)
                st.success("Saved.")
                st.rerun()
        if entry.reflections:
            st.markdown("*Saved reflections*")
            for y, n in sorted(entry.reflections.items()):
                st.write(f"**{y}:** {n}")

        if st.button("Delete diary entry", key=f"del-{selected}"):
            diary.delete(selected)
            st.success("Deleted.")
            st.rerun()

    return selected


def render_first_solved_banner(st, entry: PromptDiaryEntry | None) -> None:
    if not entry:
        return
    if entry.solved_mark != "unset":
        st.info(
            f"Diary `{entry.entry_id}` first solved by **{entry.first_solved_model_id}** "
            f"({entry.solved_mark}) — progress can be honesty, not omniscience."
        )
