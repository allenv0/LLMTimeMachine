# Protocol appendix: local-v2-eval (estimated machine quality)

**Status:** Optional experimental track. Does **not** replace `local-v1`.  
**Base protocol:** `local-v1` remains in force for trips, privacy, adapters, and generation.

## Why this appendix exists

`idea.md` asks for automatic quality ranks and a graph over time. `local-v1` correctly forbids silent LLM-as-judge scoring. This appendix defines a **loud, inspectable, opt-in** judge track so estimated scores can exist without pretending they are ground truth.

## Claim boundary

> Estimated scores are produced by a pinned local judge model under a versioned rubric. They are **not** scientific measurements, **not** ground truth, and **not** comparable across rubric or judge versions.

UI copy when any judge score is visible must include an experimental banner with this meaning.

## Rules

1. **Explicit action only.** Judge scoring never runs during `run_trip`. The user must trigger **“Score with local judge (experimental)”**.
2. **Separate identity.** The judge is recorded as `judge_model_id` + `judge_revision` + `rubric_id` on every score. Prefer a judge that is **not** the status-quo (“today”) display slot.
3. **Versioned rubric.** Rubric text lives in `registry/judges/rubric-*.yaml` and is exported with scores. Changing anchors ⇒ new `rubric_id`.
4. **Refuse rather than invent.** If the task is unverifiable (private unpublished facts, personal taste with no criterion), the judge must return `unscored` + reason. Never coerce a 1–10.
5. **Full audit.** Each score stores: prepared judge input, raw judge output, parsed score or unscored reason, generation profile, seed, and artifact checksum when available.
6. **Offline after preload.** No network during scoring.
7. **Human curves stay separate.** Track A ordinal ratings and Track B estimated scores never silently merge into one line without labels.
8. **Protocol banner.** Any estimated quality chart shows `local-v2-eval` and the rubric id.

## JudgeScore schema (logical)

| Field | Meaning |
|---|---|
| `model_id` | Historical model being scored |
| `trip_id` | Trip under evaluation |
| `status` | `scored` \| `unscored` \| `failed` |
| `score_1_10` | Integer 1–10 when `status=scored` |
| `unscored_reason` | Why no score (required when unscored) |
| `rubric_id` | e.g. `judge-rubric-v1` |
| `judge_model_id` / `judge_revision` | Pinned judge identity |
| `judge_prompt_sha256` | Hash of prepared judge input |
| `judge_output_path` | Relative path to raw judge transcript |
| `sampled_at` | UTC timestamp |

## Storage

```text
local-data/judge/<trip_id>/<model_id>/score.json
local-data/judge/<trip_id>/<model_id>/judge-input.txt
local-data/judge/<trip_id>/<model_id>/judge-output.txt
```

Derived and deletable with the trip. Not written into `manifest.json` run telemetry as if it were generation.

## Out of scope for local-v2-eval

- Global density overlays (need a corpus pack / cloud-v1).
- Email updates, accounts, public sharing.
- Using judge scores as automatic retries or model substitution.
