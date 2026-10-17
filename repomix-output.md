This file is a merged representation of a subset of the codebase, containing files not matching ignore patterns, combined into a single document by Repomix.

# File Summary

## Purpose
This file contains a packed representation of a subset of the repository's contents that is considered the most important context.
It is designed to be easily consumable by AI systems for analysis, code review,
or other automated processes.

## File Format
The content is organized as follows:
1. This summary section
2. Repository information
3. Directory structure
4. Repository files (if enabled)
5. Multiple file entries, each consisting of:
  a. A header with the file path (## File: path/to/file)
  b. The full contents of the file in a code block

## Usage Guidelines
- This file should be treated as read-only. Any changes should be made to the
  original repository files, not this packed version.
- When processing this file, use the file path to distinguish
  between different files in the repository.
- Be aware that this file may contain sensitive information. Handle it with
  the same level of security as you would the original repository.

## Notes
- Some files may have been excluded based on .gitignore rules and Repomix's configuration
- Binary files are not included in this packed representation. Please refer to the Repository Structure section for a complete list of file paths, including binary files
- Files matching these patterns are excluded: questions.csv, skill.md
- Files matching patterns in .gitignore are excluded
- Files matching default ignore patterns are excluded
- Files are sorted by Git change count (files with more changes are at the bottom)

# Directory Structure
```
core/
  __init__.py
  data.py
  quiz_engine.py
  sql_data.py
  state.py
  ui.py
views/
  __init__.py
  quiz.py
  sql.py
  welcome.py
app.py
README.md
```

# Files

## File: core/__init__.py
```python
"""Shared core modules for the interview-prep app."""
```

## File: core/data.py
```python
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

DEFAULT_CSV_NAME = "questions.csv"
DEFAULT_CSV_PATH = Path(__file__).resolve().parent.parent / DEFAULT_CSV_NAME


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
    """Load the default CSV once per session and store it in session state."""
    if "df" in st.session_state:
        return

    if DEFAULT_CSV_PATH.exists():
        try:
            st.session_state["df"] = prepare(read_csv_from_path(str(DEFAULT_CSV_PATH)))
            st.session_state["df_source"] = DEFAULT_CSV_NAME
            st.session_state["df_error"] = None
        except Exception as exc:  # noqa: BLE001
            st.session_state["df"] = None
            st.session_state["df_source"] = None
            st.session_state["df_error"] = str(exc)
    else:
        st.session_state["df"] = None
        st.session_state["df_source"] = None
        st.session_state["df_error"] = None


def set_df(df: pd.DataFrame, source: str) -> None:
    """Replace the active dataframe (e.g. after an upload)."""
    st.session_state["df"] = df
    st.session_state["df_source"] = source
    st.session_state["df_error"] = None
```

## File: core/quiz_engine.py
```python
"""Reusable question-flow renderer shared by every quiz page.

Callers are responsible for:
  1. `state.init_quiz_state(prefix=...)`
  2. calling `state.start_quiz(..., prefix=...)` when the user clicks Start
  3. passing the already-filtered dataframe in `df`
"""

import pandas as pd
import streamlit as st

from core import data, state, ui


def render_question_flow(df: pd.DataFrame, *, prefix: str = "") -> None:
    order = state.get_state(prefix, "order", [])
    total = len(order)

    if total == 0:
        st.info("No questions in the current quiz. Start one to begin.")
        return

    pos = max(0, min(state.get_state(prefix, "pos", 0), total - 1))
    state.set_state(prefix, "pos", pos)
    qid = order[pos]

    if qid not in df.index:
        st.warning("The question set changed. Please start the quiz again.")
        state.reset_quiz(prefix)
        st.stop()

    row = df.loc[qid]

    # Header
    head_left, head_right = st.columns([3, 1])
    with head_left:
        st.markdown(f"**Question {pos + 1} of {total}**")
    with head_right:
        responses = state.get_state(prefix, "responses", {})
        st.caption(f"Answered: {len(responses)} / {total}")

    ui.render_question_badges(row)
    st.progress((pos + 1) / total)

    # Stem
    with st.container(border=True):
        st.markdown(row["question"])

    # Options
    perm = state.answer_order_for(qid, row, prefix=prefix)
    display_answers = [row[data.ANSWER_COLS[i]] for i in perm]
    option_labels = [
        f"**{data.LETTERS[i]}.** {text}"
        for i, text in enumerate(display_answers)
    ]

    revealed_set = state.get_state(prefix, "revealed", set())
    revealed = qid in revealed_set
    widget_key = f"{prefix}radio_{state.get_state(prefix, 'quiz_id')}_{qid}"

    selection = st.radio(
        "Select one answer:",
        options=option_labels,
        index=None,
        key=widget_key,
        disabled=revealed,
        label_visibility="collapsed",
    )
    selected_pos = option_labels.index(selection) if selection is not None else None

    if not revealed:
        if st.button(
            "✅ Submit answer",
            type="primary",
            disabled=selected_pos is None,
            key=f"{prefix}submit",
        ):
            responses = state.get_state(prefix, "responses", {})
            responses[qid] = selected_pos
            state.set_state(prefix, "responses", responses)
            revealed_set = state.get_state(prefix, "revealed", set())
            revealed_set.add(qid)
            state.set_state(prefix, "revealed", revealed_set)
            st.rerun()
    else:
        responses = state.get_state(prefix, "responses", {})
        chosen_pos = responses.get(qid)
        correct_pos = state.correct_position(qid, row, prefix=prefix)
        correct_text = display_answers[correct_pos]

        if chosen_pos == correct_pos:
            st.success("✅ **Correct!**")
        else:
            st.error(
                f"❌ **Incorrect.** The correct answer is "
                f"**{data.LETTERS[correct_pos]}. {correct_text}**"
            )

        with st.container(border=True):
            st.markdown("#### 💡 Explanation")
            st.markdown(row["explanation"] or "_No explanation provided._")

    # Nav
    nav_left, nav_mid, nav_right = st.columns([1, 2, 1])
    with nav_left:
        if st.button(
            "⬅️ Previous",
            use_container_width=True,
            disabled=pos == 0,
            key=f"{prefix}prev",
        ):
            state.set_state(prefix, "pos", pos - 1)
            st.rerun()
    with nav_right:
        if st.button(
            "Next ➡️",
            use_container_width=True,
            disabled=pos >= total - 1,
            key=f"{prefix}next",
        ):
            state.set_state(prefix, "pos", pos + 1)
            st.rerun()

    # Summary
    st.divider()
    responses = state.get_state(prefix, "responses", {})
    answered_total = len(responses)
    n_correct = sum(
        1 for q in responses if state.is_correct(q, df.loc[q], prefix=prefix)
    )

    with st.expander(
        f"📊 Session summary & review ({answered_total}/{total} answered)"
    ):
        ui.render_review_section(
            df, answered_total, n_correct, total, prefix=prefix
        )

    if answered_total == total and total > 0:
        st.balloons()
        st.success(
            f"🎉 Quiz complete — final score **{n_correct}/{total}** "
            f"({100 * n_correct / total:.0f}%)."
        )
```

## File: core/sql_data.py
```python
"""Sample warehouse for the SQL training page (in-memory SQLite)."""

import sqlite3

import streamlit as st

SAMPLE_DATA = {
    "customers": {
        "schema": "customer_id INTEGER PRIMARY KEY, name TEXT, signup_date DATE, country TEXT, segment TEXT",
        "columns": ["customer_id", "name", "signup_date", "country", "segment"],
        "rows": [
            (1, "Alice", "2023-01-15", "FR", "Enterprise"),
            (2, "Bob",   "2023-02-20", "US", "SMB"),
            (3, "Carol", "2023-03-10", "FR", "SMB"),
            (4, "Dan",   "2023-04-05", "DE", "Enterprise"),
            (5, "Eve",   "2023-05-12", "US", "Enterprise"),
            (6, "Frank", "2023-06-01", "FR", "SMB"),
        ],
    },
    "orders": {
        "schema": "order_id INTEGER PRIMARY KEY, customer_id INTEGER, order_date DATE, amount REAL, status TEXT",
        "columns": ["order_id", "customer_id", "order_date", "amount", "status"],
        "rows": [
            (101, 1, "2024-01-10", 250.00, "shipped"),
            (102, 1, "2024-02-15", 150.00, "shipped"),
            (103, 2, "2024-01-20", 500.00, "cancelled"),
            (104, 3, "2024-03-05",  75.50, "shipped"),
            (105, 3, "2024-03-20", 120.00, "shipped"),
            (106, 4, "2024-02-25", 800.00, "returned"),
            (107, 5, "2024-04-01", 300.00, "shipped"),
            (108, 1, "2024-04-15",  90.00, "shipped"),
        ],
    },
    "order_items": {
        "schema": "item_id INTEGER PRIMARY KEY, order_id INTEGER, product_id INTEGER, quantity INTEGER, unit_price REAL",
        "columns": ["item_id", "order_id", "product_id", "quantity", "unit_price"],
        "rows": [
            (1001, 101, 1, 2,  75.00),
            (1002, 101, 2, 1, 100.00),
            (1003, 102, 3, 3,  50.00),
            (1004, 103, 1, 5, 100.00),
            (1005, 104, 2, 1,  75.50),
            (1006, 105, 4, 2,  60.00),
            (1007, 106, 3, 4, 200.00),
            (1008, 107, 1, 3, 100.00),
            (1009, 108, 2, 1,  90.00),
        ],
    },
    "products": {
        "schema": "product_id INTEGER PRIMARY KEY, name TEXT, category TEXT, list_price REAL",
        "columns": ["product_id", "name", "category", "list_price"],
        "rows": [
            (1, "Widget",  "Hardware",  75.00),
            (2, "Gadget",  "Hardware", 100.00),
            (3, "License", "Software",  50.00),
            (4, "Support", "Services",  60.00),
        ],
    },
    "events": {
        "schema": "event_id INTEGER PRIMARY KEY, customer_id INTEGER, event_type TEXT, event_ts TIMESTAMP, page TEXT",
        "columns": ["event_id", "customer_id", "event_type", "event_ts", "page"],
        "rows": [
            (1, 1, "page_view",  "2024-01-10 10:00:00", "/home"),
            (2, 1, "page_view",  "2024-01-10 10:05:00", "/products"),
            (3, 1, "add_to_cart", "2024-01-10 10:10:00", "/cart"),
            (4, 2, "page_view",  "2024-01-20 14:00:00", "/home"),
            (5, 3, "page_view",  "2024-03-05 09:00:00", "/products"),
            (6, 3, "purchase",   "2024-03-05 09:15:00", "/checkout"),
            (7, 5, "page_view",  "2024-04-01 16:00:00", "/home"),
        ],
    },
}


def _build_db() -> sqlite3.Connection:
    conn = sqlite3.connect(":memory:", check_same_thread=False)
    for name, tbl in SAMPLE_DATA.items():
        conn.execute(f"CREATE TABLE {name} ({tbl['schema']})")
        placeholders = ",".join(["?"] * len(tbl["columns"]))
        conn.executemany(
            f"INSERT INTO {name} VALUES ({placeholders})",
            tbl["rows"],
        )
    conn.commit()
    return conn


def get_db() -> sqlite3.Connection:
    if "_sql_db" not in st.session_state:
        st.session_state["_sql_db"] = _build_db()
    return st.session_state["_sql_db"]


def reset_db() -> None:
    old = st.session_state.get("_sql_db")
    if old is not None:
        try:
            old.close()
        except Exception:
            pass
    st.session_state["_sql_db"] = _build_db()
```

## File: core/state.py
```python
"""Session-state helpers for the quiz flow.

All keys are prefixed so multiple quizzes (general, SQL, ...) can run
independently within one session. `prefix=""` keeps the original bare keys,
so existing callers keep working unchanged.

NOTE: helper names are `get_state` / `set_state` (not `get` / `set`) so we
never shadow Python's builtin `set()`.
"""

import random

import streamlit as st


def _key(prefix: str, name: str) -> str:
    return f"{prefix}{name}" if prefix else name


def init_quiz_state(prefix: str = "") -> None:
    defaults = {
        "started": False,
        "quiz_id": 0,
        "order": [],
        "pos": 0,
        "responses": {},
        "revealed": set(),
        "answer_orders": {},
        "shuffle_answers": True,
    }
    for name, value in defaults.items():
        key = _key(prefix, name)
        if key not in st.session_state:
            st.session_state[key] = value


def get_state(prefix: str, name: str, default=None):
    return st.session_state.get(_key(prefix, name), default)


def set_state(prefix: str, name: str, value) -> None:
    st.session_state[_key(prefix, name)] = value


def start_quiz(
    pool_indices,
    shuffle_questions: bool,
    shuffle_answers: bool,
    *,
    prefix: str = "",
) -> None:
    order = list(pool_indices)
    if shuffle_questions:
        random.shuffle(order)

    st.session_state[_key(prefix, "quiz_id")] += 1
    st.session_state[_key(prefix, "order")] = order
    st.session_state[_key(prefix, "pos")] = 0
    st.session_state[_key(prefix, "responses")] = {}
    st.session_state[_key(prefix, "revealed")] = set()
    st.session_state[_key(prefix, "answer_orders")] = {}
    st.session_state[_key(prefix, "shuffle_answers")] = shuffle_answers
    st.session_state[_key(prefix, "started")] = True


def reset_quiz(prefix: str = "") -> None:
    set_state(prefix, "started", False)
    set_state(prefix, "order", [])
    set_state(prefix, "pos", 0)
    set_state(prefix, "responses", {})
    set_state(prefix, "revealed", set())
    set_state(prefix, "answer_orders", {})


def answer_order_for(qid, row, *, prefix: str = "") -> list:
    orders = st.session_state[_key(prefix, "answer_orders")]
    if qid not in orders:
        perm = [0, 1, 2, 3]
        if st.session_state[_key(prefix, "shuffle_answers")]:
            random.shuffle(perm)
        orders[qid] = perm
    return orders[qid]


def correct_position(qid, row, *, prefix: str = "") -> int:
    return st.session_state[_key(prefix, "answer_orders")][qid].index(
        int(row["correct_index"])
    )


def is_correct(qid, row, *, prefix: str = "") -> bool:
    return (
        st.session_state[_key(prefix, "responses")].get(qid)
        == correct_position(qid, row, prefix=prefix)
    )
```

## File: core/ui.py
```python
"""Shared UI components."""

import pandas as pd
import streamlit as st

from core.data import ANSWER_COLS, LETTERS, split_multi


def _key(prefix: str, name: str) -> str:
    return f"{prefix}{name}" if prefix else name


def render_question_badges(row) -> None:
    parts = [f"🏷️ {row['theme']}"]
    sec = split_multi(row["secondary_themes"])
    if sec:
        parts.append("➕ " + ", ".join(sec))
    parts.append(f"📊 {row['difficulty']}")
    verts = split_multi(row["vertical"])
    if verts:
        parts.append("🌍 " + ", ".join(verts))
    st.caption(" · ".join(parts))


def render_review_section(
    df: pd.DataFrame,
    answered_total: int,
    n_correct: int,
    total: int,
    *,
    prefix: str = "",
) -> None:
    """Render the full session-summary body (metrics + breakdowns + table)."""
    if answered_total == 0:
        st.info("Answer some questions to see your summary here.")
        return

    acc = 100.0 * n_correct / answered_total
    m1, m2, m3 = st.columns(3)
    m1.metric("Answered", f"{answered_total} / {total}")
    m2.metric("Correct", n_correct)
    m3.metric("Accuracy", f"{acc:.0f}%")

    responses = st.session_state.get(_key(prefix, "responses"), {})
    answer_orders = st.session_state.get(_key(prefix, "answer_orders"), {})

    review_rows = []
    for q, chosen in responses.items():
        r = df.loc[q]
        q_perm = answer_orders[q]
        q_display = [r[ANSWER_COLS[i]] for i in q_perm]
        c_pos = q_perm.index(int(r["correct_index"]))
        review_rows.append(
            {
                "Theme": r["theme"],
                "Secondary themes": r["secondary_themes"],
                "Difficulty": r["difficulty"],
                "Vertical": r["vertical"],
                "Question": r["question"],
                "Your answer": q_display[chosen] if chosen is not None else "—",
                "Correct answer": q_display[c_pos],
                "Result": "✅" if chosen == c_pos else "❌",
                "_themes": [r["theme"], *split_multi(r["secondary_themes"])],
                "_correct": chosen == c_pos,
            }
        )
    review_df = pd.DataFrame(review_rows)

    theme_rows = []
    for _, rr in review_df.iterrows():
        for t in rr["_themes"]:
            if t:
                theme_rows.append({"Theme": t, "Correct": rr["_correct"]})
    if theme_rows:
        theme_df = pd.DataFrame(theme_rows)
        by_theme = (
            theme_df.groupby("Theme")
            .agg(Answered=("Correct", "size"), Correct=("Correct", "sum"))
            .reset_index()
        )
        by_theme["Accuracy"] = (
            100 * by_theme["Correct"] / by_theme["Answered"]
        ).round(0).astype(int).astype(str) + " %"
        st.markdown("##### Accuracy by theme (primary + secondary)")
        st.dataframe(by_theme, hide_index=True, use_container_width=True)

    by_diff = (
        review_df[["Difficulty", "_correct"]]
        .groupby("Difficulty")
        .agg(Answered=("_correct", "size"), Correct=("_correct", "sum"))
        .reset_index()
    )
    by_diff["Accuracy"] = (
        100 * by_diff["Correct"] / by_diff["Answered"]
    ).round(0).astype(int).astype(str) + " %"
    st.markdown("##### Accuracy by difficulty")
    st.dataframe(by_diff, hide_index=True, use_container_width=True)

    vert_rows = []
    for _, rr in review_df.iterrows():
        for v in split_multi(rr["Vertical"]) or ["general"]:
            vert_rows.append({"Vertical": v, "Correct": rr["_correct"]})
    if vert_rows:
        vert_df = pd.DataFrame(vert_rows)
        by_vert = (
            vert_df.groupby("Vertical")
            .agg(Answered=("Correct", "size"), Correct=("Correct", "sum"))
            .reset_index()
        )
        by_vert["Accuracy"] = (
            100 * by_vert["Correct"] / by_vert["Answered"]
        ).round(0).astype(int).astype(str) + " %"
        st.markdown("##### Accuracy by vertical")
        st.dataframe(by_vert, hide_index=True, use_container_width=True)

    st.markdown("##### Full review")
    st.dataframe(
        review_df.drop(columns=["_themes", "_correct"]),
        hide_index=True,
        use_container_width=True,
    )
```

## File: views/__init__.py
```python
"""Page modules for the interview-prep app."""
```

## File: views/quiz.py
```python
"""Interactive quiz page."""

import pandas as pd
import streamlit as st

from core import data, quiz_engine, state


def render() -> None:
    state.init_quiz_state()

    with st.sidebar:
        _render_sidebar()

    df = st.session_state.get("df")
    if df is None:
        st.info("No questions loaded. Upload a CSV in the sidebar to begin.")
        return

    if not state.get_state("", "started") or not state.get_state("", "order"):
        st.title("🧠 Quiz")
        st.markdown(
            "Pick your filters in the sidebar and press "
            "**Start / Restart quiz** to begin."
        )
        return

    quiz_engine.render_question_flow(df)


def _render_sidebar() -> None:
    st.header("⚙️ Settings")

    uploaded = st.file_uploader(
        "Upload a questions CSV", type=["csv"], key="quiz_uploader"
    )
    if uploaded is not None and uploaded.name != st.session_state.get("df_source"):
        try:
            data.set_df(data.prepare(pd.read_csv(uploaded)), uploaded.name)
        except Exception as exc:  # noqa: BLE001
            st.error(f"Could not read the uploaded CSV: {exc}")
            st.stop()

    df = st.session_state.get("df")
    if df is None:
        st.warning(
            f"No file uploaded and `{data.DEFAULT_CSV_NAME}` was not found."
        )
        st.stop()

    source = st.session_state.get("df_source") or "—"
    st.caption(f"Loaded: `{source}` — {len(df)} question(s)")

    themes = data.all_themes(df)
    selected_themes = st.multiselect("Themes", options=themes, default=themes)

    selected_diff = st.multiselect(
        "Difficulty", options=data.DIFFICULTIES, default=data.DIFFICULTIES
    )

    verticals = data.all_verticals(df)
    selected_verticals = st.multiselect(
        "Verticals", options=verticals, default=verticals
    )

    shuffle_questions = st.checkbox("Shuffle questions", value=False)
    shuffle_answers = st.checkbox("Shuffle answer options", value=True)

    sel_t = set(selected_themes)
    sel_d = {d.lower() for d in selected_diff}
    sel_v = set(selected_verticals)

    mask = pd.Series(True, index=df.index)
    mask &= df.apply(lambda r: data.theme_matches(r, sel_t), axis=1)
    if sel_d:
        mask &= df["difficulty"].isin(sel_d)
    mask &= df.apply(lambda r: data.vertical_matches(r, sel_v), axis=1)

    pool = df[mask]
    st.caption(f"Pool: **{len(pool)}** question(s)")

    if st.button(
        "🚀 Start / Restart quiz",
        type="primary",
        use_container_width=True,
        disabled=pool.empty,
    ):
        state.start_quiz(pool.index.tolist(), shuffle_questions, shuffle_answers)
        st.rerun()

    if state.get_state("", "started") and state.get_state("", "responses"):
        answered = len(state.get_state("", "responses"))
        n_correct = sum(
            1 for q in state.get_state("", "responses")
            if state.is_correct(q, df.loc[q])
        )
        accuracy = (100.0 * n_correct / answered) if answered else 0.0
        st.divider()
        st.subheader("📈 Score")
        st.metric("Correct", f"{n_correct} / {answered}")
        st.metric("Accuracy", f"{accuracy:.0f}%")

    st.divider()
    template_header = ",".join(
        data.REQUIRED_COLS + list(data.OPTIONAL_DEFAULTS.keys())
    )
    st.download_button(
        "⬇️ Download CSV template",
        data=template_header + "\n",
        file_name="questions_template.csv",
        mime="text/csv",
        use_container_width=True,
    )
```

## File: views/sql.py
```python
"""SQL training page: quiz, playground, cheatsheet, schema reference."""

import pandas as pd
import streamlit as st

from core import data, quiz_engine, state
from core.sql_data import SAMPLE_DATA, get_db, reset_db

SQL_THEME = "SQL & Data Manipulation"
SQL_PREFIX = "sql_"
DEFAULT_QUERY = "SELECT * FROM customers LIMIT 5;"


def render() -> None:
    state.init_quiz_state(prefix=SQL_PREFIX)

    with st.sidebar:
        st.header("📁 Dataset")
        uploaded = st.file_uploader(
            "Upload a questions CSV", type=["csv"], key="sql_uploader"
        )
        if (
            uploaded is not None
            and uploaded.name != st.session_state.get("df_source")
        ):
            try:
                data.set_df(data.prepare(pd.read_csv(uploaded)), uploaded.name)
            except Exception as exc:  # noqa: BLE001
                st.error(f"Could not read the uploaded CSV: {exc}")

        df = st.session_state.get("df")
        if df is not None:
            st.caption(
                f"Loaded: `{st.session_state.get('df_source')}` — "
                f"{len(df)} question(s)"
            )
        else:
            st.warning("No questions loaded.")

    st.title("🗄️ SQL Training")
    st.markdown(
        "Practice SQL interview questions, run queries against a sample "
        "warehouse, and review the patterns that come up most often."
    )

    tab_quiz, tab_play, tab_cheat, tab_schema = st.tabs(
        ["🧠 Quiz", "▶️ Playground", "📚 Cheatsheet", "🗂️ Schema"]
    )

    with tab_quiz:
        _render_quiz_tab()
    with tab_play:
        _render_playground_tab()
    with tab_cheat:
        _render_cheatsheet_tab()
    with tab_schema:
        _render_schema_tab()


# --------------------------------------------------------------------------- #
#  Quiz tab
# --------------------------------------------------------------------------- #
def _sql_questions(df: pd.DataFrame) -> pd.DataFrame:
    mask = (df["theme"] == SQL_THEME) | df["secondary_themes"].apply(
        lambda s: SQL_THEME in data.split_multi(s)
    )
    return df[mask]


def _render_quiz_tab() -> None:
    df = st.session_state.get("df")
    if df is None:
        st.info("Load a questions CSV on the **Quiz** page first.")
        return

    sql_df = _sql_questions(df)
    if sql_df.empty:
        st.warning(
            f"No SQL questions found in the loaded dataset. "
            f"(Expected theme: `{SQL_THEME}`.)"
        )
        return

    if not state.get_state(SQL_PREFIX, "started"):
        st.markdown(f"**{len(sql_df)} SQL questions available.**")

        difficulties = st.multiselect(
            "Difficulty",
            options=data.DIFFICULTIES,
            default=data.DIFFICULTIES,
            key="sql_diff_filter",
        )
        c1, c2 = st.columns(2)
        with c1:
            shuffle_q = st.checkbox(
                "Shuffle questions", value=True, key="sql_shuffle_q"
            )
        with c2:
            shuffle_a = st.checkbox(
                "Shuffle answers", value=True, key="sql_shuffle_a"
            )

        pool = sql_df[sql_df["difficulty"].isin({d.lower() for d in difficulties})]
        st.caption(f"Pool: **{len(pool)}** question(s)")

        if st.button(
            "🚀 Start SQL quiz",
            type="primary",
            disabled=pool.empty,
            key="sql_start_btn",
        ):
            state.start_quiz(
                pool.index.tolist(), shuffle_q, shuffle_a, prefix=SQL_PREFIX
            )
            st.rerun()
        return

    if st.button("🔄 Restart SQL quiz", key="sql_restart_btn"):
        state.reset_quiz(SQL_PREFIX)
        st.rerun()

    quiz_engine.render_question_flow(sql_df, prefix=SQL_PREFIX)


# --------------------------------------------------------------------------- #
#  Playground tab
# --------------------------------------------------------------------------- #
def _render_playground_tab() -> None:
    st.markdown(
        "Write SQL against the sample warehouse (SQLite). "
        "Table definitions and sample rows are in the **Schema** tab."
    )

    if "sql_playground_query" not in st.session_state:
        st.session_state["sql_playground_query"] = DEFAULT_QUERY

    query = st.text_area(
        "SQL query",
        height=200,
        key="sql_playground_query",
        placeholder="SELECT * FROM orders WHERE amount > 100;",
    )
    st.caption(
        "Try: `SELECT * FROM orders;` · "
        "`SELECT c.name, SUM(o.amount) FROM customers c JOIN orders o "
        "ON o.customer_id = c.customer_id GROUP BY c.name;`"
    )

    c1, c2, c3 = st.columns([1, 1, 1])
    with c1:
        run = st.button("▶️ Run", type="primary", key="sql_run_btn")
    with c2:
        reset_query = st.button("🔄 Reset query", key="sql_reset_query_btn")
    with c3:
        reset_db_btn = st.button("🗑️ Reset DB", key="sql_reset_db_btn")

    if reset_query:
        st.session_state["sql_playground_query"] = DEFAULT_QUERY
        st.rerun()

    if reset_db_btn:
        reset_db()
        st.success("Sample database reset.")
        st.rerun()

    if run:
        if not query.strip():
            st.warning("Write a query first.")
            return
        try:
            conn = get_db()
            result = pd.read_sql_query(query, conn)
            st.success(f"{len(result)} row(s) returned")
            st.dataframe(result, use_container_width=True, hide_index=True)
        except Exception as exc:  # noqa: BLE001
            st.error(f"Query error: `{exc}`")


# --------------------------------------------------------------------------- #
#  Cheatsheet tab
# --------------------------------------------------------------------------- #
def _render_cheatsheet_tab() -> None:
    st.markdown(
        "The SQL patterns that come up most often in DS / consulting "
        "interviews."
    )

    _cheat_section(
        "1. Keep the latest row per group (deduplication)",
        "`ROW_NUMBER() OVER (PARTITION BY key ORDER BY date DESC)`",
        """SELECT *
FROM (
    SELECT *,
           ROW_NUMBER() OVER (
               PARTITION BY customer_id
               ORDER BY order_date DESC
           ) AS rn
    FROM orders
) t
WHERE rn = 1;""",
        "**Why it wins:** `SELECT DISTINCT` keeps an arbitrary row when other "
        "columns differ. `GROUP BY` loses non-key columns. The window "
        "function is deterministic and preserves every column.",
    )

    _cheat_section(
        "2. Find records missing in another table (anti-join)",
        "`LEFT JOIN ... WHERE right.key IS NULL`, or `NOT EXISTS`",
        """-- Customers with no orders
SELECT c.*
FROM customers c
LEFT JOIN orders o ON o.customer_id = c.customer_id
WHERE o.order_id IS NULL;""",
        "**Why it wins:** `NOT IN` is dangerous — if the subquery returns any "
        "NULL, the whole predicate becomes NULL and returns no rows. "
        "`NOT EXISTS` is often the safest and most performant.",
    )

    _cheat_section(
        "3. Running total / moving average",
        "`SUM(...) OVER (PARTITION BY ... ORDER BY ... ROWS BETWEEN ...)`",
        """SELECT
    customer_id,
    order_date,
    amount,
    SUM(amount) OVER (
        PARTITION BY customer_id
        ORDER BY order_date
        ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW
    ) AS running_total,
    AVG(amount) OVER (
        PARTITION BY customer_id
        ORDER BY order_date
        ROWS BETWEEN 2 PRECEDING AND CURRENT ROW
    ) AS moving_avg_3
FROM orders;""",
        "**Why it wins:** self-joins or correlated subqueries compute the "
        "same thing but are slower and harder to read. Always specify "
        "`ROWS BETWEEN ...` — the default frame can surprise you.",
    )

    _cheat_section(
        "4. Row number vs. rank vs. dense rank",
        "`ROW_NUMBER` / `RANK` / `DENSE_RANK`",
        """SELECT
    customer_id,
    amount,
    ROW_NUMBER() OVER (PARTITION BY customer_id ORDER BY amount DESC) AS rn,
    RANK()       OVER (PARTITION BY customer_id ORDER BY amount DESC) AS rnk,
    DENSE_RANK() OVER (PARTITION BY customer_id ORDER BY amount DESC) AS drnk
FROM orders;""",
        "**Difference:** for ties, `ROW_NUMBER` gives 1, 2, 3…; `RANK` gives "
        "1, 1, 3…; `DENSE_RANK` gives 1, 1, 2… Use `RANK` for 'top N per "
        "group' where ties should be included.",
    )

    _cheat_section(
        "5. Grain issues — fan-out from joins",
        "Join on the correct grain, or pre-aggregate",
        """-- Buggy: inflates revenue because one order has many items
SELECT o.customer_id, SUM(o.amount) AS revenue
FROM orders o
JOIN order_items oi ON oi.order_id = o.order_id
GROUP BY o.customer_id;

-- Correct: aggregate items first, then join
SELECT o.customer_id, SUM(o.amount) AS revenue
FROM orders o
LEFT JOIN (
    SELECT order_id, SUM(quantity * unit_price) AS items_total
    FROM order_items
    GROUP BY order_id
) oi ON oi.order_id = o.order_id
GROUP BY o.customer_id;""",
        "**Why it bites:** every one-to-many join replicates the parent row. "
        "If you `SUM` a parent column across the join, you double-count. "
        "Always know the grain of each table before joining.",
    )

    _cheat_section(
        "6. NULL handling in comparisons",
        "`IS NULL` / `IS NOT NULL`; `COALESCE` for defaults",
        """SELECT *
FROM customers
WHERE country IS NULL;

SELECT
    customer_id,
    COALESCE(country, 'UNKNOWN') AS country_clean
FROM customers;""",
        "**Watch out:** `col = NULL` is never true, and `col <> 'x'` silently "
        "excludes NULL rows. This is the #1 source of 'missing rows' bugs "
        "in analytics SQL.",
    )

    _cheat_section(
        "7. Cohort retention",
        "First-purchase month + subsequent activity",
        """WITH first_order AS (
    SELECT customer_id,
           MIN(order_date) AS first_date
    FROM orders
    GROUP BY customer_id
)
SELECT
    strftime('%Y-%m', fo.first_date) AS cohort,
    strftime('%Y-%m', o.order_date)  AS activity_month,
    COUNT(DISTINCT o.customer_id)    AS active_customers
FROM orders o
JOIN first_order fo USING (customer_id)
GROUP BY cohort, activity_month
ORDER BY cohort, activity_month;""",
        "**Why it's asked:** cohort retention is the bread-and-butter of "
        "marketing analytics at Jakala and Artefact. Get the two-step "
        "pattern (first-date per user, then join and group) into muscle "
        "memory.",
    )


def _cheat_section(title: str, pattern: str, code: str, note: str) -> None:
    with st.expander(title, expanded=False):
        st.markdown(f"**Pattern:** {pattern}")
        st.code(code, language="sql")
        st.markdown(note)


# --------------------------------------------------------------------------- #
#  Schema tab
# --------------------------------------------------------------------------- #
def _render_schema_tab() -> None:
    st.markdown(
        "Sample warehouse available in the **Playground** tab. "
        "All tables live in an in-memory SQLite database."
    )

    for name, tbl in SAMPLE_DATA.items():
        with st.expander(f"`{name}`", expanded=False):
            st.code(tbl["schema"], language="sql")
            st.dataframe(
                pd.DataFrame(tbl["rows"], columns=tbl["columns"]),
                use_container_width=True,
                hide_index=True,
            )
```

## File: views/welcome.py
```python
"""Welcome / landing page."""

import streamlit as st


def render() -> None:
    st.title("🧠 ML / DS / AI Consulting Interview Prep")
    st.markdown(
        r"""
        Practice multiple-choice questions on machine learning, statistics,
        data science and AI consulting.

        **How it works**

        1. Open the **Quiz** page from the sidebar.
        2. Upload a CSV in the sidebar, or let the app pick up
           `questions.csv` sitting next to `app.py`.
        3. Filter by **themes**, **difficulty** and **verticals**, then press
           **Start / Restart quiz**.
        """
    )

    st.subheader("CSV schema")
    st.code(
        "question,answer1,answer2,answer3,answer4,correctanswer,"
        "explanation,theme,difficulty,secondary_themes,vertical",
        language="text",
    )

    st.markdown(
        r"""
        * `correctanswer` accepts `1`-`4`, `answer1`-`answer4`, or the exact
          text of the correct option.
        * `difficulty` is `easy`, `medium` or `hard` (defaults to `medium`).
        * `secondary_themes` is a semicolon-separated list of extra themes.
        * `vertical` is a semicolon-separated list of industries
          (`general`, `finance`, `healthcare`, `retail`, `telecom`, ...).
          `general` questions always appear when any vertical is selected.
        * LaTeX is supported everywhere:
          `$P(A\mid B) = \frac{P(B\mid A)P(A)}{P(B)}$` or a `$$ ... $$` block.
        """
    )

    st.divider()
    df = st.session_state.get("df")
    source = st.session_state.get("df_source")
    error = st.session_state.get("df_error")

    if df is not None:
        st.success(
            f"Loaded **{len(df)}** questions from `{source}`. "
            "Head to the **Quiz** page to begin."
        )
    else:
        msg = "No questions loaded yet. Open the **Quiz** page to upload a CSV."
        if error:
            msg += f"\n\n_Startup error: `{error}`_"
        st.warning(msg)
```

## File: app.py
```python
"""
ML / DS / AI Consulting interview prep — entry point.

Run with:
    streamlit run app.py
"""

import streamlit as st

st.set_page_config(
    page_title="ML / DS / AI Interview Prep",
    page_icon="🧠",
    layout="wide",
)

from core import data  # noqa: E402
from views import quiz, sql, welcome  # noqa: E402

data.init_session()

NAV_PAGES = [
    st.Page(
        welcome.render,
        title="Welcome",
        icon="🏠",
        url_path="welcome",
        default=True,
    ),
    st.Page(
        quiz.render,
        title="Quiz",
        icon="🧠",
        url_path="quiz",
    ),
    st.Page(
        sql.render,
        title="SQL Training",
        icon="🗄️",
        url_path="sql",
    ),
]

st.navigation(NAV_PAGES).run()
```

## File: README.md
```markdown
# streamlit-ds-training
Data sicen
```
