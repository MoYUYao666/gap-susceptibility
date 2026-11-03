# -*- coding: utf-8 -*-
r"""云端：**并行分段**下载权重（最后一次尝试服务器端获取，2026-10-09）。

## 为什么还要试

项目规则（`AGENTS.md`）：**模型一律在服务器端下载，禁止本地下载后上传**。
但实测：hf-mirror **0.11–0.22 MB/s**（单连接），**并行 8 段约 0.9 MB/s**，
而 **SFTP 上传 1.28 MB/s**。

**本脚本用 16 段并行**（若带宽允许，可达 1.5–2 MB/s）→ 若 ≥1.3 MB/s 则胜出，
**否则回退到上传**（并如实记录为何偏离规则）。

    $env:CLOUD_PW='...'; python tools\_cloud_par16.py [--start]
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
PAR=16

pdl() {  # pdl <url> <dest>
  url="$1"; dest="$2"
  if [ -s "$dest" ]; then
    sz=$(stat -c%s "$dest")
    if [ "$sz" -gt 100000000 ]; then echo "SKIP $dest ($sz B)"; return 0; fi
  fi
  mkdir -p "$(dirname "$dest")"
  total=$(curl -sIL "$url" | awk 'BEGIN{IGNORECASE=1}/^content-length:/{v=$2}END{print v}' | tr -d '\r')
  if [ -z "${total:-}" ] || [ "${total:-0}" -lt 1000000 ]; then
    echo "NOLEN $url"; curl -sL -o "$dest" "$url"; return $?
  fi
  echo "DL $dest  total=$total  x$PAR"
  t0=$(date +%s)
  chunk=$(( total / PAR + 1 ))
  pids=""
  for i in $(seq 0 $((PAR-1))); do
    a=$(( i * chunk )); b=$(( a + chunk - 1 ))
    [ "$b" -ge "$total" ] && b=$(( total - 1 ))
    curl -sL --retry 5 --retry-delay 2 -r "${a}-${b}" -o "${dest}.p${i}" "$url" &
    pids="$pids $!"
  done
  for p in $pids; do wait $p; done
  cat "${dest}".p* > "$dest" && rm -f "${dest}".p*
  t1=$(date +%s)
  sz=$(stat -c%s "$dest")
  echo "  OK $sz B in $((t1-t0))s  → $(( sz / (t1-t0+1) )) B/s"
}

# 小文件先取（快）
for repo_dir in "openai/clip-vit-base-patch32:models/clip-vit-base-patch32" \
                "openai/clip-vit-base-patch16:models/clip-vit-base-patch16"; do
  repo="${repo_dir%%:*}"; d="${repo_dir##*:}"
  for f in config.json preprocessor_config.json tokenizer.json tokenizer_config.json \
           vocab.json merges.txt special_tokens_map.json; do
    [ -s "$d/$f" ] || curl -sL -o "$d/$f" "$M/$repo/resolve/main/$f"
  done
  echo "small files done: $d"
done

pdl "$M/openai/clip-vit-base-patch32/resolve/main/pytorch_model.bin" \
    models/clip-vit-base-patch32/pytorch_model.bin
echo "=== b32 done ==="
pdl "$M/openai/clip-vit-base-patch16/resolve/main/pytorch_model.bin" \
    models/clip-vit-base-patch16/pytorch_model.bin
echo "=== b16 done ==="
'''


def main() -> int:
    from _cloud_ssh import bg, client, run

    c = client()
    try:
        run(c, "pkill -f _cloud_par.sh; pkill -f _cloud_bin.sh; "
               "pkill -f 'wget.*hf-mirror'; pkill -f _cloud_ms; sleep 2; echo cleaned",
            timeout=60)
        local = REPO / "tools" / "_cloud_par16.sh"
        io.open(local, "w", encoding="utf-8", newline="\n").write(SH)
        sftp = c.open_sftp()
        sftp.put(str(local), f"{WORK}/_cloud_par16.sh")
        sftp.close()
        run(c, f"cd {WORK} && sed -i 's/\\r$//' _cloud_par16.sh", timeout=60)

        if "--start" in sys.argv:
            print("=== 启动 16 段并行下载（脱离运行）===")
            bg(c, "bash _cloud_par16.sh", "outputs_par16.log")
        else:
            print("  （未加 --start，仅上传脚本）")
    finally:
        c.close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
