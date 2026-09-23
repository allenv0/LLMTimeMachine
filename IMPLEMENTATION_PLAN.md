# LLM Time Machine — Local Demo Implementation Plan

## Status and instruction to implementers

**Status:** Planning complete; implementation has not started.

This document is the implementation specification for the **local-demo** stage of the LLM Time Machine. Do not build public-service features, paid API integrations, automatic LLM judging, or a universal progress graph under this plan. Those are deliberately deferred.

Before changing any locked decision below, create a new version of this plan and explain the rationale in the decision log. The credibility of the product depends on stable, inspectable methodology.

## 1. Product definition

### 1.1 Product statement

Build a private, local web application that accepts one text prompt, runs it through a small frozen cohort of historically representative open-weight language models, reveals the outputs in chronological order, and lets the user inspect exactly what each model received.

The local demo is meant to answer:

1. Does a user experience substantial model progress on prompts they personally care about?
2. Does exposing the model cohort, prompt adapters, and inference settings make the experience more trustworthy than a fixed benchmark page?
3. Can a self-contained demo be run locally without a paid model API or sending prompts off-device?

### 1.2 Truthful public-facing claim

Use this wording in the app and README:

> A laptop-compatible, auditable sample of LLM history. It is not a verified record of the best model in every year.

The demo must never claim that it runs the historical frontier model for every year. The selected checkpoints are constrained by local deployability, licensing, and reproducibility.

### 1.3 Explicit non-goals

Do **not** implement any of the following:

- Public hosting, accounts, authentication, payments, or multi-user concurrency.
- Any paid model API or remote inference provider.
- User analytics, telemetry, cloud logging, email, or prompt sharing.
- Automatic LLM-as-a-judge scoring, numeric quality curves, or global benchmark overlays.
- A public prompt corpus, data collection, or model-training use of user prompts.
- Tools, web browsing, RAG, file upload, code execution, or multimodal input.
- A claim of uniform fairness across base, instruction-tuned, and chat models.
- Silent model substitution, hidden prompt rewriting, or automatic retries after weak answers.

## 2. Scope and success criteria

### 2.1 In-scope experience

1. A local browser UI runs on `127.0.0.1` only.
2. A user enters a short English text prompt and optionally a success criterion.
3. The application runs a frozen five-model cohort sequentially to reduce memory pressure.
4. It reveals outputs as an ordered timeline from the oldest to newest model.
5. It offers a blind A–E comparison view, personal ratings, and local notes.
6. Each output includes an audit view showing raw prompt, exact prepared input, model information, generation settings, and limitations.
7. Each completed trip is stored locally and can be exported as a ZIP or JSON bundle.
8. The user can delete one trip or all local records.

### 2.2 Definition of done

The local demo is complete only when all conditions below are met.

- It functions with no paid API key and no remote inference request.
- After checkpoints are downloaded, a full trip works with networking disabled.
- A new user can start it with one documented command.
- The standard cohort completes on a documented supported hardware profile, or unsupported models visibly report failure.
- The app never silently truncates prompts, changes the cohort, changes sampling settings, or retries a model.
- Every result has a durable run manifest with the model source revision, local artifact checksum, adapter version, runtime settings, and run status.
- A failed, timed-out, or unsupported model is displayed as such in the chronological timeline.
- Exact prepared model inputs can be inspected and exported.
- An automated test suite covers registry validation, adapter rendering, manifest serialization, local storage, deletion, and UI behavior using fake runners.
- A manual real-model test suite has been completed and recorded in `docs/validation.md`.

### 2.3 Acceptance metrics for the product decision

These metrics are for deciding whether to advance to an alpha, not for marketing the demo.

- At least five non-builders complete a trip using a prompt of their own choosing.
- At least three voluntarily run a second prompt or inspect the audit drawer.
- Users can explain the cohort limitation after using the app.
- Total time from clicking Run to final result is measured for every hardware profile.
- The app remains stable across ten consecutive local trips after model weights are cached.

## 3. Locked methodological protocol

Create `PROTOCOL.md` before any model response is shown to a tester. It must be versioned. The first version is `local-v1`.

### 3.1 Cohort rule

The initial cohort is a **laptop-compatible representative cohort**, not an annual frontier cohort. It should contain these eras, subject to final license and runtime validation:

| Display year | Target class | Mode | Purpose |
|---|---|---|---|
| 2019 | GPT-2 XL-class checkpoint | Base continuation | Pre-chat behavior |
| 2021 | GPT-J 6B-class checkpoint | Base continuation | Stronger pre-instruction behavior |
| 2022 | FLAN-T5 XL-class checkpoint | Instruction tuned | Instruction-tuning transition |
| 2023 | Mistral 7B Instruct-class checkpoint | Chat/instruction | Early capable open chat |
| 2024 | Qwen2.5 7B Instruct-class checkpoint | Chat/instruction | Modern open instruction following |

An optional current-year laptop model may be added only as a separately labeled sixth endpoint after the five-model core is stable.

Every final selection must be pinned to an exact repository revision and documented license. A locally converted or quantized artifact is allowed only if its source and checksum are recorded.

### 3.2 Prompt rule

- Input is text only, English in the initial supported path.
- The app accepts at most 900 Unicode characters in `local-v1`.
- The user’s raw prompt is preserved exactly.
- A model receives a visible model-specific adapter only when required by its native interface.
- No model receives an invisible helpfulness system prompt, chain-of-thought request, retrieval result, tool result, or model-specific performance enhancement.
- A prompt that exceeds a model limit must fail visibly; it must not be silently shortened.

### 3.3 Generation rule

Before testing with external users, select one generation profile and freeze it in the cohort registry. Example fields:

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

The concrete values may be changed before the first protocol release if compatibility requires it. They must not vary by prompt or be tuned after examining a user’s output. If an architecture cannot honor a field, record that fact in its `generation_effective` metadata.

### 3.4 Evaluation rule

`local-v1` has no automatic LLM judge and no displayed 1–10 quality score.

The only stored evaluation fields are user-provided:

- `usefulness`: `yes | partly | no | unset`
- `blind_rank`: integer or unset
- `notes`: optional local text
- `failure_tags`: zero or more of `incorrect`, `ignored_constraints`, `irrelevant`, `unsafe`, `incomplete`, `style`, `other`

The app must make it clear these are personal annotations, not scientific measurements.

## 4. Technical architecture

### 4.1 Architecture decisions

- **Language:** Python 3.11.
- **Dependency management:** `uv` with a committed lockfile.
- **UI:** Streamlit, selected for fast local iteration and simple local serving.
- **Validation/models:** Pydantic data models plus YAML cohort files.
- **Storage:** local filesystem; no database in this stage.
- **Legacy inference:** Hugging Face Transformers with `trust_remote_code=false`.
- **Quantized inference:** an adapter around a local runtime such as `llama.cpp`; this is optional until a final model needs it.
- **Testing:** `pytest`; Streamlit behavior is isolated behind service functions and tested with fake runners rather than live weights.

The application must never bind to a public interface. The documented launch command must specify `--server.address 127.0.0.1`.

### 4.2 Directory layout

```text
.
├── IMPLEMENTATION_PLAN.md
├── PROTOCOL.md
├── README.md
├── pyproject.toml
├── uv.lock
├── app.py
├── registry/
│   ├── cohort-local-v1.yaml
│   └── adapters/
│       ├── continuation-v1.txt
│       └── adapter-notes.md
├── src/time_machine/
│   ├── __init__.py
│   ├── config.py
│   ├── domain.py
│   ├── registry.py
│   ├── preflight.py
│   ├── trip_service.py
│   ├── artifact_store.py
│   ├── export_service.py
│   ├── prompt_adapters.py
│   ├── runners/
│   │   ├── base.py
│   │   ├── fake.py
│   │   ├── transformers_runner.py
│   │   └── local_quantized_runner.py
│   └── ui/
│       ├── landing.py
│       ├── prompt_form.py
│       ├── progress.py
│       ├── results.py
│       ├── blind_compare.py
│       └── local_data.py
├── prompts/
│   └── starter_prompts.jsonl
├── docs/
│   ├── model-sources.md
│   ├── hardware-profiles.md
│   ├── validation.md
│   └── decision-log.md
├── tests/
│   ├── fixtures/
│   ├── test_registry.py
│   ├── test_adapters.py
│   ├── test_trip_service.py
│   ├── test_artifact_store.py
│   ├── test_export_service.py
│   └── test_preflight.py
└── local-data/                 # gitignored; all prompts/results live here
```

`local-data/` must be gitignored. The implementation must not put user prompt content into application logs, exceptions, test fixtures, source control, or telemetry.

### 4.3 Component responsibilities

| Component | Responsibility | Must not do |
|---|---|---|
| `registry.py` | Load/validate pinned cohort specifications | Download arbitrary models based on user input |
| `prompt_adapters.py` | Render and explain exact model-ready inputs | Add hidden performance prompts |
| `runners/*` | Load one local model, generate one output, report runtime data | Alter cohort metadata or write UI state |
| `trip_service.py` | Orchestrate a sequential trip and produce immutable artifacts | Judge output quality |
| `artifact_store.py` | Atomically write/read/delete local trip artifacts | Send content off device |
| `export_service.py` | Create portable ZIP/JSON exports | Include unrelated local trips |
| `preflight.py` | Assess local disk/RAM/runtime availability | Choose a different model silently |
| `ui/*` | Render state and collect user annotations | Access a runner directly |

## 5. Core data contracts

Use Pydantic models for all persisted structures. Persist their JSON representation alongside any human-readable files.

### 5.1 `ModelSpec`

```yaml
id: string
display_year: integer
display_name: string
release_date: ISO-8601 date
mode: base_continuation | instruction | chat
source:
  repository: string
  revision: string
  artifact_filename: string
  sha256: string
license_url: string
backend: transformers | local_quantized
precision: string
adapter_id: string
adapter_version: string
input_limit_chars: integer
generation_profile_id: string
limitations: [string]
hardware_profile: lite | standard | high
```

Validation requirements:

- Model identifiers, years, and display names are unique in a cohort.
- Display years are strictly ascending.
- Every selected model has a repository, revision, license URL, checksum, adapter, and at least one limitation.
- The configured adapter is compatible with the model mode.
- `input_limit_chars` is positive and no larger than the protocol maximum.

### 5.2 `PreparedInput`

```json
{
  "model_id": "gpt2-xl-2019",
  "raw_prompt": "…",
  "adapter_id": "continuation-v1",
  "adapter_version": "1",
  "prepared_text": "Task: …\n\nAnswer:",
  "was_truncated": false,
  "preparation_notes": ["Base model receives a continuation-style wrapper."]
}
```

`was_truncated` must always be `false` in `local-v1`. A too-long input returns a typed `InputUnsupportedError` instead.

### 5.3 `GenerationConfig`

```json
{
  "profile_id": "local-v1",
  "seed": 20260923,
  "temperature": 0.7,
  "top_p": 0.95,
  "max_new_tokens": 320,
  "tools_enabled": false,
  "network_enabled": false,
  "retries": 0
}
```

### 5.4 `ModelRun`

```json
{
  "model_id": "gpt2-xl-2019",
  "status": "completed | failed | timed_out | unsupported",
  "started_at": "…",
  "finished_at": "…",
  "load_seconds": 0.0,
  "generation_seconds": 0.0,
  "prepared_input_path": "prepared-inputs/gpt2-xl-2019.txt",
  "output_path": "outputs/gpt2-xl-2019.txt",
  "error_code": null,
  "error_message": null,
  "runtime": {
    "backend": "…",
    "backend_version": "…",
    "device": "…",
    "effective_generation": {}
  }
}
```

Failures must have a safe, non-secret `error_code` and user-readable message. Do not save stack traces in exported bundles.

### 5.5 `TripManifest`

```json
{
  "schema_version": "1",
  "trip_id": "uuid",
  "created_at": "ISO-8601 timestamp",
  "protocol_version": "local-v1",
  "cohort_id": "local-v1",
  "app_version": "git commit or package version",
  "hardware_summary": {},
  "raw_prompt_sha256": "…",
  "optional_success_criterion": "…",
  "runs": [],
  "user_annotations": {}
}
```

The full raw prompt lives in `raw-prompt.txt` inside the individual local trip directory. The manifest records only its SHA-256 hash so it remains inspectable without duplicating sensitive content.

### 5.6 Local artifact layout

```text
local-data/trips/<trip-id>/
├── manifest.json
├── raw-prompt.txt
├── success-criterion.txt
├── prepared-inputs/
│   └── <model-id>.txt
├── outputs/
│   └── <model-id>.txt
├── annotations.json
└── export/                      # temporary and excluded from exports
```

Writes must be atomic: write to a temporary directory, validate the manifest, then rename into the completed trip directory.

## 6. UI specification

### 6.1 Landing and disclosure

The landing page contains a compact disclosure before the prompt field:

1. “Runs locally: your prompt is not sent to a model API.”
2. “This is a laptop-compatible historical cohort, not verified annual frontier models.”
3. “Older models use visible historical input formats because they predate chat interfaces.”

Include a link/button to open the full protocol and cohort registry.

### 6.2 Prompt form

Inputs:

- Required text prompt, with live character counter.
- Optional success criterion: “What would a good answer accomplish?”
- Starter prompt selector with five non-sensitive examples.
- Read-only display of the selected cohort and the generation profile.
- “Run private trip” button.

Validation:

- Reject empty/whitespace-only prompt.
- Reject input over the protocol limit before a runner is started.
- Warn, but permit, non-English text: `local-v1` does not promise comparable multilingual behavior.
- Disable Run while a trip is in progress.

### 6.3 Progress view

Render one row per cohort model in chronological order:

```text
2019  GPT-2 XL       waiting | loading | generating | complete | failed
2021  GPT-J 6B       waiting | loading | generating | complete | failed
…
```

Only one runner is active at a time. Update status after model load begins, when generation begins, and when artifacts are written. A result is revealed as soon as its model run finishes.

The user can cancel a trip between model runs. Cancellation must preserve completed results, mark remaining models `unsupported` with a cancellation reason, and save a valid partial manifest.

### 6.4 Result cards

Each card must show:

- Display year and model name.
- Base / instruction / chat badge.
- Result status.
- Full generated output or a clear failure card.
- Model limitations.
- Load and generation duration.
- Personal usefulness controls: Yes / Partly / No.
- Failure tags and notes.
- Expandable audit view.

The audit view must show:

- Raw user prompt.
- Exact prepared input sent to the checkpoint.
- Adapter explanation.
- Pinned source revision and local artifact checksum.
- Generation profile and effective runtime parameters.

### 6.5 Blind comparison

Implement a separate toggle, not the default presentation:

1. Generate a stable per-trip random mapping from model IDs to labels A–E.
2. Hide model name and year while displaying complete outputs.
3. Let the user assign a strict rank or mark a tie/unranked result.
4. Save the ranking to `annotations.json`.
5. Reveal the mapping only after the user explicitly requests it.

Do not imply the blind rank is statistically meaningful. It is a user’s one-trip preference.

### 6.6 Local data controls

- “Export this trip” creates a ZIP containing that trip only.
- “Delete this trip” requires confirmation and deletes the exact selected directory.
- “Delete all local trips” requires typed confirmation and deletes only the validated `local-data/trips/` directory.
- Display the exact local data path and state that files are local.

## 7. Model runners

### 7.1 Runner interface

Define one abstract interface. The UI must not depend on an inference backend.

```python
class ModelRunner(Protocol):
    def preflight(self, spec: ModelSpec) -> RunnerAvailability: ...
    def prepare(self, raw_prompt: str, spec: ModelSpec) -> PreparedInput: ...
    def generate(
        self,
        prepared: PreparedInput,
        spec: ModelSpec,
        config: GenerationConfig,
    ) -> GenerationResult: ...
    def unload(self) -> None: ...
```

`unload()` must be called after each model so the next checkpoint gets the best chance to fit in memory.

### 7.2 Transformers runner

Use for legacy models and encoder-decoder instruction checkpoints.

Requirements:

- Pin package and model revisions.
- Default `trust_remote_code=false`.
- Disable any networking after an explicit local cache check.
- Report device, dtype, source revision, and effective parameters.
- Distinguish load failure, OOM, generation failure, and timeout.
- Never retain model references after `unload()`.

### 7.3 Quantized local runner

Use only when required to make a selected local model practical.

Requirements:

- Quantization format and conversion provenance are registry fields.
- The exact source artifact checksum is verified before a run.
- The runner exposes the raw prompt string supplied by the adapter; it must not introduce a second opaque chat template.
- Its version and inference parameters are included in `ModelRun.runtime`.

### 7.4 Fake runner

Implement first. It returns deterministic fixture responses and optional controlled errors. It supports:

- success
- load failure
- generation timeout
- malformed output
- cancellation after a selected model

Use it for all UI and storage development until the runner contract is stable.

## 8. Local privacy and safety requirements

### 8.1 Privacy

- Bind Streamlit to loopback only.
- No network client may be called during a trip.
- No telemetry SDKs, hosted error reporting, analytics, or remote fonts.
- Do not log raw prompt/output text to stdout by default.
- Add a `--debug-content` development-only option that is off by default and visibly warns before content logging.
- Model downloads happen only via an explicit setup/preload command, never in response to a user prompt.

### 8.2 Supply chain safety

- Use pinned revisions for all model downloads.
- Store and validate expected checksums when available.
- Reject unpinned model specs.
- Do not execute repository-provided custom model code.
- Document each checkpoint’s license in `docs/model-sources.md`.

### 8.3 Generated content

The demo does not transform historical output to make it safer or more polished. It should include a small warning that historical models can be incoherent, biased, or unsafe.

Do not create a public-sharing feature. Local deletion and export are sufficient for this stage.

## 9. Hardware preflight

Create a preflight command and UI panel that reports:

- Operating system and architecture.
- Python/runtime versions.
- CPU memory or unified memory when detectable.
- CUDA/Metal device name and available memory when detectable.
- Free disk space in the model cache and `local-data` locations.
- Which cohort models are available, missing, or likely unsupported.

Document hardware profiles in `docs/hardware-profiles.md`:

| Profile | Intended capability | Expected behavior |
|---|---|---|
| Lite | 16 GB unified memory or approximately 12 GB VRAM | Smaller substitute cohort; clear limitation banner |
| Standard | 32 GB unified memory or approximately 24 GB VRAM | Five-model local cohort, likely quantized for 7B models |
| High | 64 GB unified memory or approximately 48 GB VRAM | Larger/less-quantized eligible cohort |

The preflight can recommend a profile, but it cannot mutate the cohort selection automatically.

## 10. Starter prompts

Include a small `prompts/starter_prompts.jsonl` file. These are onboarding examples, not evaluation benchmarks. Each must be original, short, safe, and include a category.

Use one prompt for each category:

- constrained creative writing
- debugging/explanation without code execution
- logic or wordplay
- structured extraction from noisy text
- analytical planning or argument

The UI must explain that the user’s own unusual prompt is more informative than any starter prompt.

## 11. Testing and validation

### 11.1 Unit tests

Implement before real inference integration.

- Registry rejects missing revisions, duplicate years, invalid adapters, and missing license/checksum fields.
- All adapters preserve the raw prompt and generate expected model-ready text.
- Input over the protocol limit yields a typed visible error and no `PreparedInput` with truncation.
- Generation configuration remains unchanged across every model run unless a capability exception is declared.
- A trip manifest validates with complete, failed, timed-out, cancelled, and partial cohorts.
- Atomic writes leave no corrupt completed trip after a simulated interruption.
- Export contains only the selected trip and excludes temporary files.
- Delete-one and delete-all operations are constrained to validated local trip paths.
- Blind-label mapping is stable for a trip and differs across distinct trips.

### 11.2 UI/service integration tests

Use the fake runner to cover:

- Empty prompt and over-limit prompt validation.
- Progress-state transitions.
- Chronological card ordering.
- Failure card display.
- Audit drawer content.
- Cancellation handling.
- Annotation persistence.
- Export creation.
- Deletion confirmation behavior.

### 11.3 Manual real-model validation

Record all outcomes in `docs/validation.md`.

For every real cohort model:

1. Verify its source revision, license, and local checksum.
2. Run a short prompt and verify the audit input exactly matches the runner’s input.
3. Measure cold load time, warm load time, generation time, peak memory where available, and output length.
4. Run the same prompt twice with the frozen seed and record whether the backend is deterministic.
5. Verify `unload()` frees enough memory to load the next model.
6. Test an intentional failure and confirm the app preserves the partial trip.

For the complete cohort:

1. Test with network disabled after checkpoints are cached.
2. Run five distinct prompts including one where progress is not dramatic.
3. Run ten consecutive trips with no restart.
4. Verify delete/export behavior on a real trip.
5. Ask at least one independent reviewer to trace a response back through the audit drawer and manifest.

### 11.4 Performance targets

Targets must be reported by hardware profile, not promised universally.

- First visible model status: under 10 seconds after clicking Run.
- Local input validation: immediate.
- No UI freeze during a generation.
- Full standard-cohort trip: measure and publish actual timing; aim for a usable single-digit number of minutes.
- Model memory is released between sequential runs.

If the complete standard cohort exceeds the usability target, create a visible “quick three-era tour” rather than hiding the delay or reducing output quality silently.

## 12. Ordered implementation tasks

Complete phases in order. Do not start a later phase before its gate passes.

### Phase 0 — Repository and protocol

1. Create the Python project with pinned dependencies and test tooling.
2. Add `.gitignore` covering local models, local prompts/results, exports, caches, and environment files.
3. Write `PROTOCOL.md`, `docs/decision-log.md`, and `docs/model-sources.md`.
4. Create `registry/cohort-local-v1.yaml` with placeholder entries only after each entry has a pinned source/revision/license.
5. Write registry validation tests.

**Gate:** `pytest` passes and an invalid cohort file fails with helpful errors.

### Phase 1 — Domain and local artifacts

1. Implement domain models for `ModelSpec`, `PreparedInput`, `GenerationConfig`, `ModelRun`, `TripManifest`, and annotations.
2. Implement atomic trip artifact creation, read, export, delete-one, and delete-all.
3. Implement a fake runner and deterministic fixture outputs.
4. Test partial, failed, cancelled, and complete trip persistence.

**Gate:** A complete fake trip can be exported, reloaded, annotated, and deleted without any model dependency.

### Phase 2 — Prompt adapters and preflight

1. Implement continuation, instruction, and chat-template adapters as explicit versioned components.
2. Add tests that render exact expected strings for each adapter.
3. Implement hardware/disk/runtime preflight and profile reporting.
4. Add a preload/setup command that downloads only registry-pinned artifacts.
5. Verify no model download is triggered by a user-submitted prompt.

**Gate:** An implementer can inspect exact prepared input with the fake runner and can see why each adapter exists.

### Phase 3 — Local UI with fake runner

1. Implement the landing disclosures and protocol/registry links.
2. Implement prompt form, starter prompts, validation, and cohort display.
3. Implement sequential progress view and cancellation.
4. Implement result cards, audit drawers, annotations, blind comparison, local export, and deletion controls.
5. Bind the app to loopback only in documented launch instructions.

**Gate:** A nontechnical reviewer can complete a fake trip, inspect the input to every model, rank results blindly, export it, and delete it.

### Phase 4 — Real-model integration, one model at a time

1. Implement and validate the first legacy runner/checkpoint.
2. Implement and validate the first modern local runner/checkpoint.
3. Add remaining cohort models only after each has source, checksum, adapter, and preflight coverage.
4. Ensure every runner produces `ModelRun` telemetry and reliably unloads.
5. Record every validation result; do not conceal incompatible models.

**Gate:** All selected models either complete a real test trip or visibly fail with an actionable documented limitation.

### Phase 5 — Offline/privacy/reliability validation

1. Run after model caching with network disabled.
2. Confirm no raw content appears in default logs.
3. Run the manual real-model validation matrix.
4. Execute ten consecutive trips on the target hardware profile.
5. Prepare a concise demo script and limitation disclosure.

**Gate:** The demo meets the definition of done and is ready for a small private audience.

## 13. Risks and required responses

| Risk | Detection | Required response |
|---|---|---|
| A historical model cannot run locally | Preflight or OOM | Mark unsupported; replace only through a new cohort version |
| Modern model dominates due to a hidden template | Audit test | Remove hidden helper text; disclose native template |
| Base models appear nonsensical | Expected historical behavior | Preserve output; explain base-continuation mode |
| Full trip is too slow | Timings exceed usability target | Offer a visible quick cohort; do not silently change standard cohort |
| Quantization changes outputs materially | Validation sampling | Record format; use a clearer/lighter cohort if needed |
| Model source requires custom code | Source review | Reject it for the local demo |
| User enters private material | Product behavior | Keep all data local; no default content logs or sharing |
| Unsafe historical output | Manual testing | Warn the user; do not create public sharing in this phase |
| A model fails mid-trip | Injected fake failure / real test | Persist partial artifact and display a failure card |
| User assumes this is a frontier benchmark | Usability review | Strengthen disclosure and protocol link; do not overclaim |

## 14. Deferred work and advancement criteria

Only consider the hosted alpha after the local demo has passed the validation gate and demonstrates user value.

Deferred alpha work includes:

- Larger model cohort on rented GPUs.
- Concurrent job orchestration and rate limiting.
- Independent blinded evaluator(s) calibrated against human judgments.
- Task-family reference suites and uncertainty-aware comparison views.
- Stronger prompt retention controls, encryption, accounts, and consent flows.
- A formal advisory process for annual cohort selection.

The local demo must not be distorted merely to make these future features easier. Its purpose is to validate the core human experience first.

## 15. Decision log template

Append changes to `docs/decision-log.md` in this format:

```markdown
## YYYY-MM-DD — Short decision title

**Decision:**

**Alternatives considered:**

**Evidence:**

**Impact on protocol/cohort:**

**Owner:**
```

Examples requiring a decision-log entry: changing a checkpoint, using a different quantization, changing a prompt adapter, altering the generation profile, changing the prompt limit, or adding any network dependency.
