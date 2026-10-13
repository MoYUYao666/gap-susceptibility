# -*- coding: utf-8 -*-
r"""查论文 run 是否归档了 `logit_scale`，并确认载入后被权重覆盖（2026-10-12）。

    python tools\_p387_logit_scale_in_archive.py [--apply]
"""
from __future__ import annotations

import argparse
import glob
import io
import json
import os
import re
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
OUT = REPO / "outputs" / "analysis" / "logit_scale_in_archive.json"


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    a = ap.parse_args()
    os.environ["CUDA_VISIBLE_DEVICES"] = ""
    os.environ.setdefault("HF_HUB_OFFLINE", "1")

    print("=" * 96)
    print("① 归档里是否记录了 logit_scale")
    print("=" * 96)
    hits = {}
    for f in glob.glob(str(REPO / "outputs" / "**" / "results.json"), recursive=True):
        t = io.open(f, encoding="utf-8", errors="replace").read()
        for m in re.finditer(r'"(logit_scale[^"]*)"\s*:\s*([-\d.eE]+|true|false|null)', t):
            key = m.group(1)
            hits.setdefault(key, []).append((str(Path(f).relative_to(REPO)), m.group(2)))
    if hits:
        for k, v in hits.items():
            vals = sorted({x[1] for x in v})
            print(f"  {k}: 出现 {len(v)} 次 ｜ 取值 {vals[:8]}")
            for rel, val in v[:3]:
                print(f"     {val}  ← {rel}")
    else:
        print("  🔴 归档里**没有任何** logit_scale 字段")

    print()
    print("=" * 96)
    print("② 载入 CLIP 后 logit_scale 是否被权重覆盖")
    print("=" * 96)
    import torch
    from transformers import CLIPModel
    mp = REPO / "models" / "clip-vit-base-patch32"
    m = CLIPModel.from_pretrained(str(mp), local_files_only=True)
    v = float(m.logit_scale.detach().reshape(-1)[0])
    print(f"  载入后 logit_scale = {v:.9f} ｜ exp = {float(torch.tensor(v).exp()):.4f}")
    print(f"  与权重 4.605170 一致: {abs(v - 4.605170) < 1e-4}")
    print(f"  与 config 2.6592 一致: {abs(v - 2.6592) < 1e-3}")

    print()
    print("=" * 96)
    print("③ 判定")
    print("=" * 96)
    if not hits:
        print("  🔴 论文归档**未记录 logit_scale** → 无法从归档验证每次训练用的尺度")
    print(f"  → 论文走 `src/trainer.py` 用 `model.logit_scale.exp()` = "
          f"**{float(torch.tensor(v).exp()):.2f}**（权重真值），"
          f"而非 config 的 2.6592 或 `_p293` 硬编码的 2.6592")
    print(f"  → DINOv2 实验（`_p293` 硬编码）用 **{float(torch.tensor(2.659260036932778).exp()):.2f}**")
    print(f"  → **尺度比 = {float(torch.tensor(v).exp()) / float(torch.tensor(2.659260036932778).exp()):.2f}×**")
    print("  → 结论：**目标函数不同 → DINOv2 的 ΔCG 不可与论文 ΔCG 并列**")

    if a.apply:
        OUT.parent.mkdir(parents=True, exist_ok=True)
        io.open(OUT, "w", encoding="utf-8", newline="").write(json.dumps(
            {"archive_logit_scale_fields": {k: sorted({x[1] for x in v}) for k, v in hits.items()},
             "loaded_logit_scale": v,
             "loaded_exp": float(torch.tensor(v).exp()),
             "hardcoded_p293": 2.659260036932778,
             "hardcoded_exp": float(torch.tensor(2.659260036932778).exp()),
             "ratio": float(torch.tensor(v).exp()) / float(torch.tensor(2.659260036932778).exp()),
             }, ensure_ascii=False, indent=1))
        print(f"\n  ✅ 已写 {OUT.relative_to(REPO)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
