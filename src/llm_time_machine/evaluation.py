"""Evaluation port. local-v1 has no automatic judge.

Future alpha features (LLM-as-judge, quality curves) plug in here without
touching TripService or ArtifactStore.
"""

from __future__ import annotations

from typing import Protocol, runtime_checkable

from llm_time_machine.domain import ModelRun, TripManifest


@runtime_checkable
class EvaluationPort(Protocol):
    """Score or annotate model outputs. Must not be called implicitly by UI."""

    def evaluate_run(self, run: ModelRun, output_text: str) -> dict: ...

    def evaluate_trip(self, manifest: TripManifest) -> dict: ...


class NullEvaluator:
    """Default evaluator for local-v1: stores nothing, scores nothing."""

    def evaluate_run(self, run: ModelRun, output_text: str) -> dict:
        return {}

    def evaluate_trip(self, manifest: TripManifest) -> dict:
        return {}
