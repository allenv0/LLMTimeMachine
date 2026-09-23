"""Preflight and UI-service contract tests."""

from __future__ import annotations

from time_machine.domain import UserAnnotations
from time_machine.preflight import (
    assess_model,
    hardware_summary,
    recommend_profile,
)
from time_machine.ui import prompt_form, progress
from time_machine.trip_service import TripService
from time_machine.runners.fake import FakeRunner
from tests.conftest import make_cohort, make_model


def test_recommend_profile_buckets():
    gib = 1024**3
    assert recommend_profile(64 * gib, "cpu") == "high"
    assert recommend_profile(32 * gib, "cpu") == "standard"
    assert recommend_profile(16 * gib, "cpu") == "lite"
    assert recommend_profile(None, "cpu") == "unknown"


def test_hardware_summary_keys(paths):
    summary = hardware_summary(paths)
    for key in ("os", "arch", "python_version", "recommended_profile", "runtime_versions"):
        assert key in summary


def test_assess_model_missing_artifact(paths):
    spec = make_model("m1")
    avail = assess_model(spec, paths)
    assert avail.available is False
    assert "preload" in avail.reason.lower()


def test_assess_model_present(paths, monkeypatch):
    from time_machine import preflight as pf

    monkeypatch.setattr(pf, "recommend_profile", lambda mem, kind: "standard")
    monkeypatch.setattr(pf, "detect_memory_bytes", lambda: 32 * 1024**3)
    spec = make_model("m1")
    dest = paths.model_cache_dir / "m1"
    dest.mkdir(parents=True)
    (dest / "model.safetensors").write_bytes(b"fake")
    avail = assess_model(spec, paths)
    assert avail.available is True


def test_assess_model_profile_mismatch(paths, monkeypatch):
    from time_machine import preflight as pf

    monkeypatch.setattr(pf, "recommend_profile", lambda mem, kind: "lite")
    spec = make_model("m1")  # hardware_profile standard
    dest = paths.model_cache_dir / "m1"
    dest.mkdir(parents=True)
    (dest / "model.safetensors").write_bytes(b"fake")
    avail = assess_model(spec, paths)
    assert avail.available is False
    assert "unsupported" in avail.reason.lower()


def test_validate_prompt_form_rules():
    assert prompt_form.validate_prompt_text("", 900) is not None
    assert prompt_form.validate_prompt_text("   ", 900) is not None
    assert prompt_form.validate_prompt_text("ok", 900) is None
    assert prompt_form.validate_prompt_text("x" * 11, 10) is not None


def test_non_english_warning_heuristic():
    assert prompt_form.looks_non_english("你好") is True
    assert prompt_form.looks_non_english("hello") is False


def test_progress_transitions():
    from tests.conftest import make_cohort as mc

    cohort = mc()
    st = progress.initial_statuses(cohort.models)
    assert set(st.values()) == {"waiting"}
    st = progress.apply_status(st, cohort.models[0].id, "loading")
    assert st[cohort.models[0].id] == "loading"
    st = progress.apply_status(st, cohort.models[0].id, "complete")
    assert st[cohort.models[0].id] == "complete"


def test_ui_service_annotation_roundtrip(store, paths):
    cohort = make_cohort()
    service = TripService(cohort, store, FakeRunner(), paths=paths)
    manifest = service.run_trip("ui service")
    ann = UserAnnotations(usefulness={"gpt2-xl-2019": "partly"})
    service.save_annotations(manifest.trip_id, ann)
    assert store.read_annotations(manifest.trip_id).usefulness["gpt2-xl-2019"] == "partly"


def test_starter_prompts_load():
    from pathlib import Path

    path = Path(__file__).resolve().parents[1] / "prompts" / "starter_prompts.jsonl"
    items = prompt_form.load_starter_prompts(path)
    assert len(items) == 5
    cats = {i["category"] for i in items}
    assert "constrained creative writing" in cats
    assert "logic or wordplay" in cats
