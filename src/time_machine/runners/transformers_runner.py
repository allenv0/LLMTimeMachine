"""Hugging Face Transformers runner (legacy + encoder-decoder instruction models)."""

from __future__ import annotations

import gc
import time
from pathlib import Path
from typing import Any

from time_machine.domain import (
    GenerationConfig,
    GenerationResult,
    ModelSpec,
    PreparedInput,
    RuntimeInfo,
    RunnerAvailability,
)
from time_machine.errors import GenerationError, GenerationTimeoutError, LoadError, RunnerError
from time_machine.prompt_adapters import prepare_input
from time_machine.runners.base import ModelRunner


class TransformersRunner(ModelRunner):
    """Local Transformers inference with trust_remote_code disabled."""

    def __init__(
        self,
        model_cache: str | None = None,
        device: str | None = None,
        timeout_seconds: float = 300.0,
    ) -> None:
        self.model_cache = model_cache
        self.device = device
        self.timeout_seconds = timeout_seconds
        self._model: Any = None
        self._tokenizer: Any = None
        self._loaded_id: str | None = None

    def preflight(self, spec: ModelSpec) -> RunnerAvailability:
        try:
            import torch  # noqa: F401
            import transformers  # noqa: F401
        except Exception as exc:
            return RunnerAvailability(
                available=False,
                reason=f"transformers/torch not installed: {exc}",
                hardware_profile="unknown",
            )
        return RunnerAvailability(available=True, reason="transformers available", hardware_profile="standard")

    def prepare(self, raw_prompt: str, spec: ModelSpec) -> PreparedInput:
        return prepare_input(raw_prompt, spec)

    def _load(self, spec: ModelSpec) -> tuple[Any, Any]:
        try:
            import torch
            from transformers import AutoModelForCausalLM, AutoModelForSeq2SeqLM, AutoTokenizer
        except Exception as exc:
            raise LoadError(f"transformers runtime unavailable: {exc}") from exc

        local_files_only = self.model_cache is not None
        rev = spec.source.revision
        repo = spec.source.repository
        # Prefer the preloaded local directory so trips never touch the network.
        model_ref: str = repo
        if self.model_cache:
            local_dir = Path(self.model_cache) / spec.id
            if local_dir.is_dir() and any(local_dir.iterdir()):
                model_ref = str(local_dir)
                local_files_only = True
        try:
            tokenizer = AutoTokenizer.from_pretrained(
                model_ref,
                revision=rev if model_ref == repo else None,
                trust_remote_code=False,
                local_files_only=local_files_only,
            )
            # Prefer seq2seq for FLAN/T5 family
            if "t5" in repo.lower() or "flan" in repo.lower():
                model_cls = AutoModelForSeq2SeqLM
            else:
                model_cls = AutoModelForCausalLM
            model = model_cls.from_pretrained(
                model_ref,
                revision=rev if model_ref == repo else None,
                trust_remote_code=False,
                local_files_only=local_files_only,
                dtype=torch.float16 if spec.precision in {"fp16", "bf16"} else torch.float32,
            )
            device = self.device or ("mps" if getattr(torch.backends, "mps", None) and torch.backends.mps.is_available() else "cuda" if torch.cuda.is_available() else "cpu")
            model.to(device)
            model.eval()
            self._model = model
            self._tokenizer = tokenizer
            self._loaded_id = spec.id
            return model, tokenizer
        except Exception as exc:
            raise LoadError(f"failed to load {spec.id}: {exc}") from exc

    def generate(
        self,
        prepared: PreparedInput,
        spec: ModelSpec,
        config: GenerationConfig,
    ) -> GenerationResult:
        load_started = time.perf_counter()
        model, tokenizer = self._load(spec)
        load_seconds = time.perf_counter() - load_started

        try:
            import torch
        except Exception as exc:  # pragma: no cover
            raise GenerationError(str(exc)) from exc

        inputs = tokenizer(prepared.prepared_text, return_tensors="pt")
        device = next(model.parameters()).device
        inputs = {k: v.to(device) for k, v in inputs.items()}

        gen_started = time.perf_counter()
        try:
            torch.manual_seed(config.seed)
            with torch.no_grad():
                output_ids = model.generate(
                    **inputs,
                    max_new_tokens=config.max_new_tokens,
                    do_sample=config.temperature > 0,
                    temperature=max(config.temperature, 1e-5),
                    top_p=config.top_p,
                    pad_token_id=tokenizer.eos_token_id,
                )
        except Exception as exc:
            if "timed out" in str(exc).lower() or "timeout" in str(exc).lower():
                raise GenerationTimeoutError(str(exc)) from exc
            raise GenerationError(str(exc)) from exc
        finally:
            gen_seconds = time.perf_counter() - gen_started

        # decode only new tokens when causal
        try:
            if model.config.is_encoder_decoder:
                text = tokenizer.decode(output_ids[0], skip_special_tokens=True)
            else:
                in_len = inputs["input_ids"].shape[-1]
                text = tokenizer.decode(output_ids[0][in_len:], skip_special_tokens=True)
        except Exception:
            text = tokenizer.decode(output_ids[0], skip_special_tokens=True)

        try:
            import transformers

            tf_version = transformers.__version__
        except Exception:
            tf_version = "unknown"

        # stash load_seconds on the result via runtime
        return GenerationResult(
            output_text=text,
            runtime=RuntimeInfo(
                backend="transformers",
                backend_version=tf_version,
                device=str(next(model.parameters()).device),
                effective_generation={
                    "seed": config.seed,
                    "temperature": config.temperature,
                    "top_p": config.top_p,
                    "max_new_tokens": config.max_new_tokens,
                    "load_seconds": round(load_seconds, 4),
                    "generation_seconds": round(gen_seconds, 4),
                    "trust_remote_code": False,
                    "local_files_only": local_files_only if (local_files_only := self.model_cache is not None) else False,
                },
            ),
        )

    def unload(self) -> None:
        self._model = None
        self._tokenizer = None
        self._loaded_id = None
        gc.collect()
        try:
            import torch

            if torch.cuda.is_available():
                torch.cuda.empty_cache()
            if getattr(torch.backends, "mps", None) and torch.backends.mps.is_available():
                if hasattr(torch, "mps"):
                    torch.mps.empty_cache()
        except Exception:
            pass
