"""Explicit local judge scoring (protocol local-v2-eval).

Never invoked by TripController during a trip. User must request scoring.
"""

from __future__ import annotations

import json
from pathlib import Path

import yaml

from time_machine.artifact_store import sha256_text
from time_machine.config import AppPaths, PROTOCOL_VERSION
from time_machine.domain import GenerationConfig, JudgeScore, ModelRun, TripManifest
from time_machine.errors import LoadError, RegistryError
from time_machine.judge_prompts import (
    hash_judge_input,
    load_judge_config,
    load_rubric,
    parse_judge_reply,
    render_judge_input,
)
from time_machine.runners.factory import RunnerFactory

EVAL_PROTOCOL = "local-v2-eval"
BANNER = (
    "EXPERIMENTAL estimated quality (local-v2-eval). "
    "Not a scientific measurement and not ground truth."
)


class JudgeService:
    """Scores completed trip outputs with a pinned local judge + visible rubric."""

    def __init__(
        self,
        paths: AppPaths,
        factory: RunnerFactory | None = None,
        judge_config_path: Path | None = None,
        rubric_path: Path | None = None,
    ) -> None:
        self.paths = paths
        self.factory = factory or RunnerFactory(model_cache=str(paths.model_cache_dir))
        jdir = paths.judges_registry_dir
        self.judge_config_path = Path(judge_config_path or jdir / "judge-v1.yaml")
        self.rubric_path = Path(rubric_path or jdir / "rubric-v1.yaml")
        self._judge_cfg: dict | None = None
        self._rubric: dict | None = None

    @property
    def judge_cfg(self) -> dict:
        if self._judge_cfg is None:
            self._judge_cfg = load_judge_config(self.judge_config_path)
        return self._judge_cfg

    @property
    def rubric(self) -> dict:
        if self._rubric is None:
            self._rubric = load_rubric(self.rubric_path)
        return self._rubric

    @property
    def banner(self) -> str:
        return BANNER

    def rubric_text(self) -> str:
        return yaml.safe_dump(self.rubric, sort_keys=False, allow_unicode=True)

    def score_dir(self, trip_id: str, model_id: str) -> Path:
        return self.paths.judge_dir / trip_id / model_id

    def _generation_config(self) -> GenerationConfig:
        profiles = self.judge_cfg.get("generation_profiles") or {}
        pid = self.judge_cfg.get("generation_profile_id") or "local-v2-judge"
        if pid not in profiles:
            raise RegistryError(f"judge generation profile missing: {pid}")
        return GenerationConfig.model_validate(profiles[pid])

    def _judge_model_ref(self) -> str:
        """Resolve judge weights: prefer dedicated id, else artifact_from_model_id."""
        return str(
            self.judge_cfg.get("artifact_from_model_id") or self.judge_cfg.get("judge_model_id")
        )

    def score_run(
        self,
        *,
        trip_id: str,
        run: ModelRun,
        raw_prompt: str,
        success_criterion: str,
        output_text: str,
    ) -> JudgeScore:
        rubric = self.rubric
        judge_model_id = str(self.judge_cfg.get("judge_model_id"))
        judge_revision = str(self.judge_cfg.get("judge_revision") or "")
        base = dict(
            model_id=run.model_id,
            trip_id=trip_id,
            display_year=run.display_year,
            rubric_id=str(rubric.get("id")),
            judge_model_id=judge_model_id,
            judge_revision=judge_revision,
            protocol=EVAL_PROTOCOL,
            limitations=list(self.judge_cfg.get("limitations") or []),
        )

        if run.status != "completed" or not output_text.strip():
            return JudgeScore(
                **base,
                status="unscored",
                unscored_reason="candidate output missing or run not completed",
            )

        prepared = render_judge_input(
            rubric,
            raw_prompt=raw_prompt,
            success_criterion=success_criterion,
            model_id=run.model_id,
            display_year=run.display_year or 0,
            output_text=output_text,
        )
        out_dir = self.score_dir(trip_id, run.model_id)
        out_dir.mkdir(parents=True, exist_ok=True)
        (out_dir / "judge-input.txt").write_text(prepared, encoding="utf-8")

        try:
            result = self._generate(prepared)
        except Exception as exc:
            (out_dir / "judge-output.txt").write_text(f"ERROR: {exc}", encoding="utf-8")
            return JudgeScore(
                **base,
                status="failed",
                unscored_reason=str(exc)[:200],
                judge_prompt_sha256=hash_judge_input(prepared),
                judge_input_path="judge-input.txt",
                judge_output_path="judge-output.txt",
            )

        (out_dir / "judge-output.txt").write_text(result, encoding="utf-8")
        status, score, reason = parse_judge_reply(result)
        # Write full score record
        record = JudgeScore(
            **base,
            status=status,
            score_1_10=score,
            unscored_reason=reason,
            judge_prompt_sha256=hash_judge_input(prepared),
            judge_input_path="judge-input.txt",
            judge_output_path="judge-output.txt",
        )
        (out_dir / "score.json").write_text(
            json.dumps(record.model_dump(mode="json"), indent=2, ensure_ascii=False) + "\n",
            encoding="utf-8",
        )
        # also stash generation config used
        (out_dir / "generation.json").write_text(
            json.dumps(self._generation_config().model_dump(mode="json"), indent=2) + "\n",
            encoding="utf-8",
        )
        return record

    def _generate(self, prepared_text: str) -> str:
        """Run the judge model on prepared text only (visible template)."""
        from time_machine.domain import ModelSpec, PreparedInput
        from time_machine.prompt_adapters import prepare_input

        ref = self._judge_model_ref()
        # Build a minimal spec-like prepare via adapter if possible
        adapter_id = str(self.judge_cfg.get("adapter_id") or "instruction-v1")
        # Judge input is already a full task; use identity-style pass-through when adapter is instruction
        if adapter_id == "instruction-v1":
            judge_prompt = prepared_text
        else:
            judge_prompt = prepared_text

        # Prefer transformers/quantized based on a tiny probe spec
        # Use FakeRunner-like direct call through factory for the real backend
        model_id = ref
        cache = self.paths.model_cache_dir / model_id
        if not cache.is_dir():
            raise LoadError(f"judge weights not preloaded under {cache}")

        # Construct a throwaway ModelSpec for the runner
        spec = self._spec_for_judge()
        prepared = PreparedInput(
            model_id=spec.id,
            raw_prompt=judge_prompt,
            adapter_id=spec.adapter_id,
            adapter_version=spec.adapter_version,
            prepared_text=judge_prompt,
            was_truncated=False,
            preparation_notes=["judge input rendered from rubric-v1; no extra system prompt"],
        )
        config = self._generation_config()
        runner = self.factory.create_for_spec(spec)
        try:
            result = runner.generate(prepared, spec, config)
            return result.output_text
        finally:
            runner.unload()

    def _spec_for_judge(self):
        from datetime import date

        from time_machine.domain import ModelSource, ModelSpec

        cfg = self.judge_cfg
        model_id = self._judge_model_ref()
        return ModelSpec(
            id=model_id,
            display_year=2000,  # judge is not a historical display slot
            display_name=str(cfg.get("judge_display_name") or cfg.get("judge_model_id")),
            release_date=date(2022, 1, 1),
            mode="instruction",
            source=ModelSource(
                repository=f"local/judge/{model_id}",
                revision=str(cfg.get("judge_revision") or "judge-local-pin"),
                artifact_filename="model.safetensors",
                sha256="record-at-preload",
            ),
            license_url="https://huggingface.co/google/flan-t5-large",
            backend="transformers",
            precision="fp32",
            adapter_id=str(cfg.get("adapter_id") or "instruction-v1"),
            adapter_version=str(cfg.get("adapter_version") or "1"),
            input_limit_chars=8000,
            generation_profile_id=str(cfg.get("generation_profile_id") or "local-v2-judge"),
            limitations=list(cfg.get("limitations") or ["judge estimate only"]),
            hardware_profile="lite",
        )

    def score_trip(
        self,
        store,
        trip_id: str,
        model_ids: list[str] | None = None,
    ) -> list[JudgeScore]:
        """Explicit trip scoring. Returns one JudgeScore per selected completed run."""
        manifest: TripManifest = store.read_manifest(trip_id)
        raw_prompt = store.read_raw_prompt(trip_id)
        criterion = store.read_success_criterion(trip_id)
        scores: list[JudgeScore] = []
        for run in manifest.runs:
            if model_ids is not None and run.model_id not in model_ids:
                continue
            if run.status != "completed":
                scores.append(
                    JudgeScore(
                        model_id=run.model_id,
                        trip_id=trip_id,
                        display_year=run.display_year,
                        status="unscored",
                        unscored_reason=f"run status {run.status}",
                        rubric_id=str(self.rubric.get("id")),
                        judge_model_id=str(self.judge_cfg.get("judge_model_id")),
                        judge_revision=str(self.judge_cfg.get("judge_revision") or ""),
                        protocol=EVAL_PROTOCOL,
                    )
                )
                continue
            output = store.read_output(trip_id, run.model_id)
            scores.append(
                self.score_run(
                    trip_id=trip_id,
                    run=run,
                    raw_prompt=raw_prompt,
                    success_criterion=criterion,
                    output_text=output,
                )
            )
        return scores

    def read_scores(self, trip_id: str) -> list[JudgeScore]:
        root = self.paths.judge_dir / trip_id
        if not root.is_dir():
            return []
        out: list[JudgeScore] = []
        for path in sorted(root.glob("*/score.json")):
            try:
                out.append(JudgeScore.model_validate(json.loads(path.read_text(encoding="utf-8"))))
            except Exception:
                continue
        return out


class JudgeEvaluator:
    """EvaluationPort-compatible shell. Does NOT auto-score.

    TripController may call evaluate_*; those stay no-ops so local-v1 trips
    never acquire silent judge artifacts. Use JudgeService.score_trip explicitly.
    """

    def __init__(self, service: JudgeService) -> None:
        self.service = service

    def evaluate_run(self, run, output_text: str) -> dict:
        return {}

    def evaluate_trip(self, manifest) -> dict:
        return {"judge": "not_run", "banner": BANNER}


__all__ = ["JudgeService", "JudgeEvaluator", "EVAL_PROTOCOL", "BANNER", "PROTOCOL_VERSION"]
