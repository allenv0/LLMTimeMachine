"""Phase A: diary, ordinal curves, decade walk."""

from __future__ import annotations

import json

import pytest

from llm_time_machine.artifact_store import ArtifactStore
from llm_time_machine.curves import (
    ORDINAL_LABELS,
    build_trip_curve,
    delete_curve,
    ordinal_from_usefulness,
    portfolio_series,
    read_curve,
    write_curve,
)
from llm_time_machine.decade_walk import run_decade_walk, walk_models, walk_script
from llm_time_machine.diary import DiaryStore
from llm_time_machine.domain import CurvePoint, UserAnnotations
from llm_time_machine.evaluation_human import HumanCurveEvaluator
from llm_time_machine.runners.fake import FakeRunner
from llm_time_machine.trip_controller import TripController
from tests.conftest import make_cohort, make_model


@pytest.fixture
def diary(paths):
    return DiaryStore(paths)


def test_ordinal_validation_range():
    UserAnnotations(ordinal={"a": -2})
    UserAnnotations(ordinal={"a": 2})
    with pytest.raises(Exception):
        UserAnnotations(ordinal={"a": 3})
    with pytest.raises(Exception):
        UserAnnotations(ordinal={"a": -3})


def test_usefulness_mapping():
    assert ordinal_from_usefulness("yes") == 1
    assert ordinal_from_usefulness("partly") == 0
    assert ordinal_from_usefulness("no") == -1
    assert ordinal_from_usefulness("unset") is None


def test_curve_skips_unrated_and_prefers_explicit():
    from llm_time_machine.domain import ModelRun, TripManifest

    manifest = TripManifest(
        trip_id="c1",
        protocol_version="local-v1",
        cohort_id="local-v1",
        app_version="1",
        raw_prompt_sha256="0" * 64,
        runs=[
            ModelRun(model_id="a", display_year=2019, display_name="A", status="completed"),
            ModelRun(model_id="b", display_year=2022, display_name="B", status="completed"),
            ModelRun(model_id="c", display_year=2024, display_name="C", status="completed"),
        ],
    )
    ann = UserAnnotations(
        ordinal={"a": -1, "c": 2},
        usefulness={"b": "yes"},
    )
    pts = build_trip_curve(manifest, ann)
    assert [p.model_id for p in pts] == ["a", "b", "c"]
    assert pts[0].ordinal == -1 and pts[0].source == "explicit"
    assert pts[1].ordinal == 1 and pts[1].source == "derived_usefulness"
    assert pts[2].ordinal == 2
    # only ordinal on b absent usefulness → gap
    ann2 = UserAnnotations(ordinal={"a": 1})
    pts2 = build_trip_curve(manifest, ann2)
    assert [p.model_id for p in pts2] == ["a"]


def test_curve_roundtrip_and_delete(paths):
    pts = [
        CurvePoint(model_id="a", display_year=2019, ordinal=-1, display_name="A"),
        CurvePoint(model_id="b", display_year=2024, ordinal=2, display_name="B"),
    ]
    write_curve(paths, "trip-x", pts)
    loaded = read_curve(paths, "trip-x")
    assert [p.model_id for p in loaded] == ["a", "b"]
    delete_curve(paths, "trip-x")
    assert read_curve(paths, "trip-x") == []


def test_portfolio_needs_five_for_band():
    series = {
        f"e{i}": [CurvePoint(model_id=f"m{i}", display_year=2019 + i % 3, ordinal=i % 5 - 2)]
        for i in range(3)
    }
    data = portfolio_series(series)
    assert data["n_prompts"] == 3
    assert data["show_band"] is False
    series5 = {
        f"e{i}": [CurvePoint(model_id=f"m{i}", display_year=2019, ordinal=0)] for i in range(5)
    }
    data5 = portfolio_series(series5)
    assert data5["show_band"] is True


def test_diary_register_link_solve_reflect_delete(diary: DiaryStore):
    entry = diary.register(
        "My grandma clue: Sound of a kettle, almost (4)",
        success_criterion="4 letters",
        tags=["private", "crossword"],
        entry_id="d-test-1",
    )
    assert entry.raw_prompt_sha256
    assert diary.read_prompt("d-test-1").startswith("My grandma")
    index_text = diary.paths.diary_index_path.read_text(encoding="utf-8")
    # long private prompt must not appear whole in index; preview is capped
    full = "My grandma clue: Sound of a kettle, almost (4)"
    assert full not in index_text or len(full) <= 40
    assert entry.preview.endswith("…") or len(entry.preview) <= 40

    diary.link_trip("d-test-1", "trip-abc")
    diary.link_trip("d-test-1", "trip-abc")  # idempotent
    entry = diary.get("d-test-1")
    assert len(entry.trips) == 1

    entry = diary.mark_first_solved("d-test-1", "qwen25-7b-instruct-2024", "trip-abc", mark="user")
    assert entry.solved_mark == "user"
    assert entry.first_solved_model_id == "qwen25-7b-instruct-2024"

    entry = diary.set_reflection("d-test-1", 2019, "still nonsense")
    assert entry.reflections["2019"] == "still nonsense"

    diary.clear_first_solved("d-test-1")
    assert diary.get("d-test-1").solved_mark == "unset"

    assert diary.find_by_prompt_hash(entry.raw_prompt_sha256)
    diary.delete("d-test-1")
    assert diary.list() == []


def test_diary_hash_stable(diary: DiaryStore):
    e1 = diary.register("same prompt", entry_id="d-hash-1")
    matches = diary.find_by_prompt_hash(e1.raw_prompt_sha256)
    assert matches and matches[0].entry_id == "d-hash-1"


def test_human_curve_evaluator_writes_curve(store, paths, diary):
    cohort = make_cohort(
        [make_model("a", 2019, "A", "base_continuation", "identity-v1"),
         make_model("b", 2024, "B", "chat", "fake-chat-v1")]
    )

    class F:
        def create(self, kind="composite"):
            return FakeRunner()

        def create_for_spec(self, spec):
            return FakeRunner()

        def verify_artifact(self, spec):
            from llm_time_machine.domain import RunnerAvailability

            return RunnerAvailability(available=True, reason="ok")

        def preflight(self, spec):
            from llm_time_machine.domain import RunnerAvailability

            return RunnerAvailability(available=True, reason="ok")

    controller = TripController(
        cohort=cohort,
        store=store,
        factory=F(),
        paths=paths,
        evaluator=HumanCurveEvaluator(paths=paths, store=store),
        runner_kind="fake",
    )
    manifest = controller.run_trip("curve me", block_network_during_trip=False)
    ann = UserAnnotations(ordinal={"a": -2, "b": 2})
    controller.save_annotations(manifest.trip_id, ann)
    # save_annotations does not auto-curve; evaluator on next evaluate or manual write
    HumanCurveEvaluator(paths=paths, store=store).evaluate_trip(store.read_manifest(manifest.trip_id))
    pts = read_curve(paths, manifest.trip_id)
    assert [p.ordinal for p in pts] == [-2, 2]


def test_decade_walk_script_and_run(store, paths):
    cohort = make_cohort()
    models = walk_models(cohort)
    assert [m.display_year for m in models] == sorted(m.display_year for m in models)
    script = walk_script(cohort)
    assert len(script) == len(models)

    class F:
        def create(self, kind="composite"):
            return FakeRunner()

        def create_for_spec(self, spec):
            return FakeRunner()

        def verify_artifact(self, spec):
            from llm_time_machine.domain import RunnerAvailability

            return RunnerAvailability(available=True, reason="ok")

        def preflight(self, spec):
            from llm_time_machine.domain import RunnerAvailability

            return RunnerAvailability(available=True, reason="ok")

    controller = TripController(
        cohort=cohort, store=store, factory=F(), paths=paths, runner_kind="fake"
    )
    reflections = {}

    def on_reflect(spec):
        reflections[str(spec.display_year)] = "note"
        return "note"

    manifests = run_decade_walk(
        controller,
        "walk prompt",
        cohort,
        success_criterion="try",
        trip_id_prefix="walk-test",
        on_reflect=on_reflect,
        block_network_during_trip=False,
    )
    assert len(manifests) == 5
    assert all(m.complete for m in manifests)
    assert set(reflections) >= {"2019", "2024"}


def test_ordinals_labels_cover_range():
    assert set(ORDINAL_LABELS) == {-2, -1, 0, 1, 2}
