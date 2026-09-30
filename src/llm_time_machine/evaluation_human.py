"""Human ordinal curve evaluator (Track A). Still protocol local-v1."""

from __future__ import annotations

from llm_time_machine.artifact_store import ArtifactStore
from llm_time_machine.config import AppPaths
from llm_time_machine.curves import build_trip_curve, write_curve
from llm_time_machine.domain import ModelRun, TripManifest
from llm_time_machine.evaluation import EvaluationPort


class HumanCurveEvaluator(EvaluationPort):
    """Derives personal ordinal curves from user annotations. Never invents scores."""

    def __init__(self, paths: AppPaths, store: ArtifactStore | None = None) -> None:
        self.paths = paths
        self.store = store

    def evaluate_run(self, run: ModelRun, output_text: str) -> dict:
        # Per-run machine scoring is out of scope for Track A.
        return {}

    def evaluate_trip(self, manifest: TripManifest) -> dict:
        if self.store is None:
            return {}
        try:
            annotations = self.store.read_annotations(manifest.trip_id)
        except Exception:
            return {}
        cohort = None
        points = build_trip_curve(manifest, annotations, cohort=cohort)
        if not points:
            return {"curve_points": 0, "kind": "human_ordinal"}
        write_curve(
            self.paths,
            manifest.trip_id,
            points,
            meta={"protocol": manifest.protocol_version, "cohort_id": manifest.cohort_id},
        )
        return {
            "curve_points": len(points),
            "kind": "human_ordinal",
            "caption": "Your ratings. Not a scientific measurement.",
        }


__all__ = ["HumanCurveEvaluator", "EvaluationPort"]
