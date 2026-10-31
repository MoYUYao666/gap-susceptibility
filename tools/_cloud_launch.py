# -*- coding: utf-8 -*-
r"""云端：启动补 seed + `Γ_m`（用云端 python 绝对路径）（2026-10-09）。

## 为什么要单独写

本地驱动 `tools/_p56_add_seeds.py` 里 `PY = r"D:\Anaconda\..."`（**Windows 路径**），
**云端不可用**；且模型目录名也不同。故云端用**自己的启动器**：

| 骨干 | 模型目录 | 输出目录 |
|---|---|---|
| CLIP B/32 | `models/clip-vit-base-patch32` | `outputs/strict_freeze_b32_r4` |
| CLIP B/16 | `models/clip-vit-base-patch16` | `outputs/strict_freeze_b16/r4` |
| OpenCLIP | `models/openclip` | `outputs/strict_freeze_oclip/r4` |

**seed 123/456，rank 4，alpha-mult 2，epochs 10，max-samples 5000，batch 128**（与本地一致）。

    $env:CLOUD_PW='...'; python tools\_cloud_launch.py [--gpus]
"""
from __future__ import annotations

import io
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "tools"))
PY = "/root/miniconda3/bin/python"
WORK = "/root/autodl-tmp/work"

DRIVER = r'''
import os, subprocess, sys, time, glob, json

PY = "/root/miniconda3/bin/python"
WORK = "/root/autodl-tmp/work"
os.chdir(WORK)

JOBS = [
    ("CLIP B/32 r4", "models/clip-vit-base-patch32", "outputs/strict_freeze_b32_r4", "b32_r4_"),
    ("CLIP B/16 r4", "models/clip-vit-base-patch16", "outputs/strict_freeze_b16/r4",   "b16_r4_"),
    ("OpenCLIP r4",  "models/openclip",              "outputs/strict_freeze_oclip/r4", "oclip_r4_"),
]
ARMS = ("text_only", "both", "vision_only")
SEEDS = ["123", "456"]


def log(m):
    line = "[%s] %s" % (time.strftime("%H:%M:%S"), m)
    print(line, flush=True)
    with open("outputs_cloud_driver.log", "a") as f:
        f.write(line + "\n")


log("=" * 60)
log("云端补 seed 启动")
for name, model, outdir, prefix in JOBS:
    # 权重就绪检查
    d = model
    ok = False
    if os.path.isdir(d):
        for f in os.listdir(d):
            p = os.path.join(d, f)
            if f.endswith((".bin", ".safetensors")) and os.path.getsize(p) > 100e6:
                ok = True
    log("%s: 模型 %s ｜ 权重%s" % (name, d, "OK %.0fMB" % (max(
        os.path.getsize(os.path.join(d, f)) for f in os.listdir(d)
        if f.endswith((".bin", ".safetensors"))) / 1e6) if ok else "缺失 → 跳过"))
    if not ok:
        continue
    for arm in ARMS:
        cmd = [PY, "experiments/strict_freeze_control.py",
               "--model", model, "--out-dir", outdir, "--name", prefix,
               "--rank", "4", "--alpha-mult", "2", "--tags", arm,
               "--seeds", *SEEDS, "--epochs", "10", "--max-samples", "5000",
               "--batch-size", "128", "--skip-frozen"]
        log("RUN %s / %s" % (name, arm))
        t0 = time.time()
        try:
            r = subprocess.run(cmd, capture_output=True, text=True,
                               encoding="utf-8", errors="replace", timeout=6 * 3600)
            dt = time.time() - t0
            if r.returncode == 0:
                log("  OK %.0fs" % dt)
            else:
                err = ""
                for ln in (r.stderr or "").splitlines():
                    if "Error" in ln or "error" in ln:
                        err = ln[:150]; break
                log("  FAIL rc=%s %.0fs %s" % (r.returncode, dt, err))
        except subprocess.TimeoutExpired:
            log("  TIMEOUT 6h")
log("补 seed 完成 → 跑 Γ_m")
try:
    r = subprocess.run([PY, "tools/_p58_gamma_clip.py", "--apply"],
                       capture_output=True, text=True, encoding="utf-8",
                       errors="replace", timeout=3600)
    for ln in (r.stdout or "").splitlines():
        if any(k in ln for k in ("Gamma", "Γ", "已写", "‖")):
            log("  | " + ln.strip()[:150])
    log("  Γ_m rc=%s" % r.returncode)
except Exception as e:
    log("  Γ_m 异常 %s" % str(e)[:120])
log("ALLDONE")
'''


def main() -> int:
    from _cloud_ssh import bg, client, run

    c = client()
    try:
        if "--gpus" in sys.argv:
            run(c, "nvidia-smi --query-gpu=name,memory.total,memory.used "
                   "--format=csv,noheader", timeout=60)
            return 0
        io.open(REPO / "outputs" / "_remote_driver.py", "w", encoding="utf-8",
                newline="\n").write(DRIVER)
        sftp = c.open_sftp()
        sftp.put(str(REPO / "outputs" / "_remote_driver.py"),
                 f"{WORK}/_cloud_driver.py")
        sftp.close()
        print("=== 启动云端驱动（脱离运行）===")
        bg(c, f"{PY} _cloud_driver.py", "outputs_cloud_driver.log")
    finally:
        c.close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
