# Protocol appendix: local-v3-longitudinal (lived time & offline packs)

**Status:** Optional track for multi-session diary semantics, first-solve timelines, and offline curve packs. Does **not** replace `local-v1` or `local-v2-eval`.  
**Base protocols:** `local-v1` (trips, privacy, adapters, generation) and `local-v2-eval` (opt-in judge estimates) remain in force.

## Why this appendix exists

`idea.md` asks people to live with weird prompts across years and compare their curve to global improvement. Local demos cannot wait calendar years or host a public corpus. This appendix defines **honest local stand-ins**: re-runs when a new cohort slot lands, first-solved timelines across diary entries, and **frozen offline curve packs** that stand in for global density with explicit limits.

## Claim boundary

> Diary re-runs are **not** calendar time. Curve packs are a **published sample**, not all of LLM progress. First-solved marks are user (or opt-in judge) judgments, not scientific measurements.

## Rules

1. **No silent re-run.** Diary re-run is an explicit user action (“Re-run diary entry” / batch). Each re-run creates a new trip and links it to the entry.
2. **First-solved is marked, not inferred silently.** `solved_mark` is `user | judge_v2 | unset`. Future synthetic endpoints cannot mark first-solved unless the user opts in.
3. **Index is versioned.** `diary/index.json` carries `schema_version`. Migrations are deterministic and never rewrite `raw-prompt.txt`.
4. **Privacy.** Full prompt text lives only in `prompts/<id>/raw-prompt.txt`. Index previews stay ≤40 chars. Exports of diary packs never include full prompts unless the user explicitly includes them.
5. **Curve packs are frozen artifacts.** Pack id, protocol, cohort, judge/rubric ids, and `created_at` are recorded. Loader refuses overlay on incompatible pack version.
6. **No write-back.** Loading a pack never mutates user trips, diary entries, or local curves.
7. **Density honesty.** Overlay shows `n`, pack id, and a one-line caveat. Below min n, show lines only — never a fake band.
8. **Email is out of scope locally.** A `.ics` / todo stub may remind the user to re-run; no outbound mail from the laptop app.

## Diary index schema (v2)

```json
{
  "schema_version": "2",
  "migrated_at": "…",
  "entries": [
    {
      "entry_id": "d-…",
      "raw_prompt_sha256": "…",
      "created_at": "…",
      "tags": [],
      "success_criterion": "",
      "trips": [{"trip_id": "…", "created_at": "…", "note": ""}],
      "first_solved_model_id": null,
      "first_solved_trip_id": null,
      "first_solved_at": null,
      "solved_mark": "unset",
      "reflections": {},
      "preview": "≤40 chars",
      "reruns": [{"trip_id": "…", "created_at": "…", "mode": "tour|full", "cohort_id": "…"}]
    }
  ]
}
```

Migration: a bare JSON list is treated as schema v1 and upgraded in place on first load.

## First-solved timeline

Across diary entries, surface: entry preview, first-solved year/model when known, and earliest user (or judge_v2) mark. Gaps stay gaps. This is a **portfolio timeline**, not a leaderboard.

## Offline curve pack schema (v1)

```json
{
  "pack_id": "curves-pack-v1",
  "pack_kind": "empirical|demonstration",
  "protocol": "local-v2-eval",
  "cohort_id": "decade-v0",
  "judge_id": "…",
  "rubric_id": "judge-rubric-v2",
  "created_at": "…",
  "method_note": "How these curves were produced.",
  "caveat": "Published sample, not all of LLM history.",
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

- `pack_kind: demonstration` means method-demo synthetic curves — never claim empirical LLM history.
- `pack_kind: empirical` means our frozen runs or consenting contributors under a stated protocol.
- Overlay UI must show pack kind and caveat whenever a pack is active.

## Storage

```text
local-data/diary/index.json
local-data/diary/prompts/<entry_id>/{entry.json,raw-prompt.txt}
local-data/curve-packs/<pack_id>.json
local-data/judge-calibration/<calibration_id>/report.json
```

## Out of scope for local-v3-longitudinal

- Live multi-user corpus density (`cloud-v1`).
- Outbound email (`cloud-v1`).
- Treating demonstration packs as global ground truth.
- Silent judge re-scoring on diary re-run.
