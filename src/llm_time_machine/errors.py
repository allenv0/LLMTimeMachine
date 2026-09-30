"""Typed errors."""

from __future__ import annotations


class LLMTimeMachineError(Exception):
    code = "error"


class RegistryError(LLMTimeMachineError):
    code = "registry_invalid"


class InputUnsupportedError(LLMTimeMachineError):
    code = "input_unsupported"


class ArtifactError(LLMTimeMachineError):
    code = "artifact_error"


class RunnerError(LLMTimeMachineError):
    code = "runner_error"


class LoadError(RunnerError):
    code = "load_failed"


class GenerationTimeoutError(RunnerError):
    code = "generation_timeout"


class GenerationError(RunnerError):
    code = "generation_failed"


class CancelledError(LLMTimeMachineError):
    code = "cancelled"


class PreflightError(LLMTimeMachineError):
    code = "preflight_failed"


# Backwards-compatibility alias for code written against the Old Weights name.
TimeMachineError = LLMTimeMachineError
