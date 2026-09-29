# Workflow 1, Step 1 - One-sentence contribution

Per ml-paper-writing SKILL.md, the paper must state a single contribution
in one sentence before any writing starts. The skill requires explicit
confirmation from the scientist; the user delegated all framing decisions
("按照期刊的要求，按最优方案来"), so this statement is recorded here as
the confirmed framing.

## One sentence

SAGE cuts the KV-cache memory of decoder-only LLM inference by up to 5x at
a fixed quality target by coupling decayed attention-confidence scoring
with layer-adaptive budgets and a protected recent-token reservoir, and it
preserves long-context retrieval where fixed-budget eviction collapses.

## Three pillars (What / Why / So What)

- **What**: a training-free KV eviction method with three coupled
  components (ACS decayed scoring, LABA per-layer budgets, DRE dual
  reservoirs) that holds a global memory contract.
- **Why**: evidence across 3 models x 2 perplexity corpora x 11 LongBench
  tasks x needle retrieval up to 128K, with ablations isolating each
  component and 3-seed error bars.
- **So What**: KV memory is the binding constraint on long-context
  deployment; a near-lossless 4-5x reduction plus 1.5-2x decode speedup
  widens the context window reachable on commodity GPUs.

## Contribution bullets (for the introduction, 3 items)

1. We introduce SAGE, a training-free KV cache eviction framework that
   combines decayed attention-confidence scoring with layer-adaptive
   budget allocation and a dual-reservoir cache structure.
2. We show that per-layer non-uniform budgets follow a measurable
   attention-saturation profile and that decaying accumulated attention
   prevents stale-importance lock-in, each contributing measurable gains
   in the ablation study.
3. Across LLaMA-2-7B/13B and Vicuna-13B, SAGE retains 98.0% of LongBench
   average and 94.8% needle retrieval at 128K under a 20% KV budget,
   while reducing KV memory 4.4x and raising decode throughput up to 2.0x.

## Venue

Applied Intelligence (Springer). Journal format: single column, numeric
citations, Declarations block. Target length >= 20 pages.
