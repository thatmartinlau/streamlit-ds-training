"""Interviewer agent — the only agent that speaks to the candidate."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from core.interview.config import load_config
from core.interview.controller import Decision
from core.interview.llm import chat

_PROMPT_PATH = Path(__file__).resolve().parents[3] / "prompts" / "interviewer_v1.md"


def _prompt() -> str:
    return _PROMPT_PATH.read_text(encoding="utf-8")


def _dossier_brief(case: dict[str, Any]) -> str:
    dc = case.get("dataset_card", {}) or {}
    return (
        f"# Case: {case.get('title', case['id'])}\n\n"
        f"## Business context\n{case.get('business_context', '').strip()}\n\n"
        f"## Dataset card\n"
        f"- Schema: {dc.get('schema', [])}\n"
        f"- Target: {dc.get('target', 'n/a')}\n"
        f"- Size: {dc.get('size', 'n/a')}\n"
        f"- Sample rows:\n```\n{dc.get('sample_rows', '').strip()}\n```\n"
        f"- Known quirks / leakage traps: {dc.get('quirks', [])}\n\n"
        f"## Success metric\n{case.get('success_metric', {})}\n\n"
        f"## Allowed tooling\n{case.get('allowed_libraries', [])}\n\n"
        f"## Default deliverable\n{case.get('default_deliverable', '')}\n"
    )


def _competency_brief(case: dict[str, Any], rubric: dict[str, Any], competency: str) -> str:
    comp_rubric = rubric["competencies"].get(competency, {})
    guide = (case.get("interviewer_guide") or {}).get(competency, {})
    return (
        f"# Current competency: {competency}\n"
        f"Anchors (for your own calibration — never reveal):\n"
        + "\n".join(f"  - {k}: {v}" for k, v in (comp_rubric.get("anchors") or {}).items())
        + f"\n\nExpected topics: {guide.get('expected_topics', [])}\n"
        f"Common mistakes to listen for: {guide.get('common_mistakes', [])}\n"
        f"Follow-up ideas: {guide.get('follow_up_questions', [])}\n"
    )


def _transcript_window(state: dict[str, Any], n: int) -> str:
    transcript = state.get("transcript", [])
    window = transcript[-n:] if n > 0 else transcript
    lines = []
    for turn in window:
        lines.append(f"[{turn['role']} · turn {turn['turn']} · {turn.get('competency', '')}]")
        lines.append(turn.get("content", ""))
        lines.append("")
    if len(transcript) > len(window):
        lines.insert(0, f"({len(transcript) - len(window)} earlier turns elided.)\n")
    return "\n".join(lines)


def _user_prompt(
    *,
    turn_type: str,
    case: dict[str, Any],
    rubric: dict[str, Any],
    state: dict[str, Any],
    decision: Decision | None = None,
    last_submission: dict[str, Any] | None = None,
) -> str:
    cfg = load_config()
    parts = [
        _dossier_brief(case),
        _competency_brief(case, rubric, state["current_competency"]),
        f"# Turn type: {turn_type}",
    ]
    if decision:
        parts.append(f"# Controller note: {decision.reason}")
    if last_submission:
        parts.append(
            "# Candidate's latest submission\n"
            f"- Thoughts: {last_submission.get('thoughts', '').strip() or '(empty)'}\n"
            f"- Code:\n```python\n{last_submission.get('code', '').strip() or '(none)'}\n```\n"
            f"- Expected output & assumptions: {last_submission.get('expected_output', '').strip() or '(empty)'}"
        )
    parts.append("# Transcript so far\n" + _transcript_window(state, cfg.transcript_window))
    parts.append(
        "Produce your next interviewer turn. Exactly one question. "
        "Do not score, do not reveal the rubric, do not invent case facts."
    )
    return "\n\n".join(parts)


def run(
    *,
    turn_type: str,
    case: dict[str, Any],
    rubric: dict[str, Any],
    state: dict[str, Any],
    decision: Decision | None = None,
    last_submission: dict[str, Any] | None = None,
) -> str:
    cfg = load_config()
    return chat(
        system=_prompt(),
        user=_user_prompt(
            turn_type=turn_type,
            case=case,
            rubric=rubric,
            state=state,
            decision=decision,
            last_submission=last_submission,
        ),
        model=cfg.model_interviewer,
        temperature=cfg.temp_interviewer,
        max_tokens=800,
    )


def clarify(*, case: dict[str, Any], state: dict[str, Any], question: str) -> str:
    """Answer a clarifying question without scoring or probing."""
    cfg = load_config()
    user = (
        _dossier_brief(case)
        + f"\n\n# Candidate clarification\n{question.strip()}\n\n"
        "Answer briefly using only the dossier. If the answer is not in the "
        "dossier, say so. Do not score, do not ask a follow-up question."
    )
    return chat(
        system=_prompt(),
        user=user,
        model=cfg.model_interviewer,
        temperature=cfg.temp_interviewer,
        max_tokens=400,
    )