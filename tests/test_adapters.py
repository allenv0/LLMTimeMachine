"""Prompt adapter rendering tests."""

from __future__ import annotations

import pytest

from time_machine.errors import InputUnsupportedError
from time_machine.prompt_adapters import (
    CHAT_MISTRAL_TEMPLATE,
    CHAT_QWEN_TEMPLATE,
    CONTINUATION_TEMPLATE,
    adapter_explanation,
    prepare_input,
    render_prepared_text,
)
from tests.conftest import make_model


def test_continuation_adapter_preserves_raw_prompt():
    raw = "Write a poem about lighthouses."
    text = render_prepared_text("continuation-v1", raw)
    assert raw in text
    assert text == CONTINUATION_TEMPLATE.format(prompt=raw)


def test_instruction_adapter_identity_task():
    raw = "Summarize this contract clause."
    assert render_prepared_text("instruction-v1", raw) == raw


def test_mistral_chat_adapter():
    raw = "What is 2+2?"
    assert render_prepared_text("chat-mistral-v1", raw) == CHAT_MISTRAL_TEMPLATE.format(prompt=raw)


def test_qwen_chat_adapter():
    raw = "What is 2+2?"
    assert render_prepared_text("chat-qwen-v1", raw) == CHAT_QWEN_TEMPLATE.format(prompt=raw)


def test_prepare_input_never_truncates():
    spec = make_model("m1", 2019, "M1", adapter_id="continuation-v1")
    prepared = prepare_input("hello", spec)
    assert prepared.was_truncated is False
    assert prepared.raw_prompt == "hello"
    assert prepared.prepared_text == CONTINUATION_TEMPLATE.format(prompt="hello")
    assert prepared.preparation_notes


def test_over_limit_raises_input_unsupported():
    spec = make_model("m1", 2019, "M1", input_limit_chars=10)
    with pytest.raises(InputUnsupportedError):
        prepare_input("x" * 11, spec)


def test_protocol_max_enforced():
    spec = make_model("m1", 2019, "M1", input_limit_chars=900)
    with pytest.raises(InputUnsupportedError):
        prepare_input("x" * 901, spec)


def test_adapter_explanation():
    assert "continuation" in adapter_explanation("continuation-v1").lower()
    with pytest.raises(Exception):
        adapter_explanation("nope-v1")
