# -*- coding: utf-8 -*-
r"""云端：装 HF 官方加速器（`hf_xet` / `hf_transfer`）并实测下载提速（2026-10-09）。

## 为什么要

7B 权重共 **5 shard / 约 15.5 GB**，当前 `curl` 单连接约 **3 MB/s** → 60–90 min。
HF 官方有两条加速路线：

| 路线 | 机制 | 开关 |
|---|---|---|
| **`hf_xet`** | **Xet** 存储后端（分块去重 + 并行） | 新版 huggingface_hub **默认优先**（`HF_HUB_DISABLE_XET=1` 可关） |
| **`hf_transfer`** | Rust 多连接传输 | `HF_HUB_ENABLE_HF_TRANSFER=1`（新版**已弃用**，改由 xet 接管） |

**故正确做法**：装 `hf_xet`，**并把 `HF_HUB_DISABLE_XET` 去掉**（我此前一直设成 1，**反而关掉了最快的路径**）。

    $env:CLOUD_PW='...'; python tools\_cloud_hf_accel.py
"""
from __future__ import annotations

import io
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "tools"))
PY = "/root/miniconda3/bin/python"
WORK = "/root/autodl-tmp/work"

REMOTE = r'''
import os, sys, subprocess, time, json
os.chdir("/root/autodl-tmp/work")

def sh(cmd):
    r = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    return (r.stdout or "") + (r.stderr or "")

print("=== ① 现状 ===")
print("  huggingface_hub:", sh("/root/miniconda3/bin/pip show huggingface_hub 2>/dev/null | head -2").strip())
for pkg in ("hf_xet", "hf_transfer"):
    out = sh("/root/miniconda3/bin/pip show %s 2>/dev/null | head -2" % pkg).strip()
    print("  %-12s: %s" % (pkg, out if out else "未装"))

print("\n=== ② 安装 hf_xet（Xet 后端，官方推荐的加速）===")
print(sh("/root/miniconda3/bin/pip install -q hf_xet 2>&1 | tail -3").strip())
print("  装后:", sh("/root/miniconda3/bin/pip show hf_xet 2>/dev/null | head -2").strip())

print("\n=== ③ 实测：hf_xet 下载一个 shard 的速度 ===")
env = dict(os.environ)
env.pop("HF_HUB_DISABLE_XET", None)        # **关键：不再禁用 xet**
env["HF_ENDPOINT"] = "https://hf-mirror.com"
env["HF_HUB_ENABLE_HF_TRANSFER"] = "1"     # 若旧版仍认这个
env["HF_HOME"] = "/root/autodl-tmp/work/.hf"

code = r"""
import os, time, sys
from huggingface_hub import hf_hub_download
for repo, fn in [("Qwen/Qwen2-VL-7B-Instruct", "model-00002-of-00005.safetensors")]:
    t0 = time.time()
    try:
        p = hf_hub_download(repo_id=repo, filename=fn,
                            local_dir="models/qwen2vl7b", resume_download=True)
        dt = time.time() - t0
        sz = os.path.getsize(p)
        print("  %s: %.0f MB in %.0fs → %.2f MB/s" % (fn, sz/1e6, dt, sz/1e6/dt))
    except Exception as e:
        print("  FAIL", str(e)[:200])
"""
open("/root/autodl-tmp/work/_xet_test.py", "w").write(code)
r = subprocess.run(["/root/miniconda3/bin/python", "/root/autodl-tmp/work/_xet_test.py"],
                   capture_output=True, text=True, env=env, timeout=1800)
print((r.stdout or "")[-800:])
if r.stderr:
    print("  stderr:", r.stderr[-300:])
'''


def main() -> int:
    from _cloud_ssh import client, run

    c = client()
    try:
        io.open(REPO / "outputs" / "_remote_accel.py", "w", encoding="utf-8",
                newline="\n").write(REMOTE)
        sftp = c.open_sftp()
        sftp.put(str(REPO / "outputs" / "_remote_accel.py"), f"{WORK}/_accel.py")
        sftp.close()
        run(c, f"{PY} {WORK}/_accel.py", timeout=2400)
    finally:
        c.close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
