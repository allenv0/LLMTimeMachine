"""Visible judge prompt construction (local-v2-eval). No hidden CoT smuggling beyond the rubric."""

from __future__ import annotations

from pathlib import Path

import yaml

from llm_time_machine.artifact_store import sha256_text
from llm_time_machine.errors import RegistryError


def load_rubric(path: Path) -> dict:
    if not path.is_file():
        raise RegistryError(f"rubric not found: {path}")
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict) or "id" not in data:
        raise RegistryError(f"invalid rubric: {path}")
    return data


def load_judge_config(path: Path) -> dict:
    if not path.is_file():
        raise RegistryError(f"judge config not found: {path}")
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict) or "judge_model_id" not in data:
        raise RegistryError(f"invalid judge config: {path}")
    return data


def render_judge_input(
    rubric: dict,
    *,
    raw_prompt: str,
    success_criterion: str,
    model_id: str,
    display_year: int,
    output_text: str,
) -> str:
    criteria_lines = []
    for c in rubric.get("criteria") or []:
        criteria_lines.append(f"- ({c.get('id')}) {c.get('text')}")
    anchors = rubric.get("anchors") or {}
    anchor_lines = [f"  {k}: {v}" for k, v in anchors.items()]
    refuse = "\n".join(f"- {r}" for r in rubric.get("refuse_when") or [])
    contract = (rubric.get("output_contract") or "").strip()
    criterion = success_criterion.strip() if success_criterion else "(none)"
    parse_mode = str(rubric.get("parse_mode") or "text")
    contract_hint = contract
    if parse_mode == "json" and "JSON" not in contract.upper():
        contract_hint = contract + "\nReturn a single JSON object."
    parts = [
        f"You are a strict local quality judge under rubric `{rubric.get('id')}`.",
        "This is an ESTIMATE, not ground truth.",
        "",
        "## Criteria",
        "\n".join(criteria_lines),
        "",
        "## Score anchors",
        "\n".join(anchor_lines),
        "",
        "## Refuse (return UNSCORED) when",
        refuse,
        "",
        "## User prompt",
        raw_prompt,
        "",
        "## Success criterion",
        criterion,
        "",
        f"## Candidate output (historical model {model_id}, {display_year})",
        output_text,
        "",
        "## Output contract",
        contract_hint,
        "",
        "Judge response:",
    ]
    return "\n".join(parts)


def hash_judge_input(text: str) -> str:
    return sha256_text(text)


def parse_judge_reply(text: str) -> tuple[str, int | None, str]:
    """Return (status, score_1_10, reason).

    Supports rubric v2 JSON contract and v1 free-text SCORE/UNSCORED lines.
    Never coerces an unparseable reply into a number.
    """
    if not text or not text.strip():
        return "unscored", None, "empty judge reply"

    stripped = text.strip()
    json_result = _try_parse_json_contract(stripped)
    if json_result is not None:
        return json_result

    for line in text.splitlines():
        s = line.strip()
        if not s:
            continue
        # Strip optional code fences noise around a JSON payload on one line.
        if s.startswith("{") and s.endswith("}"):
            json_result = _try_parse_json_contract(s)
            if json_result is not None:
                return json_result
        upper = s.upper()
        if upper.startswith("SCORE:"):
            rest = s.split(":", 1)[1].strip()
            num = ""
            for ch in rest.split()[0] if rest.split() else "":
                if ch.isdigit():
                    num += ch
                else:
                    break
            digits = "".join(ch for ch in rest if ch.isdigit())
            if not num and digits:
                num = digits[:2]
            try:
                score = int(num)
            except ValueError:
                return "unscored", None, f"unparseable score line: {s[:80]}"
            if score < 1 or score > 10:
                return "unscored", None, f"score out of range: {score}"
            return "scored", score, ""
        if upper == "UNSCORED" or upper.startswith("UNSCORED"):
            if ":" in s:
                reason = s.split(":", 1)[1].strip() or "judge refused"
            else:
                reason = "judge refused (no detail)"
            return "unscored", None, reason
    return "unscored", None, "no SCORE/UNSCORED line in judge reply"


def _try_parse_json_contract(text: str) -> tuple[str, int | None, str] | None:
    """Parse rubric v2 JSON: {"score": n} or {"unscored": reason}."""
    import json
    import re

    candidate = text.strip()
    if candidate.startswith("```"):
        candidate = re.sub(r"^```(?:json)?\s*", "", candidate)
        candidate = re.sub(r"\s*```$", "", candidate).strip()
    # Tolerate a single JSON object embedded in short noise.
    match = re.search(r"\{[^{}]*\}", candidate, flags=re.DOTALL)
    if not match:
        return None
    blob = match.group(0)
    try:
        data = json.loads(blob)
    except json.JSONDecodeError:
        return None
    if not isinstance(data, dict):
        return None
    if "unscored" in data:
        reason = str(data.get("unscored") or "judge refused").strip() or "judge refused"
        return "unscored", None, reason
    if "score" in data:
        raw = data.get("score")
        try:
            score = int(raw)
        except (TypeError, ValueError):
            return "unscored", None, f"unparseable JSON score: {raw!r}"
        if score < 1 or score > 10:
            return "unscored", None, f"score out of range: {score}"
        return "scored", score, ""
    return None
