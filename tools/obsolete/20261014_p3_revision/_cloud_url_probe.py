# -*- coding: utf-8 -*-
r"""云端：查真实 URL / 大小，并**只用可信长度**下载（2026-10-09）。

## 两次失败的根因

| 失败 | 原因 |
|---|---|
| 大小对但 `header too small` | **多进程同时写同一文件**（wget + curl 交错） |
| `total=1093` 覆盖好文件 | **`curl -sIL` 只拿到重定向页大小**，我据此分段 → 写出 1 KB 垃圾 |

## 正确做法

1. 用 `curl -sL -o /dev/null -w '%{size_download} %{url_effective}'` 跟随重定向取**真实**大小；
2. **下载前先备份**已有可用文件；
3. **写临时文件 → 校验 → 才 `mv` 覆盖**（绝不在原文件上写）。

    $env:CLOUD_PW='...'; python tools\_cloud_url_probe.py
"""
from __future__ import annotations

import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "tools"))

P = r'''
cd /root/autodl-tmp/work
echo "=== 当前权重状态（已被覆盖成垃圾）==="
ls -la models/clip-vit-base-patch32/pytorch_model.bin \
       models/clip-vit-base-patch16/pytorch_model.bin 2>/dev/null | awk '{printf "  %12s %s\n",$5,$9}'
echo
echo "=== 真实 URL 与长度（跟随重定向）==="
for u in \
 "https://hf-mirror.com/openai/clip-vit-base-patch32/resolve/main/pytorch_model.bin" \
 "https://hf-mirror.com/openai/clip-vit-base-patch16/resolve/main/pytorch_model.bin" ; do
  info=$(curl -sL -o /dev/null --max-time 25 -w '%{size_download} %{url_effective}' -r 0-0 "$u")
  echo "  $u"
  echo "    → $info"
done
echo
echo "=== HEAD 的真实 content-length（-L 跟随）==="
curl -sL -I --max-time 25 "https://hf-mirror.com/openai/clip-vit-base-patch32/resolve/main/pytorch_model.bin" \
  | tr -d '\r' | grep -iE '^(HTTP/|content-length|location)' | head -8
'''


def main() -> int:
    from _cloud_ssh import client, run

    c = client()
    try:
        print("=== URL 探测 ===")
        run(c, P, timeout=300)
    finally:
        c.close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
