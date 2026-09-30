"""Application configuration and paths."""

from __future__ import annotations

import os
from pathlib import Path
from typing import Literal

from pydantic import BaseModel, Field, field_validator

APP_NAME = "LLMTimeMachine"
APP_TAGLINE = "Your prompt, answered by a decade of AI."
TRUTHFUL_CLAIM = (
    "A laptop-compatible, auditable sample of LLM history. "
    "It is not a verified record of the best model in every year."
)
PROTOCOL_VERSION = "local-v1"
SCHEMA_VERSION = "1"
DEBUG_CONTENT_ENV = "LLM_TIME_MACHINE_DEBUG_CONTENT"
# Legacy names from before the Old Weights → LLMTimeMachine rename.
LEGACY_DEBUG_CONTENT_ENV = "TIME_MACHINE_DEBUG_CONTENT"

# Fixed disclosure strings required by the plan.
DISCLOSURE_LINES = (
    "Runs locally: your prompt is not sent to a model API.",
    "This is a laptop-compatible historical cohort, not verified annual frontier models.",
    "Older models use visible historical input formats because they predate chat interfaces.",
)

FAILURE_TAG_VALUES = (
    "incorrect",
    "ignored_constraints",
    "irrelevant",
    "unsafe",
    "incomplete",
    "style",
    "other",
)

UsefulnessLiteral = Literal["yes", "partly", "no", "unset"]
RunStatusLiteral = Literal["completed", "failed", "timed_out", "unsupported", "cancelled"]
ModelModeLiteral = Literal["base_continuation", "instruction", "chat"]
BackendLiteral = Literal["transformers", "local_quantized", "fake"]
HardwareProfileLiteral = Literal["lite", "standard", "high", "unknown"]


class AppPaths(BaseModel):
    """Filesystem layout for registry, prompts, and local data."""

    root: Path = Field(default_factory=lambda: Path.cwd())
    local_data: Path | None = None
    model_cache: Path | None = None
    cohort_file: Path | None = None

    model_config = {"arbitrary_types_allowed": True}

    @field_validator("root", mode="before")
    @classmethod
    def _abs(cls, value: object) -> Path:
        return Path(value).resolve()

    @property
    def registry_path(self) -> Path:
        if self.cohort_file is not None:
            return Path(self.cohort_file).resolve()
        return self.root / "registry" / "cohort-local-v1.yaml"

    @property
    def adapters_dir(self) -> Path:
        return self.root / "registry" / "adapters"

    @property
    def starter_prompts_path(self) -> Path:
        return self.root / "prompts" / "starter_prompts.jsonl"

    @property
    def protocol_path(self) -> Path:
        return self.root / "PROTOCOL.md"

    @property
    def trips_dir(self) -> Path:
        base = self.local_data or (self.root / "local-data")
        return (base / "trips").resolve()

    @property
    def local_data_dir(self) -> Path:
        base = self.local_data or (self.root / "local-data")
        return Path(base).resolve()

    @property
    def cache_index_path(self) -> Path:
        base = self.model_cache or (self.root / "local-data" / "model-cache")
        return Path(base).resolve() / "local-cache-index.json"

    @property
    def model_cache_dir(self) -> Path:
        base = self.model_cache or (self.root / "local-data" / "model-cache")
        return Path(base).resolve()

    @property
    def diary_dir(self) -> Path:
        return (self.local_data_dir / "diary").resolve()

    @property
    def diary_prompts_dir(self) -> Path:
        return (self.diary_dir / "prompts").resolve()

    @property
    def diary_index_path(self) -> Path:
        return self.diary_dir / "index.json"

    @property
    def curves_dir(self) -> Path:
        return (self.local_data_dir / "curves").resolve()

    @property
    def judge_dir(self) -> Path:
        return (self.local_data_dir / "judge").resolve()

    @property
    def judges_registry_dir(self) -> Path:
        return self.root / "registry" / "judges"

    @property
    def chats_dir(self) -> Path:
        return (self.local_data_dir / "chats").resolve()

    @property
    def curve_packs_dir(self) -> Path:
        return (self.local_data_dir / "curve-packs").resolve()

    @property
    def curve_packs_registry_dir(self) -> Path:
        return self.root / "registry" / "curve-packs"

    @property
    def judge_cache_dir(self) -> Path:
        return (self.local_data_dir / "judge-cache").resolve()

    @property
    def judge_calibration_dir(self) -> Path:
        return (self.local_data_dir / "judge-calibration").resolve()


def _env(new_key: str, legacy_key: str, default: str = "") -> str:
    """Prefer the LLM_TIME_MACHINE_* name, fall back to legacy TIME_MACHINE_*."""
    value = os.environ.get(new_key, "")
    if value == "":
        value = os.environ.get(legacy_key, "")
    return value if value != "" else default


def default_paths(root: Path | None = None) -> AppPaths:
    root_value = _env("LLM_TIME_MACHINE_ROOT", "TIME_MACHINE_ROOT", "")
    root_path = root or (Path(root_value) if root_value else Path.cwd())
    local = _env("LLM_TIME_MACHINE_LOCAL_DATA", "TIME_MACHINE_LOCAL_DATA")
    cache = _env("LLM_TIME_MACHINE_MODEL_CACHE", "TIME_MACHINE_MODEL_CACHE")
    cohort = _env("LLM_TIME_MACHINE_COHORT", "TIME_MACHINE_COHORT")
    return AppPaths(
        root=root_path,
        local_data=Path(local) if local else None,
        model_cache=Path(cache) if cache else None,
        cohort_file=Path(cohort) if cohort else None,
    )


def debug_content_enabled() -> bool:
    """Content logging is off unless explicitly enabled in the environment."""
    raw = os.environ.get(DEBUG_CONTENT_ENV, "").strip().lower()
    if raw == "":
        raw = os.environ.get(LEGACY_DEBUG_CONTENT_ENV, "").strip().lower()
    return raw in {"1", "true", "yes", "on"}
