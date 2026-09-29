#!/usr/bin/env python3
"""
Data figures for the SAGE paper (figs 2-8).

Follows:
- academic-plotting SKILL.md publication styling template
- chart-type selections from process-docs/02-chart-selection.md
- vector PDF export + 300 dpi PNG
- SAGE highlighted in coral (#E76F51), baselines in muted colors,
  colorblind-safe with distinct markers/linestyles.
"""
import csv
import os
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

RES = "/home/z/my-project/paper-project/research-repo/results"
FIG = "/home/z/my-project/paper-project/paper/figures"

plt.rcParams.update({
    "font.family": "serif",
    "font.serif": ["Times New Roman", "Liberation Serif", "DejaVu Serif"],
    "font.size": 10, "axes.titlesize": 11, "axes.titleweight": "bold",
    "axes.labelsize": 10.5, "legend.fontsize": 8.5, "legend.frameon": False,
    "figure.dpi": 300, "savefig.dpi": 300,
    "axes.spines.top": False, "axes.spines.right": False,
    "axes.grid": True, "grid.alpha": 0.18, "grid.linestyle": "-",
    "lines.linewidth": 1.7, "lines.markersize": 5,
    "xtick.direction": "out", "ytick.direction": "out",
})

COLORS = {"SAGE": "#E76F51"}
BASE_SEQ = ["#264653", "#2A9D8F", "#E9C46A", "#5E81AC", "#8C8C8C"]
MARKERS = {"SAGE": "o", "TOVA": "s", "FastGen": "D", "ScissorHands": "v",
           "H2O": "^", "StreamingLLM": "x", "Full": "P"}
LINESTYLE = {"SAGE": "-", "TOVA": "-", "FastGen": "--", "ScissorHands": "--",
             "H2O": "-.", "StreamingLLM": ":", "Full": "-"}


def read(path):
    with open(os.path.join(RES, path)) as f:
        return list(csv.DictReader(f))


def save(fig, name):
    fig.savefig(os.path.join(FIG, name + ".pdf"))
    fig.savefig(os.path.join(FIG, name + ".png"))
    plt.close(fig)
    print("saved", name)


# ----------------------------------------------------------------------
# fig2: perplexity vs budget (7B, two panels)
# ----------------------------------------------------------------------
rows = read("ppl_compression.csv")
budgets = [0.10, 0.20, 0.50, 1.00]
methods = ["SAGE", "TOVA", "FastGen", "ScissorHands", "H2O", "StreamingLLM"]

fig, axes = plt.subplots(1, 2, figsize=(6.9, 2.9), constrained_layout=True)
for ax, ds in zip(axes, ["wikitext2", "pg19"]):
    for mi, m in enumerate(methods):
        ys, es = [], []
        for b in budgets:
            r = [x for x in rows if x["model"] == "llama2-7b"
                 and x["dataset"] == ds and x["budget"] == f"{b:.2f}"
                 and x["method"] == m][0]
            ys.append(float(r["ppl_mean"]))
            es.append(float(r["ppl_std"]))
        ys, es = np.array(ys), np.array(es)
        if m == "SAGE":
            c, lw, z = "#E76F51", 2.1, 5
        else:
            c, lw, z = BASE_SEQ[mi % len(BASE_SEQ)] if m != "H2O" else "#5E81AC", 1.5, 3
            c = {"TOVA": "#2A9D8F", "FastGen": "#E9C46A",
                 "ScissorHands": "#8C8C8C", "H2O": "#264653",
                 "StreamingLLM": "#5E81AC"}[m]
        ax.plot(budgets, ys, label=m, color=c, lw=lw, zorder=z,
                marker=MARKERS[m], ls=LINESTYLE[m], markersize=4.5)
        ax.fill_between(budgets, ys - es, ys + es, color=c, alpha=0.13, zorder=z)
    ax.set_xscale("log")
    ax.set_xticks(budgets)
    ax.set_xticklabels(["0.1", "0.2", "0.5", "1.0"])
    ax.set_xlabel("KV budget (fraction of full cache)")
    ax.set_ylabel("Perplexity")
    ax.set_title({"wikitext2": "WikiText-2", "pg19": "PG19"}[ds], fontsize=10)
    ax.set_xlim(0.085, 1.25)
axes[0].legend(loc="upper left", fontsize=7.6, ncol=1, handlelength=1.6,
               bbox_to_anchor=(0.02, 0.99))
save(fig, "fig2_ppl_budget")

# ----------------------------------------------------------------------
# fig3: layer-wise budget profile
# ----------------------------------------------------------------------
rows = read("layer_budget.csv")
layers = np.array([int(r["layer"]) for r in rows])
ret = np.array([float(r["retention_ratio"]) for r in rows])
fig, ax = plt.subplots(figsize=(6.9, 2.5), constrained_layout=True)
ax.bar(layers, ret, width=0.78, color="#5E81AC", alpha=0.85,
       edgecolor="white", linewidth=0.4)
ax.axhline(0.20, color="#64748B", ls="--", lw=1.3)
ax.text(1.1, 0.225, "uniform 0.20 budget", fontsize=8.5, color="#64748B")
ax.set_xlabel("Layer index (LLaMA-2-7B, 32 layers)")
ax.set_ylabel("Retention ratio")
ax.set_ylim(0, 0.65)
ax.set_xlim(0, 33)
save(fig, "fig3_layer_budget")

# ----------------------------------------------------------------------
# fig4: LongBench radar
# ----------------------------------------------------------------------
rows = read("longbench_20pct.csv")
tasks = ["NarrativeQA", "Qasper", "MultiFieldQA", "HotpotQA", "2WikiMQA",
         "MuSiQue", "GovReport", "QMSum", "TREC", "TriviaQA", "SAMSum"]
short = ["NQA", "QSP", "MFQA", "HPQA", "2Wiki", "MSQ", "GovR", "QMS",
         "TREC", "TQA", "SMS"]
LB_FULL = [23.4, 37.2, 45.1, 38.6, 32.4, 21.7, 31.2, 23.9, 71.5, 60.3, 46.8]
methods4 = ["SAGE", "TOVA", "H2O", "StreamingLLM"]
score = {m: [float(next(x["score_mean"] for x in rows
                        if x["method"] == m and x["task"] == t)) for t in tasks]
         for m in methods4}

angles = np.linspace(0, 2 * np.pi, len(tasks), endpoint=False).tolist()
angles += angles[:1]

fig = plt.figure(figsize=(4.9, 4.4))
ax = fig.add_subplot(111, polar=True)
ax.set_theta_offset(np.pi / 2)
ax.set_theta_direction(-1)
ax.set_rlabel_position(12)

# full-cache reference (light gray filled)
full = LB_FULL + LB_FULL[:1]
ax.plot(angles, full, color="#9AA5B1", lw=1.2, ls=":", label="Full cache")
ax.fill(angles, full, color="#9AA5B1", alpha=0.15)

radar_c = {"SAGE": "#E76F51", "TOVA": "#2A9D8F", "H2O": "#264653",
           "StreamingLLM": "#E9C46A"}
for m in methods4:
    v = score[m] + score[m][:1]
    ax.plot(angles, v, color=radar_c[m], lw=1.9 if m == "SAGE" else 1.3,
            label=m, ls="-" if m in ("SAGE", "H2O") else "--",
            marker="o" if m == "SAGE" else None, markersize=3.2)
    if m == "SAGE":
        ax.fill(angles, v, color="#E76F51", alpha=0.10)

ax.set_xticks(angles[:-1])
ax.set_xticklabels(short, fontsize=8.3)
ax.set_ylim(15, 75)
ax.set_yticks([25, 40, 55, 70])
ax.set_yticklabels(["25", "40", "55", "70"], fontsize=7.5, color="#64748B")
ax.tick_params(pad=3)
ax.legend(loc="upper center", bbox_to_anchor=(0.5, -0.06), fontsize=8,
          ncol=3, columnspacing=1.2, handlelength=1.5)
fig.savefig(os.path.join(FIG, "fig4_longbench_radar.pdf"), bbox_inches="tight")
fig.savefig(os.path.join(FIG, "fig4_longbench_radar.png"), bbox_inches="tight")
plt.close(fig)
print("saved fig4_longbench_radar")

# ----------------------------------------------------------------------
# fig5: needle heatmap (SAGE vs H2O)
# ----------------------------------------------------------------------
rows = read("needle_heatmap.csv")
depths = ["0-25%", "25-50%", "50-75%", "75-100%"]
ctxs = [8, 16, 32, 64, 128]

fig, axes = plt.subplots(1, 2, figsize=(6.9, 2.7), constrained_layout=True)
for ax, m in zip(axes, ["SAGE", "H2O"]):
    M = np.zeros((4, 5))
    for r in rows:
        if r["method"] == m:
            i = depths.index(r["depth_bin"])
            j = ctxs.index(int(r["context_k"]))
            M[i, j] = float(r["accuracy"])
    im = ax.imshow(M, cmap="RdYlGn", vmin=35, vmax=100, aspect="auto")
    ax.set_xticks(range(5))
    ax.set_xticklabels([f"{c}K" for c in ctxs], fontsize=9)
    ax.set_yticks(range(4))
    ax.set_yticklabels(depths, fontsize=9)
    ax.set_xlabel("Context length")
    if m == "SAGE":
        ax.set_ylabel("Document depth")
    ax.set_title(m, fontsize=10)
    for i in range(4):
        for j in range(5):
            ax.text(j, i, f"{M[i, j]:.0f}", ha="center", va="center",
                    fontsize=7.6, color="#1F2937")
    ax.grid(False)
cbar = fig.colorbar(im, ax=axes, shrink=0.86, pad=0.02)
cbar.set_label("Retrieval accuracy (%)", fontsize=9)
cbar.ax.tick_params(labelsize=8)
save(fig, "fig5_needle_heatmap")

# ----------------------------------------------------------------------
# fig6: efficiency (memory + throughput)
# ----------------------------------------------------------------------
rows = read("efficiency.csv")
e7 = [r for r in rows if r["model"] == "llama2-7b"]
ctx = np.array([int(r["context_k"]) for r in e7])
mem_f = np.array([float(r["kv_mem_full_gb"]) for r in e7])
mem_s = np.array([float(r["kv_mem_sage_gb"]) for r in e7])
tps_f = np.array([float(r["decode_tps_full"]) for r in e7])
tps_s = np.array([float(r["decode_tps_sage"]) for r in e7])
speed = np.array([float(r["speedup"]) for r in e7])

fig, axes = plt.subplots(1, 2, figsize=(6.9, 2.8), constrained_layout=True)
ax = axes[0]
ax.plot(ctx, mem_f, color="#264653", marker="^", label="Full cache")
ax.plot(ctx, mem_s, color="#E76F51", marker="o", lw=2.0, label="SAGE (20%)")
ax.annotate("4.4$\\times$ smaller", xy=(48, 8.5), fontsize=8.5,
            color="#E76F51", ha="center")
ax.annotate("", xy=(32, 3.79), xytext=(32, 16.77),
            arrowprops=dict(arrowstyle="->", color="#E76F51", lw=1.1))
ax.set_xlabel("Context length (K tokens)")
ax.set_ylabel("KV cache memory (GB)")
ax.set_xticks(ctx)
ax.set_xticklabels([f"{c}K" for c in ctx])
ax.legend(loc="upper left")

ax = axes[1]
ax.plot(ctx, tps_f, color="#264653", marker="^", label="Full cache")
ax.plot(ctx, tps_s, color="#E76F51", marker="o", lw=2.0, label="SAGE (20%)")
for x, y, s in [(32, tps_s[3], "1.52$\\times$"), (128, tps_s[5], "2.02$\\times$")]:
    ax.annotate(s, xy=(x, y + 1.5), fontsize=8.5, color="#E76F51", ha="center")
ax.set_xlabel("Context length (K tokens)")
ax.set_ylabel("Decode throughput (tokens/s)")
ax.set_xticks(ctx)
ax.set_xticklabels([f"{c}K" for c in ctx])
ax.set_ylim(0, 70)
ax.legend(loc="center right")
save(fig, "fig6_efficiency")

# ----------------------------------------------------------------------
# fig7: ablation (two panels: ppl bars + LongBench bars)
# ----------------------------------------------------------------------
rows = read("ablation.csv")
configs = [r["config"] for r in rows]
ppl = [float(r["ppl_mean"]) for r in rows]
ppl_e = [float(r["ppl_std"]) for r in rows]
lb = [float(r["longbench_avg"]) for r in rows]
labels = ["SAGE (full)", "w/o LABA", "w/o reservoir", "w/o decay",
          "w/o scheduler"]

fig, axes = plt.subplots(1, 2, figsize=(6.9, 2.6), constrained_layout=True)
y = np.arange(len(configs))
cols = ["#E76F51"] + ["#5E81AC"] * 4
ax = axes[0]
ax.barh(y, ppl, xerr=ppl_e, color=cols, height=0.58,
        error_kw=dict(lw=0.9, capsize=2.5, ecolor="#475569"))
ax.axvline(5.12, color="#64748B", ls=":", lw=1.2)
ax.text(5.16, -0.42, "full cache 5.12", fontsize=7.8, color="#64748B")
ax.set_yticks(y)
ax.set_yticklabels(labels, fontsize=9)
ax.invert_yaxis()
ax.set_xlabel("WikiText-2 perplexity")
ax.set_xlim(4.8, 6.6)

ax = axes[1]
ax.barh(y, lb, color=cols, height=0.58)
ax.axvline(39.3, color="#64748B", ls=":", lw=1.2)
ax.text(39.45, -0.42, "full 39.3", fontsize=7.8, color="#64748B")
ax.set_yticks(y)
ax.set_yticklabels([])
ax.invert_yaxis()
ax.set_xlabel("LongBench average")
ax.set_xlim(30, 41)
for i, v in enumerate(lb):
    ax.text(v + 0.25, i, f"{v:.1f}", va="center", fontsize=8, color="#334155")
save(fig, "fig7_ablation")

# ----------------------------------------------------------------------
# fig8: sensitivity (dual-axis, reservoir + decay)
# ----------------------------------------------------------------------
res_r = read("sensitivity_reservoir.csv")
dec = read("sensitivity_decay.csv")

fig, axes = plt.subplots(1, 2, figsize=(6.9, 2.7), constrained_layout=True)
ax = axes[0]
rs = np.array([int(r["reservoir_size"]) for r in res_r])
pplr = np.array([float(r["ppl"]) for r in res_r])
nkr = np.array([float(r["needle_128k"]) for r in res_r])
ax.set_xscale("log", base=2)
ax.plot(rs, pplr, color="#264653", marker="o", label="WikiText-2 ppl (left)")
ax.axvline(32, color="#E76F51", ls=":", lw=1.2)
ax.text(33.5, 5.585, "default $r$=32", fontsize=8, color="#E76F51")
ax.set_xlabel("Recent-window reservoir size $r$")
ax.set_ylabel("Perplexity", color="#264653")
ax.set_xticks(rs)
ax.set_xticklabels([str(x) for x in rs])
ax2 = ax.twinx()
ax2.plot(rs, nkr, color="#E76F51", marker="s", ls="--",
         label="Needle@128K (right)")
ax2.set_ylabel("Needle accuracy @128K (%)", color="#E76F51")
ax2.set_ylim(88, 97)
ax2.tick_params(axis="y", colors="#E76F51")
ax2.spines["right"].set_visible(True)
h1, l1 = ax.get_legend_handles_labels()
h2, l2 = ax2.get_legend_handles_labels()
ax.legend(h1 + h2, l1 + l2, loc="upper center", fontsize=7.6,
          bbox_to_anchor=(0.5, 1.16), ncol=2)

ax = axes[1]
lams = np.array([float(r["decay_lambda"]) for r in dec])
ppld = np.array([float(r["ppl"]) for r in dec])
nkd = np.array([float(r["needle_128k"]) for r in dec])
ax.plot(lams, ppld, color="#264653", marker="o")
ax.axvline(0.99, color="#E76F51", ls=":", lw=1.2)
ax.text(0.9605, 5.62, "default $\\lambda$=0.99", fontsize=8, color="#E76F51")
ax.set_xlabel("Decay factor $\\lambda$")
ax.set_ylabel("Perplexity", color="#264653")
ax2 = ax.twinx()
ax2.plot(lams, nkd, color="#E76F51", marker="s", ls="--")
ax2.set_ylabel("Needle accuracy @128K (%)", color="#E76F51")
ax2.set_ylim(88, 97)
ax2.tick_params(axis="y", colors="#E76F51")
ax2.spines["right"].set_visible(True)
save(fig, "fig8_sensitivity")

print("\nAll data figures generated.")

# ----------------------------------------------------------------------
# fig9 (appendix): sensitivity to tau and scheduler interval K
# ----------------------------------------------------------------------
def read2(path):
    with open(os.path.join(RES, path)) as f:
        return list(csv.DictReader(f))

tau_rows = read2("sensitivity_tau.csv")
k_rows = read2("sensitivity_k.csv")

fig, axes = plt.subplots(1, 2, figsize=(6.9, 2.6), constrained_layout=True)
ax = axes[0]
taus = [float(r["tau"]) for r in tau_rows]
pplt = [float(r["ppl"]) for r in tau_rows]
ax.plot(taus, pplt, color="#264653", marker="o")
ax.axvline(1.5, color="#E76F51", ls=":", lw=1.2)
ax.text(1.58, 5.80, "default $\\tau$=1.5", fontsize=8, color="#E76F51")
ax.annotate("uniform split", xy=(0.0, 5.81), xytext=(0.25, 5.60),
            fontsize=8, color="#64748B",
            arrowprops=dict(arrowstyle="->", color="#64748B", lw=0.9))
ax.set_xlabel("Contrast exponent $\\tau$")
ax.set_ylabel("WikiText-2 perplexity")
ax.set_ylim(5.35, 5.95)

ax = axes[1]
ks = [int(r["interval_k"]) for r in k_rows]
pplk = [float(r["ppl"]) for r in k_rows]
ovh = [float(r["prefill_overhead_pct"]) for r in k_rows]
ax.set_xscale("log", base=2)
ax.plot(ks, pplk, color="#264653", marker="o")
ax.axvline(512, color="#E76F51", ls=":", lw=1.2)
ax.text(560, 5.545, "default $K$=512", fontsize=8, color="#E76F51")
ax.set_xlabel("Scheduler interval $K$ (steps)")
ax.set_ylabel("WikiText-2 perplexity", color="#264653")
ax.set_xticks(ks)
ax.set_xticklabels([str(x) for x in ks])
ax.set_ylim(5.35, 5.60)
ax2 = ax.twinx()
ax2.plot(ks, ovh, color="#E76F51", marker="s", ls="--")
ax2.set_ylabel("Prefill overhead (%)", color="#E76F51")
ax2.set_ylim(4, 9)
ax2.tick_params(axis="y", colors="#E76F51")
ax2.spines["right"].set_visible(True)
save(fig, "fig9_appendix_sensitivity")
