# What is still not in the product

**As of:** 2026-09-23 (after local-v1 demo + Phase A diary/curves + Phase B local-v2-eval judge)  
**Compared to:** `idea.md` — *LLM Time Travel Visualization Proposal*  
**Honest summary:** The **core teaching loop** is in. The **full proposal** is not.

Use this list when talking to users, funders, or teammates. Do **not** claim full `idea.md` delivery.

---

## Accurate claim (safe wording)

> A local, auditable demo of the LLM time-travel idea: feel progress on your own prompts with frozen historical stand-ins. It is not the full decade of frontier models, not automatic ground-truth ranking, and not a global progress study.

Aligned with the product truthful claim:

> A laptop-compatible, auditable sample of LLM history. It is not a verified record of the best model in every year.

---

## Gap table (idea.md → product)

| # | What `idea.md` proposes | What the product has today | Gap type |
|---|---|---|---|
| 1 | **Best surviving LLM from every year** over the past decade (~2015–2026) | Five laptop-era **stand-ins** (2019 GPT-2, 2021 GPT-2 Medium, 2022 FLAN-T5 Large, 2023 Mistral-7B Q4, 2024 Qwen2.5-7B Q4) + optional empty-slot thinking in plans | **Coverage / fidelity** |
| 2 | **Automatic quality ranking** of every response (e.g. 1–10) | (A) Human −2..+2 ordinal + usefulness; (B) **opt-in** local judge estimate (`local-v2-eval`), often `UNSCORED`; never auto on trip | **Partial — not automatic, not ground truth** |
| 3 | Graph of **this prompt’s improvement over time** | Personal ordinal curve + estimated judge curve (gaps stay gaps) | **Mostly there (Track A/B)** |
| 4 | Compare that to **global improvement over time** (density of all curves) | **Local portfolio only** (your diary prompts). No global / crowd / published density | **Missing — G2 full form** |
| 5 | Anti-cherrypicking via **direct comparison** on **user-chosen** prompts | Strong: free text, frozen cohort, audit drawers, blind A–E | **Delivered** |
| 6 | **Live through the decade** year after year; see when a release **first solved** it | Diary + first-solved + **simulated** decade walk with reflections | **Partial — simulation, not calendar time** |
| 7 | **Diverse weird prompts**, pre-registered, revisited regularly | Starter prompts + diary pre-registration; no scheduled portfolio regimen | **Partial** |
| 8 | Chatbot **playground** (“fire up a checkpoint and talk to it”) | One-shot **trips** (compare modes) + decade walk; **no multi-turn chat** with one year | **Missing — G5** |
| 9 | **Status-quo endpoint** = best available model today | Timeline ends at 2024 Qwen 7B Q4 (labeled stand-in) | **Missing / constrained** |
| 10 | Optional **“future”** best-of-n extrapolating model | Not built | **Missing — G6** |
| 11 | **Public corpus** of prompts/responses (abuse-dependent) | Local-only by design; export for the user | **Out of scope for local-v1** |
| 12 | **Email** semi-annual re-runs when new models land | Not built (local stub only in plan) | **Missing — G7** |
| 13 | **Public multi-user outreach** (labs / nonprofit / arena-scale) | Single-user Streamlit on `127.0.0.1` | **Different product — cloud-v1** |

---

## Detail on the important gaps

### 1. Decade coverage is not the decade

`idea.md` lists roughly: 2015 char-RNN · 2016 LM1B · 2018 GPT-1 · 2019 GPT-2 1.5B · 2020 GPT-3 · 2021 GPT-J 6B · 2022 FLAN-T5 XXL / GLM-130B · 2023 Qwen-72B-Chat · 2024 DeepSeek-V3 · 2025–2026 frontier.

We ship **five hardware-fit slots** with **disclosed substitutions** (e.g. GPT-2 Medium stands in for GPT-J-class; Q4 GGUF 7Bs stand in for large open chat). Missing years are not empty UI nodes yet — they are simply absent.

**Never say:** “the best model of each year.”  
**Always say:** “laptop-compatible sample / stand-ins.”

### 2. Automatic ranking is estimated and opt-in

- Track A: **your** ordinal — honest, sparse, subjective.  
- Track B: local judge under `judge-rubric-v1` + FLAN-T5 Large in judge role — **experimental banner required**, refuse-to-score on unverifiable private facts. Real runs often return `UNSCORED`.  
- No silent judge on trips. No claimed ground truth. No merge of human and machine lines without labels.

`idea.md`’s “best available model grades each response 1–10” is **not** fully realized.

### 3. Global improvement overlay is absent

Without a corpus of many users’ (or a published pack of) quality curves, we cannot draw the density plot that answers “am I being cherrypicked?” We only show **your** portfolio (and only with a band at n≥5).

### 4. Longitudinal “solved it over years” is simulated

Decade walk reveals one year at a time with reflection pauses — useful theater over real checkpoints — but it is **not** waiting for new model releases over calendar years, and there is no hosted re-run/email loop.

### 5. Playground vs trips

The pitch’s “talk to it” is unmet: no multi-turn session against GPT-2 or Mistral with visible historical adapters per turn.

---

## What *is* solid (do not undersell)

- Private, user-chosen prompts (the idiosyncratic conviction mechanism in `idea.md`)
- Frozen cohort, pinned revisions, visible adapters, full audit trail
- Chronological reveal + quick base→instruction→chat progress arc
- Blind compare, personal annotations, local export/delete
- Honesty protocol (`PROTOCOL.md`, `PROTOCOL-local-v2-eval.md`, decision log)
- Diary: pre-register, link trips, first-solved, reflections
- Personal quality curves with honest gaps
- Opt-in estimated scores with refuse-to-score and full judge I/O audit

---

## One-line verdict

**Core idea delivered as a local demo; full `idea.md` not delivered** — missing true decade/frontier coverage, automatic ground-truth ranking, global density comparison, chat playground, future model, and all hosted outreach features (corpus, email, multi-user).
