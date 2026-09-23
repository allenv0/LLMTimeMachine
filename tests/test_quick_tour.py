"""Quick three-era tour: selection, progress arc, subset trips."""

from __future__ import annotations

from time_machine.cohort_catalog import CohortCatalog
from time_machine.runners.fake import FakeRunner
from time_machine.trip_controller import TripController
from time_machine.ui import progress, quick_tour
from tests.conftest import REPO_ROOT, make_cohort, make_model


def test_quick_tour_prefers_mode_coverage():
    cohort = make_cohort()
    cat = CohortCatalog(REPO_ROOT)
    ids = cat.quick_tour_ids(cohort)
    assert len(ids) == 3
    by_id = {m.id: m for m in cohort.models}
    modes = [by_id[i].mode for i in ids]
    assert modes == ["base_continuation", "instruction", "chat"]
    # chronological order, full year span: oldest base → newest chat
    years = [by_id[i].display_year for i in ids]
    assert years == sorted(years)
    assert ids[0] == "gpt2-xl-2019"
    assert ids[-1] == "qwen25-7b-instruct-2024"


def test_quick_tour_models_match_ids():
    cohort = make_cohort()
    cat = CohortCatalog(REPO_ROOT)
    models = cat.quick_tour_models(cohort)
    assert [m.id for m in models] == cat.quick_tour_ids(cohort)
    assert len(models) == 3


def test_quick_tour_small_cohort_uses_all():
    cohort = make_cohort(
        [
            make_model("a", 2019, "A", "base_continuation"),
            make_model("b", 2022, "B", "instruction"),
        ]
    )
    cat = CohortCatalog(REPO_ROOT)
    assert cat.quick_tour_ids(cohort) == ["a", "b"]


def test_quick_tour_fallback_without_full_modes():
    cohort = make_cohort(
        [
            make_model("a", 2019, "A", "base_continuation"),
            make_model("b", 2020, "B", "base_continuation"),
            make_model("c", 2021, "C", "base_continuation"),
            make_model("d", 2022, "D", "base_continuation"),
            make_model("e", 2023, "E", "base_continuation"),
        ]
    )
    cat = CohortCatalog(REPO_ROOT)
    ids = cat.quick_tour_ids(cohort)
    assert ids == ["a", "c", "e"]


def test_pick_arc_models_prefers_modes():
    cohort = make_cohort()
    arc = quick_tour.pick_arc_models(list(cohort.models))
    assert [m.mode for m in arc] == ["base_continuation", "instruction", "chat"]


def test_pick_arc_models_honors_tour_ids():
    cohort = make_cohort()
    tour_ids = ["qwen25-7b-instruct-2024", "gpt2-xl-2019", "flan-t5-xl-2022"]
    arc = quick_tour.pick_arc_models(list(cohort.models), tour_ids=tour_ids)
    assert [m.id for m in arc] == [
        "gpt2-xl-2019",
        "flan-t5-xl-2022",
        "qwen25-7b-instruct-2024",
    ]


def test_progress_initial_statuses_subset():
    cohort = make_cohort()
    models = [cohort.models[0], cohort.models[-1]]
    statuses = progress.initial_statuses(models)
    assert set(statuses) == {models[0].id, models[-1].id}
    assert all(s == progress.WAITING for s in statuses.values())


def test_trip_runs_only_tour_models(store, paths):
    cohort = make_cohort()
    cat = CohortCatalog(REPO_ROOT)
    tour = cat.quick_tour_models(cohort)
    controller = TripController(
        cohort=cohort,
        store=store,
        factory=None,
        paths=paths,
        runner_kind="fake",
    )
    from time_machine.domain import RunnerAvailability

    class F:
        def create(self, kind="composite"):
            return FakeRunner()

        def create_for_spec(self, spec):
            return FakeRunner()

        def verify_artifact(self, spec):
            return RunnerAvailability(available=True, reason="ok")

        def preflight(self, spec):
            return RunnerAvailability(available=True, reason="ok")

    controller.factory = F()
    manifest = controller.run_trip(
        "three era please",
        models=tour,
        block_network_during_trip=False,
    )
    assert len(manifest.runs) == 3
    assert [r.model_id for r in manifest.runs] == [m.id for m in tour]
    assert manifest.complete is True


def test_real_five_era_tour_modes():
    cat = CohortCatalog(REPO_ROOT)
    cohort = cat.load_file(REPO_ROOT / "registry" / "cohort-five-era-v1.yaml")
    ids = cat.quick_tour_ids(cohort)
    by_id = {m.id: m for m in cohort.models}
    modes = [by_id[i].mode for i in ids]
    assert modes == ["base_continuation", "instruction", "chat"]
    assert ids[0] == "gpt2-2019"
    assert ids[-1] == "qwen25-7b-instruct-2024"
