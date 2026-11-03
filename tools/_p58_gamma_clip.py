# -*- coding: utf-8 -*-
r"""补测**完整** `Γ_m`（含 `cos φ_m`）在 CLIP 三臂上的值（2026-10-08）。

## 为什么必须补

`tools/_p57` 只用归档的 `norm_g_vision` / `norm_g_text`（**只有范数，没有 cos**），
发现"范数大的一侧 ≠ 效果更好"。**但论文的 `Γ_m = ‖∇_mDG*‖·cos φ_m` 是完整量**，
`Γ_m` 与 `‖g_m‖` 的乘积才进入动力学：

    d(DG*)/dt = −η Σ_m Γ_m ‖g_m‖

**故只用范数推断预测力是不完整的**。本脚本实测**完整 `Γ_m`**（含 cos）。

## 判据（先写明）

对 CLIP B/32 的三臂各做一次 `∇DG*` 反传，计算两侧的
`‖∇_mDG*‖`、`cos φ_m`（与**全部可训梯度**的夹角）、**`Γ_m`**；
然后比较 `Γ_m·‖g_m‖` 与实测 `CGΔ` 的**符号与量级**是否一致。

**注意**：论文的 `Γ_m` 是**轨迹平均**，本测为**单批瞬时**——两者不等价，
须计算**多批平均**以缩小差距（本脚本取 8 批平均）。

    python tools\_p58_gamma_clip.py [--apply]
"""
from __future__ import annotations

import io
import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO))
sys.path.insert(0, str(REPO / "src"))
OUT = REPO / "outputs" / "analysis" / "gamma_clip.json"

ARMS = {
    "text_only":   dict(apply_to_vision=False, apply_to_text=True),
    "both":        dict(apply_to_vision=True,  apply_to_text=True),
    "vision_only": dict(apply_to_vision=True,  apply_to_text=False),
}
RANK = 8
N_BATCHES = 8      # 多批平均以近似"轨迹平均"


def main() -> int:
    apply = "--apply" in sys.argv
    if not apply:
        print("=== 补测完整 Γ_m（CLIP B/32，三臂，8 批平均）===")
        print("  Γ_m = ‖∇_m DG*‖ · cos φ_m（cos 为与全部可训梯度的夹角）")
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
    print(f"=== 完整 Γ_m 测量（device={device}，{len(batches)} 批）===", flush=True)

    out = {}
    for arm, flags in ARMS.items():
        print(f"\n  ── {arm} ──", flush=True)
        torch.manual_seed(42)
        cfg = ExperimentConfig(
            name=f"gamma_{arm}",
            lora=LoRAConfig(rank=RANK, alpha=RANK * 2, **flags),
            train=TrainConfig(dataset="flickr30k", batch_size=64, num_epochs=1,
                              max_samples=512, clip_model="models/clip-vit-base-patch32",
                              save_dir=str(REPO / "outputs/_gamma_clip")))
        tr = GapAwareTrainer(cfg)
        tr.device = device
        tr.setup_model()
        params = [p for p in tr.model.parameters() if p.requires_grad]
        tr.model.eval()

        acc = {"nv": 0.0, "nt": 0.0, "cv": [], "ct": [], "nb": 0}
        for b in batches:
            tr.model.zero_grad(set_to_none=True)
            with torch.enable_grad():
                imgs = b["image"].to(device)
                ii = b["input_ids"].to(device)
                am = b["attention_mask"].to(device)
                o = tr.model(pixel_values=imgs, input_ids=ii, attention_mask=am)
                I = F.normalize(o.image_embeds.float(), p=2, dim=-1)
                T = F.normalize(o.text_embeds.float(), p=2, dim=-1)
                dg = ((I - T) ** 2).sum(-1).mean()
                dg.backward()
            grads = [(n, p.grad.detach().float().flatten())
                     for n, p in tr.model.named_parameters()
                     if p.requires_grad and p.grad is not None]
            gv = [(n, g) for n, g in grads if "vision_model" in n]
            gt = [(n, g) for n, g in grads if "text_model" in n]

            def dot(a, b):
                return float(sum(torch.dot(x, y) for (_, x), (_, y) in zip(a, b)))

            nv = dot(gv, gv) ** 0.5 if gv else 0.0
            nt = dot(gt, gt) ** 0.5 if gt else 0.0
            tot = dot(grads, grads) ** 0.5
            acc["nv"] += nv
            acc["nt"] += nt
            if gv and tot > 0:
                acc["cv"].append(dot(gv, gv) / (nv * tot))
            if gt and tot > 0:
                acc["ct"].append(dot(gt, gt) / (nt * tot))
            acc["nb"] += 1

        nb = max(acc["nb"], 1)
        nv, nt = acc["nv"] / nb, acc["nt"] / nb
        cv = sum(acc["cv"]) / len(acc["cv"]) if acc["cv"] else float("nan")
        ct = sum(acc["ct"]) / len(acc["ct"]) if acc["ct"] else float("nan")
        rec = {"arm": arm, "n_batches": nb,
               "norm_grad_vision": nv, "norm_grad_text": nt,
               "cos_phi_vision": cv, "cos_phi_text": ct,
               "Gamma_vision": nv * cv if acc["cv"] else 0.0,
               "Gamma_text": nt * ct if acc["ct"] else 0.0}
        out[arm] = rec
        print(f"     ‖∇_vDG*‖={nv:.4f} cos_v={cv:+.4f} → Γ_v={rec['Gamma_vision']:+.4f}", flush=True)
        print(f"     ‖∇_tDG*‖={nt:.4f} cos_t={ct:+.4f} → Γ_t={rec['Gamma_text']:+.4f}", flush=True)

    print("\n=== 与实测 CGΔ 对照 ===")
    sc = json.loads(io.open(REPO / "outputs/analysis/strict_control_summary.json",
                            encoding="utf-8").read())["configs"]
    for arm in ARMS:
        r = out[arm]
        print(f"  {arm:<12} Γ_v={r['Gamma_vision']:+.4f} Γ_t={r['Gamma_text']:+.4f} "
              f"｜ 实测 CGΔ={sc[arm]['cg_delta_mean']:+.4f}")

    if apply:
        OUT.parent.mkdir(parents=True, exist_ok=True)
        io.open(OUT, "w", encoding="utf-8", newline="").write(json.dumps(
            {"model": "CLIP ViT-B/32", "rank": RANK, "n_batches": N_BATCHES,
             "note": "single-pass average over batches; paper Gamma_m is trajectory-averaged",
             "arms": out}, ensure_ascii=False, indent=1))
        print(f"\n  ✅ 已写 {OUT.relative_to(REPO)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
