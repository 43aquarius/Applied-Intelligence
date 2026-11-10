# ext8k run notes (2026-11-10, kernel v2)

## Postmortem: kernel v1 (137 s) vs v2 (2,514 s)

v1 OOM'd all three models at the memprobe gate in 137 s. Root cause: the v1
probe executed a MONOLITHIC full-window forward, materializing [1,H,L,L]
fp32 attention — 3.00 / 4.00 / 12.00 GiB at 8K / 8K / 16K — a path no
experiment phase executes. All PPL/needle phases run through the engine's
chunked path (chunk=64, attention footprint [1,H,chunk,cache+chunk]). v2
probes the real worst case instead (one chunked no-compression pass at
rho=1.0) and keeps the monolithic forward as a non-fatal feasibility record.
Fix commit: 0ccc78f (GPU driver only; engine/policies untouched).

## Results (v2, driver clock 2,514 s)

Design matrix outcome: 1.5B@8K full grid ✓; 1.5B@16K stretch ✓;
3B@8K ✗ memprobe OOM (guarded skip, 24 MiB short with 14.20 GiB
allocated — a genuine capacity limit of fp32 3B + full-cache chunked probe
on T4 15.6 GB, not fragmentation; negative result is final for this
protocol/hardware combo, consistent with the 7B-delay rationale).

### PPL (WikiText-2, matched-entry fp32, rho=0.2 unless noted)

| config | full | sage-uniform | sage | h2o | pyramidkv |
|---|---|---|---|---|---|
| 1.5B@8K  | 7.949 | **8.661** | 8.716 | 9.287 | 9.775 |
| 1.5B@16K | 7.863 | **8.373** | 8.417 | 9.415 | 9.899 |

Budget curves @8K (1.5B): h2o {0.05: 10.831, 0.1: 9.947, 0.2: 9.287};
pyramidkv {0.05: 11.423, 0.1: 10.584, 0.2: 9.775}; sage {0.05: 10.061,
0.1: 9.249, 0.2: 8.716}. The SAGE-family advantage over h2o/pyramidkv
persists at 8K and 16K; sage-uniform is best-in-class at both windows.

### Needle (mean hit-rate / mean retention)

| config | method | single | multi |
|---|---|---|---|
| 1.5B@8K  | sage | 0.20 / **0.242** | **0.333** / **0.320** |
| 1.5B@8K  | h2o | 0.40 / 0.023 | 0.000 / 0.022 |
| 1.5B@8K  | pyramidkv | 0.20 / 0.036 | 0.000 / 0.036 |
| 1.5B@16K | sage | 0.333 / **0.369** | — |
| 1.5B@16K | h2o | 0.667 / 0.040 | — |
| 1.5B@16K | pyramidkv | 0.000 / 0.042 | — |
| (full = 1.000 everywhere; streamingllm: 0.20@8K, 0.333@16K) | | | |

sage keeps by far the highest retention among compressed methods and is
the only compressed method that hits anything on multi-needle@8K.

## First non-zero budget-violation counts in project history

`sage` (adaptive dispersion dial), rho=0.2: **4 violations @8K, 57 @16K**.
All other policies (sage-uniform, h2o, pyramidkv): 0 at both windows.
All released 4K grids and the CPU study: 0 everywhere.

Pattern (from accounting.json step records):

- All violations in the LATE regime — none before t=5888 in either window
  (8K: 4/4 late; 16K: 4 in first half, 53 in second half).
- ALL diffs NEGATIVE: total_retained < nominal_budget — under-retention,
  never over-retention.
- Magnitude grows with t: 8K max |diff|=13; 16K max |diff|=100
  (histogram: -2,-1,-4,-13 @8K; up to -100 @16K).
- sage-uniform is integer-exact by construction at every depth; h2o and
  pyramidkv (per-layer independent quotas) likewise.

Reading: the adaptive dial's deep-window integer allocation loses
exactness (under-allocation). Theorem 1's guarantee holds on the uniform
path; the dispersion path has a deep-window edge case. This does NOT
affect the released 4K results (0 violations there, verified) but it
strengthens the dial-guide deployment recommendation (sage-uniform:
best PPL at both new windows AND contract-exact). Next step: source-level
audit of the dispersion budget computation (largest-remainder residual
handling) to localize the off-by-small deficit; candidate fix belongs in
sage/policies.py, not the driver.

## memprobe v2 records

- 1.5B@8K: chunked peak 8.77 GB; monolithic forward feasible (13.94 GB).
- 1.5B@16K: chunked peak 11.24 GB; monolithic INFEASIBLE (requested
  12 GiB — the exact number that killed v1). The chunked online protocol
  is what makes 16K fp32 executable on T4; the monolithic path is not.
  Usable as limitation-section evidence.

## Paper impact (pending)

- RQ7b extension table: 8K/16K rows (1.5B), sage-uniform headline.
- Limitation: 3B@8K fp32 capacity ceiling on T4; monolithic-vs-chunked
  feasibility contrast.
- Dial-guide reinforcement + the violations finding (report honestly;
  characterize as adaptive-dial deep-window under-allocation, fixable in
  policy code, orthogonal to the engine-level contract).
