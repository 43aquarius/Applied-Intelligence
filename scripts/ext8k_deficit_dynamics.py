#!/usr/bin/env python3
"""Task 21: ext8k under-retention deficit dynamics — rebuttal-grade figure + stats.

Data: repo/results/gpu/ext8k/ppl/*.accounting.json (per-step aggregated).
Mechanism context (Task 18 audit): deficit = budget jump (delta_w * B(t)) outruns
the fixed 64-entries-per-chunk cache refill; one-sided (under, never over);
self-healing at up to 64 entries/step.

Outputs:
  download/SAGE-v2/analysis_notes/fig_ext8k_deficit.png   (2-panel figure)
  stdout: markdown stats table (goes into the analysis note)
"""
import json, os

import os
HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(HERE)  # repo root
OUT = os.path.join(REPO, "analysis", "fig_ext8k_deficit.png")

FILES = {
    "8K adaptive":   "results/gpu/ext8k/ppl/qwen15b-ext8k__sage__r0.2__gNone__tNone.accounting.json",
    "16K adaptive":  "results/gpu/ext8k/ppl/qwen15b-ext16k__sage__r0.2__gNone__tNone.accounting.json",
    "16K uniform":   "results/gpu/ext8k/ppl/qwen15b-ext16k__sage-uniform__r0.2__gNone__tNone.accounting.json",
    "16K h2o":       "results/gpu/ext8k/ppl/qwen15b-ext16k__h2o__r0.2__gNone__tNone.accounting.json",
    "16K pyramidkv": "results/gpu/ext8k/ppl/qwen15b-ext16k__pyramidkv__r0.2__gNone__tNone.accounting.json",
}

series = {}
meta = {}
for name, rel in FILES.items():
    d = json.load(open(os.path.join(REPO, rel)))
    ts = [s["t"] for s in d["steps"]]
    defs = [s["nominal_budget"] - s["total_retained"] for s in d["steps"]]
    nom = [s["nominal_budget"] for s in d["steps"]]
    series[name] = (ts, defs, nom)
    deficit_steps = [(t, x) for t, x, n in zip(ts, defs, nom) if x != 0]
    meta[name] = dict(
        n_steps=len(ts),
        violations=d["budget_violations"],
        deficit_steps=len(deficit_steps),
        onset=deficit_steps[0][0] if deficit_steps else None,
        max_def=max((x for _, x in deficit_steps), default=0),
        rel=[(x / n) for x, n in zip(defs, nom) if x != 0],
    )

# ---------- markdown stats ----------
lines = []
lines.append("| policy | steps | deficit steps | onset t | max deficit | max deficit / nominal |")
lines.append("|---|---|---|---|---|---|")
for name, m in meta.items():
    md = f"{m['max_def']}"
    onset = f"{m['onset']}" if m["onset"] else "--"
    rel = f"{max(m['rel'])*100:.3f}%" if m["rel"] else "--"
    lines.append(f"| {name} | {m['n_steps']} | {m['deficit_steps']} | {onset} | {md} | {rel} |")
print("\n".join(lines))

# mechanism quantities
for w, L in [("8K", 8192), ("16K", 16384)]:
    d = json.load(open(os.path.join(REPO, FILES[f"{w} adaptive"])))
    slope = d["rho"] * d["n_layers"]
    print(f"\n{w}: n_layers={d['n_layers']}, rho={d['rho']}, mean budget slope B'(t)={slope:.1f} entries/step "
          f"(refill=64/step); B(t_onset)={int(slope*5888)}")

# deficit episode structure (16K): episodes = maximal runs of consecutive deficit steps
ts, defs, nom = series["16K adaptive"]
episodes, cur = [], None
for t, x in zip(ts, defs):
    if x > 0:
        if cur is None:
            cur = [t, t, x, x]
        else:
            cur[1] = t
            cur[3] = max(cur[3], x)
    else:
        if cur is not None:
            episodes.append(cur)
            cur = None
if cur is not None:
    episodes.append(cur)
print(f"\n16K deficit episodes: {len(episodes)}")
for i, (t0, t1, first, mx) in enumerate(episodes[:12], 1):
    dur = (t1 - t0) // 64 + 1
    print(f"  ep{i:2d}: t {t0:>6}-{t1:>6}  steps={dur:>2}  max={mx}")

# ---------- figure ----------
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

fig, axes = plt.subplots(1, 2, figsize=(10.5, 4.0), constrained_layout=True, sharey=False)

# Panel A: absolute deficit dynamics (adaptive vs controls)
ax = axes[0]
for name, color, lw in [("16K adaptive", "#c0392b", 1.8), ("8K adaptive", "#e67e22", 1.5),
                         ("16K uniform", "#2980b9", 1.0), ("16K h2o", "#7f8c8d", 0.9),
                         ("16K pyramidkv", "#95a5a6", 0.9)]:
    ts, defs, _ = series[name]
    lbl = name if "adaptive" in name else f"{name} (all zero)"
    ax.plot(ts, defs, color=color, lw=lw, label=lbl)
ax.axvline(5888, color="k", ls=":", lw=0.9)
ax.annotate("onset t=5,888", xy=(5888, 88), xytext=(7000, 88), fontsize=8.5,
            arrowprops=dict(arrowstyle="->", lw=0.7))
ax.annotate("max 100 (0.11% of nominal)", xy=(16384, 100), xytext=(10300, 96), fontsize=8.5,
            arrowprops=dict(arrowstyle="->", lw=0.7))
ax.set_xlabel("decode position t (chunked prefill, 64-token chunks)")
ax.set_ylabel("under-retention deficit = nominal − retained (entries)")
ax.set_title("(a) Adaptive dial: one-sided, bounded, deep-window only", fontsize=10)
ax.legend(fontsize=7.5, loc="upper left", framealpha=0.9)
ax.set_xlim(0, 16600)
ax.set_ylim(-4, 112)

# Panel B: relative deficit on log-ish scale + budget slope context
ax = axes[1]
for name, color, lw in [("16K adaptive", "#c0392b", 1.8), ("8K adaptive", "#e67e22", 1.5)]:
    ts, defs, nom = series[name]
    rel = [x / n * 100 for x, n in zip(defs, nom)]
    ax.plot(ts, rel, color=color, lw=lw, label=name)
ax.axvline(5888, color="k", ls=":", lw=0.9)
ax.set_xlabel("decode position t")
ax.set_ylabel("deficit / nominal budget (%)")
ax.set_title("(b) Relative magnitude stays below 0.11% (16K) / 0.03% (8K)", fontsize=10)
ax.legend(fontsize=8, loc="upper left", framealpha=0.9)
ax.set_xlim(0, 16600)
ax.set_ylim(-0.005, 0.13)

fig.suptitle("Deep-window under-retention of the adaptive dial (Qwen2.5-1.5B, rho=0.2, matched-entry fp32, T4)",
             fontsize=10.5)
fig.savefig(OUT, dpi=200)
print("\nFIGURE:", OUT)

# non-blank check
from PIL import Image
im = Image.open(OUT).convert("L")
px = list(im.getdata())
ratio = sum(1 for p in px if p < 240) / len(px)
print(f"non-white ratio: {ratio:.3f}", "OK" if ratio > 0.01 else "BLANK?")
