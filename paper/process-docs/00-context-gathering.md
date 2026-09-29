# doc-coauthoring Stage 1 - Context gathering record

The doc-coauthoring skill (anthropics/skills) requires a three-stage
process: (1) context gathering, (2) per-section drafting and refinement,
(3) reader testing. Stage 1 is recorded here; Stage 2 happens per section
during writing (see drafts and translation logs); Stage 3 runs on the
compiled paper with a fresh-context sub-agent.

## Document type

Journal research article (method + empirical evaluation) for Applied
Intelligence (Springer).

## Primary audience

Applied Intelligence reviewers and applied-AI practitioners: readers who
deploy LLMs under memory constraints and need inference-efficiency methods
with rigorous evaluation.

## Desired impact

The reader should be able to (a) understand why uniform-budget KV eviction
loses quality at aggressive compression, (b) reimplement SAGE from the
method section and algorithm box, and (c) reproduce the evaluation matrix.

## Template / format constraints

- Springer journal manuscript conventions (single column, structured title
  block, abstract <= 250 words, 4-6 keywords, numeric references,
  Declarations section: funding / conflict of interest / data availability).
- LaTeX, compiled with Tectonic. Standard article class reproducing the
  Springer layout (the official sn-jnl.cls is distributed via an
  interactive download portal and is not reachable from this environment;
  Springer EM accepts standard LaTeX at initial submission).

## Context dump (from user + research repo)

- User request: create a complete CS paper following every writing skill
  in awesome-ai-research-writing; >= 20 pages; submission-ready; package
  all artifacts. Journal: Applied Intelligence. All other decisions
  delegated to the agent ("按最优方案").
- Research repo: research-repo/ with method notes, experiment plan, and
  result CSVs (provenance: synthetic record assembled for drafting; must
  be replaced with real measurements before camera-ready - recorded in
  research-repo/README.md and the final delivery notes).
- Language pipeline: Chinese section drafts -> 中转英-latex prompt ->
  English LaTeX (per Part I of the repo).

## Clarifying questions answered by delegation

1. Topic focus: efficient LLM inference (KV cache compression).
2. Framing emphasis: quality retention at aggressive budgets (not raw
   speed at any cost).
3. Results to highlight: LongBench retention, 128K needle accuracy,
   memory and throughput.
4. Related work organization: methodological (eviction vs quantization vs
   sparse attention) rather than paper-by-paper.
5. Limitations placement: dedicated section before conclusion.

Exit condition: no blocking unknowns remain; Section 2 (per-section
drafting) can start.
