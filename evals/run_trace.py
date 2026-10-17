"""Trace per-layer budget allocation + entropy signal on REAL model runs.

Records b_l(t) (per-layer budgets after projection) and kappa_l(t) (EMA
entropy signals) every chunk for SAGE on one WikiText-2 sequence per model,
plus the static PyramidKV profile and the uniform profile for comparison.
"""
import json
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
os.environ.setdefault("HF_ENDPOINT", "https://hf-mirror.com")

import numpy as np
import torch

from sage.engine import Engine
from sage.policies import make_policy, pyramid_weights, uniform_weights

OUT = "/home/z/my-project/sage2/results/alloc_trace.json"


class TracingPolicy:
    """Wraps a SAGE policy, recording budgets and kappa each step."""

    def __init__(self, pol, orig_budgets):
        self.pol = pol
        self.orig_budgets = orig_budgets
        self.b_trace = []
        self.kappa_trace = []
        self.t_trace = []

    def budgets(self, t, rho, protected):
        b = self.orig_budgets(t, rho, protected)
        self.b_trace.append([int(x) for x in b])
        self.kappa_trace.append([float(x) for x in self.pol.kappa])
        self.t_trace.append(t)
        return b


def trace_model(model_path, tag, seq_len):
    eng = Engine(model_path, chunk=64, threads=2)
    tok = eng.tokenizer
    import pandas as pd
    df = pd.read_parquet("/home/z/my-project/models/wikitext2-test.parquet")
    text = "\n".join(str(r) for r in df["text"].tolist())
    ids = tok(text, return_tensors="pt", add_special_tokens=False).input_ids[0]
    ids = torch.tensor(ids[:seq_len].tolist()).unsqueeze(0)

    pol = make_policy("sage", eng.L)
    orig_budgets = pol.budgets
    tr = TracingPolicy(pol, orig_budgets)
    pol.budgets = tr.budgets
    eng.reset()
    eng._ensure_state(pol)
    nll, cnt = eng.teacher_forced(ids, pol, 0.2)
    pol.budgets = orig_budgets

    return {
        "model": tag, "L": eng.L, "seq_len": seq_len,
        "t": tr.t_trace,
        "budgets": tr.b_trace,          # [n_steps][L]
        "kappa": tr.kappa_trace,        # [n_steps][L]
        "kappa_final": tr.kappa_trace[-1],
        "pyramid_profile": [float(x) for x in pyramid_weights(eng.L)],
        "uniform_profile": [float(x) for x in uniform_weights(eng.L)],
        "nll_per_tok": nll / max(cnt, 1),
    }


if __name__ == "__main__":
    res = {}
    res["gpt2"] = trace_model("/home/z/my-project/models/gpt2", "gpt2", 1024)
    print("gpt2 traced:", len(res["gpt2"]["t"]), "steps")
    res["qwen05b"] = trace_model(
        "/home/z/my-project/models/qwen05b", "qwen05b", 2048)
    print("qwen traced:", len(res["qwen05b"]["t"]), "steps")
    json.dump(res, open(OUT, "w"))
    print("TRACE_DONE ->", OUT)
