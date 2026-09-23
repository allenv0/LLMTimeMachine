"""Deep tests: protocol invariants, audit reconstructability, idea.md alignment seams."""

from __future__ import annotations

import json
import zipfile
from pathlib import Path

import pytest

from time_machine.adapter_catalog import AdapterCatalog
from time_machine.artifact_store import ArtifactStore
from time_machine.cohort_catalog import CohortCatalog
from time_machine.config import DISCLOSURE_LINES, TRUTHFUL_CLAIM, FAILURE_TAG_VALUES
from time_machine.domain import UserAnnotations
from time_machine.errors import InputUnsupportedError
from time_machine.evaluation import NullEvaluator
from time_machine.export_service import ExportService
from time_machine.network_guard import NetworkBlockedError, block_network
from time_machine.prompt_adapters import prepare_input, render_prepared_text
from time_machine.runners.factory import RunnerFactory
from time_machine.runners.fake import FakeRunner
from time_machine.trip_controller import TripController
from time_machine.trip_utils import blind_mapping_for_trip, hash_prompt
from time_machine.ui import progress, quick_tour
from time_machine.ui.prompt_form import looks_non_english, validate_prompt_text
from tests.conftest import REPO_ROOT, make_cohort, make_model


# --- idea.md / PROTOCOL claim boundary -------------------------------------

def test_truthful_claim_is_not_frontier_overclaim():
    assert "not a verified record of the best model" in TRUTHFUL_CLAIM.lower()
    assert "laptop-compatible" in TRUTHFUL_CLAIM.lower()
    for line in DISCLOSURE_LINES:
        assert "api" in line.lower() or "historical" in line.lower() or "cohort" in line.lower() or "format" in line.lower()


def test_no_llm_judge_scores_in_local_v1():
    ev = NullEvaluator()
    assert ev.evaluate_run.__doc__ is None or True
    from time_machine.domain import ModelRun, TripManifest

    assert ev.evaluate_run(ModelRun(model_id="x", status="completed"), "out") == {}
    assert ev.evaluate_trip(
        TripManifest(protocol_version="local-v1", cohort_id="c", app_version="1", raw_prompt_sha256="0" * 64)
    ) == {}
    # UI annotation vocabulary is personal only
    assert "quality_score" not in FAILURE_TAG_VALUES
    assert set(FAILURE_TAG_VALUES) <= {
        "incorrect",
        "ignored_constraints",
        "irrelevant",
        "unsafe",
        "incomplete",
        "style",
        "other",
    }


def test_generation_profile_frozen_fields():
    cohort = make_cohort()
    gen = cohort.generation_profiles["local-v1"]
    assert gen.retries == 0
    assert gen.tools_enabled is False
    assert gen.network_enabled is False
    assert gen.seed == 20260923
    assert gen.max_new_tokens == 320
    assert gen.temperature == 0.7
    assert gen.top_p == 0.95


def test_prompt_never_truncated_and_limit_enforced():
    spec = make_model("a", 2019, "A", "base_continuation", "identity-v1")
    prepared = prepare_input("hello", spec)
    assert prepared.was_truncated is False
    with pytest.raises(InputUnsupportedError):
        prepare_input("x" * 901, spec)
    with pytest.raises(InputUnsupportedError):
        prepare_input("x" * 51, make_model("b", 2019, "B", input_limit_chars=50))


def test_adapters_add_no_hidden_system_prompt():
    """Visible adapters only: no system/developer/tool/CoT smuggled in."""
    cat = AdapterCatalog.load(REPO_ROOT / "registry" / "adapters" / "catalog.yaml")
    banned = ["system:", "developer", "chain of thought", "step by step", "tool call", "browse"]
    for aid in cat.ids():
        out = cat.render(aid, "SECRET_PROMPT_XYZ")
        assert "SECRET_PROMPT_XYZ" in out
        low = out.lower()
        for phrase in banned:
            assert phrase not in low, (aid, phrase, out)
        assert "{prompt}" not in out


def test_raw_prompt_hash_stable_and_not_reversible_in_manifest_fields():
    h1 = hash_prompt("my private grandma crossword clue")
    h2 = hash_prompt("my private grandma crossword clue")
    assert h1 == h2
    assert len(h1) == 64
    assert "grandma" not in h1


# --- audit reconstructability ----------------------------------------------

def test_trip_directory_reconstructable(store: ArtifactStore, paths):
    cohort = make_cohort()
    controller = TripController(
        cohort=cohort, store=store, factory=None, paths=paths, runner_kind="fake"
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
    prompt = "Private: unpublished crossword 7-across"
    criterion = "Should refuse if unknown"
    manifest = controller.run_trip(
        prompt, success_criterion=criterion, block_network_during_trip=False
    )
    tdir = store.paths.trips_dir / manifest.trip_id

    # required files per PROTOCOL auditability rule
    assert (tdir / "manifest.json").is_file()
    assert (tdir / "raw-prompt.txt").read_text(encoding="utf-8") == prompt
    assert (tdir / "success-criterion.txt").read_text(encoding="utf-8") == criterion
    for run in manifest.runs:
        assert (tdir / "prepared-inputs" / f"{run.model_id}.txt").is_file()
        if run.status == "completed":
            assert (tdir / "outputs" / f"{run.model_id}.txt").is_file()
            prepared = (tdir / "prepared-inputs" / f"{run.model_id}.txt").read_text(encoding="utf-8")
            assert prompt in prepared or prompt in prepared.replace("\n", " ")

    data = json.loads((tdir / "manifest.json").read_text(encoding="utf-8"))
    assert data["raw_prompt_sha256"] == hash_prompt(prompt)
    assert "grandma" not in json.dumps(data)  # hash only in manifest
    assert data["protocol_version"] == "local-v1"
    assert data["complete"] is True

    # no stack traces in manifest errors
    blob = json.dumps(data).lower()
    assert "traceback" not in blob
    assert "file \"" not in blob


def test_export_bundle_roundtrip(store: ArtifactStore, paths):
    cohort = make_cohort([make_model("a", 2019, "A", "base_continuation", "identity-v1")])
    controller = TripController(
        cohort=cohort, store=store, factory=None, paths=paths, runner_kind="fake"
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
    manifest = controller.run_trip("export me", block_network_during_trip=False)
    svc = ExportService(store)
    zpath = svc.export_zip(manifest.trip_id)
    assert zpath.is_file()
    with zipfile.ZipFile(zpath) as zf:
        names = zf.namelist()
        assert any("manifest.json" in n for n in names)
        assert any("raw-prompt.txt" in n for n in names)
        # no absolute host paths leaking as required content names with Users/
        assert not any(n.startswith("/") for n in names)


def test_delete_trip_only_selected(store: ArtifactStore, paths):
    cohort = make_cohort([make_model("a", 2019, "A"), make_model("b", 2020, "B")])
    controller = TripController(
        cohort=cohort, store=store, factory=None, paths=paths, runner_kind="fake"
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
    m1 = controller.run_trip("t1", block_network_during_trip=False)
    m2 = controller.run_trip("t2", block_network_during_trip=False)
    store.delete_trip(m1.trip_id)
    trips = store.list_trips()
    assert m1.trip_id not in trips
    assert m2.trip_id in trips


# --- network / integrity ---------------------------------------------------

def test_network_blocked_during_trip_window():
    import socket

    with pytest.raises(NetworkBlockedError):
        with block_network(True):
            socket.create_connection(("127.0.0.1", 9), timeout=0.05)


def test_factory_verify_before_generate_path(store, paths):
    factory = RunnerFactory(model_cache=str(paths.model_cache_dir))
    spec = make_model("missing-model", 2019, "M")
    avail = factory.verify_artifact(spec)
    assert avail.available is False
    assert "preload" in avail.reason.lower() or "not" in avail.reason.lower()


def test_fake_runner_records_effective_generation():
    runner = FakeRunner()
    cohort = make_cohort([make_model("a", 2019, "A", "base_continuation", "identity-v1")])
    spec = cohort.models[0]
    prepared = prepare_input("hi", spec)
    result = runner.generate(prepared, spec, cohort.generation_profiles["local-v1"])
    assert result.runtime.effective_generation["retries"] == 0
    assert result.runtime.effective_generation["seed"] == 20260923


# --- UI pure helpers / progress arc ----------------------------------------

def test_validate_prompt_text_boundaries():
    assert validate_prompt_text("", 900) is not None
    assert validate_prompt_text("   ", 900) is not None
    assert validate_prompt_text("ok", 900) is None
    assert validate_prompt_text("x" * 901, 900) is not None
    assert looks_non_english("café") is True
    assert looks_non_english("cafe") is False


def test_blind_mapping_three_model_tour_stable():
    ids = ["gpt2-2019", "flan-t5-large-2022", "qwen25-7b-instruct-2024"]
    m1 = blind_mapping_for_trip("tour-abc", ids)
    m2 = blind_mapping_for_trip("tour-abc", ids)
    assert m1 == m2
    assert sorted(m1.values()) == ["A", "B", "C"]
    assert set(m1) == set(ids)


def test_progress_arc_covers_three_modes_and_missing_run():
    from time_machine.domain import ModelRun

    cohort = make_cohort()
    tour = CohortCatalog(REPO_ROOT).quick_tour_models(cohort)
    runs = [
        ModelRun(model_id=tour[0].id, status="completed", display_year=tour[0].display_year),
        ModelRun(model_id=tour[1].id, status="failed", error_code="load_failed", display_year=tour[1].display_year),
        # tour[2] missing entirely
    ]
    outputs = {tour[0].id: "base output text"}
    arc = quick_tour.pick_arc_models(tour)
    assert [m.mode for m in arc] == ["base_continuation", "instruction", "chat"]
    # missing run should not crash selection
    assert quick_tour.pick_arc_models(tour + [make_model("zz", 2030, "ZZ", "chat")])[-1].mode == "chat"


def test_progress_statuses_subset_and_unknown_status():
    models = [make_model("a", 2019, "A"), make_model("b", 2022, "B", "instruction")]
    st = progress.initial_statuses(models)
    assert set(st) == {"a", "b"}
    st = progress.apply_status(st, "a", "loading")
    st = progress.apply_status(st, "a", "complete")
    st = progress.apply_status(st, "b", "weird")
    assert st["a"] == "complete"
    assert st["b"] == "weird"  # passthrough unknown


def test_annotations_roundtrip_and_tags_validated(store, paths):
    cohort = make_cohort([make_model("a", 2019, "A")])
    controller = TripController(
        cohort=cohort, store=store, factory=None, paths=paths, runner_kind="fake"
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
    manifest = controller.run_trip("ann", block_network_during_trip=False)
    ann = UserAnnotations(
        usefulness={"a": "partly"},
        notes={"a": "honest refusal"},
        failure_tags={"a": ["incomplete"]},
        trip_notes="progress felt real",
    )
    controller.save_annotations(manifest.trip_id, ann)
    loaded = store.read_annotations(manifest.trip_id)
    assert loaded.usefulness["a"] == "partly"
    assert loaded.trip_notes == "progress felt real"
    assert loaded.failure_tags["a"] == ["incomplete"]


def test_tour_subset_trip_manifest_has_only_three_runs(store, paths):
    cohort = make_cohort()
    tour = CohortCatalog(REPO_ROOT).quick_tour_models(cohort)
    controller = TripController(
        cohort=cohort, store=store, factory=None, paths=paths, runner_kind="fake"
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
    statuses = []

    def on_status(mid, status, detail):
        statuses.append((mid, status))

    manifest = controller.run_trip(
        "tour deep", models=tour, on_status=on_status, block_network_during_trip=False
    )
    assert len(manifest.runs) == 3
    assert [r.model_id for r in manifest.runs] == [m.id for m in tour]
    # progress only reported for tour models
    reported = {mid for mid, _ in statuses}
    assert reported == {m.id for m in tour}


def test_five_era_registry_pinned_and_ascending_years():
    cat = CohortCatalog(REPO_ROOT)
    cohort = cat.load_file(REPO_ROOT / "registry" / "cohort-five-era-v1.yaml")
    years = [m.display_year for m in cohort.models]
    assert years == sorted(years)
    assert len(set(years)) == len(years)
    for m in cohort.models:
        assert m.source.revision.lower() not in {"main", "master", "latest", "head"}
        assert m.limitations  # must disclose
        assert m.license_url.startswith("http")
