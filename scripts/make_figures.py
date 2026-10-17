#!/usr/bin/env python3
"""Generate all paper figures (vector PDF) + LaTeX table bodies from the
real experiment results. English labels (paper language)."""
import glob
import json
import os
from collections import defaultdict

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

RES = "/home/z/my-project/sage2/results"
FIG = "/home/z/my-project/sage2/figures"
TAB = "/home/z/my-project/sage2/figures"
os.makedirs(FIG, exist_ok=True)

plt.rcParams.update({
    "font.size": 9, "axes.labelsize": 9, "axes.titlesize": 9,
    "legend.fontsize": 8, "xtick.labelsize": 8, "ytick.labelsize": 8,
    "axes.spines.top": False, "axes.spines.right": False,
    "axes.grid": True, "grid.linestyle": "--", "grid.alpha": 0.18,
    "grid.linewidth": 0.5, "legend.frameon": False,
    "pdf.fonttype": 42,
})

C = {"h2o": "#7f7f7f", "pyramidkv": "#dd8452", "sage": "#1a5276",
     "full": "#2ca02c", "streamingllm": "#9467bd", "reverse-pyramid": "#d62728",
     "sage-nodecay": "#8c564b", "sage-uniform": "#17becf"}
NICE = {"h2o": "H2O", "pyramidkv": "PyramidKV (static)", "sage": "SAGE",
        "full": "Full cache", "streamingllm": "StreamingLLM",
        "reverse-pyramid": "Reverse pyramid", "sage-nodecay": "SAGE no-decay",
        "sage-uniform": "SAGE uniform-budget"}


def load_ppl():
    rows = []
    for f in glob.glob(f"{RES}/ppl/*.json"):
        if f.endswith("accounting.json"):
            continue
        rows.append(json.load(open(f)))
    return rows


# ----------------------------------------------------------- fig 1: budget
def fig_budget():
    d = json.load(open(f"{RES}/budget_sim.json"))
    orig = d["ratios_original_first200"]
    corr = d["ratios_corrected_first200"]
    fig, ax = plt.subplots(figsize=(4.6, 2.9), constrained_layout=True)
    t = np.arange(1, len(orig) + 1)
    ax.plot(t, orig, color="#d62728", lw=1.8, label="Original formula (as written)")
    ax.plot(t, corr, color="#1a5276", lw=1.8,
            label="Corrected projection (Theorem 1)")
    ax.axhline(1.0, color="k", lw=0.8, ls=":", alpha=0.7)
    ax.set_xlabel("Sequence position $t$")
    ax.set_ylabel("Realised cache size / contract $\\rho L t$")
    ax.set_ylim(0.9, 1.35)
    ax.annotate(f"mean +{100 * (d['original']['mean_ratio'] - 1):.1f}%\n"
                f"violates at {100 * d['original']['violation_rate']:.0f}% of steps",
                xy=(t[-1] * 0.55, orig[-1]), xytext=(t[-1] * 0.5, 1.22),
                color="#d62728", fontsize=8,
                arrowprops=dict(arrowstyle="-", color="#d62728", lw=0.6))
    ax.annotate("warmup allowance\n(protected region)",
                xy=(30, corr[29]), xytext=(45, 1.13), fontsize=8,
                arrowprops=dict(arrowstyle="-", color="#1a5276", lw=0.6))
    ax.legend(loc="upper right")
    fig.savefig(f"{FIG}/fig_budget.pdf")
    plt.close(fig)


# ------------------------------------------------------- fig 2: ppl curves
def fig_ppl_curve():
    rows = load_ppl()
    data = defaultdict(dict)  # (model, method) -> {rho: ppl}
    for r in rows:
        if r["gamma"] is not None or r["tau"] is not None:
            continue
        data[(r["model"], r["policy"])][r["rho"]] = r["ppl"]
    fig, axes = plt.subplots(1, 2, figsize=(6.6, 2.7), constrained_layout=True)
    for ax, model, title in zip(axes, ["gpt2", "qwen05b"],
                                ["GPT-2 (124M, MHA)", "Qwen2.5-0.5B (GQA)"]):
        for m in ["h2o", "pyramidkv", "sage"]:
            pts = sorted(data[(model, m)].items())
            if pts:
                ax.plot([p[0] for p in pts], [p[1] for p in pts], "-o",
                        ms=3.5, lw=1.8, color=C[m], label=NICE[m])
        full = data[(model, "full")].get(1.0)
        if full:
            ax.axhline(full, color=C["full"], lw=1.0, ls="--", alpha=0.9)
            ax.annotate("full cache", xy=(0.06, full),
                        xycoords=("axes fraction", "data"),
                        xytext=(2, -10), textcoords="offset points",
                        color=C["full"], fontsize=8)
        ax.set_xlabel("Retention ratio $\\rho$")
        ax.set_title(title, fontsize=8.5)
        ax.set_xticks([0.05, 0.1, 0.2, 0.3])
    axes[0].set_ylabel("WikiText-2 perplexity")
    axes[0].legend(loc="upper right")
    fig.savefig(f"{FIG}/fig_ppl_curve.pdf")
    plt.close(fig)


# --------------------------------------------------- fig 3: allocation heat
def fig_alloc():
    d = json.load(open(f"{RES}/alloc_trace.json"))
    fig, axes = plt.subplots(1, 2, figsize=(6.6, 2.6), constrained_layout=True)
    for ax, key, title in zip(axes, ["gpt2", "qwen05b"],
                              ["GPT-2, 12 layers", "Qwen2.5-0.5B, 24 layers"]):
        B = np.array(d[key]["budgets"], dtype=float)     # steps x L
        avg = B.mean(axis=1, keepdims=True)
        rel = B / np.maximum(avg, 1e-9)                  # relative to uniform
        im = ax.imshow(rel.T, aspect="auto", origin="lower", cmap="RdBu_r",
                       vmin=0.55, vmax=1.45,
                       extent=[d[key]["t"][0], d[key]["t"][-1], 0, d[key]["L"]])
        ax.set_xlabel("Sequence position $t$")
        ax.set_ylabel("Layer index $l$")
        ax.set_title(title, fontsize=8.5)
        ax.grid(False)
    fig.colorbar(im, ax=axes, shrink=0.9, pad=0.02,
                 label="Budget / uniform average")
    fig.savefig(f"{FIG}/fig_alloc.pdf")
    plt.close(fig)


# ------------------------------------------------------- fig 4: kappa signal
def fig_kappa():
    d = json.load(open(f"{RES}/alloc_trace.json"))
    fig, axes = plt.subplots(1, 2, figsize=(6.6, 2.4), constrained_layout=True)
    for ax, key, title in zip(axes, ["gpt2", "qwen05b"],
                              ["GPT-2", "Qwen2.5-0.5B"]):
        k = np.array(d[key]["kappa_final"])
        L = len(k)
        ax.bar(np.arange(L), k, color="#1a5276", alpha=0.85, width=0.72,
               label="Dispersion signal $\\kappa_l$ (SAGE, measured)")
        pyr = np.array(d[key]["pyramid_profile"])
        ax.plot(np.arange(L), pyr / pyr.mean() * k.mean(), "--", color="#dd8452",
                lw=1.6, label="PyramidKV static prior (scaled)")
        ax.set_xlabel("Layer index $l$")
        ax.set_title(title, fontsize=8.5)
    axes[0].set_ylabel("Normalised entropy")
    axes[0].legend(loc="lower left")
    fig.savefig(f"{FIG}/fig_kappa.pdf")
    plt.close(fig)


# ----------------------------------------------------------- fig 5: needle
def fig_needle():
    files = glob.glob(f"{RES}/needle/L2048__d*__t*.json")
    by_m_d = defaultdict(list)
    ret_by_m = defaultdict(list)
    for f in files:
        r = json.load(open(f))
        by_m_d[(r["method"], r["depth"])].append(r["hits"][0])
        ret_by_m[r["method"]].append(r["retention_mean"])
    depths = [0, 25, 50, 75, 100]
    fig, ax = plt.subplots(figsize=(4.4, 2.7), constrained_layout=True)
    for m in ["full", "streamingllm", "h2o", "pyramidkv", "sage"]:
        ys = [np.mean(by_m_d.get((m, d), [np.nan])) for d in depths]
        ax.plot(depths, ys, "-o", ms=3.5, lw=1.8, color=C[m], label=NICE[m])
    ax.set_xlabel("Needle depth (% of haystack)")
    ax.set_ylabel("Retrieval accuracy")
    ax.set_ylim(-0.05, 1.1)
    ax.set_xticks(depths)
    ax.legend(loc="lower left", ncol=2, columnspacing=1.0)
    fig.savefig(f"{FIG}/fig_needle.pdf")
    plt.close(fig)
    return {m: float(np.mean(v)) for m, v in ret_by_m.items()}


# ------------------------------------------------------ fig 6: sensitivity
def fig_sens():
    rows = load_ppl()
    g2 = [r for r in rows if r["model"] == "gpt2"]
    gam = [(r["gamma"], r["ppl"]) for r in g2
           if r["policy"] == "sage" and r["gamma"] is not None
           and r["rho"] == 0.2]
    # gamma=1.0 point comes from sage-nodecay main run
    nd = [r for r in g2 if r["policy"] == "sage-nodecay" and r["rho"] == 0.2
          and r["gamma"] is None]
    gam.append((1.0, nd[0]["ppl"]) if nd else (1.0, np.nan))
    tau_g = sorted([(r["tau"], r["ppl"]) for r in g2
                    if r["policy"] == "sage" and r["tau"] is not None
                    and r["rho"] == 0.2] + [(1.5, 49.798)])
    tau_q = sorted([(r["tau"], r["ppl"]) for r in rows
                    if r["model"] == "qwen05b" and r["policy"] == "sage"
                    and r["tau"] is not None and r["rho"] == 0.2]
                   + [(1.5, 17.019)])
    fig, axes = plt.subplots(1, 2, figsize=(6.6, 2.6), constrained_layout=True)
    gam = sorted(gam)
    axes[0].plot([g for g, _ in gam], [p for _, p in gam], "-o", ms=3.5,
                 lw=1.8, color="#1a5276")
    axes[0].set_xlabel("Decay rate $\\gamma$")
    axes[0].set_ylabel("WikiText-2 perplexity")
    axes[0].set_title("Decay sensitivity (GPT-2, $\\rho{=}0.2$)", fontsize=8.5)
    axes[0].set_xticks([0.98, 0.99, 0.999, 1.0])
    axes[1].plot([t for t, _ in tau_g], [p for _, p in tau_g], "-o", ms=3.5,
                 lw=1.8, color="#1a5276", label="GPT-2")
    axes[1].plot([t for t, _ in tau_q], [p for _, p in tau_q], "-s", ms=3.5,
                 lw=1.8, color="#dd8452", label="Qwen2.5-0.5B")
    axes[1].set_xlabel("Allocation exponent $\\tau$")
    axes[1].set_title("Entropy-weight sensitivity", fontsize=8.5)
    axes[1].legend()
    fig.savefig(f"{FIG}/fig_sens.pdf")
    plt.close(fig)


if __name__ == "__main__":
    fig_budget()
    fig_ppl_curve()
    fig_alloc()
    fig_kappa()
    ret = fig_needle()
    fig_sens()
    print("retention means:", {k: round(v, 3) for k, v in ret.items()})
    print("FIGURES_DONE")
