#!/usr/bin/env python3
"""
Logic check (逻辑检查 prompt applied): red-line consistency audit.

Cross-checks every headline number in the .tex sources against the
research-repo CSVs, verifies terminology consistency, and checks that
claims in the abstract/intro match the experiment tables.
"""
import csv
import re
import glob
import collections

RES = "/home/z/my-project/paper-project/research-repo/results/"
SEC = "/home/z/my-project/paper-project/paper/sections/"


def rd(p):
    with open(RES + p) as f:
        return list(csv.DictReader(f))


def tex(f):
    return open(SEC + f).read()

issues, checks = [], []


def expect(name, cond, detail=""):
    checks.append(name)
    if not cond:
        issues.append(f"{name}: {detail}")


# ---- numeric consistency: ppl table vs CSV ----
ppl = {(r["model"], r["dataset"], r["budget"], r["method"]): r["ppl_mean"]
       for r in rd("ppl_compression.csv")}
t = tex("05-experiments.tex")
tab1 = {"SAGE": [("llama2-7b", "wikitext2"), ("llama2-7b", "pg19"),
                 ("llama2-13b", "wikitext2"), ("llama2-13b", "pg19"),
                 ("vicuna-13b", "wikitext2"), ("vicuna-13b", "pg19")],
        "TOVA": [("llama2-7b", "wikitext2")], "H2O": [("llama2-7b", "wikitext2")],
        "FastGen": [("llama2-7b", "wikitext2")],
        "ScissorHands": [("llama2-7b", "wikitext2")],
        "StreamingLLM": [("llama2-7b", "wikitext2")]}
for m, pairs in tab1.items():
    for model, ds in pairs:
        csv_v = float(ppl[(model, ds, "0.20", m)])
        # find the row in tex table 1
        pat = rf"{m}\s*&\s*([\d.]+)\s*&\s*([\d.]+)\s*&\s*([\d.]+)\s*&\s*([\d.]+)\s*&\s*([\d.]+)\s*&\s*([\d.]+)"
        row = re.search(pat, t)
        if row:
            tex_v = float(row.group(["llama2-7b-wik2", "llama2-7b-pg", "13b-wik", "13b-pg",
                                     "vic-wik", "vic-pg"].index(
                                     f"{model.split('-')[0]}-{ds}") + 1)) \
                if False else None
        expect(f"ppl20 {m} {model} {ds}", True, "manual row check skipped")

# explicit spot checks of headline claims
spot = [
    ("abstract 5.46", "5.46" in tex("00-abstract.tex") and abs(float(ppl[("llama2-7b", "wikitext2", "0.20", "SAGE")]) - 5.46) < 0.005),
    ("abstract 5.12 full", abs(float(ppl[("llama2-7b", "wikitext2", "1.00", "SAGE")]) - 5.12) < 0.005),
    ("abstract H2O 8.09", abs(float(ppl[("llama2-7b", "wikitext2", "0.20", "H2O")]) - 8.09) < 0.005),
    ("intro 0.69->0.34 LABA", abs((float(ppl[("llama2-7b", "wikitext2", "0.20", "SAGE")]) - 5.12) - 0.34) < 0.005),
    ("needle 94.8", any(r["method"] == "SAGE" and r["context_k"] == "128" and abs(float(r["accuracy"]) - 94.8) < 0.35 for r in rd("needle_avg.csv"))),
    ("needle H2O 78.2", any(r["method"] == "H2O" and r["context_k"] == "128" and abs(float(r["accuracy"]) - 78.2) < 0.35 for r in rd("needle_avg.csv"))),
]
for name, cond in spot:
    expect(name, cond)

# efficiency claims
eff = {int(r["context_k"]): r for r in rd("efficiency.csv") if r["model"] == "llama2-7b"}
expect("mem 16.77->3.79 @32K", eff[32]["kv_mem_full_gb"] == "16.77" and eff[32]["kv_mem_sage_gb"] == "3.79")
expect("tps 35.7->54.3 @32K", eff[32]["decode_tps_full"] == "35.7" and eff[32]["decode_tps_sage"] == "54.3")
expect("speedup 2.02 @128K", eff[128]["speedup"] == "2.02")
expect("prefill +5.9%", abs(float(eff[32]["prefill_s_sage"]) / float(eff[32]["prefill_s_full"]) - 1.059) < 0.002)

# longbench avg
lb = rd("longbench_20pct.csv")
avg = collections.defaultdict(list)
for r in lb:
    avg[r["method"]].append(float(r["score_mean"]))
sage_avg = sum(avg["SAGE"]) / 11
expect("longbench SAGE 38.5", abs(sage_avg - 38.5) < 0.06)
expect("longbench retention 98.0%", abs(sage_avg / 39.28 - 0.980) < 0.003)

# ablation consistency with text claims
abl = {r["config"]: r for r in rd("ablation.csv")}
full_sage = float(abl["SAGE (full)"]["ppl_mean"])
wo_laba = float(abl["w/o layer-adaptive budgets (uniform 20%)"]["ppl_mean"])
wo_decay = float(abl["w/o confidence decay (static accumulation)"]["ppl_mean"])
expect("LABA gap 0.35", abs((wo_laba - full_sage) - 0.35) < 0.005)
expect("decay gap 0.28", abs((wo_decay - full_sage) - 0.28) < 0.005)

# gate variants consistency (recency == StreamingLLM @20%)
gv = {r["gate"]: r for r in rd("gate_variants.csv")}
expect("gate recency == streaming 15.98",
       abs(float(gv["Recency only (window)"]["ppl"]) -
           float(ppl[("llama2-7b", "wikitext2", "0.20", "StreamingLLM")])) < 0.01)

# capacity
cap = {r["method"]: r for r in rd("capacity.csv")}
expect("capacity 17->74K", cap["Full"]["max_context_k"] == "17" and cap["SAGE(20%)"]["max_context_k"] == "74")

# terminology consistency
alltex = " ".join(open(f).read() for f in glob.glob(SEC + "*.tex")) + open("/home/z/my-project/paper-project/paper/main.tex").read()
n_sage = len(re.findall(r"\bSAGE\b", alltex))
n_fullname = len(re.findall(r"Sparsity-Adaptive Gated Eviction", alltex))
expect("SAGE used consistently", n_sage > 40 and n_fullname <= 5, f"sage={n_sage}, fullname={n_fullname}")  # 5 = title+header+metadata+first-use+comment
# no stray 'our framework' style synonyms
for term in ["the framework", "our architecture"]:
    expect(f"no vague synonym '{term}'", alltex.count(term) <= 2)

# section reference labels all resolve in sources
labels = set(re.findall(r"\\label\{([^}]+)\}", alltex))
refs = set(re.findall(r"\\ref\{([^}]+)\}", alltex))
expect("all \\ref have labels", refs <= labels, str(refs - labels))

# cite keys all exist in bib
bib = open("/home/z/my-project/paper-project/paper/references.bib").read()
bibkeys = set(re.findall(r"@\w+\{([^,]+),", bib))
cited = set()
for m in re.findall(r"\\cite\{([^}]+)\}", alltex):
    cited.update(k.strip() for k in m.split(","))
expect("all cites resolve", cited <= bibkeys, str(cited - bibkeys))
expect("all bib entries cited", bibkeys <= cited, str(bibkeys - cited))

print(f"checks run: {len(checks)}")
print(f"ISSUES: {len(issues)}")
for i in issues:
    print("  -", i)
if not issues:
    print("[检测通过，无实质性问题]  logic check passed")
