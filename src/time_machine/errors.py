"""Typed errors."""

from __future__ import annotations


class TimeMachineError(Exception):
    code = "error"


class RegistryError(TimeMachineError):
    code = "registry_invalid"


class InputUnsupportedError(TimeMachineError):
    code = "input_unsupported"


class ArtifactError(TimeMachineError):
    code = "artifact_error"


class RunnerError(TimeMachineError):
    code = "runner_error"


class LoadError(RunnerError):
    code = "load_failed"


class GenerationTimeoutError(RunnerError):
    code = "generation_timeout"


class GenerationError(RunnerError):
    code = "generation_failed"


class CancelledError(TimeMachineError):
    code = "cancelled"


class PreflightError(TimeMachineError):
    code = "preflight_failed"
