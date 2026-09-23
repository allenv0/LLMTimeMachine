"""Local data path display, export, and deletion controls."""

from __future__ import annotations

from pathlib import Path

from time_machine.artifact_store import ArtifactStore
from time_machine.export_service import ExportService


def render_local_data_panel(st, store: ArtifactStore, trip_id: str | None = None) -> None:
    st.subheader("Local data")
    st.write(f"Path: `{store.paths.local_data_dir}`")
    st.caption("Files are local only. Nothing is uploaded. Diary prompts stay under local-data/diary/.")

    trips = store.list_trips()
    st.write(f"Stored trips: **{len(trips)}**")
    try:
        from time_machine.diary import DiaryStore

        n_diary = len(DiaryStore(store.paths).list())
    except Exception:
        n_diary = 0
    st.write(f"Diary entries: **{n_diary}**")

    if trip_id and trip_id in trips:
        if st.button("Export this trip (ZIP)", key="export-zip"):
            svc = ExportService(store)
            out = svc.export_zip(trip_id)
            st.success(f"Exported to `{out}`")
        if st.button("Export this trip (JSON)", key="export-json"):
            svc = ExportService(store)
            out = svc.export_json_bundle(trip_id)
            st.success(f"Exported to `{out}`")

        if st.button("Delete this trip", key="delete-one"):
            st.session_state["confirm_delete_one"] = True
        if st.session_state.get("confirm_delete_one"):
            st.warning("Delete this trip permanently from local disk?")
            c1, c2 = st.columns(2)
            if c1.button("Yes, delete this trip", key="delete-one-yes"):
                store.delete_trip(trip_id)
                st.session_state["confirm_delete_one"] = False
                st.session_state.pop("active_trip_id", None)
                st.success("Trip deleted.")
                st.rerun()
            if c2.button("Cancel", key="delete-one-no"):
                st.session_state["confirm_delete_one"] = False

    st.markdown("---")
    if st.button("Delete all local trips", key="delete-all"):
        st.session_state["confirm_delete_all"] = True
    if st.session_state.get("confirm_delete_all"):
        st.warning("This deletes every trip under local-data/trips/ and cannot be undone.")
        typed = st.text_input("Type DELETE-ALL to confirm", key="delete-all-text")
        if st.button("Confirm delete all", key="delete-all-yes"):
            if typed.strip() == "DELETE-ALL":
                n = store.delete_all_trips()
                st.session_state["confirm_delete_all"] = False
                st.session_state.pop("active_trip_id", None)
                st.success(f"Deleted {n} trips.")
                st.rerun()
            else:
                st.error("Confirmation text did not match.")
