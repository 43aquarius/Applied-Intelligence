# Experiment plan

Each experiment is tied to one claim. Claims C1-C3 mirror the contribution
list drafted for the manuscript.

- C1 (quality): SAGE keeps language quality and long-context task scores
  near the full cache at 10-50% budgets, outperforming uniform-budget
  eviction baselines.
- C2 (retrieval): protected recency + decayed confidence preserves
  needle-in-a-haystack retrieval at 128K, where window methods collapse.
- C3 (efficiency): the memory contract translates into 4-5x KV reduction,
  1.5-2x decode throughput at long contexts, at <=6% prefill overhead.

## Matrix

E1 Main quality: WikiText-2 + PG19 perplexity, budgets {0.1, 0.2, 0.5, 1.0},
   methods {SAGE, TOVA, FastGen, ScissorHands, H2O, StreamingLLM},
   models {LLaMA-2-7B-Chat, LLaMA-2-13B-Chat, Vicuna-13B-v1.5}.
   3 seeds {42, 123, 2024}; report mean and std. -> ppl_compression.csv

E2 Long-context tasks: LongBench (11 tasks) at 20% budget, 13B. -> longbench_20pct.csv

E3 Retrieval: needle-in-a-haystack, contexts 8K-128K, 4 depth bins,
   13B @ 20% budget. -> needle_avg.csv, needle_heatmap.csv

E4 Efficiency: KV memory, prefill latency, decode throughput vs context
   4K-128K, 7B/13B, A100-40GB, batch 1. -> efficiency.csv
   Capacity: max context on 24GB card. -> capacity.csv

E5 Ablations: remove LABA / DRE / decay / scheduler. -> ablation.csv
   Gate variants: ACS vs static vs entropy vs L2 vs recency vs random.
   -> gate_variants.csv

E6 Sensitivity: reservoir r in {8..128}; decay lambda in {0.90..1.00}.
   -> sensitivity_*.csv

E7 Layer profile: per-layer retention under a 20% global contract.
   -> layer_budget.csv

E8 Generation quality: MT-Bench (LLM judge), 13B @ 20%. -> mtbench.csv

## Baseline configuration

All baselines use the budget definitions of their papers: H2O heavy-hitter
ratio 0.2 (plus 4 recent), ScissorHands persistence-of-importance,
StreamingLLM sink 4 + window, TOVA greedy tovar score, FastGen profiling
per head. Tuning grids for baselines are listed in the appendix of the
paper; we tuned baselines with the same GPU budget as SAGE.

## Compute

8 x A100-40GB, ~420 GPU-hours total (E1-E8 including baseline tuning).
