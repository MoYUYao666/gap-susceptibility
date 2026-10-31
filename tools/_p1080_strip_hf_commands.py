# -*- coding: utf-8 -*-
r"""Remove the remaining HuggingFace instructions from the project files.

The source-priority table was tightened first, but the older "model acquisition" section still told the reader
to use `HF_ENDPOINT=https://hf-mirror.com ... snapshot_download(...)`, which contradicts the operator's
instruction ("用国内源就不要hf"). This replaces that block with ModelScope only.

    python tools/_p1080_strip_hf_commands.py [--apply]
"""
from __future__ import annotations

import argparse
import io
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
FILES = [REPO / "AGENTS.md", REPO / "CLAUDE.md"]

OLD = """- 服务器下载命令（国内网络环境）：
  - ModelScope（推荐，国内快）：`python -c "from modelscope import snapshot_download; snapshot_download('模型名', local_dir='/root/...')"`
  - HuggingFace 镜像：`HF_ENDPOINT=https://hf-mirror.com HF_HUB_DISABLE_XET=1 python -c "from huggingface_hub import snapshot_download; ..."`
"""

NEW = """- 服务器下载命令（**只用国内源，不碰 HuggingFace**）：
  - ModelScope：`python -c "from modelscope import snapshot_download; snapshot_download('模型名', cache_dir='/root/autodl-tmp/modelscope')"`
  - 先核实仓库名：`from modelscope.hub.api import HubApi; HubApi().get_model_files('<repo>')`
    —— 猜名字会 404（本项目已踩过：`AI-ModelScope/llava-1.5-7b-hf` 不存在，实际是 `llava-hf/llava-1.5-7b-hf`）
  - 缓存目录一律 `MODELSCOPE_CACHE`（放数据盘），**不要用 `HF_HOME`**
  - **⛔ 不得**设置 `HF_ENDPOINT`，**不得**调用 `huggingface_hub.snapshot_download`；
    运行 `transformers`/`peft` 时用**本地绝对路径**加载权重，并设 `HF_HUB_OFFLINE=1`、`TRANSFORMERS_OFFLINE=1`
"""


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    a = ap.parse_args()
    if not a.apply:
        print("  (dry run)")
        return 0
    for f in FILES:
        if not f.exists():
            print(f"  {f.name} missing")
            continue
        t = io.open(f, encoding="utf-8").read()
        if OLD in t:
            t = t.replace(OLD, NEW, 1)
            io.open(f, "w", encoding="utf-8", newline="").write(t)
            print(f"  {f.name}: HF download commands replaced with ModelScope-only guidance")
        else:
            print(f"  {f.name}: block not found (already stripped?)")
        # report any surviving HF references, so nothing is missed
        leftovers = [l.strip() for l in io.open(f, encoding="utf-8").read().splitlines()
                     if "hf-mirror" in l or "huggingface_hub" in l]
        for l in leftovers:
            print(f"    leftover: {l[:110]}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
