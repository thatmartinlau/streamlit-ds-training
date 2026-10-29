"""Session-state schema and helpers for the interview simulator.

All state lives in `st.session_state["interview_state"]`. The schema is
documented in `docs/design.md`. This module is the single write-point for
the top-level state so the schema is easy to evolve.
"""

from __future__ import annotations

import copy
from typing import Any

import streamlit as st

STATE_KEY = "interview_state"


def empty_state(case: dict[str, Any], rubric: dict[str, Any], mode: str, target_role: str) -> dict[str, Any]:
    competencies = list(rubric["competencies"].keys())
    first = competencies[0]
    return {
        "case_id": case["id"],
        "mode": mode,
        "target_role": target_role,
        "current_competency": first,
        "visit_history": [first],
        "visited_competencies": [first],
        "revisit_return": None,
        "rubric_state": {
            c: {"score": None, "evidence": [], "probes_sent": 0, "advanced": False}
            for c in competencies
        },
        "pending_probes": [],
        "critical_fails": [],
        "code_artifacts": [],
        "explanations": [],
        "transcript": [],
        "transcript_summary": "",
        "evaluator_log": [],
        "turn": 0,
        "status": "active",
        "opening_sent": False,
        "debrief": None,
    }


def init_state(case: dict[str, Any], rubric: dict[str, Any], mode: str, target_role: str) -> dict[str, Any]:
    state = empty_state(case, rubric, mode, target_role)
    st.session_state[STATE_KEY] = state
    return state


def get_state() -> dict[str, Any] | None:
    return st.session_state.get(STATE_KEY)


def reset_state() -> None:
    st.session_state.pop(STATE_KEY, None)


def snapshot() -> dict[str, Any] | None:
    """Return a deep copy — useful for export and tests."""
    state = get_state()
    return copy.deepcopy(state) if state is not None else None