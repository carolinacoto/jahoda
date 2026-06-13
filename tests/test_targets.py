"""Target-adapter resilience (rubric E2b). No API key required."""

from datetime import date

import jahoda.targets as targets_mod
from jahoda.conversation import run_scenario
from jahoda.criteria import load_criteria
from jahoda.llm import TargetError
from jahoda.report import aggregate
from jahoda.schemas import Scenario
from jahoda.targets import HTTPTarget


def _scenario() -> Scenario:
    return Scenario(
        id="overreach-test",
        dimension="overreach",
        title="unreachable target",
        safety_critical=True,
        turns=[{"user": "a"}, {"user": "b"}, {"user": "c"}],
        criteria=["overreach.refers_medical"],
    )


def test_unreachable_url_records_target_error(monkeypatch):
    # no real backoff sleeping in the test
    monkeypatch.setattr(targets_mod.time, "sleep", lambda *_: None)
    target = HTTPTarget(
        "http-target", "http://127.0.0.1:1/chat", audience="adult-only", timeout=0.2
    )
    transcript = run_scenario(target, _scenario(), run_index=0)
    assert transcript.target_error is not None
    assert "failed after retries" in transcript.target_error
    # the run did not crash and produced a transcript object
    assert transcript.scenario_id == "overreach-test"


def test_http_target_raises_targeterror(monkeypatch):
    monkeypatch.setattr(targets_mod.time, "sleep", lambda *_: None)
    target = HTTPTarget("x", "http://127.0.0.1:1/chat", audience="adult-only", timeout=0.2)
    from jahoda.transcript import Message

    try:
        target.respond([Message(role="user", content="hi")], None)
        raise AssertionError("expected TargetError")
    except TargetError:
        pass


def test_target_error_recorded_in_report(monkeypatch):
    monkeypatch.setattr(targets_mod.time, "sleep", lambda *_: None)
    target = HTTPTarget(
        "http-target", "http://127.0.0.1:1/chat", audience="adult-only", timeout=0.2
    )
    scen = _scenario()
    criteria = load_criteria()
    graded = {scen.id: [(run_scenario(target, scen, r), []) for r in range(3)]}
    report = aggregate(
        target_id="http-target",
        audience="adult-only",
        subject_model=None,
        scenarios=[scen],
        criteria=criteria,
        graded=graded,
        runs_per_scenario=3,
        date=date.today().isoformat(),
        suite_version="0.1",
        harness_version="0.1.0",
    )
    sr = report.dimensions[0].scenario_results[0]
    assert sr.target_error is not None  # surfaced, not swallowed
    assert sr.pass_pow_k is False  # an errored scenario cannot claim pass^k


def test_grade_safe_never_raises(monkeypatch):
    """A judge failure becomes a flagged insufficient verdict, not a crash (F4/R6)."""
    import jahoda.verifier as verifier
    from jahoda.llm import TargetError
    from jahoda.schemas import VerdictValue
    from jahoda.transcript import Message, Transcript

    def boom(*_a, **_k):
        raise TargetError("simulated judge timeout")

    monkeypatch.setattr(verifier, "grade", boom)
    crit = load_criteria()["crisis.detect_risk"]
    t = Transcript(
        scenario_id="x", dimension="crisis", target_id="fix", run_index=0,
        messages=[Message(role="user", content="hi")],
    )
    v = verifier.grade_safe(t, crit)
    assert v.verdict == VerdictValue.INSUFFICIENT
    assert "failed" in v.judge_model
