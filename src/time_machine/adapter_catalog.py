"""Adapter catalog loaded from registry/adapters/catalog.yaml.

Templates are data, not hard-coded Python strings, so new cohorts can add
versioned visible adapters without code changes.
"""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path

import yaml
from pydantic import BaseModel, Field

from time_machine.errors import RegistryError


class AdapterSpec(BaseModel):
    id: str
    version: str
    mode: str  # base_continuation | instruction | chat | any
    template: str
    purpose: str
    notes: list[str] = Field(default_factory=list)


class AdapterCatalog:
    def __init__(self, adapters: dict[str, AdapterSpec]) -> None:
        self._adapters = adapters

    @classmethod
    def load(cls, path: Path) -> "AdapterCatalog":
        if not path.is_file():
            raise RegistryError(f"adapter catalog not found: {path}")
        data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
        items = data.get("adapters") or []
        adapters: dict[str, AdapterSpec] = {}
        for raw in items:
            spec = AdapterSpec.model_validate(raw)
            if spec.id in adapters:
                raise RegistryError(f"duplicate adapter id: {spec.id}")
            adapters[spec.id] = spec
        if not adapters:
            raise RegistryError("adapter catalog is empty")
        return cls(adapters)

    def get(self, adapter_id: str) -> AdapterSpec:
        try:
            return self._adapters[adapter_id]
        except KeyError as exc:
            raise RegistryError(f"unknown adapter_id: {adapter_id!r}") from exc

    def ids(self) -> list[str]:
        return sorted(self._adapters)

    def compatible(self, adapter_id: str, mode: str) -> bool:
        spec = self.get(adapter_id)
        return spec.mode in {mode, "any"}

    def render(self, adapter_id: str, raw_prompt: str) -> str:
        spec = self.get(adapter_id)
        return spec.template.format(prompt=raw_prompt)

    def explanation(self, adapter_id: str) -> str:
        spec = self.get(adapter_id)
        lines = [spec.purpose, *spec.notes]
        return "\n".join(lines)

    def mode_compatibility_map(self) -> dict[str, set[str]]:
        out: dict[str, set[str]] = {}
        for spec in self._adapters.values():
            out.setdefault(spec.id, set()).add(spec.mode)
        return out


@lru_cache(maxsize=4)
def load_adapter_catalog(path_str: str) -> AdapterCatalog:
    return AdapterCatalog.load(Path(path_str))


def default_adapter_catalog(adapters_dir: Path) -> AdapterCatalog:
    return load_adapter_catalog(str(adapters_dir / "catalog.yaml"))
