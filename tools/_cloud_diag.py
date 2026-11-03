# -*- coding: utf-8 -*-
r"""云端：诊断下载带宽瓶颈 + 试更快的获取途径（2026-10-09）。

## 已知

hf-mirror `pytorch_model.bin` 实测 **66 KB/s** → 605 MB 需 2.5 h。
**但 pip 装包很快** → 说明链路本身不慢，**是镜像对该文件的限速**。

## 本脚本测

1. **pip 下载速度**（对照，判断链路上限）；
2. **hf-mirror 的 CDN 直链**（`cdn-lfs` 域名，通常比 `resolve` 快）；
3. **并行分段**是否绕开单连接限速；
4. `modelscope` 的**有效**文件 URL 格式。

    $env:CLOUD_PW='...'; python tools\_cloud_diag.py
"""
from __future__ import annotations

import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "tools"))

D = r'''
cd /root/autodl-tmp/work
echo "=== ① pip 速度对照（10 MB 包）==="
timeout 20 curl -sL -o /dev/null -w '  pypi: %{speed_download} B/s (%{size_download} B)\n' \
  -r 0-10000000 https://pypi.tuna.tsinghua.edu.cn/simple/ 2>/dev/null || echo "  pypi 取不到"

echo
echo "=== ② hf-mirror 不同端点 ==="
U=https://hf-mirror.com/openai/clip-vit-base-patch32/resolve/main/pytorch_model.bin
for opt in "-r 0-20000000" "-r 0-20000000 --http1.1" "-r 100000000-120000000"; do
  sp=$(curl -sL -o /dev/null -w '%{speed_download}' --max-time 15 $opt "$U" 2>/dev/null)
  printf "  %-28s %10.0f B/s\n" "$opt" "${sp:-0}"
done

echo
echo "=== ③ 并行 8 段（各 2.5MB）总计 ==="
T0=$(date +%s%N)
for i in $(seq 0 7); do
  a=$((i*3000000)); b=$((a+2500000))
  curl -sL -r ${a}-${b} -o /tmp/p$i --max-time 20 "$U" &
done
wait
T1=$(date +%s%N)
BYTES=$(du -cb /tmp/p* 2>/dev/null | tail -1 | cut -f1)
MS=$(( (T1-T0)/1000000 ))
printf "  并行取得 %s B 用 %s ms → %.0f B/s\n" "$BYTES" "$MS" "$(echo "scale=0; $BYTES*1000/($MS+1)" | bc)"
rm -f /tmp/p*

echo
echo "=== ④ modelscope 有效 URL ==="
for u in \
 "https://www.modelscope.cn/api/v1/models/AI-ModelScope/clip-vit-base-patch32/repo?Revision=master&FilePath=config.json" \
 "https://modelscope.cn/models/AI-ModelScope/clip-vit-base-patch32/resolve/master/config.json" ; do
  code=$(curl -sL -o /dev/null -w '%{http_code} %{size_download}' --max-time 15 "$u" 2>/dev/null)
  printf "  %-20s %s\n" "$code" "$(echo "$u" | cut -c1-60)"
done

echo
echo "=== ⑤ modelscope python 直下测速 ==="
/root/miniconda3/bin/python - <<PY
import time, os
os.environ["MODELSCOPE_CACHE"]="/root/autodl-tmp/work/.ms"
try:
    from modelscope.hub.file_download import model_file_download
    t0=time.time()
    p=model_file_download("AI-ModelScope/clip-vit-base-patch32","pytorch_model.bin",
                          cache_dir="/root/autodl-tmp/work/.ms")
    print("  ms download %.1fs ->"%  (time.time()-t0), p, os.path.getsize(p))
except Exception as e:
    print("  ms fail:", str(e)[:150])
PY
'''


def main() -> int:
    from _cloud_ssh import client, run

    c = client()
    try:
        print("=== 带宽诊断 ===")
        run(c, D, timeout=420)
    finally:
        c.close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
