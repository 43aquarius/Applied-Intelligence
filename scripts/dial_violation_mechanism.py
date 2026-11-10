#!/usr/bin/env python3
"""Task 18: verify the under-retention mechanism of the adaptive dial at 8K/16K.

Two verifications, both model-free (seconds):

  A. Allocator exactness: capped_waterfilling must return sum(b) == B with
     box constraints on every feasible instance (exonerates the Theorem-1
     projector; the observed violations cannot originate there).

  B. Cache-refill dynamics replay: per-layer cache grows by chunk=64/step;
     compression enforces the budget as a CEILING; when budget_l > cache_l
     the engine keeps all cache_l entries (under-retention). Replay the
     budget-vs-cache race with static vs adaptive (kappa-EMA) weights:
     static -> 0 violations at any depth; adaptive -> late-regime
     under-retention whose signature matches the observed run
     (t >= ~5900 onset, all-negative diffs, |diff| growing with t).
"""
import numpy as np
import sys

import os
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))

from sage.allocation import (capped_waterfilling, uniform_weights)  # noqa: E402

L, CHUNK, RHO = 24, 64, 0.2
SINK, RECENT = 4, 32


# ---------------------------------------------------------------------------
# A. allocator exactness on 100k random SAGE-like instances
# ---------------------------------------------------------------------------
def test_allocator(n=100_000, seed=0):
    rng = np.random.default_rng(seed)
    bad = 0
    for _ in range(n):
        t = int(rng.integers(128, 16385))
        kappa = rng.uniform(0.05, 1.0, L)
        tau = rng.choice([0.0, 1.5, 3.0])
        w = np.power(kappa + 1e-12, tau)
        w = w / w.sum()
        lower = np.full(L, min(SINK + RECENT, t), dtype=np.int64)
        upper = np.full(L, t, dtype=np.int64)
        B = max(int(RHO * L * t), int(lower.sum()))
        B = min(B, int(upper.sum()))
        b = capped_waterfilling(w, lower, upper, B)
        if int(b.sum()) != B or np.any(b < lower) or np.any(b > upper):
            bad += 1
    print(f"A. allocator exactness: {n} instances, {bad} failures "
          f"({'PASS' if bad == 0 else 'FAIL'})")
    return bad == 0


# ---------------------------------------------------------------------------
# B. budget-vs-cache race replay (engine semantics, model-free)
# ---------------------------------------------------------------------------
def replay(weights_mode, T, seed=0, beta=0.9, tau=1.5, verbose=False):
    """Simulate per-layer cache/budget dynamics with engine semantics.

    cache_l(t) = retained_l(t-1) + CHUNK   (chunk append)
    retained_l(t) = min(cache_l(t), b_l(t))  (compress: ceiling exact,
                                             keep-all when b_l > cache_l)
    nominal(t) = rho*L*t ; b = capped_waterfilling(w(t), ..., nominal)
    """
    rng = np.random.default_rng(seed)
    kappa = np.ones(L)
    cache = np.zeros(L, dtype=np.int64)
    violations = []          # (t, nominal - total_retained)
    protected = SINK + RECENT
    for step in range(1, T // CHUNK + 1):
        t = step * CHUNK
        if weights_mode == "adaptive":
            # one observation per step: entropy-ish signal in [0,1]
            obs = rng.beta(2.0, 3.0, L)
            kappa = beta * kappa + (1 - beta) * obs
            w = np.power(np.maximum(kappa, 0.0) + 1e-12, tau)
            w = w / w.sum()
        else:
            w = uniform_weights(L)
        lower = np.full(L, min(protected, t), dtype=np.int64)
        upper = np.full(L, t, dtype=np.int64)
        B = max(int(RHO * L * t), int(lower.sum()))
        b = capped_waterfilling(w, lower, upper, B)
        cache = cache + CHUNK                      # chunk append
        retained = np.minimum(cache, b)            # engine keep-all path
        total = int(retained.sum())
        if total != B:
            violations.append((t, B - total))
        cache = retained.copy()
    return violations


def summarize_run(name, T, violations):
    n = len(violations)
    if n:
        ts = [t for t, _ in violations]
        ds = [d for _, d in violations]
        print(f"B. {name} (T={T}): {n} violations, onset t={min(ts)}, "
              f"max |diff|={max(ds)}, all-under={all(d > 0 for d in ds)}")
    else:
        print(f"B. {name} (T={T}): 0 violations")


if __name__ == "__main__":
    ok = test_allocator()
    # static weights: expect 0 at both depths
    for mode, T in [("static", 8192), ("static", 16384),
                    ("adaptive", 8192), ("adaptive", 16384)]:
        # several seeds for the adaptive mode (stochastic kappa)
        if mode == "static":
            v = replay("static", T, seed=0)
            summarize_run(f"static-weights", T, v)
        else:
            all_v, seeds = [], 5
            for s in range(seeds):
                all_v += replay("adaptive", T, seed=s + 1)
            all_v.sort()
            summarize_run(f"adaptive(seed-avg x{seeds})", T, all_v)
    sys.exit(0 if ok else 1)
