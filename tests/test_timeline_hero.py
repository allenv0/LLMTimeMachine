"""Hero rail (Lifeline port): data contract + honesty encoding + markup."""

from __future__ import annotations

import json

from llm_time_machine.cohort_catalog import CohortCatalog
from llm_time_machine.ui import timeline as tl
from llm_time_machine.ui.progress import to_rail_statuses
from tests.conftest import REPO_ROOT


def _decade():
    return CohortCatalog(REPO_ROOT).load("decade-v0")


def test_markers_cover_full_range_with_gap_not_fake():
    cohort = _decade()
    markers = tl.lifeline_markers(cohort)
    years = [m["year"] for m in markers]
    assert years == sorted(years)
    assert years[0] == 2015 and years[-1] == 2026
    # 2017 has no model and no declared hole -> gap, never a fake model.
    gap_2017 = [m for m in markers if m["year"] == 2017]
    assert len(gap_2017) == 1 and gap_2017[0]["kind"] == "gap"
    assert gap_2017[0]["id"] == "gap-2017"
    # Declared holes stay holes with reasons.
    holes = [m for m in markers if m["kind"] == "hole"]
    assert {m["year"] for m in holes} == {2015, 2016, 2018, 2020, 2025, 2026}
    assert all(m["limitations"] for m in holes)
    # Models keep substitute honesty.
    subs = [m for m in markers if m.get("slot_status") == "substitute"]
    assert subs and all(m["stand_for" if "stand_for" in m else "stands_for"] for m in subs)
    # JSON-serializable: the React contract.
    json.dumps(markers)


def test_markers_never_invent_frontier_names():
    cohort = _decade()
    markers = tl.lifeline_markers(cohort)
    labels = " ".join(m["label"] for m in markers)
    for claimed in ("GPT-3", "GPT-1 117M", "Astra", "GLM-5"):
        assert claimed not in labels


def test_status_normalization_for_live_dots():
    cohort = _decade()
    statuses = {
        "gpt2-2019": "completed",
        "gpt2-medium-2021": "loading",
        "flan-t5-large-2022": "failed",
    }
    markers = tl.lifeline_markers(cohort, statuses=statuses)
    by_id = {m["id"]: m for m in markers}
    assert by_id["gpt2-2019"]["status"] == "complete"
    assert by_id["gpt2-medium-2021"]["status"] == "live"
    assert by_id["flan-t5-large-2022"]["status"] == "failed"


def test_to_rail_statuses_prefers_terminal_runs():
    rail = to_rail_statuses(
        statuses={"m1": "generating"},
        runs=[type("R", (), {"model_id": "m1", "status": "completed"})()],
    )
    assert rail["m1"] == "complete"


def test_walk_step_drives_next_done_upcoming():
    cohort = _decade()
    markers = tl.lifeline_markers(cohort, walk_step=0)
    walk = [m for m in markers if m.get("walk_state") is not None]
    assert walk and walk[0]["walk_state"] == "next"
    assert all(m["walk_state"] == "upcoming" for m in walk[1:])

    markers2 = tl.lifeline_markers(cohort, walk_step=2)
    states = [m["walk_state"] for m in markers2 if m.get("walk_state")]
    assert states[:2] == ["done", "done"] and states[2] == "next"

    # Clamped, never raises on out-of-range UI state.
    markers3 = tl.lifeline_markers(cohort, walk_step=999)
    assert all(m["walk_state"] in {"done", "upcoming"} for m in markers3 if m.get("walk_state"))


def test_hero_html_has_shield_playhead_legend_and_motion_guard():
    cohort = _decade()
    markers = tl.lifeline_markers(cohort, walk_step=1)
    doc = tl.hero_rail_html(cohort, markers, mode="walk", intro=True)
    assert "ll-shield" in doc
    assert "ll-playhead" in doc
    assert "next stop" in doc
    assert "ll-legend" in doc
    assert "prefers-reduced-motion" in doc
    assert "ArrowRight" in doc  # keyboard scrub
    assert "scroll-snap" in doc or "scrollSnap" in doc or "snap" in doc
    assert "Status quo (today)" in doc
    assert "derailed" in doc  # quarantined FUTURE, off by default
    # No intro classes on stops when intro=False (Streamlit reruns don't replay).
    # NOTE: the CSS keyframe *definitions* always ship in the island stylesheet.
    doc2 = tl.hero_rail_html(cohort, markers, mode="walk", intro=False)
    assert 'll-marker-intro"' not in doc2
    assert "ll-shield ll-labels-intro" not in doc2


def test_hero_stop_titles_keep_honesty():
    cohort = _decade()
    markers = tl.lifeline_markers(cohort)
    hole = next(m for m in markers if m["kind"] == "hole")
    assert "hole" in tl._marker_title(hole)
    gap = next(m for m in markers if m["kind"] == "gap")
    assert "Gap stays empty" in tl._marker_title(gap)
    sub = next(m for m in markers if m.get("slot_status") == "substitute")
    assert "substitute for" in tl._marker_title(sub)


def test_birth_year_helper():
    cohort = _decade()
    assert tl.lifeline_birth_year(cohort) == 2015
