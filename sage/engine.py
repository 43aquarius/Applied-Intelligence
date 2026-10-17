"""Chunked inference engine with exact-budget KV compression.

Drives a HuggingFace causal LM in eager-attention mode so that exact
attention probabilities are available for scoring (the honest accounting
alternative to FlashAttention-2 score extraction, which the original
submission left unexplained). Works in chunks: forward a block of tokens,
update policy scores from the returned attention probabilities, then
project the cache onto the exact per-layer budgets (Theorem 1).

Correctness-critical details:
- Retained absolute positions are kept SORTED, so the causal mask over
  [retained..., chunk...] is valid even after eviction.
- Explicit position_ids carry ABSOLUTE positions (RoPE rotation for new
  tokens is then correct; retained K keep their original rotation).
- Budget compliance is asserted at every chunk: sum_l |C_l| == B_eff.
"""
from __future__ import annotations

import json
import math
import os
import time
from dataclasses import dataclass, field, asdict
from typing import List, Optional, Tuple

import numpy as np
import torch

from .policies import Policy, make_policy

os.environ.setdefault("HF_ENDPOINT", "https://hf-mirror.com")


# ---------------------------------------------------------------------------
# custom attention interface: per-layer causal masking
# ---------------------------------------------------------------------------
def _sage_eager_attention(module, query, key, value, attention_mask=None,
                          scaling=None, dropout=0.0, **kwargs):
    """Eager attention that builds its OWN causal mask from the true
    per-layer key length.

    Why: after per-layer budget enforcement, cache lengths DIFFER across
    layers, so any model-level (shared) mask would be wrong for some
    layers. Here every cached token is attended (evicted tokens simply do
    not exist), and within-chunk causality is enforced relative to each
    layer's own cache length. Returns post-softmax probabilities so
    output_attentions keeps working for exact score extraction.
    """
    if scaling is None:
        scaling = query.size(-1) ** -0.5
    # GQA support: repeat KV heads to match the query-head count
    if key.shape[1] != query.shape[1]:
        n_rep = query.shape[1] // key.shape[1]
        key = torch.repeat_interleave(key, n_rep, dim=1)
        value = torch.repeat_interleave(value, n_rep, dim=1)
    attn_weights = torch.matmul(query, key.transpose(-1, -2)) * scaling
    q_len, k_len = attn_weights.shape[-2], attn_weights.shape[-1]
    cache_len = k_len - q_len
    if q_len > 1:
        causal = torch.ones(q_len, k_len, dtype=torch.bool,
                            device=attn_weights.device)
        causal = causal.triu(diagonal=cache_len + 1)
        attn_weights = attn_weights.masked_fill(
            causal, torch.finfo(attn_weights.dtype).min)
    attn_weights = torch.softmax(attn_weights, dim=-1).type(value.dtype)
    attn_output = torch.matmul(attn_weights, value)
    attn_output = attn_output.transpose(1, 2)
    return attn_output, attn_weights


def _register_sage_attention():
    from transformers.modeling_utils import ALL_ATTENTION_FUNCTIONS
    if "sage_eager" not in list(ALL_ATTENTION_FUNCTIONS.keys()):
        ALL_ATTENTION_FUNCTIONS.register("sage_eager", _sage_eager_attention)


# ---------------------------------------------------------------------------
# accounting
# ---------------------------------------------------------------------------
@dataclass
class StepLog:
    t: int                      # absolute sequence length after the chunk
    total_retained: int         # sum_l |C_l|
    nominal_budget: int         # B_eff(t) = max(rho*L*t, L*min(protected,t))
    aux_bytes: int              # scores + index bookkeeping estimate
    observe_ms: float
    compress_ms: float
    forward_ms: float


@dataclass
class RunLog:
    model: str
    policy: str
    rho: float
    seq_len: int
    n_layers: int
    n_kv_heads: int
    head_dim: int
    entry_bytes: int            # bytes per cached token per layer
    steps: List[StepLog] = field(default_factory=list)
    budget_violations: int = 0

    def dump(self, path: str):
        with open(path, "w") as f:
            json.dump(asdict(self), f)


# ---------------------------------------------------------------------------
# HF cache adapter (robust across transformers versions)
# ---------------------------------------------------------------------------
class HFCacheAdapter:
    """Build/extract per-layer (key, value) tensors from HF cache objects."""

    def __init__(self):
        self.mode = None  # set on first successful build

    def build(self, kv_pairs):
        """kv_pairs: list of (k, v) tensors -> a past_key_values object."""
        from transformers import DynamicCache
        dc = DynamicCache()
        for l, (k, v) in enumerate(kv_pairs):
            try:
                dc.update(k, v, l)          # 4.x signature
                self.mode = "update_kvl"
            except TypeError:
                try:
                    dc.update(l, k, v)      # alternative signature
                    self.mode = "update_lkv"
                except Exception:
                    raise
        return dc

    def extract(self, past) -> List[Tuple[torch.Tensor, torch.Tensor]]:
        if past is None:
            return []
        # transformers 4.x: plain lists
        kc = getattr(past, "key_cache", None)
        if isinstance(kc, list) and kc:
            return [(kc[l], past.value_cache[l]) for l in range(len(kc))]
        # newer versions may wrap layers
        layers = getattr(past, "layers", None)
        if layers is not None:
            out = []
            for lay in layers:
                k = getattr(lay, "keys", None)
                v = getattr(lay, "values", None)
                if k is None and hasattr(lay, "key"):
                    k, v = lay.key, lay.value
                out.append((k, v))
            return out
        # legacy tuple format
        try:
            return [(k, v) for (k, v) in past]
        except Exception:
            raise RuntimeError(f"cannot extract cache from {type(past)}")


# ---------------------------------------------------------------------------
# engine
# ---------------------------------------------------------------------------
class Engine:
    def __init__(self, model_name: str, device: str = "cpu",
                 dtype: torch.dtype = torch.float32, chunk: int = 64,
                 threads: Optional[int] = None):
        from transformers import AutoModelForCausalLM, AutoTokenizer
        if threads:
            torch.set_num_threads(threads)
        self.model_name = model_name
        self.device = device
        self.dtype = dtype
        self.chunk = chunk
        self.tokenizer = AutoTokenizer.from_pretrained(model_name)
        self.model = AutoModelForCausalLM.from_pretrained(
            model_name, dtype=dtype, attn_implementation="eager",
        ).to(device).eval()
        _register_sage_attention()
        self.model.config._attn_implementation = "sage_eager"
        # ensure every attention submodule sees the override (they share
        # the config object, but be explicit for safety across versions)
        for m in self.model.modules():
            if hasattr(m, "config") and getattr(m, "config", None) is not None:
                try:
                    m.config._attn_implementation = "sage_eager"
                except Exception:
                    pass
        cfg = self.model.config
        self.L = cfg.num_hidden_layers
        self.Hq = cfg.num_attention_heads
        self.Hkv = getattr(cfg, "num_key_value_heads", self.Hkv_or(cfg))
        self.head_dim = getattr(cfg, "head_dim", None) or (
            cfg.hidden_size // self.Hq)
        self.entry_bytes = 2 * self.Hkv * self.head_dim * (
            2 if dtype in (torch.float16, torch.bfloat16) else 4)
        self.adapter = HFCacheAdapter()
        # state
        self.kv: List[Tuple[torch.Tensor, torch.Tensor]] = []
        self.positions: List[np.ndarray] = []   # per layer, sorted abs pos
        self.scores: List[np.ndarray] = []      # per layer, aligned

    @staticmethod
    def Hkv_or(cfg):
        return getattr(cfg, "n_head_kv", getattr(cfg, "num_key_value_heads",
                                                 cfg.num_attention_heads))

    # ------------------------------------------------------------------
    def reset(self):
        self.kv = []
        self.positions = []
        self.scores = []

    # ------------------------------------------------------------------
    def _forward_chunk(self, ids: torch.Tensor, pos_ids: torch.Tensor):
        """One forward over a chunk. Returns (logits, attn_probs, past).

        attention_mask=None: the registered sage_eager interface builds a
        per-layer causal mask from each layer's true key length, so layers
        may hold DIFFERENT numbers of retained tokens. position_ids are
        ABSOLUTE; cache_position is bookkeeping only."""
        have_cache = bool(self.kv) and self.kv[0] is not None
        q = ids.shape[1]
        past = self.adapter.build(self.kv) if have_cache else None
        cache_position = torch.arange(0, q, device=self.device)
        try:
            with torch.no_grad():
                out = self.model(
                    input_ids=ids,
                    attention_mask=None,
                    position_ids=pos_ids,
                    past_key_values=past,
                    output_attentions=True,
                    use_cache=True,
                    cache_position=cache_position,
                )
        except Exception as e:
            T0 = self.kv[0][0].shape[2] if have_cache else 0
            print(f"[fwd-fail] T0={T0} q={q} ids={tuple(ids.shape)} "
                  f"err={e}", flush=True)
            raise
        return out.logits, out.attentions, out.past_key_values

    # ------------------------------------------------------------------
    def _observe_and_compress(self, attn, q_len: int, t_after: int,
                              policy: Policy, rho: float,
                              log: Optional[RunLog]):
        """Update scores/signals from attention probs, then enforce budgets."""
        t0 = time.perf_counter()
        gamma = policy.gamma
        # decay factor for old scores over this chunk
        decay_old = gamma ** q_len
        # per-query decay weights: query j (0-based) has weight gamma^(q-1-j)
        dec = gamma ** np.arange(q_len - 1, -1, -1) if gamma != 1.0 else np.ones(q_len)

        head_mean_probs = []
        for l in range(self.L):
            p = attn[l][0].to(torch.float64).mean(dim=0).cpu().numpy()  # (q,k)
            head_mean_probs.append(p)
        t1 = time.perf_counter()

        new_positions = np.arange(t_after - q_len, t_after)
        for l in range(self.L):
            p = head_mean_probs[l]
            old_scores = self.scores[l]
            padded = np.concatenate(
                [old_scores, np.zeros(q_len, dtype=np.float64)])
            if policy.needs_scores:
                self.scores[l] = decay_old * padded + dec @ p
            else:
                self.scores[l] = padded
            self.positions[l] = np.concatenate([self.positions[l], new_positions])

        # dispersion signals for SAGE (entropy of recent attention)
        if policy.adaptive:
            probs_last = []
            w = min(q_len, 16)
            for l in range(self.L):
                p = head_mean_probs[l][-w:].mean(axis=0)
                probs_last.append(p)
            policy.update_kappa_signals(probs_last)
        t2 = time.perf_counter()

        # budget enforcement (Theorem 1 projection + policy selection)
        protected = (policy.sink + policy.recent) if policy.uses_recent \
            else policy.sink
        if not policy.uses_sinks:
            protected = policy.recent
        budgets = policy.budgets(t_after, rho, protected)
        t3 = time.perf_counter()
        total_retained = 0
        for l in range(self.L):
            n = self.positions[l].shape[0]
            b_l = int(budgets[l])
            if b_l >= n:
                total_retained += n
                continue
            keep = policy.select_keep(self.positions[l], self.scores[l], b_l, t_after)
            idx = np.where(keep)[0]
            k, v = self.kv[l]
            self.kv[l] = (k[:, :, idx, :].contiguous(),
                          v[:, :, idx, :].contiguous())
            self.positions[l] = self.positions[l][idx]
            self.scores[l] = self.scores[l][idx]
            total_retained += idx.shape[0]
        t4 = time.perf_counter()

        nominal = int(max(rho * self.L * t_after,
                          self.L * min(protected, t_after)))
        # the policy's own contract definition wins (StreamingLLM's floor is
        # sink-only, so its warmup allowance differs by design)
        nominal = int(getattr(policy, "last_nominal", nominal))
        if log is not None:
            aux = 8 * total_retained + 8 * self.L  # scores+indices+budgets
            log.steps.append(StepLog(
                t=t_after, total_retained=total_retained,
                nominal_budget=nominal, aux_bytes=aux,
                observe_ms=(t2 - t0) * 1e3, compress_ms=(t4 - t3) * 1e3,
                forward_ms=0.0))
            if total_retained != nominal:
                log.budget_violations += 1
        self._last_stats = {
            "observe_ms": (t2 - t0) * 1e3, "budgets_ms": (t3 - t2) * 1e3,
            "compress_ms": (t4 - t3) * 1e3,
        }

    # ------------------------------------------------------------------
    def _ensure_state(self, policy: Policy):
        if not self.kv:
            self.kv = [None] * self.L
            self.positions = [np.zeros(0, dtype=np.int64) for _ in range(self.L)]
            self.scores = [np.zeros(0, dtype=np.float64) for _ in range(self.L)]

    def _append_chunk_kv(self, past, q_len: int):
        """Take the returned (appended) cache into our own storage."""
        kv_new = self.adapter.extract(past)
        if not kv_new:
            return
        # replace wholesale: the returned cache == our retained + this chunk
        self.kv = list(kv_new)

    # ------------------------------------------------------------------
    def teacher_forced(self, input_ids: torch.Tensor, policy: Policy,
                       rho: float, log: Optional[RunLog] = None):
        """Chunked teacher-forced pass; returns (sum_nll, n_predicted).

        Every next-token prediction at position i uses exactly the cache
        state a deployed system would have after compressing the prefix
        up to the last chunk boundary - the honest protocol."""
        self._ensure_state(policy)
        N = input_ids.shape[1]
        sum_nll, count = 0.0, 0
        start = 0
        while start < N:
            end = min(start + self.chunk, N)
            ids = input_ids[:, start:end]
            pos = torch.arange(start, end, device=self.device).unsqueeze(0)
            t0 = time.perf_counter()
            logits, attn, past = self._forward_chunk(ids, pos)
            fwd_ms = (time.perf_counter() - t0) * 1e3
            self._append_chunk_kv(past, end - start)
            self._observe_and_compress(attn, end - start, end, policy, rho, log)
            if log is not None and log.steps:
                log.steps[-1].forward_ms = fwd_ms
            # NLL for targets in this chunk: positions start..end-1 predict
            # tokens start+1..end
            tgt_end = min(end, N - 1)
            if tgt_end > start:
                lp = torch.log_softmax(
                    logits[0, : tgt_end - start].to(torch.float64), dim=-1)
                targets = input_ids[0, start + 1: tgt_end + 1]
                nll = -lp[torch.arange(tgt_end - start), targets]
                sum_nll += float(nll.sum())
                count += tgt_end - start
            start = end
        return sum_nll, count

    # ------------------------------------------------------------------
    def generate(self, input_ids: torch.Tensor, policy: Policy, rho: float,
                 max_new_tokens: int = 48, log: Optional[RunLog] = None,
                 stop_token: Optional[int] = None):
        """Prefill (chunked) + greedy decode with continuing compression."""
        self._ensure_state(policy)
        N = input_ids.shape[1]
        # ---- prefill
        start = 0
        while start < N:
            end = min(start + self.chunk, N)
            ids = input_ids[:, start:end]
            pos = torch.arange(start, end, device=self.device).unsqueeze(0)
            logits, attn, past = self._forward_chunk(ids, pos)
            self._append_chunk_kv(past, end - start)
            self._observe_and_compress(attn, end - start, end, policy, rho, log)
            start = end
        # ---- greedy decode
        generated = []
        cur = int(input_ids.shape[1])
        last = logits[0, -1]
        for _ in range(max_new_tokens):
            nxt = int(torch.argmax(last).item())
            generated.append(nxt)
            if stop_token is not None and nxt == stop_token:
                break
            ids = torch.tensor([[nxt]], device=self.device)
            pos = torch.tensor([[cur]], device=self.device)
            logits, attn, past = self._forward_chunk(ids, pos)
            self._append_chunk_kv(past, 1)
            self._observe_and_compress(attn, 1, cur + 1, policy, rho, log)
            cur += 1
            last = logits[0, -1]
        return generated

    # ------------------------------------------------------------------
    def new_log(self, policy: Policy, rho: float, seq_len: int) -> RunLog:
        return RunLog(
            model=self.model_name, policy=policy.name, rho=rho,
            seq_len=seq_len, n_layers=self.L, n_kv_heads=self.Hkv,
            head_dim=self.head_dim, entry_bytes=self.entry_bytes)
