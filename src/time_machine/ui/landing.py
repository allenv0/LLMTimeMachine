"""Landing disclosure and protocol links."""

from __future__ import annotations

from pathlib import Path

from time_machine.config import DISCLOSURE_LINES, TRUTHFUL_CLAIM, APP_NAME
from time_machine.domain import Cohort


def render_landing(st, protocol_path: Path, cohort: Cohort) -> None:
    st.title(APP_NAME)
    st.caption(TRUTHFUL_CLAIM)
    st.markdown("### Before you run")
    for line in DISCLOSURE_LINES:
        st.markdown(f"- {line}")
    st.info(
        "Historical models can be incoherent, biased, or unsafe. "
        "Outputs are shown unpolished so you can inspect real historical behavior."
    )
    col1, col2 = st.columns(2)
    with col1:
        with st.expander("Protocol (local-v1)", expanded=False):
            if protocol_path.is_file():
                st.markdown(protocol_path.read_text(encoding="utf-8")[:8000])
            else:
                st.write("PROTOCOL.md not found on disk.")
    with col2:
        with st.expander("Cohort registry", expanded=False):
            st.write(f"Cohort id: **{cohort.cohort_id}**")
            st.write(f"Prompt limit: **{cohort.prompt.max_chars} characters**")
            for m in cohort.models:
                st.write(
                    f"- `{m.display_year}` **{m.display_name}** · {m.mode} · "
                    f"`{m.source.repository}@{m.source.revision[:10]}`"
                )
