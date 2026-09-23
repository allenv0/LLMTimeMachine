"""LLM Time Machine — local Streamlit entrypoint (thin UI shell).

Launch (loopback only):

    streamlit run app.py --server.address 127.0.0.1 --server.port 8501
"""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / "src"))

import streamlit as st

from time_machine import __version__
from time_machine.artifact_store import ArtifactStore
from time_machine.config import APP_NAME, default_paths, debug_content_enabled
from time_machine.cohort_catalog import CohortCatalog
from time_machine.chat_session import ChatService, ChatStore
from time_machine.curves import build_trip_curve, write_curve
from time_machine.diary import DiaryStore
from time_machine.diary_rerun import DiaryRerunService
from time_machine.domain import UserAnnotations
from time_machine.evaluation_human import HumanCurveEvaluator
from time_machine.evaluation_judge import JudgeService
from time_machine.preflight import hardware_summary
from time_machine.trip_controller import TripController
from time_machine.runners.factory import RunnerFactory
from time_machine.ui import (
    blind_compare,
    chat as chat_ui,
    curves as curves_ui,
    decade_walk as decade_walk_ui,
    diary as diary_ui,
    diary_rerun as diary_rerun_ui,
    judge as judge_ui,
    landing,
    local_data,
    pack_overlay as pack_overlay_ui,
    prompt_form,
    progress,
    quick_tour,
    results,
    timeline as timeline_ui,
)

st.set_page_config(page_title=APP_NAME, page_icon="⏳", layout="wide")


@st.cache_resource
def load_static():
    paths = default_paths(ROOT)
    catalog = CohortCatalog(ROOT)
    if paths.cohort_file is None:
        cohort = catalog.default_cohort()
    else:
        cohort = catalog.load_file(paths.cohort_file)
    store = ArtifactStore(paths)
    factory = RunnerFactory(model_cache=str(paths.model_cache_dir))
    diary = DiaryStore(paths)
    judge = JudgeService(paths=paths, factory=factory)
    chat_store = ChatStore(paths)
    chat = ChatService(chat_store, factory, cohort)
    return paths, catalog, cohort, store, factory, diary, judge, chat_store, chat


def _controller(store, factory, cohort, paths, kind: str) -> TripController:
    return TripController(
        cohort=cohort,
        store=store,
        factory=factory,
        paths=paths,
        evaluator=HumanCurveEvaluator(paths=paths, store=store),
        runner_kind=kind,
    )


def _save_curve(paths, store, cohort, trip_id: str, annotations: UserAnnotations) -> int:
    manifest = store.read_manifest(trip_id)
    points = build_trip_curve(manifest, annotations, cohort=cohort)
    if points:
        write_curve(
            paths,
            trip_id,
            points,
            meta={"protocol": manifest.protocol_version, "cohort_id": manifest.cohort_id},
        )
    return len(points)


def main() -> None:
    paths, catalog, cohort, store, factory, diary, judge, chat_store, chat = load_static()

    if debug_content_enabled():
        st.warning("Development content logging is enabled (TIME_MACHINE_DEBUG_CONTENT).")

    landing.render_landing(st, paths.protocol_path, cohort)
    if cohort.cohort_id != "local-v1":
        st.warning(
            f"**Limitation banner:** active cohort is `{cohort.cohort_id}` "
            "(hardware-profile substitute / decade spine), not the standard `local-v1` five-model cohort."
        )
    timeline_ui.render_decade_spine(st, cohort)

    with st.sidebar:
        st.header("Session")
        st.write(f"App version `{__version__}`")
        st.write(f"Protocol `{cohort.protocol_version}`")
        st.write(f"Cohort `{cohort.cohort_id}` · {len(cohort.models)} models")
        st.selectbox(
            "Runner",
            ["composite", "fake", "transformers", "quantized"],
            key="runner_mode",
            help="composite = transformers + llama.cpp by backend. fake = no weights.",
        )
        if st.checkbox("Show preflight", value=False):
            st.json(hardware_summary(paths))
        st.caption("Bind address must remain 127.0.0.1. No remote inference.")

    raw_prompt, criterion, trip_scope = prompt_form.render_prompt_form(
        st, cohort, paths.starter_prompts_path
    )

    if trip_scope and not st.session_state.get("trip_running"):
        st.session_state["trip_running"] = True
        st.session_state.pop("active_trip_id", None)
        try:
            kind = st.session_state.get("runner_mode", "composite")
            controller = _controller(store, factory, cohort, paths, kind)
            if trip_scope == "tour":
                run_models = catalog.quick_tour_models(cohort)
            else:
                run_models = list(cohort.models)
            st.session_state["trip_scope"] = trip_scope
            statuses = progress.initial_statuses(run_models)
            details: dict[str, str] = {}
            status_slot = st.empty()
            detail_state = {"statuses": statuses, "details": details}

            def on_status(mid: str, status: str, detail: str) -> None:
                detail_state["statuses"] = progress.apply_status(
                    detail_state["statuses"], mid, status
                )
                detail_state["details"][mid] = detail
                with status_slot.container():
                    progress.render_progress(
                        st, run_models, detail_state["statuses"], detail_state["details"]
                    )

            with status_slot.container():
                progress.render_progress(st, run_models, statuses, details)

            manifest = controller.run_trip(
                raw_prompt,
                success_criterion=criterion,
                on_status=on_status,
                hardware_summary=hardware_summary(paths),
                models=run_models,
                block_network_during_trip=(kind != "fake"),
            )
            st.session_state["active_trip_id"] = manifest.trip_id
        except Exception as exc:
            st.error(f"Trip failed to start: {exc}")
        finally:
            st.session_state["trip_running"] = False

    trip_id = st.session_state.get("active_trip_id")
    if trip_id:
        manifest = store.read_manifest(trip_id)
        raw = store.read_raw_prompt(trip_id)
        outputs: dict[str, str] = {}
        prepared: dict[str, str] = {}
        for run in manifest.runs:
            if run.output_path and run.status == "completed":
                try:
                    outputs[run.model_id] = store.read_output(trip_id, run.model_id)
                except Exception:
                    outputs[run.model_id] = ""
            if run.prepared_input_path:
                try:
                    prepared[run.model_id] = store.read_prepared_input(trip_id, run.model_id)
                except Exception:
                    prepared[run.model_id] = run.prepared_text or ""
        annotations = store.read_annotations(trip_id)
        controller = _controller(store, factory, cohort, paths, "fake")

        trip_models = [m for m in cohort.models if m.id in {r.model_id for r in manifest.runs}]
        if not trip_models:
            trip_models = list(cohort.models)

        tab_results, tab_curve, tab_judge, tab_blind, tab_diary, tab_walk, tab_chat, tab_data = st.tabs(
            [
                "Results",
                "Progress curve",
                "Judge estimate",
                "Blind compare",
                "Diary",
                "Decade walk",
                "Playground chat",
                "Local data",
            ]
        )
        with tab_results:
            quick_tour.render_progress_arc(st, trip_models, manifest.runs, outputs)
            st.divider()
            updated = results.render_result_cards(
                st, cohort, manifest, raw, outputs, prepared, annotations
            )
            if updated.model_dump(mode="json") != annotations.model_dump(mode="json"):
                if st.button("Save annotations"):
                    controller.save_annotations(trip_id, updated)
                    n = _save_curve(paths, store, cohort, trip_id, updated)
                    st.success(f"Saved locally. Curve points: {n}.")
        with tab_curve:
            trip_points = curves_ui.render_trip_curve(st, cohort, manifest, annotations)
            # portfolio across diary-linked rated trips
            series = {}
            for e in diary.list():
                pts = []
                for t in e.trips:
                    try:
                        m = store.read_manifest(t.trip_id)
                        ann = store.read_annotations(t.trip_id)
                        pts.extend(build_trip_curve(m, ann, cohort=cohort))
                    except Exception:
                        continue
                if pts:
                    series[e.entry_id] = pts
            curves_ui.render_portfolio(st, series)
            pack_overlay_ui.render_pack_overlay(
                st,
                paths,
                my_points=[p.model_dump(mode="json") for p in trip_points],
                trip_id=trip_id,
            )
        with tab_judge:
            scores = judge_ui.render_score_action(st, judge, store, manifest)
            if scores:
                judge_ui.render_estimated_curve(st, scores)
        with tab_blind:
            updated_b = blind_compare.render_blind_compare(
                st, cohort, manifest, outputs, annotations
            )
            if updated_b.model_dump(mode="json") != annotations.model_dump(mode="json"):
                if st.button("Save blind ranking"):
                    controller.save_annotations(trip_id, updated_b)
                    st.success("Saved locally.")
        with tab_diary:
            diary_ui.render_diary_panel(
                st, diary, active_trip_id=trip_id, raw_prompt=raw
            )
            rerun = DiaryRerunService(diary, controller, cohort)
            diary_rerun_ui.render_diary_rerun(st, rerun, diary)
            diary_rerun_ui.render_first_solved_timeline(st, rerun.first_solved_timeline())
        with tab_walk:
            decade_walk_ui.render_decade_walk(
                st,
                cohort=cohort,
                diary=diary,
                controller=controller,
                hardware_summary=hardware_summary(paths),
            )
        with tab_chat:
            chat_ui.render_chat_panel(st, chat, chat_store, cohort)
        with tab_data:
            local_data.render_local_data_panel(st, store, trip_id=trip_id)
    else:
        tab_spine, tab_diary, tab_walk, tab_chat, tab_data = st.tabs(
            ["Decade spine", "Diary", "Decade walk", "Playground chat", "Local data"]
        )
        with tab_spine:
            timeline_ui.render_decade_spine(st, cohort)
        with tab_diary:
            diary_ui.render_diary_panel(st, diary, active_trip_id=None, raw_prompt="")
            walk_controller = _controller(
                store, factory, cohort, paths, st.session_state.get("runner_mode", "fake")
            )
            rerun = DiaryRerunService(diary, walk_controller, cohort)
            diary_rerun_ui.render_diary_rerun(st, rerun, diary)
            diary_rerun_ui.render_first_solved_timeline(st, rerun.first_solved_timeline())
        with tab_walk:
            walk_controller = _controller(store, factory, cohort, paths, st.session_state.get("runner_mode", "fake"))
            decade_walk_ui.render_decade_walk(
                st,
                cohort=cohort,
                diary=diary,
                controller=walk_controller,
                hardware_summary=hardware_summary(paths),
            )
        with tab_chat:
            chat_ui.render_chat_panel(st, chat, chat_store, cohort)
        with tab_data:
            local_data.render_local_data_panel(st, store, trip_id=None)


if __name__ == "__main__":
    main()
