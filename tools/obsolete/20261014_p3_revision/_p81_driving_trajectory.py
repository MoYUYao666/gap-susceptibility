# -*- coding: utf-8 -*-
r"""**驱动项随训练的演化**：`Σ_m <∇_m DG*, g_m>`（2026-10-09）。

## 要回答的问题

`tools/_p79` 测得：**训练前的瞬时驱动项在三臂间只差 1.29%**，
而实测 CGΔ 差 4.4 倍（排序也不同）→ **一阶驱动项无法解释位置效应**。

**但论文用的是轨迹平均**（`theory.tex:75`）→ **不排除"平均后差异变大"。**

**→ 本脚本逐 epoch 测该驱动项，给出轨迹。**

## 设计

| 项 | 值 |
|---|---|
| 臂 | `text_only` / `both` / `vision_only`（各 1 seed = 42） |
| 训练 | `max_samples 5000`、`batch 128`、**10 epoch**（与归档一致） |
| 测量 | **每 epoch 末**，用 2 个验证批算 `<∇_mDG*, g_m>`（按**参数名配对**） |
| 输出 | `outputs/analysis/driving_trajectory.json` |

## 预写判据

- 对每个 epoch：**三臂驱动项的极差 / 均值**；
- **若轨迹平均后极差仍 < 10%** → 理论的一阶项**确实无法**解释位置效应 → **须修订理论**；
- **若某个 epoch 后极差扩大并与实测同向** → 理论**可解释**，只是需要轨迹平均。

    python tools\_p81_driving_trajectory.py [--apply]
"""
from __future__ import annotations

import io
import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO))
sys.path.insert(0, str(REPO / "src"))
OUT = REPO / "outputs" / "analysis" / "driving_trajectory.json"

ARMS = {
    "text_only":   dict(apply_to_vision=False, apply_to_text=True),
    "both":        dict(apply_to_vision=True,  apply_to_text=True),
    "vision_only": dict(apply_to_vision=True,  apply_to_text=False),
}
SEED = 42
EPOCHS = 10
N_MEASURE_BATCHES = 2


def measure(tr, batches, device, params):
    """在**当前模型状态**上算 Σ_m<∇_mDG*, g_m> 与两侧分量。"""
    import torch
    import torch.nn.functional as F
    tr.model.eval()
    acc = {"ip_v": 0.0, "ip_t": 0.0, "nv": 0.0, "nt": 0.0, "nb": 0}
    for b in batches:
        imgs = b["image"].to(device)
        ii = b["input_ids"].to(device)
        am = b["attention_mask"].to(device)
        # ① 任务梯度
        tr.model.zero_grad(set_to_none=True)
        o = tr.model(pixel_values=imgs, input_ids=ii, attention_mask=am)
        I = F.normalize(o.image_embeds, p=2, dim=-1)
        T = F.normalize(o.text_embeds, p=2, dim=-1)
        logits = 100.0 * I @ T.T
        lab = torch.arange(I.shape[0], device=device)
        loss = (F.cross_entropy(logits, lab) + F.cross_entropy(logits.T, lab)) / 2
        loss.backward()
        gL = {n: (p.grad.detach().float().clone() if p.grad is not None else None)
              for n, p in params}
        # ② ∇DG*
        tr.model.zero_grad(set_to_none=True)
        o2 = tr.model(pixel_values=imgs, input_ids=ii, attention_mask=am)
        I2 = F.normalize(o2.image_embeds.float(), p=2, dim=-1)
        T2 = F.normalize(o2.text_embeds.float(), p=2, dim=-1)
        dg = ((I2 - T2) ** 2).sum(-1).mean()
        dg.backward()
        gD = {n: (p.grad.detach().float().clone() if p.grad is not None else None)
              for n, p in params}

        for side in ("v", "t"):
            key = "vision_model" if side == "v" else "text_model"
            names = [n for n in gL if key in n]
            if not names:
                continue
            ip = float(sum(torch.dot(gD[n].flatten(), gL[n].flatten())
                           for n in names
                           if gD.get(n) is not None and gL.get(n) is not None))
            nd = float(sum(torch.dot(gD[n].flatten(), gD[n].flatten())
                           for n in names if gD.get(n) is not None)) ** 0.5
            acc[f"ip_{side}"] += ip
            acc[f"n{side}"] += nd
        acc["nb"] += 1
    nb = max(acc["nb"], 1)
    return {"ip_v": acc["ip_v"] / nb, "ip_t": acc["ip_t"] / nb,
            "sum": (acc["ip_v"] + acc["ip_t"]) / nb,
            "normDG_v": acc["nv"] / nb, "normDG_t": acc["nt"] / nb}


def main() -> int:
    apply = "--apply" in sys.argv
    if not apply:
        print("=== 驱动项轨迹（3 臂 × 10 epoch，每 epoch 测 2 批）===")
        print("  判据：轨迹平均后三臂极差是否 ≥10%（<10% 则理论须修订）")
        print("  （预演；加 --apply 实跑）")
        return 0

    import torch
    from src.config import ExperimentConfig, LoRAConfig, TrainConfig
    from src.trainer import GapAwareTrainer
    from src.dataset import create_dataloaders

    device = "cuda" if torch.cuda.is_available() else "cpu"
    loader, val_loader, _ = create_dataloaders(
        dataset_name="flickr30k", data_dir=".", batch_size=128, max_samples=5000)
    mbatches = [b for i, b in enumerate(val_loader) if i < N_MEASURE_BATCHES]
    print(f"=== 驱动项轨迹（device={device}，train {len(loader)} 批，"
          f"测量 {len(mbatches)} 批）===", flush=True)

    result = {}
    for arm, flags in ARMS.items():
        print(f"\n  ── {arm} ──", flush=True)
        torch.manual_seed(SEED)
        cfg = ExperimentConfig(
            name=f"drv_{arm}",
            lora=LoRAConfig(rank=8, alpha=16, **flags),
            train=TrainConfig(dataset="flickr30k", batch_size=128, num_epochs=EPOCHS,
                              max_samples=5000, clip_model="models/clip-vit-base-patch32",
                              save_dir=str(REPO / "outputs/_drv")))
        tr = GapAwareTrainer(cfg)
        tr.device = device
        tr.setup_model()
        params = [(n, p) for n, p in tr.model.named_parameters() if p.requires_grad]
        opt = torch.optim.AdamW([p for _, p in params], lr=1e-4, weight_decay=0.01)
        sched = torch.optim.lr_scheduler.CosineAnnealingLR(
            opt, T_max=max(len(loader) * EPOCHS, 1))

        traj = [measure(tr, mbatches, device, params)]
        print(f"     ep 0: Σip={traj[0]['sum']:+.4f}", flush=True)
        for ep in range(1, EPOCHS + 1):
            tr.model.train()
            for b in loader:
                imgs = b["image"].to(device)
                ii = b["input_ids"].to(device)
                am = b["attention_mask"].to(device)
                o = tr.model(pixel_values=imgs, input_ids=ii, attention_mask=am)
                import torch.nn.functional as F
                I = F.normalize(o.image_embeds, p=2, dim=-1)
                T = F.normalize(o.text_embeds, p=2, dim=-1)
                logits = 100.0 * I @ T.T
                lab = torch.arange(I.shape[0], device=device)
                loss = (F.cross_entropy(logits, lab) + F.cross_entropy(logits.T, lab)) / 2
                loss.backward()
                opt.step(); sched.step(); opt.zero_grad()
            m = measure(tr, mbatches, device, params)
            traj.append(m)
            print(f"     ep {ep:>2}: Σip={m['sum']:+.4f}", flush=True)
        result[arm] = traj
        del tr
        if device == "cuda":
            torch.cuda.empty_cache()

    print("\n=== 三臂驱动项轨迹（Σ_m<∇_mDG*, g_m>）===")
    print(f"  {'ep':>3}" + "".join(f"{a:>16}" for a in ARMS) + f"{'极差/均值':>12}")
    spreads = []
    for ep in range(EPOCHS + 1):
        vals = [result[a][ep]["sum"] for a in ARMS]
        sp = (max(vals) - min(vals)) / abs(sum(vals) / 3) * 100
        spreads.append(sp)
        print(f"  {ep:>3}" + "".join(f"{v:>+16.4f}" for v in vals) + f"{sp:>11.2f}%")

    import statistics as st
    mean_traj = {a: st.mean(result[a][ep]["sum"] for ep in range(EPOCHS + 1))
                 for a in ARMS}
    mv = [mean_traj[a] for a in ARMS]
    sp_mean = (max(mv) - min(mv)) / abs(sum(mv) / 3) * 100
    print(f"\n=== 判据 ===")
    print(f"  逐 epoch 极差：最小 {min(spreads):.2f}% ｜ 最大 {max(spreads):.2f}%")
    print(f"  **轨迹平均后**极差 = **{sp_mean:.2f}%**")
    print(f"  实测 CGΔ 极差 = 0.0571（4.4× 于均值）")
    if sp_mean < 10:
        print("  → ❌ **轨迹平均后极差仍 <10%** ⇒ 理论的一阶项**确实无法**解释位置效应")
    else:
        print("  → ✅ 轨迹平均后差异扩大 ⇒ 理论**可解释**，只是需要轨迹平均")

    if apply:
        OUT.parent.mkdir(parents=True, exist_ok=True)
        io.open(OUT, "w", encoding="utf-8", newline="").write(json.dumps({
            "trajectories": result, "per_epoch_spread_pct": spreads,
            "trajectory_mean_spread_pct": sp_mean,
            "trajectory_means": mean_traj,
            "measured_cg_delta_spread": 0.0571,
            "criterion": "spread <10% after averaging => first-order term cannot "
                         "explain the position effect",
        }, ensure_ascii=False, indent=1))
        print(f"\n  ✅ 已写 {OUT.relative_to(REPO)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
