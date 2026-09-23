"""Trip service orchestration tests with the fake runner."""

from __future__ import annotations

from time_machine.domain import UserAnnotations
from time_machine.errors import InputUnsupportedError
from time_machine.runners.fake import FakeRunner
from time_machine.trip_service import TripService, blind_mapping_for_trip
from tests.conftest import make_cohort, make_model


def test_complete_trip(service: TripService):
    manifest = service.run_trip("hello world", success_criterion="be helpful")
    assert manifest.complete is True
    assert manifest.cancelled is False
    assert len(manifest.runs) == 5
    assert all(r.status == "completed" for r in manifest.runs)
    assert manifest.raw_prompt_sha256
    assert service.store.read_raw_prompt(manifest.trip_id) == "hello world"


def test_empty_prompt_rejected(service: TripService):
    try:
        service.run_trip("   ")
        raise AssertionError("expected InputUnsupportedError")
    except InputUnsupportedError:
        pass


def test_over_limit_rejected(service: TripService):
    try:
        service.run_trip("x" * 901)
        raise AssertionError("expected InputUnsupportedError")
    except InputUnsupportedError:
        pass


def test_partial_failure_preserves_completed(store, paths):
    cohort = make_cohort()
    runner = FakeRunner(fail_after=2)
    service = TripService(cohort, store, runner, paths=paths)
    manifest = service.run_trip("partial please")
    statuses = [r.status for r in manifest.runs]
    assert statuses[:2] == ["completed", "completed"]
    assert all(s in {"failed", "completed"} for s in statuses)
    assert manifest.complete is False
    assert service.store.read_raw_prompt(manifest.trip_id) == "partial please"


def test_cancellation_preserves_completed(store, paths):
    cohort = make_cohort()
    runner = FakeRunner()
    service = TripService(cohort, store, runner, paths=paths)
    calls = {"n": 0}

    def cancel_after_one():
        # cancel before second model
        return calls["n"] >= 1

    def on_status(mid, status, detail):
        if status == "complete":
            calls["n"] += 1

    manifest = service.run_trip("cancel me", cancel_check=cancel_after_one, on_status=on_status)
    assert manifest.cancelled is True
    assert manifest.complete is False
    # first completed, remaining cancelled
    assert manifest.runs[0].status == "completed"
    assert all(r.status == "cancelled" for r in manifest.runs[1:])


def test_timeout_status(store, paths):
    cohort = make_cohort([make_model("a", 2019, "A"), make_model("b", 2021, "B")])
    runner = FakeRunner(behaviors={"b": "generation_timeout"})
    service = TripService(cohort, store, runner, paths=paths)
    manifest = service.run_trip("timeout case")
    assert manifest.runs[0].status == "completed"
    assert manifest.runs[1].status == "timed_out"
    assert manifest.runs[1].error_code == "generation_timeout"


def test_load_failure_status(store, paths):
    cohort = make_cohort([make_model("a", 2019, "A")])
    runner = FakeRunner(behaviors={"a": "load_failure"})
    service = TripService(cohort, store, runner, paths=paths)
    manifest = service.run_trip("load fail")
    assert manifest.runs[0].status == "failed"
    assert manifest.runs[0].error_code == "load_failed"


def test_annotations_persist(service: TripService):
    manifest = service.run_trip("annotate me")
    ann = UserAnnotations(
        usefulness={"gpt2-xl-2019": "yes"},
        notes={"gpt2-xl-2019": "solid"},
        failure_tags={"gpt-j-6b-2021": ["irrelevant"]},
    )
    service.save_annotations(manifest.trip_id, ann)
    loaded = service.store.read_annotations(manifest.trip_id)
    assert loaded.usefulness["gpt2-xl-2019"] == "yes"
    assert loaded.failure_tags["gpt-j-6b-2021"] == ["irrelevant"]


def test_blind_mapping_stable_and_distinct():
    ids = ["a", "b", "c", "d", "e"]
    m1 = blind_mapping_for_trip("trip-1", ids)
    m2 = blind_mapping_for_trip("trip-1", ids)
    m3 = blind_mapping_for_trip("trip-2", ids)
    assert m1 == m2
    assert m1 != m3
    assert sorted(m1.values()) == ["A", "B", "C", "D", "E"]
    assert set(m1.keys()) == set(ids)


def test_generation_config_not_mutated(store, paths):
    cohort = make_cohort()
    service = TripService(cohort, store, FakeRunner(), paths=paths)
    before = cohort.generation_profiles["local-v1"].model_dump()
    service.run_trip("config freeze")
    after = cohort.generation_profiles["local-v1"].model_dump()
    assert before == after
