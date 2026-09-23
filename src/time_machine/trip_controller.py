"""UI-agnostic trip orchestration. Streamlit never touches runners directly."""

from __future__ import annotations

import time
from collections.abc import Callable
from typing import Any
from uuid import uuid4

from time_machine import __version__
from time_machine.artifact_store import ArtifactStore
from time_machine.config import AppPaths, PROTOCOL_VERSION
from time_machine.cohort_catalog import CohortCatalog
from time_machine.domain import (
    Cohort,
    GenerationConfig,
    ModelRun,
    ModelSpec,
    TripManifest,
    UserAnnotations,
    utc_now_iso,
)
from time_machine.errors import (
    InputUnsupportedError,
    RunnerError,
    TimeMachineError,
)
from time_machine.evaluation import EvaluationPort, NullEvaluator
from time_machine.network_guard import block_network
from time_machine.prompt_adapters import prepare_input
from time_machine.runners.factory import RunnerFactory
from time_machine.trip_utils import blind_mapping_for_trip, hash_prompt

StatusCallback = Callable[[str, str, str], None]


class TripController:
    def __init__(
        self,
        cohort: Cohort,
        store: ArtifactStore,
        factory: RunnerFactory | None = None,
        paths: AppPaths | None = None,
        evaluator: EvaluationPort | None = None,
        app_version: str = __version__,
        runner_kind: str = "composite",
    ) -> None:
        self.cohort = cohort
        self.store = store
        self.factory = factory or RunnerFactory(
            model_cache=str(paths.model_cache_dir) if paths else None
        )
        self.paths = paths
        self.evaluator = evaluator or NullEvaluator()
        self.app_version = app_version
        self.runner_kind = runner_kind
        self._cancel = False

    def request_cancel(self) -> None:
        self._cancel = True

    def validate_prompt(self, raw_prompt: str, max_chars: int | None = None) -> None:
        limit = max_chars or self.cohort.prompt.max_chars
        if not raw_prompt or not raw_prompt.strip():
            raise InputUnsupportedError("prompt must not be empty or whitespace-only")
        if len(raw_prompt) > limit:
            raise InputUnsupportedError(f"prompt length {len(raw_prompt)} exceeds limit {limit}")

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
        block_network_during_trip: bool = True,
    ) -> TripManifest:
        self.validate_prompt(raw_prompt)
        models = models if models is not None else list(self.cohort.models)
        trip_id = trip_id or str(uuid4())
        config = self.cohort.generation_profiles[self.cohort.generation_profile_id]

        manifest = TripManifest(
            trip_id=trip_id,
            created_at=utc_now_iso(),
            protocol_version=PROTOCOL_VERSION,
            cohort_id=self.cohort.cohort_id,
            app_version=self.app_version,
            hardware_summary=hardware_summary or {},
            raw_prompt_sha256=hash_prompt(raw_prompt),
            optional_success_criterion=success_criterion or "",
            runs=[],
            user_annotations=UserAnnotations().model_dump(mode="json"),
        )
        writer = self.store.start_trip(manifest)
        writer.begin(raw_prompt, success_criterion)

        def notify(model_id: str, status: str, detail: str = "") -> None:
            if on_status:
                on_status(model_id, status, detail)

        def cancelled() -> bool:
            return self._cancel or bool(cancel_check and cancel_check())

        completed = 0
        cancelled_flag = False

        with block_network(enabled=block_network_during_trip):
            for spec in models:
                if cancelled():
                    cancelled_flag = True
                    run = ModelRun(
                        model_id=spec.id,
                        display_name=spec.display_name,
                        display_year=spec.display_year,
                        status="cancelled",
                        finished_at=utc_now_iso(),
                        error_code="cancelled",
                        error_message="trip cancelled before this model ran",
                        mode=spec.mode,
                        limitations=list(spec.limitations),
                        adapter_id=spec.adapter_id,
                        adapter_version=spec.adapter_version,
                        source_repository=spec.source.repository,
                        source_revision=spec.source.revision,
                        source_sha256=spec.source.sha256,
                    )
                    writer.record_run(run)
                    notify(spec.id, "failed", "cancelled")
                    continue

                started = utc_now_iso()
                notify(spec.id, "loading", "loading checkpoint")
                t0 = time.perf_counter()
                try:
                    verify = self.factory.verify_artifact(spec)
                    if not verify.available and self.runner_kind != "fake":
                        raise RunnerError(f"artifact check failed: {verify.reason}")

                    prepared = prepare_input(raw_prompt, spec)
                    notify(spec.id, "generating", "generating output")
                    runner = self.factory.create(self.runner_kind)
                    t_gen = time.perf_counter()
                    try:
                        result = runner.generate(prepared, spec, config)
                    finally:
                        runner.unload()
                    gen_seconds = time.perf_counter() - t_gen
                    load_seconds = max(t_gen - t0, 0.0)
                    total = time.perf_counter() - t0

                    run = ModelRun(
                        model_id=spec.id,
                        display_name=spec.display_name,
                        display_year=spec.display_year,
                        status="completed",
                        started_at=started,
                        finished_at=utc_now_iso(),
                        load_seconds=round(load_seconds, 4),
                        generation_seconds=round(gen_seconds, 4),
                        prepared_input_path=f"prepared-inputs/{spec.id}.txt",
                        output_path=f"outputs/{spec.id}.txt",
                        runtime=result.runtime,
                        adapter_id=spec.adapter_id,
                        adapter_version=spec.adapter_version,
                        source_repository=spec.source.repository,
                        source_revision=spec.source.revision,
                        source_sha256=spec.source.sha256,
                        mode=spec.mode,
                        limitations=list(spec.limitations),
                        prepared_text=prepared.prepared_text,
                    )
                    writer.record_run(run, prepared.prepared_text, result.output_text)
                    completed += 1
                    notify(spec.id, "complete", "output ready")
                    _ = total
                except InputUnsupportedError as exc:
                    run = ModelRun(
                        model_id=spec.id,
                        display_name=spec.display_name,
                        display_year=spec.display_year,
                        status="unsupported",
                        started_at=started,
                        finished_at=utc_now_iso(),
                        error_code="input_unsupported",
                        error_message=str(exc),
                        mode=spec.mode,
                        limitations=list(spec.limitations),
                        adapter_id=spec.adapter_id,
                        adapter_version=spec.adapter_version,
                        source_repository=spec.source.repository,
                        source_revision=spec.source.revision,
                        source_sha256=spec.source.sha256,
                    )
                    writer.record_run(run)
                    notify(spec.id, "failed", "input unsupported")
                except RunnerError as exc:
                    status = "timed_out" if exc.code == "generation_timeout" else "failed"
                    run = ModelRun(
                        model_id=spec.id,
                        display_name=spec.display_name,
                        display_year=spec.display_year,
                        status=status,
                        started_at=started,
                        finished_at=utc_now_iso(),
                        error_code=exc.code,
                        error_message=str(exc),
                        mode=spec.mode,
                        limitations=list(spec.limitations),
                        adapter_id=spec.adapter_id,
                        adapter_version=spec.adapter_version,
                        source_repository=spec.source.repository,
                        source_revision=spec.source.revision,
                        source_sha256=spec.source.sha256,
                    )
                    writer.record_run(run)
                    notify(spec.id, "failed", exc.code)
                except TimeMachineError as exc:
                    run = ModelRun(
                        model_id=spec.id,
                        display_name=spec.display_name,
                        display_year=spec.display_year,
                        status="failed",
                        started_at=started,
                        finished_at=utc_now_iso(),
                        error_code=getattr(exc, "code", "error"),
                        error_message=str(exc),
                        mode=spec.mode,
                        limitations=list(spec.limitations),
                    )
                    writer.record_run(run)
                    notify(spec.id, "failed", "error")

        complete = (not cancelled_flag) and completed == len(models)
        final = writer.finalize(cancelled=cancelled_flag, complete=complete)
        # EvaluationPort seam (NullEvaluator in local-v1).
        _ = self.evaluator.evaluate_trip(final)
        return final

    def save_annotations(self, trip_id: str, annotations: UserAnnotations) -> None:
        self.store.write_annotations(trip_id, annotations)
        manifest = self.store.read_manifest(trip_id)
        manifest.user_annotations = annotations.model_dump(mode="json")
        self.store.update_manifest(trip_id, manifest)


def make_controller(
    paths: AppPaths,
    cohort: Cohort | None = None,
    runner_kind: str = "composite",
) -> TripController:
    catalog = CohortCatalog(paths.root)
    cohort = cohort or catalog.default_cohort()
    return TripController(
        cohort=cohort,
        store=ArtifactStore(paths),
        factory=RunnerFactory(model_cache=str(paths.model_cache_dir)),
        paths=paths,
        evaluator=NullEvaluator(),
        runner_kind=runner_kind,
    )


__all__ = [
    "TripController",
    "make_controller",
    "blind_mapping_for_trip",
    "hash_prompt",
]
