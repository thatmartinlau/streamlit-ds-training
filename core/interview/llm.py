"""Thin DeepSeek chat wrapper.

Mirrors the secret-resolution order used by `core.dynamic_quiz.get_secret`
(`st.secrets` first, then `os.environ`) so the two entry points behave
identically w.r.t. how `DEEPSEEK_API_KEY` is discovered.
"""

from __future__ import annotations

import os
from typing import Any

import streamlit as st
from openai import OpenAI

from core.interview.config import InterviewConfig, load_config


def get_secret(name: str) -> str | None:
    try:
        v = st.secrets.get(name)
        if v:
            return str(v).strip()
    except Exception:
        pass
    return (os.environ.get(name) or "").strip() or None


def _client(cfg: InterviewConfig) -> OpenAI:
    key = get_secret("DEEPSEEK_API_KEY")
    if not key:
        raise RuntimeError(
            "DEEPSEEK_API_KEY is not configured. Add it to "
            "`.streamlit/secrets.toml` or export it as an environment variable."
        )
    return OpenAI(api_key=key, base_url=cfg.base_url)


def chat(
    system: str,
    user: str,
    *,
    model: str,
    temperature: float,
    max_tokens: int = 2000,
    json_mode: bool = False,
) -> str:
    cfg = load_config()
    kwargs: dict[str, Any] = dict(
        model=model,
        messages=[
            {"role": "system", "content": system},
            {"role": "user", "content": user},
        ],
        temperature=temperature,
        max_tokens=max_tokens,
    )
    if json_mode:
        kwargs["response_format"] = {"type": "json_object"}

    resp = _client(cfg).chat.completions.create(**kwargs)
    choice = resp.choices[0]
    if getattr(choice, "finish_reason", None) == "length":
        raise RuntimeError("LLM response was truncated by the max_tokens budget.")
    return choice.message.content or ""