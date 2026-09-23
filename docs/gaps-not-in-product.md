# What is still not in the product

**As of:** 2026-09-23 (after Wave 1–3 of `docs/plan-full-idea.md`: decade spine, local-v3 diary, judge v2, packs, chat, FUTURE)  
**Compared to:** `idea.md` — *LLM Time Travel Visualization Proposal*  
**Honest summary:** The **individual-delivery path** (WS1–WS6) is implemented. The **public outreach product** (`cloud-v1`) is not.

Use this list when talking to users, funders, or teammates. Do **not** claim full public `idea.md` outreach delivery.

---

## Accurate claim (safe wording)

> A local, auditable LLM time-travel demo: year-by-year spine with visible holes, your weird prompts, human + opt-in judge curves, offline pack overlay, and a multi-turn playground. It is not a verified annual frontier lineup, not ground-truth ranking, and not a global progress study.

Aligned with the product truthful claim:

> A laptop-compatible, auditable sample of LLM history. It is not a verified record of the best model in every year.

---

## Gap table (idea.md → product)

| # | What `idea.md` proposes | What the product has today | Gap type |
|---|---|---|---|
| 1 | **Best surviving LLM from every year** over the past decade | **Decade spine** `decade-v0` with visible holes (2015/16/18/20/25/26) + labeled substitutes (2019 GPT-2 available; 2021–2024 stand-ins) | **Partial — holes + substitutes, not verified frontier** |
| 2 | **Automatic quality ranking** 1–10 | Opt-in local judge (`local-v2-eval`, rubric v2 JSON, cache, refuse-to-score) + human −2..+2 | **Partial — estimate, not ground truth** |
| 3 | Graph of **this prompt’s improvement over time** | Human curve + estimated judge curve (gaps stay gaps) | **Delivered (Track A/B)** |
| 4 | Compare to **global improvement** (density of all curves) | **Offline curve packs** + demonstration pack overlay (median/IQR, min-n). No live multi-user corpus | **Partial — pack stand-in, not live global** |
| 5 | Anti-cherrypicking via **user-chosen** prompts | Free text, frozen cohort, audit drawers, blind A–E | **Delivered** |
| 6 | **Live through the decade**; see when a release **first solved** it | Diary re-run + first-solved timeline + simulated decade walk | **Partial — re-run ≠ calendar years; no email** |
| 7 | **Diverse weird prompts**, pre-registered, revisited | Diary pre-register + explicit re-run + .ics stub | **Partial — no scheduled regimen** |
| 8 | Chatbot **playground** | **Multi-turn chat** with visible historical adapters + per-turn audit | **Delivered (WS5)** |
| 9 | **Status-quo endpoint** | Labeled `status_quo` slot (Qwen 2024 stand-in for today) | **Delivered as labeled stand-in** |
| 10 | Optional **“future”** best-of-n | `FutureEnsemble` best-of-n; **off by default**; quarantined | **Delivered as optional synthetic** |
| 11 | **Public corpus** of prompts/responses | Local-only + export; demonstration pack is synthetic | **Missing — cloud-v1** |
| 12 | **Email** semi-annual re-runs | Local `.ics` stub only | **Missing — cloud-v1** |
| 13 | **Public multi-user outreach** | Single-user Streamlit on `127.0.0.1` | **Missing — cloud-v1** |

---

## What *is* solid (do not undersell)

- Decade spine with **visible holes** and labeled substitutes (`stands_for`)
- Status-quo endpoint + optional quarantined FUTURE (off by default)
- Private prompts, frozen cohort, pins, full audit trail
- Diary schema v2, explicit re-run, first-solved timeline
- Human ordinal curves + opt-in judge (rubric v2 JSON, cache, refuse)
- Offline curve packs + overlay with honest n/caveat (demo pack labeled synthetic)
- Multi-turn playground with visible adapters (no hidden chat glue on 2019)
- Calibration bias report (never rewrites scores)

---

## One-line verdict

**Individual idea.md delivery is in (WS1–WS6); public outreach (WS7 cloud corpus/email/live density) is not.**
