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
        4. For hands-on SQL practice, open **SQL Training** — it has a
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