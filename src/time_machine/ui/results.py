"""Result dispatches — newspaper wire copy with year gutter, folio, erratum."""

from __future__ import annotations

from html import escape

from time_machine.config import FAILURE_TAG_VALUES
from time_machine.domain import Cohort, ModelRun, TripManifest, UserAnnotations
from time_machine.prompt_adapters import adapter_explanation
from time_machine.ui import theme

MODE_BADGE = {
    "base_continuation": "Base",
    "instruction": "Instruction",
    "chat": "Chat",
}


def _annotation_defaults(annotations: UserAnnotations, model_id: str) -> dict:
    return {
        "usefulness": annotations.usefulness.get(model_id, "unset"),
        "ordinal": annotations.ordinal.get(model_id, None),
        "notes": annotations.notes.get(model_id, ""),
        "failure_tags": annotations.failure_tags.get(model_id, []),
    }


def render_result_cards(
    st,
    cohort: Cohort,
    manifest: TripManifest,
    raw_prompt: str,
    outputs: dict[str, str],
    prepared_inputs: dict[str, str],
    annotations: UserAnnotations,
):
    """Render chronological dispatches. Returns updated annotations."""
    theme.inject(st)
    updated = annotations.model_copy(deep=True)
    by_id = {m.id: m for m in cohort.models}

    st.markdown(
        theme.section("Dispatches", "oldest → newest · your notes are not measurements"),
        unsafe_allow_html=True,
    )

    if not manifest.runs:
        st.markdown(theme.empty_state("No dispatches filed yet."), unsafe_allow_html=True)
        return updated

    for run in manifest.runs:
        spec = by_id.get(run.model_id)
        year = run.display_year or (spec.display_year if spec else 0)
        name = run.display_name or (spec.display_name if spec else run.model_id)
        mode = run.mode or (spec.mode if spec else "chat")

        with st.container(border=True):
            chips = [
                theme.badge(MODE_BADGE.get(mode, mode), "ink"),
                theme.badge(run.status, "ok" if run.status == "completed" else "danger"),
            ]
            if spec is not None and getattr(spec, "slot_status", "available") == "substitute":
                chips.append(theme.badge("Sub", "accent"))
            st.markdown(theme.card_head(str(year), name, *chips), unsafe_allow_html=True)

            if spec is not None and getattr(spec, "slot_status", "available") == "substitute":
                st.caption(f"Stand-in for {spec.stands_for or 'an annual frontier class'}.")

            meta_bits = []
            if run.load_seconds or run.generation_seconds:
                meta_bits.append(f"<span>load {run.load_seconds:.2f}s</span>")
                meta_bits.append(f"<span>gen {run.generation_seconds:.2f}s</span>")
            if meta_bits:
                st.markdown(theme.row(*meta_bits), unsafe_allow_html=True)

            if run.status == "completed":
                body = escape(outputs.get(run.model_id, "") or "")
                if not body.strip():
                    st.markdown(
                        '<div class="tm-output"><em>(no copy filed)</em></div>',
                        unsafe_allow_html=True,
                    )
                else:
                    st.markdown(
                        f'<div class="tm-output clamp">{body}</div>',
                        unsafe_allow_html=True,
                    )
                    with st.expander("Continue reading", expanded=False):
                        st.markdown(outputs.get(run.model_id, ""))
            else:
                st.markdown(
                    theme.erratum(
                        f"delayed at {year} · {run.status}: {run.error_code or 'error'} — "
                        f"{run.error_message or 'no detail'}"
                    ),
                    unsafe_allow_html=True,
                )

            # Folio / byline
            pin = (run.source_revision or "")[:10]
            st.markdown(
                theme.folio(
                    f"<span>{escape(run.adapter_id or '')}</span>",
                    f"<span>pin {escape(pin)}…</span>",
                    f"<span>mode {escape(mode)}</span>",
                ),
                unsafe_allow_html=True,
            )

            if run.limitations:
                st.caption("Limitations: " + "; ".join(run.limitations))

            st.markdown(theme.rule(), unsafe_allow_html=True)
            st.markdown(theme.kicker("Rate this dispatch"), unsafe_allow_html=True)
            defaults = _annotation_defaults(updated, run.model_id)
            ord_labels = [
                "unset",
                "−2 much worse",
                "−1 worse",
                "0 about as hoped",
                "+1 better",
                "+2 much better",
            ]
            ord_values = [None, -2, -1, 0, 1, 2]
            cur = defaults["ordinal"]
            ord_index = 0 if cur is None else ord_values.index(cur)
            ord_choice = st.radio(
                "Ordinal (personal)",
                ord_labels,
                index=ord_index,
                horizontal=True,
                key=f"ord-{run.model_id}",
                help="Track A personal rating. Not a scientific measurement. Feeds the progress curve.",
            )
            picked = ord_values[ord_labels.index(ord_choice)]
            if picked is None:
                updated.ordinal.pop(run.model_id, None)
            else:
                updated.ordinal[run.model_id] = int(picked)

            usefulness = st.radio(
                "Usefulness",
                ["unset", "yes", "partly", "no"],
                index=["unset", "yes", "partly", "no"].index(defaults["usefulness"]),
                horizontal=True,
                key=f"useful-{run.model_id}",
            )
            if usefulness == "unset":
                updated.usefulness.pop(run.model_id, None)
            else:
                updated.usefulness[run.model_id] = usefulness

            tags = st.multiselect(
                "Failure tags",
                list(FAILURE_TAG_VALUES),
                default=defaults["failure_tags"],
                key=f"tags-{run.model_id}",
            )
            if tags:
                updated.failure_tags[run.model_id] = list(tags)
            else:
                updated.failure_tags.pop(run.model_id, None)

            notes = st.text_area(
                "Notes",
                value=defaults["notes"],
                key=f"notes-{run.model_id}",
                height=80,
            )
            if notes.strip():
                updated.notes[run.model_id] = notes
            else:
                updated.notes.pop(run.model_id, None)

            with st.expander("Audit view", expanded=False):
                st.markdown("**Raw user prompt**")
                st.code(raw_prompt, language="text")
                prepared = prepared_inputs.get(run.model_id) or run.prepared_text or ""
                st.markdown("**Exact prepared input**")
                st.code(prepared, language="text")
                adapter_id = run.adapter_id or (spec.adapter_id if spec else "")
                try:
                    explanation = adapter_explanation(adapter_id)
                except Exception:
                    explanation = "Adapter explanation unavailable."
                st.markdown("**Adapter explanation**")
                st.write(explanation)
                st.markdown("**Source pin**")
                st.write(
                    f"repository: `{run.source_repository}`  \n"
                    f"revision: `{run.source_revision}`  \n"
                    f"sha256: `{run.source_sha256}`"
                )
                st.markdown("**Generation profile and runtime**")
                if run.runtime:
                    st.json(run.runtime.model_dump(mode="json"))
                else:
                    st.write("No runtime telemetry for this run.")

    st.markdown(theme.rule(heavy=True), unsafe_allow_html=True)
    st.markdown(theme.dirty_bar("Review notes before leaving this desk"), unsafe_allow_html=True)
    trip_notes = st.text_area(
        "Trip notes (local only)",
        value=updated.trip_notes,
        key="trip-notes",
    )
    updated.trip_notes = trip_notes
    return updated
