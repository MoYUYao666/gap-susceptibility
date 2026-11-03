# -*- coding: utf-8 -*-
r"""云端：测 SFTP 上传速度，决定"上传"还是"继续下载"（2026-10-09）。

## 判断依据

| 途径 | 实测 |
|---|---|
| PyPI（清华） | **1.71 MB/s**（链路上限） |
| hf-mirror | **0.11–0.22 MB/s**（镜像限速） |
| 并行 8 段 | ~0.9 MB/s |

**若 SFTP 上传 > 0.5 MB/s，则"上传本地已有权重"优于"等镜像下载"**：
本地权重齐全（已校验 patch size），上传 605 MB × 3 ≈ 1.8 GB
→ 0.6 MB/s 时约 **50 min**，且**确定性高**（不受镜像波动影响）。

    $env:CLOUD_PW='...'; python tools\_cloud_uplink_test.py
"""
from __future__ import annotations

import io
import sys
import time
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "tools"))
WORK = "/root/autodl-tmp/work"


def main() -> int:
    from _cloud_ssh import client

    # 造一个 64 MB 的测试文件（用本地 CLIP 权重的前 64 MB）
    src = REPO / "models" / "clip-vit-base-patch32" / "pytorch_model.bin"
    if not src.exists():
        # 尝试其它常见文件名
        for cand in ("model.safetensors", "pytorch_model.bin"):
            p = REPO / "models" / "clip-vit-base-patch32" / cand
            if p.exists():
                src = p
                break
    if not src.exists():
        print("  ❌ 本地找不到 clip-vit-base-patch32 权重")
        return 1
    print(f"  本地权重: {src.name} ｜ {src.stat().st_size/2**20:.0f} MB")

    chunk = REPO / "outputs" / "_uplink_test.bin"
    with io.open(src, "rb") as f, io.open(chunk, "wb") as g:
        g.write(f.read(64 * 2**20))
    print(f"  测试块: 64.0 MB")

    c = client()
    try:
        sftp = c.open_sftp()
        t0 = time.time()
        sftp.put(str(chunk), f"{WORK}/_uplink_test.bin")
        dt = time.time() - t0
        mb = 64.0 / dt
        print(f"\n  ⏱️ 上传 64 MB 用时 {dt:.1f}s → **{mb:.2f} MB/s**")
        print(f"  → 1.8 GB 需约 **{1800/mb/60:.0f} min**")
        sftp.remove(f"{WORK}/_uplink_test.bin")
        sftp.close()
        print("\n  判定：")
        print(f"    镜像并行 ~0.9 MB/s ｜ 上传 {mb:.2f} MB/s")
        print(f"    → {'✅ **上传更快**' if mb > 0.9 else '⚠️ 上传不比镜像快'}")
    finally:
        c.close()
        chunk.unlink(missing_ok=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
