# SAGE design notes

## Motivation

Autoregressive decoding of decoder-only LLMs keeps a KV entry for every
past token. At 32K tokens a 7B model already spends ~16.8 GB on the cache;
the footprint scales linearly and quickly dominates device memory. Existing
KV eviction methods (H2O, ScissorHands, TOVA) keep a fixed fraction of
entries chosen by an importance heuristic, but they share three problems
we observed in preliminary studies:

1. **Uniform budgets.** The same retention ratio is applied to every layer,
   although attention maps in deep layers concentrate on far fewer
   positions than in shallow layers. Uniform budgets over-keep in deep
   layers and under-keep in shallow layers at the same total cost.
2. **Stale importance.** Accumulated-attention scores never decay, so a
   token that was heavily attended early keeps its slot forever even after
   the discussion moved on.
3. **No protected recency.** Pure importance eviction can drop the most
   recent tokens, and local attention patterns (induction heads, positional
   locality) then break, which shows up as retrieval collapse on long
   contexts.

## Design decisions

- **Decayed accumulated attention** (ACS). Score s_i <- lambda * s_i +
  a_t(i) each step, where a_t(i) is the attention received by token i at
  step t. lambda in [0.95, 0.99] works best; lambda = 1 recovers static
  accumulation (H2O-style scoring) and degrades (see
  gate_variants.csv).
- **Per-layer saturation signal.** Layer l's budget is proportional to its
  attention-entropy ratio: layers whose query attention is peaked need
  few entries. The scheduler runs online, every K = 512 steps, and
  respects a global memory contract B.
- **Reservoir split.** Cache = recent window (size r, protected) +
  historical set (budget-controlled, evicted by lowest confidence).
  r = 32 tokens is the sweet spot; larger r wastes budget, smaller r
  hurts local coherence (sensitivity_reservoir.csv).
- **Complexity.** Scoring is O(1) per cached entry per step (streaming
  accumulation). Eviction runs only when a layer exceeds its budget:
  a bucketed min-heap gives O(log n) amortized. Gate memory is O(n) floats
  per layer, 2.5% of the KV bytes it controls.

## What we claim (and do not)

We claim near-lossless quality at aggressive budgets on the evaluated
7B/13B chat models, plus throughput gains from shorter attention sweeps.
We do not claim training-free quantization-level compression (KIVI is
orthogonal and can be combined), nor any training/finetuning of the model.
