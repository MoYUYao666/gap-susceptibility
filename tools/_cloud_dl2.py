# -*- coding: utf-8 -*-
r"""云端：用 `bg()` 正确脱离地启动模型下载（2026-10-09）。

先测带宽，再选最快的源。**不猜**——实测决定。

    $env:CLOUD_PW='...'; python tools\_cloud_dl2.py [--src hf|ms]
"""
from __future__ import annotations

import argparse
import io
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "tools"))
PY = "/root/miniconda3/bin/python"
WORK = "/root/autodl-tmp/work"

BENCH = r'''
cd /root/autodl-tmp/work
echo "=== 带宽实测（各取 20MB，限时 12s）==="
for u in \
  "https://hf-mirror.com/openai/clip-vit-base-patch32/resolve/main/pytorch_model.bin" \
  "https://modelscope.cn/api/v1/models/AI-ModelScope/clip-vit-base-patch32/repo?Revision=master&FilePath=pytorch_model.bin" \
  "https://www.modelscope.cn/api/v1/models/dienstag/clip-vit-base-patch32/repo?Revision=master&FilePath=pytorch_model.bin" ; do
  sp=$(curl -sL -o /dev/null -w '%{speed_download}' --max-time 12 -r 0-20000000 "$u" 2>/dev/null)
  printf "  %10.0f B/s  %s\n" "${sp:-0}" "$(echo "$u" | cut -c1-70)"
done
'''

MS = r'''
import os, sys, time
os.chdir("/root/autodl-tmp/work")
os.environ["MODELSCOPE_CACHE"] = "/root/autodl-tmp/work/.ms"
from modelscope import snapshot_download as ms_dl

CANDS = {
    "models/clip-vit-base-patch32": ["AI-ModelScope/clip-vit-base-patch32",
                                     "dienstag/clip-vit-base-patch32",
                                     "Xenova/clip-vit-base-patch32"],
    "models/clip-vit-base-patch16": ["AI-ModelScope/clip-vit-base-patch16",
                                     "dienstag/clip-vit-base-patch16",
                                     "Xenova/clip-vit-base-patch16"],
    "models/openclip": ["AI-ModelScope/CLIP-ViT-B-32-laion2B-s34B-b79K",
                        "laion/CLIP-ViT-B-32-laion2B-s34B-b79K"],
}
for dst, ids in CANDS.items():
    ok = False
    for mid in ids:
        t0 = time.time()
        try:
            print(f"try {mid} ...", flush=True)
            ms_dl(mid, local_dir=dst,
                  ignore_file_pattern=[r".*\.msgpack$", r".*\.h5$",
                                       r"flax_model.*", r"tf_model.*", r".*\.onnx$"])
            bg = [f for f in os.listdir(dst)
                  if f.endswith((".bin", ".safetensors"))
                  and os.path.getsize(os.path.join(dst, f)) > 100e6]
            if bg:
                print(f"OK {mid} {max(os.path.getsize(os.path.join(dst,f)) for f in bg)} B "
                      f"in {time.time()-t0:.0f}s", flush=True)
                ok = True; break
            print("  no big weights", flush=True)
        except Exception as e:
            print(f"  fail {str(e)[:100]}", flush=True)
    if not ok:
        print(f"NOFIND {dst}", flush=True)
print("MSDONE", flush=True)
'''


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--bench", action="store_true")
    ap.add_argument("--src", choices=["hf", "ms"], default="ms")
    a = ap.parse_args()

    from _cloud_ssh import bg, client, run

    c = client()
    try:
        if a.bench:
            print("=== 带宽实测 ===")
            run(c, BENCH, timeout=180)
            return 0

        # 清掉旧的、残缺的下载
        run(c, "pkill -f _cloud_par.sh; pkill -f _cloud_bin.sh; "
               "pkill -f 'wget.*hf-mirror'; pkill -f _cloud_ms.py; "
               "sleep 2; echo cleaned", timeout=60)

        if a.src == "ms":
            local = REPO / "tools" / "_cloud_ms2.py"
            io.open(local, "w", encoding="utf-8", newline="\n").write(MS)
            sftp = c.open_sftp()
            sftp.put(str(local), f"{WORK}/_cloud_ms2.py")
            sftp.close()
            run(c, f"cd {WORK} && sed -i 's/\\r$//' _cloud_ms2.py", timeout=60)
            print("=== 启动 ModelScope 下载（脱离运行）===")
            bg(c, f"{PY} _cloud_ms2.py", "outputs_ms2.log")
        else:
            print("=== 启动 HF 镜像并行下载 ===")
            bg(c, "bash _cloud_par.sh", "outputs_par.log")
    finally:
        c.close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
