# LLM Time Machine

A laptop-compatible, auditable sample of LLM history. It is **not** a verified record of the best model in every year.

This is the **local demo** of the LLM time-travel idea (`idea.md`): one prompt, a frozen historical cohort, chronological reveal, full audit trail, local-only storage. See `IMPLEMENTATION_PLAN.md` and `PROTOCOL.md` for the methodological contract.

## Quick start

```bash
# 1) Create a virtualenv and install (editable + dev)
uv sync --dev

# 2) Run the automated suite (no model weights required)
uv run pytest

# 3) Launch the UI on loopback only
uv run streamlit run app.py --server.address 127.0.0.1 --server.port 8501
```

Open http://127.0.0.1:8501

The default **fake** runner works with no downloads and no network. Use it to explore the trip timeline, audit drawers, blind compare, export, and delete.

## What you get

| Surface | What it does |
|---|---|
| Landing disclosures | Local-only claim, cohort limitation, historical input formats |
| Prompt form | ≤900 chars, optional success criterion, starter prompts, live counter |
| Trip scope | **Run full trip** (all eras) or **Quick three-era tour** (base → instruction → chat) |
| Timeline | Sequential load → generate → complete/failed per era |
| Progress arc | Three-stop Base → Instruction → Chat comparison for the same prompt |
| Personal quality curve | −2..+2 ordinal from *your* ratings (Track A, `local-v1`) |
| Judge estimate | Opt-in local LLM-judge (`local-v2-eval`, experimental, not ground truth) |
| Diary | Pre-register prompts, first-solved year, decade-walk reflections |
| Decade walk | One year at a time with reflection pauses (simulated lived timeline) |
| Result cards | Year, mode badge, output or failure card, limitations, timings, usefulness/tags/notes |
| Audit view | Raw prompt, exact prepared input, adapter explanation, source pin, generation/runtime |
| Blind compare | Stable A–E mapping per trip, rank/tie/unranked, explicit reveal |
| Local data | Export ZIP/JSON, delete one trip (confirm), delete all (typed `DELETE-ALL`) |

## Cohort (`local-v1`)

| Year | Checkpoint | Mode |
|---|---|---|
| 2019 | GPT-2 XL | base continuation |
| 2021 | GPT-J 6B | base continuation |
| 2022 | FLAN-T5 XL | instruction |
| 2023 | Mistral 7B Instruct v0.2 | chat |
| 2024 | Qwen2.5 7B Instruct | chat |

Pinned revisions and licenses: `docs/model-sources.md`. Registry: `registry/cohort-local-v1.yaml`.

## Lite host (16 GB RAM) — five-era cohort

On a 16 GB Mac with ~25 GB free disk, use the labeled five-era cohort (the best `idea.md` arc that fits):

```bash
# ~14 GB weights: GPT-2, GPT-2 Medium, FLAN-T5 Large, Mistral-7B Q4, Qwen2.5-7B Q4
uv run python scripts/preload_five_era.py

# App auto-selects cohort-five-era-v1 when present
uv run streamlit run app.py --server.address 127.0.0.1 --server.port 8501
```

Sidebar runner: **composite** (default) runs the full five-era trip (transformers + llama.cpp). CLI alternative:

```bash
uv run python scripts/run_real_smoke.py "Do a super ultra deep analysis into the apple's design system"
```

Tiny 3-model fallback (~3 GB): `scripts/preload_lite.py` + `TIME_MACHINE_COHORT=registry/cohort-lite-v1.yaml`.

## Real models (optional)

```bash
# Install inference extras (large)
uv sync --extra inference

# Download ONLY registry-pinned artifacts (never triggered by a user prompt)
uv run time-machine preload
uv run time-machine preflight
```

Then set the sidebar runner to `transformers` or `quantized` in the UI. Without preloaded weights the app reports each model as unsupported instead of silently substituting another checkpoint.

Quantized GGUF path (optional extra `quantized`) uses llama.cpp and the adapter-prepared string only — no second opaque chat template.

## CLI

```bash
uv run time-machine preflight
uv run time-machine preload
uv run time-machine run-fake --prompt "Your idea here"
uv run time-machine export --trip-id <id> --format zip
uv run time-machine delete --trip-id <id>
uv run time-machine delete --all --confirm DELETE-ALL
```

## Privacy and safety

- Streamlit must bind to `127.0.0.1` (documented launch command).
- No paid API, no remote inference during a trip, no telemetry.
- Prompts and outputs live under `local-data/` (gitignored).
- Default logs omit raw prompt/output text. `TIME_MACHINE_DEBUG_CONTENT=1` enables dev content dumping and warns first.
- Historical outputs are shown unpolished; they can be incoherent, biased, or unsafe.

## Tests

```bash
uv run pytest -q
```

Covers registry validation, adapter rendering, trip orchestration (complete/partial/cancelled/timeout), atomic store, export isolation, deletion constraints, blind mapping stability, and UI service contracts. Manual real-model checklist: `docs/validation.md`.

## Repository layout

```text
app.py                     Streamlit UI (loopback)
PROTOCOL.md                Frozen local-v1 methodology
IMPLEMENTATION_PLAN.md     Product/methodology spec
registry/                  Cohort YAML + visible adapters
src/time_machine/          Domain, store, runners, services, UI modules
prompts/starter_prompts.jsonl
docs/                      model-sources, hardware, validation, decision-log
tests/                     pytest (fake runners only)
local-data/                gitignored trip artifacts
```

## Non-goals (local demo)

Public hosting, accounts, paid APIs, telemetry, LLM-as-judge scores, prompt corpora, tools/RAG/uploads, silent retries, or claims of annual frontier coverage.
