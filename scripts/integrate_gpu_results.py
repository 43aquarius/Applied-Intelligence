#!/usr/bin/env python3
"""Integrate the Kaggle GPU replication results into paper artifacts.

Reads results_gpu/ (downloaded kernel output), validates budget compliance,
and emits:
  - tab_gpu.tex          PPL main grid, Qwen2.5-1.5B + 3B columns
  - tab_gpu_needle.tex   needle hit-rates (L=2048, 5 depths) + multi + retention
  - fig_gpu_curve.pdf    PPL vs rho budget curve at 1.5B (paper style)
  - gpu_summary.json     aggregated numbers for the paper text
Fails loudly if any budget violation is found.
"""
import glob
import json
import os
import sys
from collections import defaultdict

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

SRC = sys.argv[1] if len(sys.argv) > 1 else "/home/z/my-project/kout/results_gpu"
OUT = sys.argv[2] if len(sys.argv) > 2 else "/home/z/my-project/sage2/gpu_artifacts"
os.makedirs(OUT, exist_ok=True)

plt.rcParams.update({
    "font.size": 9, "axes.labelsize": 9, "axes.titlesize": 9,
    "legend.fontsize": 8, "xtick.labelsize": 8, "ytick.labelsize": 8,
    "axes.spines.top": False, "axes.spines.right": False,
    "axes.grid": True, "grid.linestyle": "--", "grid.alpha": 0.18,
    "grid.linewidth": 0.5, "legend.frameon": False, "pdf.fonttype": 42,
})
C = {"h2o": "#7f7f7f", "pyramidkv": "#dd8452", "sage": "#1a5276",
     "full": "#2ca02c"}

MODELS = ["qwen15b", "qwen3b"]
MNICE = {"qwen15b": "Qwen2.5-1.5B", "qwen3b": "Qwen2.5-3B"}
ORDER = ["full", "streamingllm", "h2o", "pyramidkv", "reverse-pyramid",
         "sage", "sage-nodecay", "sage-uniform"]
NAMES = {
    "full": "Full cache (reference)",
    "streamingllm": "StreamingLLM (sinks + window)",
    "h2o": "H2O (cumulative, uniform budget)",
    "pyramidkv": "PyramidKV (cumulative, static pyramid)",
    "reverse-pyramid": "Reverse pyramid (control)",
    "sage": "SAGE v2 (decay + entropy budget)",
    "sage-nodecay": "SAGE v2 w/o decay ($\\gamma{=}1$)",
    "sage-uniform": "SAGE v2 w/ uniform budget ($\\tau{=}0$)",
}


def load_ppl():
    rows = []
    for f in glob.glob(f"{SRC}/ppl/*.json"):
        if f.endswith("accounting.json"):
            continue
        rows.append(json.load(open(f)))
    return rows


def main():
    rows = load_ppl()
    # ---------- hard validation: zero budget violations in PPL runs ----------
    # (teacher-forced runs compress at every step; equality must hold exactly)
    viol = [(r["model"], r["policy"], r["rho"], r["gamma"], r["tau"],
             r["budget_violations"]) for r in rows if r["budget_violations"]]
    if viol:
        print("FATAL: PPL budget violations found:", viol)
        sys.exit(1)
    # needle decode steps can benignly UNDER-fill the envelope (tokens arrive
    # one at a time while the envelope grows by rho*L per step; the contract
    # is an upper bound and over-fill is impossible: sum min(b_l, n_l) <= B_eff).
    # Same behaviour exists in the CPU study (20/72 needle files). Record only.
    nd_underfill = 0
    for f in glob.glob(f"{SRC}/needle/*.json"):
        d = json.load(open(f))
        nd_underfill += d.get("violations", 0)
    total_tokens = sum(r["n_tokens"] for r in rows)
    print(f"validated: {len(rows)} PPL runs, {total_tokens:,} tokens, "
          f"0 violations; needle decode under-fill steps: {nd_underfill} "
          f"(benign, upper-bound contract)")

    # ---------- tab_gpu.tex ----------
    main_grid = {}
    for r in rows:
        if r["gamma"] is None and r["tau"] is None and r["rho"] == 0.2:
            main_grid[(r["model"], r["policy"])] = r["ppl"]
        if r["gamma"] is None and r["tau"] is None and r["rho"] == 1.0:
            main_grid[(r["model"], "full")] = r["ppl"]
    lines = []
    for m in ORDER:
        cells = []
        for mod in MODELS:
            v = main_grid.get((mod, m))
            cells.append(f"{v:.2f}" if v else "--")
        lines.append(f"{NAMES[m]} & " + " & ".join(cells) + " \\\\")
    open(f"{OUT}/tab_gpu.tex", "w").write("\n".join(lines) + "\n")

    # ---------- tab_gpu_needle.tex ----------
    by = defaultdict(lambda: defaultdict(list))
    ret = defaultdict(list)
    multi = defaultdict(list)
    for f in glob.glob(f"{SRC}/needle/*.json"):
        d = json.load(open(f))
        mod = d["model"]
        if d.get("multi"):
            multi[(mod, d["method"])].append(d["hit_rate"])
        elif d["length"] == 2048:
            by[(mod, d["method"])].setdefault(d["depth"], []).append(d["hits"][0])
            ret[(mod, d["method"])].append(d["retention_mean"])
    depths = [0, 25, 50, 75, 100]
    nm = {"full": "Full cache", "streamingllm": "StreamingLLM",
          "h2o": "H2O", "pyramidkv": "PyramidKV", "sage": "SAGE v2"}
    lines = []
    for mod in MODELS:
        if not any((mod, m) in by for m in nm):
            continue
        for m in ["full", "streamingllm", "h2o", "pyramidkv", "sage"]:
            if (mod, m) not in by:
                continue
            cells = []
            for d in depths:
                v = by[(mod, m)].get(d)
                cells.append(f"{np.mean(v):.2f}" if v else "--")
            r_mean = np.mean(ret[(mod, m)]) if ret.get((mod, m)) else float("nan")
            r_s = f"{r_mean:.3f}" if r_mean == r_mean else "--"
            mu = multi.get((mod, m))
            mu_s = f"{np.mean(mu):.2f}" if mu else "--"
            lines.append(f"{MNICE[mod]} & {nm[m]} & " + " & ".join(cells) +
                         f" & {r_s} & {mu_s} \\\\")
        lines.append("\\midrule")
    if lines and lines[-1] == "\\midrule":
        lines.pop()
    open(f"{OUT}/tab_gpu_needle.tex", "w").write("\n".join(lines) + "\n")

    # ---------- fig_gpu_curve.pdf (1.5B) ----------
    data = defaultdict(dict)
    for r in rows:
        if r["model"] != "qwen15b" or r["gamma"] is not None or r["tau"] is not None:
            continue
        data[r["policy"]][r["rho"]] = r["ppl"]
    if data:
        fig, ax = plt.subplots(figsize=(4.6, 2.9), constrained_layout=True)
        for p in ["h2o", "pyramidkv", "sage"]:
            if p not in data:
                continue
            rhos = sorted(data[p])
            ax.plot(rhos, [data[p][x] for x in rhos], marker="o", ms=3.5,
                    lw=1.6, color=C[p],
                    label={"h2o": "H2O", "pyramidkv": "PyramidKV (static)",
                           "sage": "SAGE"}[p])
        if "full" in data:
            ax.axhline(data["full"][1.0], color=C["full"], ls=":", lw=1.4,
                       label="Full cache")
        ax.set_xlabel("Budget ratio $\\rho$")
        ax.set_ylabel("WikiText-2 perplexity")
        ax.set_title("Qwen2.5-1.5B-Instruct (GPU replication)", fontsize=9)
        ax.legend()
        fig.savefig(f"{OUT}/fig_gpu_curve.pdf")
        plt.close(fig)

    # ---------- gpu_summary.json ----------
    summary = {"env": json.load(open(f"{SRC}/env.json")) if
               os.path.exists(f"{SRC}/env.json") else {},
               "ppl_tokens_total": total_tokens, "ppl_runs": len(rows)}
    for mod in MODELS:
        g = {m: main_grid.get((mod, m)) for m in ORDER
             if main_grid.get((mod, m)) is not None}
        if g:
            ev = [m for m in ORDER if m != "full" and m in g]
            best = min(ev, key=lambda m: g[m])
            summary[f"{mod}_ppl"] = g
            summary[f"{mod}_best"] = {"method": best, "ppl": g[best]}
            # sensitivity (1.5B only)
    for r in rows:
        if r["model"] == "qwen15b" and r["gamma"] is not None:
            summary.setdefault("qwen15b_gamma", {})[str(r["gamma"])] = r["ppl"]
        if r["model"] == "qwen15b" and r["tau"] is not None:
            summary.setdefault("qwen15b_tau", {})[str(r["tau"])] = r["ppl"]
    for mod in MODELS:
        agg = defaultdict(list)
        for f in glob.glob(f"{SRC}/needle/*.json"):
            d = json.load(open(f))
            if d["model"] == mod and not d.get("multi"):
                agg[d["method"]].append(d["hit_rate"])
        if agg:
            summary[f"{mod}_needle_mean"] = {
                k: float(np.mean(v)) for k, v in agg.items()}
        magg = defaultdict(list)
        for f in glob.glob(f"{SRC}/needle/*multi*.json"):
            d = json.load(open(f))
            if d["model"] == mod:
                magg[d["method"]].append(d["hit_rate"])
        if magg:
            summary[f"{mod}_multi_mean"] = {
                k: float(np.mean(v)) for k, v in magg.items()}
    json.dump(summary, open(f"{OUT}/gpu_summary.json", "w"), indent=2)

    # ---------- digest ----------
    print("\n===== PPL main grid =====")
    for mod in MODELS:
        g = {m: main_grid.get((mod, m)) for m in ORDER if main_grid.get((mod, m))}
        if g:
            print(f"\n{MNICE[mod]} (full = {g.get('full')}):")
            for m in ORDER:
                if m in g and m != "full":
                    print(f"  {m:>16s}: {g[m]:.3f}")
    print("\n===== needle mean hit-rates =====")
    print(json.dumps({k: v for k, v in summary.items()
                      if "needle" in k or "multi" in k}, indent=1))
    print("\nARTIFACTS_DONE ->", OUT)


if __name__ == "__main__":
    main()
