"""Progress rows and status rendering."""

from __future__ import annotations

from time_machine.domain import ModelRun

WAITING = "waiting"
LOADING = "loading"
GENERATING = "generating"
COMPLETE = "complete"
FAILED = "failed"


def initial_statuses(models: list) -> dict[str, str]:
    return {m.id: WAITING for m in models}


def apply_status(statuses: dict[str, str], model_id: str, status: str) -> dict[str, str]:
    statuses = dict(statuses)
    mapping = {
        "loading": LOADING,
        "generating": GENERATING,
        "complete": COMPLETE,
        "failed": FAILED,
    }
    statuses[model_id] = mapping.get(status, status)
    return statuses


def run_status_label(run: ModelRun) -> str:
    return {
        "completed": COMPLETE,
        "failed": FAILED,
        "timed_out": "timed out",
        "unsupported": "unsupported",
        "cancelled": "cancelled",
    }.get(run.status, run.status)


def render_progress(st, models: list, statuses: dict[str, str], details: dict[str, str] | None = None):
    details = details or {}
    st.subheader("Timeline")
    for m in models:
        st_status = statuses.get(m.id, WAITING)
        detail = details.get(m.id, "")
        left, right = st.columns([3, 2])
        left.markdown(f"**{m.display_year}** · {m.display_name}")
        right.markdown(f"`{st_status}`" + (f" — {detail}" if detail else ""))
        st.progress(_progress_fraction(st_status))
    st.caption("One runner at a time. Results reveal as soon as each model finishes.")


def _progress_fraction(status: str) -> float:
    return {
        WAITING: 0.05,
        LOADING: 0.35,
        GENERATING: 0.7,
        COMPLETE: 1.0,
        FAILED: 1.0,
    }.get(status, 0.05)
