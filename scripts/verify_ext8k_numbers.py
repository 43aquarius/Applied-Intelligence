#!/usr/bin/env python3
"""Re-verify every 8K/16K extension number quoted in the paper (RQ7b).

Checks, all against the raw JSON logs in results/gpu/ext8k/:
  1. Perplexity grid (Table tab:ext8k + budget-curve text): 16 runs.
  2. Accounting structure of the deep-window floor deficits: counts,
     one-sidedness, max |diff|, onset t=5888 (sage r0.2 runs); zero
     deviations for static policies (sage-uniform / h2o / pyramidkv).
  3. Needle aggregates (Table tab:ext8k retention columns): per-depth
     per-trial files aggregated to the quoted means.
  4. memprobe records (capacity ceiling / monolithic-vs-chunked text).
  5. Token totals for the 50-run / 1,130,113-token GPU claim.

Exit code 0 iff every check passes. No model required."""
import json, glob, os, sys

BASE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "results", "gpu", "ext8k")
ok = True

def check(label, got, want, tol=5e-4):
    global ok
    good = abs(got - want) <= tol if isinstance(got, float) else got == want
    print(f"{'OK ' if good else 'FAIL'} {label}: raw={got} expected={want}")
    if not good:
        ok = False

# ---- 1. PPL ----
def ppl(model, policy, rho):
    p = f"{BASE}/ppl/{model}__{policy}__r{rho}__gNone__tNone.json"
    d = json.load(open(p))
    return d["ppl"], d["budget_violations"], d["n_tokens"]

exp8k = {"full": 7.949, "h2o": 9.287, "pyramidkv": 9.775, "sage": 8.716, "sage-uniform": 8.661}
exp16k = {"full": 7.863, "h2o": 9.415, "pyramidkv": 9.899, "sage": 8.417, "sage-uniform": 8.373}
for model, exp, sage_vio in [("qwen15b-ext8k", exp8k, 4), ("qwen15b-ext16k", exp16k, 57)]:
    for pol, want in exp.items():
        r = "1.0" if pol == "full" else "0.2"
        got, vio, _ = ppl(model, pol, r)
        check(f"{model} {pol} r{r}", round(got, 3), want)
        check(f"{model} {pol} violations", vio, sage_vio if pol == "sage" else 0)

print("== budget curve @8K rho 0.05/0.1 ==")
for pol, rho, want in [("h2o", "0.05", 10.831), ("h2o", "0.1", 9.947),
                       ("pyramidkv", "0.05", 11.423), ("pyramidkv", "0.1", 10.584),
                       ("sage", "0.05", 10.061), ("sage", "0.1", 9.249)]:
    got, vio, _ = ppl("qwen15b-ext8k", pol, rho)
    check(f"8K {pol} r{rho}", round(got, 3), want)
    check(f"8K {pol} r{rho} violations", vio, 0)

# ---- 2. accounting: sage r0.2 floor-deficit structure ----
print("== accounting structure (sage r0.2) ==")
for model, want_n, want_max in [("qwen15b-ext8k", 4, 13), ("qwen15b-ext16k", 57, 100)]:
    d = json.load(open(f"{BASE}/ppl/{model}__sage__r0.2__gNone__tNone.accounting.json"))
    diffs = [(s["total_retained"] - s["nominal_budget"], s["t"]) for s in d["steps"]
             if s["total_retained"] != s["nominal_budget"]]
    neg = [x for x, _ in diffs if x < 0]
    first_t = min((t for _, t in diffs), default=None)
    mx = max((abs(x) for x, _ in diffs), default=0)
    check(f"{model} deficit count", len(diffs), want_n)
    check(f"{model} all under-retention", len(neg) == len(diffs), True)
    check(f"{model} max |diff|", mx, want_max)
    check(f"{model} first onset t", first_t, 5888)
    check(f"{model} header count", d["budget_violations"], want_n)

print("== static policies zero-diff ==")
for model in ["qwen15b-ext8k", "qwen15b-ext16k"]:
    for pol in ["sage-uniform", "h2o", "pyramidkv"]:
        d = json.load(open(f"{BASE}/ppl/{model}__{pol}__r0.2__gNone__tNone.accounting.json"))
        nd = sum(1 for s in d["steps"] if s["total_retained"] != s["nominal_budget"])
        check(f"{model} {pol} deviations", nd, 0)

# ---- 3. needle aggregates ----
print("== needle aggregates ==")
def agg(model, method, multi):
    pat = f"{BASE}/needle/{model}__multi__*__{method}.json" if multi else \
          f"{BASE}/needle/{model}__L*__d*__t*__{method}.json"
    files = sorted(glob.glob(pat))
    hrs, rets = [], []
    for p in files:
        d = json.load(open(p))
        hrs.append(d["hit_rate"])
        rets.append(d["retention_mean"])
    return (sum(hrs) / len(hrs), sum(rets) / len(rets), len(files)) if files else (None, None, 0)

exp_needle = [
    ("qwen15b-ext8k", "sage", False, 0.20, 0.242), ("qwen15b-ext8k", "sage", True, 0.333, 0.320),
    ("qwen15b-ext8k", "h2o", False, 0.40, 0.023), ("qwen15b-ext8k", "h2o", True, 0.000, 0.022),
    ("qwen15b-ext8k", "pyramidkv", False, 0.20, 0.036), ("qwen15b-ext8k", "pyramidkv", True, 0.000, 0.036),
    ("qwen15b-ext8k", "streamingllm", False, 0.20, 0.200),
    ("qwen15b-ext16k", "sage", False, 0.333, 0.369), ("qwen15b-ext16k", "h2o", False, 0.667, 0.040),
    ("qwen15b-ext16k", "pyramidkv", False, 0.000, 0.042), ("qwen15b-ext16k", "streamingllm", False, 0.333, 0.333),
]
for model, method, multi, want_hr, want_ret in exp_needle:
    hr, ret, n = agg(model, method, multi)
    check(f"needle {model} {method} multi={multi} hit (n={n})", round(hr, 3), want_hr)
    check(f"needle {model} {method} multi={multi} ret", round(ret, 3), want_ret)
for model in ["qwen15b-ext8k", "qwen15b-ext16k"]:
    hr, _, _ = agg(model, "full", False)
    check(f"needle {model} full single hit", round(hr, 3), 1.0)

# ---- 4. memprobe ----
print("== memprobe ==")
mp = json.load(open(f"{BASE}/memprobe.json"))
m8 = next(m for m in mp if m["seq_len"] == 8192)
m16 = next(m for m in mp if m["seq_len"] == 16384)
check("8K chunked peak GB", m8["peak_gb"], 8.77)
check("8K monolithic feasible", int(m8["monolithic_forward"]["feasible"]), 1)
check("8K monolithic peak GB", m8["monolithic_forward"]["peak_gb"], 13.94)
check("16K chunked peak GB", m16["peak_gb"], 11.24)
check("16K monolithic feasible", int(m16["monolithic_forward"]["feasible"]), 0)

# ---- 5. token totals ----
print("== token totals ==")
all_ppl = [p for p in glob.glob(f"{BASE}/ppl/*.json") if not p.endswith("accounting.json")]
tok_all = sum(json.load(open(p))["n_tokens"] for p in all_ppl)
check("extension PPL runs", len(all_ppl), 16)
check("extension PPL tokens", tok_all, 434133)
print(f"combined GPU perplexity tokens = 695980 + {tok_all} = {695980 + tok_all} (paper: 1,130,113)")
check("combined GPU perplexity tokens", 695980 + tok_all, 1130113)

pe = json.load(open(f"{BASE}/phase_errors.json"))
check("phase_errors (3B@8K OOM guard only)", len(pe), 1)
check("phase_errors kind", pe[0]["kind"] if pe else "none", "OOM")

print("\nALL OK" if ok else "\nSOME CHECKS FAILED")
sys.exit(0 if ok else 1)
