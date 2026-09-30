"""Discover and load cohort YAML files + adapter catalog."""

from __future__ import annotations

from pathlib import Path

from llm_time_machine.adapter_catalog import AdapterCatalog, default_adapter_catalog
from llm_time_machine.domain import Cohort
from llm_time_machine.errors import RegistryError
from llm_time_machine.registry import load_cohort
from llm_time_machine import prompt_adapters


class CohortCatalog:
    def __init__(self, root: Path) -> None:
        self.root = Path(root)
        self.registry_dir = self.root / "registry"
        self.adapters_dir = self.registry_dir / "adapters"
        self._adapter_catalog: AdapterCatalog | None = None

    @property
    def adapters(self) -> AdapterCatalog:
        if self._adapter_catalog is None:
            self._adapter_catalog = default_adapter_catalog(self.adapters_dir)
            prompt_adapters.bind_catalog(self._adapter_catalog)
        return self._adapter_catalog

    def list_cohort_files(self) -> list[Path]:
        if not self.registry_dir.is_dir():
            return []
        return sorted(self.registry_dir.glob("cohort-*.yaml"))

    def list_cohorts(self) -> list[dict]:
        out = []
        for path in self.list_cohort_files():
            try:
                cohort = self.load_file(path)
                out.append(
                    {
                        "cohort_id": cohort.cohort_id,
                        "path": path,
                        "n_models": len(cohort.models),
                        "years": [m.display_year for m in cohort.models],
                        "protocol_version": cohort.protocol_version,
                    }
                )
            except RegistryError as exc:
                out.append({"cohort_id": path.stem, "path": path, "error": str(exc)})
        return out

    def load_file(self, path: Path | str) -> Cohort:
        path = Path(path)
        if not path.is_file():
            # allow bare cohort id
            candidate = self.registry_dir / f"cohort-{path}.yaml"
            if candidate.is_file():
                path = candidate
            else:
                raise RegistryError(f"cohort not found: {path}")
        # ensure adapters are bound before validation of adapter compatibility
        _ = self.adapters
        return load_cohort(path)

    def load(self, cohort_id_or_path: str | Path) -> Cohort:
        return self.load_file(cohort_id_or_path)

    def default_cohort(self) -> Cohort:
        """Prefer decade spine, then five-era, then local-v1, then lite."""
        preferred = [
            "cohort-decade-v0.yaml",
            "cohort-five-era-v1.yaml",
            "cohort-local-v1.yaml",
            "cohort-lite-v1.yaml",
        ]
        for name in preferred:
            path = self.registry_dir / name
            if path.is_file():
                return self.load_file(path)
        files = self.list_cohort_files()
        if not files:
            raise RegistryError(f"no cohort-*.yaml under {self.registry_dir}")
        return self.load_file(files[0])

    def quick_tour_ids(self, cohort: Cohort) -> list[str]:
        """Visible quick three-era tour.

        Prefer one model per interaction mode (base → instruction → chat) so the
        progress arc is honest: oldest base, a middle instruction model, newest
        chat. Fall back to oldest / middle / newest.
        """
        models = sorted(cohort.models, key=lambda m: (m.display_year, m.id))
        if len(models) <= 3:
            return [m.id for m in models]

        by_mode: dict[str, list] = {}
        for m in models:
            by_mode.setdefault(m.mode, []).append(m)

        picked = []
        for mode in ("base_continuation", "instruction", "chat"):
            pool = by_mode.get(mode) or []
            if not pool:
                continue
            if mode == "base_continuation":
                picked.append(pool[0])
            elif mode == "chat":
                picked.append(pool[-1])
            else:
                picked.append(pool[len(pool) // 2])
        if len(picked) == 3:
            picked.sort(key=lambda m: (m.display_year, m.id))
            return [m.id for m in picked]

        return [models[0].id, models[len(models) // 2].id, models[-1].id]

    def quick_tour_models(self, cohort: Cohort):
        """ModelSpecs for the quick three-era tour, chronological."""
        want = set(self.quick_tour_ids(cohort))
        models = [m for m in cohort.models if m.id in want]
        models.sort(key=lambda m: (m.display_year, m.id))
        return models
