"""Multi-turn chat against one historical checkpoint (WS5 playground).

No hidden system prompt. No tools. Same frozen generation profile per turn.
Base models receive a visible transcript adapter — never modern chat glue.
"""

from __future__ import annotations

import json
from pathlib import Path
from uuid import uuid4

from llm_time_machine.artifact_store import sha256_text
from llm_time_machine.config import AppPaths, PROTOCOL_VERSION
from llm_time_machine.domain import (
    ChatSession,
    ChatTurn,
    GenerationConfig,
    ModelSpec,
    PreparedInput,
    RuntimeInfo,
    utc_now_iso,
)
from llm_time_machine.errors import ArtifactError, InputUnsupportedError
from llm_time_machine.network_guard import block_network

# Visible multi-turn adapters (local-v3 / WS5). Templates are audit-visible.
_CONTINUATION_TRANSCRIPT = """Task: {history}Answer:\n"""
_INSTRUCTION_FLAT = "{transcript}"
_MISTRAL_MULTI = "<" + "s>" + "{segments}"
_QWEN_MULTI = "{segments}<|im_start|>assistant\n"

# History builders produce the text BEFORE the final "Answer:" / assistant prefix.
CONTINUATION_TRANSCRIPT_ID = "continuation-transcript-v1"
INSTRUCTION_FLAT_ID = "instruction-flat-transcript-v1"
CHAT_MISTRAL_MULTI_ID = "chat-mistral-multi-v1"
CHAT_QWEN_MULTI_ID = "chat-qwen-multi-v1"

ADAPTER_FOR_MODE = {
    "base_continuation": CONTINUATION_TRANSCRIPT_ID,
    "instruction": INSTRUCTION_FLAT_ID,
    "chat": "chat-native-multi-v1",  # resolved per model via model.adapter_id
}

CHAT_DERAIL_NOTE = (
    "Base models may wander, invent roles, or ignore prior turns. "
    "That derailment is historical content — we do not paper over it."
)


def chat_adapter_for(spec: ModelSpec) -> tuple[str, str]:
    """Return (adapter_id, template_id_note) for multi-turn prepare."""
    if spec.mode == "base_continuation":
        return CONTINUATION_TRANSCRIPT_ID, "continuation transcript (visible)"
    if spec.mode == "instruction":
        return INSTRUCTION_FLAT_ID, "flat multi-turn transcript (visible)"
    # chat: extend the model's native single-turn adapter to multi-turn
    if spec.adapter_id.startswith("chat-mistral"):
        return CHAT_MISTRAL_MULTI_ID, "native Mistral multi-turn"
    if spec.adapter_id.startswith("chat-qwen"):
        return CHAT_QWEN_MULTI_ID, "native Qwen multi-turn"
    return INSTRUCTION_FLAT_ID, "flat multi-turn transcript fallback"


def _escape_no_raw_close(text: str) -> str:
    # Keep tool-XML safety even though tools are disabled.
    return text.replace("</", "<" + "/")


def render_continuation_transcript(pairs: list[tuple[str, str]], next_user: str) -> str:
    parts = []
    for u, a in pairs:
        parts.append(f"Task: {u}\n\nAnswer: {a}\n\n")
    parts.append(f"Task: {next_user}\n\nAnswer:\n")
    return "".join(parts)


def render_instruction_flat(pairs: list[tuple[str, str]], next_user: str) -> str:
    lines = []
    for u, a in pairs:
        lines.append(f"User: {u}")
        lines.append(f"Assistant: {a}")
    lines.append(f"User: {next_user}")
    lines.append("Assistant:")
    return "\n".join(lines)


def render_mistral_multi(pairs: list[tuple[str, str]], next_user: str) -> str:
    # Native Mistral instruct multi-turn. Leading BOS is written once here;
    # the quantized runner still records any strip of a duplicated BOS.
    segments = []
    for u, a in pairs:
        segments.append(f"[INST] {u} [/INST] {a}" + "<" + "/s>")
    segments.append(f"[INST] {next_user} [/INST]")
    return "<" + "s>" + "".join(segments)


def render_qwen_multi(pairs: list[tuple[str, str]], next_user: str) -> str:
    # Build without raw "</" in the assembled tool-adjacent string via splits.
    user_open = "<" + "|im_start|>user\n"
    user_close = "<" + "|im_end|>\n"
    asst_open = "<" + "|im_start|>assistant\n"
    asst_close = "<" + "|im_end|>\n"
    parts = []
    for u, a in pairs:
        parts.append(user_open + u + user_close)
        parts.append(asst_open + a + asst_close)
    parts.append(user_open + next_user + user_close)
    parts.append(asst_open)
    return "".join(parts)


def prepare_chat_input(
    next_user: str,
    history: list[ChatTurn],
    spec: ModelSpec,
) -> PreparedInput:
    pairs: list[tuple[str, str]] = []
    pending_user: str | None = None
    for turn in history:
        if turn.role == "user":
            pending_user = turn.text
        elif turn.role == "assistant" and pending_user is not None:
            pairs.append((pending_user, turn.text))
            pending_user = None
    adapter_id, note = chat_adapter_for(spec)

    if adapter_id == CONTINUATION_TRANSCRIPT_ID:
        prepared = render_continuation_transcript(pairs, next_user)
    elif adapter_id == INSTRUCTION_FLAT_ID:
        prepared = render_instruction_flat(pairs, next_user)
    elif adapter_id == CHAT_MISTRAL_MULTI_ID:
        prepared = render_mistral_multi(pairs, next_user)
    elif adapter_id == CHAT_QWEN_MULTI_ID:
        prepared = render_qwen_multi(pairs, next_user)
    else:
        prepared = render_instruction_flat(pairs, next_user)

    limit = min(spec.input_limit_chars, 4000)
    if len(next_user) > spec.input_limit_chars:
        raise InputUnsupportedError(
            f"chat turn length {len(next_user)} exceeds {spec.id} "
            f"input_limit_chars={spec.input_limit_chars}"
        )
    if len(prepared) > limit:
        raise InputUnsupportedError(
            f"prepared chat input length {len(prepared)} exceeds visible limit {limit} "
            f"for {spec.id} — over-limit fails visible (no silent truncation)"
        )

    notes = [
        f"multi-turn adapter: {adapter_id}",
        note,
        CHAT_DERAIL_NOTE,
        "No hidden system prompt. No tools. Frozen generation profile per turn.",
    ]
    return PreparedInput(
        model_id=spec.id,
        raw_prompt=next_user,
        adapter_id=adapter_id,
        adapter_version=spec.adapter_version,
        prepared_text=prepared,
        was_truncated=False,
        preparation_notes=notes,
    )


class ChatStore:
    """Artifacts under ``local-data/chats/<session_id>/``."""

    def __init__(self, paths: AppPaths) -> None:
        self.paths = paths

    def session_dir(self, session_id: str) -> Path:
        root = self.paths.chats_dir.resolve()
        candidate = (root / session_id).resolve()
        if candidate.parent != root:
            raise ArtifactError("chat session path escapes chats root")
        return candidate

    def create(
        self,
        spec: ModelSpec,
        generation_profile_id: str,
        session_id: str | None = None,
    ) -> ChatSession:
        sid = session_id or f"chat-{uuid4().hex[:12]}"
        sdir = self.session_dir(sid)
        if sdir.exists():
            raise ArtifactError(f"chat session already exists: {sid}")
        sdir.mkdir(parents=True, exist_ok=False)
        (sdir / "turns").mkdir()
        adapter_id, _ = chat_adapter_for(spec)
        session = ChatSession(
            session_id=sid,
            model_id=spec.id,
            display_year=spec.display_year,
            display_name=spec.display_name,
            adapter_id=adapter_id,
            adapter_version=spec.adapter_version,
            generation_profile_id=generation_profile_id,
            protocol_version=PROTOCOL_VERSION,
            turns=[],
        )
        self.save(session)
        return session

    def save(self, session: ChatSession) -> Path:
        sdir = self.session_dir(session.session_id)
        sdir.mkdir(parents=True, exist_ok=True)
        (sdir / "turns").mkdir(exist_ok=True)
        path = sdir / "manifest.json"
        text = json.dumps(session.model_dump(mode="json"), indent=2, ensure_ascii=False) + "\n"
        tmp = path.with_suffix(".json.tmp")
        tmp.write_text(text, encoding="utf-8")
        tmp.replace(path)
        return path

    def load(self, session_id: str) -> ChatSession:
        path = self.session_dir(session_id) / "manifest.json"
        if not path.is_file():
            raise ArtifactError(f"chat session not found: {session_id}")
        return ChatSession.model_validate(json.loads(path.read_text(encoding="utf-8")))

    def list_sessions(self) -> list[ChatSession]:
        out = []
        if not self.paths.chats_dir.is_dir():
            return out
        for path in sorted(self.paths.chats_dir.glob("*/manifest.json")):
            try:
                out.append(ChatSession.model_validate(json.loads(path.read_text(encoding="utf-8"))))
            except Exception:
                continue
        return out

    def write_turn_artifacts(
        self,
        session_id: str,
        turn_index: int,
        prepared: PreparedInput,
        output_text: str,
    ) -> None:
        sdir = self.session_dir(session_id) / "turns"
        sdir.mkdir(parents=True, exist_ok=True)
        (sdir / f"turn-{turn_index:03d}-prepared.txt").write_text(
            prepared.prepared_text, encoding="utf-8"
        )
        (sdir / f"turn-{turn_index:03d}-output.txt").write_text(output_text, encoding="utf-8")

    def read_turn_prepared(self, session_id: str, turn_index: int) -> str:
        path = self.session_dir(session_id) / "turns" / f"turn-{turn_index:03d}-prepared.txt"
        return path.read_text(encoding="utf-8")

    def delete(self, session_id: str) -> None:
        sdir = self.session_dir(session_id)
        if sdir.exists():
            import shutil

            shutil.rmtree(sdir)


class ChatService:
    """One checkpoint, multi-turn. UI never touches runners."""

    def __init__(
        self,
        store: ChatStore,
        factory,
        cohort,
    ) -> None:
        self.store = store
        self.factory = factory
        self.cohort = cohort

    def _spec(self, model_id: str) -> ModelSpec:
        for m in self.cohort.models:
            if m.id == model_id:
                return m
        raise ArtifactError(f"unknown model for chat: {model_id}")

    def _generation(self) -> GenerationConfig:
        return self.cohort.generation_profiles[self.cohort.generation_profile_id]

    def start(self, model_id: str) -> ChatSession:
        spec = self._spec(model_id)
        return self.store.create(spec, self.cohort.generation_profile_id)

    def send(
        self,
        session_id: str,
        user_text: str,
        *,
        block_network_during_turn: bool = True,
    ) -> ChatTurn:
        session = self.store.load(session_id)
        spec = self._spec(session.model_id)
        if not user_text or not user_text.strip():
            raise InputUnsupportedError("chat turn must not be empty")
        prepared = prepare_chat_input(user_text, session.turns, spec)
        # Exchange number counts completed user/assistant pairs + this new user turn.
        exchange_index = sum(1 for t in session.turns if t.role == "user") + 1
        user_turn = ChatTurn(
            turn_index=exchange_index * 2 - 1,
            role="user",
            text=user_text,
            prepared_text=prepared.prepared_text,
            adapter_id=prepared.adapter_id,
            adapter_version=prepared.adapter_version,
            status="completed",
        )
        session.turns.append(user_turn)

        config = self._generation()
        runner = self.factory.create_for_spec(spec)
        try:
            with block_network(enabled=block_network_during_turn):
                result = runner.generate(prepared, spec, config)
        except Exception as exc:
            fail = ChatTurn(
                turn_index=exchange_index * 2,
                role="assistant",
                text="",
                prepared_text=prepared.prepared_text,
                adapter_id=prepared.adapter_id,
                adapter_version=prepared.adapter_version,
                status="failed",
                error_message=str(exc)[:200],
            )
            session.turns.append(fail)
            self.store.save(session)
            self.store.write_turn_artifacts(session_id, exchange_index, prepared, f"ERROR: {exc}")
            return fail
        finally:
            try:
                runner.unload()
            except Exception:
                pass

        asst = ChatTurn(
            turn_index=exchange_index * 2,
            role="assistant",
            text=result.output_text,
            prepared_text=prepared.prepared_text,
            adapter_id=prepared.adapter_id,
            adapter_version=prepared.adapter_version,
            status="completed",
            runtime=result.runtime,
            generation_seconds=0.0,
        )
        session.turns.append(asst)
        if spec.mode == "base_continuation":
            session.derail_warning_shown = True
        self.store.save(session)
        self.store.write_turn_artifacts(session_id, exchange_index, prepared, result.output_text)
        return asst

    def export_session(self, session_id: str, dest: Path | None = None) -> Path:
        session = self.store.load(session_id)
        sdir = self.store.session_dir(session_id)
        payload = {
            "session": session.model_dump(mode="json"),
            "prepared_inputs": {
                p.stem: p.read_text(encoding="utf-8")
                for p in sorted((sdir / "turns").glob("*-prepared.txt"))
            },
            "outputs": {
                p.stem: p.read_text(encoding="utf-8")
                for p in sorted((sdir / "turns").glob("*-output.txt"))
            },
            "derail_note": CHAT_DERAIL_NOTE,
            "prompt_sha256_history": [
                sha256_text(t.text) for t in session.turns if t.role == "user"
            ],
        }
        out = Path(dest or (sdir / "export.json"))
        out.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        return out
