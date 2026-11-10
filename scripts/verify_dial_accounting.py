#!/usr/bin/env python3
"""Task 19 part 2: verify accounting violation structure + needle aggregates."""
import json, glob, os, re

BASE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "results", "gpu", "ext8k")
ok = True

def check(label, got, want):
    global ok
    good = got == want
    print(f"{'OK ' if good else 'FAIL'} {label}: raw={got} expected={want}")
    if not good: ok = False

# ---- accounting: sage r0.2 violation structure ----
print("== accounting structure (sage r0.2) ==")
for model, want_n, want_max in [("qwen15b-ext8k", 4, 13), ("qwen15b-ext16k", 57, 100)]:
    d = json.load(open(f"{BASE}/ppl/{model}__sage__r0.2__gNone__tNone.accounting.json"))
    diffs = [(s["total_retained"] - s["nominal_budget"], s["t"]) for s in d["steps"]
             if s["total_retained"] != s["nominal_budget"]]
    neg = [x for x, _ in diffs if x < 0]
    first_t = min((t for _, t in diffs), default=None)
    mx = max((abs(x) for x, _ in diffs), default=0)
    check(f"{model} violation count", len(diffs), want_n)
    check(f"{model} all negative", len(neg) == len(diffs), True)
    check(f"{model} max |diff|", mx, want_max)
    print(f"   {model}: diffs={sorted([x for x,_ in diffs])}, first_bad_t={first_t}")
    check(f"{model} header count", d["budget_violations"], want_n)

# static policies: confirm 0 diff everywhere
print("== static policies zero-diff ==")
for model in ["qwen15b-ext8k", "qwen15b-ext16k"]:
    for pol in ["sage-uniform", "h2o", "pyramidkv"]:
        d = json.load(open(f"{BASE}/ppl/{model}__{pol}__r0.2__gNone__tNone.accounting.json"))
        nd = sum(1 for s in d["steps"] if s["total_retained"] != s["nominal_budget"])
        check(f"{model} {pol} diffs", nd, 0)

# ---- needle aggregates ----
print("== needle aggregates ==")
def agg(model, method, multi):
    pat = f"{BASE}/needle/{model}__multi__*__{method}.json" if multi else \
          f"{BASE}/needle/{model}__L*__d*__t*__{method}.json"
    files = sorted(glob.glob(pat))
    hrs, rets = [], []
    for p in files:
        d = json.load(open(p))
        hrs.append(d["hit_rate"]); rets.append(d["retention_mean"])
    return (sum(hrs)/len(hrs), sum(rets)/len(rets), len(files)) if files else (None,)*3

exp = [
    ("qwen15b-ext8k","sage",False,0.20,0.242),("qwen15b-ext8k","sage",True,0.333,0.320),
    ("qwen15b-ext8k","h2o",False,0.40,0.023),("qwen15b-ext8k","h2o",True,0.000,0.022),
    ("qwen15b-ext8k","pyramidkv",False,0.20,0.036),("qwen15b-ext8k","pyramidkv",True,0.000,0.036),
    ("qwen15b-ext8k","streamingllm",False,0.20,0.200),
    ("qwen15b-ext16k","sage",False,0.333,0.369),("qwen15b-ext16k","h2o",False,0.667,0.040),
    ("qwen15b-ext16k","pyramidkv",False,0.000,0.042),("qwen15b-ext16k","streamingllm",False,0.333,0.333),
]
for model, method, multi, want_hr, want_ret in exp:
    hr, ret, n = agg(model, method, multi)
    check(f"needle {model} {method} multi={multi} hit (n={n})", round(hr,3), want_hr)
    check(f"needle {model} {method} multi={multi} ret", round(ret,3), want_ret)

# full-cache references
for model in ["qwen15b-ext8k", "qwen15b-ext16k"]:
    hr, ret, n = agg(model, "full", False)
    check(f"needle {model} full single hit", round(hr,3), 1.0)

print("\nALL OK" if ok else "\nSOME CHECKS FAILED")
