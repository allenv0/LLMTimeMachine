"""Prompt diary: pre-registered private prompts, trips, first-solved, reflections.

Schema v2 (local-v3-longitudinal): versioned index + reruns. Migrations never
rewrite raw-prompt.txt. Full prompt text lives only in raw-prompt.txt.
"""

from __future__ import annotations

import json
import re
import shutil
from pathlib import Path
from uuid import uuid4

from llm_time_machine.artifact_store import sha256_text
from llm_time_machine.config import AppPaths
from llm_time_machine.domain import (
    DiaryRerunRef,
    DiaryTripRef,
    PromptDiaryEntry,
    utc_now_iso,
)
from llm_time_machine.errors import ArtifactError

_SAFE_ID = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]*$")
INDEX_SCHEMA_VERSION = "2"


class DiaryStore:
    """Local-only diary under ``local-data/diary/``.

    Full prompt text is stored only in ``prompts/<id>/raw-prompt.txt``.
    ``index.json`` holds metadata + a short preview (≤40 chars). Short prompts
    may appear in that preview; long private prompts must not appear whole.
    """

    def __init__(self, paths: AppPaths) -> None:
        self.paths = paths

    def _ensure(self) -> None:
        self.paths.diary_prompts_dir.mkdir(parents=True, exist_ok=True)

    def _validate(self, entry_id: str) -> str:
        if not _SAFE_ID.match(entry_id):
            raise ArtifactError(f"invalid diary entry id: {entry_id!r}")
        return entry_id

    def entry_dir(self, entry_id: str) -> Path:
        self._validate(entry_id)
        root = self.paths.diary_prompts_dir.resolve()
        candidate = (root / entry_id).resolve()
        if candidate.parent != root:
            raise ArtifactError("diary path escapes prompts root")
        return candidate

    def _load_index(self) -> dict:
        path = self.paths.diary_index_path
        if not path.is_file():
            return {"schema_version": INDEX_SCHEMA_VERSION, "migrated_at": None, "entries": []}
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:
            raise ArtifactError(f"corrupt diary index: {exc}") from exc
        original_is_v1_list = isinstance(data, list)
        index = self._migrate_index(data)
        # Persist migration so later readers see schema v2.
        if original_is_v1_list or str(index.get("schema_version")) != INDEX_SCHEMA_VERSION:
            self._save_index(index)
        elif not path.is_file():
            self._save_index(index)
        return index

    def _migrate_index(self, data: object) -> dict:
        """Deterministic migration. Bare list = schema v1. Never touches raw prompts."""
        if isinstance(data, list):
            return {
                "schema_version": INDEX_SCHEMA_VERSION,
                "migrated_at": utc_now_iso(),
                "entries": data,
            }
        if not isinstance(data, dict):
            raise ArtifactError("diary index must be a list (v1) or object (v2)")
        entries = data.get("entries")
        if entries is None:
            raise ArtifactError("diary index missing entries")
        if not isinstance(entries, list):
            raise ArtifactError("diary index entries must be a list")
        version = str(data.get("schema_version") or "1")
        if version != INDEX_SCHEMA_VERSION:
            data = dict(data)
            data["schema_version"] = INDEX_SCHEMA_VERSION
            data["migrated_at"] = utc_now_iso()
            # Ensure reruns field exists on every entry (additive).
            migrated = []
            for row in entries:
                if isinstance(row, dict) and "reruns" not in row:
                    row = dict(row)
                    row["reruns"] = []
                migrated.append(row)
            data["entries"] = migrated
        return data

    def _save_index(self, index: dict) -> None:
        self._ensure()
        path = self.paths.diary_index_path
        text = json.dumps(index, indent=2, ensure_ascii=False) + "\n"
        tmp = path.with_suffix(".json.tmp")
        tmp.write_text(text, encoding="utf-8")
        tmp.replace(path)

    def register(
        self,
        raw_prompt: str,
        success_criterion: str = "",
        tags: list[str] | None = None,
        trip_id: str | None = None,
        entry_id: str | None = None,
        preview_chars: int = 40,
    ) -> PromptDiaryEntry:
        """Register a prompt. Full text lives only in raw-prompt.txt.

        ``preview`` is a short local label for lists (≤ preview_chars). Short
        prompts may appear in full there; long prompts are truncated with …
        """
        if not raw_prompt or not raw_prompt.strip():
            raise ArtifactError("diary prompt must not be empty")
        self._ensure()
        eid = entry_id or f"d-{uuid4().hex[:12]}"
        self._validate(eid)
        edir = self.entry_dir(eid)
        if edir.exists():
            raise ArtifactError(f"diary entry already exists: {eid}")
        edir.mkdir(parents=True, exist_ok=False)
        (edir / "raw-prompt.txt").write_text(raw_prompt, encoding="utf-8")
        preview = raw_prompt.strip().replace("\n", " ")
        if len(preview) > preview_chars:
            preview = preview[:preview_chars].rstrip() + "…"
        entry = PromptDiaryEntry(
            entry_id=eid,
            raw_prompt_sha256=sha256_text(raw_prompt),
            created_at=utc_now_iso(),
            tags=list(tags or []),
            success_criterion=success_criterion or "",
            trips=[],
            reruns=[],
            preview=preview,
        )
        if trip_id:
            entry.trips.append(DiaryTripRef(trip_id=trip_id, created_at=utc_now_iso()))
        self._write_entry(entry)
        return entry

    def _write_entry(self, entry: PromptDiaryEntry) -> None:
        edir = self.entry_dir(entry.entry_id)
        edir.mkdir(parents=True, exist_ok=True)
        path = edir / "entry.json"
        text = json.dumps(entry.model_dump(mode="json"), indent=2, ensure_ascii=False) + "\n"
        tmp = path.with_suffix(".json.tmp")
        tmp.write_text(text, encoding="utf-8")
        tmp.replace(path)
        # keep index row in sync
        index = self._load_index()
        items = [e for e in index.get("entries") or [] if e.get("entry_id") != entry.entry_id]
        items.append(entry.model_dump(mode="json"))
        items.sort(key=lambda e: e.get("created_at") or "")
        index["entries"] = items
        index["schema_version"] = INDEX_SCHEMA_VERSION
        self._save_index(index)

    def list(self) -> list[PromptDiaryEntry]:
        out = []
        for row in self._load_index().get("entries") or []:
            try:
                out.append(PromptDiaryEntry.model_validate(row))
            except Exception:
                continue
        return out

    def get(self, entry_id: str) -> PromptDiaryEntry:
        path = self.entry_dir(entry_id) / "entry.json"
        if not path.is_file():
            raise ArtifactError(f"diary entry not found: {entry_id}")
        return PromptDiaryEntry.model_validate(json.loads(path.read_text(encoding="utf-8")))

    def read_prompt(self, entry_id: str) -> str:
        path = self.entry_dir(entry_id) / "raw-prompt.txt"
        if not path.is_file():
            raise ArtifactError(f"diary prompt missing: {entry_id}")
        return path.read_text(encoding="utf-8")

    def link_trip(self, entry_id: str, trip_id: str, note: str = "") -> PromptDiaryEntry:
        entry = self.get(entry_id)
        if any(t.trip_id == trip_id for t in entry.trips):
            return entry
        entry.trips.append(DiaryTripRef(trip_id=trip_id, created_at=utc_now_iso(), note=note))
        self._write_entry(entry)
        return entry

    def record_rerun(
        self,
        entry_id: str,
        trip_id: str,
        *,
        mode: str = "full",
        cohort_id: str = "",
    ) -> PromptDiaryEntry:
        if mode not in {"tour", "full"}:
            raise ArtifactError(f"unknown diary rerun mode: {mode}")
        entry = self.get(entry_id)
        entry.reruns.append(
            DiaryRerunRef(
                trip_id=trip_id,
                created_at=utc_now_iso(),
                mode=mode,
                cohort_id=cohort_id,
            )
        )
        if not any(t.trip_id == trip_id for t in entry.trips):
            entry.trips.append(
                DiaryTripRef(trip_id=trip_id, created_at=utc_now_iso(), note=f"re-run:{mode}")
            )
        self._write_entry(entry)
        return entry

    def mark_first_solved(
        self,
        entry_id: str,
        model_id: str,
        trip_id: str,
        mark: str = "user",
    ) -> PromptDiaryEntry:
        if mark not in {"user", "judge_v2"}:
            raise ArtifactError(f"unknown solved_mark: {mark}")
        entry = self.get(entry_id)
        entry.first_solved_model_id = model_id
        entry.first_solved_trip_id = trip_id
        entry.first_solved_at = utc_now_iso()
        entry.solved_mark = mark
        self._write_entry(entry)
        return entry

    def clear_first_solved(self, entry_id: str) -> PromptDiaryEntry:
        entry = self.get(entry_id)
        entry.first_solved_model_id = None
        entry.first_solved_trip_id = None
        entry.first_solved_at = None
        entry.solved_mark = "unset"
        self._write_entry(entry)
        return entry

    def set_reflection(self, entry_id: str, year: int | str, note: str) -> PromptDiaryEntry:
        entry = self.get(entry_id)
        key = str(year)
        if note.strip():
            entry.reflections[key] = note.strip()
        else:
            entry.reflections.pop(key, None)
        self._write_entry(entry)
        return entry

    def delete(self, entry_id: str) -> None:
        self._validate(entry_id)
        edir = self.entry_dir(entry_id)
        if edir.exists():
            shutil.rmtree(edir)
        index = self._load_index()
        index["entries"] = [
            e for e in index.get("entries") or [] if e.get("entry_id") != entry_id
        ]
        self._save_index(index)

    def find_by_prompt_hash(self, raw_prompt_sha256: str) -> list[PromptDiaryEntry]:
        return [e for e in self.list() if e.raw_prompt_sha256 == raw_prompt_sha256]

    def first_solved_timeline(self, model_years: dict[str, int] | None = None) -> list[dict]:
        """Portfolio timeline of first-solved marks. Gaps stay gaps.

        ``model_years`` maps model_id → display_year when known, so the UI can
        show the year of the solving checkpoint.
        """
        model_years = model_years or {}
        rows: list[dict] = []
        for entry in self.list():
            year = None
            if entry.first_solved_model_id:
                year = model_years.get(entry.first_solved_model_id)
            rows.append(
                {
                    "entry_id": entry.entry_id,
                    "preview": entry.preview,
                    "created_at": entry.created_at,
                    "first_solved_model_id": entry.first_solved_model_id,
                    "first_solved_year": year,
                    "first_solved_trip_id": entry.first_solved_trip_id,
                    "first_solved_at": entry.first_solved_at,
                    "solved_mark": entry.solved_mark,
                    "n_trips": len(entry.trips),
                    "n_reruns": len(entry.reruns),
                    "tags": list(entry.tags),
                }
            )
        rows.sort(key=lambda r: r.get("created_at") or "")
        return rows
