"""Judge calibration report: show bias vs a small human-labeled set. Never silently fix scores."""

from __future__ import annotations

import json
from pathlib import Path
from statistics import mean

from llm_time_machine.config import AppPaths
from llm_time_machine.errors import ArtifactError

# Compact gold-ish set (human 1-10). Reporting only — never used to rewrite judge scores.
# Keep small and local; expand deliberately. 24 items cover easy/hard/private/refusal shapes.
DEFAULT_CALIBRATION = [
    {"id": "cal-01", "human_1_10": 9, "kind": "easy_factual", "note": "capital of France"},
    {"id": "cal-02", "human_1_10": 2, "kind": "wrong_confident", "note": "fabricated citation"},
    {"id": "cal-03", "human_1_10": 1, "kind": "incoherent", "note": "token salad"},
    {"id": "cal-04", "human_1_10": 8, "kind": "instruction", "note": "clear short how-to"},
    {"id": "cal-05", "human_1_10": 5, "kind": "partial", "note": "half the constraints"},
    {"id": "cal-06", "human_1_10": 3, "kind": "irrelevant", "note": "topic drift"},
    {"id": "cal-07", "human_1_10": 7, "kind": "code_small", "note": "correct tiny function"},
    {"id": "cal-08", "human_1_10": 4, "kind": "code_bug", "note": "off-by-one"},
    {"id": "cal-09", "human_1_10": 10, "kind": "excellent", "note": "complete + caveats"},
    {"id": "cal-10", "human_1_10": 6, "kind": "ok_style", "note": "right but rambling"},
    {"id": "cal-11", "human_1_10": 2, "kind": "private_hallucinate", "note": "invents grandma clue"},
    {"id": "cal-12", "human_1_10": 8, "kind": "private_refuse", "note": "says cannot know"},
    {"id": "cal-13", "human_1_10": 7, "kind": "svg_attempt", "note": "valid but crude SVG"},
    {"id": "cal-14", "human_1_10": 3, "kind": "svg_prose", "note": "describes SVG only"},
    {"id": "cal-15", "human_1_10": 9, "kind": "reasoning", "note": "multi-step correct"},
    {"id": "cal-16", "human_1_10": 4, "kind": "reasoning_gap", "note": "skips middle step"},
    {"id": "cal-17", "human_1_10": 6, "kind": "translation", "note": "adequate"},
    {"id": "cal-18", "human_1_10": 2, "kind": "translation_bad", "note": "wrong language"},
    {"id": "cal-19", "human_1_10": 8, "kind": "summarize", "note": "faithful abstract"},
    {"id": "cal-20", "human_1_10": 5, "kind": "summarize_pad", "note": "boilerplate heavy"},
    {"id": "cal-21", "human_1_10": 1, "kind": "refusal_unneeded", "note": "refuses easy task"},
    {"id": "cal-22", "human_1_10": 7, "kind": "creative", "note": "tight short poem"},
    {"id": "cal-23", "human_1_10": 3, "kind": "creative_cliche", "note": "generic filler"},
    {"id": "cal-24", "human_1_10": 9, "kind": "constraint_rich", "note": "honors all limits"},
]


def calibration_path(paths: AppPaths, calibration_id: str = "gold-v1") -> Path:
    return paths.judge_calibration_dir / calibration_id / "report.json"


def build_report(
    judgments: list[dict],
    *,
    calibration_id: str = "gold-v1",
    judge_id: str = "",
    rubric_id: str = "",
) -> dict:
    """Compare judge outputs to human gold. Bias is reported, never corrected.

    Each judgment: {id, status, score_1_10, unscored_reason}
    """
    gold = {row["id"]: row for row in DEFAULT_CALIBRATION}
    rows = []
    deltas = []
    scored_n = 0
    unscored_n = 0
    for j in judgments:
        gid = j.get("id")
        g = gold.get(gid)
        if not g:
            continue
        status = j.get("status") or "unscored"
        score = j.get("score_1_10")
        human = g["human_1_10"]
        delta = None
        if status == "scored" and score is not None:
            scored_n += 1
            delta = int(score) - int(human)
            deltas.append(delta)
        else:
            unscored_n += 1
        rows.append(
            {
                "id": gid,
                "kind": g.get("kind"),
                "human_1_10": human,
                "judge_status": status,
                "judge_score_1_10": score,
                "delta": delta,
                "unscored_reason": j.get("unscored_reason") or "",
            }
        )
    bias = None
    if deltas:
        bias = {
            "mean_delta": mean(deltas),
            "n_scored": len(deltas),
            "exact_match_rate": sum(1 for d in deltas if d == 0) / len(deltas),
            "within_1_rate": sum(1 for d in deltas if abs(d) <= 1) / len(deltas),
        }
    return {
        "calibration_id": calibration_id,
        "judge_id": judge_id,
        "rubric_id": rubric_id,
        "n_items": len(rows),
        "n_scored": scored_n,
        "n_unscored": unscored_n,
        "coverage_rate": (scored_n / len(rows)) if rows else 0.0,
        "bias": bias,
        "note": (
            "Calibration reports judge bias vs human gold. "
            "It never silently rewrites judge scores."
        ),
        "rows": rows,
    }


def write_report(paths: AppPaths, report: dict, calibration_id: str = "gold-v1") -> Path:
    path = calibration_path(paths, calibration_id)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return path


def read_report(paths: AppPaths, calibration_id: str = "gold-v1") -> dict | None:
    path = calibration_path(paths, calibration_id)
    if not path.is_file():
        return None
    return json.loads(path.read_text(encoding="utf-8"))


def heuristic_gold_for_tests() -> list[dict]:
    """Deterministic stand-in judgments for unit tests (no model load)."""
    out = []
    for row in DEFAULT_CALIBRATION:
        human = row["human_1_10"]
        if row["kind"] in {"private_hallucinate", "wrong_confident"}:
            out.append(
                {
                    "id": row["id"],
                    "status": "scored",
                    "score_1_10": min(10, human + 2),
                    "unscored_reason": "",
                }
            )
        elif row["kind"] in {"private_refuse", "refusal_unneeded"}:
            out.append(
                {
                    "id": row["id"],
                    "status": "unscored",
                    "score_1_10": None,
                    "unscored_reason": "judge refused",
                }
            )
        else:
            out.append(
                {
                    "id": row["id"],
                    "status": "scored",
                    "score_1_10": human,
                    "unscored_reason": "",
                }
            )
    return out
