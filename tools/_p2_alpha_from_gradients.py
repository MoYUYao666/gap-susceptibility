# -*- coding: utf-8 -*-
r"""**从梯度预测 α**（2026-10-07）——把 ODE 从"拟合"变成"预测"。

## 为什么这是本文最重要的补实验

`validation.tex` 图注：*"Solid curves: ODE predictions (α, β **fitted** over the full training
trajectory)"* → **R²=0.986 是两参数在完整轨迹上拟合的优度**，**任何指数收敛模型都会拟合得好**。
`docs/NEW_EXPERIMENTS_20261005.md` 自己写着这个缺口：*"拟合好 ≠ 推导对"*。

## 思路

梯度流恒等式（`theory.tex` 的 `eq:gradflow`）：

$$\frac{d(DG^*)}{dt} = -\eta\,\langle \nabla_\theta DG^*,\ \nabla_\theta \mathcal{L}\rangle$$

恒等式右端**可直接测量**（`_exp1_gradflow_identity.py` 已验证 cos=0.9977、中位误差 2.70%）。
而 ODE 写为 $d(DG^*)/dt = \alpha - \beta(DG^*-DG_0)$。

**→ 在初值附近（$DG^*\!\approx\!DG_0$，即 $\beta$ 项≈0）有 $\alpha = -\eta\langle \nabla DG^*, \nabla L\rangle$。**

**故本实验给出 α 的独立预测** $\hat\alpha = -\bar\eta \cdot \overline{\langle \nabla DG^*, \nabla L\rangle}$，
与**从轨迹拟合出的 α** 对比。

**β 不预测**：$\beta = \eta\,\partial\langle\cdot\rangle/\partial DG^*|_0$ 是景观曲率的二阶量，
单次梯度给不出 —— **如实标注为待定**，不假装。

## 判据（**事先写明**）

- corr(α̂, α_fit) > 0.7（跨 9 条轨迹）
- 中位相对误差 < 35%
- 两者**量级一致**（比值中位落在 [0.5, 2.0]）

## 口径

沿用既有轨迹：`rank=8`、`alpha_mult=2`、`batch=64`、`lr=1e-4`、AdamW+cosine、
`max_samples` 与 `_exp1` 一致（2000）。**逐 epoch** 在**同一批数据**上测内积，与主训练同 seed。

    python tools\_p2_alpha_from_gradients.py --apply
"""
from __future__ import annotations

import io
import json
import statistics as st
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO))
sys.path.insert(0, str(REPO / "src"))
sys.path.insert(0, str(REPO / "experiments"))

OUT = REPO / "outputs" / "theory" / "alpha_from_gradients"

RANK = 8
ALPHA_MULT = 2
BATCH = 64
MAX_SAMPLES = 2000
EPOCHS = 10
SEEDS = [42, 123, 456]
CONFIGS = {
    "text_only":   dict(apply_to_vision=False, apply_to_text=True),
    "both":        dict(apply_to_vision=True,  apply_to_text=True),
    "vision_only": dict(apply_to_vision=True,  apply_to_text=False),
}
PRISTINE = str(REPO / "models" / "clip-vit-base-patch32")


def grid_fit(t, y):
    """网格 β + 解析幅度 → (α, β, R²)。与 `_p1_ode_loco2.py` 同法。"""
    import numpy as np
    t = np.asarray(t, float); y = np.asarray(y, float)
    dg0 = float(y[0]); r = y - dg0
    best = (float("nan"), float("nan"), float("inf"))
    for logb in np.linspace(np.log10(0.005), np.log10(20.0), 800):
        b = 10.0 ** logb
        u = 1.0 - np.exp(-b * t)
        den = float((u * u).sum())
        if den < 1e-12:
            continue
        a = float((u * r).sum()) / den
        resid = float(((r - a * u) ** 2).sum())
        if resid < best[2]:
            best = (a * b, b, resid)
    A, B, _ = best
    yh = dg0 + (A / B) * (1.0 - np.exp(-B * t))
    ss = float(((y - y.mean()) ** 2).sum())
    R = 1.0 - float(((y - yh) ** 2).sum()) / ss if ss > 0 else float("nan")
    return float(A), float(B), float(R)


def main() -> int:
    apply = "--apply" in sys.argv
    smoke = "--smoke" in sys.argv
    # 配置可在命令行覆盖（操作者选 B：先只跑 both 臂）
    global EPOCHS, SEEDS, CONFIGS, MAX_SAMPLES
    if smoke:
        EPOCHS, SEEDS, MAX_SAMPLES = 1, [42], 128
        CONFIGS = {"text_only": dict(apply_to_vision=False, apply_to_text=True)}
        print("  [SMOKE] 1 臂 × 1 seed × 1 epoch × 128 样本")
    ALL_ARMS = {"text_only": dict(apply_to_vision=False, apply_to_text=True),
                "both":      dict(apply_to_vision=True,  apply_to_text=True),
                "vision_only": dict(apply_to_vision=True, apply_to_text=False)}
    if "--arms" in sys.argv:
        want = sys.argv[sys.argv.index("--arms") + 1].split(",")
        CONFIGS = {k: ALL_ARMS[k] for k in want if k in ALL_ARMS}
    if "--seeds" in sys.argv:
        SEEDS = [int(x) for x in sys.argv[sys.argv.index("--seeds") + 1].split(",")]
    if "--epochs" in sys.argv:
        EPOCHS = int(sys.argv[sys.argv.index("--epochs") + 1])
    if "--maxsamples" in sys.argv:
        MAX_SAMPLES = int(sys.argv[sys.argv.index("--maxsamples") + 1])
    print("=== 从梯度预测 α（把 ODE 从拟合变成预测）===")
    print(f"  rank={RANK} alpha={RANK*ALPHA_MULT} batch={BATCH} max_samples={MAX_SAMPLES} "
          f"epochs={EPOCHS} seeds={SEEDS}")
    if not apply:
        print("\n  （预演；加 --apply 实跑，需 GPU）")
        return 0

    import numpy as np
    import torch
    import torch.nn.functional as F

    from src.config import ExperimentConfig, LoRAConfig, TrainConfig
    from src.dataset import create_dataloaders
    from src.trainer import GapAwareTrainer, get_null_space_loss
    from experiments.strict_freeze_control import strict_freeze

    dev = "cuda" if torch.cuda.is_available() else "cpu"
    OUT.mkdir(parents=True, exist_ok=True)
    records = []

    for arm, flags in CONFIGS.items():
        for seed in SEEDS:
            torch.manual_seed(seed)
            lc = LoRAConfig(rank=RANK, alpha=RANK * ALPHA_MULT, **flags)
            cfg = ExperimentConfig(
                name="afg_%s" % arm, lora=lc,
                train=TrainConfig(dataset="flickr30k", batch_size=BATCH,
                                  num_epochs=EPOCHS, max_samples=MAX_SAMPLES,
                                  save_dir=str(OUT / arm), learning_rate=1e-4,
                                  clip_model=str(PRISTINE)))
            tr = GapAwareTrainer(cfg)
            tr.setup_model()
            n_tr = strict_freeze(tr)
            params = [p for p in tr.model.parameters() if p.requires_grad]
            assert params, f"{arm}: 无任何可训参数"

            loader, _, _ = create_dataloaders(
                dataset_name="flickr30k", data_dir=".", batch_size=BATCH,
                max_samples=MAX_SAMPLES)
            batch = next(iter(loader))
            images = batch["image"].to(dev)
            inp = {k: v.to(dev) for k, v in batch.items()
                   if k in ("input_ids", "attention_mask")}

            def fwd():
                o = tr.model(pixel_values=images, input_ids=inp["input_ids"],
                             attention_mask=inp["attention_mask"], return_loss=False)
                return (F.normalize(o.image_embeds, p=2, dim=-1),
                        F.normalize(o.text_embeds, p=2, dim=-1))

            def dg_s(ie, te):
                return ((ie - te) ** 2).sum(dim=-1).mean()

            def loss_of(ie, te):
                ls = tr.model.logit_scale.exp()
                lg = ls * ie @ te.t()
                lb = torch.arange(lg.shape[0], device=dev)
                L = (F.cross_entropy(lg, lb) + F.cross_entropy(lg.t(), lb)) / 2.0
                if tr.peft_method == "lora":
                    L = L + get_null_space_loss(tr.lora_layers)
                return L

            # ── 真实训练（按 trainer 的优化器/scheduler 构造），逐 epoch 记录
            opt = torch.optim.AdamW(params, lr=1e-4, weight_decay=0.01)
            from torch.optim.lr_scheduler import CosineAnnealingLR
            steps_per_ep = max(1, (MAX_SAMPLES or 31783) // BATCH)
            sched = CosineAnnealingLR(opt, T_max=steps_per_ep * EPOCHS)

            traj, inner_hist, lr_hist = [], [], []
            for ep in range(1, EPOCHS + 1):
                tr.model.train()
                ep_lrs = []
                for bi, b in enumerate(loader):
                    if MAX_SAMPLES and bi * BATCH >= MAX_SAMPLES:
                        break
                    im = b["image"].to(dev)
                    ip = {k: v.to(dev) for k, v in b.items()
                          if k in ("input_ids", "attention_mask")}

                    def fwd_b(im=im, ip=ip):
                        o = tr.model(pixel_values=im, input_ids=ip["input_ids"],
                                     attention_mask=ip["attention_mask"], return_loss=False)
                        return (F.normalize(o.image_embeds, p=2, dim=-1),
                                F.normalize(o.text_embeds, p=2, dim=-1))

                    # ∇DG*（在含 L2 归一化的计算图内求导，不 detach）
                    tr.model.zero_grad(set_to_none=True)
                    ie, te = fwd_b()
                    dg_s(ie, te).backward(retain_graph=True)
                    ga = torch.cat([p.grad.flatten() for p in params if p.grad is not None])
                    # ∇L（同一批）
                    tr.model.zero_grad(set_to_none=True)
                    ie2, te2 = fwd_b()
                    L = loss_of(ie2, te2)
                    L.backward()
                    gt = torch.cat([p.grad.flatten() for p in params if p.grad is not None])
                    inner = torch.dot(ga.detach(), gt.detach()).item()
                    opt.step(); sched.step()
                    ep_lrs.append(opt.param_groups[0]["lr"])
                    del ga, gt

                # epoch 末测 DG*
                tr.model.eval()
                with torch.no_grad():
                    ie, te = fwd()
                    traj.append(float(dg_s(ie, te).item()))
                inner_hist.append(inner)
                lr_hist.append(st.mean(ep_lrs))
                if ep % 2 == 0 or ep == 1:
                    print(f"  {arm:<12} seed={seed:<4} ep{ep:>2} DG*={traj[-1]:.4f} "
                          f"inner={inner:+.3e} lr={lr_hist[-1]:.2e}", flush=True)

            if len(traj) < 5:
                print(f"  [SMOKE] {arm}/{seed} 训练完成，DG* 轨迹 {traj}")
                A, B, R = float("nan"), float("nan"), float("nan")
            else:
                A, B, R = grid_fit(list(range(1, EPOCHS + 1)), traj)
            eta_bar = st.mean(lr_hist)
            alpha_hat = -eta_bar * st.mean(inner_hist)
            records.append(dict(arm=arm, seed=seed, n_trainable=n_tr,
                                traj=traj, inner=inner_hist, lr=lr_hist,
                                eta_bar=eta_bar, alpha_fit=A, beta_fit=B, R2_fit=R,
                                alpha_hat=alpha_hat))

    # 汇总
    af = [r["alpha_fit"] for r in records]
    ah = [r["alpha_hat"] for r in records]
    mf, mh = st.mean(af), st.mean(ah)
    sf = sum((x - mf) ** 2 for x in af) ** 0.5
    sh = sum((x - mh) ** 2 for x in ah) ** 0.5
    corr = (sum((x - mf) * (y - mh) for x, y in zip(af, ah)) / (sf * sh)) if sf and sh else float("nan")
    ratios = [h / f for h, f in zip(ah, af) if abs(f) > 1e-12]
    med_ratio = st.median(ratios) if ratios else float("nan")
    rel = [abs(h - f) / abs(f) for h, f in zip(ah, af) if abs(f) > 1e-12]
    med_rel = st.median(rel) if rel else float("nan")

    print("\n=== 汇总 ===")
    print(f"  n={len(records)} 条轨迹")
    print(f"  α_fit 均值 {mf:+.5f} ｜ α̂(梯度) 均值 {mh:+.5f}")
    print(f"  **corr(α̂, α_fit) = {corr:.4f}** ｜ 中位相对误差 {med_rel:.4f} ｜ 比值中位 {med_ratio:.3f}")
    print(f"  轨迹拟合 R² 均值 {st.mean([r['R2_fit'] for r in records]):.4f}")
    ok = (corr > 0.7) and (med_rel < 0.35) and (0.5 <= med_ratio <= 2.0)
    print(f"  → 判据（corr>0.7 且 中位相对误差<35% 且 比值∈[0.5,2]）: "
          f"{'✅ 成立' if ok else '⚠ 未达判据'}")

    io.open(OUT / "alpha_from_gradients.json", "w", encoding="utf-8", newline="").write(
        json.dumps({"eta": 1e-4, "rank": RANK, "epochs": EPOCHS, "seeds": SEEDS,
                    "batch": BATCH, "max_samples": MAX_SAMPLES,
                    "alpha_fit_mean": mf, "alpha_hat_mean": mh,
                    "corr": corr, "median_rel_err": med_rel, "median_ratio": med_ratio,
                    "r2_fit_mean": st.mean([r["R2_fit"] for r in records]),
                    "passed": bool(ok), "records": records}, indent=2))
    print(f"  ✅ 已写 {OUT.relative_to(REPO)}/alpha_from_gradients.json")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
