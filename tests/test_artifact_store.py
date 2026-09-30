"""Atomic artifact store tests."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from llm_time_machine.artifact_store import ArtifactStore, sha256_text
from llm_time_machine.domain import TripManifest, UserAnnotations
from llm_time_machine.errors import ArtifactError


def _manifest(trip_id: str = "trip-abc") -> TripManifest:
    return TripManifest(
        trip_id=trip_id,
        protocol_version="local-v1",
        cohort_id="local-v1",
        app_version="0.1.0",
        raw_prompt_sha256=sha256_text("hello"),
    )


def test_write_read_roundtrip(store: ArtifactStore):
    manifest = _manifest()
    path = store.write_trip(
        manifest=manifest,
        raw_prompt="hello",
        success_criterion="good",
        prepared_inputs={"m1": "Task: hello"},
        outputs={"m1": "world"},
        annotations=UserAnnotations(),
    )
    assert path.is_dir()
    loaded = store.read_manifest("trip-abc")
    assert loaded.trip_id == "trip-abc"
    assert store.read_raw_prompt("trip-abc") == "hello"
    assert store.read_prepared_input("trip-abc", "m1") == "Task: hello"
    assert store.read_output("trip-abc", "m1") == "world"


def test_atomic_write_no_partial_on_failure(store: ArtifactStore, monkeypatch):
    manifest = _manifest("trip-fail")

    def boom(*args, **kwargs):
        raise RuntimeError("interrupt")

    monkeypatch.setattr(TripManifest, "model_validate", staticmethod(lambda *a, **k: boom()))
    with pytest.raises(ArtifactError):
        store.write_trip(
            manifest=manifest,
            raw_prompt="x",
            success_criterion="",
            prepared_inputs={},
            outputs={},
        )
    assert not (store.trips_root / "trip-fail").exists()


def test_delete_one(store: ArtifactStore):
    store.write_trip(_manifest("trip-1"), "a", "", {}, {}, UserAnnotations())
    store.write_trip(_manifest("trip-2"), "b", "", {}, {}, UserAnnotations())
    store.delete_trip("trip-1")
    assert store.list_trips() == ["trip-2"]


def test_delete_all(store: ArtifactStore):
    store.write_trip(_manifest("trip-1"), "a", "", {}, {}, UserAnnotations())
    store.write_trip(_manifest("trip-2"), "b", "", {}, {}, UserAnnotations())
    n = store.delete_all_trips()
    assert n == 2
    assert store.list_trips() == []


def test_delete_all_path_constrained(paths):
    store = ArtifactStore(paths)
    store.write_trip(_manifest("trip-1"), "a", "", {}, {}, UserAnnotations())
    # force wrong root
    store.paths = paths.model_copy(update={"local_data": paths.root / "elsewhere"})
    with pytest.raises(ArtifactError):
        store.delete_all_trips()


def test_invalid_trip_id_rejected(store: ArtifactStore):
    with pytest.raises(ArtifactError):
        store.trip_dir("../evil")
    with pytest.raises(ArtifactError):
        store.trip_dir("a/b")


def test_duplicate_trip_rejected(store: ArtifactStore):
    store.write_trip(_manifest("dup"), "a", "", {}, {}, UserAnnotations())
    with pytest.raises(ArtifactError):
        store.write_trip(_manifest("dup"), "a", "", {}, {}, UserAnnotations())


def test_annotations_update(store: ArtifactStore):
    store.write_trip(_manifest("ann"), "a", "", {}, {}, UserAnnotations())
    store.write_annotations("ann", UserAnnotations(notes={"m1": "hi"}))
    assert store.read_annotations("ann").notes["m1"] == "hi"
