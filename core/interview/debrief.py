"""Final debrief / scorecard generation."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from core.interview.config import load_config
from core.interview.llm import chat

_PROMPT_PATH = Path(__file__).resolve().parents[2] / "prompts" / "debrief_v1.md"


def _prompt() -> str:
    return _PROMPT_PATH.read_text(encoding="utf-8")


def _score_table(state: dict[str, Any]) -> str:
    lines = ["| Competency | Score | Evidence |", "|---|---|---|"]
    for comp, rs in state["rubric_state"].items():
        score = rs.get("score")
        score_txt = str(score) if score is not None else "insufficient evidence"
        quotes = " / ".join(f'"{q}"' for q in (rs.get("evidence") or [])[:3]) or "—"
        lines.append(f"| {comp} | {score_txt} | {quotes} |")
    return "\n".join(lines)


def _fails_block(state: dict[str, Any]) -> str:
    fails = state.get("critical_fails") or []
    if not fails:
        return "(none)"
    return "\n".join(
        f"- **{cf['id']}** (turn {cf.get('turn', '?')}): {cf.get('evidence', '')}"
        for cf in fails
    )


def generate(state: dict[str, Any], case: dict[str, Any], rubric: dict[str, Any]) -> str:
    cfg = load_config()
    guide = case.get("interviewer_guide") or {}
    guide_lines = []
    for comp, g in guide.items():
        guide_lines.append(f"## {comp}")
        guide_lines.append(f"- expected: {g.get('expected_topics', [])}")
        guide_lines.append(f"- mistakes: {g.get('common_mistakes', [])}")
        outline = (g.get("model_answer_outline") or "").strip()
        if outline:
            guide_lines.append(f"- model answer outline:\n{outline}")

    user = "\n\n".join(
        [
            f"# Case: {case.get('title', case['id'])}",
            f"# Mode: {state.get('mode')}",
            f"# Target role: {state.get('target_role')}",
            "# Scores\n" + _score_table(state),
            "# Critical fails\n" + _fails_block(state),
            "# Hidden guide (use only for the ideal-solution outline)\n" + "\n".join(guide_lines),
            "# Evaluator log\n```json\n"
            + "\n".join(str(entry) for entry in state.get("evaluator_log", []))
            + "\n```",
            "# Transcript\n"
            + "\n".join(
                f"[{t['role']} · {t.get('competency', '')}] {t.get('content', '')}"
                for t in state.get("transcript", [])
            ),
            "Produce the debrief Markdown now, following the five-section contract.",
        ]
    )

    return chat(
        system=_prompt(),
        user=user,
        model=cfg.model_debrief,
        temperature=cfg.temp_debrief,
        max_tokens=3000,
    )