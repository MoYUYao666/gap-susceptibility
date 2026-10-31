"""A1 #4：TauMonitor —— 训练期零开销 τ 监控回调（代码先行，未执行、未接入训练）。

思路（A1 §5.5 结论的工程化）：
  1. 训练前用冻结模型在验证集上算一次 top-5 类别集与冻结分数（precompute，一次性）；
  2. 每个 epoch 用当前微调模型的图像嵌入 + 类别文本嵌入算 top-5 集上的 Kendall τ；
  3. 早停逻辑：τ 相对历史最大值的平台化（默认 3 个 epoch 不创新高即触发），
     可在 τ 开始侵蚀、top-1 仍平坦时提前叫停（A1：τ 第 3 epoch 降、top-1 到第 10 epoch 都不动）。

零开销论证：验证时本来就要算相似度矩阵拿 top-k 类集，τ 只是同一矩阵上的
top-5 子块的 Kendall 系数——O(5 log 5) 每样本，无额外前向。

用法示例（接入现有训练循环的伪代码）：
    mon = TauMonitor(frozen_text_features, val_topk5_sets, patience=3)
    for epoch in ...:
        img_feats = encoder(images)            # 微调模型图像嵌入
        tau = mon.step(img_feats)              # 返回本 epoch 的平均 τ
        if mon.should_stop():
            break

依赖：torch, numpy, scipy。不导入模型、不下载权重。
"""
from __future__ import annotations

import numpy as np
from scipy import stats


def kendall_tau_topk(ranks_a: np.ndarray, ranks_b: np.ndarray) -> float:
    """两组 top-k 排序（同一样本）的 Kendall τ。ranks: 长度为 k 的类别索引序列。"""
    assert ranks_a.shape == ranks_b.shape
    k = ranks_a.shape[0]
    if k < 2:
        return 1.0
    r1 = np.empty(k)
    r2 = np.empty(k)
    # 用各自序列的位置作为秩
    r1[ranks_a] = np.arange(k)
    r2[ranks_b] = np.arange(k)
    if np.std(r1) < 1e-12 or np.std(r2) < 1e-12:
        return 1.0
    t, _ = stats.kendalltau(r1, r2)
    return float(t) if np.isfinite(t) else 0.0


class TauMonitor:
    """训练期 τ 监控 + 早停。"""

    def __init__(self, frozen_text_features, val_topk5_sets, patience: int = 3,
                 min_epochs: int = 1, verbose: bool = True):
        """
        frozen_text_features: [K, D] 归一化类别文本嵌入（冻结模型，一次性）。
        val_topk5_sets:       [N, 5] 冻结模型在验证集每张图像上的 top-5 类别索引
                              （一次性；同时可缓存冻结分数 [N, 5] 省掉重复取数）。
        patience: τ 平台化容忍的 epoch 数（不创新高）。
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
        """image_feats: [N, D] 当前微调模型的验证集图像嵌入（调用方负责归一化）。
        返回本 epoch 平均 τ。"""
        S = image_feats @ self.text_feats.T          # [N, K]
        S = S.cpu().numpy() if hasattr(S, 'cpu') else S
        taus = []
        for i in range(self.n_val):
            k5 = self.topk5[i]
            # 约定：topk5 按冻结分数降序存储（precompute_frozen 保证）
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
        """τ 平台化（连续 patience 个 epoch 不创新高）且超过 min_epochs 时触发。"""
        return (len(self.history) >= self.min_epochs
                and self.epochs_since_best >= self.patience)


def precompute_frozen(encoder_fn, text_feats, val_loader, k: int = 5):
    """一次性：用冻结模型算验证集 top-k 类别集（按分数降序）。
    encoder_fn(images) -> [N, D] 归一化图像嵌入；text_feats: [K, D]。
    训练前调用一次，结果喂给 TauMonitor。"""
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
    # 自检（不涉模型）：随机秩与打乱秩的 τ 应在 1 附近/明显更低
    rng = np.random.RandomState(0)
    a = np.array([3, 1, 4, 2, 0])
    print('self τ:', kendall_tau_topk(a, a.copy()))
    print('random τ:', kendall_tau_topk(a, rng.permutation(a)))
    print('reversed τ:', kendall_tau_topk(a, a[::-1]))
