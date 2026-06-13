"""Run orchestration: drive a target, grade transcripts, emit the report.

Conversation runs fan out across (scenario, run) units. Grading fans out across
transcripts; a transcript's criterion calls run sequentially so the cached
[system + transcript] blocks stay warm within the 5-minute TTL (~80-90% judge
cost cut). Inspect AI gives this concurrency for free when used as the
substrate; this scratch path is the runner-agnostic fallback the timebox rule
allows, reading the same YAML.
"""

from __future__ import annotations

import logging
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

from jahoda.config import HARNESS_VERSION, MODELS, RUNS_PER_SCENARIO, SUITE_VERSION
from jahoda.conversation import run_scenario
from jahoda.criteria import Criterion, load_criteria
from jahoda.report import GradedRun, aggregate
from jahoda.report_html import render_html
from jahoda.schemas import Report, Scenario, Verdict
from jahoda.targets import Target
from jahoda.transcript import Transcript
from jahoda.verifier import grade

log = logging.getLogger("jahoda.engine")

SMOKE_IDS_HINT = {
    "crisis": ["gradual", "buried", "01"],
    "boundaries": ["clean"],
    "dependence": ["only", "gets_me", "sole"],
    "reality": ["01"],
    "overreach": ["01"],
    "minors": ["age", "cue", "01"],
    "controls": ["01"],
}


def select_smoke(scenarios: list[Scenario], include_minors: bool) -> list[Scenario]:
    """Exactly the flagship set for the <5 min live demo."""
    by_dim: dict[str, list[Scenario]] = {}
    for s in scenarios:
        by_dim.setdefault(s.dimension, []).append(s)
    picks: list[Scenario] = []

    def pick(dim: str, hints: list[str]) -> Scenario | None:
        pool = by_dim.get(dim, [])
        for s in pool:
            blob = f"{s.id} {s.scenario_type or ''} {s.title}".lower()
            if any(h in blob for h in hints):
                return s
        return pool[0] if pool else None

    # two crisis flagships: gradual disclosure + Tessa-ED
    crisis = by_dim.get("crisis", [])
    grad = pick("crisis", ["gradual", "buried", "planning"]) or (crisis[0] if crisis else None)
    tessa = next(
        (
            s
            for s in crisis
            if "ed" in (s.scenario_type or "").lower() or "eating" in s.title.lower()
        ),
        None,
    )
    for s in (grad, tessa):
        if s and s not in picks:
            picks.append(s)
    for dim in ("boundaries", "dependence", "reality", "overreach"):
        s = pick(dim, SMOKE_IDS_HINT.get(dim, []))
        if s and s not in picks:
            picks.append(s)
    if include_minors:
        s = pick("minors", SMOKE_IDS_HINT["minors"])
        if s and s not in picks:
            picks.append(s)
    s = pick("controls", SMOKE_IDS_HINT["controls"])
    if s and s not in picks:
        picks.append(s)
    return picks


def _grade_transcript(
    transcript: Transcript, scenario: Scenario, criteria: dict[str, Criterion]
) -> list[Verdict]:
    if transcript.target_error:
        return []
    verdicts: list[Verdict] = []
    for cid in scenario.criteria:
        crit = criteria.get(cid)
        if crit is None:
            log.warning("scenario %s references unknown criterion %s", scenario.id, cid)
            continue
        verdicts.append(grade(transcript, crit))  # sequential -> cache stays warm
    return verdicts


def run_eval(
    *,
    target: Target,
    scenarios: list[Scenario],
    criteria: dict[str, Criterion],
    runs_per_scenario: int = RUNS_PER_SCENARIO,
    max_workers: int = 8,
    transcripts_dir: Path | None = None,
) -> dict[str, list[GradedRun]]:
    scen_by_id = {s.id: s for s in scenarios}

    # 1. conversation runs, fanned out across (scenario, run)
    run_tasks = [(s, r) for s in scenarios for r in range(runs_per_scenario)]
    log.info(
        "running %d conversations (%d scenarios x %d runs)",
        len(run_tasks),
        len(scenarios),
        runs_per_scenario,
    )
    with ThreadPoolExecutor(max_workers=max_workers) as pool:
        transcripts = list(pool.map(lambda t: run_scenario(target, t[0], t[1]), run_tasks))

    if transcripts_dir:
        for t in transcripts:
            d = transcripts_dir / target.target_id / t.scenario_id
            d.mkdir(parents=True, exist_ok=True)
            (d / f"run{t.run_index}.json").write_text(t.model_dump_json(indent=2))

    # 2. grade each transcript (criteria sequential within transcript for caching)
    def grade_one(t: Transcript) -> tuple[str, GradedRun]:
        verdicts = _grade_transcript(t, scen_by_id[t.scenario_id], criteria)
        return t.scenario_id, (t, verdicts)

    log.info("grading %d transcripts", len(transcripts))
    with ThreadPoolExecutor(max_workers=max_workers) as pool:
        results = list(pool.map(grade_one, transcripts))

    graded: dict[str, list[GradedRun]] = {}
    for sid, gr in results:
        graded.setdefault(sid, []).append(gr)
    return graded


def full_run(
    *,
    target: Target,
    scenarios: list[Scenario],
    date: str,
    out_dir: Path,
    criteria: dict[str, Criterion] | None = None,
    runs_per_scenario: int = RUNS_PER_SCENARIO,
    max_workers: int = 8,
) -> Report:
    criteria = criteria or load_criteria()
    out_dir.mkdir(parents=True, exist_ok=True)
    graded = run_eval(
        target=target,
        scenarios=scenarios,
        criteria=criteria,
        runs_per_scenario=runs_per_scenario,
        max_workers=max_workers,
        transcripts_dir=out_dir / "transcripts",
    )
    report = aggregate(
        target_id=target.target_id,
        audience=target.audience,
        subject_model=getattr(target, "model", None),
        scenarios=scenarios,
        criteria=criteria,
        graded=graded,
        runs_per_scenario=runs_per_scenario,
        date=date,
        suite_version=SUITE_VERSION,
        harness_version=HARNESS_VERSION,
    )
    (out_dir / "report.json").write_text(report.model_dump_json(indent=2))
    (out_dir / "report.html").write_text(render_html(report, criteria))
    # transcripts already persisted; also dump a flat index for the HTML links
    log.info("report written to %s (judge models: %s)", out_dir, MODELS.as_report_dict())
    return report
