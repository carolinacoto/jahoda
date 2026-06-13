"""jahoda CLI — run the harness against any chat endpoint."""

from __future__ import annotations

import logging
import sys
import uuid
from pathlib import Path

import click

from jahoda.config import RUNS_PER_SCENARIO
from jahoda.conversation import load_suites
from jahoda.criteria import load_criteria
from jahoda.engine import full_run, select_smoke
from jahoda.schemas import Report
from jahoda.subject import (
    SPECIMEN_ID,
    VANILLA_ID,
    build_specimen_target,
)
from jahoda.targets import HTTPTarget


def _configure_logging(run_id: str) -> None:
    logging.basicConfig(
        level=logging.INFO,
        format=f"%(asctime)s run={run_id} %(name)s %(levelname)s %(message)s",
        stream=sys.stderr,
    )


def _print_summary(report: Report) -> None:
    click.echo("")
    click.echo(f"  TARGET   {report.target_id} ({report.target_audience})")
    click.echo(f"  RUNS     {report.runs_per_scenario}/scenario · temp {report.temperature}")
    click.echo(f"  JUDGES   {report.judge_models}")
    click.echo("  " + "-" * 58)
    for d in report.dimensions:
        n_pass = sum(1 for sr in d.scenario_results if sr.pass_pow_k)
        if d.mean_score is not None:
            metric = f"mean {d.mean_score:.2f}"
        elif d.over_trigger_rate is not None and d.dimension == "controls":
            metric = f"over-trigger {d.over_trigger_rate * 100:.0f}%"
        else:
            metric = f"pass^k {n_pass}/{d.n_scenarios}"
        click.echo(f"  {d.dimension:12} {metric}")
    if report.calibration:
        click.echo("  " + "-" * 58)
        click.echo(f"  judge-judge disagreement {report.calibration.disagreement_rate * 100:.1f}%")
    click.echo("")


@click.group()
def cli() -> None:
    """JAHODA — wellness verification harness for companion AI."""


@cli.command()
@click.option("--target", "target_spec", required=True, help="specimen | vanilla | <http url>")
@click.option("--smoke", is_flag=True, help="run only the 8 flagship scenarios (<5 min)")
@click.option("--runs", type=int, default=RUNS_PER_SCENARIO, help="runs per scenario")
@click.option("--out", type=click.Path(), default=None, help="output dir for report + transcripts")
@click.option("--workers", type=int, default=8)
def run(target_spec: str, smoke: bool, runs: int, out: str | None, workers: int) -> None:
    """Run the suites against a target and write a report."""
    run_id = uuid.uuid4().hex[:8]
    _configure_logging(run_id)

    is_specimen = target_spec == "specimen"
    scenarios = load_suites()
    # external targets run all suites EXCEPT minors (liability).
    if not is_specimen:
        scenarios = [s for s in scenarios if s.dimension != "minors"]
    if smoke:
        scenarios = select_smoke(scenarios, include_minors=is_specimen)

    criteria = load_criteria()

    vanilla_server = None
    if is_specimen:
        target = build_specimen_target()
        target_id = SPECIMEN_ID
    elif target_spec == "vanilla":
        from jahoda.vanilla_server import serve_in_thread

        vanilla_server = serve_in_thread(port=8900)
        target = HTTPTarget(VANILLA_ID, "http://127.0.0.1:8900/chat", audience="adult-only")
        target_id = VANILLA_ID
    elif target_spec.startswith("http"):
        target = HTTPTarget("http-target", target_spec, audience="adult-only")
        target_id = "http-target"
    else:
        raise click.BadParameter(f"unknown target: {target_spec}")

    out_dir = Path(out) if out else Path("reports") / target_id
    click.echo(
        f"jahoda run · {target_id} · {len(scenarios)} scenarios · {runs} runs · run_id={run_id}"
    )
    try:
        report = full_run(
            target=target,
            scenarios=scenarios,
            date=_today(),
            out_dir=out_dir,
            criteria=criteria,
            runs_per_scenario=runs,
            max_workers=workers,
        )
    finally:
        if vanilla_server:
            vanilla_server.shutdown()

    _print_summary(report)
    click.echo(f"report: {out_dir / 'report.html'}")


def _today() -> str:
    # imported lazily so importing the module has no clock dependency
    from datetime import date

    return date.today().isoformat()


if __name__ == "__main__":
    cli()
