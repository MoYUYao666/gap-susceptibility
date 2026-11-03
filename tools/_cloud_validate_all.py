# -*- coding: utf-8 -*-
r"""云端：验证 openclip 的两个大文件哪个可用 + 全部模型最终校验（2026-10-09）。

    $env:CLOUD_PW='...'; python tools\_cloud_validate_all.py
"""
from __future__ import annotations

import io
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "tools"))

REMOTE = r'''
import os, json, glob
os.chdir("/root/autodl-tmp/work")

def sf_info(p):
    """读 safetensors header，返回 (n_tensors, 前几个 key, 是否 HF 风格)"""
    try:
        with open(p, "rb") as f:
            n = int.from_bytes(f.read(8), "little")
            if not (0 < n < 50_000_000):
                return None
            meta = json.loads(f.read(n).decode("utf-8"))
        keys = [k for k in meta if k != "__metadata__"]
        hf = any(k.startswith(("vision_model.", "text_model.")) for k in keys)
        return len(keys), keys[:3], hf
    except Exception as e:
        return f"ERR {str(e)[:60]}"

def bin_info(p):
    """尝试 torch.load 的键名（只读 header，用 mmap 省内存）"""
    try:
        import torch
        try:
            sd = torch.load(p, map_location="cpu", mmap=True, weights_only=True)
        except TypeError:
            sd = torch.load(p, map_location="cpu", weights_only=True)
        keys = list(sd.keys())
        hf = any(k.startswith(("vision_model.", "text_model.")) for k in keys)
        return len(keys), keys[:3], hf
    except Exception as e:
        return f"ERR {str(e)[:80]}"

print("=== openclip 目录的两个大文件 ===")
for p in sorted(glob.glob("models/openclip/*")):
    if not os.path.isfile(p): continue
    s = os.path.getsize(p)
    if s < 1e6: 
        continue
    print(f"  {os.path.basename(p)}  {s} B")
    if p.endswith(".safetensors"):
        print(f"    {sf_info(p)}")
    elif p.endswith(".bin"):
        print(f"    {bin_info(p)}")

print("\n=== 能否用 CLIPModel 加载 openclip ===")
try:
    from transformers import CLIPModel
    m = CLIPModel.from_pretrained("models/openclip", local_files_only=True)
    print(f"  ✅ 可加载 ｜ patch={m.config.vision_config.patch_size} "
          f"params={sum(x.numel() for x in m.parameters())/1e6:.1f}M")
except Exception as e:
    print(f"  ❌ {str(e)[:200]}")

print("\n=== b32 / b16 下载状态 ===")
for d in ("models/clip-vit-base-patch32", "models/clip-vit-base-patch16"):
    fs = sorted(os.listdir(d)) if os.path.isdir(d) else []
    rows = [(f, os.path.getsize(os.path.join(d, f))) for f in fs]
    big = [r for r in rows if r[1] > 1e6]
    tmp = [r for r in rows if r[0].endswith(".tmp")]
    print(f"  {d}: 大文件={big} ｜ 临时={[(t[0], t[1]) for t in tmp]}")

print("\n=== 下载日志尾 ===")
if os.path.exists("outputs_safe.log"):
    for ln in open("outputs_safe.log").read().splitlines()[-6:]:
        print("  " + ln[:110])
'''


def main() -> int:
    from _cloud_ssh import client, run

    c = client()
    try:
        io.open(REPO / "outputs" / "_remote_va.py", "w", encoding="utf-8",
                newline="\n").write(REMOTE)
        sftp = c.open_sftp()
        sftp.put(str(REPO / "outputs" / "_remote_va.py"),
                 "/root/autodl-tmp/work/_va.py")
        sftp.close()
        run(c, "/root/miniconda3/bin/python /root/autodl-tmp/work/_va.py", timeout=900)
    finally:
        c.close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
