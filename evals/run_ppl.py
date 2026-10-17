"""WikiText-2 perplexity protocol (chunked teacher forcing, honest accounting).

All methods run in ONE harness with identical retained-entry budgets at
every step. Results are checkpointed as JSON (resume-safe).
"""
import argparse
import glob
import json
import math
import os
import sys
import time

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
os.environ.setdefault("HF_ENDPOINT", "https://hf-mirror.com")

import numpy as np
import pandas as pd
import torch

from sage.engine import Engine
from sage.policies import make_policy

RESULTS = "/home/z/my-project/sage2/results/ppl"


def load_wikitext2(tokenizer, window: int, n_seqs: int):
    parquet = "/home/z/my-project/models/wikitext2-test.parquet"
    df = pd.read_parquet(parquet)
    text = "\n".join(str(r) for r in df["text"].tolist())
    ids = tokenizer(text, return_tensors="pt", add_special_tokens=False).input_ids[0]
    n = (ids.shape[0] // window) * window
    seqs = ids[:n].view(-1, window)
    if n_seqs > seqs.shape[0]:
        n_seqs = seqs.shape[0]
    return seqs[:n_seqs]


def run_config(engine_path, model_tag, policy_name, rho, seqs, chunk,
               save_log_first=True, gamma=None, tau=None, recent=32, sink=4):
    out = os.path.join(
        RESULTS, f"{model_tag}__{policy_name}__r{rho}__g{gamma}__t{tau}.json")
    if os.path.exists(out):
        return json.load(open(out))
    eng = Engine(engine_path, chunk=chunk, threads=2)
    kw = {}
    if gamma is not None:
        kw["gamma"] = gamma
    if tau is not None:
        kw["tau"] = tau
    if recent is not None:
        kw["recent"] = recent
    if sink is not None:
        kw["sink"] = sink
    pol_name = "sage" if policy_name == "full" else policy_name
    pol = make_policy(pol_name, eng.L, **kw)
    if policy_name == "full":
        rho = 1.0
    total_nll, total_cnt = 0.0, 0
    t0 = time.perf_counter()
    log = eng.new_log(pol, rho, int(seqs.shape[1]))
    log_path = out.replace(".json", ".accounting.json")
    for i in range(seqs.shape[0]):
        eng.reset()
        nll, cnt = eng.teacher_forced(
            torch.tensor(seqs[i].tolist()).unsqueeze(0), pol, rho,
            log=log if i == 0 else None)
        total_nll += nll
        total_cnt += cnt
    dt = time.perf_counter() - t0
    res = {
        "model": model_tag, "policy": policy_name, "rho": rho,
        "gamma": gamma, "tau": tau, "recent": recent, "sink": sink,
        "n_seqs": int(seqs.shape[0]), "n_tokens": int(total_cnt),
        "avg_nll": total_nll / max(total_cnt, 1),
        "ppl": math.exp(total_nll / max(total_cnt, 1)),
        "wall_s": dt, "tok_s": total_cnt / dt,
        "budget_violations": log.budget_violations,
    }
    with open(out, "w") as f:
        json.dump(res, f, indent=2)
    if save_log_first:
        log.seq_len = int(seqs.shape[1])
        log.dump(log_path)
    # free memory
    del eng
    return res


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--model", default="gpt2",
                    choices=["gpt2", "qwen05b"])
    ap.add_argument("--grid", default="main")
    args = ap.parse_args()

    os.makedirs(RESULTS, exist_ok=True)
    if args.model == "gpt2":
        engine_path = "/home/z/my-project/models/gpt2"
        window, n_seqs, chunk = 1024, 32, 64
    else:
        engine_path = "/home/z/my-project/models/qwen05b"
        window, n_seqs, chunk = 2048, 10, 64

    from transformers import AutoTokenizer
    tok = AutoTokenizer.from_pretrained(engine_path)
    seqs = load_wikitext2(tok, window, n_seqs)
    print(f"[{args.model}] {seqs.shape[0]} sequences x {seqs.shape[1]} tokens")

    main_policies = ["full", "streamingllm", "h2o", "pyramidkv",
                     "reverse-pyramid", "sage", "sage-nodecay", "sage-uniform"]
    curve_policies = ["h2o", "pyramidkv", "sage"]
    curve_rhos = [0.05, 0.1, 0.3]
    sens_gammas = [0.98, 0.99, 0.999, 1.0]
    sens_taus = [0.5, 1.0, 2.0]

    if args.grid == "main":
        jobs = []
        for p in main_policies:
            rho = 1.0 if p == "full" else 0.2
            jobs.append(dict(policy_name=p, rho=rho))
        for p in curve_policies:
            for r in curve_rhos:
                jobs.append(dict(policy_name=p, rho=r))
        for j in jobs:
            r = run_config(engine_path, args.model, j["policy_name"],
                           j["rho"], seqs, chunk)
            print(f"[{args.model}] {j['policy_name']:>16s} rho={j['rho']} "
                  f"PPL={r['ppl']:.3f} viol={r['budget_violations']} "
                  f"({r['wall_s']:.0f}s)", flush=True)
    elif args.grid == "sensitivity":
        # gamma scan (tau=1.5 default) - note gamma applies to SAGE family
        for g in sens_gammas:
            name = "sage" if g != 1.0 else "sage-nodecay"
            r = run_config(engine_path, args.model, "sage", 0.2, seqs[:16],
                           chunk, gamma=g)
            print(f"[{args.model}] gamma={g} PPL={r['ppl']:.3f}", flush=True)
        for tv in sens_taus:
            r = run_config(engine_path, args.model, "sage", 0.2, seqs[:16],
                           chunk, tau=tv)
            print(f"[{args.model}] tau={tv} PPL={r['ppl']:.3f}", flush=True)
        r = run_config(engine_path, args.model, "sage-nosink", 0.2, seqs[:16], chunk)
        print(f"[{args.model}] nosink PPL={r['ppl']:.3f}", flush=True)
        r = run_config(engine_path, args.model, "sage-norecent", 0.2, seqs[:16], chunk)
        print(f"[{args.model}] norecent PPL={r['ppl']:.3f}", flush=True)
    print("PPL_GRID_DONE")


if __name__ == "__main__":
    main()
