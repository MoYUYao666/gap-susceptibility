# -*- coding: utf-8 -*-
r"""云端：用 ModelScope 找可用的 CLIP 镜像并下载（比 hf-mirror 快）（2026-10-09）。

## 背景

hf-mirror 单线程实测 **0.3–2 MB/s** → 605 MB/模型太慢。
ModelScope（阿里，国内）通常 **10–50 MB/s**。

**本脚本先在 ModelScope 搜索可用的 CLIP 仓库 id**（不猜），命中后下载。

    $env:CLOUD_PW='...'; python tools\_cloud_ms_model.py
"""
from __future__ import annotations

import io
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "tools"))
PY = "/root/miniconda3/bin/python"
WORK = "/root/autodl-tmp/work"

SCRIPT = r'''
import os, sys, time, json
os.chdir("/root/autodl-tmp/work")
os.environ["MODELSCOPE_CACHE"] = "/root/autodl-tmp/work/.ms"

# ① 搜索候选（不猜 id）
print("=== ModelScope 搜索 ===", flush=True)
try:
    from modelscope.hub.api import HubApi
    api = HubApi()
    for kw in ("clip-vit-base-patch32", "clip-vit-base-patch16",
               "CLIP-ViT-B-32-laion2B", "open_clip"):
        try:
            r = api.list_models(model_name=kw) if hasattr(api, "list_models") else None
            print(f"  search {kw}: {type(r)}", flush=True)
        except Exception as e:
            print(f"  search {kw} fail: {str(e)[:80]}", flush=True)
except Exception as e:
    print("  HubApi unavailable:", str(e)[:80], flush=True)

# ② 直接尝试已知的常见镜像 id
CANDS = {
    "models/clip-vit-base-patch32": [
        "AI-ModelScope/clip-vit-base-patch32",
        "dienstag/clip-vit-base-patch32",
        "tinyhhj/clip-vit-base-patch32",
        "Xenova/clip-vit-base-patch32",
        "openai-mirror/clip-vit-base-patch32",
    ],
    "models/clip-vit-base-patch16": [
        "AI-ModelScope/clip-vit-base-patch16",
        "dienstag/clip-vit-base-patch16",
        "Xenova/clip-vit-base-patch16",
        "openai-mirror/clip-vit-base-patch16",
    ],
    "models/openclip": [
        "AI-ModelScope/CLIP-ViT-B-32-laion2B-s34B-b79K",
        "laion/CLIP-ViT-B-32-laion2B-s34B-b79K",
    ],
}
from modelscope import snapshot_download as ms_dl
for dst, ids in CANDS.items():
    if os.path.isdir(dst):
        binf = [f for f in os.listdir(dst) if f.endswith((".bin", ".safetensors"))]
        if binf and max(os.path.getsize(os.path.join(dst, f)) for f in binf) > 100e6:
            print(f"SKIP {dst} (weights present)", flush=True); continue
    ok = False
    for mid in ids:
        t0 = time.time()
        try:
            print(f"  try {mid} ...", flush=True)
            ms_dl(mid, local_dir=dst,
                  ignore_file_pattern=[r".*\.msgpack$", r".*\.h5$",
                                       r"flax_model.*", r"tf_model.*", r".*\.onnx$"])
            binf = [f for f in os.listdir(dst) if f.endswith((".bin", ".safetensors"))]
            if binf and max(os.path.getsize(os.path.join(dst, f)) for f in binf) > 100e6:
                sz = max(os.path.getsize(os.path.join(dst, f)) for f in binf)
                print(f"OK {mid} {sz} B in {time.time()-t0:.0f}s", flush=True)
                ok = True; break
            print(f"  {mid} downloaded but no big weights", flush=True)
        except Exception as e:
            print(f"  fail {str(e)[:90]}", flush=True)
    if not ok:
        print(f"NOFIND {dst}", flush=True)
print("MSDONE", flush=True)
'''


def main() -> int:
    from _cloud_ssh import client, run

    c = client()
    try:
        run(c, "pkill -f _cloud_par.sh; pkill -f 'wget.*hf-mirror'; "
               "pkill -f 'curl.*hf-mirror'; sleep 2; echo killed")
        local = REPO / "tools" / "_cloud_ms.py"
        io.open(local, "w", encoding="utf-8", newline="\n").write(SCRIPT)
        sftp = c.open_sftp()
        sftp.put(str(local), f"{WORK}/_cloud_ms.py")
        sftp.close()
        print("=== 运行 ModelScope 镜像下载（后台）===")
        run(c, f"cd {WORK} && sed -i 's/\\r$//' _cloud_ms.py && "
               f"nohup {PY} _cloud_ms.py > outputs_ms.log 2>&1 & echo started")
        run(c, f"sleep 40; cd {WORK} && head -24 outputs_ms.log")
    finally:
        c.close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
