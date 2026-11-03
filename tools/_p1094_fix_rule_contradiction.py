# -*- coding: utf-8 -*-
r"""Resolve the contradiction left by the rule change: the model-acquisition section still banned the mirror.

After `_p1093` set the priority table to "mirror first", the older "model acquisition" section in the same
files still read "只用国内源，不碰 HuggingFace" with an explicit prohibition on `HF_ENDPOINT` and
`huggingface_hub.snapshot_download` -- the opposite of the new rule. Two rules that disagree are worse than
either one, so this rewrites that block and fixes a stray typo ("Redis 兜底" -> "若慢则兜底").

    python tools/_p1094_fix_rule_contradiction.py [--apply]
"""
from __future__ import annotations

import argparse
import io
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
FILES = [REPO / "AGENTS.md", REPO / "CLAUDE.md"]

OLD = """- 服务器下载命令（**只用国内源，不碰 HuggingFace**）：
  - ModelScope：`python -c "from modelscope import snapshot_download; snapshot_download('模型名', cache_dir='/root/autodl-tmp/modelscope')"`
  - 先核实仓库名：`from modelscope.hub.api import HubApi; HubApi().get_model_files('<repo>')`
    —— 猜名字会 404（本项目已踩过：`AI-ModelScope/llava-1.5-7b-hf` 不存在，实际是 `llava-hf/llava-1.5-7b-hf`）
  - 缓存目录一律 `MODELSCOPE_CACHE`（放数据盘），**不要用 `HF_HOME`**
  - **⛔ 不得**设置 `HF_ENDPOINT`，**不得**调用 `huggingface_hub.snapshot_download`；
    运行 `transformers`/`peft` 时用**本地绝对路径**加载权重，并设 `HF_HUB_OFFLINE=1`、`TRANSFORMERS_OFFLINE=1`
"""

NEW = """- 服务器下载命令（**镜像优先**，见上方源优先级表）：
  - **首选**：`export HF_ENDPOINT=https://hf-mirror.com; export HF_HOME=/root/autodl-tmp/hf`，
    然后 `python -c "from huggingface_hub import snapshot_download; print(snapshot_download('llava-hf/llava-1.5-7b-hf'))"`
    —— 主机 3 实测 **15 GB / 6–8 分钟**；`HF_HOME` 必须指向 50 GB 数据盘（根盘只有 30 GB）
  - **兜底**：ModelScope，`modelscope.snapshot_download`（缓存目录用 `MODELSCOPE_CACHE`，同样放数据盘）；
    **仓库名必须先用 `HubApi().get_model_files('<repo>')` 核实**——猜名会 404
    （已踩过：`AI-ModelScope/llava-1.5-7b-hf` 不存在，实际是 `llava-hf/llava-1.5-7b-hf`）
  - **单连慢时不要换源就先试多连接**：`tools/_p1083_parallel_fetch.py` 实测把 ModelScope 的 1 MB/s 提到 **13–18 MB/s**
  - 运行 `transformers`/`peft` 时可只用本地缓存（`HF_HUB_OFFLINE=1`、`TRANSFORMERS_OFFLINE=1`），避免下载后再联网解析
"""

TYPO_OLD = "2. **Redis 兜底**：镜像若慢，换 ModelScope；"
TYPO_NEW = "2. **兜底**：镜像若慢，换 ModelScope；"


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
        n = 0
        if OLD in t:
            t = t.replace(OLD, NEW, 1)
            n += 1
        if TYPO_OLD in t:
            t = t.replace(TYPO_OLD, TYPO_NEW, 1)
            n += 1
        if n:
            io.open(f, "w", encoding="utf-8", newline="").write(t)
            print(f"  {f.name}: {n} block(s) fixed")
        else:
            print(f"  {f.name}: nothing matched")
        # verify no contradiction remains: the file must not both prefer and ban the mirror
        txt = io.open(f, encoding="utf-8").read()
        prefers = "hf-mirror.com" in txt and "首选" in txt
        bans = "不得**设置 `HF_ENDPOINT`" in txt or "不碰 HuggingFace" in txt
        print(f"    prefers mirror: {prefers} | still bans it: {bans} "
              f"=> {'CONSISTENT' if prefers and not bans else 'CHECK'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
