"""Welcome / landing page."""

import streamlit as st

from core import data


def render() -> None:
    st.title("🧠 ML / DS / AI Consulting Interview Prep")
    st.markdown(
        r"""
        Practice multiple-choice questions on machine learning, statistics,
        data science and AI consulting.

        **How it works**

        1. Drop one or more CSV files (matching the schema below) into
           `quiz_questions/`. Every `*.csv` in that folder is loaded and
           merged into a single question pool.
        2. Open the **Quiz** page, optionally upload a CSV in the sidebar to
           replace the pool for the current session, filter by **themes**,
           **difficulty** and **verticals**, and press **Start / Restart quiz**.
        3. For hands-on SQL practice, open **SQL Training** — it has a
           multiple-choice SQL quiz, a **Write SQL** mode where your own
           queries are checked against a reference result set, a playground,
           a cheatsheet, and the schema of the sample warehouse.
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
    sources = st.session_state.get("df_sources") or []
    errors = st.session_state.get("df_errors") or []
    startup_error = st.session_state.get("df_error")

    if df is not None:
        st.success(
            f"Loaded **{len(df)}** question(s) from **{len(sources)}** "
            f"file(s) in `{data.QUESTIONS_DIR.name}/`. "
            "Head to the **Quiz** page to begin."
        )
        with st.expander("Loaded files", expanded=True):
            for s in sources:
                st.markdown(f"- `{s['file']}` — {s['rows']} question(s)")
            if errors:
                st.markdown("**Skipped files**")
                for err in errors:
                    st.markdown(f"- ⚠️ `{err['file']}` — {err['error']}")
    else:
        msg = (
            f"No questions loaded. Add CSV files to "
            f"`{data.QUESTIONS_DIR.name}/` or upload one on the **Quiz** page."
        )
        if startup_error:
            msg += f"\n\n_{startup_error}_"
        st.warning(msg)
        if errors:
            for err in errors:
                st.caption(f"⚠️ `{err['file']}` — {err['error']}")