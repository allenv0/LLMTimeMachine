# Decision log

Append-only record of methodology and cohort changes. Format follows the implementation plan.

## 2026-09-23 — Initial local-v1 protocol and cohort freeze

**Decision:**

Freeze protocol `local-v1` and cohort `local-v1` with five laptop-representative checkpoints: GPT-2 XL (2019), GPT-J 6B (2021), FLAN-T5 XL (2022), Mistral-7B-Instruct-v0.2 (2023), Qwen2.5-7B-Instruct (2024). Generation profile `local-v1` uses max_new_tokens=320, temperature=0.7, top_p=0.95, seed=20260923, retries=0.

**Alternatives considered:**

- Annual frontier cohort including closed API snapshots (rejected: not locally deployable, not reproducible offline).
- Fewer than five eras (rejected: collapses the instruction-tuning and chat transitions).
- Including a 2015 char-RNN / 2018 GPT-1 (deferred: weak local artifact story and poor prompt interface comparability).

**Evidence:**

Implementation plan §3.1 laptop-compatible representative cohort; open-weight checkpoints with stable Hugging Face revisions and permissive licenses.

**Impact on protocol/cohort:**

Defines the frozen cohort and generation profile. Substitutions require a new cohort version.

**Owner:**

Local demo implementation

## 2026-09-23 — Lite substitute cohort for disk/RAM-constrained hosts

**Decision:**

Add `registry/cohort-lite-v1.yaml` (GPT-2 small 2019, GPT-2 Medium 2021, FLAN-T5 Base 2022) as the hardware-profile **lite** substitute. It is labeled `lite-v1`, not `local-v1`. UI must show a limitation banner when this cohort is active. The standard five-model cohort remains unchanged.

**Alternatives considered:**

- Download the standard cohort anyway (rejected: ~15–50 GB of weights vs ~4.6 GB free disk on the validation host).
- Silent substitution of smaller checkpoints in `local-v1` (forbidden by protocol).
- Include FLAN-T5 Large (~3.1 GB) as well (deferred: would leave less than ~1 GB free).

**Evidence:**

Host preflight: 16 GB unified memory (lite), ~4.6 GB free disk. GPT-2 XL alone is ~6.4 GB.

**Impact on protocol/cohort:**

Adds an explicitly labeled substitute cohort only. Does not change `local-v1` generation profile or evaluation rules.

**Owner:**

Local demo implementation

## 2026-09-23 — Five-era cohort (16 GB RAM / ~25 GB disk)

**Decision:**

Add `registry/cohort-five-era-v1.yaml`: GPT-2 (2019), GPT-2 Medium (2021), FLAN-T5 Large (2022), Mistral-7B-Instruct-v0.2 Q4_K_M GGUF (2023), Qwen2.5-7B-Instruct Q4_K_M GGUF (2024). Backend: transformers for 2019–2022, local_quantized (llama.cpp) for 2023–2024. App defaults to this cohort when present.

**Alternatives considered:**

- Stopping at the 3-model lite cohort (rejected: no modern endpoint, fails idea.md “eventually solved”).
- Full FP16/FP32 standard cohort (rejected: disk and 16 GB RAM).
- Only one modern model (rejected: loses the 2023→2024 chat progression).

**Evidence:**

User raised disk budget to 25 GB. Q4_K_M GGUF 7B runs sequentially on 16 GB unified memory. Measured trip on “Do a super ultra deep analysis into the apple's design system” shows clear base→instruction→chat→modern progression.

**Impact on protocol/cohort:**

New cohort id `five-era-v1` under protocol `local-v1`. Modern slots are quantized (recorded in limitations). Not a claim of annual frontier coverage.

**Owner:**

Local demo implementation

## 2026-09-23 — Checksum policy

**Decision:**

Each `ModelSpec.source.sha256` is the expected SHA-256 of the primary weight artifact named by `artifact_filename`. Preload verifies it after download. Registry validation accepts a 64-char hex digest or the sentinel `record-at-preload`, which means: record the measured digest into `local-cache-index.json` on first successful download and fail closed on later mismatch.

**Alternatives considered:**

- Tree hash of all repo files (harder to explain in the audit drawer).
- No checksums, revision pin only (weaker supply-chain guarantee).

**Evidence:**

Implementation plan §8.2 store and validate expected checksums when available; §1 decision log examples include quantization/provenance changes.

**Impact on protocol/cohort:**

Strengthens artifact integrity without blocking first-time preload.

**Owner:**

Local demo implementation

## 2026-09-23 — Seam refactor for composability

**Decision:**

Extract seams before next features: incremental `TripWriter`, `RunnerFactory` (verify-before-generate), `TripController` (UI never touches runners), `CohortCatalog` + `registry/adapters/catalog.yaml`, and `EvaluationPort`/`NullEvaluator`. `TripService` remains a thin wrapper.

**Alternatives considered:**

- Keep monolithic trip + app.py and bolt features on (rejected: crash loses partial trips; alpha judge/jobs would tangle further).
- Full rewrite to a job queue/DB (rejected: plan forbids DB and multi-user in local-v1).

**Evidence:**

Plan §4.3 UI must not access runners; §7.3 checksum verify before run; idea.md future judge/curves must stay out of trip orchestration.

**Impact on protocol/cohort:**

No protocol change. Adapter templates now live in `registry/adapters/catalog.yaml` (same visible semantics).

**Owner:**

Local demo implementation

## 2026-09-23 — Quick three-era tour + progress arc

**Decision:**

Add a one-click **Quick three-era tour** beside **Run full trip**. The tour runs only three models: oldest base → a middle instruction model → newest chat (`CohortCatalog.quick_tour_ids` / `quick_tour_models`). Results open with a **progress arc** panel (Base → Instruction → Chat) showing one column per stop, then the full audit cards.

**Alternatives considered:**

- Oldest / middle / newest only (rejected as sole rule: can miss mode coverage when eras cluster).
- Quality-curve UI with numeric scores first (rejected for now: needs an honest `EvaluationPort` metric; local-v1 forbids LLM-judge).
- Infer tour from `len(runs)==3` only (rejected: full subset trips would mislabel).

**Evidence:**

`idea.md` progress arc (base → instruction → chat). `CohortCatalog.quick_tour_ids` already existed unused after the seam refactor. `TripController.run_trip(models=...)` already supported subsets.

**Impact on protocol/cohort:**

No protocol change. Tour is a view/scope over the same frozen cohort and generation profile. Selection prefers mode coverage with full year span (not a silent model swap).

**Owner:**

Local demo implementation

## 2026-09-23 — Deep test + real re-run evidence (pelican tour, grandma full)

**Decision:**

Keep `local-v1` scope. Re-ran real trips after the quick-tour feature: `tour-pelican-idea` (idea.md pelican motif, 3-era) and `full-grandma-kettle` (private unpublished clue, 5-era). Both complete with reconstructable audit dirs. Deepened `tests/test_deep_protocol.py` for protocol invariants and idea.md seams.

**Alternatives considered:**

- Pull LLM-judge quality curve forward to match idea.md ranking paragraph (rejected: PROTOCOL local-v1 forbids it; would break audit honesty).
- Claim “best of year” coverage (rejected: cohort is laptop-compatible stand-ins; truthful claim required).

**Evidence:**

- Tour arc on pelican SVG: 2019 wanders, 2022 describes in prose, 2024 emits real SVG — the idea.md “feel progress on your own weird prompt” moment.
- Private crossword: 2023/2024 hallucinate confident wrong answers (`whist` / `BOI`) — progress is honesty/coherence, not omniscience on unpublished facts.
- 93 tests green; manifest hash matches raw prompt; prepared inputs exact; no `{prompt}` leaks.

**Impact on protocol/cohort:**

None. Evidence only.

**Owner:**

Local demo implementation

## 2026-09-23 — Phase A: diary, ordinal curves, decade walk

**Decision:**

Implement Track A from `docs/plan-close-idea-gaps.md` under protocol `local-v1`: prompt diary (pre-register, link trips, first-solved, reflections), explicit −2..+2 ordinal ratings (usefulness can derive as fallback), personal progress curves with honest gaps (never zero-filled), local portfolio band at n≥5, and a stepwise decade walk with reflection pauses. No LLM-judge.

**Alternatives considered:**

- Jump to `local-v2-eval` judge curves first (deferred: Track B after A).
- Fold blind rank into the quality curve (rejected: rank is preference among candidates).
- Calendar-time longitudinal study (rejected for local: decade walk is labeled simulation).

**Evidence:**

`docs/plan-close-idea-gaps.md` Phase A. `tests/test_phase_a_diary_curves.py`. UI tabs: Progress curve, Diary, Decade walk.

**Impact on protocol/cohort:**

None. Track A stays `local-v1`. `UserAnnotations.ordinal` is additive.

**Owner:**

Local demo implementation

## 2026-09-23 — Phase B: local-v2-eval judge (opt-in)

**Decision:**

Add Track B estimated quality under `PROTOCOL-local-v2-eval.md`: versioned `registry/judges/rubric-v1.yaml`, pinned judge `judge-v1.yaml` (FLAN-T5 Large in judge role — not the status-quo Qwen slot), `JudgeService.score_trip` only on explicit UI action, full judge I/O audit under `local-data/judge/`, experimental banner on every estimate, refuse-to-score (`UNSCORED`) for unverifiable private facts. `TripController` never auto-scores.

**Alternatives considered:**

- Auto-score every trip (rejected: silent judge violates local-v1 trust).
- Use Qwen 2024 as judge (rejected: status-quo slot should not grade “today”).
- Merge judge scores into Track A ordinal curve (rejected: keep human vs estimate separate).

**Evidence:**

`tests/test_phase_b_judge.py` (parse, refuse, explicit-only, no judge artifacts after plain trip). Export JSON includes judge bundle only when scores exist.

**Impact on protocol/cohort:**

`local-v1` unchanged. `local-v2-eval` is an optional appendix. Judge is a role over an existing checkpoint, not a new historical year slot.

**Owner:**

Local demo implementation

## 2026-09-23 — Deep validation pass (A+B) + fixes

**Decision:**

Full deep test after Phase A/B: 111 unit tests, 63 protocol/idea.md invariants, end-to-end chain (trip→curve→diary→judge→export→delete), real-model tour + real FLAN judge. Two fixes from findings: (1) diary index preview capped at 40 chars so long private prompts cannot appear whole in `index.json`; (2) judge parser accepts bare `UNSCORED` (FLAN often omits the colon/reason).

**Alternatives considered:**

- Leave diary preview at 80 chars (rejected: long private prompts would leak into index).
- Coerce bare `UNSCORED` into a numeric score (rejected: refuse is the correct Track B behavior).

**Evidence:**

Real trip `deep-real-tour-final` complete in 32s; judge returned bare `UNSCORED` and is now recorded honestly as unscored with reason. Suite green after fixes.

**Impact on protocol/cohort:**

None.

**Owner:**

Local demo implementation

## 2026-09-23 — Wave 1 freeze: local-v3-longitudinal + decade-v0 + rubric v2

**Decision:**

Freeze Wave 1 from `docs/plan-full-idea.md` for individual delivery (WS1 partial + WS2 B1 + WS4 local):

1. Write `PROTOCOL-local-v3-longitudinal.md` (diary re-run semantics, versioned diary index, offline curve packs).
2. Ship `registry/cohort-decade-v0.yaml` with **visible holes** (2015/2016/2018/2020/2025/2026), labeled `substitute` slots (`stands_for`), and a **status-quo** endpoint (not a fake year).
3. Upgrade judge to **rubric v2 JSON contract** + dedicated pin `judge-v2.yaml` + cache keyed by `(judge, rubric, judge_prompt_sha256)`.
4. Diary re-run (explicit tour/full) + first-solved timeline across entries.
5. Validation matrix filled from real hardware evidence on this host.

**Alternatives considered:**

- Skip holes and keep only five running models (rejected: idea.md year-by-year fidelity requires empty nodes with reasons).
- Fake a 2020 GPT-3 slot with a local stand-in (rejected: silent substitution).
- Auto re-run diary on every app start (rejected: local-v3 forbids silent re-run).
- Free-text judge forever (rejected: JSON contract cuts parse failures; refuse still preferred over invent).

**Evidence:**

`docs/plan-full-idea.md` §4 Wave 1 and §9 immediate actions. Gate W1: non-builder completes trip, rates, sees human + estimated curves, marks first-solve, re-runs diary after a new year slot appears.

**Impact on protocol/cohort:**

`local-v1` frozen and unchanged for trip generation. `local-v3-longitudinal` is an additive appendix. New cohort id `decade-v0`. Judge track stays `local-v2-eval` with new `judge-rubric-v2` / `judge-flan-v2` (scores not comparable across rubric versions).

**Owner:**

Local demo implementation

## 2026-09-23 — Wave 2+3: packs, chat playground, FUTURE quarantine

**Decision:**

Complete the individual-delivery path (WS1–WS6) under `local-v3-longitudinal` + existing `local-v2-eval`:

1. **WS3 pack overlay:** `curves_pack.py` + `curves-pack-v1` schema, version gate, min-n band, demonstration pack (32 synthetic curves, labeled `pack_kind: demonstration`), compare-pack export.
2. **WS2 calibration:** `judge_calibration.py` gold set + bias report (never rewrites scores).
3. **WS5 playground:** `chat_session.py` multi-turn with visible `continuation-transcript-v1` / `instruction-flat-transcript-v1` / native chat multi adapters; per-turn audit; export.
4. **WS6 FUTURE:** `future_ensemble.py` best-of-n across members × seeds; off by default; quarantined; cannot mark first-solved without opt-in.

**Alternatives considered:**

- Claim the demonstration pack is empirical global progress (rejected: dishonest density).
- Wrap GPT-2 in modern chat glue for the playground (rejected: hides history).
- Auto-enable FUTURE on the decade spine (rejected: novelty vs credibility).
- Silent judge calibration “fix” of scores (rejected: report bias only).

**Evidence:**

`tests/test_wave_idea_full.py` (holes, diary v2, judge cache, pack gate, chat turn-2 contains turn-1, FUTURE quarantine). Full suite green after Wave 1–3. Gate W2/W3 for individual delivery: overlay caveat + playground audit + unmistakable FUTURE labels.

**Impact on protocol/cohort:**

`local-v1` unchanged. `local-v3-longitudinal` + `local-v2-eval` carry packs/chat/future. Demonstration packs are never “global LLM progress.”

**Owner:**

Local demo implementation

