"""Landing: newsprint masthead + disclosure note."""

from __future__ import annotations

from pathlib import Path

from time_machine.config import (
    APP_NAME,
    APP_TAGLINE,
    DISCLOSURE_LINES,
    TRUTHFUL_CLAIM,
)
from time_machine.domain import Cohort
from time_machine.ui import theme


def render_landing(st, protocol_path: Path, cohort: Cohort) -> None:
    theme.inject(st)
    st.markdown(
        theme.masthead(APP_NAME, [], deck=APP_TAGLINE),
        unsafe_allow_html=True,
    )
    st.caption(TRUTHFUL_CLAIM)

    lines = "".join(f"<li>{line}</li>" for line in DISCLOSURE_LINES)
    st.markdown(
        theme.note_block(
            "<strong>Before you board</strong>"
            f"<ul>{lines}</ul>"
            "<span class='tm-meta'>Historical models can be incoherent, biased, or unsafe. "
            "Outputs are unpolished so you can inspect real historical behavior.</span>"
        ),
        unsafe_allow_html=True,
    )

    col1, col2 = st.columns(2)
    with col1:
        with st.expander("Methodology", expanded=False):
            if protocol_path.is_file():
                st.markdown(protocol_path.read_text(encoding="utf-8")[:8000])
            else:
                st.write(
                    "Frozen cohort + visible adapters + pinned revisions. "
                    "See README and the registry YAML for the full contract."
                )
    with col2:
        with st.expander("Cohort registry", expanded=False):
            st.write(f"Cohort id: **{cohort.cohort_id}**")
            st.write(f"Prompt limit: **{cohort.prompt.max_chars} characters**")
            for m in cohort.models:
                st.write(
                    f"- `{m.display_year}` **{m.display_name}** · {m.mode} · "
                    f"`{m.source.repository}@{m.source.revision[:10]}`"
                )
