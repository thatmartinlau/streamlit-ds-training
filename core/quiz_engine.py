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