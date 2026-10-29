"""Evaluator agent — JSON-only, no candidate-facing text."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from core.interview.config import load_config
from core.interview.llm import chat
from core.interview.schemas import EvaluatorOutput

_PROMPT_PATH = Path(__file__).resolve().parents[3] / "prompts" / "evaluator_v1.md"


def _prompt() -> str:
    return _PROMPT_PATH.read_text(encoding="utf-8")


def _rubric_brief(rubric: dict[str, Any]) -> str:
    lines = ["# Rubric"]
    for name, cfg in rubric["competencies"].items():
        anchors = cfg.get("anchors", {})
        exit_cfg = cfg.get("exit", {})
        lines.append(f"## {name}")
        lines.append(f"- exit: min_score={exit_cfg.get('min_score')}, max_follow_ups={exit_cfg.get('max_follow_ups')}")
        for k in sorted(anchors):
            lines.append(f"  - {k}: {anchors[k]}")
    lines.append("\n# Critical fail ids (use exactly these ids)")
    for cf in rubric.get("critical_fails", []):
        lines.append(f"- {cf['id']}: {cf.get('description', '')}")
    return "\n".join(lines)


def _submission_block(submission: dict[str, Any]) -> str:
    return (
        "# Candidate submission\n"
        f"## Thoughts / reasoning\n{submission.get('thoughts', '').strip() or '(empty)'}\n\n"
        f"## Code (not executed)\n```python\n{submission.get('code', '').strip() or '(none)'}\n```\n\n"
        f"## Expected output & assumptions\n{submission.get('expected_output', '').strip() or '(empty)'}"
    )


def _transcript_window(state: dict[str, Any], n: int) -> str:
    transcript = state.get("transcript", [])
    window = transcript[-n:] if n > 0 else transcript
    lines = []
    for turn in window:
        lines.append(f"[{turn['role']} · {turn.get('competency', '')}]")
        lines.append(turn.get("content", ""))
    return "\n".join(lines)


def _user_prompt(
    *,
    case: dict[str, Any],
    rubric: dict[str, Any],
    state: dict[str, Any],
    submission: dict[str, Any],
) -> str:
    cfg = load_config()
    guide = (case.get("interviewer_guide") or {}).get(state["current_competency"], {})
    return "\n\n".join(
        [
            f"# Case: {case.get('title', case['id'])}",
            f"# Current competency: {state['current_competency']}",
            f"# Hidden guide (do not quote verbatim): {guide}",
            _rubric_brief(rubric),
            _submission_block(submission),
            "# Recent transcript\n" + _transcript_window(state, cfg.transcript_window),
            (
                "# Required JSON schema\n"
                "{\n"
                '  "competency_updates": {"<comp_id>": {"score": 1|2|3|4, "evidence": ["<quote>", ...]}},\n'
                '  "covered_items": ["<item>", ...],\n'
                '  "missing_items": ["<item>", ...],\n'
                '  "critical_fails": [{"id": "<critical_fail_id>", "evidence": "<quote>"}],\n'
                '  "confidence": "low" | "medium" | "high",\n'
                '  "recommended_action": "probe_more" | "advance" | "revisit_previous" | "end",\n'
                '  "suggested_probe": "<short note for the controller>"\n'
                "}\n"
                "Return JSON only."
            ),
        ]
    )


def run(
    *,
    case: dict[str, Any],
    rubric: dict[str, Any],
    state: dict[str, Any],
    submission: dict[str, Any],
) -> tuple[EvaluatorOutput, dict[str, Any]]:
    """Return ``(parsed_output, raw_json_for_audit)``."""
    cfg = load_config()
    system = _prompt()
    base_user = _user_prompt(case=case, rubric=rubric, state=state, submission=submission)

    last_err: Exception | None = None
    for attempt in range(cfg.max_evaluator_retries + 1):
        suffix = "" if attempt == 0 else (
            "\n\nSTRICT: your previous response could not be parsed. "
            "Return ONLY a single JSON object matching the schema above."
        )
        try:
            content = chat(
                system=system,
                user=base_user + suffix,
                model=cfg.model_evaluator,
                temperature=cfg.temp_evaluator,
                max_tokens=2000,
                json_mode=True,
            )
            raw = json.loads(content)
            parsed = EvaluatorOutput.from_raw(raw)
            return parsed, raw
        except Exception as exc:  # noqa: BLE001
            last_err = exc

    fallback = EvaluatorOutput(
        competency_updates={},
        covered_items=[],
        missing_items=[],
        critical_fails=[],
        confidence="low",
        recommended_action="probe_more",
        suggested_probe="Evaluator failed to return valid JSON; ask a clarifying question.",
    )
    return fallback, {"_fallback": True, "error": str(last_err)}