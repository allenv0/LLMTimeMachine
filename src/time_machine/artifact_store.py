"""Atomic and incremental local trip artifact store."""

from __future__ import annotations

import hashlib
import json
import os
import re
import shutil
import tempfile
from pathlib import Path
from typing import Any

from time_machine.config import AppPaths
from time_machine.domain import ModelRun, TripManifest, UserAnnotations, utc_now_iso
from time_machine.errors import ArtifactError

_SAFE_ID = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]*$")


def sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


class TripWriter:
    """Incremental, cancel-safe trip directory writer.

    Starts a trip directory, records each ModelRun as it finishes, and
    finalizes once. Crash mid-trip leaves a valid partial manifest on disk.
    """

    def __init__(self, store: "ArtifactStore", manifest: TripManifest) -> None:
        self.store = store
        self.manifest = manifest
        self.dir = store.trip_dir(manifest.trip_id)
        self._started = False

    def begin(self, raw_prompt: str, success_criterion: str) -> Path:
        if self.dir.exists():
            raise ArtifactError(f"trip already exists: {self.manifest.trip_id}")
        self.dir.mkdir(parents=True, exist_ok=False)
        (self.dir / "prepared-inputs").mkdir()
        (self.dir / "outputs").mkdir()
        (self.dir / "raw-prompt.txt").write_text(raw_prompt, encoding="utf-8")
        (self.dir / "success-criterion.txt").write_text(success_criterion or "", encoding="utf-8")
        self.manifest.raw_prompt_sha256 = sha256_text(raw_prompt)
        self.manifest.optional_success_criterion = success_criterion or ""
        self.manifest.runs = []
        self.manifest.complete = False
        self.manifest.cancelled = False
        self._write_manifest()
        (self.dir / "annotations.json").write_text(
            json.dumps(UserAnnotations().model_dump(mode="json"), indent=2, ensure_ascii=False)
            + "\n",
            encoding="utf-8",
        )
        self._started = True
        return self.dir

    def record_run(
        self,
        run: ModelRun,
        prepared_text: str | None = None,
        output_text: str | None = None,
    ) -> None:
        if not self._started:
            raise ArtifactError("TripWriter.begin() must be called first")
        mid = run.model_id
        self.store._validate_trip_id(mid)
        if prepared_text is not None:
            path = self.dir / "prepared-inputs" / f"{mid}.txt"
            path.write_text(prepared_text, encoding="utf-8")
            run.prepared_input_path = f"prepared-inputs/{mid}.txt"
            run.prepared_text = prepared_text
        if output_text is not None:
            path = self.dir / "outputs" / f"{mid}.txt"
            path.write_text(output_text, encoding="utf-8")
            run.output_path = f"outputs/{mid}.txt"
        # replace or append
        self.manifest.runs = [r for r in self.manifest.runs if r.model_id != mid] + [run]
        self._write_manifest()

    def finalize(self, *, cancelled: bool = False, complete: bool = False) -> TripManifest:
        self.manifest.cancelled = cancelled
        self.manifest.complete = complete
        self._write_manifest()
        return self.manifest

    def _write_manifest(self) -> None:
        payload = self.manifest.model_dump(mode="json")
        text = json.dumps(payload, indent=2, ensure_ascii=False) + "\n"
        TripManifest.model_validate(json.loads(text))
        tmp = self.dir / "manifest.json.tmp"
        tmp.write_text(text, encoding="utf-8")
        os.replace(tmp, self.dir / "manifest.json")


class ArtifactStore:
    """Read/write/delete local trip directories under ``local-data/trips``."""

    def __init__(self, paths: AppPaths) -> None:
        self.paths = paths
        # Lock the validated trips root at construction so delete-all cannot be
        # retargeted by mutating paths later.
        self._locked_trips_root = paths.trips_dir.resolve()

    @property
    def trips_root(self) -> Path:
        return self.paths.trips_dir

    def _ensure_root(self) -> Path:
        root = self.trips_root
        root.mkdir(parents=True, exist_ok=True)
        return root

    def _validate_trip_id(self, trip_id: str) -> str:
        if not _SAFE_ID.match(trip_id):
            raise ArtifactError(f"invalid trip id: {trip_id!r}")
        return trip_id

    def trip_dir(self, trip_id: str) -> Path:
        self._validate_trip_id(trip_id)
        root = self._ensure_root()
        candidate = (root / trip_id).resolve()
        if candidate.parent != root.resolve():
            raise ArtifactError("trip path escapes trips root")
        return candidate

    def start_trip(self, manifest: TripManifest) -> TripWriter:
        self._validate_trip_id(manifest.trip_id)
        return TripWriter(self, manifest)

    def write_trip(
        self,
        manifest: TripManifest,
        raw_prompt: str,
        success_criterion: str,
        prepared_inputs: dict[str, str],
        outputs: dict[str, str],
        annotations: UserAnnotations | None = None,
    ) -> Path:
        """Atomic all-at-once write (export/tests). Prefer TripWriter for runs."""
        self._validate_trip_id(manifest.trip_id)
        root = self._ensure_root()
        final = root / manifest.trip_id
        if final.exists():
            raise ArtifactError(f"trip already exists: {manifest.trip_id}")

        tmp_parent = root / ".staging"
        tmp_parent.mkdir(parents=True, exist_ok=True)
        tmp = Path(tempfile.mkdtemp(prefix=f"{manifest.trip_id}.", dir=tmp_parent))
        try:
            (tmp / "prepared-inputs").mkdir()
            (tmp / "outputs").mkdir()
            (tmp / "raw-prompt.txt").write_text(raw_prompt, encoding="utf-8")
            (tmp / "success-criterion.txt").write_text(success_criterion or "", encoding="utf-8")
            for model_id, text in prepared_inputs.items():
                self._write_member(tmp / "prepared-inputs", model_id, text)
            for model_id, text in outputs.items():
                self._write_member(tmp / "outputs", model_id, text)
            ann = annotations or UserAnnotations()
            (tmp / "annotations.json").write_text(
                json.dumps(ann.model_dump(mode="json"), indent=2, ensure_ascii=False) + "\n",
                encoding="utf-8",
            )
            payload = manifest.model_dump(mode="json")
            manifest_text = json.dumps(payload, indent=2, ensure_ascii=False) + "\n"
            TripManifest.model_validate(json.loads(manifest_text))
            (tmp / "manifest.json").write_text(manifest_text, encoding="utf-8")
            for junk in ("export", ".staging"):
                p = tmp / junk
                if p.exists():
                    shutil.rmtree(p, ignore_errors=True)
            os.replace(tmp, final)
        except Exception as exc:
            shutil.rmtree(tmp, ignore_errors=True)
            raise ArtifactError(f"failed to write trip: {exc}") from exc
        return final

    def _write_member(self, folder: Path, model_id: str, text: str) -> None:
        self._validate_trip_id(model_id)
        folder.mkdir(parents=True, exist_ok=True)
        (folder / f"{model_id}.txt").write_text(text, encoding="utf-8")

    def read_manifest(self, trip_id: str) -> TripManifest:
        path = self.trip_dir(trip_id) / "manifest.json"
        if not path.is_file():
            raise ArtifactError(f"manifest missing for trip {trip_id}")
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:
            raise ArtifactError(f"corrupt manifest for {trip_id}: {exc}") from exc
        return TripManifest.model_validate(data)

    def read_raw_prompt(self, trip_id: str) -> str:
        path = self.trip_dir(trip_id) / "raw-prompt.txt"
        if not path.is_file():
            raise ArtifactError(f"raw-prompt missing for trip {trip_id}")
        return path.read_text(encoding="utf-8")

    def read_success_criterion(self, trip_id: str) -> str:
        path = self.trip_dir(trip_id) / "success-criterion.txt"
        if not path.is_file():
            return ""
        return path.read_text(encoding="utf-8")

    def read_prepared_input(self, trip_id: str, model_id: str) -> str:
        path = self.trip_dir(trip_id) / "prepared-inputs" / f"{model_id}.txt"
        if not path.is_file():
            raise ArtifactError(f"prepared input missing: {trip_id}/{model_id}")
        return path.read_text(encoding="utf-8")

    def read_output(self, trip_id: str, model_id: str) -> str:
        path = self.trip_dir(trip_id) / "outputs" / f"{model_id}.txt"
        if not path.is_file():
            raise ArtifactError(f"output missing: {trip_id}/{model_id}")
        return path.read_text(encoding="utf-8")

    def read_annotations(self, trip_id: str) -> UserAnnotations:
        path = self.trip_dir(trip_id) / "annotations.json"
        if not path.is_file():
            return UserAnnotations()
        return UserAnnotations.model_validate(json.loads(path.read_text(encoding="utf-8")))

    def write_annotations(self, trip_id: str, annotations: UserAnnotations) -> None:
        path = self.trip_dir(trip_id) / "annotations.json"
        tmp = path.with_suffix(".json.tmp")
        tmp.write_text(
            json.dumps(annotations.model_dump(mode="json"), indent=2, ensure_ascii=False) + "\n",
            encoding="utf-8",
        )
        os.replace(tmp, path)

    def update_manifest(self, trip_id: str, manifest: TripManifest) -> None:
        path = self.trip_dir(trip_id) / "manifest.json"
        tmp = path.with_suffix(".json.tmp")
        text = json.dumps(manifest.model_dump(mode="json"), indent=2, ensure_ascii=False) + "\n"
        TripManifest.model_validate(json.loads(text))
        tmp.write_text(text, encoding="utf-8")
        os.replace(tmp, path)

    def list_trips(self) -> list[str]:
        root = self.trips_root
        if not root.is_dir():
            return []
        names = []
        for child in sorted(root.iterdir(), key=lambda p: p.name):
            if child.is_dir() and not child.name.startswith(".") and _SAFE_ID.match(child.name):
                if (child / "manifest.json").is_file():
                    names.append(child.name)
        return names

    def delete_trip(self, trip_id: str) -> None:
        path = self.trip_dir(trip_id)
        if not path.exists():
            raise ArtifactError(f"trip not found: {trip_id}")
        shutil.rmtree(path)

    def delete_all_trips(self) -> int:
        root = self.paths.trips_dir.resolve()
        expected = (self.paths.local_data_dir / "trips").resolve()
        if root != expected:
            raise ArtifactError("refusing to delete unexpected trips root")
        if root != self._locked_trips_root:
            raise ArtifactError("refusing to delete trips root that is not the initialized path")
        if root.name != "trips":
            raise ArtifactError("refusing to delete a path that is not named 'trips'")
        if not root.exists():
            return 0
        count = 0
        for child in list(root.iterdir()):
            if child.name.startswith("."):
                continue
            if child.is_dir() and _SAFE_ID.match(child.name):
                shutil.rmtree(child)
                count += 1
            elif child.is_file() and _SAFE_ID.match(child.name):
                child.unlink()
                count += 1
        staging = root / ".staging"
        if staging.is_dir():
            shutil.rmtree(staging, ignore_errors=True)
        return count

    def export_trip_dir(self, trip_id: str) -> Path:
        path = self.trip_dir(trip_id)
        if not (path / "manifest.json").is_file():
            raise ArtifactError(f"trip not found: {trip_id}")
        return path
