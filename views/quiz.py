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
        st.title("🧠 Quiz")
        st.info(
            "No questions loaded. Upload a CSV in the sidebar, or drop CSV "
            "files into `quiz_questions/` and click **Reload from "
            "`quiz_questions/`**."
        )
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
    if (
        uploaded is not None
        and uploaded.name != st.session_state.get("df_upload_sig")
    ):
        try:
            data.set_df(data.prepare(pd.read_csv(uploaded)), uploaded.name)
        except Exception as exc:  # noqa: BLE001
            st.error(f"Could not read the uploaded CSV: {exc}")
            return

    if st.button("🔄 Reload from quiz_questions/", use_container_width=True):
        data.reload_from_dir()
        st.rerun()

    df = st.session_state.get("df")
    if df is None:
        st.warning(
            "No questions loaded. Upload a CSV or add files to "
            "`quiz_questions/`."
        )
        for err in st.session_state.get("df_errors", []):
            st.caption(f"⚠️ `{err['file']}` — {err['error']}")
        return

    _render_sources_summary()

    themes = data.all_themes(df)
    selected_themes = st.multiselect("Themes", options=themes, default=themes)

    selected_diff = st.multiselect(
        "Difficulty", options=data.DIFFICULTIES, default=data.DIFFICULTIES
    )

    verticals = data.all_verticals(df)
    selected_verticals = st.multiselect(
        "Verticals", options=verticals, default=verticals
    )

    shuffle_questions = st.checkbox("Shuffle questions", value=True)
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


def _render_sources_summary() -> None:
    sources = st.session_state.get("df_sources") or []
    errors = st.session_state.get("df_errors") or []
    total = sum(s["rows"] for s in sources)

    if len(sources) == 1 and not errors:
        st.caption(f"Loaded `{sources[0]['file']}` — {total} question(s)")
        return

    st.caption(
        f"Loaded **{len(sources)}** file(s) — **{total}** question(s)"
    )
    with st.expander("Files", expanded=False):
        for s in sources:
            st.caption(f"`{s['file']}` — {s['rows']} question(s)")
        for err in errors:
            st.caption(f"⚠️ `{err['file']}` skipped — {err['error']}")