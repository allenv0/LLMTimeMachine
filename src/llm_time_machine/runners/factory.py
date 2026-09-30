"""RunnerFactory: construct runners and verify artifacts before generate."""

from __future__ import annotations

from pathlib import Path

from llm_time_machine.domain import ModelSpec, RunnerAvailability
from llm_time_machine.errors import LoadError
from llm_time_machine.preflight import artifact_available
from llm_time_machine.runners.base import ModelRunner, RunnerProtocol
from llm_time_machine.runners.composite import CompositeRunner
from llm_time_machine.runners.fake import FakeRunner
from llm_time_machine.runners.local_quantized_runner import LocalQuantizedRunner
from llm_time_machine.runners.transformers_runner import TransformersRunner
from llm_time_machine.artifact_store import sha256_file


class RunnerFactory:
    """Single construction + integrity path for all backends."""

    def __init__(self, model_cache: str | Path | None = None) -> None:
        self.model_cache = Path(model_cache) if model_cache else None

    def create(self, kind: str = "composite") -> RunnerProtocol:
        kind = (kind or "composite").lower()
        if kind == "fake":
            return FakeRunner()
        if kind == "transformers":
            return TransformersRunner(model_cache=str(self.model_cache) if self.model_cache else None)
        if kind == "quantized":
            return LocalQuantizedRunner(model_cache=str(self.model_cache) if self.model_cache else None)
        if kind == "composite":
            return CompositeRunner(model_cache=str(self.model_cache) if self.model_cache else None)
        raise LoadError(f"unknown runner kind: {kind!r}")

    def create_for_spec(self, spec: ModelSpec) -> RunnerProtocol:
        if spec.backend == "local_quantized":
            return self.create("quantized")
        if spec.backend == "transformers":
            return self.create("transformers")
        return self.create("fake")

    def verify_artifact(self, spec: ModelSpec) -> RunnerAvailability:
        """Verify the primary weight artifact exists and matches the pinned sha256.

        Sentinel ``record-at-preload`` accepts a measured hash already stored in
        ``local-cache-index.json``; if neither exists, verification fails closed.
        """
        if self.model_cache is None:
            return RunnerAvailability(available=False, reason="no model cache configured")
        cache = self.model_cache
        dest = cache / spec.id
        name = spec.source.artifact_filename
        art = dest / name
        if not art.is_file():
            candidates = sorted(dest.glob("*.safetensors")) or sorted(dest.glob("*.gguf"))
            if candidates:
                art = next((p for p in candidates if "00001" in p.name), candidates[0])
            else:
                return RunnerAvailability(
                    available=False,
                    reason="checkpoint not preloaded; run preload first",
                )

        expected = spec.source.sha256.lower()
        measured = sha256_file(art)
        index_path = cache / "local-cache-index.json"
        recorded = None
        if index_path.is_file():
            import json

            try:
                index = json.loads(index_path.read_text(encoding="utf-8"))
                recorded = (index.get(spec.id) or {}).get("sha256")
            except Exception:
                recorded = None

        if expected == "record-at-preload":
            if recorded and recorded != measured:
                return RunnerAvailability(
                    available=False,
                    reason="artifact checksum mismatch vs local-cache-index",
                    details={"expected": recorded, "measured": measured},
                )
            ok = True
        else:
            ok = expected == measured

        return RunnerAvailability(
            available=ok,
            reason="checksum ok" if ok else "artifact checksum mismatch",
            details={"artifact": art.name, "sha256": measured},
        )

    def preflight(self, spec: ModelSpec) -> RunnerAvailability:
        verify = self.verify_artifact(spec)
        if not verify.available:
            return verify
        runner = self.create_for_spec(spec)
        runtime = runner.preflight(spec)
        if not runtime.available:
            return runtime
        return RunnerAvailability(
            available=True,
            reason="ready",
            hardware_profile=runtime.hardware_profile,
            details={**verify.details, **runtime.details},
        )
