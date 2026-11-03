# -*- coding: utf-8 -*-
r"""**优先级 2**：核心机制——间隙方向 与 适配子空间的关系（2026-10-05）。

## 动机

论文说"**视觉侧干预有害**"，但这是**框架预测**，没有**直接测过机制**。
若能把"位置效应"升级为"机制解释"，是审稿人最想看的。

## 做三件事

### ① 间隙方向是否近似**秩 1**？

$\hat d = \overline{z^I - z^T}$（单位向量）。
- **解释方差** $= \|\hat d\|^2 / \text{mean}\|z^I_i - z^T_i\|^2$ —— 若接近 1，间隙基本是**单一方向**。
- 与 `sharma2026readout`（CLIP/SigLIP 上 94.4–99.9%）对照。

### ② LoRA 更新与间隙方向的对齐度

对每个适配层：$\Delta W = \text{scaling}\cdot BA$，贴到对应权重形状。
- **对齐度** $= |\langle \Delta W, \hat d\,\hat d^\top\rangle_F| / \|\Delta W\|_F$ —— 即 $\Delta W$ 里"沿间隙方向"的成分占比。
- **对照**：同形状**随机矩阵**的同样指标（排除"任何矩阵都有一定对齐"的平凡解释）。

### ③ 对齐度能否预测 ΔCG？

按位置（text_only / both / vision_only）比较对齐度与实测 ΔCG——若同序，则机制成立。

## 数据

- 检查点：`outputs/strict_freeze/*/seed42/best_checkpoint.pt`（含 `lora_state_dict`，48 键）
- 嵌入：现算（冻结 CLIP + Flickr30k 样本）

## 通过判据（先写明）

- ① **解释方差 > 0.5** → 间隙确有主导方向
- ② **对齐度显著高于随机对照**（如 >2 倍）→ LoRA 更新非随机地指向间隙方向
- ③ **对齐度与 ΔCG 同序** → 机制成立；**若不同序，如实记录**（也是结果）

    python tools\_exp2_mechanism_gap_direction.py [--apply]
"""
from __future__ import annotations

import glob
import json
import os
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO))
os.chdir(REPO)

PRISTINE = str(REPO / "models" / "clip-vit-base-patch32")
OUT = REPO / "outputs" / "theory" / "gap_direction"
MAX_SAMPLES, BATCH = 2000, 64


def main() -> int:
    apply = "--apply" in sys.argv
    print("=== 优先级 2：间隙方向 vs 适配子空间 ===")
    print("  ① 间隙方向的秩 1 程度（解释方差）")
    print("  ② LoRA 更新与间隙方向的对齐度（含随机对照）")
    print("  ③ 对齐度 vs 实测 ΔCG（按位置）")
    if not apply:
        print("\n  （预演；加 --apply 实跑，需 GPU 数分钟）")
        return 0

    import torch
    import torch.nn.functional as F
    from src.dataset import create_dataloaders

    dev = "cuda" if torch.cuda.is_available() else "cpu"
    from transformers import CLIPModel, CLIPProcessor
    model = CLIPModel.from_pretrained(PRISTINE, local_files_only=True).to(dev).eval()
    proc = CLIPProcessor.from_pretrained(PRISTINE, local_files_only=True)

    loader, _, _ = create_dataloaders(dataset_name="flickr30k", data_dir=".",
                                      batch_size=BATCH, max_samples=MAX_SAMPLES)
    I, T = [], []
    with torch.no_grad():
        for b in loader:
            o = model(pixel_values=b["image"].to(dev),
                      input_ids=b["input_ids"].to(dev),
                      attention_mask=b["attention_mask"].to(dev), return_loss=False)
            I.append(F.normalize(o.image_embeds, p=2, dim=-1).cpu())
            T.append(F.normalize(o.text_embeds, p=2, dim=-1).cpu())
    IE, TE = torch.cat(I), torch.cat(T)
    print(f"  嵌入: {IE.shape[0]} 对, 维度 {IE.shape[1]}")

    diff = IE - TE
    d_hat_raw = diff.mean(dim=0)
    d_norm = d_hat_raw.norm()
    d_hat = d_hat_raw / d_norm
    mean_sq = (diff ** 2).sum(dim=-1).mean().item()

    # ① 秩 1 解释方差
    proj = (diff @ d_hat)
    explained = (proj ** 2).mean().item()
    ev_ratio = explained / mean_sq
    print("\n  ① 秩 1 检验")
    print(f"     ‖mean(img−txt)‖          = {d_norm:.4f}")
    print(f"     mean‖z_i^I − z_i^T‖²     = {mean_sq:.4f}")
    print(f"     沿 d̂ 的解释方差           = {explained:.4f}")
    print(f"     → 解释方差占比            = {ev_ratio:.4f}")
    print(f"     → 判据（>0.5）: {'✅ 有主导方向' if ev_ratio > 0.5 else '⚠ 无单一主导方向'}")
    # 谱：最强奇异值占比
    U, S, V = torch.svd_lowrank(diff - diff.mean(0, keepdim=True), q=8)
    print(f"     中心化后前 3 奇异值        = {[round(float(x),3) for x in S[:3]]}")
    print(f"     第一奇异值占总能量         = {(S[0]**2/ (S**2).sum()):.4f}")

    # ② LoRA 更新与 d̂ 的对齐度
    print("\n  ② LoRA 更新对齐度（含随机对照）")
    results = {}
    for ck in sorted(glob.glob("outputs/strict_freeze/*/seed42/best_checkpoint.pt")):
        arm = Path(ck).parent.parent.name
        d = torch.load(ck, map_location="cpu", weights_only=False)
        sd = d.get("lora_state_dict") or {}
        if not sd:
            print(f"     {arm}: 无 lora_state_dict，跳过")
            continue
        # 按层聚合：每层的 ΔW 用该层 A/B 重建（out×in）
        per_layer = {}
        for k, v in sd.items():
            if "lora_A" in k:
                base = k.replace(".lora_A.weight", "")
                per_layer.setdefault(base, {})["A"] = v
            elif "lora_B" in k:
                base = k.replace(".lora_B.weight", "")
                per_layer.setdefault(base, {})["B"] = v
        num = den = 0.0
        for base, m in per_layer.items():
            if "A" not in m or "B" not in m:
                continue
            A, B = m["A"].float(), m["B"].float()          # (r,in) (out,r)
            dW = B @ A                                      # (out,in)
            # 该层面对应的间隙方向切片：按 in 维度取（做不到精确对应时用 d̂ 的前 in 维）
            in_dim = dW.shape[1]
            dv = d_hat[:in_dim] if in_dim <= d_hat.numel() else d_hat
            dv = dv / dv.norm()
            # 沿间隙方向的秩 1 成分
            num += float((dW @ dv).norm())
            den += float(dW.norm())
        align = num / den if den else float("nan")
        # 随机对照（同形状）
        rnd = []
        for base, m in per_layer.items():
            if "A" not in m or "B" not in m:
                continue
            A, B = m["A"].float(), m["B"].float()
            Ar, Br = torch.randn_like(A), torch.randn_like(B)
            dWr = Br @ Ar
            dv = d_hat[:dWr.shape[1]]
            dv = dv / dv.norm()
            rnd.append(float((dWr @ dv).norm()) / float(dWr.norm()))
        import statistics as st
        rnd_m = st.mean(rnd) if rnd else float("nan")
        results[arm] = dict(align=align, random=rnd_m, n_layers=len(per_layer))
        print(f"     {arm:<12} 对齐度={align:.4f} ｜ 随机对照={rnd_m:.4f} ｜ 比值={align/rnd_m:.2f}×"
              f" ｜ 层数={len(per_layer)}")

    # ③ 对齐度 vs 实测 ΔCG
    print("\n  ③ 对齐度 vs 实测 ΔCG")
    dcg = {}
    for f in glob.glob("outputs/strict_freeze/*/seed*/results.json"):
        arm = Path(f).parent.parent.name
        r = json.loads(Path(f).read_text(encoding="utf-8", errors="ignore"))
        ig, fg = r.get("initial_gap") or {}, r.get("final_gap") or {}
        if ig.get("centroid_gap") is not None and fg.get("centroid_gap") is not None:
            dcg.setdefault(arm, []).append(fg["centroid_gap"] - ig["centroid_gap"])
    import statistics as st
    rows = []
    for arm in results:
        if arm in dcg and dcg[arm]:
            rows.append((arm, results[arm]["align"], st.mean(dcg[arm])))
            print(f"     {arm:<12} 对齐度={results[arm]['align']:.4f} ｜ ΔCG={st.mean(dcg[arm]):+.4f}")
    if len(rows) >= 3:
        a = [r[1] for r in rows]; g = [r[2] for r in rows]
        ma, mg = st.mean(a), st.mean(g)
        sa = sum((x - ma) ** 2 for x in a) ** 0.5
        sg = sum((x - mg) ** 2 for x in g) ** 0.5
        r_ag = sum((x - ma) * (y - mg) for x, y in zip(a, g)) / (sa * sg) if sa and sg else float("nan")
        print(f"     Pearson r(对齐度, ΔCG) = {r_ag:+.3f}（n={len(rows)}，仅 3 点，仅供参照）")

    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "gap_direction.json").write_text(json.dumps(
        {"n_pairs": int(IE.shape[0]), "embed_dim": int(IE.shape[1]),
         "mean_separation_norm": d_norm, "mean_sq_separation": mean_sq,
         "explained_variance_ratio": ev_ratio,
         "top_singular_values": [float(x) for x in S[:3]],
         "lora_alignment": results}, indent=2), encoding="utf-8")
    print(f"\n  ✅ 已写 {OUT.relative_to(REPO)}/gap_direction.json")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
