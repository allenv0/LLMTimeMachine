"""Blind A–E comparison view (not the default presentation)."""

from __future__ import annotations

from time_machine.domain import Cohort, TripManifest, UserAnnotations
from time_machine.trip_service import blind_mapping_for_trip


def ensure_mapping(annotations: UserAnnotations, trip_id: str, model_ids: list[str]) -> UserAnnotations:
    if not annotations.blind_mapping:
        annotations = annotations.model_copy(deep=True)
        annotations.blind_mapping = blind_mapping_for_trip(trip_id, model_ids)
    return annotations


def render_blind_compare(
    st,
    cohort: Cohort,
    manifest: TripManifest,
    outputs: dict[str, str],
    annotations: UserAnnotations,
):
    """Return updated annotations after blind ranking."""
    completed = [r for r in manifest.runs if r.status == "completed"]
    model_ids = [r.model_id for r in completed]
    annotations = ensure_mapping(annotations, manifest.trip_id, [m.id for m in cohort.models])
    mapping = annotations.blind_mapping
    reverse = {label: mid for mid, label in mapping.items()}

    st.subheader("Blind comparison")
    st.caption(
        "Blind rank is one user’s one-trip preference — not a statistical measurement."
    )

    labels = sorted(mapping.values())
    # show completed outputs under labels without year/name until reveal
    label_to_model = {}
    for run in completed:
        label = mapping.get(run.model_id)
        if label:
            label_to_model[label] = run.model_id

    ranks = dict(annotations.blind_rank)
    unranked = list(annotations.blind_unranked)
    ties = list(annotations.blind_tie)

    for label in labels:
        mid = label_to_model.get(label)
        if not mid:
            continue
        with st.container(border=True):
            st.markdown(f"### Candidate {label}")
            st.markdown(outputs.get(mid, ""))
            choice = st.radio(
                f"Rank for {label}",
                ["1", "2", "3", "4", "5", "tie", "unranked"],
                index=_index_for(ranks, mid, ties, unranked, labels),
                horizontal=True,
                key=f"blind-{mid}",
            )
            if choice == "tie":
                ranks.pop(mid, None)
                if mid not in ties:
                    ties.append(mid)
                if mid in unranked:
                    unranked.remove(mid)
            elif choice == "unranked":
                ranks.pop(mid, None)
                if mid not in unranked:
                    unranked.append(mid)
                if mid in ties:
                    ties.remove(mid)
            else:
                ranks[mid] = int(choice)
                if mid in ties:
                    ties.remove(mid)
                if mid in unranked:
                    unranked.remove(mid)

    annotations = annotations.model_copy(deep=True)
    annotations.blind_rank = ranks
    annotations.blind_tie = ties
    annotations.blind_unranked = unranked

    if st.checkbox("Reveal model mapping", value=annotations.blind_mapping_revealed, key="reveal-blind"):
        annotations.blind_mapping_revealed = True
        st.markdown("**Mapping**")
        for mid, label in sorted(mapping.items(), key=lambda kv: kv[1]):
            st.write(f"{label} → `{mid}`")
    else:
        annotations.blind_mapping_revealed = False

    return annotations


def _index_for(ranks: dict[str, int], mid: str, ties: list[str], unranked: list[str], labels: list[str]) -> int:
    options = ["1", "2", "3", "4", "5", "tie", "unranked"]
    if mid in ranks:
        return options.index(str(ranks[mid]))
    if mid in ties:
        return options.index("tie")
    if mid in unranked:
        return options.index("unranked")
    return options.index("unranked")
