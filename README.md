# SAGE-v2 — Research Artifact

Code, raw experiment logs, and figures for
**"SAGE-v2: Provably Budget-Consistent, Layer-Adaptive KV-Cache Eviction for
Memory-Efficient Long-Context Inference."**

> **Paper & journal-submission artifacts** (compiled PDF, title page, cover
> letter, submission LaTeX bundle) are published on the
> [Releases](../../releases) page — this repository intentionally contains
> research material only (code, data, figures, paper source).

This repository is the **complete v2 redo** of the earlier (rejected)
submission. The v1 state — whose experiment tables were self-consistent
*synthetic* records — is preserved for the record at git tag
[`v1.0-superseded`](../../tree/v1.0-superseded) and should not be used.

## What v2 fixes relative to v1 (all P0 review findings)

1. **Budget formula** — the original entropy-exponent allocation
   `b_l = clip(rho*t*(kappa_l/kbar)^tau, b_min*t, t)` violates its own global
   memory contract (Jensen gap: 97.4% of steps overshoot, +4.2% mean, up to
   +10.6%). It is replaced by the **capped water-filling projection**
   (Theorem 1), which hits the global budget *exactly* at every step. The
   original formula is retained in `evals/run_budget_sim.py` as the
   quantified negative control.
2. **Synthetic data** — every v1 table was script-generated and is discarded.
   Every number in the v2 paper is read from a raw JSON log under `results/`,
   and every table/figure is regenerated from those logs by
   `scripts/gen_tables.py` / `scripts/make_figures.py`.
3. **Protocol** — all methods (StreamingLLM, H2O, PyramidKV, reverse-pyramid
   control, SAGE ablations) run through the *same* exact-budget projector and
   cache manager at identical retained-entry counts (matched-entry protocol),
   with auxiliary memory reported separately.
4. **Scope honesty** — experiments are CPU-scale (2 cores, fp32): GPT-2-124M
   (MHA) and Qwen2.5-0.5B-Instruct (GQA), native context lengths, no
   FlashAttention score claims. No GPU throughput numbers are claimed.

## Repository layout

```
sage/                core library
  allocation.py        Theorem 1: capped water-filling (numpy, exact integers)
  policies.py          SAGE + ablations + StreamingLLM/H2O/PyramidKV baselines
  engine.py            chunked eager-attention engine, per-layer causal masks,
                       GQA, per-step accounting + budget assertions
evals/
  run_ppl.py           WikiText-2 perplexity (GPT-2 32x1024, Qwen 10x2048)
  run_needle.py        needle + multi-needle retrieval with retention diagnostics
  run_budget_sim.py    Theorem-1 verification + original-formula overshoot
  run_trace.py         per-layer budget/entropy allocation traces
tests/
  test_allocation.py   20,000 randomized exactness checks (all pass)
scripts/
  probe_engine.py      engine correctness gates (chunked == full, compliance)
  make_figures.py      regenerates all 6 figures from results/
  gen_tables.py        regenerates all 4 LaTeX table bodies from results/
  check_divergence.py  chunked-vs-full divergence debugging aid
  debug_chunk.py       single-chunk engine diagnostics
  diag_needle.py       needle retention diagnostics
  setup/               restricted-network environment bootstrap (see below)
results/              raw JSON: ppl/, needle/, budget_sim.json, alloc_trace.json
figures/              generated vector figures + LaTeX table bodies
paper/                LaTeX source of the paper (compile with Tectonic;
                      compiled PDF lives in the GitHub Release)
```

## Reproduce (CPU, ~6 h total on 2 cores)

```bash
# 1. environment (restricted-network variant in scripts/setup/):
#    HF_ENDPOINT=https://hf-mirror.com, models openai-community/gpt2 and
#    Qwen/Qwen2.5-0.5B-Instruct, WikiText-2 test parquet from Salesforce/wikitext
pip install torch transformers numpy matplotlib datasets huggingface_hub

# 2. correctness gates
python tests/test_allocation.py            # Theorem 1 unit gates
python scripts/probe_engine.py             # chunked == full forward, both models
python evals/run_budget_sim.py             # compliance simulation

# 3. experiments
python evals/run_ppl.py --model gpt2 --grid main
python evals/run_ppl.py --model gpt2 --grid sensitivity
python evals/run_ppl.py --model qwen05b --grid main
python evals/run_needle.py --lengths 2048 --depths 0,25,50,75,100 \
       --trials 2 --methods full,streamingllm,h2o,pyramidkv,sage
python evals/run_needle.py --lengths 4096 --depths 0,50,100 --trials 1 \
       --methods full,h2o,pyramidkv,sage
python evals/run_needle.py --lengths 2048,4096 --trials 1 \
       --methods full,h2o,pyramidkv,sage,sage-nodecay --multi
python evals/run_trace.py                  # allocation / kappa traces

# 4. paper artifacts
python scripts/make_figures.py             # figures from results/
python scripts/gen_tables.py               # table bodies from results/
cd paper && tectonic -X compile main.tex   # manuscript PDF
```

Every run is checkpointed (existing result JSONs are skipped) and asserts
`sum(|C_l|) == B_eff` after every compression step; a violation aborts the
run. Across the complete study the assertion never fired: **3,840 deployed
compression steps, zero violations.**

## Key results (all from `results/`)

| Quantity | Number |
|---|---|
| Original formula budget violations | 97.4% of steps (mean +4.2%, max +10.6%) |
| Corrected projection violations | **0** (3,840 deployed steps + 19,980 random instances) |
| GPT-2 PPL @ rho=0.2 (full = 32.41) | sage-nodecay **47.58** < h2o 49.63 < pyramidkv 50.77 < streamingllm 59.92 |
| Qwen2.5-0.5B PPL @ rho=0.2 (full = 13.37) | sage-uniform **16.40** < h2o 16.78 < pyramidkv 18.27 |
| Removing attention sinks (GPT-2) | PPL 4079 (84x degradation — sinks are existential) |
| Needle retention, mid-depth (Qwen) | SAGE 0.123 vs H2O 0.025 (~5x) |
| Multi-needle retrieval (Qwen, 4096) | SAGE 33% vs no-decay 0% |

## GPU replication protocol

The engine is hardware-agnostic PyTorch; to scale the study on A100/H100
(or free-tier T4/P100) hardware:

1. Replace model paths with LLaMA-3.1-8B-Instruct / Qwen2.5-7B-Instruct (GQA)
   and Mistral-7B (sliding-window aware); keep
   `attn_implementation="eager"` for exact score extraction, or implement the
   chunked score re-computation described in paper Section 4.4.
2. Extend contexts to 32K/128K (native windows only; no interpolation).
3. Add batched execution and wall-clock / peak-memory measurement under
   `torch.cuda.max_memory_allocated`; the accounting log already records
   per-chunk timings.
4. Replace the synthetic needle with RULER / LongBench under the identical
   matched-entry projector.
5. Keep the budget assertions on. Report violations (expected: zero).

## Environment

Reference stack: Python 3.12, torch 2.14.1+cpu, transformers 5.20.1,
numpy 2.2.4, matplotlib 3.9.2. `scripts/setup/` contains the exact
bootstrap used on a restricted network (`HF_ENDPOINT=https://hf-mirror.com`,
wheel pre-download with stall protection, ModelScope fallback for Qwen
weights) plus `dl_qwen.sh` / `download_models.py` for the model snapshots.
