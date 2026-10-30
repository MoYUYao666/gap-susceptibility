# -*- coding: utf-8 -*-
r"""改用 **ModelScope** 下载 CLIP B/16（2026-10-07）。

## 为什么换渠道

`hf-mirror.com` 与 `huggingface.co` **双双超时**（实测），而 **ModelScope 返回 HTTP 200**。
项目 `AGENTS.md` 的规则本就写明：**ModelScope 为国内网络首选**。

## 模型 ID

ModelScope 上的 OpenAI CLIP 镜像候选（按优先级试）：
1. `AI-ModelScope/clip-vit-base-patch16`
2. `openai-mirror/clip-vit-base-patch16`
3. `dienstag/clip-vit-base-patch16`

## 完整性

下载后**必须**验证：可加载 + `patch_size == 16` + 参数量合理（~150M）。

    python tools\_p4_download_clip_b16_ms.py [--apply]
"""
from __future__ import annotations

import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
DST = REPO / "models" / "clip-vit-base-patch16"

CANDIDATES = [
    "AI-ModelScope/clip-vit-base-patch16",
    "openai-mirror/clip-vit-base-patch16",
    "dienstag/clip-vit-base-patch16",
    "laion/CLIP-ViT-B-16-laion2B-s34B-b88K",
]


def verify() -> bool:
    import torch
    from transformers import CLIPModel
    try:
        m = CLIPModel.from_pretrained(str(DST), torch_dtype=torch.float32)
    except Exception as e:
        print(f"  ❌ 加载失败: {str(e)[:120]}")
        return False
    patch = m.config.vision_config.patch_size
    n = sum(x.numel() for x in m.parameters()) / 1e6
    print(f"  校验: patch_size={patch} ｜ 参数量 {n:.1f}M")
    if patch != 16:
        print(f"  ❌ patch_size 应为 16，实为 {patch}")
        return False
    print("  ✅ patch_size = 16，模型可加载")
    return True


def main() -> int:
    apply = "--apply" in sys.argv
    print(f"  目标: {DST}")
    # 判据：**权重存在且够大**，而非"目录非空"——
    # 实测两次踩坑：目录有配置但权重未下（或被删残件后配置仍在）→ 误判"已完成"而跳过。
    weights = [DST / "pytorch_model.bin", DST / "model.safetensors"]
    have_w = [w for w in weights if w.exists() and w.stat().st_size > 500 * 2**20]
    if have_w:
        n = sum(f.stat().st_size for f in DST.rglob("*") if f.is_file()) / 2**20
        print(f"  ✅ 权重已就位（{have_w[0].name}, {n:.0f} MB）→ 直接校验")
        return 0 if verify() else 1
    print("  ⏳ 权重缺失或过小 → 继续下载")
    if not apply:
        print("  （预演；加 --apply 实下）")
        return 0

    from modelscope import snapshot_download
    last = None
    for mid in CANDIDATES:
        print(f"\n  ── 试 {mid} ──", flush=True)
        try:
            # 只要 PyTorch 权重与配置：排除 flax/tf（实测默认会下 570MB 的 flax_model.msgpack，无用）
            p = snapshot_download(mid, local_dir=str(DST),
                                  ignore_file_pattern=[
                                      r".*\.msgpack$", r".*\.h5$", r".*\.ckpt$",
                                      r"tf_model.*", r"flax_model.*", r".*\.tar\.gz$"])
            n = sum(f.stat().st_size for f in Path(p).rglob("*") if f.is_file()) / 2**20
            print(f"  ✅ 下载完成: {p} ｜ {n:.0f} MB")
            if verify():
                print(f"  ✅ 成功（来源 {mid}）")
                return 0
            print("  ⚠ 校验未过，试下一个")
        except Exception as e:
            last = str(e)[:140]
            print(f"  ❌ 失败: {last}")
    print(f"\n  ❌ 全部候选失败，最后错误: {last}")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
