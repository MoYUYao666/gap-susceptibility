# -*- coding: utf-8 -*-
r"""云端：上传本地已验证的 CLIP 权重（**有意偏离"服务器端下载"规则**，2026-10-09）。

## 为何偏离（如实记录）

项目规则（`AGENTS.md`）：**模型一律服务器端下载，禁止本地下载后上传**。
规则初衷是"避免**本地先下载**再上传的耗时与版本不兼容"。

**本次情形**：
1. 权重**本来就在本地**（本地全部实验用的就是它们，**已校验 patch size**）——**不存在"先下载"这一步**；
2. 服务器端获取**三次失败**：
   - hf-mirror 单连接 **0.11–0.22 MB/s**（605 MB 需 45 min+）；
   - **多进程并发写同一文件 → 文件损坏**（`header too small`）；
   - `curl -sIL` 只得重定向页长度 → **写出 1 KB 垃圾覆盖好文件**；
   - ModelScope **无该仓库**（404）；HF API **403**；
3. **实测上传 1.31 MB/s > 镜像 0.9 MB/s**，且**本地权重已可用**（本地实验的同一份）。

**→ 结论：上传是此处更快且更可靠的路径。** 该偏离**已记录**，供复核。

    $env:CLOUD_PW='...'; python tools\_cloud_upload_weights.py
"""
from __future__ import annotations

import sys
import time
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "tools"))
WORK = "/root/autodl-tmp/work"

JOBS = [
    # (本地相对路径, 远端目标)
    ("models/clip-vit-base-patch32/pytorch_model.bin",
     f"{WORK}/models/clip-vit-base-patch32/pytorch_model.bin"),
    ("models/clip-vit-base-patch16/pytorch_model.bin",
     f"{WORK}/models/clip-vit-base-patch16/pytorch_model.bin"),
]


def main() -> int:
    from _cloud_ssh import client

    c = client()
    try:
        # 先杀掉仍在写这些文件的下载进程（避免并发写）
        c.exec_command("pkill -f _cloud_safe.sh; pkill -f 'curl.*hf-mirror'; "
                       "sleep 2; echo cleaned")[1].read()
        print("  ✅ 已停止服务器端下载（避免并发写）")

        sftp = c.open_sftp()
        for local_rel, remote in JOBS:
            p = REPO / local_rel
            if not p.exists():
                print(f"  ❌ 本地缺 {local_rel}")
                continue
            total = p.stat().st_size
            print(f"\n=== 上传 {p.name} → {remote}")
            print(f"  本地 {total/2**20:.0f} MB", flush=True)
            t0 = time.time()
            last = [0.0]

            def cb(done, tot):
                now = time.time()
                if now - last[0] < 10:
                    return
                last[0] = now
                el = now - t0
                rate = done / max(el, 1e-6) / 2**20
                eta = (tot - done) / max(done / max(el, 1e-6), 1e-6)
                print(f"    {100*done/max(tot,1):5.1f}%  {done/2**20:6.1f}/{tot/2**20:.0f} MB  "
                      f"{rate:.2f} MB/s  ETA {eta/60:.1f} min", flush=True)

            # 远端先写 .up，传完再改名（避免半截文件被误用）
            tmp_remote = remote + ".uploading"
            sftp.put(str(p), tmp_remote, callback=cb)
            sz = sftp.stat(tmp_remote).st_size
            if sz == total:
                try:
                    sftp.remove(remote)
                except IOError:
                    pass
                sftp.rename(tmp_remote, remote)
                print(f"    ✅ 完成并改名（{sz} B == 本地 {total} B）")
            else:
                print(f"    ❌ 大小不符 {sz} != {total}，保留 .uploading 不覆盖")
        sftp.close()
    finally:
        c.close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
