"""Structured contracts between the evaluator and the controller."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

VALID_ACTIONS = {"probe_more", "advance", "revisit_previous", "end"}
VALID_CONFIDENCE = {"low", "medium", "high"}


class SchemaError(ValueError):
    """Raised when an LLM output does not conform to the expected schema."""


@dataclass
class EvaluatorOutput:
    competency_updates: dict[str, dict[str, Any]] = field(default_factory=dict)
    covered_items: list[str] = field(default_factory=list)
    missing_items: list[str] = field(default_factory=list)
    critical_fails: list[dict[str, str]] = field(default_factory=list)
    confidence: str = "low"
    recommended_action: str = "probe_more"
    suggested_probe: str = ""

    @classmethod
    def from_raw(cls, raw: dict[str, Any]) -> "EvaluatorOutput":
        if not isinstance(raw, dict):
            raise SchemaError("Evaluator output must be a JSON object.")

        updates = raw.get("competency_updates") or {}
        if not isinstance(updates, dict):
            raise SchemaError("`competency_updates` must be an object.")

        cleaned: dict[str, dict[str, Any]] = {}
        for comp, upd in updates.items():
            if not isinstance(upd, dict):
                continue
            score = upd.get("score")
            if score is not None:
                try:
                    score = int(score)
                except (TypeError, ValueError):
                    continue
                if score < 1 or score > 4:
                    continue
            evidence = upd.get("evidence") or []
            if not isinstance(evidence, list):
                evidence = []
            evidence = [str(e).strip() for e in evidence if str(e).strip()]
            if score is not None and not evidence:
                # A score without evidence is invalid; drop it.
                continue
            cleaned[comp] = {"score": score, "evidence": evidence}

        fails: list[dict[str, str]] = []
        for cf in raw.get("critical_fails") or []:
            if isinstance(cf, dict) and cf.get("id"):
                fails.append(
                    {"id": str(cf["id"]).strip(), "evidence": str(cf.get("evidence", "")).strip()}
                )

        action = str(raw.get("recommended_action", "probe_more")).strip()
        if action not in VALID_ACTIONS:
            action = "probe_more"

        confidence = str(raw.get("confidence", "low")).strip().lower()
        if confidence not in VALID_CONFIDENCE:
            confidence = "low"

        def _str_list(v):
            if not isinstance(v, list):
                return []
            return [str(x).strip() for x in v if str(x).strip()]

        return cls(
            competency_updates=cleaned,
            covered_items=_str_list(raw.get("covered_items")),
            missing_items=_str_list(raw.get("missing_items")),
            critical_fails=fails,
            confidence=confidence,
            recommended_action=action,
            suggested_probe=str(raw.get("suggested_probe", "")).strip(),
        )