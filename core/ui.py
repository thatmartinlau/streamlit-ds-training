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