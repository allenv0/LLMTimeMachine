"""Prompt form with validation and starter prompts."""

from __future__ import annotations

import json
import re
from pathlib import Path

from time_machine.domain import Cohort
from time_machine.errors import InputUnsupportedError

_NON_ASCII_RE = re.compile(r"[^\x00-\x7F]")


def load_starter_prompts(path: Path) -> list[dict]:
    if not path.is_file():
        return []
    items = []
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line:
            continue
        items.append(json.loads(line))
    return items


def looks_non_english(text: str) -> bool:
    # Heuristic warning only — protocol does not promise multilingual comparability.
    if _NON_ASCII_RE.search(text):
        return True
    return False


def validate_prompt_text(text: str, max_chars: int) -> str | None:
    if not text or not text.strip():
        return "Prompt must not be empty or whitespace-only."
    if len(text) > max_chars:
        return f"Prompt is {len(text)} characters; maximum is {max_chars}."
    return None


def render_prompt_form(st, cohort: Cohort, starter_path: Path):
    """Return (raw_prompt, success_criterion, trip_scope).

    trip_scope is ``"full"``, ``"tour"``, or ``""`` when not running.
    """
    starters = load_starter_prompts(starter_path)
    st.subheader("Your prompt")
    st.caption("Your own unusual prompt is more informative than any starter prompt.")

    starter_label = "Write your own"
    labels = [starter_label] + [
        f"{s['category']} — {s['prompt'][:48]}…" if len(s["prompt"]) > 52 else f"{s['category']} — {s['prompt']}"
        for s in starters
    ]
    choice = st.selectbox("Starter prompts (optional)", labels, index=0)
    default_prompt = ""
    for s in starters:
        if choice.endswith(s["prompt"][:48] + "…") or choice.endswith(s["prompt"]):
            default_prompt = s["prompt"]
            break
        if choice.startswith(s["category"]):
            default_prompt = s["prompt"]
            break

    prompt = st.text_area(
        "Prompt (English supported path)",
        value=default_prompt,
        height=160,
        max_chars=None,
        help=f"Maximum {cohort.prompt.max_chars} characters. Preserved exactly.",
    )
    st.caption(f"`{len(prompt)}` / {cohort.prompt.max_chars} characters")

    if prompt and looks_non_english(prompt):
        st.warning(
            "Non-English text detected. local-v1 does not promise comparable multilingual behavior."
        )

    criterion = st.text_input(
        "Optional success criterion",
        placeholder="What would a good answer accomplish?",
    )

    err = validate_prompt_text(prompt, cohort.prompt.max_chars) if prompt or True else None
    # show live error only after interaction
    if prompt is not None and (prompt.strip() or len(prompt) > cohort.prompt.max_chars):
        err = validate_prompt_text(prompt, cohort.prompt.max_chars)
    else:
        err = None

    # cohort / generation profile read-only
    gen = cohort.generation_profiles[cohort.generation_profile_id]
    with st.expander("Selected cohort and generation profile (read-only)", expanded=False):
        for m in cohort.models:
            st.write(f"{m.display_year} · {m.display_name} · {m.mode} · adapter `{m.adapter_id}`")
        st.json(gen.model_dump(mode="json"))

    st.markdown("**Trip scope**")
    col_full, col_tour = st.columns(2)
    full_clicked = col_full.button(
        "Run full trip",
        type="primary",
        disabled=bool(err),
        use_container_width=True,
        help="Every model in the frozen cohort, oldest → newest.",
    )
    tour_clicked = col_tour.button(
        "Quick three-era tour",
        disabled=bool(err),
        use_container_width=True,
        help="Three stops only: base → instruction → chat.",
    )
    if err and (full_clicked or tour_clicked):
        st.error(err)
    if err and prompt.strip():
        st.error(err)
    if full_clicked and not err:
        return prompt, criterion, "full"
    if tour_clicked and not err:
        return prompt, criterion, "tour"
    return prompt, criterion, ""
