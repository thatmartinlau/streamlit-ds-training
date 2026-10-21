"""Titanic dataset loading for the pandas training page."""

from pathlib import Path

import pandas as pd
import streamlit as st

CACHE_KEY = "_titanic_df"
SOURCE_KEY = "_titanic_source"

# Common locations the dataset may be dropped into.
DEFAULT_PATHS = [
    Path(__file__).resolve().parent.parent / "titanic.csv",
    Path(__file__).resolve().parent.parent / "data" / "titanic.csv",
    Path(__file__).resolve().parent.parent / "titanic" / "train.csv",
    Path.cwd() / "titanic.csv",
]


def _first_existing() -> Path | None:
    for p in DEFAULT_PATHS:
        if p.is_file():
            return p
    return None


def _load_from_disk() -> tuple[pd.DataFrame | None, str | None]:
    path = _first_existing()
    if path is None:
        return None, None
    try:
        return pd.read_csv(path), f"{path.name} (auto-detected)"
    except Exception:
        return None, None


def get_df() -> pd.DataFrame | None:
    return st.session_state.get(CACHE_KEY)


def get_source() -> str | None:
    return st.session_state.get(SOURCE_KEY)


def set_df(df: pd.DataFrame, source: str) -> None:
    st.session_state[CACHE_KEY] = df
    st.session_state[SOURCE_KEY] = source
    # Invalidate the upload signature so the same filename isn't re-read.
    st.session_state.pop("_titanic_upload_sig", None)


def init_session() -> None:
    if CACHE_KEY in st.session_state:
        return
    df, source = _load_from_disk()
    st.session_state[CACHE_KEY] = df
    st.session_state[SOURCE_KEY] = source


def reload_from_disk() -> None:
    st.session_state.pop(CACHE_KEY, None)
    st.session_state.pop(SOURCE_KEY, None)
    st.session_state.pop("_titanic_upload_sig", None)
    init_session()