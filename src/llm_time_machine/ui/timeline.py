"""Decade timetable: holes, substitutes, status-quo, quarantined FUTURE.

Hero rail (Lifeline port, MIT: evilrabbit/lifeline): single horizontal
scroll-scrubbed rail with sticky Years shield, intro draw, hover previews,
live departure dots, and walk-theater playhead. Rendered as a zinc/Geist
contrast island inside the newsprint shell.

The legacy static timetable (`_timetable`) is kept as fallback/audit.
`spine_rows` is the source of truth; `lifeline_markers` is the React-ready
JSON contract both the iframe rail and the future custom component consume.
"""

from __future__ import annotations

from html import escape as _escape

from llm_time_machine.domain import Cohort, ModelSpec
from llm_time_machine.future_ensemble import future_enabled
from llm_time_machine.ui import theme


def spine_rows(cohort: Cohort) -> list[dict]:
    """Chronological slots: models + holes. Status-quo and FUTURE are appended labels."""
    rows: list[dict] = []
    for m in sorted(cohort.models, key=lambda x: (x.display_year, x.id)):
        rows.append(
            {
                "kind": "model",
                "year": m.display_year,
                "label": m.display_name,
                "model_id": m.id,
                "slot_status": m.slot_status,
                "stands_for": m.stands_for,
                "mode": m.mode,
                "limitations": list(m.limitations),
            }
        )
    for h in sorted(cohort.timeline_holes, key=lambda x: x.display_year):
        rows.append(
            {
                "kind": "hole",
                "year": h.display_year,
                "label": "hole",
                "model_id": None,
                "slot_status": "hole",
                "stands_for": h.target_class,
                "mode": "",
                "limitations": [h.reason],
                "reason": h.reason,
                "target_class": h.target_class,
            }
        )
    rows.sort(key=lambda r: (r["year"], 0 if r["kind"] == "model" else 1, r.get("model_id") or ""))
    return rows


# ── Lifeline data contract (React-ready JSON) ──────────────────────────
# Port of evilrabbit/lifeline `defineLifeline({birthYear, endYear,
# milestones})`: every calendar year in range gets a marker so the rail is
# continuous. Years with no model and no declared hole become `gap` —
# faint, never a fake model. Declared holes stay `hole` (dashed).
# Models keep their honesty encoding (substitute vs available).

_LIVE_MAP = {
    "waiting": "waiting",
    "loading": "live",
    "generating": "live",
    "complete": "complete",
    "completed": "complete",
    "failed": "failed",
    "timed_out": "failed",
    "unsupported": "failed",
    "cancelled": "failed",
}


def lifeline_markers(
    cohort: Cohort,
    statuses: dict[str, str] | None = None,
    walk_step: int | None = None,
    walk_ids: list[str] | None = None,
) -> list[dict]:
    """Build Lifeline-style markers for the hero rail.

    React-ready: JSON-serializable, stable keyed by `id`, ordered oldest →
    newest. Both the Streamlit iframe rail and `frontend/lifeline-rail`
    consume this shape verbatim.
    """
    statuses = statuses or {}
    rows = spine_rows(cohort)
    by_year: dict[int, list[dict]] = {}
    for r in rows:
        by_year.setdefault(r["year"], []).append(r)

    if rows:
        birth = min(r["year"] for r in rows)
        end = max(r["year"] for r in rows)
    else:
        birth = end = 0

    if walk_ids is None:
        walk_ids = [m.id for m in sorted(cohort.models, key=lambda x: (x.display_year, x.id))]
    if walk_step is not None:
        walk_step = max(0, min(int(walk_step), len(walk_ids)))
    next_walk_id = walk_ids[walk_step] if walk_step is not None and walk_step < len(walk_ids) else None
    done_walk_ids = set(walk_ids[:walk_step]) if walk_step is not None else set()

    markers: list[dict] = []
    for year in range(birth, end + 1):
        entries = by_year.get(year, [])
        if not entries:
            markers.append(
                {
                    "year": year,
                    "id": f"gap-{year}",
                    "kind": "gap",
                    "label": "—",
                    "mode": "",
                    "slot_status": "gap",
                    "stands_for": "",
                    "limitations": [],
                    "status": "gap",
                    "walk_state": None,
                    "age": year - birth,
                }
            )
            continue
        for r in entries:
            if r["kind"] == "hole":
                markers.append(
                    {
                        "year": year,
                        "id": f"hole-{year}",
                        "kind": "hole",
                        "label": "not staged",
                        "mode": "",
                        "slot_status": "hole",
                        "stands_for": r.get("stands_for") or "",
                        "limitations": list(r.get("limitations") or []),
                        "status": "hole",
                        "walk_state": None,
                        "age": year - birth,
                    }
                )
            else:
                mid = r.get("model_id") or ""
                raw = statuses.get(mid, "waiting")
                live = _LIVE_MAP.get(str(raw), "waiting")
                if walk_step is not None:
                    if mid in done_walk_ids:
                        walk_state: str | None = "done"
                    elif mid == next_walk_id:
                        walk_state = "next"
                    else:
                        walk_state = "upcoming"
                else:
                    walk_state = None
                markers.append(
                    {
                        "year": year,
                        "id": mid or f"model-{year}",
                        "kind": "model",
                        "label": r.get("label") or "",
                        "mode": r.get("mode") or "",
                        "slot_status": r.get("slot_status") or "available",
                        "stands_for": r.get("stands_for") or "",
                        "limitations": list(r.get("limitations") or []),
                        "status": live,
                        "walk_state": walk_state,
                        "age": year - birth,
                    }
                )
    return markers


def lifeline_birth_year(cohort: Cohort) -> int | None:
    rows = spine_rows(cohort)
    return min((r["year"] for r in rows), default=None)


def _stop_title(row: dict) -> str:
    if row["kind"] == "hole":
        return f"{row['year']} hole — {row.get('reason') or row.get('limitations', [''])[0]}"
    bits = [f"{row['year']} {row['label']}", row.get("mode") or ""]
    if row.get("stands_for"):
        bits.append(f"stands for {row['stands_for']}")
    if row.get("limitations"):
        bits.append(row["limitations"][0])
    return " · ".join(b for b in bits if b)


def _timetable(rows: list[dict], now_year: int | None = None, active_year: int | None = None) -> str:
    """Horizontal timetable with optional playhead at now/active year."""
    stops = []
    playhead_html = ""
    n = max(len(rows), 1)
    focus_year = active_year if active_year is not None else now_year
    for i, row in enumerate(rows):
        year = row["year"]
        cls = "tm-stop"
        if row["kind"] == "hole":
            cls += " is-hole"
            name = "not staged"
            meta = "hole"
        else:
            if row["slot_status"] == "substitute":
                cls += " is-sub"
                meta = "sub"
            else:
                meta = "avail"
            name = row["label"]
            if focus_year is not None and year == focus_year:
                cls += " is-now"
        from html import escape

        title = escape(_stop_title(row), quote=True)
        stops.append(
            f'<div class="{cls}" title="{title}" tabindex="0">'
            '<div class="tm-stop-tick"></div>'
            '<div class="tm-stop-dot"></div>'
            f'<div class="tm-stop-year">{year}</div>'
            f'<div class="tm-stop-name">{name}</div>'
            f'<div class="tm-stop-meta">{meta}</div>'
            "</div>"
        )
        if focus_year is not None and year == focus_year:
            left_pct = ((i + 0.5) / n) * 100
            label = "in service" if active_year is not None else "you are here"
            playhead_html = (
                f'<div class="tm-playhead" style="left:{left_pct:.2f}%">'
                f"<span>{label}</span></div>"
            )
    return (
        '<div class="tm-timetable tm-fade">'
        '<div class="tm-track">'
        f"{playhead_html}{''.join(stops)}"
        "</div>"
        "</div>"
    )


def _marker_title(m: dict) -> str:
    if m["kind"] == "hole":
        reason = (m.get("limitations") or [""])[0]
        return f"{m['year']} hole — {reason}"
    if m["kind"] == "gap":
        return f"{m['year']} — no staged checkpoint, no declared hole. Gap stays empty."
    bits = [f"{m['year']} {m['label']}", m.get("mode") or ""]
    if m.get("slot_status") == "substitute":
        bits.append(f"substitute for {m.get('stands_for') or 'an annual frontier class'}")
    if m.get("limitations"):
        bits.append(m["limitations"][0])
    if m.get("walk_state") == "next":
        bits.append("next stop on the decade walk")
    return " · ".join(b for b in bits if b)


def _hero_stop_html(m: dict, index: int, intro: bool) -> str:
    cls = "ll-stop"
    if m["kind"] == "hole":
        cls += " is-hole"
        meta = "hole"
    elif m["kind"] == "gap":
        cls += " is-gap"
        meta = "—"
    else:
        if m.get("slot_status") == "substitute":
            cls += " is-sub"
            meta = "sub"
        else:
            meta = "avail"
    status = m.get("status") or ""
    if status == "live":
        cls += " is-live"
        meta = "live"
    elif status == "complete":
        cls += " is-done" if m.get("walk_state") == "done" else ""
        meta = "done" if m.get("walk_state") == "done" else meta
    elif status == "failed":
        cls += " is-failed"
        meta = "failed"
    walk = m.get("walk_state")
    if walk == "next":
        cls += " is-next"
    elif walk == "done":
        cls += " is-done"
    if intro:
        cls += " ll-marker-intro"
    delay = min(index * 70, 840)
    style = f' style="animation-delay:{delay}ms"' if intro else ""
    title = _escape(_marker_title(m), quote=True)
    name = _escape(m.get("label") or "", quote=False)
    preview_bits: list[str] = []
    if m.get("stands_for"):
        preview_bits.append(_escape(f"Stands for {m['stands_for']}", quote=False))
    if m.get("limitations"):
        preview_bits.append(_escape(m["limitations"][0], quote=False))
    preview = f'<div class="ll-preview">{" · ".join(preview_bits)}</div>' if preview_bits else ""
    flag = ""
    if walk == "next":
        flag = '<span class="ll-flag next">Next</span>'
    elif walk == "done":
        flag = '<span class="ll-flag done">Revealed</span>'
    elif status == "live":
        flag = '<span class="ll-flag live">Running</span>'
    elif status == "failed":
        flag = '<span class="ll-flag failed">Delayed</span>'
    return (
        f'<div class="{cls}" title="{title}" tabindex="0" role="button"'
        f' aria-label="{title}" data-year="{m["year"]}" data-kind="{m["kind"]}"{style}>'
        '<div class="tick"></div>'
        '<div class="ll-dot"></div>'
        f'<div class="ll-year">{m["year"]}</div>'
        f'<div class="ll-name">{name}</div>'
        f'<div class="ll-meta">{meta}</div>'
        f"{flag}{preview}"
        "</div>"
    )


def hero_rail_html(
    cohort: Cohort,
    markers: list[dict],
    *,
    mode: str = "walk",
    active_year: int | None = None,
    intro: bool = True,
    appearance: str = "auto",
) -> str:
    """Standalone iframe document for the hero rail island."""
    stops = "".join(_hero_stop_html(m, i, intro) for i, m in enumerate(markers))
    rail_cls = "ll-rail ll-rail-intro" if intro else "ll-rail solid"
    # Playhead at active year, else at walk-next, else hidden.
    playhead = ""
    focus_id: str | None = None
    if active_year is not None:
        for m in markers:
            if m["year"] == active_year and m["kind"] == "model":
                focus_id = m["id"]
                break
    if focus_id is None:
        for m in markers:
            if m.get("walk_state") == "next":
                focus_id = m["id"]
                break
    if focus_id is not None:
        idx = next((i for i, m in enumerate(markers) if m["id"] == focus_id), 0)
        # shield (92px) + stop width (132px); playhead sits mid-stop.
        px = 92 + idx * 132 + 66
        label = "in service" if active_year is not None else "next stop"
        playhead = f'<div class="ll-playhead" style="left:{px}px"><span>{label}</span></div>'
    years = [m["year"] for m in markers if m["kind"] == "model"]
    span = f"{min(years)}–{max(years)}" if years else ""
    n_holes = sum(1 for m in markers if m["kind"] == "hole")
    n_subs = sum(1 for m in markers if m.get("slot_status") == "substitute")
    endpoint = ""
    if cohort.status_quo is not None:
        endpoint = (
            '<div class="ll-endpoint">'
            f"<strong>{_escape(cohort.status_quo.display_name)}</strong> · "
            f"<code>{_escape(cohort.status_quo.model_id)}</code> — "
            f"{_escape(cohort.status_quo.note)}"
            "</div>"
        )
    future_note = ""
    if cohort.future is not None and not future_enabled(cohort):
        future_note = (
            '<div class="ll-endpoint muted">'
            f"<strong>{_escape(cohort.future.display_name)}</strong> · derailed (off by default) — "
            "Never a calendar year."
            "</div>"
        )
    mode_note = "walk-first · one year at a time" if mode == "walk" else "full trip · all eras"
    body_cls = " class='ll-dark'" if appearance == "dark" else ""
    return (
        "<!DOCTYPE html><html><head><meta charset='utf-8'>"
        "<meta name='viewport' content='width=device-width, initial-scale=1'>"
        f"{theme.lifeline_island_css()}"
        f"{theme.lifeline_island_dark_css(appearance)}"
        f"</head><body{body_cls}><div class='ll-shell'>"
        f"<div class='ll-top'><div class='ll-title'>Time table</div>"
        f"<div class='ll-sub'>{_escape(span)} · {mode_note}</div></div>"
        "<div class='ll-legend'>"
        "<span><i></i>avail</span><span><i class='sub'></i>substitute</span>"
        "<span><i class='hole'></i>hole</span><span><i class='gap'></i>gap</span>"
        "<span><i class='live'></i>running</span>"
        "</div>"
        f"<div class='ll-viewport' id='ll-viewport' tabindex='0' aria-label='Decade rail, {len(markers)} stops'>"
        "<div class='ll-track' id='ll-track'>"
        "<div class='ll-shield" + (" ll-labels-intro" if intro else "") + "'>"
        "<div class='age'>Age</div><div class='years'>Years</div>"
        "<div class='hint'>Scroll sideways · ← → keys work when focused. Holes stay empty.</div>"
        "</div>"
        f"<div class='ll-rail-wrap'><div class='{rail_cls}' id='ll-rail'></div>"
        f"<div class='ll-rail' style='border-top-style:solid;opacity:0.35'></div>"
        f"<div class='ll-markers'>{stops}</div>{playhead}</div>"
        "</div></div>"
        f"<div class='ll-foot'><span>{len(markers)} stops</span>"
        f"<span>{n_holes} holes</span><span>{n_subs} substitutes</span>"
        "<span>sample ≠ frontier</span></div>"
        f"{endpoint}{future_note}"
        "<script>(function(){"
        "var vp=document.getElementById('ll-viewport');"
        "var rail=document.getElementById('ll-rail');"
        "var reduce=window.matchMedia&&window.matchMedia('(prefers-reduced-motion: reduce)').matches;"
        "vp.addEventListener('keydown',function(e){"
        "if(e.key==='ArrowRight'){vp.scrollBy({left:264});e.preventDefault();}"
        "else if(e.key==='ArrowLeft'){vp.scrollBy({left:-264});e.preventDefault();}});"
        "vp.addEventListener('wheel',function(e){"
        "if(Math.abs(e.deltaY)>Math.abs(e.deltaX)&&e.deltaY!==0){"
        "if(vp.scrollWidth>vp.clientWidth+4){"
        "var atStart=vp.scrollLeft<=0&&e.deltaY<0;"
        "var atEnd=vp.scrollLeft+vp.clientWidth>=vp.scrollWidth-2&&e.deltaY>0;"
        "if(!atStart&&!atEnd){vp.scrollLeft+=e.deltaY;e.preventDefault();}}}}"
        ",{passive:false});"
        + (
            "if(rail&&!reduce){var t0=null;function f(t){if(!t0)t0=t;"
            "var p=Math.min((t-t0)/900,1);"
            "rail.style.setProperty('--ll-intro',p.toFixed(3));"
            "if(p<1)requestAnimationFrame(f);}requestAnimationFrame(f);}"
            "else if(rail){rail.style.setProperty('--ll-intro',1);}"
            if intro else "if(rail){rail.style.setProperty('--ll-intro',1);}"
        )
        + "})();</script>"
        "</div></body></html>"
    )


def render_hero_rail(
    st,
    cohort: Cohort,
    *,
    markers: list[dict] | None = None,
    statuses: dict[str, str] | None = None,
    walk_step: int | None = None,
    mode: str = "walk",
    active_year: int | None = None,
    intro: bool = True,
    height: int = 430,
    appearance: str | None = None,
) -> list[dict]:
    """Render the Lifeline hero rail island. Returns markers (React-ready)."""
    if markers is None:
        markers = lifeline_markers(cohort, statuses=statuses, walk_step=walk_step)
    if appearance is None:
        appearance = theme.resolve_appearance()
    doc = hero_rail_html(
        cohort, markers, mode=mode, active_year=active_year, intro=intro, appearance=appearance
    )
    try:
        import streamlit.components.v1 as components

        components.html(doc, height=height, scrolling=True)
    except Exception:
        # Fallback: legacy static timetable never breaks the page.
        rows = spine_rows(cohort)
        st.markdown(_timetable(rows, active_year=active_year), unsafe_allow_html=True)
    return markers


def render_decade_spine(
    st,
    cohort: Cohort,
    now_year: int | None = None,
    active_year: int | None = None,
    *,
    statuses: dict[str, str] | None = None,
    walk_step: int | None = None,
    mode: str = "walk",
) -> None:
    theme.inject(st)
    st.markdown(
        theme.section("Time table", "sample ≠ frontier · holes stay empty"),
        unsafe_allow_html=True,
    )
    st.caption(
        "Board the lineup year by year. Dashed stops are honest holes — never a fake model. "
        "Ochre squares are labeled substitutes. Hover a stop for the station note."
    )
    # Intro plays once per session so Streamlit reruns don't replay the draw.
    try:
        intro = not bool(st.session_state.get("hero_intro_played", False))
    except Exception:
        intro = True
    render_hero_rail(
        st,
        cohort,
        statuses=statuses,
        walk_step=walk_step,
        mode=mode,
        active_year=active_year,
        intro=intro,
    )
    try:
        st.session_state["hero_intro_played"] = True
    except Exception:
        pass
    rows = spine_rows(cohort)

    # Editorial stop notes — ledger: one station per block, year gutter +
    # stacked lines (name, stands-for, limits). Never run on in one line.
    from html import escape as _esc

    mode_label = {"base_continuation": "Base", "instruction": "Instruction", "chat": "Chat"}
    notes_html: list[str] = []
    for row in rows:
        year = _esc(str(row["year"]))
        if row["kind"] == "hole":
            target = _esc(row["stands_for"] or "an annual frontier class")
            reason = _esc((row["limitations"] or [""])[0])
            notes_html.append(
                f'<div class="tm-stop-note is-hole">'
                f'<div class="tm-stop-note-year">{year}</div>'
                f'<div class="tm-stop-note-body">'
                f'<span class="tm-stop-note-name">Not staged</span>'
                f'<span class="tm-stop-note-chips">{theme.badge("Hole", "hole")}</span>'
                f'<div class="tm-stop-note-sub">Would have been <strong>{target}</strong>.</div>'
                f'<div class="tm-stop-note-sub">{reason}</div>'
                f"</div>"
                f"</div>"
            )
        else:
            chip = (
                theme.badge("Sub", "accent")
                if row["slot_status"] == "substitute"
                else theme.badge("Avail", "ink")
            )
            name = _esc(row["label"] or "")
            mode = _esc(mode_label.get(row.get("mode") or "", row.get("mode") or ""))
            subs: list[str] = []
            if row.get("stands_for"):
                subs.append(
                    f'<div class="tm-stop-note-sub">Stands for <strong>{_esc(row["stands_for"])}</strong>.</div>'
                )
            for lim_text in (row.get("limitations") or [])[:2]:
                subs.append(f'<div class="tm-stop-note-sub">{_esc(lim_text)}</div>')
            notes_html.append(
                f'<div class="tm-stop-note">'
                f'<div class="tm-stop-note-year">{year}</div>'
                f'<div class="tm-stop-note-body">'
                f'<span class="tm-stop-note-name">{name}</span>'
                f'<span class="tm-stop-note-chips">{chip} {theme.badge(mode, "")}</span>'
                f'{"".join(subs)}'
                f"</div>"
                f"</div>"
            )

    endpoints = []
    if cohort.status_quo is not None:
        endpoints.append(
            f'<div class="tm-endpoint">'
            f'{theme.badge("Now", "accent")} '
            f'<strong>{cohort.status_quo.display_name}</strong> · '
            f'<code>{cohort.status_quo.model_id}</code><br>'
            f'<span class="tm-meta">{cohort.status_quo.note}</span>'
            f"</div>"
        )
    if cohort.future is not None:
        if future_enabled(cohort):
            endpoints.append(
                f'<div class="tm-endpoint">'
                f'{theme.badge("Future", "ink")} '
                f'<strong>{cohort.future.display_name}</strong> — quarantined synthetic<br>'
                f'<span class="tm-meta">{cohort.future.quarantine_note}</span>'
                f"</div>"
            )
        else:
            endpoints.append(
                f'<div class="tm-endpoint is-muted">'
                f'{theme.badge("Future", "hole")} '
                f'<strong>{cohort.future.display_name}</strong> · derailed (off by default)<br>'
                f'<span class="tm-meta">Never a calendar year. First-solved only with opt-in.</span>'
                f"</div>"
            )

    st.markdown(theme.rule(), unsafe_allow_html=True)
    st.markdown(theme.kicker("Stop notes"), unsafe_allow_html=True)
    n_models = sum(1 for r in rows if r["kind"] == "model")
    n_holes = sum(1 for r in rows if r["kind"] == "hole")
    st.caption(f"{n_models} running stops · {n_holes} honest holes — oldest first.")
    st.markdown(
        f'<div class="tm-stop-notes">{"".join(notes_html)}</div>',
        unsafe_allow_html=True,
    )
    if endpoints:
        st.markdown(
            f'<div class="tm-endpoints">{"".join(endpoints)}</div>',
            unsafe_allow_html=True,
        )


def render_slot_badge(st, spec: ModelSpec) -> None:
    if spec.slot_status == "substitute":
        st.markdown(
            f'{theme.badge("Sub", "accent")} stand-in for '
            f'{spec.stands_for or "an annual frontier class"}',
            unsafe_allow_html=True,
        )
    elif spec.slot_status == "available":
        st.caption("Slot status: available (named checkpoint)")
