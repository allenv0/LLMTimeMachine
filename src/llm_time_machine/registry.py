"""Load and validate the pinned cohort registry."""

from __future__ import annotations

from pathlib import Path

import yaml
from pydantic import ValidationError

from llm_time_machine.config import PROTOCOL_VERSION, SCHEMA_VERSION
from llm_time_machine.domain import Cohort, GenerationConfig, ModelSpec
from llm_time_machine.errors import RegistryError
from llm_time_machine.adapter_catalog import AdapterCatalog

ADAPTER_MODE_COMPAT = {
    "continuation-v1": {"base_continuation"},
    "instruction-v1": {"instruction"},
    "chat-mistral-v1": {"chat"},
    "chat-qwen-v1": {"chat"},
    # test fixture adapters may use these
    "identity-v1": {"base_continuation", "instruction", "chat"},
    "fake-chat-v1": {"chat"},
}


def _load_yaml(path: Path) -> dict:
    if not path.is_file():
        raise RegistryError(f"cohort file not found: {path}")
    try:
        data = yaml.safe_load(path.read_text(encoding="utf-8"))
    except yaml.YAMLError as exc:
        raise RegistryError(f"invalid YAML in {path}: {exc}") from exc
    if not isinstance(data, dict):
        raise RegistryError(f"cohort file must be a mapping: {path}")
    return data


def validate_cohort_dict(
    data: dict,
    *,
    known_adapters: set[str] | None = None,
    adapter_catalog=None,
) -> Cohort:
    """Validate a cohort mapping and return a typed Cohort."""
    try:
        cohort = Cohort.model_validate(data)
    except ValidationError as exc:
        raise RegistryError(f"cohort validation failed:\n{exc}") from exc

    _validate_semantics(
        cohort, known_adapters=known_adapters, adapter_catalog=adapter_catalog
    )
    return cohort


def _validate_semantics(
    cohort: Cohort,
    *,
    known_adapters: set[str] | None = None,
    adapter_catalog: AdapterCatalog | None = None,
) -> None:
    if cohort.cohort_id != "local-v1" and not cohort.cohort_id:
        raise RegistryError("cohort_id is required")

    years = [m.display_year for m in cohort.models]
    if years != sorted(years):
        raise RegistryError(f"display_year values must be strictly ascending: {years}")
    if len(set(years)) != len(years):
        raise RegistryError(f"display_year values must be unique: {years}")

    ids = [m.id for m in cohort.models]
    if len(set(ids)) != len(ids):
        raise RegistryError(f"model ids must be unique: {ids}")

    names = [m.display_name for m in cohort.models]
    if len(set(names)) != len(names):
        raise RegistryError(f"display_name values must be unique: {names}")

    if len(years) >= 2:
        for a, b in zip(years, years[1:], strict=False):
            if a >= b:
                raise RegistryError("display_year values must be strictly ascending")

    max_prompt = cohort.prompt.max_chars
    for model in cohort.models:
        if model.input_limit_chars <= 0 or model.input_limit_chars > max_prompt:
            raise RegistryError(
                f"{model.id}: input_limit_chars must be positive and <= protocol max {max_prompt}"
            )
        if model.generation_profile_id not in cohort.generation_profiles:
            raise RegistryError(
                f"{model.id}: unknown generation_profile_id {model.generation_profile_id!r}"
            )
        if adapter_catalog is not None:
            if model.adapter_id not in adapter_catalog.ids():
                raise RegistryError(f"{model.id}: unknown adapter_id {model.adapter_id!r}")
            if not adapter_catalog.compatible(model.adapter_id, model.mode):
                raise RegistryError(
                    f"{model.id}: adapter {model.adapter_id} incompatible with mode {model.mode}"
                )
        elif known_adapters is not None and model.adapter_id not in known_adapters:
            raise RegistryError(f"{model.id}: unknown adapter_id {model.adapter_id!r}")
        else:
            allowed_modes = ADAPTER_MODE_COMPAT.get(model.adapter_id)
            if allowed_modes is not None and model.mode not in allowed_modes:
                raise RegistryError(
                    f"{model.id}: adapter {model.adapter_id} incompatible with mode {model.mode}"
                )
        if not model.limitations:
            raise RegistryError(f"{model.id}: at least one limitation is required")
        if not model.license_url:
            raise RegistryError(f"{model.id}: license_url is required")
        if not model.source.repository or not model.source.revision:
            raise RegistryError(f"{model.id}: source repository/revision required")
        if model.slot_status == "substitute" and not model.stands_for:
            raise RegistryError(f"{model.id}: substitute slots must set stands_for")

    _validate_timeline(cohort)


def _validate_timeline(cohort: Cohort) -> None:
    """Decade spine: holes never collide with models; endpoints resolve."""
    model_years = {m.display_year for m in cohort.models}
    hole_years = [h.display_year for h in cohort.timeline_holes]
    if len(set(hole_years)) != len(hole_years):
        raise RegistryError(f"timeline_holes years must be unique: {hole_years}")
    for h in cohort.timeline_holes:
        if h.display_year in model_years:
            raise RegistryError(
                f"timeline hole {h.display_year} collides with a model display_year"
            )
        if not h.reason.strip():
            raise RegistryError(f"timeline hole {h.display_year}: reason required")
    # Combined spine years must be strictly ascending when interleaved by year.
    spine = sorted(
        [(m.display_year, "model", m.id) for m in cohort.models]
        + [(h.display_year, "hole", str(h.display_year)) for h in cohort.timeline_holes]
    )
    years_only = [y for y, _, _ in spine]
    if years_only != sorted(years_only):
        raise RegistryError("timeline spine years must sort")
    if len(set(years_only)) != len(years_only):
        raise RegistryError(f"duplicate years on timeline spine: {years_only}")

    if cohort.status_quo is not None:
        ids = {m.id for m in cohort.models}
        if cohort.status_quo.model_id not in ids:
            raise RegistryError(
                f"status_quo.model_id {cohort.status_quo.model_id!r} not in cohort models"
            )
    if cohort.future is not None and cohort.future.enabled:
        ids = {m.id for m in cohort.models}
        for mid in cohort.future.member_model_ids:
            if mid not in ids:
                raise RegistryError(f"future.member_model_id {mid!r} not in cohort models")
        if not cohort.future.selection_rule.strip():
            raise RegistryError("future.enabled requires a frozen selection_rule")
        if not cohort.future.member_model_ids:
            raise RegistryError("future.enabled requires member_model_ids")


def load_cohort(path: Path | str) -> Cohort:
    path = Path(path)
    data = _load_yaml(path)
    profiles = data.get("generation_profiles") or {}
    if isinstance(profiles, dict):
        for key, prof in profiles.items():
            if isinstance(prof, dict) and prof.get("id") not in (None, key):
                raise RegistryError(
                    f"generation_profiles[{key}].id must equal {key!r}, got {prof.get('id')!r}"
                )
    catalog = None
    adapters = path.parent / "adapters" / "catalog.yaml"
    if adapters.is_file():
        try:
            from llm_time_machine.adapter_catalog import AdapterCatalog

            catalog = AdapterCatalog.load(adapters)
        except RegistryError:
            catalog = None
    return validate_cohort_dict(data, adapter_catalog=catalog)


def load_generation_profile(cohort: Cohort, profile_id: str | None = None) -> GenerationConfig:
    pid = profile_id or cohort.generation_profile_id
    if pid not in cohort.generation_profiles:
        raise RegistryError(f"unknown generation profile: {pid}")
    return cohort.generation_profiles[pid]


def model_adapter_compatible(adapter_id: str, mode: str) -> bool:
    allowed = ADAPTER_MODE_COMPAT.get(adapter_id)
    if allowed is None:
        return True
    return mode in allowed


__all__ = [
    "ADAPTER_MODE_COMPAT",
    "load_cohort",
    "load_generation_profile",
    "model_adapter_compatible",
    "validate_cohort_dict",
    "SCHEMA_VERSION",
    "PROTOCOL_VERSION",
    "ModelSpec",
]
