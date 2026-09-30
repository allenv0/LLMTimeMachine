"""Optional FUTURE synthetic endpoint (WS6). Quarantined. Off by default.

Best-of-n across member models and/or seeds under a frozen selection rule.
Never a historical year. Cannot mark first-solved unless the user opts in.
"""

from __future__ import annotations

import json
from pathlib import Path
from uuid import uuid4

from llm_time_machine.domain import Cohort, FutureSlot, GenerationConfig, ModelSpec, TripManifest
from llm_time_machine.errors import ArtifactError


def future_slot(cohort: Cohort) -> FutureSlot | None:
    return cohort.future


def future_enabled(cohort: Cohort) -> bool:
    slot = cohort.future
    return bool(slot and slot.enabled and slot.member_model_ids and slot.selection_rule.strip())


def member_models(cohort: Cohort) -> list[ModelSpec]:
    slot = cohort.future
    if not slot:
        return []
    by_id = {m.id: m for m in cohort.models}
    out = []
    for mid in slot.member_model_ids:
        if mid in by_id:
            out.append(by_id[mid])
    return out


class FutureEnsemble:
    """Produce a labeled synthetic endpoint by sampling members × seeds.

    Selection rule (frozen in cohort.future.selection_rule):
      - generate n_seeds per member with distinct seeds derived from base seed
      - rank candidates with an explicit scorer (judge callback or heuristic)
      - ties: lower mean generation seconds, then model_id ascending
    """

    def __init__(
        self,
        cohort: Cohort,
        factory,
        scorer=None,
    ) -> None:
        self.cohort = cohort
        self.factory = factory
        self.scorer = scorer  # optional callable(output_text, raw_prompt) -> float

    def _config_for_seed(self, base: GenerationConfig, seed: int) -> GenerationConfig:
        data = base.model_dump()
        data["seed"] = seed
        return GenerationConfig.model_validate(data)

    def generate_candidates(
        self,
        raw_prompt: str,
        *,
        prepare_fn,
        block_network_during_trip: bool = True,
    ) -> list[dict]:
        slot = self.cohort.future
        if not future_enabled(self.cohort):
            raise ArtifactError("FUTURE ensemble is disabled (off by default)")
        base = self.cohort.generation_profiles[self.cohort.generation_profile_id]
        candidates: list[dict] = []
        members = member_models(self.cohort)
        if not members:
            raise ArtifactError("FUTURE ensemble has no member models on disk/registry")

        from llm_time_machine.network_guard import block_network

        with block_network(enabled=block_network_during_trip):
            for spec in members:
                prepared = prepare_fn(raw_prompt, spec)
                runner = self.factory.create_for_spec(spec)
                try:
                    for i in range(slot.n_seeds):
                        cfg = self._config_for_seed(base, base.seed + 1000 + i)
                        result = runner.generate(prepared, spec, cfg)
                        candidates.append(
                            {
                                "model_id": spec.id,
                                "seed": cfg.seed,
                                "output_text": result.output_text,
                                "generation_seconds": 0.0,
                            }
                        )
                finally:
                    try:
                        runner.unload()
                    except Exception:
                        pass
        return candidates

    def select(self, candidates: list[dict], raw_prompt: str) -> dict:
        slot = self.cohort.future
        if not candidates:
            raise ArtifactError("no FUTURE candidates to select")
        if self.scorer is not None:
            def score_of(c: dict) -> float:
                try:
                    return float(self.scorer(c["output_text"], raw_prompt))
                except Exception:
                    return float("-inf")
        else:
            # Visible heuristic when no judge is wired: longer coherent non-empty text,
            # then deterministic tie-break. Recorded in selection_rule metadata.
            def score_of(c: dict) -> float:
                text = (c.get("output_text") or "").strip()
                return float(len(text))

        ranked = sorted(
            candidates,
            key=lambda c: (
                -score_of(c),
                float(c.get("generation_seconds") or 0.0),
                str(c.get("model_id") or ""),
                int(c.get("seed") or 0),
            ),
        )
        best = dict(ranked[0])
        best["selection_rule"] = (slot.selection_rule if slot else "").strip()
        best["method"] = slot.method if slot else "best-of-n-seeds"
        best["n_candidates"] = len(candidates)
        best["quarantine_note"] = (
            slot.quarantine_note if slot else "Synthetic. Not a historical year."
        )
        best["ranking"] = [
            {
                "model_id": c["model_id"],
                "seed": c["seed"],
                "score": score_of(c),
            }
            for c in ranked
        ]
        return best

    def run(
        self,
        raw_prompt: str,
        *,
        prepare_fn,
        trip_id: str | None = None,
        store=None,
        block_network_during_trip: bool = True,
    ) -> dict:
        candidates = self.generate_candidates(
            raw_prompt,
            prepare_fn=prepare_fn,
            block_network_during_trip=block_network_during_trip,
        )
        best = self.select(candidates, raw_prompt)
        result = {
            "trip_id": trip_id or f"future-{uuid4().hex[:10]}",
            "future_synthetic": True,
            "display_name": (self.cohort.future.display_name if self.cohort.future else "FUTURE"),
            "output_text": best["output_text"],
            "selected_model_id": best["model_id"],
            "selected_seed": best["seed"],
            "selection_rule": best["selection_rule"],
            "method": best["method"],
            "n_candidates": best["n_candidates"],
            "ranking": best["ranking"],
            "quarantine_note": best["quarantine_note"],
            "candidates": [
                {k: c[k] for k in ("model_id", "seed", "output_text")} for c in candidates
            ],
        }
        if store is not None:
            # Store under local-data/future/<trip_id>.json — never a year slot.
            root = Path(store.paths.local_data_dir) / "future"
            root.mkdir(parents=True, exist_ok=True)
            path = root / f"{result['trip_id']}.json"
            path.write_text(
                json.dumps(result, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
            )
        return result


def future_mark_first_solved_allowed(user_opt_in: bool) -> bool:
    """FUTURE cannot mark first-solved unless the user opts in (WS6)."""
    return bool(user_opt_in)
