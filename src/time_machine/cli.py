"""CLI entry points: preflight, preload, run-fake, export, delete."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from time_machine.artifact_store import ArtifactStore, sha256_file
from time_machine.config import default_paths, debug_content_enabled, DEBUG_CONTENT_ENV
from time_machine.export_service import ExportService
from time_machine.preflight import hardware_summary, preflight_report
from time_machine.registry import load_cohort
from time_machine.runners.factory import RunnerFactory
from time_machine.trip_controller import TripController


def _paths(args: argparse.Namespace):
    root = Path(args.root).resolve() if getattr(args, "root", None) else None
    return default_paths(root)


def cmd_preflight(args: argparse.Namespace) -> int:
    paths = _paths(args)
    cohort = load_cohort(paths.registry_path)
    report = preflight_report(cohort, paths)
    print(json.dumps(report, indent=2))
    return 0


def cmd_preload(args: argparse.Namespace) -> int:
    """Download only registry-pinned artifacts. Never called from a user prompt."""
    paths = _paths(args)
    cohort = load_cohort(paths.registry_path)
    cache_dir = paths.model_cache_dir
    cache_dir.mkdir(parents=True, exist_ok=True)
    index_path = paths.cache_index_path
    index: dict = json.loads(index_path.read_text(encoding="utf-8")) if index_path.is_file() else {}

    only = set(args.only.split(",")) if getattr(args, "only", None) else None
    print(f"Preloading cohort {cohort.cohort_id} into {cache_dir}")
    print("This is an explicit setup command; user prompts never trigger downloads.")

    try:
        from huggingface_hub import snapshot_download
    except Exception as exc:
        print(f"ERROR: huggingface_hub required for preload: {exc}", file=sys.stderr)
        print("Install the inference extra or huggingface_hub to download checkpoints.", file=sys.stderr)
        return 2

    for spec in cohort.models:
        if only and spec.id not in only:
            continue
        dest = cache_dir / spec.id
        dest.mkdir(parents=True, exist_ok=True)
        print(f"- {spec.id}: {spec.source.repository}@{spec.source.revision}")
        try:
            snapshot_download(
                repo_id=spec.source.repository,
                revision=spec.source.revision,
                local_dir=str(dest),
                allow_patterns=[
                    "*.json",
                    "*.txt",
                    "*.model",
                    "*.safetensors",
                    "*.bin",
                    "*.gguf",
                    "tokenizer*",
                    "vocab*",
                    "merges.txt",
                    "config*",
                    "generation_config*",
                ],
            )
        except Exception as exc:
            print(f"  download failed: {exc}", file=sys.stderr)
            continue

        art = dest / spec.source.artifact_filename
        measured = None
        if art.is_file():
            measured = sha256_file(art)
        else:
            # pick first weight-like file
            candidates = list(dest.glob("*.safetensors")) or list(dest.glob("*.bin")) or list(dest.glob("*.gguf"))
            if candidates:
                measured = sha256_file(candidates[0])
                art = candidates[0]

        expected = spec.source.sha256
        if measured:
            if expected == "record-at-preload":
                index[spec.id] = {
                    "artifact": str(art.name),
                    "sha256": measured,
                    "repository": spec.source.repository,
                    "revision": spec.source.revision,
                }
                print(f"  recorded checksum {measured[:12]}… for {art.name}")
            elif expected != measured:
                print(f"  CHECKSUM MISMATCH for {spec.id}: expected {expected}, got {measured}", file=sys.stderr)
                return 1
            else:
                print(f"  checksum ok {measured[:12]}…")
        else:
            print("  warning: no weight artifact found to checksum")

        if args.record_checksums:
            # convenience: print YAML snippet
            print(f"    sha256: {measured}")

    index_path.write_text(json.dumps(index, indent=2) + "\n", encoding="utf-8")
    print(f"Cache index written to {index_path}")
    return 0


def cmd_run_fake(args: argparse.Namespace) -> int:
    paths = _paths(args)
    cohort = load_cohort(paths.registry_path)
    store = ArtifactStore(paths)
    service = TripController(
        cohort=cohort,
        store=store,
        factory=RunnerFactory(model_cache=str(paths.model_cache_dir)),
        paths=paths,
        runner_kind="fake",
    )

    def on_status(mid: str, status: str, detail: str) -> None:
        print(f"  {mid}: {status} {detail}")

    manifest = service.run_trip(
        args.prompt,
        success_criterion=args.criterion or "",
        on_status=on_status,
        hardware_summary=hardware_summary(paths),
        trip_id=args.trip_id,
    )
    print(f"trip {manifest.trip_id} complete={manifest.complete} runs={len(manifest.runs)}")
    if debug_content_enabled():
        print("DEBUG_CONTENT is on — raw content may be printed.")
    return 0


def cmd_export(args: argparse.Namespace) -> int:
    paths = _paths(args)
    store = ArtifactStore(paths)
    svc = ExportService(store)
    if args.format == "zip":
        out = svc.export_zip(args.trip_id, dest=Path(args.out) if args.out else None)
    else:
        out = svc.export_json_bundle(args.trip_id, dest=Path(args.out) if args.out else None)
    print(str(out))
    return 0


def cmd_delete(args: argparse.Namespace) -> int:
    paths = _paths(args)
    store = ArtifactStore(paths)
    if args.all:
        if args.confirm != "DELETE-ALL":
            print("Refusing delete-all without --confirm DELETE-ALL", file=sys.stderr)
            return 1
        n = store.delete_all_trips()
        print(f"deleted {n} trips")
        return 0
    if not args.trip_id:
        print("trip_id required unless --all", file=sys.stderr)
        return 1
    store.delete_trip(args.trip_id)
    print(f"deleted {args.trip_id}")
    return 0


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(prog="old-weights", description="Old Weights local demo")
    p.add_argument("--root", default=None, help="project root (default: cwd)")
    sub = p.add_subparsers(dest="command", required=True)

    sp = sub.add_parser("preflight", help="report hardware and cohort availability")
    sp.set_defaults(func=cmd_preflight)

    sp = sub.add_parser("preload", help="download registry-pinned checkpoints only")
    sp.add_argument("--only", default=None, help="comma-separated model ids")
    sp.add_argument("--record-checksums", action="store_true")
    sp.set_defaults(func=cmd_preload)

    sp = sub.add_parser("run-fake", help="run a fake cohort trip (no real weights)")
    sp.add_argument("--prompt", required=True)
    sp.add_argument("--criterion", default="")
    sp.add_argument("--trip-id", default=None)
    sp.set_defaults(func=cmd_run_fake)

    sp = sub.add_parser("export", help="export one trip")
    sp.add_argument("--trip-id", required=True)
    sp.add_argument("--format", choices=["zip", "json"], default="zip")
    sp.add_argument("--out", default=None)
    sp.set_defaults(func=cmd_export)

    sp = sub.add_parser("delete", help="delete one trip or all trips")
    sp.add_argument("--trip-id", default=None)
    sp.add_argument("--all", action="store_true")
    sp.add_argument("--confirm", default="", help="must be DELETE-ALL when using --all")
    sp.set_defaults(func=cmd_delete)

    return p


def main(argv: list[str] | None = None) -> int:
    if debug_content_enabled():
        print(
            f"WARNING: {DEBUG_CONTENT_ENV}=1 — content logging/dumping is enabled for development only.",
            file=sys.stderr,
        )
    parser = build_parser()
    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
