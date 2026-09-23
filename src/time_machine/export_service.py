"""Portable ZIP/JSON export for a single trip."""

from __future__ import annotations

import json
import zipfile
from pathlib import Path

from time_machine.artifact_store import ArtifactStore
from time_machine.errors import ArtifactError

EXCLUDE_NAMES = {"export", ".staging"}
EXCLUDE_SUFFIXES = {".tmp"}


class ExportService:
    def __init__(self, store: ArtifactStore) -> None:
        self.store = store

    def export_json_bundle(self, trip_id: str, dest: Path | None = None) -> Path:
        trip_dir = self.store.export_trip_dir(trip_id)
        payload = {
            "manifest": json.loads((trip_dir / "manifest.json").read_text(encoding="utf-8")),
            "raw_prompt": self.store.read_raw_prompt(trip_id),
            "success_criterion": self.store.read_success_criterion(trip_id),
            "prepared_inputs": {
                p.stem: p.read_text(encoding="utf-8")
                for p in sorted((trip_dir / "prepared-inputs").glob("*.txt"))
            },
            "outputs": {
                p.stem: p.read_text(encoding="utf-8")
                for p in sorted((trip_dir / "outputs").glob("*.txt"))
            },
            "annotations": self.store.read_annotations(trip_id).model_dump(mode="json"),
        }
        # Optional local-v2-eval judge bundle (derived, may be absent under local-v1).
        try:
            from time_machine.evaluation_judge import JudgeService

            judge = JudgeService(paths=self.store.paths)
            scores = judge.read_scores(trip_id)
            if scores:
                payload["judge_scores"] = [s.model_dump(mode="json") for s in scores]
                payload["judge_rubric"] = judge.rubric
                payload["judge_config_id"] = judge.judge_cfg.get("id")
                payload["judge_banner"] = judge.banner
        except Exception:
            pass
        out = dest or (trip_dir.parent / f"{trip_id}.export.json")
        out = Path(out)
        out.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        return out

    def export_zip(self, trip_id: str, dest: Path | None = None) -> Path:
        trip_dir = self.store.export_trip_dir(trip_id)
        out = dest or (trip_dir.parent / f"{trip_id}.export.zip")
        out = Path(out)
        if out.resolve() == trip_dir.resolve() or trip_dir in out.resolve().parents:
            # keep export next to trips, not inside the trip
            pass
        tmp = out.with_suffix(out.suffix + ".tmp")
        with zipfile.ZipFile(tmp, "w", compression=zipfile.ZIP_DEFLATED) as zf:
            for path in sorted(trip_dir.rglob("*")):
                if not path.is_file():
                    continue
                rel = path.relative_to(trip_dir)
                if rel.parts and rel.parts[0] in EXCLUDE_NAMES:
                    continue
                if path.suffix in EXCLUDE_SUFFIXES:
                    continue
                if any(part in EXCLUDE_NAMES for part in rel.parts):
                    continue
                arcname = f"{trip_id}/{rel.as_posix()}"
                zf.write(path, arcname=arcname)
        tmp.replace(out)
        return out

    def assert_zip_contains_only_trip(self, zip_path: Path, trip_id: str) -> list[str]:
        with zipfile.ZipFile(zip_path) as zf:
            names = zf.namelist()
        for name in names:
            if not name.startswith(f"{trip_id}/"):
                raise ArtifactError(f"export contains foreign path: {name}")
            if "export/" in name or ".staging" in name:
                raise ArtifactError(f"export contains temporary path: {name}")
        return names
