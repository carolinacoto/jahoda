"""Suite-coverage guards (rubric A3/A3b). No API key required."""

import collections

from jahoda.conversation import load_suites
from jahoda.criteria import load_criteria

MINIMUMS = {
    "crisis": 8,
    "dependence": 6,
    "reality": 6,
    "overreach": 8,
    "integrity": 8,
    "boundaries": 6,
    "minors": 4,
    "controls": 8,
}

BOUNDARY_TYPES = {
    "clean_exit",
    "marathon_session",
    "displacement",
    "return_pressure",
    "exit_under_load",
    "coercive_restraint",
}


def test_minimum_scenario_counts():
    scen = load_suites()
    counts = collections.Counter(s.dimension for s in scen)
    for dim, lo in MINIMUMS.items():
        assert counts[dim] >= lo, f"{dim} has {counts[dim]} < {lo}"


def test_every_scenario_multi_turn():
    for s in load_suites():
        assert len(s.turns) >= 3, f"{s.id} has < 3 user turns"


def test_boundaries_covers_six_types():
    types = {s.scenario_type for s in load_suites() if s.dimension == "boundaries"}
    assert BOUNDARY_TYPES <= types, f"missing boundary types: {BOUNDARY_TYPES - types}"


def test_controls_have_twin_of():
    for s in load_suites():
        if s.dimension == "controls":
            assert s.twin_of, f"control {s.id} missing twin_of"


def test_every_referenced_criterion_has_file():
    crit = load_criteria()
    referenced = {c for s in load_suites() for c in s.criteria}
    missing = referenced - set(crit)
    assert not missing, f"criteria referenced but no file: {missing}"


def test_crisis_seven_behaviors_covered():
    # B1b: each of the 7 crisis behaviors covered by >= 1 scenario
    behaviors = {
        "crisis.detect_risk",
        "crisis.ask_directly",
        "crisis.connection_first",
        "crisis.warm_referral",
        "crisis.ai_limits",
        "crisis.safe_messaging",
        "crisis.no_abandonment",
    }
    used = {c for s in load_suites() if s.dimension == "crisis" for c in s.criteria}
    assert behaviors <= used, f"crisis behaviors not covered: {behaviors - used}"


def test_tessa_criteria_present():
    used = {c for s in load_suites() if s.dimension == "crisis" for c in s.criteria}
    assert "crisis.no_numeric_prescription" in used
    assert "crisis.no_method_detail" in used
    assert "crisis.no_coping_framing" in used
