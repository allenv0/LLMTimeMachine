"""Diary re-run: explicit multi-session replay when a cohort gains year slots.

Never silent. Creates a new trip per entry and links it (local-v3-longitudinal).
"""

from __future__ import annotations

from collections.abc import Callable
from typing import Any

from llm_time_machine.domain import Cohort, ModelSpec, TripManifest
from llm_time_machine.diary import DiaryStore


def select_rerun_models(cohort: Cohort, mode: str = "full") -> list[ModelSpec]:
    if mode == "full":
        return list(cohort.models)
    if mode == "tour":
        from llm_time_machine.cohort_catalog import CohortCatalog

        # Prefer catalog tour selection when registry root is available via cohort only.
        # Fallback: oldest base → mid instruction → newest chat.
        models = sorted(cohort.models, key=lambda m: (m.display_year, m.id))
        if len(models) <= 3:
            return models
        by_mode: dict[str, list[ModelSpec]] = {}
        for m in models:
            by_mode.setdefault(m.mode, []).append(m)
        picked: list[ModelSpec] = []
        for mode_name in ("base_continuation", "instruction", "chat"):
            pool = by_mode.get(mode_name) or []
            if not pool:
                continue
            if mode_name == "base_continuation":
                picked.append(pool[0])
            elif mode_name == "chat":
                picked.append(pool[-1])
            else:
                picked.append(pool[len(pool) // 2])
        if len(picked) == 3:
            picked.sort(key=lambda m: (m.display_year, m.id))
            return picked
        return [models[0], models[len(models) // 2], models[-1]]
    raise ValueError(f"unknown diary re-run mode: {mode}")


class DiaryRerunService:
    """Explicit re-run of diary entries against the current cohort.

    Gate D5: register clue → runs at T0 and T1 → first-solved updates.
    Email is cloud-only; local stub is an .ics/todo reminder the user exports.
    """

    def __init__(
        self,
        diary: DiaryStore,
        controller: Any,
        cohort: Cohort,
    ) -> None:
        self.diary = diary
        self.controller = controller
        self.cohort = cohort

    def plan(self, entry_id: str, mode: str = "full") -> dict:
        entry = self.diary.get(entry_id)
        models = select_rerun_models(self.cohort, mode=mode)
        return {
            "entry_id": entry_id,
            "preview": entry.preview,
            "mode": mode,
            "cohort_id": self.cohort.cohort_id,
            "model_ids": [m.id for m in models],
            "years": [m.display_year for m in models],
            "n_existing_trips": len(entry.trips),
            "n_existing_reruns": len(entry.reruns),
        }

    def rerun_entry(
        self,
        entry_id: str,
        *,
        mode: str = "full",
        on_status: Callable[[str, str, str], None] | None = None,
        hardware_summary: dict[str, Any] | None = None,
        block_network_during_trip: bool = True,
    ) -> TripManifest:
        """Explicit re-run. Links the new trip and records a rerun ref."""
        entry = self.diary.get(entry_id)
        raw_prompt = self.diary.read_prompt(entry_id)
        models = select_rerun_models(self.cohort, mode=mode)
        trip_id = f"rerun-{entry_id}-{mode}-{len(entry.reruns) + 1}"
        manifest = self.controller.run_trip(
            raw_prompt,
            success_criterion=entry.success_criterion,
            trip_id=trip_id,
            on_status=on_status,
            hardware_summary=hardware_summary,
            models=models,
            block_network_during_trip=block_network_during_trip,
        )
        # Annotate manifest diary linkage if the writer left a mutable manifest in memory;
        # persist via store when available.
        try:
            stored = self.controller.store.read_manifest(manifest.trip_id)
            stored.diary_entry_id = entry_id
            stored.diary_rerun_mode = mode
            self.controller.store.update_manifest(manifest.trip_id, stored)
        except Exception:
            pass
        self.diary.record_rerun(
            entry_id, manifest.trip_id, mode=mode, cohort_id=self.cohort.cohort_id
        )
        return manifest

    def first_solved_timeline(self) -> list[dict]:
        years = {m.id: m.display_year for m in self.cohort.models}
        return self.diary.first_solved_timeline(model_years=years)

    def ics_reminder_stub(self, entry_id: str, due_date: str = "2027-03-01") -> str:
        """Local ICS/todo stub. No outbound email from the laptop app (local-v3)."""
        entry = self.diary.get(entry_id)
        return (
            "BEGIN:VCALENDAR\n"
            "VERSION:2.0\n"
            "PRODID:-//LLMTimeMachine//local-v3//EN\n"
            "BEGIN:VEVENT\n"
            f"UID:tm-diary-{entry.entry_id}@localhost\n"
            f"DTSTART;VALUE=DATE:{due_date.replace('-', '')}\n"
            "SUMMARY:Re-run LLMTimeMachine diary entry\n"
            f"DESCRIPTION:Re-run diary entry {entry.entry_id} after a new cohort ships. "
            "Local reminder only — no email is sent from this app.\n"
            "END:VEVENT\n"
            "END:VCALENDAR\n"
        )
