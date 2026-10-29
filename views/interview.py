"""Live-coding interview simulator page."""

from __future__ import annotations

import json
from typing import Any

import streamlit as st

from core import auth
from core.interview import case_loader, orchestrator
from core.interview import state as istate


# --------------------------------------------------------------------------- #
#  Entry point
# --------------------------------------------------------------------------- #
def render() -> None:
    if not auth.password_gate(
        title="🔒 Interview Simulator",
        session_key="_interview_unlocked",
    ):
        return

    st.title("🎤 Interview Simulator")
    st.caption(
        "Live-coding case interview. The interviewer, evaluator, and "
        "controller are separate agents; no code is executed — only "
        "statically reviewed."
    )

    try:
        rubric = case_loader.load_rubric()
        cases = case_loader.list_cases()
    except Exception as exc:  # noqa: BLE001
        st.error(f"Could not load rubric / cases: `{type(exc).__name__}: {exc}`")
        return

    if not cases:
        st.warning("No cases found in `cases/`. Add a YAML case pack to begin.")
        return

    with st.sidebar:
        case_id, mode, target_role, start_clicked, end_clicked = _render_sidebar(cases)

    state = istate.get_state()

    if start_clicked:
        case = case_loader.get_case(case_id)
        state = istate.init_state(case.raw, rubric, mode, target_role)
        with st.spinner("Interviewer is preparing the opening question…"):
            try:
                orchestrator.start_interview(state, case.raw, rubric)
            except Exception as exc:  # noqa: BLE001
                st.error(f"Could not start the interview: `{type(exc).__name__}: {exc}`")
                return
        st.rerun()

    if state is None:
        st.info("Pick a case and click **Start interview** in the sidebar.")
        return

    case = case_loader.get_case(state["case_id"])
    _render_dossier(case)
    st.divider()
    _render_progress(state, rubric)
    _render_transcript(state)

    if state.get("status") == "active":
        st.divider()
        _render_active_panel(state, case, rubric)
    else:
        st.divider()
        _render_debrief_panel(state)

    if end_clicked and state.get("status") == "active":
        with st.spinner("Generating debrief…"):
            orchestrator.end_interview(state, case.raw, rubric)
        st.rerun()


# --------------------------------------------------------------------------- #
#  Sidebar
# --------------------------------------------------------------------------- #
def _render_sidebar(cases) -> tuple[str, str, str, bool, bool]:
    st.header("🎛️ Setup")

    if st.button("🔒 Lock this feature", use_container_width=True):
        # Clear the unlock flag *and* the in-progress interview so a
        # relock is a clean slate — mirrors the dynamic screen's behavior.
        st.session_state.pop("_interview_unlocked", None)
        istate.reset_state()
        st.rerun()

    case_titles = {c.id: f"{c.title} · {c.difficulty}" for c in cases}
    case_id = st.selectbox(
        "Case",
        options=list(case_titles.keys()),
        format_func=lambda cid: case_titles[cid],
    )
    mode = st.radio("Mode", ["practice", "exam"], index=0, horizontal=True)
    target_role = st.text_input("Target role", value="DS / AI Consultant")

    st.divider()
    start_clicked = st.button("🚀 Start interview", type="primary", use_container_width=True)

    state = istate.get_state()
    end_clicked = False
    if state is not None and state.get("status") == "active":
        end_clicked = st.button("🏁 End interview and debrief", use_container_width=True)
        st.divider()
        st.subheader("📤 Export")
        st.download_button(
            "⬇️ Transcript (Markdown)",
            data=_export_markdown(state),
            file_name=f"interview_{state['case_id']}.md",
            mime="text/markdown",
            use_container_width=True,
        )
        st.download_button(
            "⬇️ State (JSON)",
            data=json.dumps(state, default=str, indent=2),
            file_name=f"interview_{state['case_id']}_state.json",
            mime="application/json",
            use_container_width=True,
        )

    if state is not None:
        st.divider()
        st.caption(
            f"Active case: `{state['case_id']}` · mode `{state['mode']}` · "
            f"turn {state.get('turn', 0)}"
        )

    return case_id, mode, target_role, start_clicked, end_clicked


# --------------------------------------------------------------------------- #
#  Dossier
# --------------------------------------------------------------------------- #
def _render_dossier(case) -> None:
    st.markdown(f"### {case.title}")
    with st.expander("📋 Case dossier", expanded=True):
        st.markdown(f"**Business context**\n\n{case.business_context}")
        dc = case.dataset_card
        st.markdown("**Dataset card**")
        st.markdown(f"- Target: `{dc.get('target', 'n/a')}`")
        st.markdown(f"- Size: {dc.get('size', 'n/a')}")
        st.markdown(f"- Schema: `{dc.get('schema', [])}`")
        if dc.get("sample_rows"):
            st.code(dc["sample_rows"], language="text")
        quirks = dc.get("quirks", [])
        if quirks:
            st.markdown("**Known quirks**")
            for q in quirks:
                st.markdown(f"- {q}")
        st.markdown(f"**Success metric**: {case.success_metric}")


# --------------------------------------------------------------------------- #
#  Progress
# --------------------------------------------------------------------------- #
def _render_progress(state: dict[str, Any], rubric: dict[str, Any]) -> None:
    competencies = list(rubric["competencies"].keys())
    visited = set(state.get("visited_competencies", []))
    current = state.get("current_competency")
    n_done = sum(1 for c in visited if state["rubric_state"][c].get("advanced"))
    st.progress(
        n_done / max(1, len(competencies)),
        text=f"Competency progress: {n_done} / {len(competencies)} completed · current: `{current}`",
    )


# --------------------------------------------------------------------------- #
#  Transcript
# --------------------------------------------------------------------------- #
def _render_transcript(state: dict[str, Any]) -> None:
    st.markdown("### Transcript")
    if not state["transcript"]:
        st.info("The interviewer's opening turn will appear here.")
        return
    for turn in state["transcript"]:
        role = turn["role"]
        label = "🧑‍💼 Interviewer" if role == "interviewer" else "🙋 Candidate"
        prefix = "🔎 " if turn.get("is_clarification") else ""
        with st.chat_message("assistant" if role == "interviewer" else "user"):
            st.markdown(f"**{label} · turn {turn['turn']} · `{turn.get('competency','')}`**")
            st.markdown(prefix + turn.get("content", ""))


# --------------------------------------------------------------------------- #
#  Active panel
# --------------------------------------------------------------------------- #
def _render_active_panel(state: dict[str, Any], case, rubric: dict[str, Any]) -> None:
    st.markdown("### Your answer")
    col_left, col_right = st.columns([1, 1])
    with col_left:
        thoughts = st.text_area("Thoughts / reasoning", height=180, key="int_thoughts")
    with col_right:
        code = st.text_area("Code (not executed)", height=180, key="int_code")
    expected = st.text_area(
        "Expected output & assumptions (required when you submit code)",
        height=120,
        key="int_expected",
    )

    c1, c2, _ = st.columns([1, 1, 2])
    with c1:
        submitted = st.button("📨 Submit answer", type="primary", key="int_submit")
    with c2:
        clarify_clicked = st.button("❓ Clarify case", key="int_clarify")

    if submitted:
        submission = {
            "thoughts": thoughts or "",
            "code": code or "",
            "expected_output": expected or "",
        }
        if not any(v.strip() for v in submission.values()):
            st.warning("Write at least one of the three boxes before submitting.")
        elif submission["code"].strip() and not submission["expected_output"].strip():
            st.error(
                "When you submit code, you must also state the expected output "
                "and assumptions. The interviewer cannot run your code."
            )
        else:
            with st.spinner("Evaluator is scoring; interviewer is preparing the next turn…"):
                try:
                    orchestrator.submit_answer(state, case.raw, rubric, submission)
                except Exception as exc:  # noqa: BLE001
                    st.error(f"Turn failed: `{type(exc).__name__}: {exc}`")
                    return
            st.rerun()

    if clarify_clicked:
        with st.form("clarify_form", clear_on_submit=True):
            q = st.text_input("Your clarifying question")
            ok = st.form_submit_button("Ask")
        if ok and q.strip():
            with st.spinner("Interviewer is answering…"):
                try:
                    orchestrator.clarify(state, case.raw, rubric, q)
                except Exception as exc:  # noqa: BLE001
                    st.error(f"Clarification failed: `{type(exc).__name__}: {exc}`")
                    return
            st.rerun()

    # Practice-mode stage feedback
    if state.get("mode") == "practice":
        current = state["current_competency"]
        rs = state["rubric_state"][current]
        if rs.get("score") is not None:
            st.info(
                f"**Practice feedback — `{current}`** · score {rs['score']}/4 · "
                f"evidence: {rs['evidence'][-2:]}"
            )


# --------------------------------------------------------------------------- #
#  Debrief panel
# --------------------------------------------------------------------------- #
def _render_debrief_panel(state: dict[str, Any]) -> None:
    st.markdown("### 🏁 Debrief")
    if state.get("debrief"):
        st.markdown(state["debrief"])
    else:
        st.warning("No debrief available.")

    with st.expander("Raw evaluator log (audit)", expanded=False):
        for entry in state.get("evaluator_log", []):
            st.markdown(f"**Turn {entry.get('turn')}**")
            st.json(entry.get("output"))


# --------------------------------------------------------------------------- #
#  Export
# --------------------------------------------------------------------------- #
def _export_markdown(state: dict[str, Any]) -> str:
    lines = [f"# Interview transcript — {state['case_id']}", ""]
    for t in state.get("transcript", []):
        lines.append(f"### {t['role'].title()} — turn {t['turn']} — `{t.get('competency', '')}`")
        lines.append(t.get("content", ""))
        lines.append("")
    if state.get("debrief"):
        lines.append("# Debrief")
        lines.append(state["debrief"])
    return "\n".join(lines)