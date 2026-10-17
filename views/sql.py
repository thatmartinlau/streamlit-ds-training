"""SQL training page: quiz, free-form challenges, playground, cheatsheet, schema."""

import pandas as pd
import streamlit as st

from core import data, quiz_engine, state
from core.sql_challenges import (
    CHALLENGES,
    check_read_only,
    evaluate,
    get_challenge,
)
from core.sql_data import SAMPLE_DATA, get_db, reset_db

SQL_THEME = "SQL & Data Manipulation"
SQL_PREFIX = "sql_"
DEFAULT_QUERY = "SELECT * FROM customers LIMIT 5;"


def render() -> None:
    state.init_quiz_state(prefix=SQL_PREFIX)

    with st.sidebar:
        _render_dataset_sidebar()

    st.title("🗄️ SQL Training")
    st.markdown(
        "Practice SQL interview questions, **write your own queries** and get "
        "them checked against the expected result, run ad-hoc SQL against a "
        "sample warehouse, and review the patterns that come up most often."
    )

    tab_quiz, tab_write, tab_play, tab_cheat, tab_schema = st.tabs(
        [
            "🧠 Quiz",
            "✍️ Write SQL",
            "▶️ Playground",
            "📚 Cheatsheet",
            "🗂️ Schema",
        ]
    )

    with tab_quiz:
        _render_quiz_tab()
    with tab_write:
        _render_write_tab()
    with tab_play:
        _render_playground_tab()
    with tab_cheat:
        _render_cheatsheet_tab()
    with tab_schema:
        _render_schema_tab()


def _render_dataset_sidebar() -> None:
    st.header("📁 Dataset")

    uploaded = st.file_uploader(
        "Upload a questions CSV", type=["csv"], key="sql_uploader"
    )
    if (
        uploaded is not None
        and uploaded.name != st.session_state.get("df_upload_sig")
    ):
        try:
            data.set_df(data.prepare(pd.read_csv(uploaded)), uploaded.name)
        except Exception as exc:  # noqa: BLE001
            st.error(f"Could not read the uploaded CSV: {exc}")

    if st.button("🔄 Reload from quiz_questions/", use_container_width=True):
        data.reload_from_dir()
        st.rerun()

    df = st.session_state.get("df")
    sources = st.session_state.get("df_sources") or []
    errors = st.session_state.get("df_errors") or []

    if df is None:
        st.warning("No questions loaded.")
        for err in errors:
            st.caption(f"⚠️ `{err['file']}` — {err['error']}")
        return

    if len(sources) == 1 and not errors:
        st.caption(f"Loaded `{sources[0]['file']}` — {len(df)} question(s)")
    else:
        st.caption(f"Loaded {len(sources)} file(s) — {len(df)} question(s)")
        with st.expander("Files", expanded=False):
            for s in sources:
                st.caption(f"`{s['file']}` — {s['rows']} question(s)")
            for err in errors:
                st.caption(f"⚠️ `{err['file']}` skipped — {err['error']}")


# ... rest of the file unchanged (_render_quiz_tab, _render_write_tab,
#     _render_playground_tab, _render_cheatsheet_tab, _render_schema_tab, etc.)