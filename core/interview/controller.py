"""Deterministic controller agent.

Reads the evaluator's structured output plus the current session state and
decides the next action. This module makes **no** LLM calls. The only
place an LLM is involved in a decision is the evaluator (score/action
suggestion), and even there the controller can override the evaluator's
`recommended_action` when the rubric exit criteria disagree.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from core.interview.schemas import EvaluatorOutput


@dataclass
class Decision:
    action: str  # probe_more | advance | revisit_previous | end
    next_competency: str | None
    reason: str
    penalty: bool = False


_HARD_STOP_FAILS = {"claims_execution"}


def _competencies(rubric: dict[str, Any]) -> list[str]:
    return list(rubric["competencies"].keys())


def _next_unvisited_after(current: str, competencies: list[str], visited: list[str]) -> str | None:
    idx = competencies.index(current)
    for c in competencies[idx + 1:]:
        if c not in visited:
            return c
    for c in competencies[:idx]:
        if c not in visited:
            return c
    return None


def decide(
    evaluator: EvaluatorOutput,
    state: dict[str, Any],
    case: dict[str, Any],
    rubric: dict[str, Any],
) -> Decision:
    competencies = _competencies(rubric)
    current = state["current_competency"]

    # 1. Hard stops.
    if any(cf["id"] in _HARD_STOP_FAILS for cf in evaluator.critical_fails):
        return Decision("end", None, "Candidate claimed code execution; interview terminated.")

    # 2. Evaluator explicitly asks to end.
    if evaluator.recommended_action == "end":
        return Decision("end", None, "Evaluator recommended ending the interview.")

    # 3. Revisit requested and we have somewhere to go back to.
    history = state.get("visit_history") or []
    if evaluator.recommended_action == "revisit_previous" and len(history) >= 2:
        previous = history[-2]
        return Decision("revisit_previous", previous, "Revisiting previous competency.")

    # 4. Gather current-competency exit criteria.
    comp_cfg = rubric["competencies"][current]
    exit_cfg = comp_cfg.get("exit", {}) or {}
    min_score = int(exit_cfg.get("min_score", 2))
    max_follow_ups = int(exit_cfg.get("max_follow_ups", 2))

    comp_state = state["rubric_state"][current]
    score = comp_state.get("score")
    probes_sent = int(comp_state.get("probes_sent", 0))
    enough_evidence = score is not None and score >= min_score
    maxed_probes = probes_sent >= max_follow_ups

    def _advance_or_end(reason: str, penalty: bool = False) -> Decision:
        # Prefer the return-to competency if we're on a revisit.
        return_target = state.get("revisit_return")
        if return_target:
            return Decision("advance", return_target, reason, penalty)
        nxt = _next_unvisited_after(current, competencies, state.get("visited_competencies", []))
        if nxt is None:
            return Decision("end", None, "All competencies have been covered.")
        return Decision("advance", nxt, reason, penalty)

    # 5. Evaluator said advance — honour only if exit criteria are met.
    if evaluator.recommended_action == "advance":
        if enough_evidence:
            return _advance_or_end("Exit criteria met; advancing.")
        if maxed_probes:
            return _advance_or_end(
                "Evaluator wanted to advance but exit score not met after max probes.",
                penalty=True,
            )
        return Decision("probe_more", current, "Evaluator wanted advance; exit score not met — probing.")

    # 6. Default: probe more, unless we've used the follow-up budget.
    if maxed_probes:
        return _advance_or_end(
            "Max follow-ups reached without sufficient evidence.",
            penalty=True,
        )
    return Decision("probe_more", current, "Additional evidence needed.")