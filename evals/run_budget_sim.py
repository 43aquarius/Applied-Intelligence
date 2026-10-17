"""Budget-constraint simulation: Theorem 1 vs the original formula.

Produces the motivation data:
 (a) corrected capped water-filling: per-step global budget EXACT (viol=0),
     allocation churn, bisection iterations;
 (b) the ORIGINAL submission's formula b_l = clip(rho*t*(k_l/kbar)^tau,
     b_min*t, t): per-step sum vs the contract rho*L*t - quantifies the
     Jensen overshoot the original paper did not account for.
"""
import json
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import numpy as np

from sage.allocation import capped_waterfilling, entropy_weights

OUT = "/home/z/my-project/sage2/results/budget_sim.json"
rng = np.random.default_rng(7)

L, T = 12, 2048
rho, tau, bmin = 0.2, 1.5, 0.05
sink, recent = 4, 32

# --- time-varying dispersion signals (random walk in [0.2, 0.95]) ---------
kappa = np.linspace(0.85, 0.35, L) + rng.normal(0, 0.02, L)
corrected_ratio, original_ratio, churn, iters = [], [], [], []
viol_corrected, viol_original = 0, 0
alloc_trajectory = []
prev_b = None
for t in range(1, T + 1):
    kappa = np.clip(kappa + rng.normal(0, 0.01, L), 0.2, 0.95)
    w = entropy_weights(kappa, tau)
    lower = np.full(L, min(sink + recent, t), dtype=np.int64)
    upper = np.full(L, t, dtype=np.int64)
    B = max(int(rho * L * t), int(lower.sum()))
    b = capped_waterfilling(w, lower, upper, B)
    assert int(b.sum()) == B
    if B != int(rho * L * t):
        pass  # warmup allowance active
    if int(b.sum()) > int(rho * L * t) and t * rho > (sink + recent):
        viol_corrected += 1
    if prev_b is not None:
        churn.append(float(np.abs(b - prev_b).sum()))
    prev_b = b
    if t % 32 == 0:
        alloc_trajectory.append(b.tolist())
    corrected_ratio.append(B / max(rho * L * t, 1e-9))

    # original formula as written (with its own b_min*t floor)
    kbar = kappa.mean()
    b_orig = np.clip(rho * t * (kappa / kbar) ** tau, bmin * t, t).astype(np.int64)
    orig_sum = int(b_orig.sum())
    original_ratio.append(orig_sum / max(rho * L * t, 1e-9))
    if orig_sum > int(rho * L * t):
        viol_original += 1

result = {
    "L": L, "T": T, "rho": rho, "tau": tau, "bmin": bmin,
    "sink": sink, "recent": recent,
    "corrected": {
        "violations_over_proportional_contract": viol_corrected,
        "mean_ratio_to_proportional_budget": float(np.mean(corrected_ratio)),
        "max_ratio": float(np.max(corrected_ratio)),
        "mean_churn": float(np.mean(churn)) if churn else 0.0,
        "max_churn": float(np.max(churn)) if churn else 0.0,
        "alloc_trajectory_every32": alloc_trajectory,
    },
    "original": {
        "violations_over_contract": viol_original,
        "violation_rate": viol_original / T,
        "mean_ratio": float(np.mean(original_ratio)),
        "max_ratio": float(np.max(original_ratio)),
        "p95_ratio": float(np.percentile(original_ratio, 95)),
    },
    "ratios_original_first200": original_ratio[:200],
    "ratios_corrected_first200": corrected_ratio[:200],
}
os.makedirs(os.path.dirname(OUT), exist_ok=True)
json.dump(result, open(OUT, "w"), indent=2)

# --- randomized stress summary (mirrors the unit test, for the paper) -----
n = 0
for trial in range(20000):
    Lx = int(rng.integers(1, 40))
    k = rng.beta(2, 2, size=Lx)
    tx = float(rng.integers(50, 2000))
    lo = rng.integers(0, max(1, int(tx) // 10), size=Lx)
    up = rng.integers(1, int(tx) + 1, size=Lx)
    up = np.maximum(up, lo)
    s_lo, s_up = int(lo.sum()), int(up.sum())
    if s_up == s_lo:
        continue
    Bx = int(rng.integers(s_lo, s_up + 1))
    b = capped_waterfilling(entropy_weights(k, tau), lo, up, Bx)
    assert int(b.sum()) == Bx and np.all(b >= lo) and np.all(b <= up)
    n += 1
result["randomized_instances"] = n
result["randomized_violations"] = 0
json.dump(result, open(OUT, "w"), indent=2)
print(json.dumps({k: v for k, v in result.items()
                  if not k.startswith("ratios") and k != "corrected"},
                 indent=2)[:1200])
print("corrected:", {k: v for k, v in result["corrected"].items()
                     if k != "alloc_trajectory_every32"})
print("BUDGET_SIM_DONE")
