"""Decade spine UI: holes, substitutes, status-quo, quarantined FUTURE."""

from __future__ import annotations

from time_machine.domain import Cohort, ModelSpec
from time_machine.future_ensemble import future_enabled


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
                "label": f"{h.display_year} · hole",
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


def render_decade_spine(st, cohort: Cohort) -> None:
    st.subheader("Decade spine")
    st.caption(
        "Year-by-year lineup with **visible holes** and labeled substitutes. "
        "Sample ≠ frontier. A hole is honest emptiness — never a fake model."
    )
    rows = spine_rows(cohort)
    for row in rows:
        if row["kind"] == "hole":
            st.markdown(
                f"`{row['year']}` · 🕳 **HOLE** · target {row['stands_for']}\n\n"
                f"> {row['limitations'][0]}"
            )
        else:
            badge = "AVAILABLE" if row["slot_status"] == "available" else "SUBSTITUTE"
            extra = f" · stands for **{row['stands_for']}**" if row.get("stands_for") else ""
            st.markdown(
                f"`{row['year']}` · **{row['label']}** · `{badge}` · {row['mode']}{extra}"
            )
            if row["limitations"]:
                st.caption(" · ".join(row["limitations"][:2]))

    if cohort.status_quo is not None:
        st.divider()
        st.markdown(
            f"**{cohort.status_quo.display_name}** · `STATUS_QUO` · model `{cohort.status_quo.model_id}`"
        )
        st.caption(cohort.status_quo.note)

    if cohort.future is not None:
        st.divider()
        if future_enabled(cohort):
            st.warning(
                f"**{cohort.future.display_name}** · `FUTURE (synthetic)` — QUARANTINED. "
                f"{cohort.future.quarantine_note}"
            )
            st.caption(f"Method: `{cohort.future.method}` · {cohort.future.selection_rule}")
        else:
            st.info(
                f"**{cohort.future.display_name}** is present but **disabled** (off by default). "
                "Enable only as a labeled synthetic endpoint — never a year."
            )


def render_slot_badge(st, spec: ModelSpec) -> None:
    if spec.slot_status == "substitute":
        st.warning(f"SUBSTITUTE stand-in for {spec.stands_for or 'an annual frontier class'}")
    elif spec.slot_status == "available":
        st.caption("Slot status: available (named checkpoint)")
