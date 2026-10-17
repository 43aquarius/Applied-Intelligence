"""Diagnose needle pipeline bottlenecks step by step."""
import os
import sys
import time

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
os.environ.setdefault("HF_ENDPOINT", "https://hf-mirror.com")

import torch

from sage.engine import Engine
from sage.policies import make_policy

sys.path.insert(0, "/home/z/my-project/sage2/evals")
from run_needle import build_prompt, run_case

MODEL = "/home/z/my-project/models/qwen05b"

t0 = time.perf_counter()
eng = Engine(MODEL, chunk=64, threads=2)
print(f"load: {time.perf_counter() - t0:.1f}s")

tok = eng.tokenizer

t0 = time.perf_counter()
ids, spans, codes, prompt = build_prompt(tok, 1024, 50, 42)
dt = time.perf_counter() - t0
print(f"build_prompt: {dt:.1f}s len={ids.shape[1]} spans={spans} codes={codes}")

pol = make_policy("sage", eng.L)
eng.reset()
eng._ensure_state(pol)
t0 = time.perf_counter()
# prefill only
start = 0
N = ids.shape[1]
while start < N:
    end = min(start + eng.chunk, N)
    logits, attn, past = eng._forward_chunk(
        ids[:, start:end],
        torch.arange(start, end).unsqueeze(0))
    eng._append_chunk_kv(past, end - start)
    eng._observe_and_compress(attn, end - start, end, pol, 0.2, None)
    start = end
print(f"prefill {N}: {time.perf_counter() - t0:.1f}s")

t0 = time.perf_counter()
gen = eng.generate(ids, pol, 0.2, max_new_tokens=4)
print(f"generate(4 new) total: {time.perf_counter() - t0:.1f}s "
      f"(includes re-prefill)")
