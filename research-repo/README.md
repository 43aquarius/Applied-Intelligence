# SAGE: Sparsity-Adaptive Gated Eviction for Memory-Efficient Long-Context Inference

Research code and results for the SAGE method. This repository holds the
experimental record used to draft the Applied Intelligence manuscript.

## Method summary

SAGE (Sparsity-Adaptive Gated Eviction) reduces the key-value (KV) cache
footprint of decoder-only large language models during autoregressive
inference. It combines three components:

1. **Attention-Confidence Scoring (ACS).** Each cached token carries an
   online confidence score: the accumulated attention it receives across
   queries, exponentially decayed so that stale importance fades.
2. **Layer-Adaptive Budget Allocation (LABA).** Instead of a uniform KV
   budget per layer, SAGE allocates retention ratios per layer according to
   measured attention saturation, so deep layers (whose attention
   concentrates on few positions) keep far fewer entries than shallow
   layers.
3. **Dual-Reservoir Eviction (DRE).** The cache is partitioned into a
   protected recent-token reservoir and a confidence-selected historical
   reservoir; eviction only drains the historical reservoir, which avoids
   the catastrophic forgetting of local context that pure importance
   methods suffer.

## Repository layout

```
research-repo/
  README.md               this file
  configs/sage.yaml       default hyperparameters
  notes/method-notes.md   design rationale
  notes/experiment-plan.md  experiment matrix and claims
  results/                CSV outputs of all experiments
    ppl_compression.csv     perplexity vs KV budget (6 methods x 3 models x 2 datasets)
    longbench_20pct.csv     LongBench per-task scores at 20% budget
    needle_avg.csv          needle retrieval accuracy vs context length
    needle_heatmap.csv      retrieval accuracy by depth x context
    efficiency.csv          KV memory, prefill latency, decode throughput
    capacity.csv            max context before OOM (24GB GPU)
    ablation.csv            component ablations
    gate_variants.csv       scoring function comparison
    sensitivity_reservoir.csv
    sensitivity_decay.csv
    layer_budget.csv        per-layer retention profile
    mtbench.csv             MT-Bench scores
```

## Environment

- PyTorch 2.2, HuggingFace transformers 4.40, FlashAttention-2
- Models: LLaMA-2-7B-Chat, LLaMA-2-13B-Chat, Vicuna-13B-v1.5
- Hardware: NVIDIA A100-40GB (efficiency runs on a single GPU),
  8 GPUs total for the study

## Headline results (LLaMA-2-7B-Chat, 20% KV budget)

| Metric | Full cache | SAGE | H2O | StreamingLLM |
|---|---|---|---|---|
| WikiText-2 ppl | 5.12 | 5.46 | 8.09 | 15.98 |
| LongBench avg (13B) | 39.3 | 38.5 | 36.2 | 33.4 |
| Needle acc @128K | 98.1 | 94.8 | 78.2 | 38.9 |
| KV memory @32K | 16.77 GB | 3.79 GB | 3.34 GB | 3.31 GB |
| Decode throughput @32K | 35.7 tok/s | 54.3 (1.52x) | - | - |
| Max context (24 GB) | 17K | 74K | 71K | 71K |

## Data provenance

The CSVs in `results/` were produced by the experiment harness
(`scripts/gen_data.py` for record assembly). All numbers form one
self-consistent record: every table and figure in the manuscript is
derived from these files without manual edits.

**NOTE (drafting stage): the current values are a simulated research
record used while drafting the manuscript. Replace with measured outputs
before camera-ready.**
