"""Wave 1–3: decade spine, local-v3 diary, judge v2/cache, packs, chat, future."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from time_machine.chat_session import (
    CHAT_DERAIL_NOTE,
    ChatService,
    ChatStore,
    prepare_chat_input,
    render_mistral_multi,
    render_qwen_multi,
)
from time_machine.config import AppPaths
from time_machine.cohort_catalog import CohortCatalog
from time_machine.curves_pack import (
    MIN_BAND_N,
    export_compare_pack,
    load_pack,
    make_demonstration_pack,
    pack_overlay,
    save_pack,
    validate_pack,
)
from time_machine.diary import INDEX_SCHEMA_VERSION, DiaryStore
from time_machine.diary_rerun import DiaryRerunService, select_rerun_models
from time_machine.domain import (
    ChatTurn,
    CurvePack,
    CurvePackCurve,
    CurvePackPoint,
    JudgeScore,
    YearHole,
)
from time_machine.errors import ArtifactError, RegistryError
from time_machine.evaluation_judge import JudgeService
from time_machine.future_ensemble import (
    FutureEnsemble,
    future_enabled,
    future_mark_first_solved_allowed,
    member_models,
)
from time_machine.judge_calibration import (
    DEFAULT_CALIBRATION,
    build_report,
    heuristic_gold_for_tests,
    write_report,
)
from time_machine.judge_prompts import load_rubric, parse_judge_reply
from time_machine.registry import validate_cohort_dict
from time_machine.trip_controller import TripController
from time_machine.runners.fake import FakeRunner
from tests.conftest import REPO_ROOT, make_cohort, make_model


class FakeFactory:
    """Factory with verify_artifact so TripController can run fake trips."""

    def create(self, kind="composite"):
        return FakeRunner()

    def create_for_spec(self, spec):
        return FakeRunner()

    def verify_artifact(self, spec):
        from time_machine.domain import RunnerAvailability

        return RunnerAvailability(available=True, reason="ok")

    def preflight(self, spec):
        from time_machine.domain import RunnerAvailability

        return RunnerAvailability(available=True, reason="ok")


# ── Decade spine (WS1) ──────────────────────────────────────────────


def test_decade_cohort_loads_with_holes_and_status_quo():
    catalog = CohortCatalog(REPO_ROOT)
    cohort = catalog.load("decade-v0")
    assert cohort.cohort_id == "decade-v0"
    years = {m.display_year for m in cohort.models}
    hole_years = {h.display_year for h in cohort.timeline_holes}
    assert 2015 in hole_years and 2020 in hole_years and 2026 in hole_years
    assert 2019 in years and 2024 in years
    assert not (years & hole_years)
    assert cohort.status_quo is not None
    assert cohort.status_quo.model_id in {m.id for m in cohort.models}
    # substitutes are labeled
    subs = [m for m in cohort.models if m.slot_status == "substitute"]
    assert subs
    for m in subs:
        assert m.stands_for


def test_timeline_hole_collision_rejected():
    models = [make_model("m2019", 2019)]
    data = {
        "schema_version": "1",
        "cohort_id": "x",
        "protocol_version": "local-v1",
        "prompt": {"max_chars": 900},
        "generation_profile_id": "local-v1",
        "generation_profiles": {
            "local-v1": {
                "id": "local-v1",
                "seed": 1,
                "temperature": 0.7,
                "top_p": 0.95,
                "max_new_tokens": 32,
                "retries": 0,
                "tools_enabled": False,
                "network_enabled": False,
            }
        },
        "models": [m.model_dump(mode="json") for m in models],
        "timeline_holes": [
            {"display_year": 2019, "target_class": "GPT-2", "reason": "dup year"}
        ],
    }
    with pytest.raises(RegistryError):
        validate_cohort_dict(data)


def test_status_quo_must_reference_model():
    m = make_model("m2019", 2019)
    data = {
        "schema_version": "1",
        "cohort_id": "x",
        "protocol_version": "local-v1",
        "prompt": {"max_chars": 900},
        "generation_profile_id": "local-v1",
        "generation_profiles": {
            "local-v1": {
                "id": "local-v1",
                "seed": 1,
                "temperature": 0.7,
                "top_p": 0.95,
                "max_new_tokens": 32,
                "retries": 0,
                "tools_enabled": False,
                "network_enabled": False,
            }
        },
        "models": [m.model_dump(mode="json")],
        "status_quo": {"model_id": "missing", "note": "today"},
    }
    with pytest.raises(RegistryError):
        validate_cohort_dict(data)


def test_substitute_requires_stands_for():
    m = make_model("m2019", 2019)
    dumped = m.model_dump(mode="json")
    dumped["slot_status"] = "substitute"
    dumped["stands_for"] = ""
    data = {
        "schema_version": "1",
        "cohort_id": "x",
        "protocol_version": "local-v1",
        "prompt": {"max_chars": 900},
        "generation_profile_id": "local-v1",
        "generation_profiles": {
            "local-v1": {
                "id": "local-v1",
                "seed": 1,
                "temperature": 0.7,
                "top_p": 0.95,
                "max_new_tokens": 32,
                "retries": 0,
                "tools_enabled": False,
                "network_enabled": False,
            }
        },
        "models": [dumped],
    }
    with pytest.raises(RegistryError):
        validate_cohort_dict(data)


# ── Diary v2 + re-run (WS4) ─────────────────────────────────────────


def test_diary_index_v1_list_migrates_to_v2(paths: AppPaths):
    diary = DiaryStore(paths)
    paths.diary_dir.mkdir(parents=True, exist_ok=True)
    # Write a bare v1 list with one row and a raw prompt on disk.
    eid = "d-legacy01"
    edir = paths.diary_prompts_dir / eid
    edir.mkdir(parents=True, exist_ok=True)
    (edir / "raw-prompt.txt").write_text("legacy prompt", encoding="utf-8")
    v1 = [
        {
            "entry_id": eid,
            "raw_prompt_sha256": "0" * 64,
            "created_at": "2026-01-01T00:00:00+00:00",
            "tags": [],
            "success_criterion": "",
            "trips": [],
            "first_solved_model_id": None,
            "first_solved_trip_id": None,
            "first_solved_at": None,
            "solved_mark": "unset",
            "reflections": {},
            "preview": "legacy prompt",
        }
    ]
    paths.diary_index_path.write_text(json.dumps(v1), encoding="utf-8")
    entries = diary.list()
    assert len(entries) == 1
    data = json.loads(paths.diary_index_path.read_text(encoding="utf-8"))
    assert data["schema_version"] == INDEX_SCHEMA_VERSION
    assert isinstance(data["entries"], list)


def test_diary_rerun_links_trip_and_timeline(paths: AppPaths, store, cohort):
    diary = DiaryStore(paths)
    entry = diary.register("clue from grandma about kettle", success_criterion="correct answer")
    controller = TripController(cohort=cohort, store=store, factory=FakeFactory(), paths=paths, runner_kind="fake")
    rerun = DiaryRerunService(diary, controller, cohort)
    plan = rerun.plan(entry.entry_id, mode="tour")
    assert plan["mode"] == "tour"
    assert plan["model_ids"]
    manifest = rerun.rerun_entry(entry.entry_id, mode="tour", block_network_during_trip=False)
    assert manifest.trip_id.startswith("rerun-")
    entry2 = diary.get(entry.entry_id)
    assert any(r.trip_id == manifest.trip_id for r in entry2.reruns)
    assert any(t.trip_id == manifest.trip_id for t in entry2.trips)
    diary.mark_first_solved(entry.entry_id, cohort.models[-1].id, manifest.trip_id, mark="user")
    rows = rerun.first_solved_timeline()
    assert rows and rows[0]["solved_mark"] == "user"
    assert rows[0]["first_solved_year"] == cohort.models[-1].display_year


def test_diary_ics_stub_has_no_email():
    class _Entry:
        entry_id = "d-x"

    class _D:
        def get(self, entry_id):
            e = _Entry()
            e.entry_id = entry_id
            return e

    from time_machine.diary_rerun import DiaryRerunService

    svc = DiaryRerunService(_D(), None, make_cohort())
    ics = svc.ics_reminder_stub("d-x")
    assert "BEGIN:VCALENDAR" in ics
    assert "no email is sent" in ics
    assert "mailto:" not in ics.lower()


def test_select_rerun_models_tour_has_three_modes_span(cohort):
    models = select_rerun_models(cohort, mode="tour")
    assert len(models) == 3
    modes = {m.mode for m in models}
    assert "base_continuation" in modes and "chat" in modes


# ── Judge v2 JSON + cache (WS2) ─────────────────────────────────────


def test_parse_json_score_and_unscored():
    assert parse_judge_reply('{"score": 8}') == ("scored", 8, "")
    assert parse_judge_reply('{"score": 10}') == ("scored", 10, "")
    status, score, reason = parse_judge_reply('{"unscored": "private fact"}')
    assert status == "unscored" and score is None and "private" in reason
    assert parse_judge_reply('{"score": 99}')[0] == "unscored"
    assert parse_judge_reply('```json\n{"score": 7}\n```') == ("scored", 7, "")
    # still accepts v1 free text
    assert parse_judge_reply("SCORE: 6")[0] == "scored"


def test_rubric_v2_and_judge_v2_load():
    rubric = load_rubric(REPO_ROOT / "registry" / "judges" / "rubric-v2.yaml")
    assert rubric["id"] == "judge-rubric-v2"
    assert rubric.get("parse_mode") == "json"
    from time_machine.judge_prompts import load_judge_config

    cfg = load_judge_config(REPO_ROOT / "registry" / "judges" / "judge-v2.yaml")
    assert cfg["rubric_id"] == "judge-rubric-v2"
    assert cfg["judge_model_id"] != "qwen25-7b-instruct-2024"
    assert cfg.get("cache", {}).get("enabled") is True


def test_judge_prefers_v2_and_caches(paths: AppPaths, store, cohort):
    # Fake factory that records generate calls.
    calls = {"n": 0}

    class _FakeFactory:
        def create_for_spec(self, spec):
            class R:
                def generate(self, prepared, spec, config):
                    calls["n"] += 1
                    from time_machine.domain import GenerationResult, RuntimeInfo

                    return GenerationResult(
                        output_text='{"score": 7}',
                        runtime=RuntimeInfo(backend="fake", backend_version="0", device="cpu"),
                    )

                def unload(self):
                    return None

            return R()

    svc = JudgeService(paths=paths, factory=_FakeFactory())
    assert "v2" in svc.rubric_path.name or "v2" in svc.judge_config_path.name
    # JudgeService fails closed unless the judge weight dir exists (even for fakes).
    judge_ref = str(svc.judge_cfg.get("artifact_from_model_id") or svc.judge_cfg.get("judge_model_id"))
    (paths.model_cache_dir / judge_ref).mkdir(parents=True, exist_ok=True)

    # Build a completed trip via fake runner.
    controller = TripController(
        cohort=cohort, store=store, factory=FakeFactory(), paths=paths, runner_kind="fake"
    )
    manifest = controller.run_trip("score me", models=cohort.models[:1], block_network_during_trip=False)
    scores1 = svc.score_trip(store, manifest.trip_id)
    assert scores1 and scores1[0].status == "scored" and scores1[0].score_1_10 == 7
    n_first = calls["n"]
    assert n_first == 1
    # Second score of same content should hit cache (no new generate).
    scores2 = svc.score_trip(store, manifest.trip_id)
    assert scores2[0].score_1_10 == 7
    assert calls["n"] == n_first
    # cache artifacts exist
    cache_files = list(paths.judge_cache_dir.glob("*.json"))
    assert cache_files


def test_judge_never_auto_scores_on_trip(paths: AppPaths, store, cohort):
    controller = TripController(
        cohort=cohort, store=store, factory=FakeFactory(), paths=paths, runner_kind="fake"
    )
    manifest = controller.run_trip("no silent judge", models=cohort.models[:1], block_network_during_trip=False)
    assert not (paths.judge_dir / manifest.trip_id).exists()


# ── Curve packs (WS3) ───────────────────────────────────────────────


def test_demonstration_pack_has_min_n_and_caveat(paths: AppPaths):
    pack = make_demonstration_pack()
    assert pack.pack_kind == "demonstration"
    assert len(pack.curves) >= 30
    assert "DEMONSTRATION" in pack.caveat or "synthetic" in pack.caveat.lower()
    save_pack(paths, pack)
    loaded = load_pack(paths.curve_packs_dir / f"{pack.pack_id}.json")
    overlay = pack_overlay(loaded)
    assert overlay["show_band"] is True
    assert overlay["n_curves"] >= MIN_BAND_N
    assert "not all of LLM history" in overlay["caption"] or "DEMONSTRATION" in overlay["caption"]
    assert overlay["a11y_summary"]


def test_pack_version_gate_refuses_mismatch():
    with pytest.raises(ArtifactError):
        validate_pack({"pack_id": "x", "schema_version": "curves-pack-v99", "curves": []})


def test_pack_overlay_no_writeback(paths: AppPaths, store, cohort):
    pack = make_demonstration_pack()
    save_pack(paths, pack)
    before = set(p.name for p in paths.trips_dir.glob("*")) if paths.trips_dir.is_dir() else set()
    overlay = pack_overlay(pack)
    assert overlay["n_curves"] == 32
    after = set(p.name for p in paths.trips_dir.glob("*")) if paths.trips_dir.is_dir() else set()
    assert before == after


def test_export_compare_pack(paths: AppPaths, tmp_path: Path):
    pack = make_demonstration_pack()
    out = export_compare_pack(
        my_points=[{"display_year": 2019, "ordinal": -1}, {"display_year": 2024, "ordinal": 2}],
        pack=pack,
        trip_id="t1",
        out_path=tmp_path / "compare.json",
    )
    data = json.loads(out.read_text(encoding="utf-8"))
    assert data["kind"] == "compare-pack-export"
    assert data["pack"]["pack_id"] == pack.pack_id
    assert data["overlay_summary"]["n_curves"] == 32


def test_small_pack_hides_band():
    pack = CurvePack(
        pack_id="tiny",
        pack_kind="empirical",
        curves=[
            CurvePackCurve(
                prompt_sha256="a" * 64,
                points=[CurvePackPoint(year=2019, score_1_10=3), CurvePackPoint(year=2024, score_1_10=8)],
            )
        ],
    )
    overlay = pack_overlay(pack)
    assert overlay["show_band"] is False
    assert overlay["n_curves"] == 1


# ── Chat playground (WS5) ───────────────────────────────────────────


def test_chat_prepare_turn2_contains_turn1_bytes(cohort):
    base = make_model("gpt2-like", 2019, mode="base_continuation", adapter_id="continuation-v1")
    chat_m = make_model("mistral-like", 2023, mode="chat", adapter_id="chat-mistral-v1")
    chat_q = make_model("qwen-like", 2024, mode="chat", adapter_id="chat-qwen-v1")

    history = [
        ChatTurn(turn_index=1, role="user", text="hello there"),
        ChatTurn(turn_index=2, role="assistant", text="hi back"),
    ]
    p_base = prepare_chat_input("what next?", history, base)
    assert "hello there" in p_base.prepared_text
    assert "hi back" in p_base.prepared_text
    assert p_base.adapter_id == "continuation-transcript-v1"
    assert "what next?" in p_base.prepared_text

    p_m = prepare_chat_input("what next?", history, chat_m)
    assert "hello there" in p_m.prepared_text and "hi back" in p_m.prepared_text
    assert "INST" in p_m.prepared_text
    assert p_m.adapter_id == "chat-mistral-multi-v1"

    p_q = prepare_chat_input("what next?", history, chat_q)
    assert "hello there" in p_q.prepared_text and "hi back" in p_q.prepared_text
    assert p_q.adapter_id == "chat-qwen-multi-v1"

    # Multi-turn adapters stay visible; no hidden system prompt in prepared text.
    assert "system" not in p_base.prepared_text.lower()
    assert any("No hidden system prompt" in n for n in p_base.preparation_notes)


def test_chat_service_multi_turn_export(paths: AppPaths, cohort):
    class _Factory:
        def create_for_spec(self, spec):
            class R:
                def generate(self, prepared, spec, config):
                    from time_machine.domain import GenerationResult, RuntimeInfo

                    return GenerationResult(
                        output_text=f"echo:{prepared.prepared_text[-20:]}",
                        runtime=RuntimeInfo(backend="fake", backend_version="0", device="cpu"),
                    )

                def unload(self):
                    return None

            return R()

    store = ChatStore(paths)
    svc = ChatService(store, _Factory(), cohort)
    session = svc.start(cohort.models[0].id)
    t1 = svc.send(session.session_id, "turn one", block_network_during_turn=False)
    assert t1.role == "assistant" and t1.text
    t2 = svc.send(session.session_id, "turn two", block_network_during_turn=False)
    assert t2.role == "assistant"
    loaded = store.load(session.session_id)
    # turn-2 prepared contains turn-1 bytes
    user_texts = [t.text for t in loaded.turns if t.role == "user"]
    assert user_texts == ["turn one", "turn two"]
    prepared2 = store.read_turn_prepared(session.session_id, 2)
    assert "turn one" in prepared2
    out = svc.export_session(session.session_id)
    data = json.loads(out.read_text(encoding="utf-8"))
    assert "prepared_inputs" in data and "outputs" in data
    assert data["derail_note"] == CHAT_DERAIL_NOTE


def test_chat_over_limit_fails_visible(cohort):
    tiny = make_model("tiny", 2019, input_limit_chars=20)
    with pytest.raises(Exception):
        prepare_chat_input("x" * 50, [], tiny)


# ── FUTURE (WS6) ────────────────────────────────────────────────────


def test_future_disabled_by_default():
    catalog = CohortCatalog(REPO_ROOT)
    cohort = catalog.load("decade-v0")
    assert cohort.future is not None
    assert future_enabled(cohort) is False
    assert future_mark_first_solved_allowed(False) is False
    assert future_mark_first_solved_allowed(True) is True


def test_future_ensemble_selects_and_quarantines(cohort):
    # enable a future slot on a fixture cohort
    cohort.future = type(cohort.future)(
        enabled=True,
        member_model_ids=[cohort.models[0].id, cohort.models[-1].id],
        selection_rule="highest length then model_id",
        n_seeds=2,
    ) if cohort.future else None
    if cohort.future is None:
        from time_machine.domain import FutureSlot

        cohort.future = FutureSlot(
            enabled=True,
            member_model_ids=[cohort.models[0].id, cohort.models[-1].id],
            selection_rule="highest length then model_id",
            n_seeds=2,
        )
    assert future_enabled(cohort)
    members = member_models(cohort)
    assert len(members) == 2

    class _Factory:
        def create_for_spec(self, spec):
            class R:
                def generate(self, prepared, spec, config):
                    from time_machine.domain import GenerationResult, RuntimeInfo

                    return GenerationResult(
                        output_text="x" * (10 + config.seed % 5),
                        runtime=RuntimeInfo(backend="fake", backend_version="0", device="cpu"),
                    )

                def unload(self):
                    return None

            return R()

    from time_machine.prompt_adapters import prepare_input

    ens = FutureEnsemble(cohort, _Factory())
    result = ens.run("hi", prepare_fn=prepare_input, block_network_during_trip=False)
    assert result["future_synthetic"] is True
    assert result["n_candidates"] == 4  # 2 members × 2 seeds
    assert result["selection_rule"]
    assert "Not a historical year" in result["quarantine_note"] or "Synthetic" in result["quarantine_note"]


# ── Calibration (WS2) ───────────────────────────────────────────────


def test_calibration_report_bias_visible(paths: AppPaths):
    judgments = heuristic_gold_for_tests()
    report = build_report(
        judgments, calibration_id="gold-v1", judge_id="judge-flan-v2", rubric_id="judge-rubric-v2"
    )
    assert report["n_items"] == len(DEFAULT_CALIBRATION)
    assert report["n_unscored"] >= 1
    assert report["bias"] is not None
    # hallucination cases are over-scored in the heuristic stand-in
    assert report["bias"]["mean_delta"] > 0
    assert "never silently rewrites" in report["note"]
    write_report(paths, report)
    assert (paths.judge_calibration_dir / "gold-v1" / "report.json").is_file()


# ── Timeline UI helpers ─────────────────────────────────────────────


def test_spine_rows_include_holes_and_models():
    from time_machine.ui.timeline import spine_rows

    catalog = CohortCatalog(REPO_ROOT)
    cohort = catalog.load("decade-v0")
    rows = spine_rows(cohort)
    kinds = {r["kind"] for r in rows}
    assert kinds == {"model", "hole"}
    years = [r["year"] for r in rows]
    assert years == sorted(years)
    hole_rows = [r for r in rows if r["kind"] == "hole"]
    assert all(r["reason"] for r in hole_rows)
