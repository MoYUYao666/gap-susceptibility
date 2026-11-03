# -*- coding: utf-8 -*-
r"""Tighten the source rule: domestic sources only, no HuggingFace.

Operator instruction 2026-10-16: "用国内源就不要hf" -- having settled on domestic sources, HuggingFace is not to
be used at all. The previous wording kept `hf-mirror.com` as a fallback; that fallback is removed, and the
rule now states plainly that HF endpoints and HF-side tooling are not used on the cloud.

    python tools/_p1077_no_hf_rule.py [--apply]
"""
from __future__ import annotations

import argparse
import io
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
FILES = [REPO / "AGENTS.md", REPO / "CLAUDE.md"]

OLD_TABLE = """| 顺序 | 源 | 用途 | 实测（2026-10-16，AutoDL 主机）|
|---|---|---|---|
| **1** | **ModelScope** `modelscope.cn` | 模型、数据集 | 单连接 **633 kB/s**（权重 4.96 GB 分片实测）|
| **2** | **pypi.tuna.tsinghua.edu.cn** | Python 包 | **3.1–4.5 MB/s** ✅ |
| 3 | `hf-mirror.com`（`HF_ENDPOINT`）| HF 模型/数据集兜底 | 探针 227 B/s，**曾成功下过 13 GB** |
| ❌ | `download.pytorch.org` | — | **0 B/s，卡死**（476 MB 已下载量停住不动）|
| ❌ | `huggingface.co` | — | **不可达**（`Network is unreachable`）|"""

NEW_TABLE = """> **"用国内源就不要hf"** —— 2026-10-16 操作者补充原话

| 顺序 | 源 | 用途 | 实测（2026-10-16，AutoDL 主机）|
|---|---|---|---|
| **1** | **ModelScope** `modelscope.cn` | 模型、数据集 | 单连接 **633 kB/s**（权重 4.96 GB 分片实测）|
| **2** | **pypi.tuna.tsinghua.edu.cn** | Python 包 | **3.1–4.5 MB/s** ✅ |
| **3** | 阿里云 pypi 镜像（备用）| Python 包 | 探针 531 kB/s |
| ⛔ | **HuggingFace（`huggingface.co` / `hf-mirror.com`）** | **不使用** | 已决定不依赖 HF |
| ❌ | `download.pytorch.org` | — | **0 B/s，卡死**（476 MB 已下载量停住不动）|

**⛔ HF 禁令的具体含义**：

1. **不设 `HF_ENDPOINT`、不调 `huggingface_hub.snapshot_download`、不设 `HF_HOME` 作为取模型的途径**；
   需要模型/数据集一律走 ModelScope（`modelscope.snapshot_download`）；
2. **注意 `transformers`/`peft` 运行时会自带 HF 客户端**，但**只读本地缓存路径**即可——
   `from_pretrained(<本地绝对路径>)` 而不是仓库名，避免任何联网解析；
   必要时设 `HF_HUB_OFFLINE=1`、`TRANSFORMERS_OFFLINE=1` 把联网路径彻底关掉；
3. **ModelScope 缓存目录用 `MODELSCOPE_CACHE`**（放数据盘，如 `/root/autodl-tmp/modelscope`），
   不要用 `HF_HOME`；"""

OLD_POINT5 = """5. **慢 ≠ 卡死**：连续 30–60 秒零增长才判定卡死，然后换源；
6. **模型权重仍然只在服务器端下载**（`AGENTS.md` 既有规则），本规则不改变这一点。"""

NEW_POINT5 = """5. **慢 ≠ 卡死**：连续 30–60 秒零增长才判定卡死，然后**换国内源**（不是换回 HF）；
6. **模型权重仍然只在服务器端下载**（既有规则），本规则不改变这一点；
7. **ModelScope 单连接 633 kB/s 偏慢时先测并行**（多连接聚合），再决定是否需要换数据集侧方案。"""


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
        changed = False
        if OLD_TABLE in t:
            t = t.replace(OLD_TABLE, NEW_TABLE, 1)
            changed = True
        if OLD_POINT5 in t:
            t = t.replace(OLD_POINT5, NEW_POINT5, 1)
            changed = True
        if changed:
            io.open(f, "w", encoding="utf-8", newline="").write(t)
            print(f"  {f.name}: HF fallback removed, ban stated")
        else:
            print(f"  {f.name}: nothing matched (already tightened?)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
