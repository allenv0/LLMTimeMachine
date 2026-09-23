"""Progress curve + local portfolio charts (human ordinal, Track A)."""

from __future__ import annotations

from time_machine.domain import Cohort, CurvePoint, TripManifest
from time_machine.curves import (
    CURVE_CAPTION,
    ORDINAL_LABELS,
    build_trip_curve,
    portfolio_series,
)


def _sparkline_ascii(points: list[CurvePoint]) -> str:
    if not points:
        return "(no rated points yet)"
    glyphs = {-2: "▁", -1: "▂", 0: "▃", 1: "▄", 2: "▅"}
    # map -2..2 → low..high blocks
    blocks = {-2: "▁", -1: "▂", 0: "▄", 1: "▆", 2: "█"}
    return "".join(blocks.get(p.ordinal, "?") for p in points)


def render_trip_curve(st, cohort: Cohort, manifest: TripManifest, annotations) -> list[CurvePoint]:
    points = build_trip_curve(manifest, annotations, cohort=cohort)
    st.subheader("Progress curve (your ratings)")
    st.caption(CURVE_CAPTION)
    if not points:
        st.info(
            "No rated models yet. Rate outputs with the −2..+2 quality control "
            "(or usefulness) and save annotations to draw this curve. "
            "Unrated models stay gaps — we do not invent scores."
        )
        return points

    st.markdown(f"**Trip series:** `{_sparkline_ascii(points)}`")
    # simple table chart (text-summary accessible)
    cols = st.columns([2, 1, 1, 2])
    cols[0].markdown("**Year · model**")
    cols[1].markdown("**Ordinal**")
    cols[2].markdown("**Source**")
    cols[3].markdown("**Meaning**")
    for p in points:
        c = st.columns([2, 1, 1, 2])
        c[0].write(f"{p.display_year} · {p.display_name or p.model_id}")
        c[1].write(f"`{p.ordinal:+d}`")
        c[2].write(p.source)
        c[3].caption(ORDINAL_LABELS.get(p.ordinal, ""))

    # lightweight SVG polyline
    st.markdown(_svg_curve(points), unsafe_allow_html=True)
    st.caption(
        "Horizontal = display year. Vertical = your ordinal (−2 much worse … +2 much better). "
        "Gaps are missing ratings."
    )
    return points


def _svg_curve(points: list[CurvePoint]) -> str:
    if len(points) < 1:
        return ""
    w, h = 640, 140
    pad_l, pad_r, pad_t, pad_b = 40, 20, 16, 28
    years = [p.display_year for p in points]
    y0, y1 = min(years), max(years)
    if y0 == y1:
        y1 = y0 + 1

    def x_of(year: int) -> float:
        return pad_l + (year - y0) / (y1 - y0) * (w - pad_l - pad_r)

    def y_of(ord_: int) -> float:
        # -2 bottom, +2 top
        t = (ord_ + 2) / 4.0
        return pad_t + (1 - t) * (h - pad_t - pad_b)

    coords = " ".join(f"{x_of(p.display_year):.1f},{y_of(p.ordinal):.1f}" for p in points)
    dots = []
    for p in points:
        dots.append(
            f'<circle cx="{x_of(p.display_year):.1f}" cy="{y_of(p.ordinal):.1f}" r="4" fill="#2f6f4e"/>'
            f'<text x="{x_of(p.display_year):.1f}" y="{y_of(p.ordinal) - 8:.1f}" text-anchor="middle" '
            f'font-size="11" fill="#1a1a1a">{p.display_year}</text>'
        )
    mid_y = y_of(0)
    return (
        f'<svg viewBox="0 0 {w} {h}" xmlns="http://www.w3.org/2000/svg" '
        f'font-family="-apple-system, sans-serif" style="max-width:100%;height:auto;">'
        f'<line x1="{pad_l}" y1="{mid_y}" x2="{w - pad_r}" y2="{mid_y}" stroke="#ccc" stroke-width="1"/>'
        f'<text x="8" y="{y_of(2) + 4}" font-size="10" fill="#666">+2</text>'
        f'<text x="8" y="{y_of(0) + 4}" font-size="10" fill="#666">0</text>'
        f'<text x="8" y="{y_of(-2) + 4}" font-size="10" fill="#666">-2</text>'
        + (
            f'<polyline points="{coords}" fill="none" stroke="#2f6f4e" stroke-width="2"/>'
            if len(points) >= 2
            else ""
        )
        + "".join(dots)
        + f'<text x="{w / 2}" y="{h - 6}" text-anchor="middle" font-size="10" fill="#666">year →</text>'
        f"</svg>"
    )


def render_portfolio(st, series_by_entry: dict[str, list[CurvePoint]]) -> None:
    st.subheader("Your prompt portfolio")
    data = portfolio_series(series_by_entry)
    st.caption(data["caption"])
    n = data["n_prompts"]
    if n == 0:
        st.info("Register diary prompts and rate outputs to build a local portfolio.")
        return
    st.write(f"Rated prompts with curves: **{n}**")
    if not data["show_band"]:
        st.warning(
            "Fewer than 5 rated prompts — showing individual lines only. "
            "A density band needs more mass to be meaningful."
        )
    else:
        st.markdown("**Local band (median / min / max by year)**")
        for row in data["band"]:
            st.write(
                f"{row['year']}: n={row['n']} median `{row['median']:+d}` "
                f"range `{row['min']:+d}`…`{row['max']:+d}`"
            )
    st.markdown("This is *your* portfolio, not global LLM progress.")


def render_decade_walk_script(st, script: list[dict]) -> None:
    st.subheader("Decade walk (simulated lived timeline)")
    st.caption(
        "One year at a time with a reflection pause. "
        "This is theater over real checkpoints — not calendar time. "
        "Newer is not always better."
    )
    for row in script:
        st.write(
            f"**{row['year']}** · {row['name']} · `{row['mode']}` — "
            + ("; ".join(row.get("limitations") or [])[:120])
        )
