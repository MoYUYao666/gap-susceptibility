# -*- coding: utf-8 -*-
r"""下载 `openai/clip-vit-base-patch16` 到本地 `models/`（2026-10-07，操作者选 A）。

## 为什么

实验 ③（补 patch-16 骨干）需要它。当前 patch-16 组**只有 BioCLIP 一个成员**，
这是"patch size 规律"的软肋——审稿人会说那是个体差异而非规律。

## 与项目规则的说明

项目规则要求"模型权重**在服务器上下载**，禁止本地下载后上传服务器"——
**本次不涉及上传**：实验 ③ 就在**本机**跑（RTX 4060），故在本地下载是必要且无冲突的。

## 用镜像（国内网络）

优先 **hf-mirror.com**（项目既有做法），失败再退 HF 官方。

    python tools\_p4_download_clip_b16.py [--apply]
"""
from __future__ import annotations

import io
import os
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
DST = REPO / "models" / "clip-vit-base-patch16"
REPO_ID = "openai/clip-vit-base-patch16"


def main() -> int:
    apply = "--apply" in sys.argv
    print(f"  目标: {DST}")
    print(f"  来源: {REPO_ID}")
    if DST.exists() and any(DST.iterdir()):
        n = sum(f.stat().st_size for f in DST.rglob("*") if f.is_file())
        print(f"  ✅ 已存在（{n/2**20:.0f} MB），跳过下载")
        return 0
    if not apply:
        print("  （预演；加 --apply 实下）")
        return 0

    os.environ.setdefault("HF_ENDPOINT", "https://hf-mirror.com")
    os.environ.setdefault("HF_HUB_DISABLE_XET", "1")
    print(f"  HF_ENDPOINT={os.environ['HF_ENDPOINT']}")
    from huggingface_hub import snapshot_download

    p = snapshot_download(repo_id=REPO_ID, local_dir=str(DST),
                          allow_patterns=["*.json", "*.txt", "*.bin", "*.safetensors", "*.model"])
    n = sum(f.stat().st_size for f in Path(p).rglob("*") if f.is_file())
    print(f"  ✅ 完成: {p} ｜ {n/2**20:.0f} MB ｜ {len(list(Path(p).rglob('*')))} 条目")

    # 完整性：能否加载 + 两塔是否如预期
    import torch
    from transformers import CLIPModel, CLIPProcessor
    m = CLIPModel.from_pretrained(str(DST), torch_dtype=torch.float32)
    _ = CLIPProcessor.from_pretrained(str(DST))
    nparam = sum(x.numel() for x in m.parameters())
    patch = m.config.vision_config.patch_size
    print(f"  校验: 参数量 {nparam/1e6:.1f}M ｜ patch_size = {patch}")
    assert patch == 16, f"patch_size 应为 16，实为 {patch}"
    assert DST.exists()
    print("  ✅ 断言通过（patch_size = 16，模型可加载）")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
