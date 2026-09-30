"""Shared test fixtures."""

from __future__ import annotations

from pathlib import Path

import pytest
import yaml

from llm_time_machine.artifact_store import ArtifactStore
from llm_time_machine.config import AppPaths
from llm_time_machine.domain import Cohort, GenerationConfig, ModelSpec
from llm_time_machine.registry import validate_cohort_dict
from llm_time_machine.runners.fake import FakeRunner
from llm_time_machine.trip_service import TripService

REPO_ROOT = Path(__file__).resolve().parents[1]


@pytest.fixture
def paths(tmp_path: Path) -> AppPaths:
    return AppPaths(root=REPO_ROOT, local_data=tmp_path / "local-data", model_cache=tmp_path / "model-cache")


@pytest.fixture
def store(paths: AppPaths) -> ArtifactStore:
    return ArtifactStore(paths)


def make_model(
    mid: str = "m1",
    year: int = 2019,
    name: str | None = None,
    mode: str = "base_continuation",
    adapter_id: str = "identity-v1",
    backend: str = "fake",
    input_limit_chars: int = 900,
) -> ModelSpec:
    return ModelSpec(
        id=mid,
        display_year=year,
        display_name=name or mid.upper(),
        release_date="2019-01-01",
        mode=mode,
        source={
            "repository": f"org/{mid}",
            "revision": "abc123def4567890abc123def4567890abc123de",
            "artifact_filename": "model.safetensors",
            "sha256": "a" * 64,
        },
        license_url="https://example.com/license",
        backend=backend,
        precision="fp32",
        adapter_id=adapter_id,
        adapter_version="1",
        input_limit_chars=input_limit_chars,
        generation_profile_id="local-v1",
        limitations=["fixture limitation"],
        hardware_profile="standard",
    )


def make_cohort(models: list[ModelSpec] | None = None) -> Cohort:
    models = models or [
        make_model("gpt2-xl-2019", 2019, "GPT-2 XL", "base_continuation", "identity-v1"),
        make_model("gpt-j-6b-2021", 2021, "GPT-J 6B", "base_continuation", "identity-v1"),
        make_model("flan-t5-xl-2022", 2022, "FLAN-T5 XL", "instruction", "identity-v1"),
        make_model("mistral-7b-instruct-2023", 2023, "Mistral 7B", "chat", "fake-chat-v1"),
        make_model("qwen25-7b-instruct-2024", 2024, "Qwen2.5 7B", "chat", "fake-chat-v1"),
    ]
    return Cohort(
        schema_version="1",
        cohort_id="local-v1",
        protocol_version="local-v1",
        prompt={"max_chars": 900, "language_note": "en"},
        generation_profile_id="local-v1",
        generation_profiles={
            "local-v1": GenerationConfig(
                profile_id="local-v1",
                seed=20260923,
                temperature=0.7,
                top_p=0.95,
                max_new_tokens=320,
                retries=0,
                tools_enabled=False,
                network_enabled=False,
            )
        },
        models=models,
    )


@pytest.fixture
def cohort() -> Cohort:
    return make_cohort()


@pytest.fixture
def service(cohort: Cohort, store: ArtifactStore, paths: AppPaths) -> TripService:
    return TripService(cohort, store, FakeRunner(), paths=paths)


@pytest.fixture
def real_registry_path() -> Path:
    return REPO_ROOT / "registry" / "cohort-local-v1.yaml"
