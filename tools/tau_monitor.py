"""A1 #4: TauMonitor — zero-overhead τ monitoring callback during training (code first, not executed, not wired into training).

Idea (engineering the conclusion of A1 §5.5):
  1. Before training, compute the top-5 class sets and frozen scores on the validation set with the frozen model (precompute, one-off);
  2. Each epoch, compute Kendall τ on the top-5 sets using the current fine-tuned model's image embeddings + class text embeddings;
  3. Early stopping: plateauing of τ relative to its historical maximum (by default triggers after 3 epochs without a new high),
     which can stop early when τ starts eroding while top-1 is still flat (A1: τ drops at epoch 3, top-1 does not move until epoch 10).

Zero-overhead argument: validation already computes the similarity matrix to get the top-k class sets, and τ is just the
Kendall coefficient over the top-5 sub-block of that same matrix — O(5 log 5) per sample, no extra forward pass.

Usage example (pseudocode for wiring into an existing training loop):
    mon = TauMonitor(frozen_text_features, val_topk5_sets, patience=3)
    for epoch in ...:
        img_feats = encoder(images)            # fine-tuned model image embeddings
        tau = mon.step(img_feats)              # returns this epoch's mean τ
        if mon.should_stop():
            break

Dependencies: torch, numpy, scipy. Does not import models or download weights.
"""
from __future__ import annotations

import numpy as np
from scipy import stats


def kendall_tau_topk(ranks_a: np.ndarray, ranks_b: np.ndarray) -> float:
    """Kendall τ between two top-k rankings (same sample). ranks: a length-k sequence of class indices."""
    assert ranks_a.shape == ranks_b.shape
    k = ranks_a.shape[0]
    if k < 2:
        return 1.0
    r1 = np.empty(k)
    r2 = np.empty(k)
    # Use each sequence's position as the rank
    r1[ranks_a] = np.arange(k)
    r2[ranks_b] = np.arange(k)
    if np.std(r1) < 1e-12 or np.std(r2) < 1e-12:
        return 1.0
    t, _ = stats.kendalltau(r1, r2)
    return float(t) if np.isfinite(t) else 0.0


class TauMonitor:
    """τ monitoring + early stopping during training."""

    def __init__(self, frozen_text_features, val_topk5_sets, patience: int = 3,
                 min_epochs: int = 1, verbose: bool = True):
        """
        frozen_text_features: [K, D] normalized class text embeddings (frozen model, one-off).
        val_topk5_sets:       [N, 5] top-5 class indices of the frozen model for each validation image
                              (one-off; the frozen scores [N, 5] can also be cached to avoid recomputation).
        patience: number of epochs τ may plateau (no new high).
        """
        self.text_feats = frozen_text_features
        self.topk5 = np.asarray(val_topk5_sets)
        self.n_val = self.topk5.shape[0]
        self.patience = patience
        self.min_epochs = min_epochs
        self.verbose = verbose
        self.history: list[float] = []
        self.best_tau = -1.0
        self.epochs_since_best = 0

    def step(self, image_feats) -> float:
        """image_feats: [N, D] validation image embeddings of the current fine-tuned model (the caller normalizes them).
        Returns this epoch's mean τ."""
        S = image_feats @ self.text_feats.T          # [N, K]
        S = S.cpu().numpy() if hasattr(S, 'cpu') else S
        taus = []
        for i in range(self.n_val):
            k5 = self.topk5[i]
            # Convention: topk5 is stored in descending frozen-score order (guaranteed by precompute_frozen)
            frozen_order = k5
            cur_order = k5[np.argsort(-S[i][k5])]
            t = kendall_tau_topk(frozen_order, cur_order)
            if np.isfinite(t):
                taus.append(t)
        tau = float(np.mean(taus)) if taus else 0.0
        self.history.append(tau)
        if tau > self.best_tau + 1e-6:
            self.best_tau = tau
            self.epochs_since_best = 0
        else:
            self.epochs_since_best += 1
        if self.verbose:
            print('[TauMonitor] epoch %d: tau=%.4f (best %.4f, plateau %d/%d)' %
                  (len(self.history), tau, self.best_tau,
                   self.epochs_since_best, self.patience), flush=True)
        return tau

    def should_stop(self) -> bool:
        """Triggered when τ plateaus (no new high for patience consecutive epochs) and min_epochs is exceeded."""
        return (len(self.history) >= self.min_epochs
                and self.epochs_since_best >= self.patience)


def precompute_frozen(encoder_fn, text_feats, val_loader, k: int = 5):
    """One-off: compute the validation top-k class sets with the frozen model (sorted by descending score).
    encoder_fn(images) -> [N, D] normalized image embeddings; text_feats: [K, D].
    Call once before training and feed the result to TauMonitor."""
    topk_sets, topk_scores = [], []
    for images in val_loader:
        feats = encoder_fn(images)
        S = feats @ text_feats.T
        idx = np.argsort(-S.cpu().numpy() if hasattr(S, 'cpu') else -S, axis=1)[:, :k]
        topk_sets.append(idx)
        topk_scores.append(np.take_along_axis(S.cpu().numpy() if hasattr(S, 'cpu') else S,
                                              idx, axis=1))
    return np.concatenate(topk_sets), np.concatenate(topk_scores)


if __name__ == '__main__':
    # Self-check (no model involved): τ of an identical rank vs a shuffled rank should be near 1 / clearly lower
    rng = np.random.RandomState(0)
    a = np.array([3, 1, 4, 2, 0])
    print('self τ:', kendall_tau_topk(a, a.copy()))
    print('random τ:', kendall_tau_topk(a, rng.permutation(a)))
    print('reversed τ:', kendall_tau_topk(a, a[::-1]))
