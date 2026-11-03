# -*- coding: utf-8 -*-
r"""**最后决定性诊断**：同一批次喂进模型的**图与文本**，本地 vs 云端（2026-10-09）。

## 已排除（逐项有证据）

| 假设 | 证据 |
|---|---|
| 数据不同 | 前 1000 图 **md5 一致**（`045e29f159e02a31`）、CSV **md5 一致**（`b12eb13ad488e50a`） |
| 模型权重不同 | `image_embeds_hash` **完全一致**（−2.814）；`effective_rank_init` 全部 **ratio=1.0000** |
| 预处理不同 | `cos_ii`/`dist_it`/`cg` 一致到 7 位 |
| 脚本不同 | sha256 一致 |
| transformers 版本 | **对齐到 5.16.1 后仍失败** |
| `n_trainable` | 一致（245,760） |

## 剩：**"喂进模型的 batch 内容"**

云端 `cosine_separation(init) = 0.000000`（正负样本对余弦**完全相等**）+ `loss 末 = 4.81`
（≈ `log(128) = 4.852`，**随机水平**）→ **文本侧无法区分样本**。

**本脚本直接比对同批次**：图张量哈希、文本 token id、以及"配对是否正确"。

    python tools\_p73_batch_parity.py
"""
from __future__ import annotations

import io
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
caps = [str(c) for c in b["caption"]]
imgs = b["image"]
ids = b["input_ids"]
out = {
    "n": int(imgs.shape[0]),
    "n_unique_caps": len(set(caps)),
    "cap_head": caps[:3],
    "cap_md5": hashlib.md5("|".join(caps).encode()).hexdigest()[:16],
    "img_md5": hashlib.md5(imgs.numpy().tobytes()).hexdigest()[:16],
    "img_sum": round(float(imgs.sum()), 3),
    "ids_md5": hashlib.md5(ids.numpy().tobytes()).hexdigest()[:16],
    "ids_row0": ids[0].tolist()[:12],
    "ids_row1": ids[1].tolist()[:12],
    "ids_unique_rows": len(set(tuple(r.tolist()) for r in ids)),
    "val_n": int(next(iter(val_loader))["image"].shape[0]),
}
print(json.dumps(out, indent=1))
'''


def main() -> int:
    print("=== 本地 ===")
    lp = REPO / "outputs" / "_bp2_local.py"
    io.open(lp, "w", encoding="utf-8", newline="\n").write(PROBE % {"work": str(REPO)})
    r = subprocess.run([sys.executable, str(lp)], capture_output=True, text=True,
                       encoding="utf-8", errors="replace", cwd=str(REPO), timeout=1800)
    print((r.stdout or "")[-1000:])
    if r.stderr:
        print("  stderr:", (r.stderr or "").strip()[-300:])

    print("\n=== 云端 ===")
    from _cloud_ssh import client, run
    c = client()
    try:
        cp = REPO / "outputs" / "_bp2_cloud.py"
        io.open(cp, "w", encoding="utf-8", newline="\n").write(
            PROBE % {"work": "/root/autodl-tmp/work"})
        sftp = c.open_sftp()
        sftp.put(str(cp), "/root/autodl-tmp/work/_bp2.py")
        sftp.close()
        run(c, "/root/miniconda3/bin/python /root/autodl-tmp/work/_bp2.py", timeout=1800)
    finally:
        c.close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
