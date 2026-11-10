# Dispersion-dial under-retention at 8K/16K: mechanism audit (Task 18)

Follow-up to `ext8k_run_notes_2026-11-10.md`: the adaptive `sage` dial
showed the project's first non-zero budget violations (4 @8K, 57 @16K;
all late-regime, all under-retention, never over). This note localizes the
root cause at source level and verifies it machine-free in seconds.

## Verdict (one line)

The exact-budget projector is INNOCENT; the deficits are a cache-refill
effect of the online protocol: when a layer's budget jumps by more than
the per-step refill (chunk = 64), the cache holds fewer entries than the
budget, and the engine keeps all of them (it cannot create entries).

## Source-level chain

1. `capped_waterfilling` (sage/allocation.py) ends with a deterministic
   repair loop and RAISES unless `sum(b) == B` with box constraints —
   it cannot emit an under-sum. Verified on 100,000 random SAGE-like
   instances (t up to 16384, tau in {0, 1.5, 3}): 0 failures.
2. The engine's compression (`_observe_and_compress`, sage/engine.py)
   enforces the per-layer budget as a ceiling: it evicts down to `b_l`.
   The only deficit path is the keep-all branch:
       if b_l >= n: total_retained += n; continue
   i.e. when `b_l > cache_l` the layer retains ALL it has (`n < b_l`).
3. Budget dynamics: `b_l(t) = w_l(t) * B(t)`, `B = rho*L*t` (proportional
   contract). A weight-share shift `delta_w` moves a layer's budget by
   `delta_w * B(t)` — amplified by t. The cache refills at a fixed
   `chunk = 64` entries/step. Starvation occurs when
   `delta_b_l(t) > 64` in the unfavourable direction, i.e.
   `delta_w > 64/B(t) ~ 0.23%` at t=5888 (the observed onset), `~0.08%`
   at 16K depth. Static-weight policies move `w_l * delta_B ~ 13/step
   << 64`, hence never starve (sage-uniform / h2o / pyramidkv: 0
   violations at both windows).
4. Recovery: the starved layer refills at 64/step, so deficits are
   transient and self-correcting; the ceiling (cache <= budget) holds at
   EVERY step. The floor is achieved up to availability — an honest,
   bounded behavior of the online protocol, not an allocation-integrity
   failure (Theorem 1 is about the projection, which is exact; verified).

## Machine verification (scripts/dial_violation_mechanism.py)

Replay of the budget-vs-cache race with engine semantics
(`retained_l = min(cache_l, b_l)`), no model required:

| weights | T=8192 | T=16384 |
|---|---|---|
| static (uniform) | 0 violations | 0 violations |
| adaptive (kappa-EMA, 5 seeds) | 490, all-under, max diff 2466 | 1130, all-under, max diff 7799 |

The synthetic kappa drifts harder than the real 1.5B attention entropy
(onset t=1408 vs the real 5888), so magnitudes are upper bounds — but the
signature class matches the real run exactly: adaptive-only, all-negative
(never over), |diff| growing with depth, static immune.

## Interpretation for the paper

- Report as an honest finding with a located cause: the adaptive dial's
  budget can outrun the cache in deep windows; the exact projection is
  intact and the deficit is bounded by the refill rate and self-corrects.
- This REINFORCES the dial-guide recommendation: sage-uniform is the
  deployment default (best PPL at 8K/16K AND floor-exact at every depth).
- No code change proposed in this round: raising the floor would require
  either larger chunks (changes the matched-entry protocol) or budget
  smoothing (changes published 4K behavior). Both are protocol-level
  decisions for future work, documented here.
