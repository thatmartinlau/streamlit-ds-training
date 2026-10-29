"""Coordinates a single interview turn: evaluator → controller → interviewer.

Also implements the *opening* and *clarify* entry points (interviewer
only, no evaluator), and the *end* entry point (debrief generation).
"""

from __future__ import annotations

from typing import Any

from core.interview import controller, debrief
from core.interview.agents import evaluator as evaluator_agent
from core.interview.agents import interviewer as interviewer_agent
from core.interview.controller import Decision


# --------------------------------------------------------------------------- #
#  Opening
# --------------------------------------------------------------------------- #
def start_interview(state: dict[str, Any], case: dict[str, Any], rubric: dict[str, Any]) -> None:
    """Emit the opening interviewer turn."""
    if state.get("opening_sent"):
        return
    text = interviewer_agent.run(
        turn_type="OPENING",
        case=case,
        rubric=rubric,
        state=state,
    )
    state["turn"] += 1
    state["transcript"].append(
        {
            "role": "interviewer",
            "turn": state["turn"],
            "competency": state["current_competency"],
            "content": text,
        }
    )
    state["opening_sent"] = True


# --------------------------------------------------------------------------- #
#  Clarification
# --------------------------------------------------------------------------- #
def clarify(
    state: dict[str, Any],
    case: dict[str, Any],
    rubric: dict[str, Any],
    question: str,
) -> None:
    if not question.strip():
        return
    state["turn"] += 1
    state["transcript"].append(
        {
            "role": "candidate",
            "turn": state["turn"],
            "competency": state["current_competency"],
            "content": f"[Clarification request] {question.strip()}",
            "is_clarification": True,
        }
    )
    text = interviewer_agent.clarify(case=case, state=state, question=question)
    state["turn"] += 1
    state["transcript"].append(
        {
            "role": "interviewer",
            "turn": state["turn"],
            "competency": state["current_competency"],
            "content": text,
        }
    )


# --------------------------------------------------------------------------- #
#  Submit answer — the full three-agent turn
# --------------------------------------------------------------------------- #
def _format_submission(submission: dict[str, Any]) -> str:
    parts = []
    if submission.get("thoughts", "").strip():
        parts.append(f"Thoughts:\n{submission['thoughts'].strip()}")
    if submission.get("code", "").strip():
        parts.append(f"Code (not executed):\n```python\n{submission['code'].strip()}\n```")
    if submission.get("expected_output", "").strip():
        parts.append(f"Expected output & assumptions:\n{submission['expected_output'].strip()}")
    return "\n\n".join(parts) or "(empty submission)"


def submit_answer(
    state: dict[str, Any],
    case: dict[str, Any],
    rubric: dict[str, Any],
    submission: dict[str, Any],
) -> None:
    if state.get("status") != "active":
        return

    # UI-level guard: code present → expected output required.
    if submission.get("code", "").strip() and not submission.get("expected_output", "").strip():
        raise ValueError(
            "When you submit code, you must also state the expected output and assumptions."
        )

    current = state["current_competency"]

    # 1. Record the candidate's turn.
    state["turn"] += 1
    state["transcript"].append(
        {
            "role": "candidate",
            "turn": state["turn"],
            "competency": current,
            "content": _format_submission(submission),
            "submission": submission,
        }
    )
    state["explanations"].append(
        {
            "turn": state["turn"],
            "thoughts": submission.get("thoughts", ""),
            "expected_output": submission.get("expected_output", ""),
        }
    )
    if submission.get("code", "").strip():
        state["code_artifacts"].append(
            {"turn": state["turn"], "competency": current, "code": submission["code"].strip()}
        )

    # 2. Evaluate.
    ev, raw = evaluator_agent.run(case=case, rubric=rubric, state=state, submission=submission)

    # 3. Merge into session state.
    for comp, upd in ev.competency_updates.items():
        if comp not in state["rubric_state"]:
            continue
        rs = state["rubric_state"][comp]
        if upd.get("score") is not None and upd.get("evidence"):
            prev = rs.get("score")
            rs["score"] = upd["score"] if prev is None else max(prev, upd["score"])
            rs["evidence"].extend(upd["evidence"])
    for cf in ev.critical_fails:
        state["critical_fails"].append({**cf, "turn": state["turn"]})
    state["pending_probes"] = list(ev.missing_items)
    state["evaluator_log"].append(
        {"turn": state["turn"], "input_summary": _format_submission(submission)[:600], "output": raw}
    )

    # 4. Controller decides.
    decision: Decision = controller.decide(ev, state, case, rubric)

    if decision.action == "end":
        _finalize(state, case, rubric)
        return

    # 5. Apply the decision to session state.
    if decision.action == "probe_more":
        state["rubric_state"][current]["probes_sent"] = (
            int(state["rubric_state"][current].get("probes_sent", 0)) + 1
        )
    elif decision.action == "advance" and decision.next_competency:
        target = decision.next_competency
        # Reset the "return-to" bookkeeping when we're leaving a revisit.
        state["revisit_return"] = None
        state["rubric_state"][current]["advanced"] = True
        state["current_competency"] = target
        if target not in state["visited_competencies"]:
            state["visited_competencies"].append(target)
        state["visit_history"].append(target)
        if not state["rubric_state"][target].get("probes_sent"):
            state["rubric_state"][target]["probes_sent"] = 0
    elif decision.action == "revisit_previous" and decision.next_competency:
        state["revisit_return"] = current
        state["current_competency"] = decision.next_competency
        state["visit_history"].append(decision.next_competency)
        state["rubric_state"][decision.next_competency]["probes_sent"] = 0

    # 6. Interviewer produces the next turn.
    turn_type = {
        "probe_more": "PROBE",
        "advance": "ADVANCE",
        "revisit_previous": "REVISIT",
    }.get(decision.action, "PROBE")
    text = interviewer_agent.run(
        turn_type=turn_type,
        case=case,
        rubric=rubric,
        state=state,
        decision=decision,
        last_submission=submission,
    )
    state["turn"] += 1
    state["transcript"].append(
        {
            "role": "interviewer",
            "turn": state["turn"],
            "competency": state["current_competency"],
            "content": text,
        }
    )


# --------------------------------------------------------------------------- #
#  Manual end + debrief
# --------------------------------------------------------------------------- #
def end_interview(state: dict[str, Any], case: dict[str, Any], rubric: dict[str, Any]) -> None:
    if state.get("status") != "active":
        return
    _finalize(state, case, rubric)


def _finalize(state: dict[str, Any], case: dict[str, Any], rubric: dict[str, Any]) -> None:
    state["status"] = "finished"
    try:
        state["debrief"] = debrief.generate(state, case, rubric)
    except Exception as exc:  # noqa: BLE001
        state["debrief"] = f"_Debrief generation failed: {type(exc).__name__}: {exc}_"