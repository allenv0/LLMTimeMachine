# Hardware profiles

Preflight reports OS, architecture, Python/runtime, memory, accelerators, and free disk. It can **recommend** a profile but must **not** mutate the cohort.

| Profile | Intended capability | Expected behavior |
|---|---|---|
| Lite | 16 GB unified memory or ~12 GB VRAM | Smaller substitute cohort (e.g. GPT-2 small/medium + FLAN-T5-base/large); clear limitation banner. Not the default `local-v1` five-model standard cohort. |
| Standard | 32 GB unified memory or ~24 GB VRAM | Full five-model `local-v1` cohort; 7B models likely quantized (4-bit / 8-bit). |
| High | 64 GB unified memory or ~48 GB VRAM | Larger / less-quantized eligible cohort; bf16 possible for 7B models. |

## Detection heuristics

| Signal | Source |
|---|---|
| OS / arch | `platform.system()`, `platform.machine()` |
| Python / runtime | `platform.python_version()`, backend package versions |
| RAM | `psutil` if available, else `os.sysconf` / `sysctl` on macOS |
| CUDA / Metal | `torch` device probe when inference extra is installed |
| Free disk | `shutil.disk_usage` on model cache and `local-data` |

## Timing targets (reported, not promised)

- First visible model status: under 10 seconds after Run.
- Local input validation: immediate.
- No UI freeze during generation (Streamlit rerun / status updates).
- Full standard-cohort trip: measure and publish actual timing; aim for usable single-digit minutes on Standard.

If the full standard cohort exceeds the usability target, offer a visible **quick three-era tour**. Do not hide delay or silently reduce output quality.
