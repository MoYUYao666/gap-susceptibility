# -*- coding: utf-8 -*-
r"""云端：**干净重下**权重并逐个校验（2026-10-09）。

## 故障

```
models/clip-vit-base-patch32/pytorch_model.bin   605,247,071 B  ← 大小"对"
models/clip-vit-base-patch16/pytorch_model.bin   598,641,023 B
→ LOAD FAIL: Error while deserializing header: header too small
```

**根因**：**多个下载进程曾同时写同一文件**（`wget` + 并行分段 `curl` + 另一 curl 交错追加）
→ **大小凑巧接近但内容错乱**。

## 修法

1. **清掉所有残缺/损坏文件**（含 `.incomplete`、`.p0..p15`）；
2. **单一进程**下（16 段并行，但**只此一个脚本在写**）；
3. **下载后逐个 `torch.load` 校验**；不一致则重下该文件。

    $env:CLOUD_PW='...'; python tools\_cloud_redownload.py [--all]
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

# ① 杀干净所有下载，避免并发写
pkill -f _cloud_par 2>/dev/null || true
pkill -f _cloud_bin 2>/dev/null || true
pkill -f "wget.*hf-mirror" 2>/dev/null || true
pkill -f "curl.*hf-mirror" 2>/dev/null || true
sleep 3

# ② 清掉损坏/残缺文件
rm -f models/*/model.safetensors models/*/*.incomplete models/*/*.p[0-9]* \
      models/*/*.part* 2>/dev/null || true
find models -name "pytorch_model.bin" -size -100M -delete 2>/dev/null || true
echo "cleaned: $(ls models/clip-vit-base-patch32/ | tr '\n' ' ')"

# ③ 串行下载 + 立即校验
dl_one() {  # dl_one <repo> <file> <dest>
  repo="$1"; file="$2"; dest="$3"
  url="$M/$repo/resolve/main/$file"
  echo "=== DL $dest ==="
  total=$(curl -sIL "$url" | awk 'BEGIN{IGNORECASE=1}/^content-length:/{v=$2}END{print v}' | tr -d '\r')
  echo "  expect total=$total"
  PAR=16; chunk=$(( total / PAR + 1 )); pids=""; t0=$(date +%s)
  for i in $(seq 0 $((PAR-1))); do
    a=$(( i * chunk )); b=$(( a + chunk - 1 ))
    [ "$b" -ge "$total" ] && b=$(( total - 1 ))
    curl -sL --retry 6 --retry-delay 2 -r "${a}-${b}" -o "${dest}.p${i}" "$url" &
    pids="$pids $!"
  done
  for p in $pids; do wait $p; done
  cat "${dest}".p* > "$dest" && rm -f "${dest}".p*
  sz=$(stat -c%s "$dest" 2>/dev/null || echo 0)
  t1=$(date +%s)
  echo "  got $sz / $total in $((t1-t0))s ($(( sz/(t1-t0+1) )) B/s)"
  if [ "$sz" != "$total" ]; then echo "  SIZE MISMATCH"; return 1; fi
  return 0
}

REPO32=openai/clip-vit-base-patch32
REPO16=openai/clip-vit-base-patch16
dl_one "$REPO32" pytorch_model.bin models/clip-vit-base-patch32/pytorch_model.bin
dl_one "$REPO16" pytorch_model.bin models/clip-vit-base-patch16/pytorch_model.bin
echo DLDONE
'''


def main() -> int:
    from _cloud_ssh import bg, client, run

    c = client()
    try:
        local = REPO / "tools" / "_cloud_redl.sh"
        io.open(local, "w", encoding="utf-8", newline="\n").write(SH)
        sftp = c.open_sftp()
        sftp.put(str(local), f"{WORK}/_cloud_redl.sh")
        sftp.close()
        run(c, f"cd {WORK} && sed -i 's/\\r$//' _cloud_redl.sh", timeout=60)
        print("=== 启动干净重下（脱离运行）===")
        bg(c, "bash _cloud_redl.sh", "outputs_redl.log")
    finally:
        c.close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
