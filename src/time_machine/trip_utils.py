"""Shared trip helpers with no imports from trip_service/trip_controller."""

from __future__ import annotations

import hashlib


def hash_prompt(raw_prompt: str) -> str:
    """SHA-256 of the exact raw prompt (manifest stores only the hash)."""
    return hashlib.sha256(raw_prompt.encode("utf-8")).hexdigest()


def blind_mapping_for_trip(trip_id: str, model_ids: list[str]) -> dict[str, str]:
    """Stable per-trip mapping model_id -> A..E. Different trips differ."""
    labels = list("ABCDE")[: len(model_ids)]
    seed = hashlib.sha256(f"blind:{trip_id}".encode("utf-8")).hexdigest()
    ordered = sorted(
        model_ids,
        key=lambda mid: hashlib.sha256(f"{seed}:{mid}".encode("utf-8")).hexdigest(),
    )
    return {mid: labels[i] for i, mid in enumerate(ordered)}
