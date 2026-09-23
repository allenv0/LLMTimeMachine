# Super-ultra plan: deliver `idea.md` fully

**Goal:** Implement the complete *LLM Time Travel Visualization Proposal* — not only the local teaching demo.  
**Baseline:** Local demo (`local-v1` + diary/curves + `local-v2-eval` judge) is done.  
**Gap list:** `docs/gaps-not-in-product.md`  
**Prior phased plan:** `docs/plan-close-idea-gaps.md` (Track A/B/C framing)  
**North star:** Help a non-specialist *feel* the speed of LLM progress on **their** weird prompt, with a method that survives skepticism (no fake cherrypicking, no fake scores, no fake “best of year”).

This plan is intentionally complete (idea.md end-state). Execute in waves; do not start Wave 3+ before Wave 1–2 gates pass.

---

## 0. Definition of “fully delivered”

`idea.md` is fully delivered when **all** of the following are true:

| ID | Acceptance (maps to idea.md) |
|---|---|
| D1 | A user enters a **private, idiosyncratic** prompt and runs it through a **year-by-year** lineup spanning the proposal’s era list (or explicit labeled holes + substitutes with disclosure). |
| D2 | Outputs are comparable **chronologically** and (optionally) **blindly**, with full audit of what each model received. |
| D3 | **Automatic quality rank (1–10)** exists for each output, produced by a **separate judge**, versioned rubric, inspectable transcripts — and UI never pretends it is ground truth. |
| D4 | A **graph over time** shows this prompt’s quality; a **density / global overlay** shows how typical that curve is (published sample or live corpus). |
| D5 | The user can **pre-register** prompts and **return over time**; the product can mark **first solve** year/model; optional **email** when a new model is added. |
| D6 | A **playground** mode lets the user **talk to** one historical checkpoint (multi-turn, visible adapters). |
| D7 | The timeline can end at a **status-quo** model and (optional) a clearly labeled **FUTURE** best-of-n. |
| D8 | If public: a **prompt/response corpus** with abuse controls; if local-only build of the same idea: export packs that stand in for global curves **with explicit limits**. |
| D9 | Claim boundary is always honest: sample vs frontier, estimate vs truth, personal vs global. |

**Not required for “full idea.md” but valuable:** Anthropic/OpenAI/nonprofit hosting (idea.md’s last paragraph is org suggestion, not product spec).

---

## 1. Target product surfaces (end state)

```text
┌─────────────────────────────────────────────────────────────────┐
│  LLM Time Travel — public + local                               │
├──────────────┬──────────────────┬───────────────────────────────┤
│ Playground   │ Time-trip        │ Curves                        │
│ chat one year│ prompt → N years │ my curve · judge · global     │
├──────────────┼──────────────────┼───────────────────────────────┤
│ Diary        │ Blind lab        │ Corpus                        │
│ pre-reg/solved│ rank without year│ browse weird prompts          │
├──────────────┴──────────────────┴───────────────────────────────┤
│ Audit everywhere: adapter, pin, checksum, judge rubric, seed    │
└─────────────────────────────────────────────────────────────────┘
```

| Surface | idea.md role | Priority |
|---|---|---|
| **Time-trip** (existing, extend) | Core comparison | P0 |
| **Curves** (my + judge + global) | Auto rank + global overlay | P0 |
| **Diary** (extend to real time) | Lived progress / first-solve | P0 |
| **Decade spine** (2015→2026 + holes + status-quo) | “Every year” fidelity | P0 |
| **Playground chat** | “Talk to it” | P1 |
| **Blind lab** (exists) | Anti-cherrypick taste | P1 |
| **Corpus** | Public weird prompts | P1 (cloud) / P2 (pack-only) |
| **Email updates** | Semi-annual re-runs | P2 |
| **FUTURE ensemble** | Speculative endpoint | P2 |

---

## 2. Protocol strategy (do not skip)

Full delivery **cannot** live under `local-v1` (it forbids automatic judge, global overlays, email, multi-user).

| Protocol | Scope | Status |
|---|---|---|
| `local-v1` | Laptop trips, audit, human ratings, diary, walk | **Frozen — keep** |
| `local-v2-eval` | Opt-in judge + estimated curves | **Done (appendix)** |
| `local-v3-longitudinal` | Multi-session diary semantics, first-solve export schema, offline curve packs | **To write** |
| `cloud-v1` | Accounts, corpus, global density, email, queues, ToS/abuse | **To write (new service)** |

Rules that survive every version:

1. No silent substitution, silent rewrite, silent retry, silent judge.  
2. Every score has rubric + judge identity + transcript path.  
3. Every year slot is `available | substitute | hole` — never a fake frontier.  
4. User prompts are private by default; corpus publish is opt-in per item.  
5. “Global” curves are labeled by pack id / corpus snapshot date.

---

## 3. Workstreams (the full build)

### WS1 — Decade spine & cohort fidelity (G3) → D1

**Goal:** 2015→2026 visible timeline with honest holes and a status-quo endpoint.

| Year | Target class | 16GB path | Stretch / server path |
|---|---|---|---|
| 2015 | char-RNN / NanoGPT-class | Tiny char-RNN (public ckpt or micro retrain) | same |
| 2016 | LM1B / n-gram era | Labeled hole **or** small KenLM demo marked “not LLM” | LM1B if license OK |
| 2018 | GPT-1 117M | GPT-1 if legally obtainable; else hole | same |
| 2019 | GPT-2-class | GPT-2 / Medium (have) | GPT-2 XL / 1.5B |
| 2020 | GPT-3-class | **Hole:** “GPT-3 not local” | OpenAI archive if offered |
| 2021 | GPT-J-class | GPT-2 Medium substitute (have) | GPT-J 6B |
| 2022 | FLAN-T5 XXL / GLM-130B | FLAN-T5 Large (have) | FLAN XL/XXL |
| 2023 | Qwen-72B-Chat-class | Mistral-7B Q4 (have) | Larger open chat |
| 2024 | DeepSeek-V3-class | Qwen2.5-7B Q4 (have) | DeepSeek-class if feasible |
| 2025 | GLM-4.7 / GPT-5.2 / Kimi… | Hole or best local 2025 open weights | Frontier open weights |
| 2026 | Astra / Fable / GLM-5.3… | Hole | Best available |
| **Today** | Status-quo endpoint | Labeled 6th+ slot | Strongest local / API only if product allows |

**Engineering**

1. `registry/cohort-decade-v0.yaml` with `slot_status: available|substitute|hole`.  
2. UI timeline with dashed hole nodes + substitute badges (never rename).  
3. Preload matrix per slot; disk tiers `lite | standard | high | server`.  
4. Hardware preflight that explains *why* a slot is a hole.  
5. Decision-log entry per added/removed checkpoint.

**Tests:** registry schema, ascending years, no unpinned revisions, UI hole rendering, preload pin tests.

**Gate D1:** A user sees a decade spine, understands holes/substitutes in one sentence, and runs every available slot.

**Effort:** L (curation-heavy). **Risk:** licensing, disk, weak early models (mitigate with micro-prompts per era).

---

### WS2 — Automatic quality + graphs (G1 full) → D3, D4-left

**Goal:** Reliable 1–10 estimates from a **separate** judge, on demand or batch.

**Upgrade path**

| Stage | Judge | When |
|---|---|---|
| B0 (done) | FLAN-T5 Large, `judge-rubric-v1`, refuse-to-score | now |
| B1 | Dedicated non-status-quo judge (e.g. mid-size instruct **not** on the year list, or clearly role-separated) | next |
| B2 | Dual-judge agreement (two models; show both or adjudicate with documented rule) | after B1 |
| B3 | Optional external judge **only** in cloud product, same rubric schema | cloud-v1 |

**Engineering**

1. `registry/judges/rubric-v2.yaml` with structured JSON output contract (`{"score": n}` or `{"unscored": reason}`) to cut parse failures.  
2. `JudgeService` batch job + progress UI; resume; cache by `(judge, rubric, output_sha)`.  
3. Calibration set: 20–50 gold-ish items (human 1–10) for **reporting** judge bias — never silently “fix” scores.  
4. Estimated quality chart always shows: rubric id, judge id, n scored / n refused.  
5. Export judge pack.

**Tests:** JSON parse, cache hits, refuse still works, no auto-run on trip, banner presence.

**Gate D3:** Score a full five/decade trip; ≥80% of non-pathological runs produce a number or a clear refusal; transcripts auditable.

**Effort:** M. **Risk:** judge bias, false precision (mitigate: anchors + refusal + dual-judge).

---

### WS3 — Global improvement overlay (G2 full) → D4-right

**Goal:** “My curve vs everyone’s” without lying.

**Two delivery modes (build both eventually)**

| Mode | Data | Trust story |
|---|---|---|
| **Offline pack** | Frozen `curves-pack-vN.json` produced under a stated protocol (our runs or consenting contributors) | “Published sample, not all of LLM history” |
| **Live corpus** | Opt-in published trips + scores; server aggregates density | “Contributors who chose to publish” |

**Pack schema (v1)**

```json
{
  "pack_id": "curves-pack-v1",
  "protocol": "local-v2-eval",
  "cohort_id": "decade-v1",
  "judge_id": "judge-…",
  "rubric_id": "judge-rubric-v2",
  "created_at": "…",
  "curves": [
    {
      "prompt_sha256": "…",
      "preview": "optional if consented",
      "tags": ["code", "logic"],
      "points": [{"year": 2019, "score_1_10": 2, "source": "judge_v2"}]
    }
  ]
}
```

**Engineering**

1. Pack loader + version compatibility check (mismatch ⇒ refuse overlay).  
2. Overlay UI: my bold line, pack spaghetti, median + IQR band; text summary for a11y.  
3. Local portfolio stays separate and labeled (already Phase A).  
4. If live: publish flow with preview of what leaves the device; delete/export account data.

**Tests:** pack version gate, no write-back into user trips, band n-threshold, caption strings.

**Gate D4:** User can explain in one sentence why the band is not “all of LLM progress.”

**Effort:** C1 pack = M; live corpus = L. **Risk:** misleading density if pack is tiny — enforce min n and show n.

---

### WS4 — Lived time: diary, first-solve, email (G4, G7) → D5

**Goal:** From “one trip” to “I tried this for years.”

| Feature | Local (`local-v3-longitudinal`) | Cloud (`cloud-v1`) |
|---|---|---|
| Pre-register prompt | done (Phase A) | same + account |
| Link many trips | done | same |
| First-solved marker | done (user) | user + optional judge_v2 |
| Decade walk + reflections | done (simulated) | same |
| **Real re-run when new cohort lands** | manual “Re-run diary” batch | automatic job |
| **Email** | ICS/todo stub only | double opt-in email |
| “First solved at year Y” timeline across entries | add portfolio view | public gallery optional |

**Engineering**

1. `diary re-run` CLI + UI: for each entry, optional tour-only or full.  
2. First-solved comparison helper: show all years for entry; user (or judge) marks earliest solve; store `solved_mark`.  
3. `local-v3` schema: `diary/index.json` version field + migrations.  
4. Email (cloud): consent record, unsubscribe, no raw prompt in email body (link to private page).

**Gate D5:** Register clue → runs at T0 and T1 → first-solved updates → optional email when `cohort-decade-v2` ships.

**Effort:** Local M; email L. **Risk:** spam law, cost; keep email cloud-only.

---

### WS5 — Playground chat (G5) → D6

**Goal:** “Fire up an old checkpoint and talk to it.”

**Engineering**

1. `ChatSession` artifacts under `local-data/chats/<id>/` (turn files + manifest).  
2. Adapter versions: `continuation-transcript-v1`, `instruction-flat-transcript-v1`, native chat multi-turn templates **visible**.  
3. UI: pick year/model → multi-turn thread → audit per turn.  
4. Same frozen generation profile per turn; no tools; no hidden system prompt.  
5. Warn when base models derail — that is content, not a bug to paper over.

**Tests:** turn-2 prepared contains turn-1 bytes; over-limit fails visible; audit parity.

**Gate D6:** Hold a 4-turn chat with GPT-2 and with Mistral; export the session; every turn’s prepared input inspectable.

**Effort:** M. **Risk:** adapter honesty (do not wrap 2019 in modern chat glue).

---

### WS6 — Status-quo + FUTURE (G6) → D7

**Engineering**

1. `status-quo` slot (not a fake year): strongest model that fits policy/hardware.  
2. `FUTURE (synthetic)`: best-of-n across 2–3 modern local models or N seeds; selection rule frozen and shown; UI quarantine (never a year).  
3. Off by default; cannot mark first-solved unless user opts in.

**Gate D7:** Timeline ends with Today + optional FUTURE badge; labels unmistakable.

**Effort:** S–M. **Risk:** novelty vs credibility — keep quarantined.

---

### WS7 — Corpus & outreach (G8) → D8 (cloud-v1)

**Goal:** idea.md’s public playground + interesting weird-prompt corpus.

**Product requirements**

1. Accounts, ToS, rate limits, abuse reporting.  
2. Per-trip **Publish** with local preview of payload. Private default forever.  
3. No training on user prompts without separate explicit consent.  
4. Browse corpus: filters (year first-solved, tags), stable prompt hashes, optional previews.  
5. Downloadable curve packs for offline compare.  
6. Multi-user inference fleet + queue (not Streamlit).  
7. Security/privacy threat model doc + retention policy.

**Gate D8:** External user publishes one trip, appears in corpus, can unpublish; density overlay can optionally include corpus snapshot.

**Effort:** XL (separate service). **Risk:** highest — start only when laptop experience is undeniable.

---

## 4. Wave plan (execution order)

```text
Wave 1 — Trust & data spine          [WS1 partial + WS2 B1 + WS4 local]
Wave 2 — Compare like idea.md        [WS3 pack + WS2 graphs polished]
Wave 3 — Feel like a playground      [WS5 + WS6 + WS1 full decade]
Wave 4 — Reach people                [WS7 cloud + WS4 email + WS3 live density]
```

### Wave 1 (next after current baseline)

1. Write `PROTOCOL-local-v3-longitudinal.md`.  
2. Cohort `decade-v0` with **holes visible** + status-quo stub.  
3. Judge rubric v2 (JSON) + dedicated judge pin + cache.  
4. Diary re-run + first-solved timeline across entries.  
5. Validation matrix filled for real hardware (close `docs/validation.md` pendings).

**Gate W1:** Non-builder completes trip, rates, sees human + estimated curves, marks first-solve, re-runs diary after “new year” slot appears.

### Wave 2

1. Ship `curves-pack-v1` (≥30 diverse prompts, frozen method).  
2. Overlay UI + local density.  
3. Judge calibration report (bias visible).  
4. Export “compare pack”.

**Gate W2:** User can answer “am I being cherrypicked?” with a chart **and** a one-line caveat.

### Wave 3

1. Full decade slots that fit + documented holes.  
2. Playground chat.  
3. FUTURE synthetic.  
4. UX polish: decade walk as first-run story.

**Gate W3:** Demo script matches idea.md’s emotional beats (pelican, grandma clue, private weird prompt).

### Wave 4

1. `cloud-v1` service design + legal.  
2. Corpus + density + email.  
3. Public education launch (labs / nonprofit / arena partners if any).

**Gate W4:** idea.md acceptance metrics from plan §2.3 at outreach scale (five non-builders, second prompt, limitation literacy).

---

## 5. Cross-cutting engineering standards

| Concern | Standard |
|---|---|
| **Claims** | Every surface: sample ≠ frontier; estimate ≠ truth; personal ≠ global |
| **Privacy** | Default private; hash-first manifests; publish explicit; no telemetry |
| **Integrity** | Pin revision + checksum; verify-before-generate; atomic writes |
| **Eval** | Rubric + judge + transcript always; refuse > invent |
| **Perf** | Sequential model load on laptop; queue on cloud; first status &lt;10s |
| **A11y** | Text summaries for every chart |
| **i18n** | English supported path until a protocol bump |
| **Ops (cloud)** | Retention, deletion, unsubscribe, rate limit, audit logs without raw prompts |

**Test pyramid additions per wave:** registry schema, pack versioning, judge cache, chat multi-turn, corpus publish/unpublish, email consent.

---

## 6. Metrics (done = full idea.md)

| Metric | Source |
|---|---|
| ≥5 non-builders complete a self-chosen prompt trip | field test |
| ≥3 open audit **or** run a second prompt | field test |
| Users can state cohort + score limitations unprompted | interview |
| Judge coverage: % scored vs refused on a fixed probe set | CI/manual |
| Pack overlay used in ≥1 session per tester | analytics **only if** cloud + consent; else interview |
| First-solve marked on ≥1 diary entry per returning user | diary |
| Email: opt-in rate + unsubscribe correctness | cloud |
| 10 consecutive trips stable | soak |

---

## 7. Rejected shortcuts (stay honest)

| Shortcut | Why rejected |
|---|---|
| Claim “best of every year” with current five stand-ins | Breaks truthful claim |
| Silent LLM-judge on every trip | Destroys anti-cherrypick story |
| Zero-fill missing years/scores | Fake smooth progress = the thing idea.md mocks |
| “Global” curve from 3 local prompts | Dishonest density |
| Wrap GPT-2 in hidden modern chat template | Hides history |
| Email / corpus inside the laptop app | Scope + privacy disaster |
| Train on user prompts | Forbidden |
| Status-quo model grades itself as “today” without disclosure | Confounds the narrative |

---

## 8. Effort map (rough)

| Workstream | Size | Depends on |
|---|---|---|
| WS1 Decade spine | L | licenses, disk |
| WS2 Judge upgrade | M | WS1 not required |
| WS3 Pack overlay | M | WS2 scores or Track A |
| WS3 Live density | L | WS7 |
| WS4 Diary/email | M / L | local-v3 / cloud-v1 |
| WS5 Chat playground | M | adapters discipline |
| WS6 Status-quo/FUTURE | S–M | WS1 |
| WS7 Corpus/outreach | XL | product + legal |

**Minimum to say “idea.md delivered for individuals”** (no public service):  
**WS1 + WS2 + WS3-pack + WS4-local + WS5 + WS6.**

**Minimum to say “idea.md delivered as public outreach”:**  
**all of the above + WS7 + email + live density.**

---

## 9. Immediate next actions (when you say go)

1. Freeze this plan’s Wave 1 scope in `docs/decision-log.md`.  
2. Write `PROTOCOL-local-v3-longitudinal.md`.  
3. Implement `cohort-decade-v0` holes + UI slot status.  
4. Rubric v2 JSON + judge cache + dedicated judge pin.  
5. Diary re-run + first-solved timeline.  
6. Fill `docs/validation.md` real-hardware matrix.

Then Wave 2 pack, Wave 3 playground/decade completion, Wave 4 cloud.

---

## 10. Verdict

| Question | Answer |
|---|---|
| Can we say the **current** project fully delivers `idea.md`? | **No.** |
| Can **this plan** get there? | **Yes**, in waves, without lying along the way. |
| What unlocks the emotional core fastest? | Wave 1–2 (decade holes + honest judge + pack overlay). |
| What is optional theater vs load-bearing? | FUTURE model = optional. Global density + decade fidelity + lived diary = load-bearing for the proposal. |
