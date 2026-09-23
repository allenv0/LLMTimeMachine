"""Offline curve packs (local-v3-longitudinal / WS3).

Frozen density overlay stand-in. Loader refuses incompatible schema versions
and never writes back into user trips.
"""

from __future__ import annotations

import json
from pathlib import Path
from statistics import median

from time_machine.config import AppPaths
from time_machine.domain import CurvePack, CurvePackCurve, CurvePackPoint
from time_machine.errors import ArtifactError

PACK_SCHEMA_VERSION = "curves-pack-v1"
MIN_BAND_N = 5
PACK_CAVEAT = "Published sample, not all of LLM history."


def validate_pack(data: dict) -> CurvePack:
    schema = str(data.get("schema_version") or "")
    if schema and schema != PACK_SCHEMA_VERSION:
        raise ArtifactError(
            f"incompatible curve pack schema {schema!r}; expected {PACK_SCHEMA_VERSION}"
        )
    if "pack_id" not in data:
        raise ArtifactError("curve pack missing pack_id")
    # Accept either nested points or flat dicts already matching the model.
    try:
        pack = CurvePack.model_validate(data)
    except Exception as exc:
        raise ArtifactError(f"invalid curve pack: {exc}") from exc
    return pack


def load_pack(path: Path | str) -> CurvePack:
    path = Path(path)
    if not path.is_file():
        raise ArtifactError(f"curve pack not found: {path}")
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise ArtifactError(f"corrupt curve pack: {exc}") from exc
    return validate_pack(data)


def save_pack(paths: AppPaths, pack: CurvePack) -> Path:
    paths.curve_packs_dir.mkdir(parents=True, exist_ok=True)
    path = paths.curve_packs_dir / f"{pack.pack_id}.json"
    text = json.dumps(pack.model_dump(mode="json"), indent=2, ensure_ascii=False) + "\n"
    tmp = path.with_suffix(".json.tmp")
    tmp.write_text(text, encoding="utf-8")
    tmp.replace(path)
    return path


def discover_packs(paths: AppPaths) -> list[Path]:
    out: list[Path] = []
    for root in (paths.curve_packs_registry_dir, paths.curve_packs_dir):
        if root.is_dir():
            out.extend(sorted(root.glob("*.json")))
    return out


def pack_overlay(pack: CurvePack) -> dict:
    """Median / IQR-style band + spaghetti lines. Honest about n and kind."""
    years: dict[int, list[int]] = {}
    lines = []
    for curve in pack.curves:
        pts = sorted(curve.points, key=lambda p: p.year)
        if not pts:
            continue
        lines.append(
            {
                "prompt_sha256": curve.prompt_sha256,
                "preview": curve.preview,
                "tags": list(curve.tags),
                "points": [p.model_dump(mode="json") for p in pts],
            }
        )
        for p in pts:
            years.setdefault(p.year, []).append(p.score_1_10)

    band = []
    for year in sorted(years):
        vals = sorted(years[year])
        n = len(vals)
        mid = median(vals)
        q1 = vals[max(0, n // 4)]
        q3 = vals[min(n - 1, (3 * n) // 4)]
        band.append(
            {
                "year": year,
                "n": n,
                "median": mid,
                "q1": q1,
                "q3": q3,
                "min": vals[0],
                "max": vals[-1],
            }
        )

    return {
        "pack_id": pack.pack_id,
        "pack_kind": pack.pack_kind,
        "protocol": pack.protocol,
        "cohort_id": pack.cohort_id,
        "judge_id": pack.judge_id,
        "rubric_id": pack.rubric_id,
        "created_at": pack.created_at,
        "method_note": pack.method_note,
        "caveat": pack.caveat or PACK_CAVEAT,
        "n_curves": len(lines),
        "show_band": len(lines) >= MIN_BAND_N,
        "min_band_n": MIN_BAND_N,
        "lines": lines,
        "band": band,
        "caption": (
            f"Pack `{pack.pack_id}` ({pack.pack_kind}) · n={len(lines)} · "
            f"{pack.caveat or PACK_CAVEAT}"
        ),
        "a11y_summary": _a11y_summary(pack, band, len(lines)),
    }


def _a11y_summary(pack: CurvePack, band: list[dict], n: int) -> str:
    if not band:
        return f"Curve pack {pack.pack_id} has no points. {pack.caveat}"
    first, last = band[0], band[-1]
    return (
        f"Pack {pack.pack_id} ({pack.pack_kind}) covers {n} curves from year {first['year']} "
        f"to {last['year']}. Median estimated score moves from {first['median']} to {last['median']} "
        f"(1-10 scale). Band shown only when n>={MIN_BAND_N}. {pack.caveat}"
    )


def build_pack_from_scored_trips(
    *,
    pack_id: str,
    curves: list[CurvePackCurve],
    cohort_id: str = "",
    judge_id: str = "",
    rubric_id: str = "",
    protocol: str = "local-v2-eval",
    pack_kind: str = "empirical",
    method_note: str = "",
) -> CurvePack:
    return CurvePack(
        pack_id=pack_id,
        pack_kind=pack_kind,  # type: ignore[arg-type]
        protocol=protocol,
        cohort_id=cohort_id,
        judge_id=judge_id,
        rubric_id=rubric_id,
        method_note=method_note,
        caveat=PACK_CAVEAT,
        curves=curves,
    )


def make_demonstration_pack(pack_id: str = "curves-pack-v1-demo") -> CurvePack:
    """Method-demo synthetic curves for overlay UI. Explicitly NOT empirical history."""
    # 32 diverse prompt hashes with heterogeneous improvement shapes.
    shapes = [
        "steady",
        "late_jump",
        "early_plateau",
        "noisy",
        "flat_easy",
        "honesty_late",
    ]
    curves: list[CurvePackCurve] = []
    years = [2019, 2021, 2022, 2023, 2024]
    for i in range(32):
        shape = shapes[i % len(shapes)]
        base = 2 + (i % 3)
        points: list[CurvePackPoint] = []
        for yi, year in enumerate(years):
            if shape == "steady":
                score = min(10, base + yi)
            elif shape == "late_jump":
                score = min(10, base + (0 if yi < 3 else 5 + (yi - 3)))
            elif shape == "early_plateau":
                score = min(10, base + min(yi, 1))
            elif shape == "noisy":
                score = max(1, min(10, base + (yi % 3) + (1 if i % 2 == 0 else -1)))
            elif shape == "flat_easy":
                score = min(10, 7 + (1 if yi >= 3 else 0))
            else:  # honesty_late
                score = max(1, min(10, 3 + (2 if yi >= 3 else 0) + (1 if yi == 4 else 0)))
            points.append(
                CurvePackPoint(year=year, score_1_10=int(score), source="synthetic_demo")
            )
        curves.append(
            CurvePackCurve(
                prompt_sha256=f"demo{i:02d}" + "0" * 58,
                preview=f"demo prompt {i:02d}",
                tags=[shape, "demonstration"],
                points=points,
            )
        )
    return CurvePack(
        pack_id=pack_id,
        pack_kind="demonstration",
        protocol="local-v2-eval",
        cohort_id="decade-v0",
        judge_id="none-synthetic",
        rubric_id="none-synthetic",
        method_note=(
            "Synthetic method demo for overlay UI only. Points are generated from "
            "documented improvement shapes (steady / late_jump / early_plateau / noisy / "
            "flat_easy / honesty_late). NOT measured model quality and NOT LLM history."
        ),
        caveat=(
            "DEMONSTRATION pack — synthetic curves for UI method demo. "
            "Not a published sample of real LLM progress."
        ),
        curves=curves,
    )


def export_compare_pack(
    *,
    my_points: list[dict],
    pack: CurvePack,
    trip_id: str = "",
    out_path: Path | None = None,
) -> Path:
    """Export a compare bundle: my curve + pack overlay metadata. Read-only w.r.t. trips."""
    overlay = pack_overlay(pack)
    payload = {
        "kind": "compare-pack-export",
        "trip_id": trip_id,
        "my_points": my_points,
        "pack": pack.model_dump(mode="json"),
        "overlay_summary": {
            "pack_id": overlay["pack_id"],
            "pack_kind": overlay["pack_kind"],
            "n_curves": overlay["n_curves"],
            "show_band": overlay["show_band"],
            "caveat": overlay["caveat"],
            "a11y_summary": overlay["a11y_summary"],
            "band": overlay["band"],
        },
    }
    out = Path(out_path or f"compare-pack-{trip_id or 'session'}.json")
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return out
