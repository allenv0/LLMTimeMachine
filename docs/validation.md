# Validation

Manual real-model validation record for protocol `local-v1` / `local-v2-eval` / `local-v3-longitudinal`. Fill rows after each hardware run. Do not conceal failures.

## Automated coverage (CI / local `pytest`)

| Area | Status | Notes |
|---|---|---|
| Registry validation | done | unit tests |
| Adapter rendering | done | unit tests |
| Manifest serialization | done | unit tests |
| Atomic store / delete | done | unit tests |
| Export isolation | done | unit tests |
| Preflight reporting | done | unit tests with fakes |
| Trip orchestration (fake runner) | done | partial/failed/cancelled/complete |
| Blind mapping stability | done | unit tests |
| UI service contracts | done | service-layer tests |
| Decade spine holes + status-quo | done | `test_wave_idea_full.py` |
| Diary schema v2 migration + re-run | done | `test_wave_idea_full.py` |
| Judge JSON contract + cache | done | `test_wave_idea_full.py` |
| Curve pack version gate + overlay | done | `test_wave_idea_full.py` |
| Chat multi-turn prepare + export | done | `test_wave_idea_full.py` |
| FUTURE quarantine + selection rule | done | `test_wave_idea_full.py` |
| Judge calibration report | done | `test_wave_idea_full.py` |

## Per-model manual matrix (five-era / decade-v0 running slots)

Host: 16GB unified Mac, composite runner (transformers + llama.cpp), weights under `local-data/model-cache/`.

| Model id | Rev/license/checksum | Audit match | Timings | Determinism | Unload | Failure path | Reviewer | Date |
|---|---|---|---|---|---|---|---|---|
| gpt2-2019 | rev pinned · HF openai-community/gpt2 · sha record-at-preload | prepared input = runner input (continuation-v1) | cold ~8–15s · gen ~2–8s · peak n/a | seed 20260923 stable enough for demo | unload before next | partial trip preserved | local | 2026-09-23 |
| gpt2-medium-2021 | rev pinned · substitute for GPT-J-class · sha record-at-preload | prepared input matches | cold ~10–20s · gen ~3–10s | frozen seed | ok | partial preserved | local | 2026-09-23 |
| flan-t5-large-2022 | rev pinned · substitute FLAN-XXL-class · sha record-at-preload | prepared = raw (instruction-v1) | cold ~8–15s · gen ~2–6s | frozen seed | ok | partial preserved | local | 2026-09-23 |
| mistral-7b-instruct-2023 | TheBloke GGUF rev `3a6fbf4a…` · Q4_K_M · sha record-at-preload | prepared = chat-mistral-v1; BOS strip recorded | cold ~15–30s · gen ~10–40s | temperature 0.7 seed fixed; not bit-identical across backends | ok | partial preserved | local | 2026-09-23 |
| qwen25-7b-instruct-2024 | Qwen GGUF rev `bb5d59e0…` · Q4_K_M sharded · sha record-at-preload | prepared = chat-qwen-v1 | cold ~20–40s · gen ~10–45s | frozen seed | ok | partial preserved | local | 2026-09-23 |

**Decade-v0 hole slots (2015, 2016, 2018, 2020, 2025, 2026):** no weights staged — UI dashed nodes with reasons. Not validation failures.

**Status-quo endpoint:** maps to `qwen25-7b-instruct-2024` with explicit “not verified 2026 frontier” note.

## Complete-cohort checks

| Check | Status | Notes |
|---|---|---|
| Network disabled after cache | done | `network_guard` during trips/judge/chat |
| Five distinct prompts (incl. one without dramatic progress) | done | pelican tour, grandma clue, apple design, easy capitals, private crossword |
| Ten consecutive trips, no restart | pending | soak not fully logged this pass |
| Delete/export on a real trip | done | zip/json isolation tests + real export |
| Independent audit-drawer + manifest trace | done | prepared inputs exact; hash matches |
| Diary re-run after new year slot | done (sim) | explicit re-run; not calendar time |
| Judge cache hit without re-generate | done | unit + cache-hit.json |
| Pack overlay min-n caveat | done | demonstration pack n=32 labeled |
| Chat 4-turn with GPT-2 and Mistral | done | prepare contains prior turns; export works |
| FUTURE off by default | done | decade-v0 future.enabled=false |

## Hardware profiles exercised

| Host | Profile | Cohort | Full-trip wall time | Date |
|---|---|---|---|---|
| 16GB unified Mac | standard (composite) | five-era-v1 / decade-v0 | tour ~32s (`deep-real-tour-final`); full five-era minutes | 2026-09-23 |

## Acceptance metrics (product decision, not marketing)

| Metric | Result |
|---|---|
| ≥5 non-builders complete a trip with their own prompt | pending field test |
| ≥3 run a second prompt or open the audit drawer | pending field test |
| Users can explain the cohort limitation after use | pending field test |
| Run→final latency measured per hardware profile | tour ~32s; full trip 2–8 min depending on quantized slots |
| Stable across 10 consecutive local trips after weights cached | pending soak |
