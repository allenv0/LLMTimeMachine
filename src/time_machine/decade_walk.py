"""Decade walk: reveal one year at a time with a reflection pause (local theater over real runs)."""

from __future__ import annotations

from collections.abc import Callable
from typing import Any

from time_machine.domain import Cohort, ModelSpec, TripManifest


def walk_models(cohort: Cohort, limit_years: list[int] | None = None) -> list[ModelSpec]:
    models = sorted(cohort.models, key=lambda m: (m.display_year, m.id))
    if limit_years is not None:
        allowed = set(limit_years)
        models = [m for m in models if m.display_year in allowed]
    return models


def walk_script(cohort: Cohort) -> list[dict[str, Any]]:
    """Static script rows for the UI before/while running."""
    rows = []
    for m in walk_models(cohort):
        rows.append(
            {
                "model_id": m.id,
                "year": m.display_year,
                "name": m.display_name,
                "mode": m.mode,
                "limitations": list(m.limitations),
            }
        )
    return rows


def run_decade_walk(
    controller: Any,
    raw_prompt: str,
    cohort: Cohort,
    *,
    success_criterion: str = "",
    trip_id_prefix: str = "walk",
    on_reveal: Callable[[ModelSpec, TripManifest, str], None] | None = None,
    on_reflect: Callable[[ModelSpec], str | None] | None = None,
    block_network_during_trip: bool = True,
) -> list[TripManifest]:
    """One trip per year (oldest → newest). Reflection callback may return a note.

    This is a simulation of living through releases — not calendar time.
    """
    manifests: list[TripManifest] = []
    models = walk_models(cohort)
    for i, spec in enumerate(models, start=1):
        trip_id = f"{trip_id_prefix}-{spec.display_year}-{spec.id}"
        manifest = controller.run_trip(
            raw_prompt,
            success_criterion=success_criterion,
            trip_id=trip_id,
            models=[spec],
            block_network_during_trip=block_network_during_trip,
        )
        manifests.append(manifest)
        output = ""
        try:
            output = controller.store.read_output(manifest.trip_id, spec.id)
        except Exception:
            output = ""
        if on_reveal:
            on_reveal(spec, manifest, output)
        if on_reflect:
            _ = on_reflect(spec)
    return manifests
