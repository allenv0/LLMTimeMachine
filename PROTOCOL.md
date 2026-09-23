# LLM Time Machine Protocol

**Protocol version:** `local-v1`  
**Status:** Frozen for the local demo  
**Cohort id:** `local-v1`

This document is the methodological contract for the local demo. The app, exports, and UI disclosures must remain consistent with it. Changing any rule here requires a new protocol version and an entry in `docs/decision-log.md`.

## Truthful claim

> A laptop-compatible, auditable sample of LLM history. It is not a verified record of the best model in every year.

The demo must never claim that it runs the historical frontier model for every year. Selected checkpoints are constrained by local deployability, licensing, and reproducibility.

## Scope

In scope for `local-v1`:

- One text prompt (optional success criterion) on a local browser UI bound to `127.0.0.1`.
- A frozen five-model cohort run sequentially.
- Chronological reveal, blind A–E comparison, personal ratings, local notes.
- Per-output audit view of raw prompt, exact prepared input, model metadata, generation settings, and limitations.
- Local trip storage with ZIP/JSON export and local deletion.
- Explicit failure cards for failed, timed-out, unsupported, or cancelled runs.

Out of scope (must not appear):

- Public hosting, accounts, auth, payments, multi-user concurrency.
- Paid model APIs or remote inference.
- Telemetry, analytics, cloud logging, email, prompt sharing.
- Automatic LLM-as-a-judge scoring or global benchmark overlays.
- Tools, browsing, RAG, file upload, code execution, multimodal input.
- Silent model substitution, hidden prompt rewriting, or automatic retries.

## Cohort rule

The cohort is a **laptop-compatible representative cohort**, not an annual frontier cohort.

| Display year | Target class | Mode | Purpose |
|---|---|---|---|
| 2019 | GPT-2 XL-class | base_continuation | Pre-chat behavior |
| 2021 | GPT-J 6B-class | base_continuation | Stronger pre-instruction behavior |
| 2022 | FLAN-T5 XL-class | instruction | Instruction-tuning transition |
| 2023 | Mistral 7B Instruct-class | chat | Early capable open chat |
| 2024 | Qwen2.5 7B Instruct-class | chat | Modern open instruction following |

Rules:

1. Cohort membership is frozen in `registry/cohort-local-v1.yaml`.
2. Every model is pinned to an exact repository revision and a documented license.
3. Locally converted or quantized artifacts are allowed only with recorded source and checksum.
4. Display years are strictly ascending and unique within the cohort.
5. Substitutions require a new cohort version and a decision-log entry. Never substitute silently.
6. An optional current-year laptop model may be added only as a separately labeled sixth endpoint after the five-model core is stable.

## Prompt rule

- Input is text only. English is the supported path for `local-v1`.
- Maximum **900 Unicode characters** (Python `len(str)`).
- The user’s raw prompt is preserved byte-for-byte in `raw-prompt.txt` and is never silently altered.
- A model receives a **visible** model-specific adapter only when required by its native interface (base continuation wrapper or documented chat/instruction template).
- No invisible helpfulness system prompt, chain-of-thought request, retrieval result, tool result, or model-specific performance enhancement.
- A prompt that exceeds a model limit fails visibly with `InputUnsupportedError`. `was_truncated` is always `false`.
- Non-English text is permitted with a warning; `local-v1` does not promise comparable multilingual behavior.

## Generation rule

Frozen generation profile `local-v1`:

```yaml
id: local-v1
max_new_tokens: 320
temperature: 0.7
top_p: 0.95
seed: 20260923
retries: 0
tools: disabled
network: disabled-after-download
```

Rules:

1. Values do not vary by prompt and are not tuned after examining a user’s output.
2. `retries` is always `0`. A failure is a result, not a reason to retry.
3. If an architecture cannot honor a field, record the limitation in `generation_effective` on the `ModelRun`.
4. Model downloads happen only via an explicit setup/preload command — never in response to a user prompt.

## Evaluation rule

`local-v1` has **no automatic LLM judge** and **no displayed 1–10 quality score**.

Stored evaluation fields are user-provided only:

| Field | Values |
|---|---|
| `usefulness` | `yes` \| `partly` \| `no` \| `unset` |
| `blind_rank` | integer or unset |
| `notes` | optional local text |
| `failure_tags` | zero or more of `incorrect`, `ignored_constraints`, `irrelevant`, `unsafe`, `incomplete`, `style`, `other` |

These are personal annotations, not scientific measurements. The UI must say so.

## Blind comparison rule

1. Generate a stable per-trip mapping from model IDs to labels A–E (seeded by trip id).
2. Hide model name and year while displaying complete outputs.
3. User assigns a strict rank or marks a tie/unranked result.
4. Ranking is saved to `annotations.json`.
5. Reveal the mapping only after an explicit user request.
6. Blind rank is one user’s one-trip preference — never imply statistical meaning.

## Artifact and privacy rule

- All trip content lives under `local-data/trips/<trip-id>/`.
- Manifest records `raw_prompt_sha256`; full text lives only in `raw-prompt.txt`.
- Writes are atomic (temp dir → validate manifest → rename).
- No raw prompt/output text in default application logs.
- `--debug-content` is development-only, off by default, and must warn before content logging.
- Streamlit binds to `127.0.0.1` only.
- No network client may be called during a trip.
- Delete-one deletes only the validated selected trip directory. Delete-all deletes only the validated `local-data/trips/` tree.

## Failure and cancellation rule

Statuses: `completed | failed | timed_out | unsupported | cancelled`.

- A failed, timed-out, unsupported, or cancelled model appears in the chronological timeline as such.
- Cancellation preserves completed results, marks remaining models `cancelled`/`unsupported` with a reason, and saves a valid partial manifest.
- Failures expose a safe `error_code` and user-readable `error_message`. Stack traces are never written into export bundles.

## Auditability rule

Every completed (or partial) trip must be reconstructable from its directory alone:

- `manifest.json` — schema version, trip id, timestamps, protocol/cohort/app versions, hardware summary, prompt hash, runs, annotations pointer.
- `raw-prompt.txt` — exact user input.
- `success-criterion.txt` — optional criterion (may be empty).
- `prepared-inputs/<model-id>.txt` — exact text sent to the checkpoint.
- `outputs/<model-id>.txt` — raw generated text (when completed).
- `annotations.json` — user usefulness / blind rank / notes / failure tags.

The audit drawer in the UI must show raw prompt, prepared input, adapter explanation, pinned source revision, local artifact checksum, generation profile, and effective runtime parameters.

## Claim boundary for generated content

Historical model output is not transformed to be safer or more polished. The UI includes a small warning that historical models can be incoherent, biased, or unsafe.
