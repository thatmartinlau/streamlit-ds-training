"""Load case packs and the global rubric from disk."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml

_REPO_ROOT = Path(__file__).resolve().parents[2]
CASES_DIR = _REPO_ROOT / "cases"
RUBRIC_PATH = _REPO_ROOT / "rubric.yaml"


@dataclass
class CasePack:
    raw: dict[str, Any]

    @property
    def id(self) -> str:
        return self.raw["id"]

    @property
    def title(self) -> str:
        return self.raw.get("title", self.id)

    @property
    def difficulty(self) -> str:
        return self.raw.get("difficulty", "medium")

    @property
    def guide(self) -> dict[str, Any]:
        return self.raw.get("interviewer_guide", {})

    @property
    def business_context(self) -> str:
        return self.raw.get("business_context", "")

    @property
    def dataset_card(self) -> dict[str, Any]:
        return self.raw.get("dataset_card", {})

    @property
    def success_metric(self) -> dict[str, Any]:
        return self.raw.get("success_metric", {})


def _read_yaml(path: Path) -> Any:
    with path.open("r", encoding="utf-8") as fh:
        return yaml.safe_load(fh)


def load_rubric(path: Path = RUBRIC_PATH) -> dict[str, Any]:
    if not path.is_file():
        raise FileNotFoundError(f"Rubric file not found: {path}")
    raw = _read_yaml(path)
    if not isinstance(raw, dict) or "competencies" not in raw:
        raise ValueError(f"Rubric file is malformed: {path}")
    return raw


def list_cases(directory: Path = CASES_DIR) -> list[CasePack]:
    if not directory.is_dir():
        return []
    cases: list[CasePack] = []
    for path in sorted(directory.glob("*.yaml")) + sorted(directory.glob("*.yml")):
        raw = _read_yaml(path)
        if not isinstance(raw, dict) or "id" not in raw:
            continue
        cases.append(CasePack(raw=raw))
    return cases


def get_case(case_id: str, directory: Path = CASES_DIR) -> CasePack:
    for case in list_cases(directory):
        if case.id == case_id:
            return case
    raise KeyError(f"Case not found: {case_id}")