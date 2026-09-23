# Ultra-deep plan: close the remaining idea.md gaps

**Status:** Plan only — not authorized for implementation until you say go.  
**Baseline:** `local-v1` demo (five-era / quick tour, audit trail, no LLM-judge).  
**Target:** Teach felt LLM progress the way `idea.md` describes, without lying about method.

This plan covers the eight gaps left after the local demo:

| ID | Gap (idea.md) | Severity to the pitch |
|---|---|---|
| G1 | Automatic quality rank + graph over time | Core |
| G2 | Your curve vs global improvement / density overlay | Core |
| G3 | Decade coverage + true “best surviving / status quo” | Core (hardware-bound) |
| G4 | Live through years; first-solve; pre-registered prompts | Core experiential |
| G5 | Chat playground (“talk to it”), not only one-shot trips | Medium |
| G6 | “Future” best-of-n extrapolating model | Low / experimental |
| G7 | Email semi-annual re-runs | Low for local; medium for outreach |
| G8 | Public weird-prompt corpus + multi-user outreach | High trust risk |

---

## 0. Non-negotiables (apply to every phase)

1. **No silent judgment.** Any automatic score is labeled, versioned, and inspectable (judge id, prompt, model, seed). Never mix it into “fact.”
2. **Protocol is law.** Changing evaluation rules ⇒ new protocol version + decision-log entry. `local-v1` stays frozen and valid.
3. **User owns local data.** Export/delete remain complete. No prompt upload without explicit, separate opt-in.
4. **Cohort honesty.** Never rename a stand-in into a frontier claim. Substitutions get a new cohort id.
5. **Seams stay clean.** UI never touches runners; scores never live in `TripController` hot path except via `EvaluationPort`.
6. **Fail visible.** Missing judge, missing corpus, unsupported model ⇒ surface the limitation, do not fake a curve.

### Protocol fork (decide once, at the start of Phase B)

| Track | Protocol | What it allows | Who it is for |
|---|---|---|---|
| **A — Honest human** | stay `local-v1` | Personal curves from usefulness / blind rank / first-solve | Default laptop demo |
| **B — Machine estimate** | `local-v2-eval` | Explicit LLM-judge (or other estimator) + quality graphs | Research / alpha, never default-silent |
| **C — Shared world** | `cloud-v1` (new product) | Accounts, corpus, global density, email | Outreach only |

**Recommendation:** Build A fully first. Gate B behind a visible “Estimated quality (experimental)” panel and a protocol banner. Treat C as a different product, not a Streamlit sidebar toggle.

---

## 1. Architecture (where each gap plugs in)

```text
                    ┌─────────────────────────────────────┐
                    │ UI (Streamlit shell)                │
                    │ trip · arc · diary · curves · chat  │
                    └──────────────┬──────────────────────┘
                                   │ never touches runners
                    ┌──────────────▼──────────────────────┐
                    │ TripController / TripUtils          │
                    │ CohortCatalog · RunnerFactory       │
                    └──────┬───────────────┬──────────────┘
                           │               │
              ┌────────────▼──┐   ┌────────▼─────────────────┐
              │ ArtifactStore │   │ EvaluationPort           │
              │ trips/...     │   │ Null | HumanCurve        │
              │ diary index   │   │ JudgeV2 (opt-in)         │
              └───────────────┘   └────────┬─────────────────┘
                                           │
                                  ┌────────▼────────┐
                                  │ CurveStore      │
                                  │ personal/global │
                                  └─────────────────┘
```

**New modules (proposed):**

| Module | Responsibility |
|---|---|
| `src/time_machine/diary.py` | Prompt diary: register prompts, link trips, first-solved, revisit |
| `src/time_machine/curves.py` | Build per-prompt and aggregate series from annotations / judge |
| `src/time_machine/evaluation_human.py` | `HumanCurveEvaluator` — maps annotations → ordinal series |
| `src/time_machine/evaluation_judge.py` | `JudgeEvaluator` (`local-v2` only) |
| `src/time_machine/judge_prompts.py` | Versioned judge rubric templates (visible) |
| `src/time_machine/chat_session.py` | Multi-turn session against one historical model |
| `src/time_machine/future_ensemble.py` | Best-of-n “future” endpoint (optional) |
| `src/time_machine/ui/diary.py` | Diary + first-solved timeline UI |
| `src/time_machine/ui/curves.py` | Personal / estimated / global curve charts |
| `src/time_machine/ui/chat.py` | Chat playground UI |
| `registry/judges/*.yaml` | Pinned judge cohort + rubric versions |
| `registry/diary/*.json` | Local pre-registered prompt portfolio (user-editable) |

**Domain extensions (additive, versioned):**

```text
PromptDiaryEntry:
  entry_id, raw_prompt_sha256, raw_prompt_ref (local file),
  created_at, tags[], success_criterion,
  trips[] (trip_id, created_at),
  first_solved: { model_id, trip_id, solved_at } | null,
  solved_mark: user | judge_v2 | unset

AnnotationScore (Track A only):
  ordinal: -2..+2 per model_id   # worse → better, human
  derived_from: usefulness | blind_rank | explicit

JudgeScore (Track B only):
  score_1_10, rubric_id, judge_model_id, judge_revision,
  judge_prompt_sha256, judge_raw_output_path, sampled_at

CurvePoint:
  x = display_year | release_date
  y = AnnotationScore | JudgeScore
  band = none | user_iqr | corpus_density
```

Manifest stays trip-scoped. Curves are **derived views** over trips + diary + annotations — do not bolt scores into `TripManifest` runs (keeps `local-v1` exports stable).

---

## 2. Gap plans

### G1 — Quality rank + graph over time

**User story.** After a trip (or across trips), I see how quality moved from 2019→2024 on *my* prompt, without a marketing line telling me “better.”

#### Track A — Human curve (ship first, legal under `local-v1`)

**Design**

- One extra annotation control per model: **ordinal quality** (−2 −1 0 +1 +2) with labels: much worse / worse / similar / better / much better relative to “what I hoped for,” *or* keep usefulness and derive ordinal (`no=-1`, `partly=0`, `yes=+1`) with an explicit mapping disclosure.
- Prefer **explicit ordinal** + optional derive-from-usefulness, because idea.md wants ranking, not just yes/no.
- `HumanCurveEvaluator.evaluate_trip` reads `annotations.json` → `CurvePoint[]` stored under `local-data/curves/<trip_id>.json` (derived, deletable with trip).
- Chart: simple year on X, ordinal on Y, one line per prompt (or one line for active trip). Missing ratings = gaps, not zeros.
- Always caption: **“Your ratings. Not a scientific measurement.”**

**UI**

- New tab **Progress curve** next to Results / Blind / Local data.
- For a single trip: sparkline/line across the trip’s model years.
- For diary (G4): overlay all registered prompts as thin lines + bold selected prompt.

**Tests**

- Mapping usefulness→ordinal documented and tested.
- Unrated models do not invent points.
- Curve JSON round-trip; deleted trip removes its points.
- No network; no judge imports on this path.

**Acceptance**

- Rate three models on pelican trip → graph shows three points and an honest gap policy.
- Blind rank can optionally feed the same series (rank inverted to ordinal) with a toggle off by default (rank is preference among candidates, not absolute quality — label it).

**Effort:** S–M (2–4 sessions). **Risk:** Low. **Protocol:** no change.

#### Track B — Machine 1–10 judge (`local-v2-eval`)

**Design**

- Judge is **another local model**, not one of the five displayed “history” slots if possible (idea.md: preferably not the status-quo model). Practical laptop pick: a small instruct model used *only* as judge (e.g. Qwen2.5-1.5B/3B-Instruct or the 7B with a strict rubric), pinned in `registry/judges/cohort-judge-v1.yaml`.
- Rubric file visible in UI: criteria (instruction-follow, correctness where checkable, relevance, honesty under uncertainty), 1–10 anchors, refusal to score when the prompt is private/unverifiable → emit `unscored` + reason (do **not** invent a number).
- `JudgeEvaluator.evaluate_run` writes `JudgeScore` + raw judge transcript under `local-data/judge/<trip_id>/<model_id>/` for audit.
- Graph: your prompt’s judge curve + optional “estimated” band. Never call it “true quality.”

**Hard rules**

- Judge runs only after an explicit **“Score with local judge (experimental)”** action (not during `run_trip` by default).
- UI banner when any judge score is on screen.
- Deterministic-ish: freeze judge gen profile; record seed; document non-determinism.
- Offline after preload; checksum the judge artifact like any model.

**Tests**

- Judge never runs on fake/Null path.
- Missing judge weights ⇒ visible unsupported, no curve.
- Rubric id + judge pin appear in export bundle.
- Property: scores not written into `ModelRun` as if they were generation telemetry.

**Acceptance**

- Score `tour-pelican-idea`: 2019 low, 2024 high; export contains rubric + judge outputs; protocol banner visible.

**Effort:** M–L. **Risk:** Medium (honesty, overfit, cost). **Protocol:** `local-v2-eval` + decision-log.

---

### G2 — Your improvement vs global improvement

**User story.** “Am I being cherrypicked? Show how my prompt’s curve sits among many other curves.”

**This is the trust device idea.md cares about.** It needs a **corpus of curves**. Local-only can only offer a **local density** of *your* diary prompts — not humanity’s.

#### Phase C1 — Local density (honest subset)

- Aggregate all diary prompts’ Track A (or B) curves on one chart: one thin line per prompt + median + IQR band.
- Label: **“Your prompt portfolio (n=…). Not global LLM progress.”**
- If n < 5, hide the band and say so (density needs mass).

#### Phase C2 — Shared corpus (`cloud-v1` or offline pack)

Two mutually exclusive ways to get “global”:

1. **Curated offline pack** (recommended first): a released JSON of pre-registered prompts + historical curves produced by *us* under a frozen protocol, shipped as `registry/corpus/curves-pack-v1.json`. Users compare against a *published sample*, not a live crowd. No accounts. Cite methodology in-app.
2. **Live public corpus** (G8): users publish prompt+outputs+scores; server aggregates density. Highest idea.md fidelity, highest abuse/privacy cost.

**Design (pack)**

- Pack schema: `pack_id`, protocol, cohort_id, judge_id (if any), `curves[]: {prompt_sha256, prompt_preview_policy, points[]}`.
- Prompt previews: only if original authors opted in; else hash + category tag (“code,” “writing,” “logic”).
- UI: toggle “Overlay sample density (pack v1).” Caption states pack date and that it is not frontier-wide.

**Tests**

- Pack version mismatch ⇒ refuse overlay.
- Overlay never writes into user trips.
- Offline load.

**Acceptance**

- User sees their pelican line against a pack band and can explain the limitation in one sentence (plan metric: “users can explain the cohort limitation”).

**Effort:** C1 = S; C2 = M (pack) / XL (live). **Risk:** C2 live = product/legal.

---

### G3 — Decade coverage + status-quo endpoint

**User story.** The timeline should feel like a decade, and “today” should feel like today.

**Cohort expansion matrix** (each slot = new cohort version):

| Year | idea.md target | 16GB fallback (status quo) | Stretch (32GB+/cloud) |
|---|---|---|---|
| 2015 | char-RNN / NanoGPT retrain | tiny char-RNN (new train or public checkpoint) | same |
| 2016 | LM1B | skip or small KenLM/n-gram demo labeled “not LLM” | LM1B if license ok |
| 2018 | GPT-1 117M | GPT-1 117M if weights legally obtainable; else labeled hole | same |
| 2019 | GPT-2 1.5B | GPT-2 / GPT-2 Medium (have) | GPT-2 XL |
| 2020 | GPT-3 | **visible empty slot** “GPT-3 not locally available” | OpenAI retrain if offered |
| 2021 | GPT-J 6B | GPT-2 Medium stand-in (have) | GPT-J 6B |
| 2022 | FLAN-T5 XXL / GLM-130B | FLAN-T5 Large (have) | FLAN-T5 XL/XXL |
| 2023 | Qwen-72B-Chat | Mistral-7B Q4 (have) | larger open chat |
| 2024 | DeepSeek-V3 | Qwen2.5-7B Q4 (have) | DeepSeek-class if feasible |
| 2025 | GLM-4.7 / GPT-5.2 / Kimi… | **empty “status quo unavailable”** or 2024 as labeled proxy | best local 2025 open weights |
| 2026 | Astra / Fable / GLM-5.3 | empty + disclosure | best available |

**Rules**

- Empty slots are **first-class UI** (dashed timeline node: “no local checkpoint”) — honesty beats a fake year.
- Never promote GPT-2 Medium to “2021 GPT-J.”
- Disk budget tiers: `lite` (~25GB), `standard` (~50GB), `high` / remote.
- Optional **sixth “status quo” endpoint** (plan already allows): one extra model labeled `status-quo`, not a year.

**Implementation**

1. Extend `hardware_profile` recommendations and preflight disk math.
2. `cohort-decade-v0.yaml` with holes; `cohort-decade-v1.yaml` when filled.
3. Timeline UI supports `status: available | hole | substitute` per year.
4. Preload scripts per slot; checksum index.

**Acceptance**

- User sees 2015→2026 spine with holes labeled; five-era still default on 16GB; no silent substitution.

**Effort:** L (months of curation). **Risk:** licensing, disk, weak early models confusing UX (mitigate with micro-prompts).

---

### G4 — Live through the years (diary, first-solve, pre-registration)

**User story.** I register weird prompts now; I come back; I see which year’s model first solved *my* task; I feel time passing.

**This is the biggest experiential gap** and is fully doable offline.

#### Data: Prompt diary

- `local-data/diary/index.json` + `local-data/diary/prompts/<entry_id>/raw-prompt.txt`.
- Entry links many trips over time (`revisit` runs the same hash).
- `success_criterion` is the solve rubric for the user (and optional judge later).

#### Features

1. **Register prompt** (from trip or blank) → diary entry (“pre-registered” in idea.md’s sense).
2. **Re-run** entry on: full cohort / tour / single year.
3. **First-solved marker:** user marks an output “this solved it” (or judge_v2 later). Timeline shows first model/year that solved each entry.
4. **Year-after-year mode (simulated):** optional “Decade walk” — one prompt, reveal year by year with a short pause and a “would you have believed this in 2019?” checkpoint reflection field (local notes). This is theater with real models — label it **simulation of living through releases**, not calendar time.
5. **Portfolio chart:** G2-C1 density of my own prompts.

**UI sketch**

- Left: diary list (tags, n trips, first-solved?).
- Center: selected entry → runs / curves / outputs by year.
- Right: “Decade walk” launcher.

**Tests**

- Revisit reuses exact raw prompt bytes (hash stable).
- First-solved is user-owned and exportable.
- Diary delete does not orphan trip files (reference integrity).
- Decade walk is a UI sequence over existing `run_trip(models=[one])` calls — no new inference path.

**Acceptance**

- Register grandma clue → run 2019–2024 → mark “still unsolved” or first-solved at 2024 → diary timeline updates. Matches idea.md’s “eventually some LLM release solved it.”

**Effort:** M. **Risk:** Low. **Protocol:** no change (Track A).

---

### G5 — Chat playground (“talk to it”)

**User story.** I want to poke GPT-2 / Mistral interactively, not only fire one prompt.

**Design**

- Mode switch: **Compare trips** (current) vs **Chat with one year**.
- Session = ordered turns stored under `local-data/chats/<session_id>/` (`turn-001-user.txt`, `turn-001-prepared.txt`, `turn-001-assistant.txt`, `manifest.json`).
- Adapters extend to multi-turn **only with visible templates**:
  - base: concatenate visible transcript as continuation (and show that’s what we do).
  - instruction: single-turn remains default; multi-turn optional with a visible “flat transcript” adapter version bump.
  - chat: native templates with explicit role markers; record exact prepared text every turn.
- Same generation profile per turn; no hidden system prompt; no tools.
- Session export/delete like trips.

**Risk callout:** Multi-turn base models will derail quickly — that is the lesson. UI should say so rather than wrap them in modern chat glue (that would hide history).

**Tests**

- Prepared input for turn 2 contains turn 1 bytes exactly as stored.
- No silent compaction/truncation (if over limit, fail visible).
- Audit parity with trips.

**Effort:** M. **Risk:** Medium (adapter versioning). **Protocol:** adapter_version bump + decision-log.

---

### G6 — “Future” best-of-n model

**User story.** A playful endpoint after 2026: “what might come next?”

**Design (strictly labeled experimental)**

- `future-ensemble-v1`: sample N completions from 2–3 modern local models (or same model N times with different seeds), pick by a frozen heuristic (judge_v2 score or length+constraint checklist — **not** hidden).
- Always render as **`FUTURE (synthetic)`** on the timeline, never as a year.
- Default **off**. Idea.md itself is unsure this works.

**Tests:** ensemble inputs/outputs audited; cannot appear in year slots; cannot affect first-solved without user opt-in.

**Effort:** S–M. **Risk:** novelty vs credibility — keep quarantined.

---

### G7 — Email semi-annual updates

**Only after** a hosted service exists (G8 / Track C). Local demo must not grow SMTP.

**Design sketch (cloud-v1)**

- Store `prompt_sha256` + email + consent timestamp; never store raw prompt on server unless user opts into corpus.
- Job: when a new cohort version lands, generate outputs (hosted weights) + optional scores, send one email with links to a **user-private** result page, delete or retain per policy.
- Double opt-in, one-click stop, no third-party trackers.

**Local stand-in (now):** “Export diary + reminder ICS / TODO” — user re-runs themselves. Honest, zero infra.

**Effort:** S local stub / L hosted. **Risk:** privacy, spam law, cost.

---

### G8 — Public corpus + multi-user outreach

**Product fork, not a feature flag.**

| Piece | Spec |
|---|---|
| Auth | accounts, rate limits, ToS |
| Publish | explicit per-trip “publish to corpus” with preview of what leaves the device |
| Private default | unpublished; personal prompts never required public (idea.md tension) |
| Corpus site | browse weird prompts, filter by year first-solved, download pack for offline compare |
| Abuse | blocklists, report, no training use without separate consent |
| Multi-user app | queue, quotas, model fleet — **not** Streamlit |

**If the goal is Anthropic/OpenAI/nonprofit outreach:** design this as `cloud-v1` product spec; reuse TripController + adapters + judge protocol server-side.

**Effort:** XL. **Risk:** highest. **Do not start** until Track A+B are convincing on a laptop.

---

## 3. Phased roadmap (ordered)

```text
Phase A  Human diary + personal curve          [G1-A, G4]     1–2 weeks
Phase B  Judge v2 + estimated quality graph    [G1-B]         1–2 weeks
Phase C  Local density → curve pack overlay    [G2]           1 week + curation
Phase D  Decade spine (holes + status-quo)     [G3]           ongoing curation
Phase E  Chat playground                       [G5]           ~1 week
Phase F  Future ensemble (optional)            [G6]           days
Phase G  Cloud: corpus, density, email         [G2-full,G7,G8] separate product
```

**Parallelization:** D can proceed anytime (artifacts). E is independent of B. C1 depends on A. C2 pack can be produced with B offline. G depends on B’s rubric being trusted.

### Phase A detail (do this next)

1. Domain: `PromptDiaryEntry`, `AnnotationScore`, `CurvePoint`.
2. Store: diary index + per-trip derived curves; export includes diary optional bundle.
3. `HumanCurveEvaluator` + curve JSON.
4. UI: ordinal ratings, **Progress curve** tab, diary sidebar, decade-walk launcher, first-solved control.
5. Tests: diary integrity, curve honesty (no zero-fill), export/delete.
6. Docs: decision-log; note that Track A is still `local-v1`.

**Gate A:** A nontechnical user registers a weird prompt, runs tour, rates it, sees a labeled personal curve, marks first-solved, exports, deletes.

### Phase B detail

1. `PROTOCOL.md` → `local-v2-eval` appendix (or `PROTOCOL-local-v2.md`).
2. Judge registry + rubric + preload.
3. Explicit score action; audit transcripts; UI experimental banner.
4. Graph estimated curve; export judge bundle.
5. Validation matrix rows for judge determinism and refusal-to-score.

**Gate B:** Same pelican trip scored; reviewer can explain why the number is an estimate.

### Phase C detail

1. C1 diary density chart.
2. Curate `curves-pack-v1` (20–50 diverse prompts, frozen method, published hashes/previews policy).
3. Overlay UI + pack versioning tests.

**Gate C:** User sentence test: “this is my portfolio / a published sample, not all of LLM history.”

---

## 4. Cross-cutting engineering

| Concern | Plan |
|---|---|
| Performance | Curves/diary are post-hoc; never block generation. Judge is a separate job. |
| Storage | Curves/judge derived under `local-data/` and delete with parent trip/entry. |
| Export | Trip export unchanged for `local-v1`. New `export_diary_pack` optional. |
| Telemetry | Still none. |
| Security | Local bind remains. Cloud plan gets its own threat model. |
| i18n | English supported path remains. |
| Accessibility | Charts need text summaries (table view of points). |

**Test pyramid additions**

- Unit: diary, curve derivation, judge schema, pack versioning.
- Contract: EvaluationPort implementations.
- Integration: fake judge; fake corpus pack.
- Manual: validation.md sections for judge, diary, chat multi-turn, decade holes.

---

## 5. Explicitly rejected shortcuts

| Shortcut | Why not |
|---|---|
| Auto-run judge on every trip by default | Violates trust; idea.md’s audience is already skeptical |
| Reuse one of the five history models as silent “today” grader | Confounds the story; idea.md prefers a different judge |
| Zero-fill missing years/scores | Fake smooth curves = the cherrypicking they fear |
| Rename five-era models as annual frontiers | Breaks truthful claim |
| Email in the laptop app | Scope and privacy disaster |
| Train on user prompts | Forbidden |
| “Global” curve from 3 local diary prompts | Dishonest density |

---

## 6. Success metrics (map to idea.md + plan §2.3)

| Metric | Phase |
|---|---|
| User chooses own prompt and sees progress | A (already mostly true) |
| User can state cohort + score limitations | A–C UI copy tests + human test |
| User revisits a pre-registered prompt | A diary |
| User sees first-solved year | A |
| User compares self vs sample without feeling tricked | C |
| ≥5 non-builders complete trips; ≥3 open audit or second prompt | field test |
| 10 consecutive trips stable | already target; keep on each phase |

---

## 7. Recommended execution call

**Build Phase A next** (diary + first-solved + personal quality curve + decade walk). It closes G4 and the honest half of G1/G2-local, deepens idea.md’s “live through the years” story, and does not fork the protocol.

Then **Phase B** only if you want machine scores in-demo; ship with `local-v2-eval` and a permanent experimental banner.

Treat **G7/G8** as productization after the laptop experience is undeniable.

---

## 8. Open decisions for you (before Phase A coding)

1. **Ordinal ratings:** new −2..+2 field, or derive from usefulness only?
2. **Blind rank → curve:** include as optional series or keep separate forever?
3. **Decade walk:** include the reflective pause theater, or keep pure data?
4. **Judge timing:** Phase B immediately after A, or stop at human curves for local-v1 purity?
5. **Status-quo sixth slot:** add a labeled “today” model when one fits on disk?

Answer those (or say “defaults”) and Phase A can be broken into implementable tasks the same day.
