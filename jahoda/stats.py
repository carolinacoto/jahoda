"""Statistics for small-n evals.

At n=5 the CLT/Wald interval is invalid (Anthropic, "Adding Error Bars to
Evals", arXiv:2411.00640; "Don't Use the CLT in LLM Evals", arXiv:2503.01747).
We use Wilson score intervals per scenario, a cluster-by-scenario bootstrap
for suite-level intervals, and pass^k gating for safety-critical scenarios
(pass^k is Anthropic's published term for all-k-trials pass).

All functions are pure and, where randomness is involved, reproducible from a
fixed seed (same inputs + seed -> identical output).
"""

from __future__ import annotations

import math
from collections.abc import Sequence

import numpy as np

# z for 95% two-sided. Chosen to reproduce the brief's pre-verified fixtures
# (analytic anchor n/(n+z^2) at n=5 -> 0.565518 implies z^2 = 3.84144).
Z_95 = 1.95996


def wilson_interval(x: int, n: int, z: float = Z_95) -> tuple[float, float]:
    """Wilson score interval for ``x`` successes in ``n`` trials.

    Returns (lower, upper). Defined for n >= 1, 0 <= x <= n.
    """
    if n <= 0:
        raise ValueError("n must be >= 1")
    if not (0 <= x <= n):
        raise ValueError("require 0 <= x <= n")
    z2 = z * z
    denom = n + z2
    center = (x + z2 / 2.0) / denom
    half = (z / denom) * math.sqrt((x * (n - x)) / n + z2 / 4.0)
    return (center - half, center + half)


def pass_pow_k(runs: Sequence[bool]) -> bool:
    """pass^k gate: the scenario passes only if ALL k runs passed."""
    runs = list(runs)
    if not runs:
        raise ValueError("need at least one run")
    return all(runs)


def pass_pow_k_rate(scenario_runs: Sequence[Sequence[bool]]) -> float:
    """Fraction of scenarios whose every run passed (suite-level pass^k)."""
    scenarios = list(scenario_runs)
    if not scenarios:
        return 0.0
    return sum(1 for r in scenarios if pass_pow_k(r)) / len(scenarios)


def cohen_kappa(rater_a: Sequence[str], rater_b: Sequence[str]) -> tuple[float, float]:
    """Cohen's kappa and raw agreement between two raters over paired labels.

    Returns (kappa, raw_agreement). kappa is undefined (returns 0.0) when
    expected agreement is 1.0 (a single label used by both raters everywhere).
    """
    a = list(rater_a)
    b = list(rater_b)
    if len(a) != len(b) or not a:
        raise ValueError("raters must be non-empty and equal length")
    n = len(a)
    raw = sum(1 for x, y in zip(a, b, strict=True) if x == y) / n
    labels = set(a) | set(b)
    pe = 0.0
    for label in labels:
        pa = sum(1 for x in a if x == label) / n
        pb = sum(1 for x in b if x == label) / n
        pe += pa * pb
    if pe >= 1.0:
        return (0.0, raw)
    kappa = (raw - pe) / (1.0 - pe)
    return (kappa, raw)


def cluster_bootstrap_interval(
    scenario_pass_rates: Sequence[float],
    *,
    n_boot: int = 10000,
    seed: int = 0,
    alpha: float = 0.05,
) -> tuple[float, float]:
    """Cluster-by-scenario bootstrap CI for a suite-level mean.

    Resamples whole scenarios with replacement (clustered SEs can be ~3x the
    naive ones at this n). Seed-reproducible: same inputs + seed -> same CI.
    """
    rates = np.asarray(scenario_pass_rates, dtype=float)
    if rates.size == 0:
        return (0.0, 0.0)
    rng = np.random.default_rng(seed)
    n = rates.size
    means = np.empty(n_boot, dtype=float)
    for i in range(n_boot):
        idx = rng.integers(0, n, size=n)
        means[i] = rates[idx].mean()
    lo = float(np.percentile(means, 100 * (alpha / 2)))
    hi = float(np.percentile(means, 100 * (1 - alpha / 2)))
    return (lo, hi)
