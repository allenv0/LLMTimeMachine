"""Pydantic domain contracts for trips, runs, and annotations."""

from __future__ import annotations

from datetime import date, datetime, timezone
from typing import Any
from uuid import uuid4

from pydantic import BaseModel, Field, field_validator

from time_machine.config import (
    FAILURE_TAG_VALUES,
    SCHEMA_VERSION,
    BackendLiteral,
    HardwareProfileLiteral,
    ModelModeLiteral,
    RunStatusLiteral,
    UsefulnessLiteral,
)


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


class ModelSource(BaseModel):
    repository: str
    revision: str = Field(min_length=1)
    artifact_filename: str
    sha256: str = Field(min_length=1)

    @field_validator("revision")
    @classmethod
    def _reject_branch(cls, value: str) -> str:
        banned = {"main", "master", "latest", "head"}
        if value.strip().lower() in banned:
            raise ValueError(f"unpinned revision not allowed: {value!r}")
        return value

    @field_validator("sha256")
    @classmethod
    def _checksum(cls, value: str) -> str:
        v = value.strip().lower()
        if v == "record-at-preload":
            return "record-at-preload"
        if len(v) != 64 or any(c not in "0123456789abcdef" for c in v):
            raise ValueError("sha256 must be 64 hex chars or 'record-at-preload'")
        return v


class GenerationConfig(BaseModel):
    # YAML registry uses `id: local-v1`; JSON exports use `profile_id`.
    profile_id: str = Field(alias="id")
    seed: int
    temperature: float
    top_p: float
    max_new_tokens: int
    tools_enabled: bool = False
    network_enabled: bool = False
    retries: int = 0

    model_config = {"populate_by_name": True, "extra": "ignore"}

    @field_validator("retries")
    @classmethod
    def _no_retries(cls, value: int) -> int:
        if value != 0:
            raise ValueError("local-v1 forbids retries; must be 0")
        return value

    @field_validator("tools_enabled", "network_enabled")
    @classmethod
    def _disabled(cls, value: bool) -> bool:
        if value:
            raise ValueError("tools/network must be disabled in local-v1")
        return value


class ModelSpec(BaseModel):
    id: str = Field(min_length=1)
    display_year: int
    display_name: str = Field(min_length=1)
    release_date: date
    mode: ModelModeLiteral
    source: ModelSource
    license_url: str
    backend: BackendLiteral
    precision: str
    adapter_id: str
    adapter_version: str
    input_limit_chars: int = Field(gt=0)
    generation_profile_id: str
    limitations: list[str] = Field(min_length=1)
    hardware_profile: HardwareProfileLiteral


class CohortPromptLimits(BaseModel):
    max_chars: int = Field(gt=0)
    language_note: str = ""


class Cohort(BaseModel):
    schema_version: str = SCHEMA_VERSION
    cohort_id: str
    protocol_version: str
    prompt: CohortPromptLimits
    generation_profile_id: str
    generation_profiles: dict[str, GenerationConfig]
    models: list[ModelSpec]


class PreparedInput(BaseModel):
    model_id: str
    raw_prompt: str
    adapter_id: str
    adapter_version: str
    prepared_text: str
    was_truncated: bool = False
    preparation_notes: list[str] = Field(default_factory=list)

    @field_validator("was_truncated")
    @classmethod
    def _never_truncate(cls, value: bool) -> bool:
        if value:
            raise ValueError("local-v1 forbids truncation; was_truncated must be false")
        return value


class RunnerAvailability(BaseModel):
    available: bool
    reason: str = ""
    hardware_profile: HardwareProfileLiteral = "unknown"
    estimated_peak_memory_mb: int | None = None
    details: dict[str, Any] = Field(default_factory=dict)


class RuntimeInfo(BaseModel):
    backend: str
    backend_version: str
    device: str
    effective_generation: dict[str, Any] = Field(default_factory=dict)


class GenerationResult(BaseModel):
    output_text: str
    runtime: RuntimeInfo
    finish_reason: str = "stop"


class ModelRun(BaseModel):
    model_id: str
    display_name: str = ""
    display_year: int | None = None
    status: RunStatusLiteral
    started_at: str | None = None
    finished_at: str | None = None
    load_seconds: float = 0.0
    generation_seconds: float = 0.0
    prepared_input_path: str | None = None
    output_path: str | None = None
    error_code: str | None = None
    error_message: str | None = None
    runtime: RuntimeInfo | None = None
    adapter_id: str | None = None
    adapter_version: str | None = None
    source_repository: str | None = None
    source_revision: str | None = None
    source_sha256: str | None = None
    mode: ModelModeLiteral | None = None
    limitations: list[str] = Field(default_factory=list)
    prepared_text: str | None = None


class UserAnnotations(BaseModel):
    usefulness: dict[str, UsefulnessLiteral] = Field(default_factory=dict)
    # Explicit human quality ordinal relative to hope/criterion: -2..+2 per model_id.
    # Track A only. Not a scientific measurement. Blind rank is separate (preference).
    ordinal: dict[str, int] = Field(default_factory=dict)
    blind_rank: dict[str, int] = Field(default_factory=dict)
    blind_tie: list[str] = Field(default_factory=list)
    blind_unranked: list[str] = Field(default_factory=list)
    blind_mapping: dict[str, str] = Field(default_factory=dict)
    blind_mapping_revealed: bool = False
    notes: dict[str, str] = Field(default_factory=dict)
    failure_tags: dict[str, list[str]] = Field(default_factory=dict)
    trip_notes: str = ""

    @field_validator("failure_tags")
    @classmethod
    def _known_tags(cls, value: dict[str, list[str]]) -> dict[str, list[str]]:
        allowed = set(FAILURE_TAG_VALUES)
        for model_id, tags in value.items():
            unknown = [t for t in tags if t not in allowed]
            if unknown:
                raise ValueError(f"unknown failure_tags for {model_id}: {unknown}")
        return value

    @field_validator("ordinal")
    @classmethod
    def _ordinal_range(cls, value: dict[str, int]) -> dict[str, int]:
        for model_id, score in value.items():
            if score not in (-2, -1, 0, 1, 2):
                raise ValueError(f"ordinal for {model_id} must be -2..+2, got {score}")
        return value


class CurvePoint(BaseModel):
    """One human-rated point on a quality-over-time series. Gaps stay gaps."""

    model_id: str
    display_year: int
    ordinal: int  # -2..+2
    source: str = "explicit"  # explicit | derived_usefulness
    display_name: str = ""


class JudgeScore(BaseModel):
    """Estimated machine quality (local-v2-eval). Never silent; never ground truth."""

    model_id: str
    trip_id: str
    display_year: int | None = None
    status: str = "unscored"  # scored | unscored | failed
    score_1_10: int | None = None
    unscored_reason: str = ""
    rubric_id: str
    judge_model_id: str
    judge_revision: str = ""
    judge_prompt_sha256: str = ""
    judge_output_path: str = ""
    judge_input_path: str = ""
    sampled_at: str = Field(default_factory=utc_now_iso)
    protocol: str = "local-v2-eval"
    limitations: list[str] = Field(default_factory=list)

    @field_validator("score_1_10")
    @classmethod
    def _score_range(cls, value: int | None) -> int | None:
        if value is None:
            return value
        if value < 1 or value > 10:
            raise ValueError("score_1_10 must be 1..10")
        return value


class DiaryTripRef(BaseModel):
    trip_id: str
    created_at: str
    note: str = ""


class PromptDiaryEntry(BaseModel):
    """Pre-registered private prompt the user can revisit over time (idea.md G4)."""

    entry_id: str
    raw_prompt_sha256: str
    created_at: str
    tags: list[str] = Field(default_factory=list)
    success_criterion: str = ""
    trips: list[DiaryTripRef] = Field(default_factory=list)
    first_solved_model_id: str | None = None
    first_solved_trip_id: str | None = None
    first_solved_at: str | None = None
    solved_mark: str = "unset"  # unset | user | judge_v2
    reflections: dict[str, str] = Field(default_factory=dict)  # year -> local note
    preview: str = ""  # short local preview only; full text lives in raw-prompt.txt


class TripManifest(BaseModel):
    schema_version: str = SCHEMA_VERSION
    trip_id: str = Field(default_factory=lambda: str(uuid4()))
    created_at: str = Field(default_factory=utc_now_iso)
    protocol_version: str
    cohort_id: str
    app_version: str
    hardware_summary: dict[str, Any] = Field(default_factory=dict)
    raw_prompt_sha256: str
    optional_success_criterion: str = ""
    runs: list[ModelRun] = Field(default_factory=list)
    user_annotations: dict[str, Any] = Field(default_factory=dict)
    cancelled: bool = False
    complete: bool = False


class ModelRunStatus:
    """Progress view statuses used by the UI (maps to run lifecycle)."""

    WAITING = "waiting"
    LOADING = "loading"
    GENERATING = "generating"
    COMPLETE = "complete"
    FAILED = "failed"
