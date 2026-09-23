"""Visible prompt adapters backed by registry/adapters/catalog.yaml."""

from __future__ import annotations

from pathlib import Path

from time_machine.adapter_catalog import AdapterCatalog, default_adapter_catalog
from time_machine.domain import ModelSpec, PreparedInput
from time_machine.errors import InputUnsupportedError, RegistryError

# Literal templates kept in sync with catalog.yaml for unit tests / docs.
_CONT = "Task: {prompt}\n\nAnswer:\n"
_INST = "{prompt}"
_MIST = "<" + "s>[INST] {prompt} [/INST]"
_QWEN = (
    "<|im_start|>user\n{prompt}<|im_end|>\n<|im_start|>assistant\n"
    .replace("<|", "<" + "|")
    .replace("|>", "|>")
)

CONTINUATION_TEMPLATE = _CONT
INSTRUCTION_TEMPLATE = _INST
CHAT_MISTRAL_TEMPLATE = _MIST
CHAT_QWEN_TEMPLATE = _QWEN

_BUILTIN_TEMPLATES = {
    "continuation-v1": CONTINUATION_TEMPLATE,
    "instruction-v1": INSTRUCTION_TEMPLATE,
    "chat-mistral-v1": CHAT_MISTRAL_TEMPLATE,
    "chat-qwen-v1": CHAT_QWEN_TEMPLATE,
    "identity-v1": "{prompt}",
    "fake-chat-v1": "<user>{prompt}</user>",
}

_BUILTIN_NOTES = {
    "continuation-v1": [
        "Base model receives a continuation-style wrapper (Task / Answer).",
        "No system prompt, tools, retrieval, or chain-of-thought request is added.",
    ],
    "instruction-v1": [
        "Instruction-tuned encoder-decoder receives the task text as-is.",
        "No chat roles or hidden helpfulness prompt.",
    ],
    "chat-mistral-v1": [
        "Native Mistral instruct tokens only.",
        "No extra system message beyond the model's native template.",
    ],
    "chat-qwen-v1": [
        "Native Qwen chat markers for a single user turn, then assistant prefix.",
        "No extra system message beyond the model's native template.",
    ],
    "identity-v1": ["Identity adapter for tests and fixtures: raw prompt passed through."],
    "fake-chat-v1": ["Fake chat adapter used by the fake runner tests."],
}

_ACTIVE_CATALOG: AdapterCatalog | None = None


def bind_catalog(catalog: AdapterCatalog | None) -> None:
    """Optional: prefer registry/adapters/catalog.yaml over builtins."""
    global _ACTIVE_CATALOG
    _ACTIVE_CATALOG = catalog


def _catalog() -> AdapterCatalog | None:
    return _ACTIVE_CATALOG


def render_prepared_text(adapter_id: str, raw_prompt: str) -> str:
    cat = _catalog()
    if cat is not None:
        return cat.render(adapter_id, raw_prompt)
    template = _BUILTIN_TEMPLATES.get(adapter_id)
    if template is None:
        raise RegistryError(f"unknown adapter_id: {adapter_id!r}")
    return template.format(prompt=raw_prompt)


def prepare_input(raw_prompt: str, spec: ModelSpec) -> PreparedInput:
    """Build the exact model-ready text. Never truncates; never hides helpers."""
    if len(raw_prompt) > spec.input_limit_chars:
        raise InputUnsupportedError(
            f"prompt length {len(raw_prompt)} exceeds {spec.id} "
            f"input_limit_chars={spec.input_limit_chars}"
        )
    if len(raw_prompt) > 900:
        raise InputUnsupportedError(
            f"prompt length {len(raw_prompt)} exceeds protocol maximum 900 characters"
        )

    prepared_text = render_prepared_text(spec.adapter_id, raw_prompt)
    notes = list(adapter_notes(spec.adapter_id))
    return PreparedInput(
        model_id=spec.id,
        raw_prompt=raw_prompt,
        adapter_id=spec.adapter_id,
        adapter_version=spec.adapter_version,
        prepared_text=prepared_text,
        was_truncated=False,
        preparation_notes=notes,
    )


def adapter_notes(adapter_id: str) -> list[str]:
    cat = _catalog()
    if cat is not None:
        return list(cat.get(adapter_id).notes) or [cat.get(adapter_id).purpose]
    notes = _BUILTIN_NOTES.get(adapter_id)
    if not notes:
        raise RegistryError(f"unknown adapter_id: {adapter_id!r}")
    return list(notes)


def adapter_explanation(adapter_id: str) -> str:
    return "\n".join(adapter_notes(adapter_id))
