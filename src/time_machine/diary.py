"""Prompt diary: pre-registered private prompts, trips, first-solved, reflections."""

from __future__ import annotations

import json
import re
import shutil
from pathlib import Path
from uuid import uuid4

from time_machine.artifact_store import sha256_text
from time_machine.config import AppPaths
from time_machine.domain import DiaryTripRef, PromptDiaryEntry, utc_now_iso
from time_machine.errors import ArtifactError

_SAFE_ID = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]*$")


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

    def _load_index(self) -> list[dict]:
        path = self.paths.diary_index_path
        if not path.is_file():
            return []
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:
            raise ArtifactError(f"corrupt diary index: {exc}") from exc
        if not isinstance(data, list):
            raise ArtifactError("diary index must be a list")
        return data

    def _save_index(self, entries: list[dict]) -> None:
        self._ensure()
        path = self.paths.diary_index_path
        text = json.dumps(entries, indent=2, ensure_ascii=False) + "\n"
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
            preview=preview,
        )
        if trip_id:
            entry.trips.append(DiaryTripRef(trip_id=trip_id, created_at=utc_now_iso()))
        self._write_entry(entry)
        items = self._load_index()
        items.append(entry.model_dump(mode="json"))
        self._save_index(items)
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
        items = self._load_index()
        items = [e for e in items if e.get("entry_id") != entry.entry_id]
        items.append(entry.model_dump(mode="json"))
        items.sort(key=lambda e: e.get("created_at") or "")
        self._save_index(items)

    def list(self) -> list[PromptDiaryEntry]:
        out = []
        for row in self._load_index():
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
        items = [e for e in self._load_index() if e.get("entry_id") != entry_id]
        self._save_index(items)

    def find_by_prompt_hash(self, raw_prompt_sha256: str) -> list[PromptDiaryEntry]:
        return [e for e in self.list() if e.raw_prompt_sha256 == raw_prompt_sha256]
