"""Preload the lite substitute cohort (fits ~16 GB RAM hosts with ~4 GB free disk)."""

from __future__ import annotations

import json
import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from huggingface_hub import snapshot_download

from llm_time_machine.artifact_store import sha256_file

MODELS = [
    (
        "gpt2-2019",
        "openai-community/gpt2",
        "607a30d783dfa663caf39e06633721c8d4cfcd7e",
        "model.safetensors",
    ),
    (
        "gpt2-medium-2021",
        "openai-community/gpt2-medium",
        "6dcaa7a952f72f9298047fd5137cd6e4f05f41da",
        "model.safetensors",
    ),
    (
        "flan-t5-base-2022",
        "google/flan-t5-base",
        "7bcac572ce56db69c1ea7c8af255c5d7c9672fc2",
        "model.safetensors",
    ),
]

ALLOW = [
    "*.json",
    "*.txt",
    "*.model",
    "*.safetensors",
    "tokenizer*",
    "vocab*",
    "config*",
    "generation_config*",
]


def main() -> int:
    cache = ROOT / "local-data" / "model-cache"
    cache.mkdir(parents=True, exist_ok=True)
    index_path = cache / "local-cache-index.json"
    index = json.loads(index_path.read_text(encoding="utf-8")) if index_path.is_file() else {}

    for mid, repo, rev, artifact in MODELS:
        dest = cache / mid
        dest.mkdir(parents=True, exist_ok=True)
        art = dest / artifact
        if art.is_file() and mid in index:
            print(f"skip {mid} (already cached)")
            continue
        print(f"Downloading {mid} from {repo}@{rev[:8]} ...", flush=True)
        snapshot_download(
            repo_id=repo,
            revision=rev,
            local_dir=str(dest),
            allow_patterns=ALLOW,
        )
        if not art.is_file():
            cands = list(dest.glob("*.safetensors"))
            art = cands[0] if cands else art
        if art.is_file():
            digest = sha256_file(art)
            index[mid] = {
                "artifact": art.name,
                "sha256": digest,
                "repository": repo,
                "revision": rev,
            }
            print(f"  checksum {digest[:12]}…  {art.stat().st_size / 1e9:.2f} GB", flush=True)
        else:
            print(f"  ERROR: missing artifact for {mid}", file=sys.stderr)

    index_path.write_text(json.dumps(index, indent=2) + "\n", encoding="utf-8")
    print(f"free disk: {shutil.disk_usage(ROOT).free / 1e9:.2f} GB")
    print(f"index: {index_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
