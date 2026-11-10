# 8K/16K Context Extension — Experiment Design Draft (prep-only, 2026-11-10)

**Status: DESIGN ONLY. Do NOT start any accelerator. Blocked on Kaggle credentials
(scripts/kaggle_api.json lost with the sandbox recycle; ask the user).**
All estimates below are estimates; the first on-GPU action is a single-run timing/memory probe
that revises them before the grid is committed.

## 1. Scientific goals (ordered)
1. **Contract scaling**: does the exact integer budget contract (Theorem 1) hold, with zero
   violations, at 8K/16K where per-layer budgets become small integers against large caches
   (harder rounding regime)? This is the headline claim to extend.
2. **Allocation behaviour at depth**: does dispersion-adaptive allocation diverge from the static
   pyramid further at 8K/16K (deeper non-monotone profiles), or converge to uniform? Directly
   extends the scale-trend and alloc-divergence analyses (fig_scale_trend / fig_alloc_divergence).
3. **History-only failure boundary**: single/multi-needle at L=8192/16384 — map where the entire
   history-only family's known 20%-budget failure stabilises or worsens; strengthens the
   diagnostics contribution (already a reviewer topic, prep doc §5).
4. **(Optional, cheap) fine rho grid at 4K**: rho ∈ {0.15, 0.25, 0.3} on 1.5B/3B to map the
   transition region between the established 0.1/0.2/0.3 points.

Explicitly deferred: Qwen2.5-7B. FP16 weights ≈ 15.2 GB vs 15.64 GB T4 HBM — no headroom for KV
cache and activations on the single-T4 deployment path the driver uses ("one T4, zero code
changes"); quantised or sharded runs would break the matched-entry protocol. Revisit only if a
dual-T4 sharding path is implemented and justified.

## 2. Design matrix

| Axis | Values | Notes |
|---|---|---|
| Models | Qwen2.5-1.5B-Instruct, Qwen2.5-3B-Instruct | established, fp16 fits T4 with KV headroom |
| Contexts | 8192; 16384 (stretch) | keep 2048/4096 anchors from the existing grids |
| Policies | full (8K only), h2o, pyramidkv, sage (default), sage-uniform | sage-uniform per dial-guide outcome on Qwen |
| rho | 8K: {0.05, 0.1, 0.2}; 16K: {0.1, 0.2} | budgets tighten at depth; 0.05@16K optional |
| PPL | WikiText-2, window=8192/16384, n_seqs reduced to hold token budget | driver takes window×n_seqs |
| Needle | L=8192: depths {0,25,50,75,100}×2 trials; L=16384: {0,50,100}×1 | same protocol as existing suite |
| Diagnostics | retention_per_layer, allocation shares, per-step accounting | unchanged assertions |

## 3. Feasibility estimates (to be revised by probe)
- KV cache/token (fp16): 1.5B ≈ 56 KiB (28 layers, 2 KV heads, 128 dim); 3B ≈ 72 KiB
  (36 layers). At 16K: ≈ 0.9 GB / 1.1 GB — well within T4 HBM next to 3–6 GB weights.
- Runtime: prefill attention grows ~quadratically in L; 16K vs 4K ≈ 16× per-sequence attention.
  Prior full grid: 0.63 h. Rough extension estimate: **4–8 h total** for the full matrix above,
  16K module ~60% of it. Kaggle weekly quota 30 h — fits with margin.
- Session limit: Kaggle max 12 h/session → run the 8K module first, checkpoint, then 16K.
  The driver's JSON-per-run output gives natural checkpointing.

## 4. Script changes (prepare locally, zero engine changes)
1. `gpu/driver.py`: add an `ext8k` model-spec block — PPL: window=8192, n_seqs=3 (≈24K tokens/run,
   comparable per-run token budget to 4K×10); needle lengths list as in §2. CLI flag rather than
   fork, so the "unmodified driver" claim in the cover letter stays intact.
2. Add full-cache reference at 8K (memory-checked) for the baseline row; skip at 16K if the probe
   shows <2 GB headroom.
3. Reuse `integrate_gpu_results.py` and `scripts/deep_analysis_cron.py` unchanged — the analysis
   pipeline is window-agnostic.

## 5. Pre-flight checklist (all must be ✅ before ANY accelerator start)
- [ ] User provides fresh `scripts/kaggle_api.json`.
- [ ] `ext8k` flag merged into `gpu/driver.py`, unit-walked on CPU with window=1024 stub.
- [ ] Kaggle quota ≥ 10 h remaining; session type T4 x2 (use one, keep second idle).
- [ ] Timing/memory probe run approved and its numbers substitute §3 estimates.
- [ ] Stop conditions written into the run header: abort if probe OOM; abort if step-2 PPL run
      exceeds 3× estimate; save-and-stop (never idle-hold) after each module.

## 6. Deliverables planned
- `results/gpu/ext8k/` JSONs (same schema), SUMMARY.md addendum, RQ7 → RQ7b table in the paper,
  updated scale-trend figure, accounting audit extended (expect zero violations; any violation
  is a **stop-the-line finding**, not a paper edit).
