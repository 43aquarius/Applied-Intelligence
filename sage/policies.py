"""Eviction policies: SAGE (ours) + faithful StreamingLLM / H2O / PyramidKV.

All policies share the same CompressedCache and the SAME exact-budget
projector (sage.allocation.capped_waterfilling), so every method in the
comparison holds an IDENTICAL number of retained KV entries at every step
(Theorem 1). Methods differ ONLY in (i) their importance scores and
(ii) their layer-weight profile. This isolates the design questions the
paper studies. Auxiliary memory (scores/bookkeeping) is accounted
separately and reported.
"""
from __future__ import annotations

import numpy as np

from .allocation import capped_waterfilling, pyramid_weights, uniform_weights


class Policy:
    """Base class. Subclasses fill in scoring and layer weighting."""

    name = "base"
    needs_scores = True
    uses_sinks = True
    uses_recent = True
    adaptive = False  # True => maintain entropy signal for layer weights

    def __init__(self, L: int, sink: int = 4, recent: int = 32,
                 gamma: float = 1.0, tau: float = 1.5, beta: float = 0.9):
        self.L = L
        self.sink = sink
        self.recent = recent
        self.gamma = gamma          # per-token decay (SAGE ACS; 1.0 = H2O)
        self.tau = tau              # entropy exponent (SAGE LABA)
        self.beta = beta            # EMA smoothing for the entropy signal
        self.kappa = np.ones(L, dtype=np.float64)  # dispersion signal (EMA)

    # ------------------------------------------------------------------
    # scoring
    # ------------------------------------------------------------------
    def observe(self, probs_per_layer, q_len: int):
        """Update scores and dispersion signals.

        probs_per_layer: list of L arrays, each (k_total,) = per-token
        attention mass received by the LAST query of the chunk, averaged
        over query heads (the engine supplies this; chunk-internal
        accumulation is handled by the engine's score buffer).
        Also updates kappa (normalised entropy, EMA-smoothed) unless the
        policy overrides ``update_kappa`` to False.
        """
        if self.needs_scores:
            raise NotImplementedError
        self.update_kappa_signals(probs_per_layer)

    def update_kappa_signals(self, probs_per_layer):
        for l, p in enumerate(probs_per_layer):
            if p is None or p.size < 2:
                continue
            p = np.asarray(p, dtype=np.float64)
            p = p / max(p.sum(), 1e-12)
            h = -(p * np.log(p + 1e-12)).sum()
            h_norm = h / np.log(p.size)
            self.kappa[l] = self.beta * self.kappa[l] + (1 - self.beta) * h_norm

    # ------------------------------------------------------------------
    # layer weighting
    # ------------------------------------------------------------------
    def weights(self) -> np.ndarray:
        return uniform_weights(self.L)

    # ------------------------------------------------------------------
    # budget vector
    # ------------------------------------------------------------------
    def budgets(self, t: int, rho: float, protected_floor: int) -> np.ndarray:
        """Exact-budget allocation at step t (t = absolute sequence length).

        The global contract is B_eff(t) = max(rho*L*t, L*min(protected, t)):
        a proportional memory contract with a constant warmup allowance of
        the protected region (documented in the paper). All methods face
        the same B_eff. The computed total is stored in self.last_nominal
        for the accounting log."""
        lower = np.full(self.L, min(protected_floor, t), dtype=np.int64)
        upper = np.full(self.L, t, dtype=np.int64)
        B_prop = int(rho * self.L * t)
        B = max(B_prop, int(lower.sum()))
        self.last_nominal = B
        return capped_waterfilling(self.weights(), lower, upper, B)

    # ------------------------------------------------------------------
    # token selection
    # ------------------------------------------------------------------
    def select_keep(self, positions: np.ndarray, scores: np.ndarray,
                    budget: int, t: int) -> np.ndarray:
        """Return a boolean mask of which retained tokens to keep.

        positions: sorted absolute positions currently cached in the layer.
        scores: aligned importance scores (may be None if !needs_scores).
        budget: exact per-layer budget after projection.
        t: current absolute length (= positions[-chunck...] context).
        """
        n = positions.shape[0]
        if budget >= n:
            return np.ones(n, dtype=bool)
        keep = np.zeros(n, dtype=bool)
        # protected: sinks (first self.sink absolute positions) + recent
        if self.uses_sinks:
            keep |= positions < self.sink
        if self.uses_recent:
            recent_pos = positions > (t - 1 - self.recent)
            keep |= recent_pos
        n_protected = int(keep.sum())
        room = budget - n_protected
        if room <= 0:
            # protection alone meets/exceeds budget: keep protection only
            if n_protected > budget:  # cannot happen: floors >= protection
                order = np.argsort(positions)
                keep = np.zeros(n, dtype=bool)
                keep[order[:budget]] = True
            return keep
        evictable = ~keep
        idx_ev = np.where(evictable)[0]
        if scores is None or not self.needs_scores:
            # pure recency fallback (StreamingLLM-style): keep newest
            idx_keep = idx_ev[np.argsort(-positions[idx_ev], kind="stable")][:room]
        else:
            idx_keep = idx_ev[np.argsort(-scores[idx_ev], kind="stable")][:room]
        keep[idx_keep] = True
        return keep


class SAGEPolicy(Policy):
    """SAGE v2: decayed cumulative scoring (ACS) + entropy-adaptive exact
    layer budgets (LABA) + sink/recent protection (DRE)."""

    name = "sage"
    needs_scores = True
    uses_sinks = True
    uses_recent = True
    adaptive = True

    def __init__(self, L, sink=4, recent=32, gamma=0.995, tau=1.5, beta=0.9):
        super().__init__(L, sink, recent, gamma, tau, beta)

    def weights(self) -> np.ndarray:
        w = np.power(np.maximum(self.kappa, 0.0) + 1e-6, self.tau)
        s = w.sum()
        if s <= 0:
            return uniform_weights(self.L)
        return w / s


class SAGENoDecay(SAGEPolicy):
    name = "sage-nodecay"  # gamma = 1 (pure H2O-style accumulation)
    adaptive = True

    def __init__(self, L, sink=4, recent=32, tau=1.5, beta=0.9):
        super().__init__(L, sink, recent, gamma=1.0, tau=tau, beta=beta)


class SAGEUniformBudget(SAGEPolicy):
    name = "sage-uniform"  # tau = 0 -> uniform layer weights (still exact)
    adaptive = False  # uniform weights: no entropy signal needed

    def __init__(self, L, sink=4, recent=32, gamma=0.995, beta=0.9):
        super().__init__(L, sink, recent, gamma=gamma, tau=0.0, beta=beta)


class SAGENoSink(SAGEPolicy):
    name = "sage-nosink"
    uses_sinks = False

    def __init__(self, L, sink=4, recent=32, gamma=0.995, tau=1.5, beta=0.9):
        super().__init__(L, sink=0, recent=recent, gamma=gamma, tau=tau, beta=beta)


class SAGENoRecent(SAGEPolicy):
    name = "sage-norecent"
    uses_recent = False

    def __init__(self, L, sink=4, recent=32, gamma=0.995, tau=1.5, beta=0.9):
        super().__init__(L, sink=sink, recent=0, gamma=gamma, tau=tau, beta=beta)


class StreamingLLMPolicy(Policy):
    """Sinks + growing recent window; no importance scores.

    With total budget b_l the cache keeps the first ``sink`` tokens plus
    the (b_l - sink) most recent tokens, which reduces to standard
    StreamingLLM when the budget is constant."""

    name = "streamingllm"
    needs_scores = False
    uses_sinks = True
    uses_recent = True

    def __init__(self, L, sink=4, recent=0):
        super().__init__(L, sink=sink, recent=10**9)  # window grows to budget

    def budgets(self, t, rho, protected_floor):
        lower = np.full(self.L, min(self.sink, t), dtype=np.int64)
        upper = np.full(self.L, t, dtype=np.int64)
        B_prop = int(rho * self.L * t)
        B = max(B_prop, int(lower.sum()))
        self.last_nominal = B
        return capped_waterfilling(uniform_weights(self.L), lower, upper, B)

    def select_keep(self, positions, scores, budget, t):
        n = positions.shape[0]
        if budget >= n:
            return np.ones(n, dtype=bool)
        keep = positions < self.sink
        room = budget - int(keep.sum())
        if room > 0:
            idx = np.where(~keep)[0]
            idx_keep = idx[np.argsort(-positions[idx], kind="stable")][:room]
            keep[idx_keep] = True
        return keep


class H2OPolicy(Policy):
    """Heavy-hitter accumulation (no decay) + recent window + sinks,
    uniform layer budgets."""

    name = "h2o"
    needs_scores = True
    uses_sinks = True
    uses_recent = True

    def __init__(self, L, sink=4, recent=32):
        super().__init__(L, sink=sink, recent=recent, gamma=1.0)


class PyramidKVPolicy(Policy):
    """Static pyramidal layer profile (more cache to lower layers) with
    cumulative scoring; the profile enters through the SAME exact-budget
    projector, so PyramidKV also respects the global contract exactly."""

    name = "pyramidkv"
    needs_scores = True
    uses_sinks = True
    uses_recent = True

    def __init__(self, L, sink=4, recent=32, shape="pyramid"):
        super().__init__(L, sink=sink, recent=recent, gamma=1.0)
        self.shape = shape
        self._w = pyramid_weights(L, shape)

    def weights(self) -> np.ndarray:
        return self._w


class ReversePyramidPolicy(PyramidKVPolicy):
    name = "reverse-pyramid"  # control condition

    def __init__(self, L, sink=4, recent=32):
        super().__init__(L, sink=sink, recent=recent, shape="reverse-pyramid")


def make_policy(name: str, L: int, **kw) -> Policy:
    table = {
        "sage": SAGEPolicy,
        "sage-nodecay": SAGENoDecay,
        "sage-uniform": SAGEUniformBudget,
        "sage-nosink": SAGENoSink,
        "sage-norecent": SAGENoRecent,
        "streamingllm": StreamingLLMPolicy,
        "h2o": H2OPolicy,
        "pyramidkv": PyramidKVPolicy,
        "reverse-pyramid": ReversePyramidPolicy,
    }
    if name not in table:
        raise KeyError(f"unknown policy {name}; have {sorted(table)}")
    return table[name](L, **kw)
