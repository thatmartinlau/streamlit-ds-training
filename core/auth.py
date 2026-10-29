"""Password gate for feature-gated views.

Both the dynamic screen and the interview simulator read the same
`DEEPSEEK_PASSWORD` secret, but each keeps its own unlock flag in
`st.session_state` so that unlocking one feature does not silently
unlock the other. If a feature needs a different secret, pass a different
`secret_name`; if two features should share an unlock, pass the same
`session_key`.
"""

from __future__ import annotations

import os

import streamlit as st


def get_secret(name: str) -> str | None:
    """Resolve a secret from ``st.secrets`` first, then the environment.

    Mirrors ``core.dynamic_quiz.get_secret`` and
    ``core.interview.llm.get_secret`` so all three call sites behave
    identically w.r.t. how ``DEEPSEEK_*`` secrets are discovered.
    """
    try:
        v = st.secrets.get(name)
        if v:
            return str(v).strip()
    except Exception:
        pass
    return (os.environ.get(name) or "").strip() or None


def password_gate(
    *,
    title: str,
    session_key: str,
    secret_name: str = "DEEPSEEK_PASSWORD",
    description: str = (
        "This feature is password-protected. Enter the password below to "
        "unlock it."
    ),
) -> bool:
    """Render the password gate for a feature.

    Returns ``True`` when the session is already unlocked, so the caller
    can proceed. Returns ``False`` when the gate is shown (or after a
    failed attempt) — callers should early-return on ``False``.
    """
    if st.session_state.get(session_key, False):
        return True

    st.title(title)
    st.markdown(description)

    pwd = st.text_input(
        "Password", type="password", key=f"{session_key}_pwd_input"
    )
    if st.button("Unlock", type="primary"):
        expected = get_secret(secret_name)
        if not expected:
            st.error(
                f"No password is configured. Add `{secret_name}` to "
                "`.streamlit/secrets.toml`."
            )
            return False
        if pwd == expected:
            st.session_state[session_key] = True
            st.rerun()
        else:
            st.error("Incorrect password.")

    return False