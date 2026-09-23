"""Sequential trip orchestration compatibility wrapper.

Prefer TripController for new callers. This module must not be imported by
trip_controller (helpers live in trip_utils to avoid cycles).
"""

from __future__ import annotations

from collections.abc import Callable
from typing import TYPE_CHECKING, Any

from time_machine import __version__
from time_machine.artifact_store import ArtifactStore
from time_machine.config import AppPaths, PROTOCOL_VERSION
from time_machine.domain import (
    Cohort,
    GenerationConfig,
    ModelSpec,
    TripManifest,
    UserAnnotations,
)
from time_machine.errors import InputUnsupportedError
from time_machine.evaluation import EvaluationPort, NullEvaluator
from time_machine.runners.base import RunnerProtocol
from time_machine.trip_utils import blind_mapping_for_trip, hash_prompt

if TYPE_CHECKING:
    from time_machine.trip_controller import TripController

StatusCallback = Callable[[str, str, str], None]

__all__ = [
    "TripService",
    "blind_mapping_for_trip",
    "hash_prompt",
    "GenerationConfig",
    "PROTOCOL_VERSION",
]


class TripService:
    """Back-compat wrapper around TripController with a fixed RunnerProtocol."""

    def __init__(
        self,
        cohort: Cohort,
        store: ArtifactStore,
        runner: RunnerProtocol,
        paths: AppPaths | None = None,
        app_version: str = __version__,
        evaluator: EvaluationPort | None = None,
    ) -> None:
        # Lazy import: trip_controller must not import this module at runtime.
        from time_machine.trip_controller import TripController

        self.cohort = cohort
        self.store = store
        self.runner = runner
        self.paths = paths
        self.app_version = app_version
        self._controller = TripController(
            cohort=cohort,
            store=store,
            factory=None,
            paths=paths,
            evaluator=evaluator or NullEvaluator(),
            app_version=app_version,
            runner_kind="fake",
        )
        self._controller.factory = _FixedRunnerFactory(runner)

    def validate_prompt(self, raw_prompt: str, max_chars: int | None = None) -> None:
        self._controller.validate_prompt(raw_prompt, max_chars=max_chars)

    def run_trip(
        self,
        raw_prompt: str,
        success_criterion: str = "",
        *,
        trip_id: str | None = None,
        cancel_check: Callable[[], bool] | None = None,
        on_status: StatusCallback | None = None,
        hardware_summary: dict[str, Any] | None = None,
        models: list[ModelSpec] | None = None,
    ) -> TripManifest:
        return self._controller.run_trip(
            raw_prompt,
            success_criterion=success_criterion,
            trip_id=trip_id,
            cancel_check=cancel_check,
            on_status=on_status,
            hardware_summary=hardware_summary,
            models=models,
            block_network_during_trip=False,
        )

    def save_annotations(self, trip_id: str, annotations: UserAnnotations) -> None:
        self._controller.save_annotations(trip_id, annotations)


class _FixedRunnerFactory:
    """Adapts a single RunnerProtocol into the factory surface."""

    def __init__(self, runner: RunnerProtocol) -> None:
        self._runner = runner

    def create(self, kind: str = "composite") -> RunnerProtocol:
        return self._runner

    def create_for_spec(self, spec: ModelSpec) -> RunnerProtocol:
        return self._runner

    def verify_artifact(self, spec: ModelSpec):
        from time_machine.domain import RunnerAvailability

        return RunnerAvailability(available=True, reason="fixed runner")

    def preflight(self, spec: ModelSpec):
        return self._runner.preflight(spec)
