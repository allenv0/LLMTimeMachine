"""Export service tests."""

from __future__ import annotations

from pathlib import Path

import pytest

from time_machine.artifact_store import ArtifactStore
from time_machine.domain import UserAnnotations
from time_machine.errors import ArtifactError
from time_machine.export_service import ExportService
from time_machine.trip_service import TripService
from time_machine.runners.fake import FakeRunner


def test_zip_contains_only_selected_trip(store: ArtifactStore, paths):
    cohort_models_ok = True
    from tests.conftest import make_cohort

    cohort = make_cohort()
    service = TripService(cohort, store, FakeRunner(), paths=paths)
    m1 = service.run_trip("first")
    m2 = service.run_trip("second")
    svc = ExportService(store)
    # inject a temporary export dir that must be excluded
    export_dir = store.trip_dir(m1.trip_id) / "export"
    export_dir.mkdir()
    (export_dir / "junk.txt").write_text("junk", encoding="utf-8")

    out = svc.export_zip(m1.trip_id)
    names = svc.assert_zip_contains_only_trip(out, m1.trip_id)
    assert names
    assert all(n.startswith(f"{m1.trip_id}/") for n in names)
    assert not any("export/" in n for n in names)
    assert not any(m2.trip_id in n for n in names)


def test_json_bundle_fields(store: ArtifactStore, paths):
    from tests.conftest import make_cohort

    cohort = make_cohort()
    service = TripService(cohort, store, FakeRunner(), paths=paths)
    manifest = service.run_trip("bundle me", success_criterion="clear")
    svc = ExportService(store)
    out = svc.export_json_bundle(manifest.trip_id)
    data = __import__("json").loads(out.read_text(encoding="utf-8"))
    assert data["raw_prompt"] == "bundle me"
    assert data["success_criterion"] == "clear"
    assert data["manifest"]["trip_id"] == manifest.trip_id
    assert data["prepared_inputs"]
    assert data["outputs"]


def test_export_missing_trip(store: ArtifactStore):
    svc = ExportService(store)
    with pytest.raises(ArtifactError):
        svc.export_zip("nope-missing")
