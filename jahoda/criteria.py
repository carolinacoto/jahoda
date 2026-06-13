"""Per-criterion grading rubric files (one YAML per criterion).

verifier/criteria/<dimension>/<short_id>.yaml. Each carries its source citation
and a review_status so credentialed reviewers can propose changes via PR
(CONTRIBUTING.md). One criterion per judge call — never holistic scoring.
"""

from __future__ import annotations

from pathlib import Path
from typing import Literal

import yaml
from pydantic import BaseModel, Field


class Criterion(BaseModel):
    id: str  # e.g. crisis.detect_risk
    dimension: str
    title: str
    kind: Literal["safety_critical", "quality"]
    question: str  # the single yes/no or anchored question the judge answers
    anchors: dict[str, str]  # level -> what that verdict/score looks like
    examples: dict[str, str] = Field(default_factory=dict)  # level -> short example
    source: str  # research grounding, named in the report
    methodology: str | None = None  # e.g. INTIMA three-way; psychosis-bench DCS
    version: str = "0.1"
    review_status: str = "awaiting-expert-review"
    reviewer_orcid: str = ""  # empty at launch; the slot for a credentialed reviewer

    @property
    def short_id(self) -> str:
        return self.id.split(".", 1)[1] if "." in self.id else self.id


def load_criteria(root: str | Path = "verifier/criteria") -> dict[str, Criterion]:
    root = Path(root)
    out: dict[str, Criterion] = {}
    for path in sorted(root.glob("*/*.yaml")):
        data = yaml.safe_load(path.read_text())
        crit = Criterion.model_validate(data)
        out[crit.id] = crit
    return out
