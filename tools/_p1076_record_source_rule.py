# -*- coding: utf-8 -*-
r"""Write the source-priority rule into the project instructions.

Operator instruction 2026-10-16: "立规矩，云端hf速度慢优先国内源ModelScope之类的" -- when HuggingFace is slow on
the cloud, use a domestic source such as ModelScope first.

The rule is added to both `AGENTS.md` and `CLAUDE.md`, which carry the same project instructions, and it is
written with the measured facts from this session (the numbers are what make it actionable rather than a
preference): on the 2026-10-16 host `download.pytorch.org` delivered 0 B/s, `huggingface.co` was unreachable,
`hf-mirror.com` answered at 227 B/s in the probe, `pypi.tuna.tsinghua.edu.cn` ran at 3.1-4.5 MB/s, and
ModelScope delivered 633 kB/s single-connection.

    python tools/_p1076_record_source_rule.py [--apply]
"""
from __future__ import annotations

import argparse
import io
import shutil
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
FILES = [REPO / "AGENTS.md", REPO / "CLAUDE.md"]
MARK = "下载源优先级"

ENTRY = """
## 🔴🔴 下载源优先级（用户明确要求，最高优先级）

> **"立规矩，云端hf速度慢优先国内源ModelScope之类的"** —— 2026-10-16 操作者原话

**云主机上取模型/数据集/依赖包，一律按此顺序选源**：

| 顺序 | 源 | 用途 | 实测（2026-10-16，AutoDL 主机）|
|---|---|---|---|
| **1** | **ModelScope** `modelscope.cn` | 模型、数据集 | 单连接 **633 kB/s**（权重 4.96 GB 分片实测）|
| **2** | **pypi.tuna.tsinghua.edu.cn** | Python 包 | **3.1–4.5 MB/s** ✅ |
| 3 | `hf-mirror.com`（`HF_ENDPOINT`）| HF 模型/数据集兜底 | 探针 227 B/s，**曾成功下过 13 GB** |
| ❌ | `download.pytorch.org` | — | **0 B/s，卡死**（476 MB 已下载量停住不动）|
| ❌ | `huggingface.co` | — | **不可达**（`Network is unreachable`）|

**执行要点**：

1. **先探速再下载**：新主机上手第一件事是量各源吞吐（`curl -m 12 -o /dev/null -w '%{speed_download}'`），
   按实测选源，**不要凭习惯直接 `hf download`**；
2. **ModelScope 仓库名必须用 API 核实**，不要猜：`HubApi().get_model_files(repo)`；
   本次教训：猜的 `AI-ModelScope/llava-1.5-7b-hf` **不存在**（404），实际是 **`llava-hf/llava-1.5-7b-hf`**；
3. **pip 一律带 `-i https://pypi.tuna.tsinghua.edu.cn/simple`**，并设
   `PIP_INDEX_URL` / `PIP_CACHE_DIR=/root/autodl-tmp/pipcache`；
4. **下载放后台并记录速率**（`setsid ... > log 2>&1 &`），便于判断是"慢"还是"卡死"；
5. **慢 ≠ 卡死**：连续 30–60 秒零增长才判定卡死，然后换源；
6. **模型权重仍然只在服务器端下载**（`AGENTS.md` 既有规则），本规则不改变这一点。
"""


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    a = ap.parse_args()
    if not a.apply:
        for f in FILES:
            print(f"  would add the rule to {f.name} ({f.exists()})")
        return 0
    for f in FILES:
        if not f.exists():
            print(f"  {f.name} missing; skipped")
            continue
        text = io.open(f, encoding="utf-8").read()
        if MARK in text:
            print(f"  {f.name}: already present")
            continue
        shutil.copy2(f, f.with_suffix(f.suffix + ".bak_p1076"))
        # insert after the first section heading block, before the model-fetch section if present
        anchor = "# 项目说明"
        idx = text.find(anchor)
        if idx < 0:
            out = ENTRY + "\n" + text
        else:
            nl = text.find("\n", idx)
            out = text[: nl + 1] + ENTRY + text[nl + 1:]
        io.open(f, "w", encoding="utf-8", newline="").write(out)
        print(f"  {f.name}: rule added ({len(out)} bytes, backup kept)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
