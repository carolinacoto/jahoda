"""Core Pydantic schemas: scenario, verdict, report.

Validated at load time. No raw-dict plumbing crosses module boundaries.
"""

from __future__ import annotations

from enum import StrEnum
from typing import Literal

from pydantic import BaseModel, Field, field_validator

# ─────────────────────────── scenario ───────────────────────────


class Turn(BaseModel):
    """One scripted user line in a multi-turn scenario."""

    user: str = Field(..., min_length=1)


class SessionMetadata(BaseModel):
    """Injected session state for time-aware (boundaries/minors) scenarios."""

    message_count: int | None = None
    elapsed_minutes: int | None = None
    local_hour: int | None = None  # 0-23, fictional
    suspected_minor: bool = False


class Scenario(BaseModel):
    """A multi-turn conversation script plus the criteria it is graded on."""

    id: str
    dimension: str
    title: str
    scenario_type: str | None = None  # e.g. boundaries "clean_exit"
    safety_critical: bool = False
    turns: list[Turn] = Field(..., min_length=3)
    criteria: list[str]  # criterion ids in verifier/criteria/<dimension>/
    session_metadata: SessionMetadata | None = None
    twin_of: str | None = None  # controls: names the suite/scenario it mirrors
    audience: Literal["adult-only", "all-ages"] | None = None
    notes: str | None = None

    @field_validator("turns")
    @classmethod
    def _min_three_user_turns(cls, v: list[Turn]) -> list[Turn]:
        if len(v) < 3:
            raise ValueError("every scenario needs >= 3 user turns")
        return v


# ─────────────────────────── verdict ───────────────────────────


class VerdictValue(StrEnum):
    PASS = "pass"
    FAIL = "fail"
    INSUFFICIENT = "insufficient_evidence"


class Confidence(StrEnum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


class Verdict(BaseModel):
    """A single judge call's structured output for one criterion."""

    scenario_id: str
    criterion_id: str
    dimension: str
    run_index: int
    verdict: VerdictValue
    confidence: Confidence
    evidence_quote: str  # must string-match the transcript
    reasoning: str
    severity: Literal["low", "medium", "high"] | None = None
    score: int | None = None  # anchored scale for quality criteria (1-5)
    judge_model: str
    rubric_version: str
    quote_verified: bool = False
    escalated: bool = False
    escalation_model: str | None = None


# ─────────────────────────── report ───────────────────────────


class Interval(BaseModel):
    lower: float
    upper: float


class ScenarioResult(BaseModel):
    scenario_id: str
    dimension: str
    safety_critical: bool
    runs: int
    passes: int  # runs that passed
    pass_pow_k: bool  # all-k-trials pass (pass^k gate)
    wilson: Interval
    mean_score: float | None = None
    verdicts: list[Verdict] = Field(default_factory=list)
    transcript_refs: list[str] = Field(default_factory=list)
    target_error: str | None = None


class DimensionResult(BaseModel):
    dimension: str
    source: str  # research grounding named in the report
    safety_critical: bool
    n_scenarios: int
    pass_pow_k_rate: float  # fraction of scenarios passing the pass^k gate
    suite_interval: Interval | None = None  # cluster bootstrap
    mean_score: float | None = None
    over_trigger_rate: float | None = None  # from controls
    scenario_results: list[ScenarioResult] = Field(default_factory=list)


class JudgeCalibration(BaseModel):
    n: int
    cohen_kappa: float | None = None
    raw_agreement: float | None = None
    disagreement_rate: float | None = None
    note: str | None = None  # e.g. "kappa pending human labels"


class Report(BaseModel):
    target_id: str
    target_audience: Literal["adult-only", "all-ages"]
    harness_version: str
    suite_version: str
    date: str
    subject_model: str | None = None
    judge_models: dict[str, str] = Field(default_factory=dict)
    temperature: float = 0.0
    runs_per_scenario: int
    dimensions: list[DimensionResult] = Field(default_factory=list)
    calibration: JudgeCalibration | None = None
    framing: str = (
        "A passing report means this agent handled these scenarios correctly "
        "on this date. Passing is necessary, not sufficient; never a guarantee."
    )
