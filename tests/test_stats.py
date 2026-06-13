"""Statistics unit tests against the brief's pre-verified fixtures.

Each Wilson fixture was confirmed by two independent methods (tolerance 1e-5).
"""

import math

import pytest

from jahoda.stats import (
    Z_95,
    cluster_bootstrap_interval,
    cohen_kappa,
    pass_pow_k,
    pass_pow_k_rate,
    wilson_interval,
)

TOL = 1e-5

# (x, n) -> (lower, upper), 95%, z = 1.95996
WILSON_FIXTURES = [
    ((3, 5), (0.230724, 0.882379)),
    ((4, 5), (0.375535, 0.963776)),
    ((9, 10), (0.595850, 0.982124)),
    ((7, 8), (0.529112, 0.977583)),
    ((20, 25), (0.608690, 0.911394)),
    ((1, 5), (0.036224, 0.624465)),
]


@pytest.mark.parametrize("xn,expected", WILSON_FIXTURES)
def test_wilson_fixtures(xn, expected):
    lo, hi = wilson_interval(*xn)
    assert lo == pytest.approx(expected[0], abs=TOL)
    assert hi == pytest.approx(expected[1], abs=TOL)


def test_wilson_analytic_anchor_x_equals_n():
    # x = n -> lower = n / (n + z^2)
    z2 = Z_95 * Z_95
    for n, expected_lower in [(5, 0.565518), (8, 0.675592)]:
        lo, hi = wilson_interval(n, n)
        assert lo == pytest.approx(n / (n + z2), abs=TOL)
        assert lo == pytest.approx(expected_lower, abs=TOL)
        assert hi == pytest.approx(1.0, abs=TOL)


def test_wilson_analytic_anchor_x_equals_zero():
    # x = 0 -> upper = z^2 / (n + z^2)
    z2 = Z_95 * Z_95
    for n in [5, 8, 10]:
        lo, hi = wilson_interval(0, n)
        assert lo == pytest.approx(0.0, abs=TOL)
        assert hi == pytest.approx(z2 / (n + z2), abs=TOL)


def test_wilson_validation():
    with pytest.raises(ValueError):
        wilson_interval(0, 0)
    with pytest.raises(ValueError):
        wilson_interval(6, 5)
    with pytest.raises(ValueError):
        wilson_interval(-1, 5)


def test_pass_pow_k():
    assert pass_pow_k([True, True, True, True, True]) is True
    assert pass_pow_k([True, True, False, True, True]) is False
    assert pass_pow_k([True]) is True
    with pytest.raises(ValueError):
        pass_pow_k([])


def test_pass_pow_k_rate():
    scenarios = [
        [True, True, True],
        [True, False, True],
        [True, True, True],
        [False, False, False],
    ]
    # 2 of 4 scenarios passed all runs
    assert pass_pow_k_rate(scenarios) == pytest.approx(0.5)
    assert pass_pow_k_rate([]) == 0.0


def test_bootstrap_seed_determinism():
    rates = [1.0, 1.0, 0.8, 1.0, 0.6, 1.0, 0.9, 1.0]
    a = cluster_bootstrap_interval(rates, n_boot=2000, seed=42)
    b = cluster_bootstrap_interval(rates, n_boot=2000, seed=42)
    assert a == b  # bit-identical for same seed
    c = cluster_bootstrap_interval(rates, n_boot=2000, seed=43)
    assert c != a  # different seed -> different draw
    # CI brackets the point mean
    lo, hi = a
    mean = sum(rates) / len(rates)
    assert lo <= mean <= hi
    assert 0.0 <= lo <= hi <= 1.0


def test_bootstrap_empty():
    assert cluster_bootstrap_interval([]) == (0.0, 0.0)


def test_cohen_kappa_perfect_and_chance():
    # perfect agreement -> kappa 1.0
    a = ["pass", "fail", "pass", "fail", "pass"]
    k, raw = cohen_kappa(a, a)
    assert k == pytest.approx(1.0)
    assert raw == pytest.approx(1.0)
    # known worked example: po=0.7, pe=0.5 -> kappa=0.4
    r1 = ["pass"] * 5 + ["fail"] * 5
    r2 = ["pass"] * 3 + ["fail"] * 2 + ["pass"] * 1 + ["fail"] * 4
    k2, raw2 = cohen_kappa(r1, r2)
    assert raw2 == pytest.approx(0.7, abs=TOL)
    assert k2 == pytest.approx(0.4, abs=TOL)


def test_cohen_kappa_validation():
    with pytest.raises(ValueError):
        cohen_kappa([], [])
    with pytest.raises(ValueError):
        cohen_kappa(["pass"], ["pass", "fail"])


def test_z_constant_matches_fixture_anchor():
    # n/(n+z^2) at n=5 must reproduce 0.565518
    z2 = Z_95 * Z_95
    assert 5 / (5 + z2) == pytest.approx(0.565518, abs=TOL)
    assert math.isclose(Z_95, 1.95996)
