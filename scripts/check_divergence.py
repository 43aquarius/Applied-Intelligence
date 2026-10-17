"""Quick policy-divergence check at real compression scale (1024 tokens)."""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
os.environ.setdefault("HF_ENDPOINT", "https://hf-mirror.com")

import torch

from sage.engine import Engine
from sage.policies import make_policy

MODEL = "/home/z/my-project/models/gpt2"

eng = Engine(MODEL, chunk=64, threads=2)
tok = eng.tokenizer
text = ("Natural language processing has changed dramatically over the past "
        "five years. Transformer models now dominate nearly every benchmark. "
        "The key innovation was attention, which lets tokens interact "
        "directly across arbitrary distances. ")
ids = tok(text * 90, return_tensors="pt").input_ids[:, :1024]
print("seq:", ids.shape)

for name in ["streamingllm", "h2o", "pyramidkv", "reverse-pyramid", "sage",
             "sage-nodecay", "sage-uniform"]:
    pol = make_policy(name, eng.L)
    eng.reset()
    nll, cnt = eng.teacher_forced(ids, pol, 0.2)
    ppl = nll / max(cnt, 1)
    print(f"{name:>16s}: NLL/tok={ppl:.6f}")
