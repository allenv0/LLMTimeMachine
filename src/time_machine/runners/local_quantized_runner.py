"""Optional quantized local runner (llama.cpp GGUF) when a 7B model needs it."""

from __future__ import annotations

import gc
import time
from pathlib import Path

from time_machine.domain import (
    GenerationConfig,
    GenerationResult,
    ModelSpec,
    PreparedInput,
    RuntimeInfo,
    RunnerAvailability,
)
from time_machine.errors import LoadError
from time_machine.prompt_adapters import prepare_input
from time_machine.runners.base import ModelRunner


def _stop_sequences() -> list[str]:
    # Built without raw angle-bracket close sequences in source.
    eos = "<" + "/s>"
    eot = "<" + "|im_end|>"
    eoa = "<" + "|eot_id|>"
    return [eos, eot, eoa]


class LocalQuantizedRunner(ModelRunner):
    """llama.cpp-backed runner. Uses the adapter-prepared string only (no second template)."""

    def __init__(self, model_cache: str | Path | None = None, n_ctx: int = 2048) -> None:
        self.model_cache = Path(model_cache) if model_cache else None
        self.n_ctx = n_ctx
        self._llm = None
        self._loaded_id: str | None = None

    def preflight(self, spec: ModelSpec) -> RunnerAvailability:
        try:
            import llama_cpp  # noqa: F401
        except Exception as exc:
            return RunnerAvailability(
                available=False,
                reason=f"llama_cpp not installed: {exc}",
                hardware_profile="standard",
            )
        path = self._artifact_path(spec)
        if not path.exists():
            return RunnerAvailability(
                available=False,
                reason=f"GGUF artifact missing: {path}",
                hardware_profile="standard",
            )
        return RunnerAvailability(
            available=True, reason="llama_cpp available", hardware_profile="standard"
        )

    def _artifact_path(self, spec: ModelSpec) -> Path:
        if self.model_cache:
            base = Path(self.model_cache) / spec.id
            named = base / spec.source.artifact_filename
            if named.exists():
                return named
            # Prefer the first shard of multi-file GGUF exports.
            ggufs = sorted(base.glob("*.gguf"))
            if ggufs:
                first = next((p for p in ggufs if "00001" in p.name), ggufs[0])
                return first
            return named
        return Path(spec.source.artifact_filename)

    def prepare(self, raw_prompt: str, spec: ModelSpec) -> PreparedInput:
        return prepare_input(raw_prompt, spec)

    def _load(self, spec: ModelSpec):
        try:
            from llama_cpp import Llama
        except Exception as exc:
            raise LoadError(f"llama_cpp unavailable: {exc}") from exc

        path = self._artifact_path(spec)
        if not path.exists():
            raise LoadError(f"quantized artifact not found: {path}")
        try:
            llm = Llama(
                model_path=str(path),
                n_ctx=self.n_ctx,
                n_threads=4,
                verbose=False,
            )
            self._llm = llm
            self._loaded_id = spec.id
            return llm
        except Exception as exc:
            raise LoadError(f"failed to load {spec.id}: {exc}") from exc

    def generate(
        self,
        prepared: PreparedInput,
        spec: ModelSpec,
        config: GenerationConfig,
    ) -> GenerationResult:
        load_started = time.perf_counter()
        llm = self._load(spec)
        load_seconds = time.perf_counter() - load_started

        # Intentionally call with the adapter-prepared string only.
        # llama.cpp adds BOS itself; strip one leading BOS token to avoid duplication.
        prompt_text = prepared.prepared_text
        stripped_bos = False
        bos = "<" + "s>"  # <s>
        if prompt_text.startswith(bos):
            prompt_text = prompt_text[len(bos) :].lstrip()
            stripped_bos = True
        gen_started = time.perf_counter()
        try:
            result = llm(
                prompt_text,
                max_tokens=config.max_new_tokens,
                temperature=config.temperature,
                top_p=config.top_p,
                seed=config.seed,
                stop=_stop_sequences(),
            )
        except Exception as exc:
            message = str(exc)
            if "timeout" in message.lower() or "timed out" in message.lower():
                from time_machine.errors import GenerationTimeoutError

                raise GenerationTimeoutError(message) from exc
            from time_machine.errors import GenerationError

            raise GenerationError(message) from exc
        gen_seconds = time.perf_counter() - gen_started

        choices = result.get("choices") or []
        text = ""
        finish = "stop"
        if choices:
            text = (choices[0].get("text") or "").lstrip("\n")
            finish = choices[0].get("finish_reason") or "stop"

        try:
            import llama_cpp

            backend_version = getattr(llama_cpp, "__version__", "unknown")
        except Exception:
            backend_version = "unknown"

        return GenerationResult(
            output_text=text,
            finish_reason=finish,
            runtime=RuntimeInfo(
                backend="local_quantized",
                backend_version=backend_version,
                device="cpu",
                effective_generation={
                    "seed": config.seed,
                    "temperature": config.temperature,
                    "top_p": config.top_p,
                    "max_new_tokens": config.max_new_tokens,
                    "load_seconds": round(load_seconds, 4),
                    "generation_seconds": round(gen_seconds, 4),
                    "n_ctx": self.n_ctx,
                    "template": "adapter-prepared-text-only",
                    "stripped_leading_bos": stripped_bos,
                },
            ),
        )

    def unload(self) -> None:
        self._llm = None
        self._loaded_id = None
        gc.collect()
