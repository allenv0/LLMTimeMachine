"""Decade timetable: holes, substitutes, status-quo, quarantined FUTURE.

Rendered as a time-machine train timetable (ticks, dots, playhead) with
newspaper type — not a chip cloud.
"""

from __future__ import annotations

from time_machine.domain import Cohort, ModelSpec
from time_machine.future_ensemble import future_enabled
from time_machine.ui import theme


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


def render_decade_spine(
    st,
    cohort: Cohort,
    now_year: int | None = None,
    active_year: int | None = None,
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
    rows = spine_rows(cohort)
    st.markdown(
        _timetable(rows, now_year=now_year, active_year=active_year),
        unsafe_allow_html=True,
    )

    # Editorial stop notes — full-width newspaper grid (not a narrow stack)
    notes_html: list[str] = []
    for row in rows:
        if row["kind"] == "hole":
            notes_html.append(
                f'<div class="tm-hole-line">'
                f'{theme.badge(str(row["year"]), "hole")} '
                f'{theme.badge("Hole", "hole")} '
                f'to <strong>{row["stands_for"]}</strong> — {row["limitations"][0]}'
                f"</div>"
            )
        else:
            chip = (
                theme.badge("Sub", "accent")
                if row["slot_status"] == "substitute"
                else theme.badge("Avail", "ink")
            )
            stands = (
                f' · stands for <strong>{row["stands_for"]}</strong>'
                if row.get("stands_for")
                else ""
            )
            lim = f'<div class="tm-meta">{" · ".join(row["limitations"][:2])}</div>' if row["limitations"] else ""
            notes_html.append(
                f'<div class="tm-model-line">'
                f'{theme.badge(str(row["year"]))} '
                f'<strong>{row["label"]}</strong> {chip} '
                f'· <span style="color:#6B6560">{row["mode"]}</span>{stands}'
                f"{lim}"
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
