"""Playground chat UI: multi-turn against one historical checkpoint."""

from __future__ import annotations

from time_machine.chat_session import CHAT_DERAIL_NOTE, ChatService, ChatStore, chat_adapter_for
from time_machine.ui import theme


def render_chat_panel(st, chat: ChatService, chat_store: ChatStore, cohort) -> None:
    theme.inject(st)
    st.markdown(
        theme.section("Talk to a checkpoint", "multi-turn · visible adapters"),
        unsafe_allow_html=True,
    )
    st.caption(
        "Fire up one historical model. No hidden system prompt. "
        "Same frozen generation profile each turn."
    )

    models = sorted(cohort.models, key=lambda m: (m.display_year, m.id))
    labels = [f"{m.display_year} · {m.display_name} · {m.mode}" for m in models]
    idx = st.selectbox("Checkpoint", range(len(models)), format_func=lambda i: labels[i])
    spec = models[idx]
    adapter_id, note = chat_adapter_for(spec)
    st.caption(f"Multi-turn adapter: `{adapter_id}` — {note}")
    if spec.mode == "base_continuation":
        st.warning(CHAT_DERAIL_NOTE)

    if st.button("Start new chat session", key="chat-new"):
        session = chat.start(spec.id)
        st.session_state["chat_session_id"] = session.session_id
        st.rerun()

    sid = st.session_state.get("chat_session_id")
    sessions = chat_store.list_sessions()
    if sessions and not sid:
        sid = sessions[-1].session_id
        st.session_state["chat_session_id"] = sid

    if not sid:
        st.info("Start a session to chat with this year/model.")
        return

    session = chat_store.load(sid)
    if session.model_id != spec.id:
        st.caption(f"Active session `{sid}` is bound to `{session.model_id}` — start a new one to switch.")

    st.write(f"Session `{session.session_id}` · {len(session.turns)} turn records")

    for turn in session.turns:
        who = "You" if turn.role == "user" else session.display_name
        text = turn.text or (turn.error_message or "")
        if turn.status == "failed" and not turn.text:
            st.markdown(theme.erratum(f"turn failed · {turn.error_message or 'no detail'}"), unsafe_allow_html=True)
        elif text:
            st.markdown(theme.slip(f"{who}: {text}", role=turn.role), unsafe_allow_html=True)
        with st.expander("Audit this turn", expanded=False):
            st.write(f"Adapter `{turn.adapter_id}` v{turn.adapter_version}")
            st.code(turn.prepared_text or "(none)", language="text")

    if session.derail_warning_shown:
        st.markdown(
            theme.colophon(CHAT_DERAIL_NOTE),
            unsafe_allow_html=True,
        )

    user_text = st.chat_input("Say something to this checkpoint…")
    if user_text:
        if session.model_id != spec.id:
            st.error("Start a new session for a different checkpoint.")
        else:
            with st.spinner("Generating…"):
                chat.send(sid, user_text)
            st.rerun()

    c1, c2 = st.columns(2)
    if c1.button("Export chat session"):
        out = chat.export_session(sid)
        st.success(f"Exported to `{out}`")
    if c2.button("Delete chat session"):
        chat_store.delete(sid)
        st.session_state.pop("chat_session_id", None)
        st.rerun()
