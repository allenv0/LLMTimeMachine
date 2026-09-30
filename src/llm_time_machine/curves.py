"""Personal quality curves from human annotations (Track A, local-v1 safe).

No LLM-judge. Missing ratings stay missing — never zero-filled.
"""

from __future__ import annotations

import json
from pathlib import Path

from llm_time_machine.config import AppPaths
from llm_time_machine.domain import Cohort, CurvePoint, TripManifest, UserAnnotations
from llm_time_machine.errors import ArtifactError

USEFULNESS_TO_ORDINAL = {
    "no": -1,
    "partly": 0,
    "yes": 1,
}

ORDINAL_LABELS = {
    -2: "much worse than hoped",
    -1: "worse than hoped",
    0: "about as hoped",
    1: "better than hoped",
    2: "much better than hoped",
}

CURVE_CAPTION = "Your ratings. Not a scientific measurement."


def ordinal_from_usefulness(value: str) -> int | None:
    return USEFULNESS_TO_ORDINAL.get(value)


def build_trip_curve(
    manifest: TripManifest,
    annotations: UserAnnotations,
    cohort: Cohort | None = None,
    prefer_explicit: bool = True,
) -> list[CurvePoint]:
    """Series for one trip. Unrated models produce no points (honest gaps)."""
    by_id = {m.id: m for m in cohort.models} if cohort else {}
    points: list[CurvePoint] = []
    for run in sorted(manifest.runs, key=lambda r: (r.display_year or 0, r.model_id)):
        mid = run.model_id
        source = None
        ordinal = None
        if prefer_explicit and mid in annotations.ordinal:
            ordinal = int(annotations.ordinal[mid])
            source = "explicit"
        elif mid in annotations.ordinal:
            ordinal = int(annotations.ordinal[mid])
            source = "explicit"
        elif mid in annotations.usefulness:
            derived = ordinal_from_usefulness(annotations.usefulness[mid])
            if derived is not None:
                ordinal = derived
                source = "derived_usefulness"
        if ordinal is None:
            continue
        spec = by_id.get(mid)
        year = run.display_year or (spec.display_year if spec else 0)
        name = run.display_name or (spec.display_name if spec else mid)
        points.append(
            CurvePoint(
                model_id=mid,
                display_year=year,
                ordinal=ordinal,
                source=source or "explicit",
                display_name=name,
            )
        )
    points.sort(key=lambda p: (p.display_year, p.model_id))
    return points


def curve_path(paths: AppPaths, trip_id: str) -> Path:
    return paths.curves_dir / f"{trip_id}.json"


def write_curve(paths: AppPaths, trip_id: str, points: list[CurvePoint], meta: dict | None = None) -> Path:
    paths.curves_dir.mkdir(parents=True, exist_ok=True)
    path = curve_path(paths, trip_id)
    payload = {
        "trip_id": trip_id,
        "kind": "human_ordinal",
        "caption": CURVE_CAPTION,
        "points": [p.model_dump(mode="json") for p in points],
        "meta": meta or {},
    }
    text = json.dumps(payload, indent=2, ensure_ascii=False) + "\n"
    tmp = path.with_suffix(".json.tmp")
    tmp.write_text(text, encoding="utf-8")
    tmp.replace(path)
    return path


def read_curve(paths: AppPaths, trip_id: str) -> list[CurvePoint]:
    path = curve_path(paths, trip_id)
    if not path.is_file():
        return []
    data = json.loads(path.read_text(encoding="utf-8"))
    return [CurvePoint.model_validate(p) for p in data.get("points") or []]


def delete_curve(paths: AppPaths, trip_id: str) -> None:
    path = curve_path(paths, trip_id)
    if path.is_file():
        path.unlink()


def portfolio_series(
    series_by_entry: dict[str, list[CurvePoint]],
) -> dict:
    """Local density over the user's own prompts (NOT global LLM progress)."""
    lines = []
    for entry_id, points in sorted(series_by_entry.items()):
        if not points:
            continue
        lines.append(
            {
                "entry_id": entry_id,
                "points": [p.model_dump(mode="json") for p in points],
            }
        )
    years: dict[int, list[int]] = {}
    for line in lines:
        for p in line["points"]:
            years.setdefault(int(p["display_year"]), []).append(int(p["ordinal"]))
    band = []
    for year in sorted(years):
        vals = sorted(years[year])
        mid = vals[len(vals) // 2]
        band.append({"year": year, "n": len(vals), "median": mid, "min": vals[0], "max": vals[-1]})
    return {
        "kind": "local_portfolio",
        "caption": "Your prompt portfolio (local). Not global LLM progress.",
        "n_prompts": len(lines),
        "show_band": len(lines) >= 5,
        "lines": lines,
        "band": band,
    }


def try_artifact_error(exc: Exception) -> ArtifactError:
    return exc if isinstance(exc, ArtifactError) else ArtifactError(str(exc))
