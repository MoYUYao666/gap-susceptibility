# -*- coding: utf-8 -*-
r"""云端：① 查 HF 格式的 openclip 仓库（可被 `CLIPModel` 直接加载）② 校验并重传数据（2026-10-09）。

## 两个事实

1. 已有 `models/openclip/open_clip_model.safetensors`（605 MB，302 张量）
   —— **是 LAION 原生格式**（`visual.transformer.*`），**`CLIPModel.from_pretrained` 读不了**；
2. 数据包上传**未完成**（`BadZipFile`）→ 需重传。

**故首选：找 HF 格式的 openclip 镜像**（如 `laion/CLIP-ViT-B-32-laion2B-s34B-b79K` 本身就有
`model.safetensors`，那是 HF `CLIPModel` 格式）。

    $env:CLOUD_PW='...'; python tools\_cloud_oc_hf.py
"""
from __future__ import annotations

import io
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "tools"))

REMOTE = r'''
import os, time
os.chdir("/root/autodl-tmp/work")
import subprocess, json, urllib.request

M = "https://hf-mirror.com"
REPO_ID = "laion/CLIP-ViT-B-32-laion2B-s34B-b79K"

print("=== 列出该仓库文件（走 HF API）===")
try:
    url = f"{M}/api/models/{REPO_ID}"
    with urllib.request.urlopen(url, timeout=30) as r:
        d = json.loads(r.read().decode())
    for s in d.get("siblings", []):
        print("   ", s.get("rfilename"))
except Exception as e:
    print("  API fail:", str(e)[:140])

print("\n=== 试下 HF 格式权重 ===")
dest = "models/openclip"
for f in ("model.safetensors", "pytorch_model.bin"):
    url = f"{M}/{REPO_ID}/resolve/main/{f}"
    hdr = subprocess.run(["curl", "-sL", "-o", "/dev/null", "--max-time", "20",
                          "-w", "%{http_code} %{size_download}", "-r", "0-0", url],
                         capture_output=True, text=True)
    print(f"  {f}: {hdr.stdout.strip()}")
'''


def main() -> int:
    from _cloud_ssh import client, run

    c = client()
    try:
        io.open(REPO / "outputs" / "_remote_oc2.py", "w", encoding="utf-8",
                newline="\n").write(REMOTE)
        sftp = c.open_sftp()
        sftp.put(str(REPO / "outputs" / "_remote_oc2.py"),
                 "/root/autodl-tmp/work/_oc2.py")
        sftp.close()
        run(c, "/root/miniconda3/bin/python /root/autodl-tmp/work/_oc2.py", timeout=300)
    finally:
        c.close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
