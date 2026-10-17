"""Needle-in-a-haystack retrieval on Qwen2.5-0.5B-Instruct (chat template).

Protocol:
- Haystack: seeded distractor sentences (non-degenerate, varied).
- Needle: a 7-digit secret code inserted at depth d% of the haystack.
- Question appended as the final user turn; greedy decode <= 32 tokens.
- Exact-match scoring + per-layer needle-retention diagnostics from the
  cache manager (was the needle still cached at the end of prefill?).

Multi-needle variant: three codes at depths {15, 50, 85}%, asking for all
three (partial credit per code) - the "multi-instruction robustness" probe.
"""
import argparse
import json
import os
import random
import sys
import time

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
os.environ.setdefault("HF_ENDPOINT", "https://hf-mirror.com")

import torch

from sage.engine import Engine
from sage.policies import make_policy

RESULTS = "/home/z/my-project/sage2/results/needle"
MODEL = "/home/z/my-project/models/qwen05b"

ADJ = ["quiet", "ancient", "little", "modern", "distant", "narrow", "bright",
       "empty", "hidden", "silver", "sudden", "gentle", "cold", "warm"]
NOUN = ["river", "market", "village", "library", "harbor", "meadow",
        "station", "garden", "bridge", "museum", "forest", "harvest",
        "ladder", "window", "morning", "evening", "winter", "summer"]
VERB = ["crossed", "watched", "remembered", "measured", "followed",
        "painted", "counted", "visited", "described", "guarded"]
PREP = ["near", "beyond", "beside", "under", "across", "before"]


def make_haystack(n_sentences: int, seed: int):
    rng = random.Random(seed)
    out = []
    for _ in range(n_sentences):
        out.append(
            f"The {rng.choice(ADJ)} {rng.choice(NOUN)} {rng.choice(VERB)} "
            f"the {rng.choice(ADJ)} {rng.choice(NOUN)} {rng.choice(PREP)} "
            f"the {rng.choice(NOUN)}.")
    return " ".join(out)


NEEDLE_TMPL = (
    "One of the secret codes hidden in the documents is {code}. "
    "Please remember the secret code {code}. ")
QUESTION = ("Question: What is the secret code mentioned in the text above? "
            "Answer with the code only.")
MULTI_QUESTION = ("Question: What are the three secret codes mentioned in "
                  "the text above? Answer with the three codes in the order "
                  "they appeared, separated by single spaces.")


def build_prompt(tok, target_len, depth_pct, seed, multi=False):
    """Returns (input_ids, needle_spans, prompt_text)."""
    rng = random.Random(seed)
    codes = [str(rng.randint(1000000, 9999999)) for _ in range(3 if multi else 1)]
    question = MULTI_QUESTION if multi else QUESTION

    def full_text(n_sent):
        hay = make_haystack(n_sent, seed)
        if multi:
            parts = []
            thirds = [hay[: len(hay) * 1 // 3], hay[len(hay) * 1 // 3: len(hay) * 2 // 3],
                      hay[len(hay) * 2 // 3:]]
            depths3 = [0.15, 0.50, 0.85]
            for c, part, d in zip(codes, thirds, depths3):
                cut = int(len(part) * d)
                parts.append(part[:cut] + NEEDLE_TMPL.format(code=c) + part[cut:])
            body = "".join(parts)
        else:
            cut = int(len(hay) * depth_pct / 100. * 0.97 + len(hay) * 0.015)
            body = hay[:cut] + NEEDLE_TMPL.format(code=codes[0]) + hay[cut:]
        return body + "\n\n" + question

    # size the haystack so the chat-templated prompt is ~target_len tokens
    n_sent = max(8, int(target_len / 18))
    for _ in range(14):
        text = full_text(n_sent)
        msgs = [{"role": "user", "content": text}]
        # tokenize=False + explicit tokenization (transformers 5.x returns a
        # BatchEncoding dict from tokenize=True, whose len() is the number
        # of keys, not tokens)
        rendered = tok.apply_chat_template(
            msgs, tokenize=False, add_generation_prompt=True)
        prompt = tok(rendered, add_special_tokens=False).input_ids
        if len(prompt) >= target_len:
            break
        n_sent = int(n_sent * (target_len / max(len(prompt), 1)) * 1.02) + 1
    # locate needle token spans (search each code in token space)
    ids = torch.tensor(prompt).unsqueeze(0)
    spans = []
    flat = prompt
    for c in codes:
        # find the LAST occurrence (the "remember" sentence)
        ctok = tok(" " + c, add_special_tokens=False).input_ids
        for start in range(len(flat) - len(ctok), -1, -1):
            if flat[start:start + len(ctok)] == ctok:
                spans.append((start, start + len(ctok)))
                break
    return ids, spans, codes, prompt


def run_case(eng, pol, rho, ids, spans, codes, max_new=32):
    eng.reset()
    log = eng.new_log(pol, rho, int(ids.shape[1]))
    t0 = time.perf_counter()
    eos = eng.tokenizer.eos_token_id
    gen = eng.generate(ids, pol, rho, max_new_tokens=max_new, log=log,
                       stop_token=eos)
    dt = time.perf_counter() - t0
    text = eng.tokenizer.decode(gen, skip_special_tokens=True)
    hits = [1 if c in text else 0 for c in codes]
    # needle retention at end of prefill (last prefill step = t == ids len)
    prefill_steps = [s for s in log.steps if s.t <= ids.shape[1]]
    retention = []
    if spans:
        for l in range(eng.L):
            pos = eng.positions[l]
            keep = 0
            tot = 0
            for (a, b) in spans:
                for p in range(a, b):
                    tot += 1
                    if (pos == p).any():
                        keep += 1
            retention.append(keep / max(tot, 1))
    return {
        "hits": hits, "hit_rate": sum(hits) / max(len(hits), 1),
        "gen": text[:120], "retention_mean": (sum(retention) / len(retention))
        if retention else None,
        "retention_per_layer": [round(r, 3) for r in retention],
        "wall_s": dt, "prompt_len": int(ids.shape[1]),
        "violations": log.budget_violations,
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--lengths", default="2048,4096")
    ap.add_argument("--depths", default="0,25,50,75,100")
    ap.add_argument("--trials", type=int, default=2)
    ap.add_argument("--methods", default="full,streamingllm,h2o,pyramidkv,sage")
    ap.add_argument("--rho", type=float, default=0.2)
    ap.add_argument("--multi", action="store_true")
    args = ap.parse_args()

    os.makedirs(RESULTS, exist_ok=True)
    lengths = [int(x) for x in args.lengths.split(",")]
    depths = [int(x) for x in args.depths.split(",")]
    methods = args.methods.split(",")
    trials = args.trials

    eng = Engine(MODEL, chunk=64, threads=2)
    tok = eng.tokenizer
    print("Qwen loaded:", eng.L, "layers, Hkv", eng.Hkv)

    for length in lengths:
        for trial in range(trials):
            seed = 1000 * trial + length
            if args.multi:
                ids, spans, codes, _ = build_prompt(tok, length, 0, seed, multi=True)
                for m in methods:
                    out_f = os.path.join(
                        RESULTS, f"multi__L{length}__t{trial}__{m}.json")
                    if os.path.exists(out_f):
                        continue
                    rho = 1.0 if m == "full" else args.rho
                    pol = make_policy("sage" if m == "full" else m, eng.L)
                    r = run_case(eng, pol, rho, ids, spans, codes)
                    r.update(dict(length=length, trial=trial, method=m,
                                  multi=True, codes=codes))
                    json.dump(r, open(out_f, "w"), indent=2)
                    print(f"multi L{length} t{trial} {m:>14s}: "
                          f"hit={r['hit_rate']:.2f} ret={r['retention_mean']}",
                          flush=True)
            else:
                for d in depths:
                    ids, spans, codes, _ = build_prompt(
                        tok, length, d, seed + d)
                    for m in methods:
                        out_f = os.path.join(
                            RESULTS, f"L{length}__d{d}__t{trial}__{m}.json")
                        if os.path.exists(out_f):
                            continue
                        rho = 1.0 if m == "full" else args.rho
                        pol = make_policy("sage" if m == "full" else m, eng.L)
                        r = run_case(eng, pol, rho, ids, spans, codes)
                        r.update(dict(length=length, depth=d, trial=trial,
                                      method=m, multi=False, codes=codes))
                        json.dump(r, open(out_f, "w"), indent=2)
                        print(f"L{length} d{d:3d} t{trial} {m:>14s}: "
                              f"hit={r['hits'][0]} ret={r['retention_mean']}",
                              flush=True)
    print("NEEDLE_DONE")


if __name__ == "__main__":
    main()
