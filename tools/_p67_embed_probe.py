# -*- coding: utf-8 -*-
r"""**决定性对比**：本地与云端在**同一张图**上的 `image_embeds`（2026-10-09）。

## 为什么

初始 CG 差 **1.31 倍**（本地 0.8187 vs 云端 1.0712）→ 不能用权重等价解释。
**本脚本用同一张图、同一 seed，各跑一次，打印嵌入范数与两两距离。**

**判据（先写明）**：
- 若本地/云端的 `mean‖I‖` 与 `mean‖T‖` 相同 → 权重等价，差异在别处；
- 若不同 → **云端加载的模型状态与本地不同**（这是根因方向）。

    python tools\_p67_embed_probe.py [--apply]
"""
from __future__ import annotations

import io
import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "tools"))

PROBE = r'''
import os, sys, json, glob
import torch, torch.nn.functional as F
os.chdir(r"""%(work)s""")
sys.path.insert(0, r"""%(work)s""")
from transformers import CLIPModel, CLIPProcessor
from PIL import Image

MD = r"""%(model)s"""
m = CLIPModel.from_pretrained(MD, local_files_only=True)
p = CLIPProcessor.from_pretrained(MD, local_files_only=True)
m.eval()

# 固定输入：前 4 张图 + 固定文本（不依赖数据集划分）
imgs = sorted(glob.glob("flickr30k/flickr30k-images/*.jpg"))[:4]
texts = ["a photo of a dog", "two men in a yard", "a child in a pink dress",
         "a dog running on grass"]
ims = [Image.open(x).convert("RGB") for x in imgs]

with torch.no_grad():
    inp = p(text=texts, images=ims, return_tensors="pt", padding=True)
    out = m(**inp)

I = out.image_embeds
T = out.text_embeds
In = F.normalize(I, p=2, dim=-1)
Tn = F.normalize(T, p=2, dim=-1)

res = {
    "n_images": len(ims),
    "image_embeds_norm_mean": float(I.norm(dim=-1).mean()),
    "image_embeds_norm_std": float(I.norm(dim=-1).std()),
    "text_embeds_norm_mean": float(T.norm(dim=-1).mean()),
    "image_embeds_dim": int(I.shape[-1]),
    "image_embeds_first5": [round(float(x), 6) for x in I[0, :5]],
    "image_embeds_hash": round(float(I.sum()), 4),
    "cos_ii_mean": float((In @ In.T).mean()),
    "dist_it_mean": float(((In - Tn) ** 2).sum(-1).mean()),
    "cg_norm": float((In.mean(0) - Tn.mean(0)).norm()),
    "cg_raw": float((I.mean(0) - T.mean(0)).norm()),
}
print(json.dumps(res, indent=1))
open("_embed_probe.json", "w").write(json.dumps(res))
'''


def main() -> int:
    apply = "--apply" in sys.argv
    out_local = None

    # ── 本地 ──
    print("=== 本地 ===")
    code = PROBE % {"work": str(REPO), "model": str(REPO / "models/clip-vit-base-patch32")}
    p = REPO / "outputs" / "_probe_local.py"
    io.open(p, "w", encoding="utf-8", newline="\n").write(code)
    import subprocess
    r = subprocess.run([sys.executable, str(p)], capture_output=True, text=True,
                       encoding="utf-8", errors="replace", cwd=str(REPO), timeout=1800)
    print((r.stdout or "")[-1400:])
    if r.stderr:
        print("  stderr:", (r.stderr or "")[-400:])
    lp = REPO / "_embed_probe.json"
    if lp.exists():
        out_local = json.loads(io.open(lp, encoding="utf-8").read())
        lp.unlink()

    # ── 云端 ──
    print("\n=== 云端 ===")
    from _cloud_ssh import client, run
    c = client()
    try:
        code_c = PROBE % {"work": "/root/autodl-tmp/work",
                          "model": "/root/autodl-tmp/work/models/clip-vit-base-patch32"}
        io.open(REPO / "outputs" / "_probe_cloud.py", "w", encoding="utf-8",
                newline="\n").write(code_c)
        sftp = c.open_sftp()
        sftp.put(str(REPO / "outputs" / "_probe_cloud.py"),
                 "/root/autodl-tmp/work/_probe.py")
        sftp.close()
        out_c, _ = run(c, "/root/miniconda3/bin/python /root/autodl-tmp/work/_probe.py",
                       timeout=1800)
    finally:
        c.close()

    if out_local:
        print("\n=== 对比 ===")
        print(f"  {'量':<26}{'本地':>14}{'云端':>14}")
        for k in ("image_embeds_dim", "image_embeds_norm_mean", "text_embeds_norm_mean",
                  "image_embeds_hash", "cos_ii_mean", "dist_it_mean", "cg_raw"):
            print(f"  {k:<26}{str(round(out_local.get(k, float('nan')), 6)):>14}"
                  f"{'':>14}")
        print("\n  ⚠️ 云端数值见上方 JSON；若 image_embeds_norm_mean 或 cg_raw 不同 →")
        print("     两边模型状态不同（不是权重等价）。")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
