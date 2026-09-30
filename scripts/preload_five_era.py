"""Download the expanded five-era cohort that fits ~16 GB RAM / ~25 GB disk."""

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
        ["*.json", "*.txt", "*.model", "*.safetensors", "tokenizer*", "vocab*", "config*", "generation_config*"],
    ),
    (
        "gpt2-medium-2021",
        "openai-community/gpt2-medium",
        "6dcaa7a952f72f9298047fd5137cd6e4f05f41da",
        "model.safetensors",
        ["*.json", "*.txt", "*.model", "*.safetensors", "tokenizer*", "vocab*", "config*", "generation_config*"],
    ),
    (
        "flan-t5-large-2022",
        "google/flan-t5-large",
        "0613663d0d48ea86ba8cb3d7a44f0f65dc596a2a",
        "model.safetensors",
        ["*.json", "*.txt", "*.model", "*.safetensors", "tokenizer*", "vocab*", "config*", "generation_config*", "spiece*"],
    ),
    (
        "mistral-7b-instruct-2023",
        "TheBloke/Mistral-7B-Instruct-v0.2-GGUF",
        "3a6fbf4a41a1d52e415a4958cde6856d34b2db93",
        "mistral-7b-instruct-v0.2.Q4_K_M.gguf",
        ["mistral-7b-instruct-v0.2.Q4_K_M.gguf", "*.json", "*.md", "tokenizer*", "vocab*", "config*"],
    ),
    (
        "qwen25-7b-instruct-2024",
        "Qwen/Qwen2.5-7B-Instruct-GGUF",
        "bb5d59e06d9551d752d08b292a50eb208b07ab1f",
        "qwen2.5-7b-instruct-q4_k_m-00001-of-00002.gguf",
        ["*q4_k_m*.gguf", "*.json", "*.md", "tokenizer*", "vocab*", "config*"],
    ),
]


def main() -> int:
    cache = ROOT / "local-data" / "model-cache"
    cache.mkdir(parents=True, exist_ok=True)
    index_path = cache / "local-cache-index.json"
    index = json.loads(index_path.read_text(encoding="utf-8")) if index_path.is_file() else {}

    for mid, repo, rev, artifact, allow in MODELS:
        dest = cache / mid
        dest.mkdir(parents=True, exist_ok=True)
        art = dest / artifact
        if art.is_file() and mid in index:
            print(f"skip {mid}", flush=True)
            continue
        print(f"Downloading {mid} ({repo}) ...", flush=True)
        snapshot_download(
            repo_id=repo,
            revision=rev,
            local_dir=str(dest),
            allow_patterns=allow,
        )
        if not art.is_file():
            cands = sorted(dest.glob("*.gguf")) or sorted(dest.glob("*.safetensors"))
            art = cands[0] if cands else art
        if art.is_file():
            digest = sha256_file(art)
            index[mid] = {
                "artifact": art.name,
                "sha256": digest,
                "repository": repo,
                "revision": rev,
                "size_bytes": art.stat().st_size,
            }
            extras = list(dest.glob("*.gguf"))
            if len(extras) > 1:
                index[mid]["gguf_parts"] = [p.name for p in sorted(extras)]
            print(f"  ok {art.name}  {art.stat().st_size/1e9:.2f}GB  {digest[:12]}…", flush=True)
        else:
            print(f"  FAIL missing artifact {mid}", file=sys.stderr)

    index_path.write_text(json.dumps(index, indent=2) + "\n", encoding="utf-8")
    used = sum(p.stat().st_size for p in cache.rglob("*") if p.is_file())
    print(f"cache total: {used/1e9:.2f} GB")
    print(f"free disk:   {shutil.disk_usage(ROOT).free/1e9:.2f} GB")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
