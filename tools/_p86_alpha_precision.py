# -*- coding: utf-8 -*-
r"""**C：确定性一致性检验**——用足够批次把 `f(DG₀)` 测准，与拟合的 `α` 对照（2026-10-10）。

## 背景（实测）

| 来源 | `α_hat`（从梯度算） | `α_fit`（从轨迹拟合） | 比 |
|---|---|---|---|
| `outputs/theory/alpha_from_gradients.json` | **−5.99e−5** | **−2.77e−3** | 46× |
| 我今日 `_p85`（7 批） | 均值 ±sd ≈ 18–32 ± 27–49 | — | **信噪比 ~0.4–1.2** |

**→ 前者用 7 批太少；46 倍的差可能主要是 MC 噪声。**

## 本脚本

**关键**：`α = −η f(DG₀)`，其中 `f(DG₀) = ⟨∇_θ DG*, ∇_θ L⟩`。
**要判定 46 倍差是"噪声"还是"真实"，只需把 `f(DG₀)` 测到 ±10% 精度。**

| 项 | 设定 |
|---|---|
| 位置 | `text_only` / `both` / `vision_only`（严格冻结，只放开 LoRA A/B） |
| 批次 | **每位置每 seed 30 批**（比归档的 7 批多 4 倍） |
| seed | 42 / 123（与归档同） |
| 输出 | 逐批值 + 均值 + **标准误 + 95% CI** + 与 `α_fit` 的比 |
| 判据 | 若 CI 覆盖 `α_fit/η` → **46 倍差主要是噪声**；若不覆盖 → **差异是真实的** |

    python tools\_p86_alpha_precision.py --apply
"""
from __future__ import annotations

import argparse
import io
import json
import statistics as st
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO))
sys.path.insert(0, str(REPO / "src"))
OUT = REPO / "outputs" / "analysis" / "alpha_precision.json"

ARMS = {
    "text_only":   dict(apply_to_vision=False, apply_to_text=True),
    "both":        dict(apply_to_vision=True,  apply_to_text=True),
    "vision_only": dict(apply_to_vision=True,  apply_to_text=False),
}
ETA = 1e-4
# 归档的 α_fit（`outputs/theory/alpha_from_gradients.json`）
ALPHA_FIT_ARCHIVE = -2.7742991623655212e-03


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    ap.add_argument("--n-batches", type=int, default=30)
    ap.add_argument("--seeds", type=int, nargs="*", default=[42, 123])
    ap.add_argument("--batch-size", type=int, default=64)
    ap.add_argument("--max-samples", type=int, default=5000)
    args = ap.parse_args()
    if not args.apply:
        print("=== C：f(DG₀) 的高精度估计 ===")
        print(f"  {args.n_batches} 批 × {len(args.seeds)} seed × 3 位置")
        print(f"  对照 α_fit = {ALPHA_FIT_ARCHIVE:.4e}（归档）→ f_fit = α_fit/η "
              f"= {ALPHA_FIT_ARCHIVE/ETA:.2f}")
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
    batches = [b for i, b in enumerate(loader) if i < args.n_batches]
    print(f"=== C：{len(batches)} 批 × {len(args.seeds)} seed × 3 位置"
          f"（device={device}）===", flush=True)

    result = {"eta": ETA, "alpha_fit_archive": ALPHA_FIT_ARCHIVE,
              "n_batches": len(batches), "seeds": args.seeds,
              "f_fit_archive": ALPHA_FIT_ARCHIVE / ETA, "rows": {}}

    for arm, flags in ARMS.items():
        per_seed = {}
        for seed in args.seeds:
            torch.manual_seed(seed)
            cfg = ExperimentConfig(
                name=f"prec_{arm}_s{seed}",
                lora=LoRAConfig(rank=8, alpha=16, **flags),
                train=TrainConfig(dataset="flickr30k", batch_size=args.batch_size,
                                  num_epochs=1, max_samples=args.max_samples,
                                  clip_model="models/clip-vit-base-patch32",
                                  save_dir=str(REPO / "outputs/_prec")))
            tr = GapAwareTrainer(cfg)
            tr.device = device
            tr.setup_model()
            params = [(n, p) for n, p in tr.model.named_parameters() if p.requires_grad]
            pmap = dict(params)
            vals = []
            for b in batches:
                imgs = b["image"].to(device); ii = b["input_ids"].to(device)
                am = b["attention_mask"].to(device)
                tr.model.zero_grad(set_to_none=True)
                o = tr.model(pixel_values=imgs, input_ids=ii, attention_mask=am)
                I = F.normalize(o.image_embeds, p=2, dim=-1)
                T = F.normalize(o.text_embeds, p=2, dim=-1)
                lg = 100.0 * I @ T.T
                lab = torch.arange(I.shape[0], device=device)
                loss = (F.cross_entropy(lg, lab) + F.cross_entropy(lg.T, lab)) / 2
                loss.backward()
                gL = {n: (pmap[n].grad.detach().float().clone()
                          if pmap[n].grad is not None else None) for n, _ in params}
                tr.model.zero_grad(set_to_none=True)
                o2 = tr.model(pixel_values=imgs, input_ids=ii, attention_mask=am)
                I2 = F.normalize(o2.image_embeds.float(), p=2, dim=-1)
                T2 = F.normalize(o2.text_embeds.float(), p=2, dim=-1)
                dg = ((I2 - T2) ** 2).sum(-1).mean()
                dg.backward()
                gD = {n: (pmap[n].grad.detach().float().clone()
                          if pmap[n].grad is not None else None) for n, _ in params}
                tot = 0.0
                for key in ("vision_model", "text_model"):
                    names = [n for n in gL if key in n]
                    for n in names:
                        if gD.get(n) is not None and gL.get(n) is not None:
                            tot += float(torch.dot(gD[n].flatten(), gL[n].flatten()))
                vals.append(tot)
                tr.model.zero_grad(set_to_none=True)

            m = st.mean(vals)
            sd = st.stdev(vals) if len(vals) > 1 else 0.0
            se = sd / (len(vals) ** 0.5) if vals else 0.0
            per_seed[seed] = {"mean": m, "sd": sd, "se": se, "n": len(vals),
                              "ci95": [m - 1.96 * se, m + 1.96 * se],
                              "snr": (m / sd) if sd else None,
                              "alpha_hat": -ETA * m}
            print(f"  {arm:<12} seed {seed}: f = {m:+.4f} ± {se:.4f} (se) ｜ "
                  f"sd {sd:.2f} ｜ SNR {m/sd if sd else 0:.2f} ｜ "
                  f"α_hat = {-ETA*m:+.4e}", flush=True)
            del tr
            if device == "cuda":
                torch.cuda.empty_cache()
        result["rows"][arm] = per_seed

    print("\n=== 判定 ===")
    f_fit = ALPHA_FIT_ARCHIVE / ETA
    print(f"  归档 α_fit = {ALPHA_FIT_ARCHIVE:.4e} → 对应 f_fit = {f_fit:.3f}")
    all_means, all_ses = [], []
    for arm, ps in result["rows"].items():
        ms = [v["mean"] for v in ps.values()]
        ses = [v["se"] for v in ps.values()]
        mm = st.mean(ms)
        pooled = (sum(s * s for s in ses) ** 0.5) / len(ses)
        all_means.append(mm)
        all_ses.append(pooled)
        cover = (mm - 1.96 * pooled) <= f_fit <= (mm + 1.96 * pooled)
        print(f"  {arm:<12} f = {mm:+.3f} ± {pooled:.3f} ｜ "
              f"覆盖 f_fit? {'✅ 是' if cover else '❌ 否'} ｜ "
              f"比 f_fit/f = {f_fit/mm if mm else float('nan'):.2f}")
    gm = st.mean(all_means)
    gse = (sum(s * s for s in all_ses) ** 0.5) / len(all_ses)
    print(f"  三位置合并: f = {gm:+.3f} ± {gse:.3f}")
    cover_all = (gm - 1.96 * gse) <= f_fit <= (gm + 1.96 * gse)
    print(f"  合并后覆盖 f_fit? {'✅ 是' if cover_all else '❌ 否'}")
    if cover_all:
        print("  → **46 倍的差主要是 Monte Carlo 噪声**（真值区间覆盖拟合值）")
    else:
        print(f"  → **46 倍的差是真实的**：即使 {args.n_batches} 批 × "
              f"{len(args.seeds)} seed 也覆盖不到 f_fit")
        print("     → 说明 `α` 不能由这一积分的均值预测（与论文 limitation 一致）")
    result["verdict"] = ("noise-dominated" if cover_all else "real discrepancy")
    result["pooled_f"] = {"mean": gm, "se": gse, "covers_fit": cover_all}
    io.open(OUT, "w", encoding="utf-8", newline="").write(
        json.dumps(result, ensure_ascii=False, indent=1))
    print(f"\n  ✅ 已写 {OUT.relative_to(REPO)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
