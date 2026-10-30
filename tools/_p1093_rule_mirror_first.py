# -*- coding: utf-8 -*-
r"""Update the source-priority rule: the mirror is fastest and is used first.

Operator instruction 2026-10-16 (latest): "规矩改了，走镜像最快" -- the earlier "domestic sources only, no HF"
wording is superseded. The mirror route (host 3's method) is the preferred one again.

Two measured lessons are kept, because they cost time today and are independent of which source is preferred:

* a single connection can be throttled to ~1 MB/s while the same host's link carries 13-18 MB/s -- so if a
  download is slow, measure single versus many connections before blaming the source;
* a download is only "stuck" after 30-60 s of zero growth, and the fix is many connections or another source,
  measured rather than assumed.

    python tools/_p1093_rule_mirror_first.py [--apply]
"""
from __future__ import annotations

import argparse
import io
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
FILES = [REPO / "AGENTS.md", REPO / "CLAUDE.md"]

OLD_HEAD = '> **"用国内源就不要hf"** —— 2026-10-16 操作者补充原话'
NEW_HEAD = ('> **"规矩改了，走镜像最快"** —— 2026-10-16 操作者最新指示（**取代**此前的"用国内源就不要hf"；'
            '该条已作废，见下）')

OLD_TABLE = """| 顺序 | 源 | 用途 | 实测（2026-10-16，AutoDL 主机）|
|---|---|---|---|
| **1** | **ModelScope** `modelscope.cn` | 模型、数据集 | 单连接 **633 kB/s**（权重 4.96 GB 分片实测）|
| **2** | **pypi.tuna.tsinghua.edu.cn** | Python 包 | **3.1–4.5 MB/s** ✅ |
| **3** | 阿里云 pypi 镜像（备用）| Python 包 | 探针 531 kB/s |
| ⛔ | **HuggingFace（`huggingface.co` / `hf-mirror.com`）** | **不使用** | 已决定不依赖 HF |
| ❌ | `download.pytorch.org` | — | **0 B/s，卡死**（476 MB 已下载量停住不动）|"""

NEW_TABLE = """| 顺序 | 源 | 用途 | 实测（2026-10-16，AutoDL 主机）|
|---|---|---|---|
| **1** ⭐ | **`hf-mirror.com`**（`HF_ENDPOINT` + `snapshot_download`）| **模型、数据集** | **主机 3：15 GB / 6–8 分钟（≈30–40 MB/s）** ✅ 首选 |
| **2** | **pypi.tuna.tsinghua.edu.cn** | Python 包 | **3.1–4.6 MB/s** ✅ |
| **3** | **ModelScope** `modelscope.cn` | 模型、数据集兜底 | 单连接 ~1 MB/s；**多连接 13–18 MB/s** |
| 4 | 阿里云 pypi 镜像 | Python 包备用 | 探针 531 kB/s |
| ❌ | `huggingface.co`（直连）| — | **不可达** |
| ❌ | `download.pytorch.org` | — | **0 B/s，卡死**（476 MB 处停住）|

> ⚠️ **同一天两台机的镜像速度差 60 倍**：主机 3 走镜像 **30–40 MB/s**；另一台新实例同样方法**只有 0.5 MB/s**。
> ⇒ **每台新机先探速再定源**（12 秒即可测），不要凭上一次的经验；**镜像优先，但以实测为准**。"""

OLD_HF_BAN = """**⛔ HF 禁令的具体含义**：

1. **不设 `HF_ENDPOINT`、不调 `huggingface_hub.snapshot_download`、不设 `HF_HOME` 作为取模型的途径**；
   需要模型/数据集一律走 ModelScope（`modelscope.snapshot_download`）；
2. **注意 `transformers`/`peft` 运行时会自带 HF 客户端**，但**只读本地缓存路径**即可——
   `from_pretrained(<本地绝对路径>)` 而不是仓库名，避免任何联网解析；
   必要时设 `HF_HUB_OFFLINE=1`、`TRANSFORMERS_OFFLINE=1` 把联网路径彻底关掉；
3. **ModelScope 缓存目录用 `MODELSCOPE_CACHE`**（放数据盘，如 `/root/autodl-tmp/modelscope`），
   不要用 `HF_HOME`；"""

NEW_HF_BAN = """**取模型的标准姿势（镜像优先）**：

1. **首选镜像**：`export HF_ENDPOINT=https://hf-mirror.com`、`export HF_HOME=/root/autodl-tmp/hf`
   （放数据盘），然后 `snapshot_download('仓库名')`；
2. **Redis 兜底**：镜像若慢，换 ModelScope；ModelScope 单连被限速时用**多连接分块下载器**
   （`tools/_p1083_parallel_fetch.py`，已验证把 1 MB/s 提到 13–18 MB/s）；
3. **别用 `HF_ENDPOINT` 之外的方式直连 `huggingface.co`**（本环境不可达）；
4. **慢 ≠ 卡死**：连续 30–60 秒零增长才判卡死；判卡死后**先测单连 vs 多连**，再换源。"""


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
        changed = 0
        for old, new in ((OLD_HEAD, NEW_HEAD), (OLD_TABLE, NEW_TABLE), (OLD_HF_BAN, NEW_HF_BAN)):
            if old in t:
                t = t.replace(old, new, 1)
                changed += 1
        if changed:
            io.open(f, "w", encoding="utf-8", newline="").write(t)
            print(f"  {f.name}: {changed}/3 blocks updated (mirror first)")
        else:
            print(f"  {f.name}: nothing matched")
        leftovers = [l.strip() for l in io.open(f, encoding="utf-8").read().splitlines()
                     if "不使用" in l and "HuggingFace" in l]
        for l in leftovers:
            print(f"    still says no-HF: {l[:100]}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
