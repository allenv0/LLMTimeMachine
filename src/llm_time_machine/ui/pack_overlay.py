"""Curve pack overlay UI: my bold line vs pack spaghetti + median/IQR band."""

from __future__ import annotations

from pathlib import Path

from llm_time_machine.curves_pack import (
    PACK_CAVEAT,
    discover_packs,
    export_compare_pack,
    load_pack,
    make_demonstration_pack,
    pack_overlay,
    save_pack,
)
from llm_time_machine.ui import theme


def render_pack_overlay(st, paths, my_points: list[dict], trip_id: str = "") -> None:
    theme.inject(st)
    st.markdown(
        theme.section("Against the world?", "pack sample · not all of LLM history"),
        unsafe_allow_html=True,
    )
    st.caption(
        "Your curve vs a published sample (or demonstration pack). "
        "Pack kind and n are always shown."
    )

    if st.button("Install demonstration pack (method demo only)", key="pack-demo"):
        pack = make_demonstration_pack()
        save_pack(paths, pack)
        st.success(f"Installed `{pack.pack_id}` (demonstration). Synthetic — not empirical.")
        st.rerun()

    pack_paths = discover_packs(paths)
    if not pack_paths:
        st.markdown(
            theme.empty_state(
                "No pack loaded — install the demonstration pack or drop a curves-pack-v1.json."
            ),
            unsafe_allow_html=True,
        )
        return

    labels = [p.name for p in pack_paths]
    idx = st.selectbox("Curve pack", range(len(pack_paths)), format_func=lambda i: labels[i])
    try:
        pack = load_pack(pack_paths[idx])
    except Exception as exc:
        st.error(f"Refusing pack overlay: {exc}")
        return

    if pack.pack_kind == "demonstration":
        st.warning(
            "**DEMONSTRATION pack** — synthetic curves for method demo. "
            "Do not treat as empirical LLM history."
        )
    overlay = pack_overlay(pack)

    st.markdown(f"**{overlay['caption']}**")
    st.caption(overlay["method_note"] or PACK_CAVEAT)
    st.write(f"Curves in pack: **{overlay['n_curves']}** · band: "
             f"{'shown' if overlay['show_band'] else f'hidden (need n≥{overlay['min_band_n']})'}")

    # Text summary first (a11y).
    st.markdown("**Text summary**")
    st.write(overlay["a11y_summary"])

    st.markdown(_svg_overlay(my_points, overlay), unsafe_allow_html=True)
    st.markdown(
        theme.figure_caption(
            4,
            "Thin lines = pack · bold green = yours · band = median/IQR when n is large enough. Gaps stay gaps.",
        ),
        unsafe_allow_html=True,
    )
    st.markdown(
        theme.legend(
            ("human", "Yours"),
            ("pack", "Pack lines"),
            ("est", "Pack median"),
        ),
        unsafe_allow_html=True,
    )

    if st.button("Export compare pack", key="pack-export"):
        out = export_compare_pack(
            my_points=my_points,
            pack=pack,
            trip_id=trip_id,
            out_path=Path(paths.local_data_dir) / f"compare-pack-{trip_id or 'session'}.json",
        )
        st.success(f"Wrote `{out}`")


def _svg_overlay(my_points: list[dict], overlay: dict) -> str:
    w, h = 680, 220
    pad_l, pad_r, pad_t, pad_b = 40, 16, 16, 28
    years = [row["year"] for row in overlay.get("band") or []]
    for line in overlay.get("lines") or []:
        for p in line.get("points") or []:
            years.append(int(p["year"]))
    for p in my_points:
        if "display_year" in p:
            years.append(int(p["display_year"]))
        elif "year" in p:
            years.append(int(p["year"]))
    if not years:
        return ""
    y0, y1 = min(years), max(years)
    if y0 == y1:
        y1 = y0 + 1

    def x_of(year: int) -> float:
        return pad_l + (year - y0) / (y1 - y0) * (w - pad_l - pad_r)

    def y10(score: float) -> float:
        t = (score - 1) / 9.0
        return pad_t + (1 - t) * (h - pad_t - pad_b)

    def y2(ord_: float) -> float:
        t = (ord_ + 2) / 4.0
        return pad_t + (1 - t) * (h - pad_t - pad_b)

    parts = [
        f'<svg class="tm-chart" viewBox="0 0 {w} {h}" xmlns="http://www.w3.org/2000/svg" '
        f'font-family="-apple-system, sans-serif" style="max-width:100%;height:auto;">',
        f'<text class="t-axis" x="8" y="{y10(10) + 4}" font-size="10">10</text>',
        f'<text class="t-axis" x="8" y="{y10(5) + 4}" font-size="10">5</text>',
        f'<text class="t-axis" x="8" y="{y10(1) + 4}" font-size="10">1</text>',
    ]

    # IQR band
    band = overlay.get("band") or []
    if overlay.get("show_band") and len(band) >= 2:
        upper = " ".join(f"{x_of(b['year']):.1f},{y10(float(b['q3'])):.1f}" for b in band)
        lower = " ".join(
            f"{x_of(b['year']):.1f},{y10(float(b['q1'])):.1f}" for b in reversed(band)
        )
        parts.append(
            f'<polygon class="s-band" points="{upper} {lower}" stroke="none"/>'
        )
        med = " ".join(f"{x_of(b['year']):.1f},{y10(float(b['median'])):.1f}" for b in band)
        parts.append(
            f'<polyline class="s-est" points="{med}" fill="none" stroke-width="1.5" stroke-dasharray="4 2"/>'
        )

    # Pack spaghetti
    for line in (overlay.get("lines") or [])[:40]:
        pts = line.get("points") or []
        if len(pts) < 2:
            continue
        coords = " ".join(
            f"{x_of(int(p['year'])):.1f},{y10(float(p['score_1_10'])):.1f}" for p in pts
        )
        parts.append(
            f'<polyline class="s-pack" points="{coords}" fill="none" stroke-width="1" stroke-opacity="0.45"/>'
        )

    # My line (map ordinal -2..2 to 1..10 band if needed, else use score_1_10)
    my_coords = []
    for p in my_points:
        year = int(p.get("display_year", p.get("year", 0)))
        if "score_1_10" in p and p["score_1_10"] is not None:
            score = float(p["score_1_10"])
            yy = y10(score)
        else:
            ord_ = float(p.get("ordinal", 0))
            yy = y2(ord_)
        my_coords.append(f"{x_of(year):.1f},{yy:.1f}")
    if len(my_coords) >= 2:
        parts.append(
            f'<polyline class="s-human" points="{" ".join(my_coords)}" fill="none" stroke-width="2.5"/>'
        )
    for coord in my_coords:
        x_s, y_s = coord.split(",")
        parts.append(f'<circle class="s-human" cx="{x_s}" cy="{y_s}" r="4"/>')

    parts.append(
        f'<text class="t-axis" x="{w / 2}" y="{h - 6}" text-anchor="middle" font-size="10">'
        f"year → (pack scores 1–10; your line may be ordinal −2…+2)</text>"
    )
    parts.append("</svg>")
    return "".join(parts)
