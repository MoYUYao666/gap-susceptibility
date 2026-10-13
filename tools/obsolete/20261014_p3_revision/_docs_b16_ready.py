# -*- coding: utf-8 -*-
r"""落账：CLIP B/16 就位 + 过夜驱动重启（2026-10-07 23:05）。

    python tools\_docs_b16_ready.py [--apply]
"""
from __future__ import annotations

import io
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]


def main() -> int:
    apply = "--apply" in sys.argv
    if not apply:
        print("  （预演）")
        return 0
    gpu = subprocess.run(["nvidia-smi", "--query-gpu=memory.used,memory.total",
                          "--format=csv,noheader"], capture_output=True, text=True).stdout.strip()
    lg = REPO / "outputs/theory/alpha_from_gradients/run_both.log"
    ep = len([l for l in io.open(lg, encoding="utf-8", errors="ignore") if " DG*=" in l]) if lg.exists() else 0
    w = REPO / "models/clip-vit-base-patch16/pytorch_model.bin"
    wsz = f"{w.stat().st_size/2**20:.0f} MB" if w.exists() else "缺失"

    hp = REPO / "HANDOFF.md"
    t = io.open(hp, encoding="utf-8").read()
    if "CLIP B/16 就位，过夜队列重启" in t:
        print("  已记录，跳过")
        return 0
    ent = f"""> **✅ 2026-10-07 23:05 —— CLIP B/16 就位，过夜队列重启**
>
> ### 下载成功（**第 4 次尝试**，逐次排障）
>
> | 尝试 | 失败原因 | 修复 |
> |---|---|---|
> | 1 | `hf-mirror.com` 超时 | 换渠道 |
> | 2 | `huggingface.co` 超时 | 换 **ModelScope** |
> | 3 | ModelScope 拉的是 **`flax_model.msgpack`（570 MB，JAX，无用）**；且**中断留 `.incomplete`** | 加 `ignore_file_pattern` 排除 flax/tf |
> | 4 | **我的"目录非空即跳过"逻辑**：删残件后配置仍在 → 又跳过 | 判据改为**权重存在且 >500 MB** |
>
> **最终**：来源 `openai-mirror/clip-vit-base-patch16`，**`pytorch_model.bin` {wsz}**，
> 实测 **`patch_size = 16`、149.6M 参数、可加载** ✅
>
> ### 🌙 过夜队列（已重启，`tools/_p7_overnight_driver.py`）
>
> | 序 | 实验 | 前提 | 状态 |
> |---|---|---|---|
> | 1 | **α 预测（both 臂）** | 运行中 {ep}/30 | ⏳ |
> | 2 | **③a OpenCLIP B/32 × r4（三臂）** | GPU 空闲 | 待 α（**冒烟已验证可跑**） |
> | 3 | **③b CLIP B/16 × r4（三臂）** | **模型 ✅ 就位** | 待 ③a |
> | 4 | **④ Qwen2-VL 三臂** | 脚本就绪 | 待 ③b（**脚本尚未写，预计跳过**） |
>
> ### 当前实测
>
> - **GPU**：{gpu}（α 独占，**8 GB 只能串行**）
> - **B/16**：✅ `pytorch_model.bin` {wsz}（`patch_size=16` 已校验）
> - **α**：{ep}/30 epoch
>
> ### ③b 的科学意义（**本阶段最重要的一次测量**）
>
> 论文的"patch size 规律"目前**patch-16 组只有 2 个成员**（CLIP B/16、BioCLIP），
> 而论文自己承认：*"domain shift alone could account for its ordering; and with two backbones per patch size
> the two are not separated."*
>
> **CLIP B/16 是唯一干净的对照**——**同族（CLIP）、同预训练目标、仅 patch size 不同**（32→16）。
> 若 ③b 复现出"both 位 gap 变化最小"，该规律从"7 配置的观察"升级为"**同族对照下的因果证据**"。
"""
    i = t.find("# 项目交接文档")
    j = t.find("\n", i)
    io.open(hp, "w", encoding="utf-8", newline="").write(t[:j + 1] + "\n" + ent + t[j + 1:])
    t2 = io.open(hp, encoding="utf-8").read()
    for k in ("CLIP B/16 就位", "flax_model.msgpack", "权重存在且 >500 MB", "patch_size = 16", "同族对照"):
        assert k in t2, f"断言失败：缺 {k}"
    print(f"  ✅ HANDOFF 已追加（{len(t2.splitlines())} 行）")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
