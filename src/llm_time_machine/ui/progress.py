"""Progress: departure-board rows for in-run timeline status."""

from __future__ import annotations

from llm_time_machine.domain import ModelRun
from llm_time_machine.ui import theme

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


def _fraction(status: str) -> float:
    return {
        WAITING: 0.05,
        LOADING: 0.35,
        GENERATING: 0.7,
        COMPLETE: 1.0,
        FAILED: 1.0,
    }.get(status, 0.05)


def _status_class(status: str) -> str:
    return {
        WAITING: "waiting",
        LOADING: "loading",
        GENERATING: "generating",
        COMPLETE: "complete",
        FAILED: "failed",
    }.get(status, "waiting")


def to_rail_statuses(
    statuses: dict[str, str] | None = None,
    runs: list | None = None,
) -> dict[str, str]:
    """Normalize departure-board / ModelRun states for the hero rail dots.

    Accepts either the live `statuses` map (waiting/loading/generating/
    complete/failed) or a list of `ModelRun`, preferring terminal run states.
    """
    out: dict[str, str] = {}
    if statuses:
        out.update(dict(statuses))
    if runs:
        for r in runs:
            mid = getattr(r, "model_id", None)
            if not mid:
                continue
            rs = getattr(r, "status", "")
            if rs == "completed":
                out[mid] = "complete"
            elif rs in {"failed", "timed_out", "unsupported", "cancelled"}:
                out[mid] = "failed"
            else:
                out.setdefault(mid, str(rs or "waiting"))
    return out


def render_progress(st, models: list, statuses: dict[str, str], details: dict[str, str] | None = None):
    details = details or {}
    theme.inject(st)
    st.markdown(theme.section("Departures", "one runner at a time"), unsafe_allow_html=True)

    rows = []
    for m in models:
        st_status = statuses.get(m.id, WAITING)
        detail = details.get(m.id, "")
        pct = _fraction(st_status) * 100
        active = " is-active" if st_status in {LOADING, GENERATING} else ""
        status_cls = _status_class(st_status)
        detail_html = f'<div class="tm-meta">{detail}</div>' if detail else ""
        rows.append(
            f'<div class="tm-dep-row{active}">'
            f'<div class="tm-dep-year">{m.display_year}</div>'
            f"<div><strong>{m.display_name}</strong>{detail_html}</div>"
            f'<div class="tm-dep-status {status_cls}">{st_status}</div>'
            f'<div class="tm-dep-track"><i style="width:{pct:.0f}%"></i></div>'
            f'<div class="tm-meta">{m.mode[:4]}</div>'
            "</div>"
        )
    st.markdown(
        f'<div class="tm-departure tm-fade">{"".join(rows)}</div>',
        unsafe_allow_html=True,
    )
    st.caption("Results reveal as soon as each model finishes.")
