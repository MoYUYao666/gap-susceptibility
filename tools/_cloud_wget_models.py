# -*- coding: utf-8 -*-
r"""云端：用 `wget` 直连 hf-mirror 下载 CLIP 权重（比 huggingface_hub 稳，支持断点续传）。

**优先级**：本项目规则要求"模型在服务器端下载"——**本脚本正是如此**（不涉及本地上传权重）。

    $env:CLOUD_PW='...'; python tools\_cloud_wget_models.py
"""
from __future__ import annotations

import io

import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "tools"))
PY = "/root/miniconda3/bin/python"
WORK = "/root/autodl-tmp/work"

REMOTE = r'''
set -u
cd /root/autodl-tmp/work
M=https://hf-mirror.com
dl() {   # dl <repo> <file> <destdir>
  local repo="$1" file="$2" dest="$3"
  mkdir -p "$dest"
  if [ -s "$dest/$file" ]; then echo "SKIP $dest/$file"; return 0; fi
  echo "GET $repo/$file"
  wget -q --show-progress -c --tries=8 --timeout=30 \
       -O "$dest/$file" "$M/$repo/resolve/main/$file" \
    && echo "  OK $(stat -c%s "$dest/$file") B" || echo "  FAIL $repo/$file"
}
for f in config.json preprocessor_config.json tokenizer.json tokenizer_config.json \
         vocab.json merges.txt special_tokens_map.json model.safetensors; do
  dl openai/clip-vit-base-patch32 "$f" models/clip-vit-base-patch32
done
echo "=== b32 done ==="
for f in config.json preprocessor_config.json tokenizer.json tokenizer_config.json \
         vocab.json merges.txt special_tokens_map.json model.safetensors; do
  dl openai/clip-vit-base-patch16 "$f" models/clip-vit-base-patch16
done
echo "=== b16 done ==="
'''


def main() -> int:
    from _cloud_ssh import client, run

    c = client()
    try:
        print("=== ① 停掉旧下载 ===")
        run(c, "pkill -f _cloud_models; sleep 2; echo killed")

        print("\n=== ② 上传 wget 脚本并运行（后台）===")
        local = REPO / "tools" / "_cloud_wget.sh"
        io.open(local, "w", encoding="utf-8", newline="\n").write(REMOTE)  # 强制 LF，否则远端 bash 会因 \\r 报错
        sftp = c.open_sftp()
        sftp.put(str(local), f"{WORK}/_cloud_wget.sh")
        sftp.close()
        run(c, f"cd {WORK} && sed -i 's/\\r$//' _cloud_wget.sh && chmod +x _cloud_wget.sh && "
               f"nohup bash _cloud_wget.sh > outputs_wget.log 2>&1 & echo started")

        print("\n=== ③ 已启动；列目录 ===")
        run(c, f"sleep 25; cd {WORK} && tail -6 outputs_wget.log; echo '--- 大小 ---'; "
               f"du -sh models 2>/dev/null")
    finally:
        c.close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
