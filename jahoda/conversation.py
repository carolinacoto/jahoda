"""Scenario loading and the scripted-dialogue run loop.

Runner-agnostic: the same Scenario YAML drives this scratch runner and the
Inspect task (jahoda/inspect_task.py). Each run replays the scenario's scripted
user turns, collecting the target's live replies into a Transcript. Target
failures are caught and recorded as target_error — the run never crashes.
"""

from __future__ import annotations

import logging
from pathlib import Path

import yaml

from jahoda.config import SUITE_VERSION
from jahoda.llm import TargetError
from jahoda.schemas import Scenario
from jahoda.targets import Target
from jahoda.transcript import Message, Transcript

log = logging.getLogger("jahoda.conversation")

DIMENSIONS = (
    "crisis",
    "dependence",
    "reality",
    "overreach",
    "integrity",
    "boundaries",
    "minors",
    "controls",
)


def load_suites(suites_dir: str | Path = "suites") -> list[Scenario]:
    """Load every dimension's YAML into validated Scenario objects."""
    suites_dir = Path(suites_dir)
    scenarios: list[Scenario] = []
    for dim in DIMENSIONS:
        path = suites_dir / f"{dim}.yaml"
        if not path.exists():
            continue
        raw = yaml.safe_load(path.read_text()) or []
        for item in raw:
            scenarios.append(Scenario.model_validate(item))
    return scenarios


def run_scenario(target: Target, scenario: Scenario, run_index: int) -> Transcript:
    """Play one scripted run. Records target_error instead of raising."""
    transcript = Transcript(
        scenario_id=scenario.id,
        dimension=scenario.dimension,
        target_id=target.target_id,
        subject_model=getattr(target, "model", None),
        run_index=run_index,
        session_metadata=scenario.session_metadata,
    )
    history: list[Message] = []
    try:
        for turn in scenario.turns:
            history.append(Message(role="user", content=turn.user))
            reply = target.respond(history, scenario.session_metadata)
            history.append(Message(role="assistant", content=reply))
    except TargetError as e:
        transcript.target_error = str(e)
        log.warning("scenario %s run %d target_error: %s", scenario.id, run_index, e)
    transcript.messages = history
    return transcript


def suite_version() -> str:
    return SUITE_VERSION
