# -*- coding: utf-8 -*-
r"""云端：查**结果与本地不一致**的根因（2026-10-09）。

## 实测不一致

| 配置 | 云端 | 本地 | 差异 |
|---|---|---|---|
| B/32 text_only | −0.0250 / −0.0283 | −0.0274 / −0.0297 | ✅ 接近 |
| **B/32 both** | **+0.1882** | **−0.0186** | ❌ **符号相反** |
| **B/32 vision_only** | **+0.2104** | **+0.0124** | ❌ 差 17 倍 |
| B/16 text_only | −0.0077 | −0.0190 | ❌ 差 2.5 倍 |

**必须查清"云端跑的到底是什么"，否则结果是污染而非验证。**

怀疑清单：
1. **模型加载错误**（`--model` 指向的目录内容不对；`CLIPModel.from_pretrained` 静默取错权重）；
2. **数据不同**（我上传的是"前 1000 张图"的子集，本地跑的是全部）；
3. **transformers 5.19 vs 5.16 行为差异**；
4. **`initial_gap` 的基线计算路径不同**（`--skip-frozen` 与冻结基线的关系）。

**本脚本逐项实测。**

    $env:CLOUD_PW='...'; python tools\_cloud_discrepancy.py
"""
from __future__ import annotations

import io
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "tools"))

REMOTE = r'''
import os, json, glob, subprocess
W = "/root/autodl-tmp/work"
os.chdir(W)

print("=== ① 各模型 config 核对（确认加载的是哪个模型）===")
for d in ("models/clip-vit-base-patch32", "models/clip-vit-base-patch16", "models/openclip"):
    p = os.path.join(d, "config.json")
    if not os.path.exists(p):
        print("  %-34s 无 config.json" % d); continue
    c = json.load(open(p))
    v = c.get("vision_config", {})
    t = c.get("text_config", {})
    print("  %-34s patch=%s vision_hidden=%s layers=%s ｜ text_hidden=%s ｜ arch=%s"
          % (d, v.get("patch_size"), v.get("hidden_size"), v.get("num_hidden_layers"),
             t.get("hidden_size"), c.get("architectures")))

print("\n=== ② 权重实际加载（比对首层权重的统计量）===")
import torch
from transformers import CLIPModel
for d in ("models/clip-vit-base-patch32", "models/clip-vit-base-patch16", "models/openclip"):
    try:
        m = CLIPModel.from_pretrained(d, local_files_only=True)
        vw = m.vision_model.embeddings.patch_embedding.weight
        tw = m.text_model.embeddings.token_embedding.weight
        print("  %-34s patch_embed mean=%+.5f std=%.5f ｜ tok_emb mean=%+.5f std=%.5f"
              % (d, vw.mean().item(), vw.std().item(), tw.mean().item(), tw.std().item()))
    except Exception as e:
        print("  %-34s FAIL %s" % (d, str(e)[:90]))

print("\n=== ③ 数据规模（本地是全部 31783 图 vs 云端只上传 1000 图）===")
n = len(glob.glob("flickr30k/flickr30k-images/*.jpg"))
print("  云端图片数: %d" % n)
print("  → ⚠️ 本地有 31783 张；云端只有 1000 张（前 1000 张）")
print("     max_samples=5000 时，本地能取到 5000 条（1000 图 × 5 标注）")
print("     云端取到的也是 1000 图 × 5 = 5000 条 —— **数量相同**，但")

print("\n=== ④ 关键：text_only 为何接近而 both/vision_only 差很多 ===")
print("  读云端 B/32 三臂的完整 results.json 字段，看 baseline 与 arm 的关系")
for arm in ("text_only", "both", "vision_only"):
    f = "outputs/strict_freeze_b32_r4/%s/seed123/results.json" % arm
    if not os.path.exists(f):
        continue
    d = json.load(open(f))
    print("  --- %s" % arm)
    for k in ("initial_gap", "final_gap", "frozen_baseline"):
        if k in d:
            print("      %-16s %s" % (k, json.dumps(d[k], ensure_ascii=False)[:150]))
    for k in sorted(d):
        if "r@" in k.lower() or "recall" in k.lower() or "n_trainable" in k:
            print("      %-16s %s" % (k, d[k]))
'''


def main() -> int:
    from _cloud_ssh import client, run

    c = client()
    try:
        io.open(REPO / "outputs" / "_remote_disc.py", "w", encoding="utf-8",
                newline="\n").write(REMOTE)
        sftp = c.open_sftp()
        sftp.put(str(REPO / "outputs" / "_remote_disc.py"),
                 "/root/autodl-tmp/work/_disc.py")
        sftp.close()
        run(c, "/root/miniconda3/bin/python /root/autodl-tmp/work/_disc.py", timeout=600)
    finally:
        c.close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
