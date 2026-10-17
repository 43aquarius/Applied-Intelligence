"""Engine correctness probe - the gate before any experiment runs.

Verifies:
 1. Chunked no-compression forward == full forward (position/mask correctness).
 2. Budget compliance: retained == nominal at EVERY step, violations == 0.
 3. All policies run; per-layer shapes survive compression.
 4. Speed benchmarks to finalize the experiment grid for a 2-core CPU.
"""
import os
import sys
import time

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
os.environ.setdefault("HF_ENDPOINT", "https://hf-mirror.com")

import numpy as np
import torch

from sage.engine import Engine
from sage.policies import make_policy

MODEL = sys.argv[1] if len(sys.argv) > 1 else "/home/z/my-project/models/gpt2"


def rss_mb():
    with open("/proc/self/status") as f:
        for line in f:
            if line.startswith("VmRSS"):
                return int(line.split()[1]) / 1024
    return -1


def probe(model_name: str, seq_len=128, chunk=32):
    print(f"\n================ PROBE {model_name} ================")
    print("torch", torch.__version__, "| transformers", __import__("transformers").__version__)
    eng = Engine(model_name, chunk=chunk, threads=2)
    tok = eng.tokenizer
    print(f"layers={eng.L} Hq={eng.Hq} Hkv={eng.Hkv} head_dim={eng.head_dim} "
          f"entry_bytes={eng.entry_bytes}")
    text = ("The quick brown fox jumps over the lazy dog. " * 200)
    ids = tok(text, return_tensors="pt").input_ids[:, :seq_len]
    print("seq:", ids.shape)

    # ---------- 1. full forward reference ----------
    with torch.no_grad():
        full = eng.model(input_ids=ids, output_attentions=False).logits
    print("full forward done; RSS", f"{rss_mb():.0f}MB")

    # ---------- 2. chunked, no compression (rho=1) ----------
    pol = make_policy("sage", eng.L)
    log = eng.new_log(pol, 1.0, seq_len)
    eng.reset()
    nll, cnt = eng.teacher_forced(ids, pol, 1.0, log)
    # reconstruct logits comparison: rerun chunked and collect logits
    eng.reset()
    logits_parts = []
    # simpler: monkey check via NLL of full model
    with torch.no_grad():
        lp = torch.log_softmax(full[0, :-1].to(torch.float64), dim=-1)
        full_nll = -lp[torch.arange(seq_len - 1), ids[0, 1:]].sum().item()
    print(f"NLL chunked(no-compress)={nll:.6f} vs full={full_nll:.6f} "
          f"rel.diff={abs(nll - full_nll) / max(abs(full_nll), 1e-9):.2e}")
    assert abs(nll - full_nll) / max(abs(full_nll), 1e-9) < 2e-3, \
        "CHUNKED FORWARD MISMATCH - position/mask bug!"
    print("PASS: chunked no-compression matches full forward")

    # ---------- 3. compression with all policies ----------
    for name in ["sage", "h2o", "streamingllm", "pyramidkv", "reverse-pyramid",
                 "sage-nodecay", "sage-uniform"]:
        pol = make_policy(name, eng.L)
        log = eng.new_log(pol, 0.3, seq_len)
        eng.reset()
        t0 = time.perf_counter()
        nll, cnt = eng.teacher_forced(ids, pol, 0.3, log)
        dt = time.perf_counter() - t0
        last = log.steps[-1]
        print(f"{name:>16s}: NLL/tok={nll / max(cnt, 1):.4f} retained={last.total_retained} "
              f"nominal={last.nominal_budget} violations={log.budget_violations} "
              f"steps={len(log.steps)} time={dt:.2f}s")
        assert log.budget_violations == 0, f"{name} BUDGET VIOLATION"
        assert last.total_retained == last.nominal_budget
    print("PASS: all policies budget-exact")

    # ---------- 4. speed benchmark ----------
    long_ids = tok(text * 20, return_tensors="pt").input_ids[:, :1024]
    pol = make_policy("sage", eng.L)
    eng.reset()
    t0 = time.perf_counter()
    nll, cnt = eng.teacher_forced(long_ids, pol, 0.2)
    dt = time.perf_counter() - t0
    print(f"SPEED prefill@1024 rho=0.2: {dt:.1f}s total = {1024 / dt:.1f} tok/s "
          f"| NLL/tok={nll / max(cnt, 1):.4f} | RSS {rss_mb():.0f}MB")

    # decode speed (short prefill then 16 tokens)
    eng.reset()
    t0 = time.perf_counter()
    gen = eng.generate(ids[:, :256], pol, 0.2, max_new_tokens=16)
    dt = time.perf_counter() - t0
    print(f"SPEED prefill256+decode16: {dt:.1f}s = {16 / (dt - 256 * dt / 272):.2f} tok/s decode approx")
    print(f"generated tail: {tok.decode(gen)[-60:]!r}")
    print(f"RSS {rss_mb():.0f}MB")


if __name__ == "__main__":
    probe(MODEL)
