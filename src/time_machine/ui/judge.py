"""Judge UI: explicit score action, experimental banner, estimated curve."""

from __future__ import annotations

from time_machine.domain import JudgeScore, TripManifest
from time_machine.evaluation_judge import BANNER, JudgeService
from time_machine.ui import theme


def render_judge_banner(st) -> None:
    st.warning(BANNER)


def render_estimated_curve(st, scores: list[JudgeScore]) -> None:
    theme.inject(st)
    st.markdown(
        theme.section("Estimated quality", "judge · not ground truth"),
        unsafe_allow_html=True,
    )
    render_judge_banner(st)
    if not scores:
        st.info(
            "No judge scores yet. Use **Score with local judge (experimental)**. "
            "Unscored and failed runs stay gaps — we never invent numbers."
        )
        return

    scored = [s for s in scores if s.status == "scored" and s.score_1_10 is not None]
    unscored = [s for s in scores if s.status != "scored"]
    st.caption(
        f"Protocol `local-v2-eval` · rubric `{scores[0].rubric_id}` · "
        f"judge `{scores[0].judge_model_id}` · scored {len(scored)} / {len(scores)}"
    )

    cols = st.columns([2, 1, 2, 2])
    cols[0].markdown("**Year · model**")
    cols[1].markdown("**Score**")
    cols[2].markdown("**Status**")
    cols[3].markdown("**Note**")
    for s in sorted(scores, key=lambda x: (x.display_year or 0, x.model_id)):
        c = st.columns([2, 1, 2, 2])
        y = s.display_year or "?"
        c[0].write(f"{y} · {s.model_id}")
        if s.status == "scored":
            c[1].write(f"**{s.score_1_10}/10**")
        else:
            c[1].write("—")
        c[2].write(s.status)
        c[3].caption(s.unscored_reason or s.judge_model_id)

    if scored:
        st.markdown(_svg_estimated(scored), unsafe_allow_html=True)
        n_s = len(scored)
        n_u = len(unscored)
        st.markdown(theme.coverage_bar(n_s, n_u), unsafe_allow_html=True)
        st.markdown(
            theme.figure_caption(
                3,
                f"Estimated 1–10 over time · scored {n_s} / refused {n_u}. "
                "ESTIMATE under a versioned rubric — not ground truth.",
            ),
            unsafe_allow_html=True,
        )
        st.markdown(theme.legend(("est", "Judge estimate"), ("pack", "Gaps = unscored")), unsafe_allow_html=True)
    else:
        st.markdown(
            theme.empty_state("No estimates filed — refuse is better than invent."),
            unsafe_allow_html=True,
        )


def _svg_estimated(scored: list[JudgeScore]) -> str:
    w, h = 640, 150
    pad_l, pad_r, pad_t, pad_b = 36, 16, 16, 28
    pts = sorted(scored, key=lambda s: (s.display_year or 0, s.model_id))
    years = [s.display_year or 0 for s in pts]
    y0, y1 = min(years), max(years)
    if y0 == y1:
        y1 = y0 + 1

    def x_of(year: int) -> float:
        return pad_l + (year - y0) / (y1 - y0) * (w - pad_l - pad_r)

    def y_of(score: int) -> float:
        t = (score - 1) / 9.0
        return pad_t + (1 - t) * (h - pad_t - pad_b)

    coords = " ".join(
        f"{x_of(s.display_year or 0):.1f},{y_of(int(s.score_1_10 or 1)):.1f}" for s in pts
    )
    dots = []
    for s in pts:
        x = x_of(s.display_year or 0)
        y = y_of(int(s.score_1_10 or 1))
        dots.append(
            f'<circle cx="{x:.1f}" cy="{y:.1f}" r="4" fill="#6b4c9a"/>'
            f'<text x="{x:.1f}" y="{y - 8:.1f}" text-anchor="middle" font-size="11" fill="#1a1a1a">'
            f"{s.display_year}:{s.score_1_10}</text>"
        )
    return (
        f'<svg viewBox="0 0 {w} {h}" xmlns="http://www.w3.org/2000/svg" '
        f'font-family="-apple-system, sans-serif" style="max-width:100%;height:auto;">'
        f'<text x="8" y="{y_of(10) + 4}" font-size="10" fill="#666">10</text>'
        f'<text x="8" y="{y_of(5) + 4}" font-size="10" fill="#666">5</text>'
        f'<text x="8" y="{y_of(1) + 4}" font-size="10" fill="#666">1</text>'
        + (f'<polyline points="{coords}" fill="none" stroke="#6b4c9a" stroke-width="2"/>' if len(pts) >= 2 else "")
        + "".join(dots)
        + f'<text x="{w/2}" y="{h-6}" text-anchor="middle" font-size="10" fill="#666">year → estimated score</text>'
        f"</svg>"
    )


def render_score_action(
    st,
    judge: JudgeService,
    store,
    manifest: TripManifest,
) -> list[JudgeScore] | None:
    st.markdown("**Machine estimate (opt-in)**")
    render_judge_banner(st)
    with st.expander("Rubric and judge pin (visible)", expanded=False):
        st.write(f"Judge: `{judge.judge_cfg.get('judge_display_name')}`")
        st.write(f"Judge model id: `{judge.judge_cfg.get('judge_model_id')}`")
        st.write(f"Rubric: `{judge.rubric.get('id')}`")
        st.code(judge.rubric_text(), language="yaml")
        st.caption("Limitations: " + "; ".join(judge.judge_cfg.get("limitations") or []))

    if st.button("Score with local judge (experimental)", key="judge-score-btn"):
        with st.spinner("Scoring with local judge…"):
            try:
                scores = judge.score_trip(store, manifest.trip_id)
            except Exception as exc:
                st.error(f"Judge scoring failed: {exc}")
                return None
        st.success(f"Scored {len(scores)} run(s). Review the estimated curve — not ground truth.")
        return scores

    existing = judge.read_scores(manifest.trip_id)
    if existing:
        st.caption(f"{len(existing)} stored judge score record(s) for this trip.")
    return existing or None
