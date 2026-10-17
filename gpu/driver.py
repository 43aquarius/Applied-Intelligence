#!/usr/bin/env python3
"""SAGE-v2 GPU replication driver (Kaggle T4 x2 / any CUDA device).

Scales the CPU study (GPT-2-124M, Qwen2.5-0.5B) to Qwen2.5-1.5B-Instruct and
Qwen2.5-3B-Instruct with the IDENTICAL engine, policies, matched-entry
protocol, and JSON result schema.

Phases per model (all checkpointed to results_gpu/, resumable):
  P1 correctness gate  - chunked == full forward; all policies budget-exact
  P2 PPL main grid     - 8 policies @ rho=0.2 (WikiText-2, window x n_seqs)
  P3 PPL budget curve  - h2o/pyramidkv/sage @ rho in {0.05, 0.1, 0.3}
  P4 sensitivity       - gamma scan, tau scan, nosink, norecent (1.5B only)
  P5 needle suite      - single-needle 2048 (5 depths x 2 trials) + 4096
                         (3 depths x 1 trial) + multi-needle (2048/4096)
  P6 summary           - aggregate tables + environment report

Resource discipline: single "Save & Run All" commit; the script terminates
by itself; nothing runs interactively.

Env overrides for local testing:
  SAGE_DRIVER_TEST=1          tiny config on local Qwen2.5-0.5B (CPU)
  SAGE_REPO_PATH=<dir>        use a local repo checkout instead of git clone
"""
import gc
import glob
import json
import math
import os
import subprocess
import sys
import time

# ---------------------------------------------------------------------------
# configuration
# ---------------------------------------------------------------------------
KAGGLE = os.path.isdir("/kaggle/working")
TEST = os.environ.get("SAGE_DRIVER_TEST") == "1"

if KAGGLE:
    WORK = "/kaggle/working"
    os.environ["HF_ENDPOINT"] = "https://huggingface.co"
else:
    WORK = os.environ.get("SAGE_DRIVER_WORK",
                          "/home/z/my-project/sage2/gpu_local_test")

os.makedirs(WORK, exist_ok=True)
RESULTS = os.path.join(WORK, "results_gpu")
REPO_URL = "https://github.com/43aquarius/Applied-Intelligence.git"
DEADLINE_S = 8.0 * 3600  # hard self-imposed cap (Kaggle session is 9h)

MAIN_POLICIES = ["full", "streamingllm", "h2o", "pyramidkv",
                 "reverse-pyramid", "sage", "sage-nodecay", "sage-uniform"]
CURVE_POLICIES = ["h2o", "pyramidkv", "sage"]
CURVE_RHOS = [0.05, 0.1, 0.3]
SENS_GAMMAS = [0.98, 0.99, 0.999, 1.0]
SENS_TAUS = [0.5, 1.0, 2.0]
NEEDLE_METHODS = ["full", "streamingllm", "h2o", "pyramidkv", "sage"]
MULTI_METHODS = ["full", "h2o", "pyramidkv", "sage", "sage-nodecay"]

if TEST:
    MODELS = [dict(tag="qwen05b-test", repo_id="local",
                   path="/home/z/my-project/models/qwen05b",
                   window=512, n_seqs=2, chunk=64,
                   ppl_main=True, ppl_curve=True, sens=False,
                   needle=True, needle_4096=False, multi=False)]
else:
    MODELS = [
        dict(tag="qwen15b", repo_id="Qwen/Qwen2.5-1.5B-Instruct", path=None,
             window=2048, n_seqs=10, chunk=64,
             ppl_main=True, ppl_curve=True, sens=True,
             needle=True, needle_4096=True, multi=True),
        dict(tag="qwen3b", repo_id="Qwen/Qwen2.5-3B-Instruct", path=None,
             window=2048, n_seqs=10, chunk=64,
             ppl_main=True, ppl_curve=False, sens=False,
             needle=True, needle_4096=False, multi=True),
    ]

T0 = time.time()


def log(msg):
    print(f"[{time.time() - T0:8.0f}s] {msg}", flush=True)


def time_left():
    return DEADLINE_S - (time.time() - T0)


def out_of_time():
    return time_left() <= 0


# ---------------------------------------------------------------------------
# environment / repo setup
# ---------------------------------------------------------------------------
def ensure_stack():
    """Use the image's preinstalled transformers 5.x as-is.

    NEVER pip-install a different transformers into a process that has
    already imported it (v1 lesson: pip replaces files on disk while the
    lazy-module state in memory belongs to the old version -> mixed-version
    ImportError). Only if the preinstalled major version is < 5 do we
    install and then os.execv into a CLEAN process.
    """
    from importlib.metadata import version as pkgver
    try:
        v = pkgver("transformers")
    except Exception:
        v = "0"
    major = int(v.split(".")[0]) if v.split(".")[0].isdigit() else 0
    if major >= 5:
        return v, False
    if os.environ.get("SAGE_STACK_REEXEC") == "1":
        raise RuntimeError(f"transformers still <5 after install (got {v})")
    subprocess.run([sys.executable, "-m", "pip", "install", "-q",
                    "transformers>=5.16,<6"],
                   check=False, timeout=1800)
    os.environ["SAGE_STACK_REEXEC"] = "1"
    os.execv(sys.executable, [sys.executable, os.path.abspath(__file__)])


def setup_env():
    import torch
    preinstalled, _ = ensure_stack()
    env = {
        "kaggle": KAGGLE,
        "test_mode": TEST,
        "torch": torch.__version__,
        "cuda_available": torch.cuda.is_available(),
        "gpu": (torch.cuda.get_device_name(0)
                if torch.cuda.is_available() else None),
        "gpu_count": torch.cuda.device_count() if torch.cuda.is_available() else 0,
        "gpu_mem_gb": (round(torch.cuda.get_device_properties(0).total_memory / 1e9, 2)
                       if torch.cuda.is_available() else 0),
        "transformers_preinstalled": preinstalled,
    }
    import transformers
    env["transformers"] = transformers.__version__
    json.dump(env, open(os.path.join(RESULTS, "env.json"), "w"), indent=2)
    log("ENV: " + json.dumps(env))
    return env


def get_repo():
    """Clone (or refresh) the SAGE-v2 research repo; returns its path.

    The clone is refreshed (fetch + reset --hard) on every run so that
    engine fixes pushed to GitHub are picked up even when /kaggle/working
    persists an older clone from a previous version."""
    local = os.environ.get("SAGE_REPO_PATH")
    if local and os.path.isdir(os.path.join(local, "sage")):
        return local
    dst = os.path.join(WORK, "Applied-Intelligence")
    if os.path.isdir(os.path.join(dst, "sage")):
        r = subprocess.run(
            ["git", "-C", dst, "fetch", "--depth", "1", "origin", "main"],
            capture_output=True, text=True, timeout=300)
        if r.returncode == 0:
            subprocess.run(["git", "-C", dst, "reset", "--hard", "FETCH_HEAD"],
                           capture_output=True, text=True, timeout=120)
            log("repo refreshed to origin/main")
        else:
            log("repo refresh failed (using existing clone): " + r.stderr[-200:])
        return dst
    r = subprocess.run(["git", "clone", "--depth", "1", REPO_URL, dst],
                       capture_output=True, text=True, timeout=600)
    if r.returncode != 0:
        raise RuntimeError("git clone failed: " + r.stderr[-500:])
    return dst


def resolve_model(spec):
    """Return a local filesystem path for the model."""
    if spec.get("path"):
        return spec["path"]
    from huggingface_hub import snapshot_download
    for attempt in range(4):
        try:
            p = snapshot_download(
                spec["repo_id"],
                allow_patterns=["*.json", "*.safetensors", "tokenizer*",
                                "merges*", "vocab*", "*.model", "*.txt"],
                max_workers=4)
            return p
        except Exception as e:
            log(f"snapshot_download retry {attempt}: {e!r}")
            time.sleep(10)
    raise RuntimeError(f"could not fetch {spec['repo_id']}")


def get_wikitext_parquet():
    """Download the WikiText-2 raw test parquet (same file as CPU study)."""
    dst = os.path.join(WORK, "wikitext2-test.parquet")
    if os.path.exists(dst) and os.path.getsize(dst) > 100_000:
        return dst
    url = (os.environ.get("HF_ENDPOINT", "https://huggingface.co")
           + "/datasets/Salesforce/wikitext/resolve/main/"
             "wikitext-2-raw-v1/test-00000-of-00001.parquet")
    r = subprocess.run(["curl", "-sL", "--retry", "4", "-m", "600",
                        url, "-o", dst], capture_output=True, text=True)
    if r.returncode != 0 or not os.path.exists(dst) or \
            os.path.getsize(dst) < 100_000:
        raise RuntimeError("wikitext parquet download failed")
    return dst


# ---------------------------------------------------------------------------
# experiment runners (schemas identical to the CPU evals)
# ---------------------------------------------------------------------------
def load_wikitext2(tokenizer, window, n_seqs, parquet):
    import pandas as pd
    df = pd.read_parquet(parquet)
    text = "\n".join(str(r) for r in df["text"].tolist())
    ids = tokenizer(text, return_tensors="pt",
                    add_special_tokens=False).input_ids[0]
    n = (ids.shape[0] // window) * window
    seqs = ids[:n].view(-1, window)
    return seqs[:min(n_seqs, seqs.shape[0])]


def run_ppl_config(eng, model_tag, policy_name, rho, seqs, chunk,
                   gamma=None, tau=None, recent=32, sink=4):
    import torch
    out = os.path.join(
        RESULTS, "ppl",
        f"{model_tag}__{policy_name}__r{rho}__g{gamma}__t{tau}.json")
    if os.path.exists(out):
        return json.load(open(out))
    kw = {}
    if gamma is not None:
        kw["gamma"] = gamma
    if tau is not None:
        kw["tau"] = tau
    kw.update(recent=recent, sink=sink)
    pol = make_policy("sage" if policy_name == "full" else policy_name,
                      eng.L, **kw)
    eff_rho = 1.0 if policy_name == "full" else rho
    total_nll, total_cnt = 0.0, 0
    t0 = time.perf_counter()
    log_obj = eng.new_log(pol, eff_rho, int(seqs.shape[1]))
    for i in range(seqs.shape[0]):
        eng.reset()
        nll, cnt = eng.teacher_forced(
            torch.tensor(seqs[i].tolist()).unsqueeze(0), pol, eff_rho,
            log=log_obj if i == 0 else None)
        total_nll += nll
        total_cnt += cnt
    dt = time.perf_counter() - t0
    res = {
        "model": model_tag, "policy": policy_name, "rho": eff_rho,
        "gamma": gamma, "tau": tau, "recent": recent, "sink": sink,
        "n_seqs": int(seqs.shape[0]), "n_tokens": int(total_cnt),
        "avg_nll": total_nll / max(total_cnt, 1),
        "ppl": math.exp(total_nll / max(total_cnt, 1)),
        "wall_s": dt, "tok_s": total_cnt / dt,
        "budget_violations": log_obj.budget_violations,
    }
    os.makedirs(os.path.dirname(out), exist_ok=True)
    json.dump(res, open(out, "w"), indent=2)
    log_obj.seq_len = int(seqs.shape[1])
    log_obj.dump(out.replace(".json", ".accounting.json"))
    eng.reset()
    return res


def correctness_gate(eng, seq_len=256):
    """Chunked no-compression forward must match the full forward."""
    import torch
    tok = eng.tokenizer
    text = "The quick brown fox jumps over the lazy dog. " * 200
    ids = tok(text, return_tensors="pt").input_ids[:, :seq_len]
    ids_d = ids.to(eng.device)
    with torch.no_grad():
        full = eng.model(input_ids=ids_d, output_attentions=False).logits
        lp = torch.log_softmax(full[0, :-1].to(torch.float64), dim=-1)
        full_nll = -lp[torch.arange(seq_len - 1, device=eng.device),
                       ids_d[0, 1:]].sum().item()
    pol = make_policy("sage", eng.L)
    eng.reset()
    nll, cnt = eng.teacher_forced(ids, pol, 1.0)
    rel = abs(nll - full_nll) / max(abs(full_nll), 1e-9)
    log(f"GATE chunked={nll:.6f} full={full_nll:.6f} rel={rel:.2e}")
    if rel > 2e-3:
        raise RuntimeError(f"chunked-vs-full mismatch rel={rel:.2e}")
    # quick all-policy budget-exactness check
    for name in ["sage", "h2o", "streamingllm", "pyramidkv",
                 "reverse-pyramid", "sage-nodecay", "sage-uniform"]:
        pol = make_policy(name, eng.L)
        lg = eng.new_log(pol, 0.3, seq_len)
        eng.reset()
        eng.teacher_forced(ids, pol, 0.3, lg)
        last = lg.steps[-1]
        assert lg.budget_violations == 0, f"{name} BUDGET VIOLATION"
        assert last.total_retained == last.nominal_budget, \
            f"{name} retained {last.total_retained} != {last.nominal_budget}"
        log(f"GATE {name:>16s}: retained={last.total_retained} "
            f"nominal={last.nominal_budget} OK")
    eng.reset()
    return True


def run_needle_suite(eng, model_tag, with_4096, with_multi):
    from needle_fns import build_prompt, run_case
    tok = eng.tokenizer
    if TEST:
        lengths = [(512, [0, 50], 1)]
    else:
        lengths = [(2048, [0, 25, 50, 75, 100], 2)]
    if with_4096 and not TEST:
        lengths.append((4096, [0, 50, 100], 1))
    for length, depths, trials in lengths:
        for trial in range(trials):
            seed = 1000 * trial + length
            for d in depths:
                ids, spans, codes, _ = build_prompt(tok, length, d, seed + d)
                for m in NEEDLE_METHODS:
                    if out_of_time():
                        log("deadline hit - skipping remaining needle")
                        return
                    out_f = os.path.join(
                        RESULTS, "needle",
                        f"{model_tag}__L{length}__d{d}__t{trial}__{m}.json")
                    if os.path.exists(out_f):
                        continue
                    rho = 1.0 if m == "full" else 0.2
                    pol = make_policy("sage" if m == "full" else m, eng.L)
                    r = run_case(eng, pol, rho, ids, spans, codes)
                    r.update(dict(model=model_tag, length=length, depth=d,
                                  trial=trial, method=m, multi=False,
                                  codes=codes))
                    os.makedirs(os.path.dirname(out_f), exist_ok=True)
                    json.dump(r, open(out_f, "w"), indent=2)
                    log(f"needle {model_tag} L{length} d{d:3d} t{trial} "
                        f"{m:>14s}: hit={r['hits'][0]} "
                        f"ret={r['retention_mean']}")
    if with_multi:
        lens = ([2048, 4096] if with_4096 else [2048]) if not TEST else [512]
        for length in lens:
            for trial in range(1):
                seed = 1000 * trial + length
                ids, spans, codes, _ = build_prompt(tok, length, 0, seed,
                                                    multi=True)
                for m in MULTI_METHODS:
                    if out_of_time():
                        return
                    out_f = os.path.join(
                        RESULTS, "needle",
                        f"{model_tag}__multi__L{length}__t{trial}__{m}.json")
                    if os.path.exists(out_f):
                        continue
                    rho = 1.0 if m == "full" else 0.2
                    pol = make_policy("sage" if m == "full" else m, eng.L)
                    r = run_case(eng, pol, rho, ids, spans, codes)
                    r.update(dict(model=model_tag, length=length, trial=trial,
                                  method=m, multi=True, codes=codes))
                    json.dump(r, open(out_f, "w"), indent=2)
                    log(f"multi {model_tag} L{length} {m:>14s}: "
                        f"hit={r['hit_rate']:.2f}")


# ---------------------------------------------------------------------------
# summary
# ---------------------------------------------------------------------------
def summarize():
    lines = ["# SAGE-v2 GPU replication — summary", ""]
    env_p = os.path.join(RESULTS, "env.json")
    if os.path.exists(env_p):
        env = json.load(open(env_p))
        lines += [f"- GPU: {env.get('gpu')} x{env.get('gpu_count')} "
                  f"({env.get('gpu_mem_gb')} GB)",
                  f"- torch {env.get('torch')} | transformers {env.get('transformers')}",
                  ""]
    for tag in [m["tag"] for m in MODELS]:
        ppl_files = sorted(glob.glob(os.path.join(
            RESULTS, "ppl", f"{tag}__*.json")))
        ppl_files = [f for f in ppl_files if "accounting" not in f]
        if ppl_files:
            lines += [f"## PPL — {tag}", "",
                      "| policy | rho | gamma | tau | PPL | violations |",
                      "|---|---|---|---|---|---|"]
            rows = []
            for f in ppl_files:
                r = json.load(open(f))
                rows.append((r["policy"], r["rho"], r["gamma"], r["tau"],
                             r["ppl"], r["budget_violations"]))
            for p, rho, g, tau, ppl, v in sorted(rows):
                lines.append(f"| {p} | {rho} | {g} | {tau} | {ppl:.3f} | {v} |")
            lines.append("")
        nd_files = sorted(glob.glob(os.path.join(
            RESULTS, "needle", f"{tag}__*.json")))
        if nd_files:
            agg = {}
            for f in nd_files:
                r = json.load(open(f))
                key = (r["method"], r["length"], r.get("multi", False))
                a = agg.setdefault(key, {"hits": [], "ret": []})
                a["hits"].append(r["hit_rate"])
                if r.get("retention_mean") is not None:
                    a["ret"].append(r["retention_mean"])
            lines += [f"## Needle — {tag}", "",
                      "| method | L | multi | mean hit-rate | mean retention |",
                      "|---|---|---|---|---|"]
            for (m, L, multi), a in sorted(agg.items()):
                mh = sum(a["hits"]) / len(a["hits"])
                mr = (sum(a["ret"]) / len(a["ret"])) if a["ret"] else float("nan")
                lines.append(f"| {m} | {L} | {multi} | {mh:.3f} | {mr:.3f} |")
            lines.append("")
    txt = "\n".join(lines)
    open(os.path.join(RESULTS, "SUMMARY.md"), "w").write(txt)
    print(txt)
    log("SUMMARY written")


# ---------------------------------------------------------------------------
# main
# ---------------------------------------------------------------------------
def main():
    os.makedirs(RESULTS, exist_ok=True)
    setup_env()
    repo = get_repo()
    sys.path.insert(0, repo)

    global Engine, make_policy
    from sage.engine import Engine
    from sage.policies import make_policy
    # reuse the CPU study's needle protocol verbatim
    nd_src = os.path.join(repo, "evals", "run_needle.py")
    import importlib.util
    spec = importlib.util.spec_from_file_location("needle_fns", nd_src)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    sys.modules["needle_fns"] = mod

    import torch
    device = "cuda:0" if torch.cuda.is_available() else "cpu"
    log(f"device = {device}")
    if device == "cpu" and not TEST:
        raise RuntimeError("no CUDA device available on a full run")

    parquet = get_wikitext_parquet()

    for spec_m in MODELS:
        if out_of_time():
            log("deadline hit before model phase")
            break
        tag = spec_m["tag"]
        log(f"===== MODEL {tag} ({spec_m['repo_id']}) =====")
        errf = os.path.join(RESULTS, f"{tag}__ERROR.json")
        if os.path.exists(errf):
            os.remove(errf)
        path = resolve_model(spec_m)
        eng = Engine(path, device=device, dtype=torch.float32,
                     chunk=spec_m["chunk"])
        log(f"loaded: L={eng.L} Hq={eng.Hq} Hkv={eng.Hkv} "
            f"head_dim={eng.head_dim}")
        try:
            correctness_gate(eng, seq_len=256)
            seqs = load_wikitext2(eng.tokenizer, spec_m["window"],
                                  spec_m["n_seqs"], parquet)
            log(f"wikitext: {seqs.shape[0]} x {seqs.shape[1]} tokens")

            if spec_m["ppl_main"]:
                for p in MAIN_POLICIES:
                    if out_of_time():
                        break
                    rho = 1.0 if p == "full" else 0.2
                    r = run_ppl_config(eng, tag, p, rho, seqs, spec_m["chunk"])
                    log(f"PPL {tag} {p:>16s} rho={rho}: {r['ppl']:.3f} "
                        f"viol={r['budget_violations']} ({r['wall_s']:.0f}s)")
            if spec_m["ppl_curve"]:
                for p in CURVE_POLICIES:
                    for rho in CURVE_RHOS:
                        if out_of_time():
                            break
                        r = run_ppl_config(eng, tag, p, rho, seqs,
                                           spec_m["chunk"])
                        log(f"PPL {tag} {p:>10s} rho={rho}: {r['ppl']:.3f} "
                            f"({r['wall_s']:.0f}s)")
            if spec_m["sens"]:
                for g in SENS_GAMMAS:
                    if out_of_time():
                        break
                    r = run_ppl_config(eng, tag, "sage", 0.2, seqs,
                                       spec_m["chunk"], gamma=g)
                    log(f"SENS {tag} gamma={g}: {r['ppl']:.3f}")
                for tv in SENS_TAUS:
                    if out_of_time():
                        break
                    r = run_ppl_config(eng, tag, "sage", 0.2, seqs,
                                       spec_m["chunk"], tau=tv)
                    log(f"SENS {tag} tau={tv}: {r['ppl']:.3f}")
                for ab in ["sage-nosink", "sage-norecent"]:
                    if out_of_time():
                        break
                    r = run_ppl_config(eng, tag, ab, 0.2, seqs, spec_m["chunk"])
                    log(f"SENS {tag} {ab}: {r['ppl']:.3f}")
            if spec_m["needle"]:
                run_needle_suite(eng, tag, spec_m["needle_4096"],
                                 spec_m["multi"])
        except Exception as e:
            import traceback
            traceback.print_exc()
            json.dump({"model": tag, "error": repr(e)},
                      open(os.path.join(RESULTS, f"{tag}__ERROR.json"), "w"))
        finally:
            eng.reset()
            del eng
            gc.collect()
            if torch.cuda.is_available():
                torch.cuda.empty_cache()
            log(f"model {tag} unloaded")

    summarize()
    log("ALL DONE")


if __name__ == "__main__":
    main()
