# Related-Work Scan — 2026-11-10 (second scan, noon)

Scope: arXiv KV-cache eviction / long-context inference papers published or surfaced since the
morning scan (Task 11, which added EchoKV and "The Gating Mechanism" to the watchlist).
Method: web search + each paper read on its arXiv abstract page (verification date 2026-11-10).

## New papers found (3)

### 1. WakeKV — arXiv:2610.02713 (Ranjan, 2 Oct 2026)
- **What it does**: reactive, reversible residency for attention heads. Measures that most heads
  change their reading behaviour at least once during generation; instead of freezing a head
  classification taken at prefill, cooling heads are moved to a recoverable CPU reservoir and can
  be woken. Evaluated on 1.5B–8B models across needle retrieval, long CoT, and multi-turn recall;
  FlexiCache/vLLM implementation on Mistral-7B.
- **S positioning**: orthogonal axis — head-level *dynamics during decoding*, not layer-wise
  budget allocation; **no exact integer budget contract** (matched memory is the experimental
  control, not an enforced per-step mechanism guarantee).
- **Action**: watchlist only. No change to sec2 positioning sentence. If cited later, cite as
  evidence that static post-prefill characterisations are insufficient — consistent with SAGE's
  *online* (every-decoding-step) refresh story.

### 2. TideKV — arXiv:2610.24499 (Wang et al., 17 Oct 2026)
- **What it does**: layer-major delayed eviction during chunked prefill. Processes all prompt
  chunks within each Transformer layer, retains full-prompt KV only for the active layer, evicts
  at layer end; preserves full-prompt-aware selection while cutting the construction-time
  transient footprint (−83.89% at 64K on A100; enables 128K prefill on RTX 4090 / Jetson).
- **S positioning**: attacks the **prefill transient**, not the decoding-time realised budget.
  Complementary: the TideKV schedule can wrap any post-prefill policy, including SAGE.
  **No exact integer budget contract.**
- **Action**: watchlist only.

### 3. Risk-Controlled KV-Cache Eviction: From Memory Budgets to Risk Targets — arXiv:2609.27981
(Kang, Yun, Kim, Seo, 23 Sep 2026)
- **What it does**: reformulates eviction as deployment risk control. Defines material
  degradation per request (utility drop beyond tolerance vs full-KV), deployment risk = population
  frequency of such events; a compressor-agnostic post-hoc certification procedure with
  finite-sample guarantee selects a retention policy from calibration data, falling back to full
  KV when nothing certifies. Empirically: certifies SnapKV at 75% retention on LongBench but no
  policy on RULER-32K (Llama).
- **S positioning**: this is a **certification layer over mechanisms, not a mechanism** — it does
  not enforce the realised cache size inside the compressor; it certifies policies post hoc.
  **No exact integer budget contract.** Notably *complementary and mutually reinforcing*: SAGE's
  auditable exact contract (zero violations at 2,112 audited steps) makes it a well-posed
  candidate policy under exactly this kind of certification — a candidate answer if a reviewer
  asks "why does mechanism-level exactness matter?" (deployment-level certificates presuppose a
  compressor whose realised budget is known exactly).
- **Action**: watchlist; also added to Reviewer_Response_Preparation watchlist (now 9 entries).

## Re-confirmed
- LaProx (2605.07234) v2: "Accepted to NeurIPS 2026" — already reflected in references.bib note
  (Task 11) and verified rendered in the v2.2 PDF reference [17].

## Net effect on the manuscript
- Section 2 closing positioning statement ("none of the recent adjacent work enforces the realised
  global budget as an exact integer contract") **remains valid against all three new papers**.
- No bib/related-work edit required this round; the three entries live in the reviewer-prep
  watchlist (submission working doc) to keep the manuscript's 28-reference list stable.
- Decision recorded: if a revision round opens (reviewer comments), WakeKV/TideKV/
  Risk-Controlled are the first candidates to cite in a short "2026 addition" sentence.

## Companion artifacts updated this round
- `submission/Reviewer_Response_Preparation.docx` (+ PDF): watchlist 6 → 9 entries.
- `submission/Cover_Letter.docx` (+ PDF): dual-scale RQ7 quantification sentence added
  (10.30/10.42 @1.5B, 9.19/9.28 @3B vs H2O 10.50/9.36, PyramidKV 11.36/10.55; 34 runs,
  zero violations) — mirrors the Release-v2.2 Cover_Letter.md wording; all eight numbers
  re-verified against `results/gpu/SUMMARY.md` (10.302/10.419/9.188/9.278/10.505/9.360/11.356/10.548).
