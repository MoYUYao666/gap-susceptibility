# -*- coding: utf-8 -*-
r"""云端：测各处带宽 + **并行分块下载**大权重（2026-10-09）。

## 为什么

单线程 wget 实测约 **0.3 MB/s** → 605 MB 需 30+ min/模型，**3 个模型 1.5 h+**。
**策略**：用 `wget` 的**多连接**（`-x` 不好用）→ 改用 **`aria2c`**（若可装），
否则用 **`curl` 分段并行**（`--range`），最后 `cat` 合并。

    $env:CLOUD_PW='...'; python tools\_cloud_parallel_dl.py
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
PAR=8

# 测带宽
echo "=== 带宽探测（1 秒取 5MB）==="
curl -s -o /dev/null -w '  speed: %{speed_download} B/s\n' --max-time 6 \
  -r 0-5000000 "$M/openai/clip-vit-base-patch32/resolve/main/pytorch_model.bin" || true

# 装 aria2（若能）
if ! command -v aria2c >/dev/null 2>&1; then
  (apt-get install -y -q aria2 >/dev/null 2>&1 || pip install -q aria2p >/dev/null 2>&1) || true
fi

pdl() {  # pdl <url> <dest>
  url="$1"; dest="$2"
  if [ -s "$dest" ]; then echo "SKIP $dest"; return 0; fi
  if command -v aria2c >/dev/null 2>&1; then
    echo "aria2c x$PAR -> $dest"
    aria2c -q -x $PAR -s $PAR -k 4M --file-allocation=none \
           --max-tries=10 --retry-wait=3 -d "$(dirname "$dest")" \
           -o "$(basename "$dest")" "$url" && echo "  OK $(stat -c%s "$dest")"
    return $?
  fi
  # curl 分段并行
  total=$(curl -sI -L "$url" | awk 'BEGIN{IGNORECASE=1}/content-length/{print $2}' | tr -d '\r' | tail -1)
  if [ -z "$total" ] || [ "$total" -lt 1000000 ] 2>/dev/null; then
    echo "no size -> single curl"; curl -sL -C - -o "$dest" "$url"; return $?
  fi
  echo "curl x$PAR segments -> $dest (total $total)"
  chunk=$(( total / PAR + 1 ))
  pids=""
  for i in $(seq 0 $((PAR-1))); do
    a=$(( i * chunk )); b=$(( a + chunk - 1 ))
    [ "$b" -ge "$total" ] && b=$(( total - 1 ))
    curl -sL -r "${a}-${b}" -o "${dest}.part${i}" "$url" &
    pids="$pids $!"
  done
  for p in $pids; do wait $p; done
  cat "${dest}".part* > "$dest" && rm -f "${dest}".part*
  echo "  OK $(stat -c%s "$dest") / $total"
}

pdl "$M/openai/clip-vit-base-patch32/resolve/main/pytorch_model.bin" \
    models/clip-vit-base-patch32/pytorch_model.bin
echo "=== b32 weights done ==="
pdl "$M/openai/clip-vit-base-patch16/resolve/main/pytorch_model.bin" \
    models/clip-vit-base-patch16/pytorch_model.bin
echo "=== b16 weights done ==="
OC=laion/CLIP-ViT-B-32-laion2B-s34B-b79K
pdl "$M/$OC/resolve/main/open_clip_pytorch_model.bin" \
    models/openclip/open_clip_pytorch_model.bin
echo "=== openclip weights done ==="

# 清掉 0 字节的 safetensors
find models -name "model.safetensors" -size 0 -delete 2>/dev/null
echo ALLWEIGHTDONE
'''


def main() -> int:
    from _cloud_ssh import client, run

    c = client()
    try:
        print("=== 停旧下载 → 启动并行下载 ===")
        run(c, "pkill -f _cloud_bin.sh; pkill -f 'wget.*hf-mirror'; sleep 2; echo killed")
        local = REPO / "tools" / "_cloud_par.sh"
        io.open(local, "w", encoding="utf-8", newline="\n").write(SH)
        sftp = c.open_sftp()
        sftp.put(str(local), f"{WORK}/_cloud_par.sh")
        sftp.close()
        run(c, f"cd {WORK} && sed -i 's/\\r$//' _cloud_par.sh && "
               f"nohup bash _cloud_par.sh > outputs_par.log 2>&1 & echo started")
    finally:
        c.close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
