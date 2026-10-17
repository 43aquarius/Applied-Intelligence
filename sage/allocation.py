"""SAGE v2: corrected layer-wise budget allocation.

This module fixes the P0 mathematical flaw of the original SAGE submission:
the original formula  b_l = clip(rho*t*(kappa_l/kappa_bar)^tau, b_min*t, t)
does NOT guarantee  sum_l b_l <= rho*L*t  because
mean_l[(kappa_l/kappa_bar)^tau] != 1 for tau != 0 (Jensen).

The corrected allocator computes, at every step, the projection of a
weight-proportional ideal allocation onto the capped simplex

    { b in Z^L :  lower_l <= b_l <= upper_l,  sum_l b_l = B }

via bisection on the water level mu ("capped water-filling"). Theorem 1
(allocation.py) guarantees an EXACT global budget with per-layer floors
(protected sinks + recent window) and caps, in O(L log B) time.
"""
from __future__ import annotations

import numpy as np

__all__ = [
    "InfeasibleBudget",
    "capped_waterfilling",
    "uniform_weights",
    "pyramid_weights",
    "entropy_weights",
]


class InfeasibleBudget(ValueError):
    """Raised when no allocation satisfies the box + budget constraints."""


def capped_waterfilling(
    weights: np.ndarray,
    lower: np.ndarray,
    upper: np.ndarray,
    budget: int,
    max_iter: int = 128,
) -> np.ndarray:
    """Exact-budget allocation by capped water-filling projection.

    Solves:  b_l = clip(w_l * mu, lower_l, upper_l),  sum_l b_l = budget,
    returning INTEGER budgets with the sum exactly equal to ``budget``.

    Parameters
    ----------
    weights : (L,) nonnegative weights (normalized internally). The ray
        {mu * w} is the "ideal" proportional allocation being projected.
    lower   : (L,) integer lower bounds (e.g. protected-region sizes).
    upper   : (L,) integer upper bounds (e.g. per-layer capacity t).
    budget  : global budget B with sum(lower) <= B <= sum(upper).

    Returns
    -------
    b : (L,) int64 array with lower <= b <= upper and sum(b) == budget.

    Notes
    -----
    Theorem 1 (exactness). Let f(mu) = sum_l clip(w_l*mu, lower_l, upper_l).
    f is continuous and non-decreasing with f(0) = sum(lower) <= B and
    f(mu_max) = sum(upper) >= B for mu_max = max_l upper_l/w_l, hence a
    root mu* of f(mu) = B exists (IVT). Integerisation uses floor plus
    largest-remainder rounding restricted to feasible directions, which
    preserves the exact sum and the box constraints whenever the instance
    is feasible. Bisection needs O(log(mu_max/eps)) <= O(log B) iterations.
    """
    w = np.asarray(weights, dtype=np.float64)
    lo = np.asarray(lower, dtype=np.int64)
    up = np.asarray(upper, dtype=np.int64)
    B = int(budget)

    if w.ndim != 1 or lo.shape != w.shape or up.shape != w.shape:
        raise ValueError("weights/lower/upper must be 1-D of equal length")
    if np.any(w < 0) or np.any(lo > up) or np.any(lo < 0):
        raise InfeasibleBudget("invalid inputs")
    s = w.sum()
    if s <= 0:
        raise InfeasibleBudget("weights sum to zero")
    w = w / s
    L = w.shape[0]

    sum_lo, sum_up = int(lo.sum()), int(up.sum())
    if not (sum_lo <= B <= sum_up):
        raise InfeasibleBudget(
            f"budget {B} outside feasible box [{sum_lo}, {sum_up}]"
        )

    # Degenerate cases: budget sits on a face of the box.
    if B == sum_lo:
        return lo.copy()
    if B == sum_up:
        return up.copy()

    # Zero-weight layers are pinned at their lower bound.
    pos = w > 0
    if not pos.any():
        # All weights zero but sum(lower) < B < sum(upper): spread over layers
        # with slack, largest-capacity first (deterministic tie-break).
        b = lo.copy()
        slack = up - lo
        rem = B - sum_lo
        order = np.argsort(-slack, kind="stable")
        for idx in order:
            if rem == 0:
                break
            add = min(int(slack[idx]), rem)
            b[idx] += add
            rem -= add
        assert rem == 0 and b.sum() == B
        return b

    # Bisection on the water level mu.
    # Invariant: f(lo_mu) <= B <= f(hi).
    hi = float(np.max(up[pos] / w[pos])) + 1.0
    lo_mu = 0.0

    def f(mu: float) -> float:
        return float(np.clip(w * mu, lo, up).sum())

    for _ in range(8):
        if f(hi) >= B:
            break
        hi *= 2.0
    else:
        raise InfeasibleBudget("could not bracket the water level")

    for _ in range(max_iter):
        mid = 0.5 * (lo_mu + hi)
        if f(mid) < B:
            lo_mu = mid
        else:
            hi = mid
        if hi - lo_mu < 1e-9:
            break

    b_int = np.clip(w * hi, lo, up).astype(np.int64)
    # Largest-remainder rounding subject to the box constraints.
    ideal = w * hi
    rem = B - int(b_int.sum())
    if rem > 0:
        frac = ideal - b_int
        order = np.argsort(-frac, kind="stable")
        for idx in order:
            if rem == 0:
                break
            if b_int[idx] < up[idx]:
                b_int[idx] += 1
                rem -= 1
    elif rem < 0:
        frac = b_int - ideal
        order = np.argsort(-frac, kind="stable")
        for idx in order:
            if rem == 0:
                break
            if b_int[idx] > lo[idx]:
                b_int[idx] -= 1
                rem += 1

    # Deterministic repair if rounding could not absorb the residual
    # (only possible with pathological ties; feasibility guarantees slack).
    guard = 0
    while int(b_int.sum()) != B and guard < 10 * L + 10:
        guard += 1
        deficit = B - int(b_int.sum())
        if deficit > 0:
            cand = np.where(b_int < up)[0]
            if cand.size == 0:
                raise InfeasibleBudget("rounding repair failed (+)")
            b_int[cand[0]] += 1
        else:
            cand = np.where(b_int > lo)[0]
            if cand.size == 0:
                raise InfeasibleBudget("rounding repair failed (-)")
            b_int[cand[0]] -= 1
    if int(b_int.sum()) != B:
        raise InfeasibleBudget("failed to hit exact budget")
    if np.any(b_int < lo) or np.any(b_int > up):
        raise InfeasibleBudget("box constraint violated after rounding")
    return b_int


def uniform_weights(L: int) -> np.ndarray:
    """Uniform allocation weights (H2O / StreamingLLM style)."""
    return np.full(L, 1.0 / L)


def pyramid_weights(L: int, shape: str = "pyramid") -> np.ndarray:
    """Static per-layer weights following PyramidKV's pyramidal profile.

    'pyramid'         : linearly decreasing, bottom layers get the most
                        (PyramidKV's observation: lower layers scatter
                        attention, upper layers concentrate).
    'reverse-pyramid' : control condition (top layers get the most).
    """
    idx = np.arange(L, dtype=np.float64)
    if shape == "pyramid":
        g = (L - idx) + 1.0  # bottom layer L, top layer 1
    elif shape == "reverse-pyramid":
        g = idx + 1.0
    else:
        raise ValueError(shape)
    return g / g.sum()


def entropy_weights(kappa: np.ndarray, tau: float = 1.5) -> np.ndarray:
    """SAGE's adaptive weights from per-layer dispersion signals.

    kappa_l in [0, 1] (e.g. normalised attention entropy of layer l).
    Returns weights proportional to kappa_l ** tau, normalised to sum 1.
    Unlike the original submission, the normalisation happens BEFORE any
    exponent-dependent bookkeeping and the projection afterwards enforces
    the global budget exactly, so Jensen-type overshoot cannot occur.
    """
    k = np.asarray(kappa, dtype=np.float64)
    if np.any(k < 0):
        raise ValueError("kappa must be nonnegative")
    w = np.power(np.maximum(k, 0.0) + 1e-12, float(tau))
    s = w.sum()
    if s <= 0:
        return uniform_weights(k.shape[0])
    return w / s
