# -*- coding: utf-8 -*-
r"""**决定性对比 5**：dump 第一批的**图名与标注**，本地 vs 云端逐项比（2026-10-09）。

## 为何到这里

已排除：模型权重、预处理、脚本、数据文件、`n_trainable`、transformers 版本。
剩：**"喂进模型的 batch 内容"**。

**云端 `cosine_separation(init) = 0.000000`**（正负样本对的余弦**完全相等**）
→ 说明**一个 batch 里的图与标注不是配对成对**（或全都一样）。

**本地 = 0.141407**（配对正常）。

    python tools\_p71_batch_probe.py [--apply]
"""
from __future__ import annotations

import io
import json
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "tools"))

PROBE = r'''
import os, sys, json, hashlib
os.chdir(r"""%(work)s""")
sys.path.insert(0, r"""%(work)s""")
import torch
from src.dataset import create_dataloaders

loader, val_loader, _ = create_dataloaders(
    dataset_name="flickr30k", data_dir=".", batch_size=128, max_samples=5000)

b = next(iter(loader))
caps = b["caption"]
imgs = b["image"]
print(json.dumps({
    "batch_size": int(imgs.shape[0]),
    "n_captions": len(caps),
    "caption_head": [str(c)[:60] for c in caps[:5]],
    "caption_unique": len(set(str(c) for c in caps)),
    "caption_hash": hashlib.md5("|".join(str(c) for c in caps).encode()).hexdigest()[:16],
    "image_shape": list(imgs.shape),
    "image_sum": round(float(imgs.sum()), 4),
    "image_hash": hashlib.md5(imgs.numpy().tobytes()).hexdigest()[:16],
    "val_batches": len(val_loader),
    "val_batch_size": int(next(iter(val_loader))["image"].shape[0]),
}, indent=1))
'''


def main() -> int:
    apply = "--apply" in sys.argv
    import hashlib

    print("=== 本地 ===")
    code = PROBE % {"work": str(REPO)}
    p = REPO / "outputs" / "_bp_local.py"
    io.open(p, "w", encoding="utf-8", newline="\n").write(code)
    r = subprocess.run([sys.executable, str(p)], capture_output=True, text=True,
                       encoding="utf-8", errors="replace", cwd=str(REPO), timeout=1800)
    print((r.stdout or "")[-1200:])
    if r.stderr:
        print("  stderr:", (r.stderr or "").strip()[-500:])

    print("\n=== 云端 ===")
    from _cloud_ssh import client, run
    c = client()
    try:
        code_c = PROBE % {"work": "/root/autodl-tmp/work"}
        io.open(REPO / "outputs" / "_bp_cloud.py", "w", encoding="utf-8",
                newline="\n").write(code_c)
        sftp = c.open_sftp()
        sftp.put(str(REPO / "outputs" / "_bp_cloud.py"),
                 "/root/autodl-tmp/work/_bp.py")
        sftp.close()
        run(c, "/root/miniconda3/bin/python /root/autodl-tmp/work/_bp.py", timeout=1800)
    finally:
        c.close()

    print("\n=== 判读 ===")
    print("  若 image_hash / caption_hash 不同 → **batch 内容不同**（数据加载路径差异）")
    print("  若相同但云端 sep=0 → 差异在模型前向之后的评估逻辑")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
