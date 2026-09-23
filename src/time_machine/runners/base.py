"""Runner protocol — UI must not depend on a concrete inference backend."""

from __future__ import annotations

from typing import Protocol, runtime_checkable

from time_machine.domain import GenerationConfig, GenerationResult, ModelSpec, PreparedInput, RunnerAvailability


@runtime_checkable
class RunnerProtocol(Protocol):
    def preflight(self, spec: ModelSpec) -> RunnerAvailability: ...

    def prepare(self, raw_prompt: str, spec: ModelSpec) -> PreparedInput: ...

    def generate(
        self,
        prepared: PreparedInput,
        spec: ModelSpec,
        config: GenerationConfig,
    ) -> GenerationResult: ...

    def unload(self) -> None: ...


class ModelRunner:
    """Optional base class with shared prepare via prompt_adapters."""

    def prepare(self, raw_prompt: str, spec: ModelSpec) -> PreparedInput:
        from time_machine.prompt_adapters import prepare_input

        return prepare_input(raw_prompt, spec)

    def unload(self) -> None:
        return None
