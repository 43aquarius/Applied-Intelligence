"""Unit tests for the corrected allocator (Theorem 1 verification).

Run:  python -m pytest tests/test_allocation.py -q   (or python tests/test_allocation.py)
"""
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import numpy as np

from sage.allocation import (
    InfeasibleBudget,
    capped_waterfilling,
    entropy_weights,
    pyramid_weights,
    uniform_weights,
)

rng = np.random.default_rng(0)


def test_exact_budget_random_instances():
    """Theorem 1: randomized verification - sum is EXACTLY the budget."""
    n_bad = 0
    for trial in range(20000):
        L = int(rng.integers(1, 40))
        # random weights (entropy-like, sometimes zero)
        k = rng.beta(2, 2, size=L)
        if trial % 3 == 0:
            k[rng.integers(0, L)] = 0.0
        tau = float(rng.choice([0.5, 1.0, 1.5, 2.0]))
        w = entropy_weights(k, tau)
        # random floors and caps
        t = int(rng.integers(50, 2000))
        lower = rng.integers(0, max(1, t // 10), size=L)
        upper = rng.integers(1, t + 1, size=L)
        upper = np.maximum(upper, lower)
        sum_lo, sum_up = int(lower.sum()), int(upper.sum())
        if sum_up == sum_lo:
            continue
        B = int(rng.integers(sum_lo, sum_up + 1))
        b = capped_waterfilling(w, lower, upper, B)
        assert int(b.sum()) == B, (trial, B, b.sum())
        assert np.all(b >= lower) and np.all(b <= upper), trial
        assert b.dtype == np.int64
        n_bad += int(b.sum() != B)
    assert n_bad == 0


def test_jensen_overshoot_of_original_formula():
    """Quantifies the ORIGINAL paper's P0 flaw for the motivation section.

    Original: b_l = clip(rho*t*(k_l/kbar)^tau, b_min*t, t)
    Without clipping: sum_l b_l / (rho*L*t) = mean_l[(k_l/kbar)^tau],
    which is > 1 for tau > 1 whenever the kappa are spread (Jensen).
    """
    for trial in range(1000):
        L = int(rng.integers(2, 40))
        k = rng.beta(0.7, 0.7, size=L) + 1e-3  # spread dispersions
        kbar = k.mean()
        tau = 1.5
        ratios = (k / kbar) ** tau
        overshoot = ratios.mean()
        assert overshoot >= 1.0 - 1e-12  # Jensen: mean of convex power >= 1
    # A concrete instance used in the paper:
    k = np.array([0.91, 0.83, 0.77, 0.71, 0.66, 0.61, 0.55, 0.50,
                  0.46, 0.42, 0.38, 0.34])
    ratios = (k / k.mean()) ** 1.5
    return float(ratios.mean())


def test_monotone_in_kappa():
    """Higher dispersion (entropy) => weakly higher budget, ceteris paribus."""
    L = 12
    k = np.linspace(0.9, 0.3, L)
    w = entropy_weights(k, tau=1.5)
    lower = np.zeros(L, dtype=np.int64)
    t = 4000
    upper = np.full(L, t, dtype=np.int64)
    B = int(0.2 * L * t)
    b = capped_waterfilling(w, lower, upper, B)
    # budgets should be (weakly) decreasing with layer index (k decreasing)
    assert np.all(np.diff(b) <= 0), b


def test_degenerate_faces():
    L = 8
    w = uniform_weights(L)
    lower = np.full(L, 5, dtype=np.int64)
    upper = np.full(L, 100, dtype=np.int64)
    b1 = capped_waterfilling(w, lower, upper, int(lower.sum()))
    assert b1.sum() == lower.sum() and np.all(b1 == lower)
    b2 = capped_waterfilling(w, lower, upper, int(upper.sum()))
    assert b2.sum() == upper.sum() and np.all(b2 == upper)


def test_infeasible_raises():
    L = 4
    w = uniform_weights(L)
    lower = np.full(L, 10, dtype=np.int64)
    upper = np.full(L, 20, dtype=np.int64)
    try:
        capped_waterfilling(w, lower, upper, budget=100)  # > sum(upper)=80
        raised = False
    except InfeasibleBudget:
        raised = True
    assert raised
    try:
        capped_waterfilling(w, lower, upper, budget=30)  # < sum(lower)=40
        raised = False
    except InfeasibleBudget:
        raised = True
    assert raised


def test_zero_weight_layers():
    L = 6
    w = np.array([0.0, 0.3, 0.0, 0.2, 0.1, 0.4])
    lower = np.array([2, 0, 3, 0, 0, 0], dtype=np.int64)
    upper = np.full(L, 500, dtype=np.int64)
    B = 600
    b = capped_waterfilling(w, lower, upper, B)
    assert b.sum() == B
    assert b[0] == 2 and b[2] == 3  # pinned at floors


def test_budget_compliance_over_time():
    """Simulate online operation: floors grow with t (recent window)."""
    L, rho, s, r = 12, 0.2, 4, 32
    k = np.linspace(0.9, 0.3, L)
    w = entropy_weights(k, 1.5)
    for t in [64, 128, 256, 512, 1024, 2048]:
        lower = np.full(L, min(s + r, t), dtype=np.int64)  # protected region
        upper = np.full(L, t, dtype=np.int64)
        B = int(rho * L * t)
        if B < int(lower.sum()):
            # infeasible: protection exceeds budget -> documented precondition
            continue
        b = capped_waterfilling(w, lower, upper, B)
        assert b.sum() == B, t
        assert np.all(b <= t) and np.all(b >= lower)


def test_profiles():
    L = 12
    assert abs(uniform_weights(L).sum() - 1) < 1e-12
    p = pyramid_weights(L)
    assert np.all(np.diff(p) < 0), "pyramid must decrease with layer index"
    rp = pyramid_weights(L, "reverse-pyramid")
    assert np.all(np.diff(rp) > 0)
    assert abs(p.sum() - 1) < 1e-12 and abs(rp.sum() - 1) < 1e-12


if __name__ == "__main__":
    test_exact_budget_random_instances()
    ov = test_jensen_overshoot_of_original_formula()
    test_monotone_in_kappa()
    test_degenerate_faces()
    test_infeasible_raises()
    test_zero_weight_layers()
    test_budget_compliance_over_time()
    test_profiles()
    print(f"ALL ALLOCATION TESTS PASSED")
    print(f"Jensen overshoot of the ORIGINAL formula (example): {ov:.4f}")
    print("(i.e. original formula overshoots the nominal budget by "
          f"{(ov - 1) * 100:.1f}% before clipping - the P0 flaw)")
