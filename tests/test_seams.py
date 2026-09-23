"""Tests for seam refactor: catalog, factory, incremental trips, controller, ports."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from time_machine.adapter_catalog import AdapterCatalog
from time_machine.artifact_store import ArtifactStore
from time_machine.cohort_catalog import CohortCatalog
from time_machine.domain import UserAnnotations
from time_machine.evaluation import NullEvaluator, EvaluationPort
from time_machine.network_guard import NetworkBlockedError, block_network
from time_machine.prompt_adapters import prepare_input, render_prepared_text
from time_machine.runners.factory import RunnerFactory
from time_machine.runners.fake import FakeRunner
from time_machine.trip_controller import TripController, make_controller
from tests.conftest import REPO_ROOT, make_cohort, make_model


def test_adapter_catalog_loads_and_renders():
    cat = AdapterCatalog.load(REPO_ROOT / "registry" / "adapters" / "catalog.yaml")
    assert "continuation-v1" in cat.ids()
    text = cat.render("continuation-v1", "Hello")
    assert "Hello" in text
    assert text.startswith("Task: ")
    assert cat.compatible("continuation-v1", "base_continuation")
    assert not cat.compatible("continuation-v1", "chat")


def test_cohort_catalog_lists_and_defaults():
    cat = CohortCatalog(REPO_ROOT)
    listed = cat.list_cohorts()
    assert listed
    ids = {x.get("cohort_id") for x in listed}
    assert "five-era-v1" in ids or "local-v1" in ids
    cohort = cat.default_cohort()
    assert cohort.models
    tour = cat.quick_tour_ids(cohort)
    assert tour
    assert len(tour) <= 3


def test_runner_factory_fake_and_verify(paths):
    factory = RunnerFactory(model_cache=str(paths.model_cache_dir))
    runner = factory.create("fake")
    assert isinstance(runner, FakeRunner)
    from time_machine.domain import ModelSpec

    raw = make_model("m1").model_dump(mode="json")
    raw["source"]["sha256"] = "record-at-preload"
    spec = ModelSpec.model_validate(raw)
    avail = factory.verify_artifact(spec)
    assert avail.available is False
    dest = paths.model_cache_dir / "m1"
    dest.mkdir(parents=True)
    (dest / "model.safetensors").write_bytes(b"abc")
    avail = factory.verify_artifact(spec)
    assert avail.available is True
    assert avail.details.get("sha256")


def test_runner_factory_checksum_mismatch(paths):
    factory = RunnerFactory(model_cache=str(paths.model_cache_dir))
    spec = make_model("m1")
    dest = paths.model_cache_dir / "m1"
    dest.mkdir(parents=True)
    (dest / "model.safetensors").write_bytes(b"abc")
    # pin wrong sha
    data = spec.model_dump(mode="json")
    data["source"]["sha256"] = "b" * 64
    from time_machine.domain import ModelSpec

    bad = ModelSpec.model_validate(data)
    avail = factory.verify_artifact(bad)
    assert avail.available is False
    assert "mismatch" in avail.reason.lower()


def test_incremental_trip_writer_preserves_partial(store: ArtifactStore):
    from time_machine.domain import ModelRun, TripManifest
    from time_machine.artifact_store import sha256_text

    manifest = TripManifest(
        trip_id="inc-trip-1",
        protocol_version="local-v1",
        cohort_id="local-v1",
        app_version="0.1.0",
        raw_prompt_sha256=sha256_text("hi"),
    )
    writer = store.start_trip(manifest)
    writer.begin("hi", "")
    writer.record_run(
        ModelRun(model_id="a", status="completed"),
        prepared_text="prep-a",
        output_text="out-a",
    )
    # simulate crash: no finalize
    loaded = store.read_manifest("inc-trip-1")
    assert loaded.complete is False
    assert loaded.runs[0].model_id == "a"
    assert store.read_output("inc-trip-1", "a") == "out-a"


def test_trip_controller_incremental_and_cancel(store, paths):
    cohort = make_cohort()
    factory = RunnerFactory()
    # force fake factory
    controller = TripController(
        cohort=cohort,
        store=store,
        factory=factory,
        paths=paths,
        runner_kind="fake",
    )
    # one shared runner that fails after 2 successful generations
    shared = FakeRunner(fail_after=2)
    from time_machine.domain import RunnerAvailability

    class F:
        def create(self, kind="composite"):
            return shared

        def create_for_spec(self, spec):
            return shared

        def verify_artifact(self, spec):
            return RunnerAvailability(available=True, reason="ok")

        def preflight(self, spec):
            return RunnerAvailability(available=True, reason="ok")

    controller.factory = F()
    manifest = controller.run_trip("hello seams", block_network_during_trip=False)
    assert manifest.complete is False
    assert len(manifest.runs) == 5
    assert store.read_raw_prompt(manifest.trip_id) == "hello seams"


def test_trip_controller_cancel_midway(store, paths):
    from time_machine.domain import RunnerAvailability

    cohort = make_cohort()

    class OneShot(FakeRunner):
        def __init__(self):
            super().__init__()
            self.n = 0

        def generate(self, prepared, spec, config):
            self.n += 1
            return super().generate(prepared, spec, config)

    holder = {"runner": OneShot()}

    class F:
        def create(self, kind="composite"):
            return holder["runner"]

        def create_for_spec(self, spec):
            return holder["runner"]

        def verify_artifact(self, spec):
            return RunnerAvailability(available=True, reason="ok")

        def preflight(self, spec):
            return RunnerAvailability(available=True, reason="ok")

    controller = TripController(
        cohort=cohort, store=store, factory=F(), paths=paths, runner_kind="fake"
    )
    calls = {"done": 0}

    def on_status(mid, status, detail):
        if status == "complete":
            calls["done"] += 1

    def cancel_check():
        return calls["done"] >= 1

    manifest = controller.run_trip(
        "cancel please",
        cancel_check=cancel_check,
        on_status=on_status,
        block_network_during_trip=False,
    )
    assert manifest.cancelled is True
    assert manifest.runs[0].status == "completed"
    assert all(r.status == "cancelled" for r in manifest.runs[1:])


def test_null_evaluator_port():
    from time_machine.domain import ModelRun, TripManifest

    ev = NullEvaluator()
    assert isinstance(ev, EvaluationPort)
    assert ev.evaluate_run(ModelRun(model_id="x", status="completed"), "y") == {}
    assert ev.evaluate_trip(TripManifest(protocol_version="local-v1", cohort_id="c", app_version="1", raw_prompt_sha256="0"*64)) == {}


def test_network_guard_blocks_connect():
    import socket

    with pytest.raises(NetworkBlockedError):
        with block_network(True):
            socket.create_connection(("127.0.0.1", 1), timeout=0.1)
    # restored afterwards
    assert socket.create_connection is not None


def test_prompt_adapters_use_catalog_when_bound():
    cat = AdapterCatalog.load(REPO_ROOT / "registry" / "adapters" / "catalog.yaml")
    from time_machine import prompt_adapters as pa

    pa.bind_catalog(cat)
    try:
        assert pa.render_prepared_text("instruction-v1", "Zed") == "Zed"
    finally:
        pa.bind_catalog(None)


def test_templates_never_leak_placeholder():
    """Regression: {{prompt}} in YAML must not survive .format() as literal {prompt}."""
    from time_machine import prompt_adapters as pa
    from time_machine.adapter_catalog import AdapterCatalog

    cat = AdapterCatalog.load(REPO_ROOT / "registry" / "adapters" / "catalog.yaml")
    pa.bind_catalog(cat)
    try:
        for aid in cat.ids():
            out = pa.render_prepared_text(aid, "Explain mechanistic interpretability in AI")
            assert "mechanistic interpretability" in out, (aid, out)
            assert "{prompt}" not in out, (aid, out)
        # builtins too
        pa.bind_catalog(None)
        for aid in list(pa._BUILTIN_TEMPLATES):
            out = pa.render_prepared_text(aid, "Explain mechanistic interpretability in AI")
            assert "mechanistic interpretability" in out, (aid, out)
            assert "{prompt}" not in out, (aid, out)
    finally:
        pa.bind_catalog(None)
