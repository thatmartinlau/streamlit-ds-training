"""CSV loading, schema validation, and question-metadata helpers."""

import re
from pathlib import Path

import pandas as pd
import streamlit as st

LETTERS = ["A", "B", "C", "D"]
ANSWER_COLS = ["answer1", "answer2", "answer3", "answer4"]
REQUIRED_COLS = ["question", *ANSWER_COLS, "correctanswer", "explanation", "theme"]
OPTIONAL_DEFAULTS = {
    "difficulty": "medium",
    "secondary_themes": "",
    "vertical": "general",
}
DIFFICULTIES = ["easy", "medium", "hard"]

QUESTIONS_DIR = Path(__file__).resolve().parent.parent / "quiz_questions"


# --------------------------------------------------------------------------- #
#  Parsing helpers
# --------------------------------------------------------------------------- #
def split_multi(value) -> list:
    """Split a `;` / `|` / `,` separated list into trimmed strings."""
    if value is None:
        return []
    s = str(value).strip()
    if not s or s.lower() in {"nan", "none"}:
        return []
    return [p.strip() for p in re.split(r"[;|,]", s) if p.strip()]


@st.cache_data(show_spinner=False)
def read_csv_from_path(path: str) -> pd.DataFrame:
    return pd.read_csv(path)


def correct_index_of(row: pd.Series) -> int:
    """0-based index of the correct answer (accepts 1-4, answerN, or text)."""
    raw = str(row.get("correctanswer", "")).strip()
    low = raw.lower()
    if low in {"1", "2", "3", "4"}:
        return int(low) - 1
    for i in range(1, 5):
        if low in {f"answer{i}", f"a{i}", f"option{i}", f"opt{i}"}:
            return i - 1
    for i, col in enumerate(ANSWER_COLS):
        if low == str(row.get(col, "")).strip().lower():
            return i
    return 0


def prepare(df: pd.DataFrame) -> pd.DataFrame:
    """Validate, clean, and enrich a questions dataframe."""
    df = df.copy()
    df.columns = [str(c).strip().lower() for c in df.columns]

    missing = [c for c in REQUIRED_COLS if c not in df.columns]
    if missing:
        raise ValueError(
            "The CSV is missing required column(s): "
            + ", ".join(f"`{m}`" for m in missing)
        )

    for col in REQUIRED_COLS:
        df[col] = df[col].fillna("").astype(str).str.strip()

    for col, default in OPTIONAL_DEFAULTS.items():
        if col not in df.columns:
            df[col] = default
        df[col] = df[col].fillna(default).astype(str).str.strip()
        df.loc[df[col] == "", col] = default

    df = df[df["question"] != ""].reset_index(drop=True)
    df["theme"] = df["theme"].replace("", "General")
    df["difficulty"] = df["difficulty"].str.lower()
    df.loc[~df["difficulty"].isin(DIFFICULTIES), "difficulty"] = "medium"
    df["correct_index"] = df.apply(correct_index_of, axis=1).astype(int)
    return df


# --------------------------------------------------------------------------- #
#  Question-bundle loading
# --------------------------------------------------------------------------- #
def load_questions_dir(directory: Path) -> tuple[pd.DataFrame | None, list, list]:
    """Load and concatenate every `*.csv` in `directory`.

    Returns ``(df, loaded, errors)``:

    * ``loaded`` is ``[{"file": name, "rows": n}, ...]``,
    * ``errors`` is ``[{"file": name, "error": msg}, ...]`` (skipped files).

    If no file could be loaded, ``df`` is ``None``.
    """
    loaded: list = []
    errors: list = []
    frames: list[pd.DataFrame] = []

    for path in sorted(directory.glob("*.csv")):
        try:
            raw = read_csv_from_path(str(path))
            prepared = prepare(raw)
        except Exception as exc:  # noqa: BLE001
            errors.append({"file": path.name, "error": str(exc)})
            continue

        if prepared.empty:
            errors.append({"file": path.name, "error": "No usable rows."})
            continue

        frames.append(prepared)
        loaded.append({"file": path.name, "rows": len(prepared)})

    if not frames:
        return None, loaded, errors

    df = pd.concat(frames, ignore_index=True)
    return df, loaded, errors


# --------------------------------------------------------------------------- #
#  Filter helpers
# --------------------------------------------------------------------------- #
def all_themes(df: pd.DataFrame) -> list:
    themes = set()
    for _, row in df.iterrows():
        t = str(row["theme"]).strip()
        if t:
            themes.add(t)
        for sec in split_multi(row["secondary_themes"]):
            themes.add(sec)
    return sorted(themes)


def all_verticals(df: pd.DataFrame) -> list:
    vs = set()
    for v in df["vertical"]:
        for part in split_multi(v):
            vs.add(part)
    return sorted(vs)


def theme_matches(row: pd.Series, selected: set) -> bool:
    if not selected:
        return True
    if str(row["theme"]).strip() in selected:
        return True
    return bool(set(split_multi(row["secondary_themes"])) & selected)


def vertical_matches(row: pd.Series, selected: set) -> bool:
    """'general' acts as a wildcard: it always shows when any vertical is selected."""
    if not selected:
        return True
    row_verts = set(split_multi(row["vertical"]))
    if "general" in row_verts:
        return True
    return bool(row_verts & selected)


# --------------------------------------------------------------------------- #
#  Shared-state bootstrap
# --------------------------------------------------------------------------- #
def init_session() -> None:
    """Load every CSV in `quiz_questions/` once per session."""
    if "df" in st.session_state:
        return

    try:
        QUESTIONS_DIR.mkdir(exist_ok=True)
    except OSError as exc:  # noqa: BLE001
        st.session_state["df"] = None
        st.session_state["df_sources"] = []
        st.session_state["df_errors"] = []
        st.session_state["df_error"] = (
            f"Could not create `{QUESTIONS_DIR.name}/`: {exc}"
        )
        return

    df, loaded, errors = load_questions_dir(QUESTIONS_DIR)
    st.session_state["df"] = df
    st.session_state["df_sources"] = loaded
    st.session_state["df_errors"] = errors
    st.session_state["df_error"] = None if df is not None else (
        f"No question files found in `{QUESTIONS_DIR.name}/`."
    )
    st.session_state.pop("df_source", None)
    st.session_state.pop("df_upload_sig", None)


def set_df(df: pd.DataFrame, source: str) -> None:
    """Replace the active dataframe (e.g. after an upload)."""
    st.session_state["df"] = df
    st.session_state["df_sources"] = [{"file": source, "rows": len(df)}]
    st.session_state["df_errors"] = []
    st.session_state["df_error"] = None
    st.session_state["df_source"] = source
    st.session_state["df_upload_sig"] = source


def reload_from_dir() -> None:
    """Drop any upload and re-scan `quiz_questions/` from disk."""
    read_csv_from_path.clear()  # pick up edits to the files
    st.session_state.pop("df", None)
    st.session_state.pop("df_source", None)
    st.session_state.pop("df_upload_sig", None)
    init_session()