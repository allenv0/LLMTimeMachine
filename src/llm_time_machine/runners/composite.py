"""Dispatch each ModelSpec to the runner matching its backend."""

from __future__ import annotations

from llm_time_machine.domain import (
    GenerationConfig,
    GenerationResult,
    ModelSpec,
    PreparedInput,
    RunnerAvailability,
)
from llm_time_machine.runners.base import ModelRunner
from llm_time_machine.runners.local_quantized_runner import LocalQuantizedRunner
from llm_time_machine.runners.transformers_runner import TransformersRunner


class CompositeRunner(ModelRunner):
    """Transformers for legacy/instruction; llama.cpp for quantized chat slots."""

    def __init__(self, model_cache: str | None = None) -> None:
        self.model_cache = model_cache
        self._tf = TransformersRunner(model_cache=model_cache)
        self._lq = LocalQuantizedRunner(model_cache=model_cache)

    def _pick(self, spec: ModelSpec) -> ModelRunner:
        if spec.backend == "local_quantized":
            return self._lq
        return self._tf

    def preflight(self, spec: ModelSpec) -> RunnerAvailability:
        return self._pick(spec).preflight(spec)

    def prepare(self, raw_prompt: str, spec: ModelSpec) -> PreparedInput:
        return self._pick(spec).prepare(raw_prompt, spec)

    def generate(
        self,
        prepared: PreparedInput,
        spec: ModelSpec,
        config: GenerationConfig,
    ) -> GenerationResult:
        return self._pick(spec).generate(prepared, spec, config)

    def unload(self) -> None:
        self._tf.unload()
        self._lq.unload()
