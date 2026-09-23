# Prompt adapter notes

Adapters are **visible** transforms required by a checkpoint’s native interface. They must not improve performance with hidden helpers.

| Adapter id | Mode | Purpose | Template summary |
|---|---|---|---|
| `continuation-v1` | base_continuation | Give a base LM a completion cue | `Task: {prompt}\n\nAnswer:\n` |
| `instruction-v1` | instruction | FLAN-T5-style task input | `{prompt}` (task text as-is) |
| `chat-mistral-v1` | chat | Native Mistral instruct tokens | `<s>[INST] {prompt} [/INST]` |
| `chat-qwen-v1` | chat | Native Qwen chat template | `<\|im_start\|>user\n{prompt}<\|im_end\|>\n<\|im_start\|>assistant\n` |

## Rules (protocol §Prompt rule)

1. Preserve the raw prompt exactly; never truncate in `local-v1`.
2. Never add a system prompt, tool result, retrieval context, or chain-of-thought request.
3. Version every adapter change (`adapter_version`).
4. The exact `prepared_text` must be inspectable and exportable.
5. If a model’s tokenizer requires a special form, document it here and in the model’s `limitations`.

## Why each adapter exists

- **continuation-v1** — base models are not instruction-tuned; without a `Task/Answer` cue they often drift.
- **instruction-v1** — FLAN-T5 expects the task as encoder input; adding chat roles would be a hidden rewrite.
- **chat-mistral-v1 / chat-qwen-v1** — chat models have a native template; using it is required for correct behavior and is fully disclosed.
