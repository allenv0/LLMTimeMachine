"""Registry validation tests."""

from __future__ import annotations

import copy

import pytest
import yaml

from llm_time_machine.errors import RegistryError
from llm_time_machine.registry import load_cohort, validate_cohort_dict
from tests.conftest import make_cohort, make_model


def test_real_cohort_file_loads(real_registry_path):
    cohort = load_cohort(real_registry_path)
    assert cohort.cohort_id == "local-v1"
    assert len(cohort.models) == 5
    years = [m.display_year for m in cohort.models]
    assert years == sorted(years)
    assert years == [2019, 2021, 2022, 2023, 2024]


def test_missing_revision_rejected():
    cohort = make_cohort()
    data = cohort.model_dump(mode="json")
    data["models"][0]["source"]["revision"] = "main"
    with pytest.raises(RegistryError):
        validate_cohort_dict(data)


def test_empty_revision_rejected():
    cohort = make_cohort()
    data = cohort.model_dump(mode="json")
    data["models"][0]["source"]["revision"] = ""
    with pytest.raises(RegistryError):
        validate_cohort_dict(data)


def test_duplicate_years_rejected():
    cohort = make_cohort([make_model("a", 2019, "A"), make_model("b", 2019, "B")])
    data = cohort.model_dump(mode="json")
    with pytest.raises(RegistryError):
        validate_cohort_dict(data)


def test_descending_years_rejected():
    cohort = make_cohort([make_model("a", 2021, "A"), make_model("b", 2019, "B")])
    data = cohort.model_dump(mode="json")
    with pytest.raises(RegistryError):
        validate_cohort_dict(data)


def test_invalid_adapter_mode_rejected():
    cohort = make_cohort([make_model("a", 2019, "A", mode="chat", adapter_id="continuation-v1")])
    data = cohort.model_dump(mode="json")
    with pytest.raises(RegistryError):
        validate_cohort_dict(data)


def test_missing_license_rejected():
    cohort = make_cohort()
    data = cohort.model_dump(mode="json")
    data["models"][0]["license_url"] = ""
    with pytest.raises(RegistryError):
        validate_cohort_dict(data)


def test_missing_checksum_rejected():
    cohort = make_cohort()
    data = cohort.model_dump(mode="json")
    data["models"][0]["source"]["sha256"] = ""
    with pytest.raises(RegistryError):
        validate_cohort_dict(data)


def test_missing_limitations_rejected():
    cohort = make_cohort()
    data = cohort.model_dump(mode="json")
    data["models"][0]["limitations"] = []
    with pytest.raises(RegistryError):
        validate_cohort_dict(data)


def test_input_limit_above_protocol_rejected():
    cohort = make_cohort()
    data = cohort.model_dump(mode="json")
    data["models"][0]["input_limit_chars"] = 2000
    with pytest.raises(RegistryError):
        validate_cohort_dict(data)


def test_retries_nonzero_rejected():
    data = make_cohort().model_dump(mode="json")
    data["generation_profiles"]["local-v1"]["retries"] = 1
    with pytest.raises(RegistryError):
        validate_cohort_dict(data)


def test_tools_enabled_rejected():
    data = make_cohort().model_dump(mode="json")
    data["generation_profiles"]["local-v1"]["tools_enabled"] = True
    with pytest.raises(RegistryError):
        validate_cohort_dict(data)


def test_duplicate_model_ids_rejected():
    cohort = make_cohort([make_model("a", 2019, "A"), make_model("a", 2021, "B")])
    data = cohort.model_dump(mode="json")
    with pytest.raises(RegistryError):
        validate_cohort_dict(data)


def test_record_at_preload_checksum_allowed():
    cohort = make_cohort()
    data = cohort.model_dump(mode="json")
    data["models"][0]["source"]["sha256"] = "record-at-preload"
    cohort2 = validate_cohort_dict(data)
    assert cohort2.models[0].source.sha256 == "record-at-preload"


def test_valid_fixture_cohort():
    validate_cohort_dict(make_cohort().model_dump(mode="json"))
