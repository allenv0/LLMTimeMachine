"""Hardware and runtime preflight."""

from __future__ import annotations

import platform
import shutil
import sys
from pathlib import Path
from typing import Any

from llm_time_machine.config import AppPaths
from llm_time_machine.domain import Cohort, ModelSpec, RunnerAvailability


def _mac_memory_bytes() -> int | None:
    if platform.system() != "Darwin":
        return None
    try:
        import subprocess

        out = subprocess.check_output(["sysctl", "-n", "hw.memsize"], text=True).strip()
        return int(out)
    except Exception:
        return None


def _linux_memory_bytes() -> int | None:
    try:
        with open("/proc/meminfo", encoding="utf-8") as fh:
            for line in fh:
                if line.startswith("MemTotal:"):
                    parts = line.split()
                    return int(parts[1]) * 1024
    except Exception:
        return None
    return None


def detect_memory_bytes() -> int | None:
    mem = _mac_memory_bytes() or _linux_memory_bytes()
    if mem:
        return mem
    try:
        import os

        if hasattr(os, "sysconf"):
            if "SC_PAGE_SIZE" in os.sysconf_names and "SC_PHYS_PAGES" in os.sysconf_names:
                return os.sysconf("SC_PAGE_SIZE") * os.sysconf("SC_PHYS_PAGES")
    except Exception:
        return None
    return None


def detect_accelerator() -> dict[str, Any]:
    info: dict[str, Any] = {"name": None, "kind": "cpu", "available_memory_mb": None}
    try:
        import torch  # type: ignore

        if torch.cuda.is_available():
            info["kind"] = "cuda"
            info["name"] = torch.cuda.get_device_name(0)
            try:
                free, total = torch.cuda.mem_get_info()
                info["available_memory_mb"] = int(free / (1024 * 1024))
                info["total_memory_mb"] = int(total / (1024 * 1024))
            except Exception:
                pass
        elif getattr(torch.backends, "mps", None) and torch.backends.mps.is_available():
            info["kind"] = "mps"
            info["name"] = "Apple Metal"
        else:
            info["name"] = platform.processor() or platform.machine()
    except Exception:
        info["name"] = platform.processor() or platform.machine()
    return info


def free_disk_mb(path: Path) -> int | None:
    try:
        path.mkdir(parents=True, exist_ok=True)
        usage = shutil.disk_usage(path)
        return int(usage.free / (1024 * 1024))
    except Exception:
        return None


def recommend_profile(memory_bytes: int | None, accel_kind: str) -> str:
    gib = (memory_bytes or 0) / (1024**3)
    if gib >= 60:
        return "high"
    if gib >= 28:
        return "standard"
    if gib >= 14:
        return "lite"
    return "unknown" if not memory_bytes else "lite"


def runtime_versions() -> dict[str, str]:
    versions = {
        "python": platform.python_version(),
        "platform": f"{platform.system()} {platform.release()} {platform.machine()}",
    }
    for mod_name in ("torch", "transformers", "pydantic", "streamlit", "llama_cpp"):
        try:
            mod = __import__(mod_name)
            versions[mod_name] = getattr(mod, "__version__", "present")
        except Exception:
            versions[mod_name] = "not installed"
    return versions


def hardware_summary(paths: AppPaths | None = None) -> dict[str, Any]:
    paths = paths or AppPaths()
    memory = detect_memory_bytes()
    accel = detect_accelerator()
    profile = recommend_profile(memory, accel.get("kind", "cpu"))
    return {
        "os": platform.system(),
        "arch": platform.machine(),
        "python_version": platform.python_version(),
        "memory_bytes": memory,
        "memory_gib": round(memory / (1024**3), 1) if memory else None,
        "accelerator": accel,
        "free_disk_model_cache_mb": free_disk_mb(paths.model_cache_dir),
        "free_disk_local_data_mb": free_disk_mb(paths.local_data_dir),
        "recommended_profile": profile,
        "runtime_versions": runtime_versions(),
    }


def artifact_available(spec: ModelSpec, model_cache: Path) -> bool:
    """True when a local artifact directory/file exists for the pinned source."""
    dest = model_cache / spec.id
    art = dest / spec.source.artifact_filename
    return dest.is_dir() and (art.is_file() or any(dest.glob("*.safetensors")) or any(dest.glob("*.gguf")))


def assess_model(spec: ModelSpec, paths: AppPaths) -> RunnerAvailability:
    memory = detect_memory_bytes()
    accel = detect_accelerator()
    rec = recommend_profile(memory, accel.get("kind", "cpu"))
    present = artifact_available(spec, paths.model_cache_dir)

    profile_rank = {"lite": 1, "standard": 2, "high": 3}
    need = profile_rank.get(spec.hardware_profile, 2)
    have = profile_rank.get(rec, 0) if rec in profile_rank else 0

    if not present:
        return RunnerAvailability(
            available=False,
            reason="checkpoint not preloaded; run `llmtimemachine preload` first",
            hardware_profile=rec if rec in profile_rank else "unknown",
            details={"artifact_present": False},
        )
    if have and have < need:
        return RunnerAvailability(
            available=False,
            reason=(
                f"likely unsupported on this host: model profile {spec.hardware_profile}, "
                f"recommended {rec}"
            ),
            hardware_profile=rec if rec in profile_rank else "unknown",
            details={"artifact_present": True, "profile_ok": False},
        )
    return RunnerAvailability(
        available=True,
        reason="ok",
        hardware_profile=rec if rec in profile_rank else "unknown",
        details={"artifact_present": True, "profile_ok": True},
    )


def assess_cohort(cohort: Cohort, paths: AppPaths) -> dict[str, RunnerAvailability]:
    return {m.id: assess_model(m, paths) for m in cohort.models}


def preflight_report(cohort: Cohort, paths: AppPaths) -> dict[str, Any]:
    return {
        "hardware": hardware_summary(paths),
        "models": {mid: avail.model_dump() for mid, avail in assess_cohort(cohort, paths).items()},
        "local_data_path": str(paths.local_data_dir),
        "model_cache_path": str(paths.model_cache_dir),
    }
