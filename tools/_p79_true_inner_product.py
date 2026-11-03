# -*- coding: utf-8 -*-
r"""**真正的理论检验**：直接测 `<∇_m DG*, g_m>`（2026-10-09）。

## 为什么必须重测

论文 `theory.tex:67`：`<∇_m DG*, g_m> = Γ_m · ‖g_m‖`。
**该等号只在 `cos φ_m` 是 `∇_mDG*` 与 `g_m` 自身夹角时成立**，
而 `_p58` 测的是 `∇_mDG*` 与「**全部可训练梯度之和**」的夹角
→ **不等价，故 `_p58` 的 `Γ_m·‖g_m‖` 只是形式值。**

**本脚本直接测三样（每臂分别测）**：

| 量 | 定义 | 来源 |
|---|---|---|
| **`g_m`** | 任务损失的梯度在该侧参数上的部分 | `∇L`（对比损失） |
| **`∇_m DG*`** | `DG*` 的梯度在该侧参数上的部分 | `∇DG*` |
| **`<∇_m DG*, g_m>`** | **直接内积**（逐张量求和） | 上面两者 |
| **`cos φ_m`** | `∇_mDG*` 与 `g_m` 的**真夹角** | 上面两者 |

**预写判据**：
- 若 `Σ_m <∇_mDG*, g_m>` 在三臂间**差异小**（<10%）而实测 CGΔ 差 4 倍
  → **理论无法解释位置效应**；
- 若差异**与实测同向且量级相称** → 理论成立。

    python tools\_p79_true_inner_product.py [--apply]
"""
from __future__ import annotations

import io
import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO))
sys.path.insert(0, str(REPO / "src"))
OUT = REPO / "outputs" / "analysis" / "true_inner_product.json"

ARMS = {
    "text_only":   dict(apply_to_vision=False, apply_to_text=True),
    "both":        dict(apply_to_vision=True,  apply_to_text=True),
    "vision_only": dict(apply_to_vision=True,  apply_to_text=False),
}
RANK = 8
N_BATCHES = 8


def main() -> int:
    apply = "--apply" in sys.argv
    if not apply:
        print("=== 真内积检验：<∇_m DG*, g_m> ｜ 三臂 × 8 批 ===")
        print("  判据：Σ 内积的臂间差异 vs 实测 CGΔ 的臂间差异")
        print("  （预演；加 --apply 实跑）")
        return 0

    import torch
    import torch.nn.functional as F
    from src.config import ExperimentConfig, LoRAConfig, TrainConfig
    from src.trainer import GapAwareTrainer
    from src.dataset import create_dataloaders

    device = "cuda" if torch.cuda.is_available() else "cpu"
    loader, _, _ = create_dataloaders(dataset_name="flickr30k", data_dir=".",
                                      batch_size=64, max_samples=512)
    batches = [b for i, b in enumerate(loader) if i < N_BATCHES]
    print(f"=== 真内积检验（device={device}，{len(batches)} 批）===", flush=True)

    out = {}
    for arm, flags in ARMS.items():
        print(f"\n  ── {arm} ──", flush=True)
        torch.manual_seed(42)
        cfg = ExperimentConfig(
            name=f"inner_{arm}",
            lora=LoRAConfig(rank=RANK, alpha=RANK * 2, **flags),
            train=TrainConfig(dataset="flickr30k", batch_size=64, num_epochs=1,
                              max_samples=512, clip_model="models/clip-vit-base-patch32",
                              save_dir=str(REPO / "outputs/_inner")))
        tr = GapAwareTrainer(cfg)
        tr.device = device
        tr.setup_model()
        params = [(n, p) for n, p in tr.model.named_parameters() if p.requires_grad]
        tr.model.eval()

        acc = {"ip_v": 0.0, "ip_t": 0.0, "nv": 0.0, "nt": 0.0,
               "gv": 0.0, "gt": 0.0, "cos_v": 0.0, "cos_t": 0.0,
               "cv": 0, "ct": 0, "nb": 0}
        for b in batches:
            imgs = b["image"].to(device)
            ii = b["input_ids"].to(device)
            am = b["attention_mask"].to(device)

            # ① g_m：任务损失（对比损失）的梯度
            tr.model.zero_grad(set_to_none=True)
            o = tr.model(pixel_values=imgs, input_ids=ii, attention_mask=am)
            I = F.normalize(o.image_embeds, p=2, dim=-1)
            T_ = F.normalize(o.text_embeds, p=2, dim=-1)
            logits = 100.0 * I @ T_.T
            lab = torch.arange(I.shape[0], device=device)
            loss = (F.cross_entropy(logits, lab) + F.cross_entropy(logits.T, lab)) / 2
            loss.backward()
            gL = {n: (p.grad.detach().float().clone() if p.grad is not None else None)
                  for n, p in params}

            # ② ∇DG*：对 DG* 的梯度
            tr.model.zero_grad(set_to_none=True)
            o2 = tr.model(pixel_values=imgs, input_ids=ii, attention_mask=am)
            I2 = F.normalize(o2.image_embeds.float(), p=2, dim=-1)
            T2 = F.normalize(o2.text_embeds.float(), p=2, dim=-1)
            dg = ((I2 - T2) ** 2).sum(-1).mean()
            dg.backward()
            gD = {n: (p.grad.detach().float().clone() if p.grad is not None else None)
                  for n, p in params}

            def side_names(side):
                """该侧的参数名（**按名配对**，不按列表位置——否则 zip 会错位）。"""
                key = "vision_model" if side == "v" else "text_model"
                return [n for n in gL if key in n]

            def dot_names(names, ga, gb):
                return float(sum(torch.dot(ga[n].flatten(), gb[n].flatten()) for n in names
                                 if ga.get(n) is not None and gb.get(n) is not None))

            def nrm_names(names, g):
                return float(sum(torch.dot(g[n].flatten(), g[n].flatten()) for n in names
                                 if g.get(n) is not None)) ** 0.5

            for side, k in (("v", "v"), ("t", "t")):
                names = side_names(side)
                if not names:
                    continue
                ip = dot_names(names, gD, gL)
                nl, nd = nrm_names(names, gL), nrm_names(names, gD)
                acc[f"ip_{k}"] += ip
                acc[f"n{k}"] += nd
                acc[f"g{k}"] += nl
                if nl > 0 and nd > 0:
                    acc[f"cos_{k}"] += ip / (nl * nd)
                    acc[f"c{k}"] += 1
            acc["nb"] += 1

        nb = max(acc["nb"], 1)
        rec = {
            "arm": arm, "nb": nb,
            "ip_vision": acc["ip_v"] / nb, "ip_text": acc["ip_t"] / nb,
            "sum_ip": (acc["ip_v"] + acc["ip_t"]) / nb,
            "norm_gradDG_vision": acc["nv"] / nb, "norm_gradDG_text": acc["nt"] / nb,
            "norm_g_task_vision": acc["gv"] / nb, "norm_g_task_text": acc["gt"] / nb,
            "cos_dg_vs_task_vision": acc["cos_v"] / max(acc["cv"], 1),
            "cos_dg_vs_task_text": acc["cos_t"] / max(acc["ct"], 1),
        }
        out[arm] = rec
        print(f"     <∇_vDG*,g_v>={rec['ip_vision']:+.5f} ｜ "
              f"<∇_tDG*,g_t>={rec['ip_text']:+.5f}", flush=True)
        print(f"     Σ内积={rec['sum_ip']:+.5f} ｜ "
              f"cos(∇_vDG*,g_v)={rec['cos_dg_vs_task_vision']:+.4f} ｜ "
              f"cos(∇_tDG*,g_t)={rec['cos_dg_vs_task_text']:+.4f}", flush=True)

    print("\n=== 与实测 CGΔ 对照 ===")
    sc = json.loads(io.open(REPO / "outputs/analysis/strict_control_summary.json",
                            encoding="utf-8").read())["configs"]
    for arm in ARMS:
        r = out[arm]
        print(f"  {arm:<13} Σ内积={r['sum_ip']:+.5f} ｜ "
              f"实测 CGΔ={sc[arm]['cg_delta_mean']:+.4f}")

    sums = [out[a]["sum_ip"] for a in out]
    cgs = [sc[a]["cg_delta_mean"] for a in out]
    sp = (max(sums) - min(sums)) / abs(sum(sums) / 3) * 100
    print(f"\n  Σ内积 极差/均值 = **{sp:.2f}%**")
    print(f"  实测 CGΔ 极差   = **{max(cgs)-min(cgs):.4f}**")
    print(f"  理论排序 = {sorted(out, key=lambda a: -out[a]['sum_ip'])}")
    print(f"  实测排序 = {sorted(out, key=lambda a: sc[a]['cg_delta_mean'])}")
    print(f"  → 排序一致? "
          f"{sorted(out, key=lambda a: -out[a]['sum_ip']) == sorted(out, key=lambda a: sc[a]['cg_delta_mean'])}")

    if apply:
        OUT.parent.mkdir(parents=True, exist_ok=True)
        io.open(OUT, "w", encoding="utf-8", newline="").write(json.dumps(
            {"rows": out, "sum_ip_pct_spread": sp,
             "cg_delta_spread": max(cgs) - min(cgs),
             "cg_delta": {a: sc[a]["cg_delta_mean"] for a in out}},
            ensure_ascii=False, indent=1))
        print(f"\n  ✅ 已写 {OUT.relative_to(REPO)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
