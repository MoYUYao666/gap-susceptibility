# -*- coding: utf-8 -*-
r"""量化「评测画廊继承 train transform」对 CG/DG/R@1 的影响（2026-10-12）。

## 复现论文冻结基线口径

由 `src/gap_metrics.py:86-98` 的**实现**（不是我的猜测）：
- `centroid_gap = ‖μ_I − μ_T‖₂`（**未归一化**）
- `centroid_gap_norm = centroid_gap / √D`（D = 嵌入维度）
- `distribution_gap = √(centroid_gap² + ‖σ_I − σ_T‖₂²)`

对照归档 `outputs/flickr30k/baseline_frozen/results.json::initial_gap`：
`centroid_gap = 0.8185`、`distribution_gap = 0.8651`、`centroid_gap_norm = 0.03617`
→ `0.8185 / √512 = 0.03618` ✅ **与实现一致**（D=512）。

**⚠️ 先前版本的本 docstring 写成 `CG / mean_cosine_pos`，是错的**（已按源码更正；
由审计成员指出，`src/gap_metrics.py:92`）。

**做法**：同一冻结 CLIP、同一画廊定义，重复 N 次评测（每次重读图 → 随机变换重新抽），
统计 CG/DG/R@1 的**均值、sd、极差**。

## 为什么用 CPU

GPU 被 task-8 占用（项目铁律：单进程串行）。500 对画廊在 CPU 上可接受。

    python tools\_p383_gallery_noise_cg.py --repeats 10 --apply
"""
from __future__ import annotations

import argparse
import io
import json
import os
import statistics
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
OUT = REPO / "outputs" / "analysis" / "gallery_noise_cg.json"


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--repeats", type=int, default=10)
    ap.add_argument("--pairs", type=int, default=500)
    ap.add_argument("--apply", action="store_true")
    a = ap.parse_args()
    os.environ["CUDA_VISIBLE_DEVICES"] = ""
    os.environ.setdefault("HF_HUB_OFFLINE", "1")
    sys.path.insert(0, str(REPO))

    import torch
    from transformers import CLIPModel, CLIPProcessor
    from src.dataset import create_dataloaders

    mp = REPO / "models" / "clip-vit-base-patch32"
    print("  载入 CLIP B/32（CPU）…")
    model = CLIPModel.from_pretrained(str(mp), local_files_only=True).eval()
    proc = CLIPProcessor.from_pretrained(str(mp), local_files_only=True)

    tr, va, te = create_dataloaders(data_dir=str(REPO), dataset_name="flickr30k",
                                    batch_size=64, num_workers=0, max_samples=5000,
                                    image_size=224)
    base = va.dataset
    real = base.dataset if hasattr(base, "dataset") else base
    idx = list(base.indices)[:a.pairs] if hasattr(base, "indices") else list(range(a.pairs))
    print(f"  画廊：{len(idx)} 对（val 子集，继承 train transform）")

    # 文本侧固定（每对一条 caption）
    texts = []
    for i in idx:
        it = real[i]
        cap = it.get("caption") or it.get("text") or ""
        texts.append(cap if isinstance(cap, str) else str(cap))
    def as_tensor(o):
        """兼容不同 transformers 版本：返回 tensor 或取 .pooler_output / [0]。"""
        if torch.is_tensor(o):
            return o
        for k in ("pooler_output", "text_embeds", "image_embeds", "last_hidden_state"):
            v = getattr(o, k, None)
            if torch.is_tensor(v):
                return v
        if isinstance(o, (tuple, list)) and torch.is_tensor(o[0]):
            return o[0]
        raise TypeError(f"无法从 {type(o).__name__} 取 tensor")

    with torch.no_grad():
        tk = proc(text=texts, return_tensors="pt", padding=True, truncation=True,
                  max_length=77)
        T = as_tensor(model.get_text_features(**tk))
        T = T / T.norm(dim=-1, keepdim=True)

    rows = []
    for r in range(a.repeats):
        vecs = []
        with torch.no_grad():
            for i in idx:
                it = real[i]
                im = it["image"] if isinstance(it, dict) else it[0]
                f = as_tensor(model.get_image_features(pixel_values=im.unsqueeze(0)))
                vecs.append(f / f.norm(dim=-1, keepdim=True))
        I = torch.cat(vecs, 0)
        muI, muT = I.mean(0), T.mean(0)
        sI, sT = I.std(0), T.std(0)
        CG = float((muI - muT).norm())
        DG = float(((muI - muT).norm() ** 2 + (sI - sT).norm() ** 2) ** 0.5)
        # 检索 R@1（i2t，对角）
        sim = I @ T.t()
        r1 = float((sim.argmax(1) == torch.arange(len(idx))).float().mean())
        cg_norm = CG / float((I * T).sum(1).mean())
        rows.append({"repeat": r, "CG": CG, "DG": DG, "R@1_i2t": r1, "CG_norm": cg_norm})
        print(f"    repeat {r+1}/{a.repeats}: CG={CG:.6f} DG={DG:.6f} R@1={r1:.4f}")

    def stat(k):
        v = [x[k] for x in rows]
        return {"mean": round(statistics.mean(v), 6),
                "sd": round(statistics.pstdev(v), 6) if len(v) > 1 else None,
                "min": round(min(v), 6), "max": round(max(v), 6),
                "range": round(max(v) - min(v), 6)}

    res = {
        "script": "tools/_p383_gallery_noise_cg.py",
        "root_cause": "src/dataset.py:416-425 random_split(Subset) inherits the train transform",
        "repeats": a.repeats, "pairs": len(idx),
        "stats": {k: stat(k) for k in ("CG", "DG", "R@1_i2t", "CG_norm")},
        "per_repeat": rows,
        "paper_frozen_reference": {
            "source": "outputs/flickr30k/baseline_frozen/results.json::initial_gap",
            "centroid_gap": 0.8185005187988281,
            "distribution_gap": 0.8651171234788589,
        },
    }
    print()
    for k in ("CG", "DG", "R@1_i2t"):
        s = res["stats"][k]
        print(f"  {k:<9} 均值 {s['mean']} ｜ sd {s['sd']} ｜ 极差 {s['range']}")
    print()
    print("  对照论文臂间差异：ΔCG 0.02–0.05 ｜ R@1 0.01–0.07")
    print(f"  → CG 抽样 sd {res['stats']['CG']['sd']} ｜ R@1 抽样 sd {res['stats']['R@1_i2t']['sd']}")

    if a.apply:
        OUT.parent.mkdir(parents=True, exist_ok=True)
        io.open(OUT, "w", encoding="utf-8", newline="").write(
            json.dumps(res, ensure_ascii=False, indent=1))
        print(f"  ✅ 已写 {OUT.relative_to(REPO)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
