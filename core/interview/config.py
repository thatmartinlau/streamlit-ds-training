"""Configuration for the interview simulator.

All knobs are environment-overridable so deployments don't need code edits.
Defaults intentionally match the spec (deepseek-chat, low-temp evaluator).
"""

from __future__ import annotations

import os
from dataclasses import dataclass


@dataclass(frozen=True)
class InterviewConfig:
    base_url: str
    model_interviewer: str
    model_evaluator: str
    model_debrief: str
    temp_interviewer: float
    temp_evaluator: float
    temp_debrief: float
    max_evaluator_retries: int
    transcript_window: int


def load_config() -> InterviewConfig:
    return InterviewConfig(
        base_url=os.environ.get("DEEPSEEK_BASE_URL", "https://api.deepseek.com"),
        model_interviewer=os.environ.get("DEEPSEEK_MODEL_INTERVIEWER", "deepseek-chat"),
        model_evaluator=os.environ.get("DEEPSEEK_MODEL_EVALUATOR", "deepseek-chat"),
        model_debrief=os.environ.get("DEEPSEEK_MODEL_DEBRIEF", "deepseek-chat"),
        temp_interviewer=float(os.environ.get("DEEPSEEK_TEMP_INTERVIEWER", "0.5")),
        temp_evaluator=float(os.environ.get("DEEPSEEK_TEMP_EVALUATOR", "0.1")),
        temp_debrief=float(os.environ.get("DEEPSEEK_TEMP_DEBRIEF", "0.3")),
        max_evaluator_retries=int(os.environ.get("INTERVIEW_EVALUATOR_RETRIES", "1")),
        transcript_window=int(os.environ.get("INTERVIEW_TRANSCRIPT_WINDOW", "10")),
    )