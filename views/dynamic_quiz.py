"""Password-gated dynamic screen powered by DeepSeek."""

import streamlit as st

from core import auth
from core import dynamic_quiz as dq


def render() -> None:
    if not auth.password_gate(
        title="🔒 Dynamic Screen",
        session_key="_dyn_unlocked",
    ):
        return
    _render_page()


# --------------------------------------------------------------------------- #
#  Main page
# --------------------------------------------------------------------------- #
def _render_page() -> None:
    st.title("✨ Dynamic Screen — Artefact Junior DS")
    st.markdown(
        "DeepSeek generates 5 interview questions on your selected themes. "
        "You answer them one at a time. When all 5 are submitted, a single "
        "consolidated feedback report is produced."
    )

    with st.sidebar:
        if st.button("🔒 Lock this feature", use_container_width=True):
            st.session_state.pop("_dyn_unlocked", None)
            _reset_state()
            st.rerun()

    phase = st.session_state.get("_dyn_phase", "idle")

    if phase == "idle":
        _render_setup()
    elif phase == "answering":
        _render_answering()
    elif phase == "evaluating":
        _render_evaluating()
    elif phase == "done":
        _render_done()

# --------------------------------------------------------------------------- #
#  Phase: setup
# --------------------------------------------------------------------------- #
def _render_setup() -> None:
    if not dq.get_secret("DEEPSEEK_API_KEY"):
        st.error(
            "`DEEPSEEK_API_KEY` is not configured. Add it to "
            "`.streamlit/secrets.toml`."
        )
        return

    st.subheader("1. Pick your themes")
    st.caption("Check the domains you want the questions drawn from.")

    selected: list[str] = []
    cols = st.columns(2)
    for i, domain in enumerate(dq.DOMAINS):
        with cols[i % 2]:
            if st.checkbox(domain, value=True, key=f"_dyn_theme_{domain}"):
                selected.append(domain)

    st.divider()
    st.subheader("2. Generate the questions")

    if st.button(
        "⚡ Generate 5 questions",
        type="primary",
        disabled=not selected,
    ):
        with st.spinner("Generating questions…"):
            try:
                questions = dq.generate_questions(selected)
            except Exception as exc:  # noqa: BLE001
                st.error(f"Generation failed: `{type(exc).__name__}: {exc}`")
                return
        st.session_state["_dyn_questions"] = questions
        st.session_state["_dyn_answers"] = [""] * len(questions)
        st.session_state["_dyn_index"] = 0
        st.session_state["_dyn_phase"] = "answering"
        st.rerun()


# --------------------------------------------------------------------------- #
#  Phase: answering
# --------------------------------------------------------------------------- #
def _render_answering() -> None:
    questions = st.session_state.get("_dyn_questions", [])
    answers = st.session_state.get("_dyn_answers", [])
    idx = st.session_state.get("_dyn_index", 0)
    n = len(questions)

    if idx >= n:
        st.session_state["_dyn_phase"] = "evaluating"
        st.rerun()

    q = questions[idx]
    st.markdown(f"**Question {idx + 1} of {n}** — *{q['topic']}*")
    st.progress((idx + 1) / n)

    with st.container(border=True):
        st.markdown(q["question"])

    widget_key = f"_dyn_ans_{idx}"
    st.text_area(
        "Your answer",
        key=widget_key,
        height=180,
        placeholder="Type your answer here — 3–6 sentences is usually enough.",
    )
    # Keep the answers list in sync with the live widget value.
    answers[idx] = st.session_state.get(widget_key, "")
    st.session_state["_dyn_answers"] = answers

    c1, c2, _ = st.columns([1, 1, 2])
    with c1:
        submit = st.button(
            "Submit answer",
            type="primary",
            disabled=not answers[idx].strip(),
            key=f"_dyn_submit_{idx}",
        )
    with c2:
        skip = st.button("Skip", key=f"_dyn_skip_{idx}")

    if submit or skip:
        if skip:
            answers[idx] = ""
            st.session_state["_dyn_answers"] = answers
        st.session_state["_dyn_index"] = idx + 1
        st.rerun()

    if idx > 0:
        with st.expander(f"Review submitted answers ({idx} so far)"):
            for i in range(idx):
                st.markdown(f"**Q{i + 1} — {questions[i]['topic']}**")
                st.markdown(questions[i]["question"])
                st.markdown(
                    f"→ {answers[i].strip() or '_(Skipped)_'}"
                )
                st.divider()


# --------------------------------------------------------------------------- #
#  Phase: evaluating
# --------------------------------------------------------------------------- #
def _render_evaluating() -> None:
    if st.session_state.get("_dyn_feedback"):
        st.session_state["_dyn_phase"] = "done"
        st.rerun()

    if st.session_state.get("_dyn_eval_error"):
        st.error(
            f"Evaluation failed: {st.session_state['_dyn_eval_error']}"
        )
        c1, c2 = st.columns(2)
        if c1.button("Retry evaluation", type="primary"):
            st.session_state.pop("_dyn_eval_error", None)
            st.rerun()
        if c2.button("Edit my answers"):
            st.session_state["_dyn_index"] = 0
            st.session_state["_dyn_phase"] = "answering"
            st.rerun()
        return

    with st.spinner("Evaluating your answers…"):
        try:
            feedback = dq.evaluate_answers(
                st.session_state["_dyn_questions"],
                st.session_state["_dyn_answers"],
            )
            st.session_state["_dyn_feedback"] = feedback
            st.session_state["_dyn_phase"] = "done"
            st.rerun()
        except Exception as exc:  # noqa: BLE001
            st.session_state["_dyn_eval_error"] = (
                f"{type(exc).__name__}: {exc}"
            )
            st.rerun()


# --------------------------------------------------------------------------- #
#  Phase: done
# --------------------------------------------------------------------------- #
def _render_done() -> None:
    st.success("Feedback ready.")
    st.markdown(st.session_state["_dyn_feedback"])
    st.divider()
    if st.button("🔁 Start a new round", type="primary"):
        _reset_state()
        st.session_state["_dyn_unlocked"] = True   # keep the session unlocked
        st.rerun()