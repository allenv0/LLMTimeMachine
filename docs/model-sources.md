# Model sources

Each cohort checkpoint is pinned to an exact Hugging Face repository revision. Licenses are recorded here and in `registry/cohort-local-v1.yaml`. Custom remote code is rejected (`trust_remote_code=false`). Downloads happen only via `time-machine preload`, never during a user trip.

Integrity: `sha256` is the expected SHA-256 of the primary weight artifact. The sentinel `record-at-preload` records the measured digest into `local-cache-index.json` on first download and pins it thereafter.

## 2019 — GPT-2 XL (`gpt2-xl-2019`)

| Field | Value |
|---|---|
| Display name | GPT-2 XL |
| Repository | `openai-community/gpt2-xl` |
| Revision | `11c5a3d5811f50298f278a704980280950aedb10` |
| Primary artifact | `model.safetensors` (or `pytorch_model.bin` on older pins) |
| License | Modified MIT / OpenAI use terms — see model card |
| License URL | https://huggingface.co/openai-community/gpt2-xl |
| Mode | base_continuation |
| Backend | transformers |
| Adapter | continuation-v1 |
| Hardware profile | standard |
| Notes | Decoder-only base LM. No chat template. Weak instruction following is expected historical behavior. |

## 2021 — GPT-J 6B (`gpt-j-6b-2021`)

| Field | Value |
|---|---|
| Display name | GPT-J 6B |
| Repository | `EleutherAI/gpt-j-6b` |
| Revision | `b5db6c3e1484a8f985230e5617372a1433f1dcaa` |
| Primary artifact | `model.safetensors` / `pytorch_model.bin` shards |
| License | Apache 2.0 |
| License URL | https://huggingface.co/EleutherAI/gpt-j-6b |
| Mode | base_continuation |
| Backend | transformers (or local_quantized if RAM-constrained) |
| Adapter | continuation-v1 |
| Hardware profile | standard / high |
| Notes | Stronger base completion than GPT-2 XL; still pre-instruction. |

## 2022 — FLAN-T5 XL (`flan-t5-xl-2022`)

| Field | Value |
|---|---|
| Display name | FLAN-T5 XL |
| Repository | `google/flan-t5-xl` |
| Revision | `7d6315df2c2fb742f8f5d55b809380a2f758a0d8` |
| Primary artifact | `model.safetensors` |
| License | Apache 2.0 |
| License URL | https://huggingface.co/google/flan-t5-xl |
| Mode | instruction |
| Backend | transformers |
| Adapter | instruction-v1 |
| Hardware profile | lite / standard |
| Notes | Encoder-decoder instruction-tuned checkpoint. Marks the instruction-tuning transition. |

## 2023 — Mistral 7B Instruct v0.2 (`mistral-7b-instruct-2023`)

| Field | Value |
|---|---|
| Display name | Mistral 7B Instruct v0.2 |
| Repository | `mistralai/Mistral-7B-Instruct-v0.2` |
| Revision | `3ad36be9f89496bc48174003c1e80f6b8dd62d21` |
| Primary artifact | `model.safetensors` |
| License | Apache 2.0 |
| License URL | https://huggingface.co/mistralai/Mistral-7B-Instruct-v0.2 |
| Mode | chat |
| Backend | transformers or local_quantized |
| Adapter | chat-mistral-v1 |
| Hardware profile | standard (4-bit / 8-bit) or high (bf16) |
| Notes | Native Mistral instruct template is applied by the visible adapter only — no extra system prompt. |

## 2024 — Qwen2.5 7B Instruct (`qwen25-7b-instruct-2024`)

| Field | Value |
|---|---|
| Display name | Qwen2.5 7B Instruct |
| Repository | `Qwen/Qwen2.5-7B-Instruct` |
| Revision | `41df7d9264de62fb91fbc53d5e864c73c9584347` |
| Primary artifact | `model.safetensors` |
| License | Apache 2.0 (Qwen license terms on model card) |
| License URL | https://huggingface.co/Qwen/Qwen2.5-7B-Instruct |
| Mode | chat |
| Backend | transformers or local_quantized |
| Adapter | chat-qwen-v1 |
| Hardware profile | standard (4-bit / 8-bit) or high (bf16) |
| Notes | Modern open instruction following. Chat template is native and visible in the audit drawer. |

## Rejected sources

| Candidate | Reason |
|---|---|
| Checkpoints requiring `trust_remote_code=true` | Supply-chain safety (plan §8.2) |
| Closed API snapshots | Not locally deployable; violates no-remote-inference rule |
| Unpinned `main` branch weights | Rejected by registry validation |

## Updating this document

Any checkpoint change requires:

1. A registry YAML update with new revision + checksum policy compliance.
2. A `docs/decision-log.md` entry.
3. A manual validation row in `docs/validation.md`.
