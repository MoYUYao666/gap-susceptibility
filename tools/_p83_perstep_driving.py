# -*- coding: utf-8 -*-
r"""**严格版**：逐 step 记录 `Σ_m <∇_m DG*, g_m>`（**重写：修掉梯度被抹掉的 bug**）（2026-10-09）。

## 上一版的致命 bug

上一版在测量 `DG*` 前调了 `zero_grad()` → **把训练梯度抹掉**，
于是优化步用的是 `DG*` 的梯度（而非任务梯度）→ **训练语义被改变**。
（我还引用了一个未定义的 `_pending`。）**已重写。**

## 本版设计（干净、可验证）

每步**只测一次**，顺序严格如下：

1. **前向 → 任务损失 → `backward()`**
2. **立即**：`gL = clone(该侧梯度)`，**同时**保留 `p.grad`（不 zero）
3. **`opt.step()`** 用**任务梯度**更新（语义正确）
4. **`zero_grad()`**
5. 再前向 → `DG*` → `backward()` → `gD = clone(...)`
6. **逐张量配对求内积**，**立即累加**，随后 `del`
7. `zero_grad()`

**关键**：测量发生在**更新后**的模型状态上，且**不干扰优化步**。
**（代价**：每步多 1 次前向+反传；`gL` 需在 `opt.step()` 前克隆。）**

## 逐 step 与逐 epoch 都存

- `per_epoch`：每个 epoch 的 `Σip` 均值；
- `sum_mean`：**全程逐 step 的均值**（= 论文的"轨迹平均"最严格对应）；
- `loss_first` / `loss_last`：**验证训练未被破坏**（应显著下降）。

    python tools\_p83_perstep_driving.py --apply --epochs 3 --max-samples 2000
"""
from __future__ import annotations

import argparse
import io
import json
import sys
import time
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO))
sys.path.insert(0, str(REPO / "src"))
OUT = REPO / "outputs" / "analysis" / "driving_perstep.json"

ARMS = {
    "text_only":   dict(apply_to_vision=False, apply_to_text=True),
    "both":        dict(apply_to_vision=True,  apply_to_text=True),
    "vision_only": dict(apply_to_vision=True,  apply_to_text=False),
}
SEED = 42


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    ap.add_argument("--epochs", type=int, default=10)
    ap.add_argument("--max-samples", type=int, default=5000)
    ap.add_argument("--batch-size", type=int, default=128)
    args = ap.parse_args()
    if not args.apply:
        print("=== 逐 step 驱动项（严格版，已修梯度 bug）===")
        print(f"  3 臂 × {args.epochs} epoch × max_samples {args.max_samples}"
              f" ｜ batch {args.batch_size}")
        print("  输出: outputs/analysis/driving_perstep.json")
        return 0

    import torch
    import torch.nn.functional as F
    from src.config import ExperimentConfig, LoRAConfig, TrainConfig
    from src.trainer import GapAwareTrainer
    from src.dataset import create_dataloaders

    device = "cuda" if torch.cuda.is_available() else "cpu"
    loader, _, _ = create_dataloaders(
        dataset_name="flickr30k", data_dir=".", batch_size=args.batch_size,
        max_samples=args.max_samples)
    print(f"=== 逐 step 驱动项（device={device}，{len(loader)} 批/epoch × "
          f"{args.epochs} epoch）===", flush=True)

    result = {}
    for arm, flags in ARMS.items():
        print(f"\n  ── {arm} ──", flush=True)
        torch.manual_seed(SEED)
        cfg = ExperimentConfig(
            name=f"ps_{arm}",
            lora=LoRAConfig(rank=8, alpha=16, **flags),
            train=TrainConfig(dataset="flickr30k", batch_size=args.batch_size,
                              num_epochs=args.epochs, max_samples=args.max_samples,
                              clip_model="models/clip-vit-base-patch32",
                              save_dir=str(REPO / "outputs/_ps")))
        tr = GapAwareTrainer(cfg)
        tr.device = device
        tr.setup_model()
        params = [(n, p) for n, p in tr.model.named_parameters() if p.requires_grad]
        opt = torch.optim.AdamW([p for _, p in params], lr=1e-4, weight_decay=0.01)
        sched = torch.optim.lr_scheduler.CosineAnnealingLR(
            opt, T_max=max(len(loader) * args.epochs, 1))

        pmap = dict(params)          # 提到循环外：避免每步重建 650 项字典
        acc = {"ip_v": 0.0, "ip_t": 0.0, "n": 0}          # 全程运行和
        per_epoch, losses = [], []
        t0 = time.time()

        for ep in range(1, args.epochs + 1):
            e = {"ip_v": 0.0, "ip_t": 0.0, "n": 0}
            tr.model.train()
            for b in loader:
                imgs = b["image"].to(device)
                ii = b["input_ids"].to(device)
                am = b["attention_mask"].to(device)

                # ① 任务损失与前向
                tr.model.zero_grad(set_to_none=True)
                o = tr.model(pixel_values=imgs, input_ids=ii, attention_mask=am)
                I = F.normalize(o.image_embeds, p=2, dim=-1)
                T = F.normalize(o.text_embeds, p=2, dim=-1)
                logits = 100.0 * I @ T.T
                lab = torch.arange(I.shape[0], device=device)
                loss = (F.cross_entropy(logits, lab) + F.cross_entropy(logits.T, lab)) / 2
                loss.backward()
                losses.append(float(loss))
                # 立即克隆任务梯度（**不 zero**，稍后用于优化）
                gL = {n: (p.grad.detach().float().clone() if p.grad is not None else None)
                      for n, p in params}

                # ② 用**任务梯度**更新（语义正确）
                opt.step(); sched.step()
                tr.model.zero_grad(set_to_none=True)

                # ③ 测量 ∇DG*（在**更新后**状态上）
                o2 = tr.model(pixel_values=imgs, input_ids=ii, attention_mask=am)
                I2 = F.normalize(o2.image_embeds.float(), p=2, dim=-1)
                T2 = F.normalize(o2.text_embeds.float(), p=2, dim=-1)
                dg = ((I2 - T2) ** 2).sum(-1).mean()
                dg.backward()

                # ④ 逐张量配对 → 立即累加
                for side, key in (("v", "vision_model"), ("t", "text_model")):
                    names = [n for n in gL if key in n]
                    if not names:
                        continue
                    ip = 0.0
                    for n in names:
                        p = pmap.get(n)
                        b_ = gL.get(n)
                        if p is not None and p.grad is not None and b_ is not None:
                            ip += float(torch.dot(p.grad.detach().float().flatten(),
                                                  b_.flatten()))
                    acc[f"ip_{side}"] += ip
                    e[f"ip_{side}"] += ip
                acc["n"] += 1
                e["n"] += 1
                tr.model.zero_grad(set_to_none=True)
                del gL, o2, I2, T2, dg

            iv = e["ip_v"] / max(e["n"], 1)
            it = e["ip_t"] / max(e["n"], 1)
            per_epoch.append({"epoch": ep, "ip_v": iv, "ip_t": it, "sum": iv + it,
                              "n_steps": e["n"]})
            print(f"     ep {ep:>2} ｜ Σip={iv+it:+.5f} ｜ 累计 {acc['n']} 步 ｜ "
                  f"{time.time()-t0:.0f}s", flush=True)

        n = max(acc["n"], 1)
        result[arm] = {
            "ip_v_mean": acc["ip_v"] / n, "ip_t_mean": acc["ip_t"] / n,
            "sum_mean": (acc["ip_v"] + acc["ip_t"]) / n, "n_steps": acc["n"],
            "per_epoch": per_epoch,
            "loss_first": losses[0] if losses else None,
            "loss_last": losses[-1] if losses else None,
        }
        print(f"     → {acc['n']} 步 ｜ Σip 均值 = {result[arm]['sum_mean']:+.5f} ｜ "
              f"loss {result[arm]['loss_first']:.4f}→{result[arm]['loss_last']:.4f}",
              flush=True)
        io.open(OUT, "w", encoding="utf-8", newline="").write(
            json.dumps(result, ensure_ascii=False, indent=1))
        del tr
        if device == "cuda":
            torch.cuda.empty_cache()

    print("\n=== 判定（逐 step 平均 = 论文'轨迹平均'的严格对应）===")
    sums = [result[a]["sum_mean"] for a in ARMS]
    sp = (max(sums) - min(sums)) / abs(sum(sums) / 3) * 100
    for a in ARMS:
        print(f"  {a:<13} Σip 全步均值 = {result[a]['sum_mean']:+.5f}")
    print(f"  → **逐 step 平均后极差 / 均值 = {sp:.2f}%**")
    print(f"  实测 CGΔ 极差 / 均值 = 277.3%（绝对 0.0571）")
    print(f"  → 相差 {277.3/max(sp,1e-9):.1f} 倍")
    o_th = sorted(ARMS, key=lambda a: -result[a]["sum_mean"])
    o_cg = ["text_only", "both", "vision_only"]
    print(f"  排序(理论)={o_th} ｜ 排序(实测)={o_cg} ｜ 一致? {o_th == o_cg}")
    verdict = ("first-order term cannot explain the position effect even when "
               "averaged over every step" if sp < 10 else
               "per-step averaging widens the gap; the theory holds")
    print(f"\n  {'❌ ' if sp < 10 else '✅ '}{verdict}")
    io.open(OUT, "w", encoding="utf-8", newline="").write(json.dumps(
        {"arms": result, "perstep_mean_spread_pct": sp,
         "cg_delta_spread_pct": 277.3, "ordering_theory": o_th,
         "ordering_measured": o_cg, "ordering_same": o_th == o_cg,
         "verdict": verdict}, ensure_ascii=False, indent=1))
    print(f"  ✅ 已写 {OUT.relative_to(REPO)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
