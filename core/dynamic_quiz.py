"""Batched dynamic screen: generate 5 questions, then evaluate all answers."""

from __future__ import annotations

import json
import os
import re

import streamlit as st
from openai import OpenAI

BASE_URL = "https://api.deepseek.com"
MODEL = "deepseek-flash"

DOMAINS = (
    "SQL",
    "Statistics & experimentation",
    "ML fundamentals",
    "Evaluation metrics & business framing",
    "Python / pandas",
    "Modern AI",
)


def get_secret(name: str) -> str | None:
    try:
        v = st.secrets.get(name)
        if v:
            return str(v).strip()
    except Exception:
        pass
    return (os.environ.get(name) or "").strip() or None


def _client() -> OpenAI:
    key = get_secret("DEEPSEEK_API_KEY")
    if not key:
        raise RuntimeError("DEEPSEEK_API_KEY is not configured.")
    return OpenAI(api_key=key, base_url=BASE_URL)


# --------------------------------------------------------------------------- #
#  Prompts
# --------------------------------------------------------------------------- #
GENERATE_SYSTEM = """\
You are a senior data scientist at Artefact running a technical screen
for a Data Scientist 1 (junior) role in data & AI consulting. Rigorous,
calm, business-minded, unimpressed by buzzwords.

Your task: generate exactly 5 technical questions in one batch, as JSON.

Return ONE JSON object:
{
  "questions": [
    {"id": 1, "topic": "<verbatim theme>", "question": "<one question>"},
    {"id": 2, "topic": "...", "question": "..."},
    {"id": 3, "topic": "...", "question": "..."},
    {"id": 4, "topic": "...", "question": "..."},
    {"id": 5, "topic": "...", "question": "..."}
  ]
}

Rules:
- Exactly 5 items. Each `topic` verbatim from the selected themes.
- No two consecutive questions from the same theme.
- Vary formats: conceptual explanation, SQL snippet, metric selection,
  short mini-case, debug-a-flawed-approach.
- At least 2 questions must connect a technical choice to a business
  decision or cost.
- Junior-appropriate: no backprop derivations, no obscure trivia, no
  LeetCode puzzles. Answerable in under 3 minutes (3-6 sentence answer).
- One question per item; no multi-part asks.
- No answers, hints, rubrics, or commentary. JSON only.
"""


def _generate_user_prompt(selected: list[str]) -> str:
    body = "\n".join(f"- {d}" for d in selected)
    return (
        "Selected themes (subset of the six domains; use these labels "
        "verbatim):\n"
        f"{body}\n\n"
        "Generate exactly 5 questions as JSON. Return only the JSON object."
    )


EVALUATE_SYSTEM = """\
You are the same senior data scientist at Artefact who wrote these 5
questions. Now score the candidate's answers and produce a single
consolidated feedback report.

Silently score each question:
- Strong:   correct, complete, business-aware
- Adequate: correct core, missing nuance or business link
- Weak:     incorrect or materially incomplete
- Skipped:  no answer given

Return a Markdown report and nothing else. Do not wrap it in JSON or
code fences. Start your response with the exact heading below and use
these five H2 sections in this order:

## 1. Scorecard
Table with columns: Question | Topic | Verdict | One-line reason.

## 2. Per-question breakdown
For each question: what they got right, what was missing, and a model
answer in 2-4 sentences.

## 3. Topic-level diagnosis
Which themes are solid, which are shaky, and any recurring pattern
across answers.

## 4. Overall verdict
Ready / Borderline / Not yet for an Artefact DS1 technical screen, with
explicit reasoning.

## 5. Top 3 study priorities
Ranked, each with one concrete drill or resource.

Tone: direct, specific, no flattery. Cite what the candidate actually said.
"""


def _evaluate_user_prompt(questions: list[dict], answers: list[str]) -> str:
    lines = ["Here are the 5 questions and the candidate's answers:", ""]
    for q, a in zip(questions, answers):
        lines.append(f"### Q{q['id']} — {q['topic']}")
        lines.append(f"Question: {q['question']}")
        lines.append(f"Answer: {a.strip() or '(Skipped)'}")
        lines.append("")
    lines.append("Return the JSON report now.")
    return "\n".join(lines)


# --------------------------------------------------------------------------- #
#  Parsing
# --------------------------------------------------------------------------- #
def _extract_json(text: str) -> dict:
    text = text.strip()
    if text.startswith("```"):
        text = re.sub(r"^```(?:json)?\s*", "", text)
        text = re.sub(r"\s*```$", "", text)
    return json.loads(text)


def _parse_questions(content: str, selected: list[str]) -> list[dict]:
    if not content.strip():
        raise ValueError("Model returned an empty response; try again.")
    payload = _extract_json(content)
    items = payload.get("questions")
    if not isinstance(items, list) or len(items) != 5:
        raise ValueError("Model did not return exactly 5 questions.")
    out = []
    for i, q in enumerate(items):
        if not isinstance(q, dict):
            raise ValueError("Each question must be a JSON object.")
        topic = str(q.get("topic", "")).strip()
        question = str(q.get("question", "")).strip()
        if not topic or not question:
            raise ValueError("Each question must have non-empty `topic` and `question`.")
        if topic not in selected:
            # Model paraphrased a theme; snap to the closest selected one.
            topic = selected[i % len(selected)]
        out.append({"id": i + 1, "topic": topic, "question": question})
    return out


def _parse_report(content: str) -> str:
    if not content.strip():
        raise ValueError("Model returned an empty response; try again.")

    text = content.strip()

    # 1. If the model wrapped it in JSON anyway (older prompt, or JSON mode
    #    enabled by mistake), unwrap it.
    if text.startswith("{"):
        try:
            payload = _extract_json(text)
            if isinstance(payload.get("report"), str):
                text = payload["report"].strip()
        except Exception:
            # Malformed JSON -> treat what we have as markdown and let the
            # validation below decide.
            pass

    # 2. Strip markdown code fences if the model added them.
    if text.startswith("```"):
        text = re.sub(r"^```(?:markdown|md)?\s*", "", text)
        text = re.sub(r"\s*```$", "", text).strip()

    # 3. Sanity check: the report should contain the section 1 heading.
    #    If it doesn't, it's almost certainly truncated or off-format.
    if "## 1." not in text and "## 1 " not in text.lower():
        preview = text[:300].replace("\n", " ")
        raise ValueError(
            f"Report is malformed (missing '## 1.' heading). "
            f"Response length: {len(text)} chars. Preview: {preview!r}"
        )

    return text

# --------------------------------------------------------------------------- #
#  Public API
# --------------------------------------------------------------------------- #
def generate_questions(selected: list[str]) -> list[dict]:
    if not selected:
        raise ValueError("Select at least one theme.")
    client = _client()
    response = client.chat.completions.create(
        model=MODEL,
        messages=[
            {"role": "system", "content": GENERATE_SYSTEM},
            {"role": "user", "content": _generate_user_prompt(selected)},
        ],
        response_format={"type": "json_object"},
        max_tokens=3000,
        temperature=0.7,
    )
    content = response.choices[0].message.content or ""
    return _parse_questions(content, selected)


def evaluate_answers(questions: list[dict], answers: list[str]) -> str:
    client = _client()
    response = client.chat.completions.create(
        model=MODEL,
        messages=[
            {"role": "system", "content": EVALUATE_SYSTEM},
            {"role": "user", "content": _evaluate_user_prompt(questions, answers)},
        ],
        # No response_format -- the model returns markdown directly.
        # A five-section report is longer than the generation output, so
        # give it a much larger token budget than the question batch.
        max_tokens=8000,
        temperature=0.3,   # lower -- we want consistent grading
    )

    choice = response.choices[0]
    content = choice.message.content or ""

    # If the model was cut off, say so plainly rather than failing on parse.
    if getattr(choice, "finish_reason", None) == "length":
        raise ValueError(
            "The evaluation was truncated because the response exceeded the "
            "max_tokens budget. Try evaluating fewer answers at a time, or "
            "raise max_tokens further."
        )

    return _parse_report(content)
