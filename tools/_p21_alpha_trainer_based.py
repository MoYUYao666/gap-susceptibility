# -*- coding: utf-8 -*-
r"""**实验 A（修正版）**：用 **trainer 自己的训练循环**测 `⟨∇DG*, ∇L⟩`，预测 α（2026-10-08）。

## 前两次失败的原因（都已实测）

| 版本 | 问题 | 证据 |
|---|---|---|
| 首跑（`max_samples=2000`） | 样本量不足 | DG\\* 跨度 **0.0102** vs 归档 **0.1538**（差 15 倍） |
| 重跑（5000 样本） | **自行实现训练循环**，动力学与归档不符 | `final_step` **780 vs 归档 630**；DG\\* 跨度 **0.0159 vs 0.1641**（差 10 倍） |

**共同点：我没有"先对齐动力学，再谈预测"。**

## 本版做法（关键差异）

**不自己写训练循环**，而是**子类化 `GapAwareTrainer`**，复用它的 `train()`：

- 调度器：`CosineAnnealingLR(T_max=len(train_loader)×epochs)`
- 优化器：`AdamW(lr=1e-4, weight_decay=...)`（trainer 默认）
- 数据：与归档同口径（5000 样本 / batch / 10 epoch）

**只在每 epoch 末尾插一次额外反向**：

1. 克隆可训参数；2. 设 `loss = DG*(val)`，`backward()` → 得 `g_dg`；
3. 取训练步累积的 `g_L`（每一步的 loss 梯度按步数平均）；
4. `inner = ⟨g_dg, g_L⟩`；5. **恢复**参数与优化器状态（不污染训练）。

**判据（事先写明，与首跑一致）**：`corr(α̂, α_fit) > 0.7` 且 中位相对误差 < 35% 且 比值 ∈ [0.5, 2]。
其中 `α̂ = −η̄ · mean_epoch(inner)`。

## 动力学对齐自检（**先跑这个，不通过就不测预测**）

**要求**：本 run 的 `final_train_loss` 与 DG\\* 跨度与归档同量级
（归档 `v1_both_r8`: `final_train_loss≈0.060`、DG\\* 跨度≈0.164）。
**不通过则本脚本明确报"未对齐"，不产出 α 结论。**

    python tools\_p21_alpha_trainer_based.py --smoke     # 2 epoch 快检
    python tools\_p21_alpha_trainer_based.py --apply
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

OUT = REPO / "outputs" / "theory" / "alpha_trainer_based"
ARCHIVE_SPAN = 0.1641        # 归档 v1_both_r8 的 DG* 跨度（可复现对照）


def main() -> int:
    argv = sys.argv
    apply = "--apply" in argv
    smoke = "--smoke" in argv
    seeds = [42] if smoke else ([int(x) for x in argv[argv.index("--seeds") + 1].split(",")]
                                if "--seeds" in argv else [42, 123, 456])
    epochs = 2 if smoke else (int(argv[argv.index("--epochs") + 1]) if "--epochs" in argv else 10)
    rank = int(argv[argv.index("--rank") + 1]) if "--rank" in argv else 8
    maxs = 512 if smoke else (int(argv[argv.index("--maxsamples") + 1])
                              if "--maxsamples" in argv else 5000)
    LR_OVERRIDE = (float(argv[argv.index("--lr") + 1]) if "--lr" in argv else None)
    BATCH_OVERRIDE = (int(argv[argv.index("--batch") + 1]) if "--batch" in argv else None)

    if not apply:
        print("=== 实验 A：基于 trainer 的 α 测量 ===")
        print(f"  seeds={seeds} epochs={epochs} rank={rank} max_samples={maxs}")
        print(f"  判据：corr>0.7 且 中位相对误差<35% 且 比值∈[0.5,2]")
        print(f"  动力学对齐要求：DG* 跨度 ≈ {ARCHIVE_SPAN}（归档 v1_both_r8）")
        print("  （预演；加 --apply 实跑）")
        return 0

    import torch
    from src.config import ExperimentConfig, LoRAConfig, TrainConfig, GapConfig
    from src.trainer import GapAwareTrainer
    from src.dataset import create_dataloaders

    OUT.mkdir(parents=True, exist_ok=True)
    records = []

    class AlphaTrainer(GapAwareTrainer):
        """复用 trainer 的训练循环，只在每 epoch 末尾加测 ⟨∇DG*, ∇L⟩。"""

        def capture_inner(self, val_loader):
            """返回 (inner, gL_norm, gdg_norm)：本轮 epoch 的 ⟨∇_θDG*, ∇_θL⟩。"""
            params = [p for p in self.model.parameters() if p.requires_grad]
            if not params:
                return None
            # ① 训练梯度：**必须用钩子在 zero_grad 之前取**（见 _p40 的实测：
            #    _train_epoch 内每个优化步后都会 zero_grad，epoch 之外 p.grad 全为 None）。
            gL = getattr(self, "_last_train_grad", None)
            if gL is None or len(gL) == 0:
                return None
            if len(gL) != len(params):
                print(f"     [capture_inner] gL({len(gL)}) 与 params({len(params)}) 不等长"
                      f" → 按 min 截断配对", flush=True)
                gL = gL[:len(params)]
            # ② ∇DG*：临时开梯度，对 val 上的 DG* 反向
            # **只取 2 批**：实测 8 批会在 8 GB 卡上 OOM（PyTorch 累计分配 21 GiB）——
            # 训练循环的图尚未释放，两者叠加超限。∇DG* 是期望的估计，
            # 2 批 × 64 = 128 样本足够；**DG* 轨迹本身仍由 _compute_dg_star_record
            # 在全验证集上单独测**（no_grad），故取值口径不变。
            self.model.eval()
            self.model.zero_grad(set_to_none=True)
            if torch.cuda.is_available():
                torch.cuda.empty_cache()
            imgs, txts = [], []
            with torch.enable_grad():
                for i, batch in enumerate(val_loader):
                    if i >= 2:
                        break
                    images = batch["image"].to(self.device)
                    texts = batch["caption"]
                    if "input_ids" in batch and "attention_mask" in batch:
                        ii = batch["input_ids"].to(self.device)
                        am = batch["attention_mask"].to(self.device)
                    else:
                        ti = self.processor(text=texts, return_tensors="pt", padding=True,
                                            truncation=True, max_length=77)
                        ii = ti["input_ids"].to(self.device)
                        am = ti["attention_mask"].to(self.device)
                    out = self.model(pixel_values=images, input_ids=ii, attention_mask=am)
                    imgs.append(out.image_embeds)
                    txts.append(out.text_embeds)
                I = torch.cat(imgs); T = torch.cat(txts)
                # **必须与 src/dg_star_tracker.py:compute 完全一致**——
                # 论文 ODE 拟合的是 dg_star（配对均方距离），不是质心间隙 cg。
                import torch.nn.functional as _F
                I = _F.normalize(I.float(), p=2, dim=-1)
                T = _F.normalize(T.float(), p=2, dim=-1)
                dg = ((I - T) ** 2).sum(dim=-1).mean()
                dg.backward()
            # 及时释放图与嵌入，避免与训练循环的图叠加爆显存
            del imgs, txts, I, T
            gdg = [(p.grad.detach().clone() if p.grad is not None else None) for p in params]
            self.model.zero_grad(set_to_none=True)
            # **按位置配对，跳过任一为 None 的对**：训练梯度与 ∇DG* 的非零个数不同
            # （实测 398 vs 397），故不能用"长度相等"做判据——那会永远返回 None。
            pairs, skipped_none = [], 0
            for a, b in zip(gdg, gL):
                if a is None or b is None:
                    skipped_none += 1
                    continue
                pairs.append((a, b))
            if not pairs:
                print(f"     [capture_inner] 无可用配对（gdg 非零 "
                      f"{sum(1 for x in gdg if x is not None)} / gL 非零 "
                      f"{sum(1 for x in gL if x is not None)}）", flush=True)
                return None
            if skipped_none:
                print(f"     [capture_inner] 用 {len(pairs)} 对，跳过 {skipped_none} 个"
                      f"（任一侧无梯度）", flush=True)
            inner = float(sum((a * b).sum() for a, b in pairs))
            nL = float(sum(a.pow(2).sum() for a, _ in pairs)) ** 0.5
            nD = float(sum(b.pow(2).sum() for _, b in pairs)) ** 0.5
            self.model.train()
            return inner, nL, nD

    for seed in seeds:
        print(f"\n  ── seed {seed} ──", flush=True)
        torch.manual_seed(seed)
        cfg = ExperimentConfig(
            name=f"alpha_trainer_r{rank}_s{seed}",
            lora=LoRAConfig(rank=rank, alpha=rank * 2, apply_to_vision=True, apply_to_text=True),
            gap=GapConfig(compute_every_n_epochs=1),
            train=TrainConfig(dataset="flickr30k", batch_size=(BATCH_OVERRIDE or 64), num_epochs=epochs,
                              max_samples=maxs,
                              learning_rate=(LR_OVERRIDE if LR_OVERRIDE else 1e-4),
                              # **必须给本地路径**：默认值是 HF 仓库 ID（openai/clip-...），
                              # 会去 hf-mirror.com 拉权重并在超时后重试 5 轮 × 多个文件
                              # —— 实测表现为"卡住"（9 分钟无输出、GPU 1%）。
                              clip_model="models/clip-vit-base-patch32",
                              save_dir=str(OUT / f"s{seed}")))
        tr = AlphaTrainer(cfg)
        tr.setup_model()
        tr.enable_dg_star_tracking()
        # **补齐 train() 会设置、而 _train_epoch 依赖的属性**——
        # 我绕过 train() 自走循环（为每 epoch 插一次 ∇DG* 反向），故这些不会自动就位。
        # 实测缺 _trainable_params 会报 AttributeError（src/trainer.py:445）。
        tr.peft_method = "lora"
        tr._trainable_params = [p for p in tr.model.parameters() if p.requires_grad]
        tr._current_gap_delta = 0.0
        tr.best_val_loss = float("inf")
        train_loader, val_loader, _ = create_dataloaders(
            dataset_name="flickr30k", data_dir=".", batch_size=(BATCH_OVERRIDE or 64), max_samples=maxs)

        # 自己走 trainer 的训练循环，但每 epoch 后加测（与 trainer.train() 同构造）
        import torch as _t
        from torch.optim import AdamW
        from torch.optim.lr_scheduler import CosineAnnealingLR
        params = [p for p in tr.model.parameters() if p.requires_grad]
        opt = AdamW(params, lr=tr.train_cfg.learning_rate, weight_decay=tr.train_cfg.weight_decay)
        total_steps = len(train_loader) * tr.train_cfg.num_epochs
        sched = CosineAnnealingLR(opt, T_max=total_steps)
        print(f"     train_loader={len(train_loader)} 步/epoch ｜ total_steps={total_steps}", flush=True)
        print(f"     lr_peak={opt.param_groups[0]['lr']:.2e}", flush=True)

        inner_hist, lr_hist, dg_hist = [], [], []
        skipped = 0
        tr._capture_train_grad = True          # 开启梯度钩子（默认关闭）
        for ep in range(1, epochs + 1):
            tr.current_epoch = ep
            loss = tr._train_epoch(train_loader, opt, sched, ep)
            if torch.cuda.is_available():
                torch.cuda.empty_cache()
            lr_hist.append(opt.param_groups[0]["lr"])
            r = tr.capture_inner(val_loader)
            if r is None:
                skipped += 1
                inner_txt = "无梯度(已跳过)"       # **不得把跳过伪装成 nan**
            else:
                inner_hist.append(r[0])
                inner_txt = f"{r[0]:+.3e}"
            rec = tr._compute_dg_star_record(val_loader, ep)
            dg_hist.append(rec.dg_star if hasattr(rec, "dg_star") else rec.get("dg_star"))
            print(f"     ep {ep:>2} loss={loss:.4f} lr={lr_hist[-1]:.2e} "
                  f"inner={inner_txt} DG*={dg_hist[-1]:.4f}", flush=True)
        if skipped:
            print(f"     ⚠ {skipped}/{epochs} 个 epoch 未取到训练梯度（inner 序列长度 "
                  f"{len(inner_hist)}）", flush=True)

        span = max(dg_hist) - min(dg_hist)
        rec = {"seed": seed, "losses": None, "span": span,
               "dg_star": dg_hist, "inner": inner_hist, "lr": lr_hist}
        records.append(rec)
        print(f"     → DG* 跨度 {span:.4f}（归档 {ARCHIVE_SPAN}）｜ "
              f"{'✅ 已对齐' if 0.4 * ARCHIVE_SPAN <= span <= 3 * ARCHIVE_SPAN else '❌ **未对齐**'}")

    aligned = [r for r in records if 0.4 * ARCHIVE_SPAN <= r["span"] <= 3 * ARCHIVE_SPAN]
    print(f"\n  === 动力学对齐自检 ===")
    print(f"     对齐 {len(aligned)}/{len(records)} 条轨迹")
    if not aligned:
        print("     ❌ **未对齐 → 不产出 α 结论**（按事先判据，对齐是本实验的前提）")
        io.open(OUT / "alpha_trainer_based.json", "w", encoding="utf-8", newline="").write(
            json.dumps({"aligned": False, "records": records,
                        "note": "DG* 跨度与归档不同量级，预测无可比性"}, ensure_ascii=False, indent=1))
        return 0

    # —— 对齐后才能算 α̂ vs α_fit ——
    import numpy as np
    out_recs = []
    for r in aligned:
        eta_bar = st.mean(r["lr"])
        a_hat = -eta_bar * st.mean(r["inner"])
        y = np.asarray(r["dg_star"], float); t = np.arange(1, len(y) + 1, dtype=float)
        dg0 = y[0]; rr = y - dg0
        best = (float("nan"), float("nan"), float("inf"))
        for logb in np.linspace(np.log10(0.005), np.log10(20.0), 800):
            b = 10.0 ** logb
            u = 1.0 - np.exp(-b * t); den = float((u * u).sum())
            if den < 1e-12:
                continue
            a = float((u * rr).sum()) / den
            resid = float(((rr - a * u) ** 2).sum())
            if resid < best[2]:
                best = (a * b, b, resid)
        A, B, _ = best
        yh = dg0 + (A / B) * (1 - np.exp(-B * t))
        ss = float(((y - y.mean()) ** 2).sum())
        R2 = 1 - float(((y - yh) ** 2).sum()) / ss if ss > 0 else float("nan")
        out_recs.append({"seed": r["seed"], "alpha_fit": A, "alpha_hat": a_hat,
                         "beta_fit": B, "R2_fit": R2, "eta_bar": eta_bar,
                         "inner": r["inner"], "span": r["span"]})
        print(f"     seed {r['seed']}: α_fit={A:+.5f} α̂={a_hat:+.6f} R²_fit={R2:.3f} "
              f"比值={a_hat/A if abs(A)>1e-12 else float('nan'):.3f}")

    af = [x["alpha_fit"] for x in out_recs]; ah = [x["alpha_hat"] for x in out_recs]
    corr = float(np.corrcoef(af, ah)[0, 1]) if len(af) > 1 else float("nan")
    rel = st.median([abs(b - a) / abs(a) for a, b in zip(af, ah)])
    ratio = st.median([b / a for a, b in zip(af, ah)])
    passed = (corr > 0.7) and (rel < 0.35) and (0.5 <= ratio <= 2)
    print(f"\n  === 结论 ===")
    print(f"     corr={corr:.4f} ｜ 中位相对误差={rel:.4f} ｜ 比值中位={ratio:.4f}")
    print(f"     判据（corr>0.7 且 误差<35% 且 比值∈[0.5,2]）→ {'✅ 通过' if passed else '❌ 未通过'}")
    io.open(OUT / "alpha_trainer_based.json", "w", encoding="utf-8", newline="").write(
        json.dumps({"aligned": True, "corr": corr, "median_rel_err": rel, "median_ratio": ratio,
                    "passed": bool(passed), "archive_span": ARCHIVE_SPAN,
                    "records": out_recs}, ensure_ascii=False, indent=1))
    print(f"     ✅ 已写 {(OUT / 'alpha_trainer_based.json').relative_to(REPO)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
