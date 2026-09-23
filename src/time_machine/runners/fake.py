"""Deterministic fake runner for UI/storage development and tests."""

from __future__ import annotations

import time
from typing import Iterable

from time_machine.domain import (
    GenerationConfig,
    GenerationResult,
    ModelSpec,
    PreparedInput,
    RuntimeInfo,
    RunnerAvailability,
)
from time_machine.errors import (
    GenerationError,
    GenerationTimeoutError,
    LoadError,
    RunnerError,
)
from time_machine.prompt_adapters import prepare_input
from time_machine.runners.base import ModelRunner

FIXTURE_OUTPUTS = {
    "gpt2-xl-2019": (
        "Task: (echo) {prompt}\n\nAnswer:\n"
        "the lamp stays dark and ships keep writing their names across the fog\n"
        "Lighthouse poems often fail here, so we continue with wooden stairs\n"
        "and a keeper who never learned the word for light."
    ),
    "gpt-j-6b-2021": (
        "(echo-2021) {prompt}\n\n"
        "Answer: A slightly longer, more fluent base continuation that still "
        "wanders rather than obeying the constraint cleanly."
    ),
    "flan-t5-xl-2022": (
        "(echo-instruction-2022)\nPrompt received: {prompt}\n\n"
        "Response: An instruction-tuned model that addresses the task more "
        "directly than the base checkpoints."
    ),
    "mistral-7b-instruct-2023": (
        "(echo-chat-2023)\nI'll help with that request.\n\n{prompt}\n\n"
        "Here is a clear, structured answer that follows the visible instruction."
    ),
    "qwen25-7b-instruct-2024": (
        "(echo-chat-2024)\nCertainly. Regarding your prompt:\n\n{prompt}\n\n"
        "A modern instruction-following reply that satisfies the stated constraints "
        "with cleaner structure and fewer digressions."
    ),
}

DEFAULT_FIXTURE = (
    "(echo-{year}-{mode}) prepared length={plen}\n"
    "Deterministic fake output for {model_id}.\n"
    "Prompt echo: {prompt}\n"
    "This response stands in for a real checkpoint during offline development."
)


class FakeRunner(ModelRunner):
    """Deterministic fixture responses and controlled errors.

    Behaviors (via ``behaviors`` mapping model_id -> behavior name):
    - success (default)
    - load_failure
    - generation_timeout
    - generation_error
    - malformed
    - slow (optional delay_seconds)
    """

    def __init__(
        self,
        behaviors: dict[str, str] | None = None,
        delay_seconds: float = 0.0,
        outputs: dict[str, str] | None = None,
        fail_after: int | None = None,
    ) -> None:
        self.behaviors = behaviors or {}
        self.delay_seconds = delay_seconds
        self.outputs = outputs or {}
        self.fail_after = fail_after
        self._loaded: str | None = None
        self._calls: list[str] = []
        self._generate_count = 0

    @property
    def calls(self) -> list[str]:
        return list(self._calls)

    def preflight(self, spec: ModelSpec) -> RunnerAvailability:
        self._calls.append(f"preflight:{spec.id}")
        return RunnerAvailability(
            available=True,
            reason="fake runner ready",
            hardware_profile="standard",
            details={"fake": True},
        )

    def prepare(self, raw_prompt: str, spec: ModelSpec) -> PreparedInput:
        self._calls.append(f"prepare:{spec.id}")
        return prepare_input(raw_prompt, spec)

    def generate(
        self,
        prepared: PreparedInput,
        spec: ModelSpec,
        config: GenerationConfig,
    ) -> GenerationResult:
        self._calls.append(f"generate:{spec.id}")
        self._generate_count += 1
        behavior = self.behaviors.get(spec.id, "success")

        if self.fail_after is not None and self._generate_count > self.fail_after:
            behavior = "load_failure"

        if behavior == "load_failure":
            raise LoadError(f"fake load failure for {spec.id}")

        started = time.perf_counter()
        if self.delay_seconds:
            time.sleep(min(self.delay_seconds, 0.05))

        if behavior == "generation_timeout":
            raise GenerationTimeoutError(f"fake generation timeout for {spec.id}")
        if behavior == "generation_error":
            raise GenerationError(f"fake generation error for {spec.id}")
        if behavior == "malformed":
            text = ""
        else:
            template = self.outputs.get(spec.id) or FIXTURE_OUTPUTS.get(spec.id) or DEFAULT_FIXTURE
            text = template.format(
                prompt=prepared.raw_prompt,
                prepared=prepared.prepared_text,
                model_id=spec.id,
                year=spec.display_year,
                mode=spec.mode,
                plen=len(prepared.prepared_text),
            )

        elapsed = max(time.perf_counter() - started, 1e-4)
        self._loaded = spec.id
        return GenerationResult(
            output_text=text,
            runtime=RuntimeInfo(
                backend="fake",
                backend_version="1",
                device="cpu",
                effective_generation={
                    "seed": config.seed,
                    "temperature": config.temperature,
                    "top_p": config.top_p,
                    "max_new_tokens": config.max_new_tokens,
                    "retries": 0,
                },
            ),
            finish_reason="stop" if behavior != "malformed" else "malformed",
        )

    def unload(self) -> None:
        self._calls.append("unload")
        self._loaded = None


class ScriptedFailureRunner(FakeRunner):
    """Raise after N successful generations (used for cancellation/partial tests)."""

    def __init__(self, succeed_count: int, **kwargs) -> None:
        super().__init__(fail_after=succeed_count, **kwargs)
