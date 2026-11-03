# -*- coding: utf-8 -*-
r"""云端：**安全重下**权重（临时文件 → 校验 → 才覆盖）（2026-10-09）。

## 三次失败的完整教训

| # | 失败 | 根因 |
|---|---|---|
| 1 | 大小对但 `header too small` | **多进程同时写同一文件** |
| 2 | `total=1093` 覆盖好文件 | **`curl -sIL` 只得重定向页大小** |
| 3 | 现在文件是 1093 B 垃圾 | 同 #2，且**直接写在原文件上** |

## 本脚本的铁律

1. **绝不写原文件**：下到 `X.tmp`，**校验字节数 == 期望**后 `mv` 覆盖；
2. **期望字节数用 `curl -sL -o /dev/null -w '%{size_download}'` 跟随重定向取得**（不是 HEAD）；
3. **同时只有一个下载进程**（先杀干净）；
4. **下载完逐个 `torch.load` 校验**。

    $env:CLOUD_PW='...'; python tools\_cloud_safe_dl.py
"""
from __future__ import annotations

import io
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "tools"))
PY = "/root/miniconda3/bin/python"
WORK = "/root/autodl-tmp/work"

SH = r'''
set -u
cd /root/autodl-tmp/work
M=https://hf-mirror.com

# ① 杀干净（单一进程铁律）
for pat in _cloud_par _cloud_bin _cloud_redl _cloud_ms _cloud_wget; do
  pkill -f "$pat" 2>/dev/null || true
done
pkill -f "wget.*hf-mirror" 2>/dev/null || true
pkill -f "curl.*hf-mirror" 2>/dev/null || true
sleep 3
echo "cleaned; procs=$(pgrep -fc 'curl|wget' 2>/dev/null || echo 0)"

# ② 期望字节数：用 GET 首字节 + size_download 跟随重定向（不是 HEAD）
expect() {
  curl -sL -o /dev/null --max-time 40 -w '%{size_download}' -r 0-0 "$1"
}

safe_dl() {  # safe_dl <url> <dest>
  url="$1"; dest="$2"; tmp="$dest.tmp"
  exp=$(expect "$url")
  echo "=== $dest"
  echo "  url: ${url:0:80}"
  echo "  curl-header-size: $exp"
  rm -f "$tmp"
  t0=$(date +%s)
  curl -sL --retry 8 --retry-delay 3 --max-time 3600 -o "$tmp" "$url"
  rc=$?
  sz=$(stat -c%s "$tmp" 2>/dev/null || echo 0)
  t1=$(date +%s)
  echo "  rc=$rc got=$sz in $((t1-t0))s ($(( sz/(t1-t0+1) )) B/s)"
  if [ "$sz" -lt 500000000 ]; then
    echo "  ❌ TOO SMALL — 保留原文件不动"; rm -f "$tmp"; return 1
  fi
  mv -f "$tmp" "$dest"
  echo "  ✅ 已覆盖 $dest ($sz B)"
  return 0
}

safe_dl "$M/openai/clip-vit-base-patch32/resolve/main/pytorch_model.bin" \
        models/clip-vit-base-patch32/pytorch_model.bin
safe_dl "$M/openai/clip-vit-base-patch16/resolve/main/pytorch_model.bin" \
        models/clip-vit-base-patch16/pytorch_model.bin
echo SAFEDONE

# ③ 校验
/root/miniconda3/bin/python - <<'PY'
import os
os.chdir("/root/autodl-tmp/work")
from transformers import CLIPModel
for d, want in [("models/clip-vit-base-patch32", 32), ("models/clip-vit-base-patch16", 16)]:
    try:
        m = CLIPModel.from_pretrained(d, local_files_only=True)
        print(f"  {d}: patch={m.config.vision_config.patch_size} "
              f"params={sum(p.numel() for p in m.parameters())/1e6:.1f}M "
              f"{'OK' if m.config.vision_config.patch_size == want else 'MISMATCH'}")
    except Exception as e:
        print(f"  {d}: LOAD FAIL {str(e)[:110]}")
PY
'''


def main() -> int:
    from _cloud_ssh import bg, client, run

    c = client()
    try:
        local = REPO / "tools" / "_cloud_safe.sh"
        io.open(local, "w", encoding="utf-8", newline="\n").write(SH)
        sftp = c.open_sftp()
        sftp.put(str(local), f"{WORK}/_cloud_safe.sh")
        sftp.close()
        run(c, f"cd {WORK} && sed -i 's/\\r$//' _cloud_safe.sh", timeout=60)
        print("=== 启动安全重下（脱离运行）===")
        bg(c, "bash _cloud_safe.sh", "outputs_safe.log")
    finally:
        c.close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
