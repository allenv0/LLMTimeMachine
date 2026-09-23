"""One real-model smoke trip on the lite cohort (no Streamlit)."""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from time_machine.artifact_store import ArtifactStore
from time_machine.config import default_paths
from time_machine.registry import load_cohort
from time_machine.trip_controller import TripController
from time_machine.runners.factory import RunnerFactory


def main() -> int:
    prompt = sys.argv[1] if len(sys.argv) > 1 else (
        "Do a super ultra deep analysis into the apple's design system"
    )
    paths = default_paths(ROOT)
    paths = paths.model_copy(
        update={"cohort_file": ROOT / "registry" / "cohort-five-era-v1.yaml"}
    )
    cohort = load_cohort(paths.registry_path)
    store = ArtifactStore(paths)
    service = TripController(
        cohort=cohort,
        store=store,
        factory=RunnerFactory(model_cache=str(paths.model_cache_dir)),
        paths=paths,
        runner_kind="composite",
    )

    def on_status(mid: str, status: str, detail: str) -> None:
        print(f"  {mid}: {status} {detail}", flush=True)

    print(f"Prompt: {prompt}")
    print(f"Cohort: {cohort.cohort_id} ({len(cohort.models)} models)")
    manifest = service.run_trip(
        prompt,
        success_criterion="Cover visual language, hierarchy, and interaction patterns.",
        on_status=on_status,
        trip_id="real-smoke-apple-design",
    )
    print(f"\ntrip={manifest.trip_id} complete={manifest.complete}")
    for run in manifest.runs:
        print(f"- {run.display_year} {run.display_name}: {run.status} ({run.error_code or 'ok'})")
        if run.status == "completed":
            text = store.read_output(manifest.trip_id, run.model_id)
            preview = text[:220].replace("\n", " ")
            print(f"    {preview}…")
    return 0 if manifest.complete else 1


if __name__ == "__main__":
    raise SystemExit(main())
