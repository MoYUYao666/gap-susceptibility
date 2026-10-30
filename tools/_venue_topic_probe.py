# -*- coding: utf-8 -*-
r"""实证明查（续）：**用本文主题词直接检索候选刊近年论文**（2026-10-07）。

## 为什么换方法

`tools/_venue_content_survey.py` 的关键词分类**有假阳性**（已目视确认）：

| 误判 | 原因 |
|---|---|
| "Rank Graduation Box for SAFE AI" 归入 `representation_geometry` | `rank` 命中"rank correlation" |
| "Hiking Optimization Algorithm" 归入 `representation_geometry` | `convergence`/`gradient` 命中优化算法 |
| "recommender systems based on knowledge graph embedding" | `embedding` |

且**更关键**：CVIU 那 20% 的样本**全是视觉任务**（Video Anomaly Recognition、
light-field super-resolution、RGB-D semantic segmentation）——只是"碰巧提到 embedding"。

## 新方法：**直接检索本文的主题词**

用 OpenAlex 的 `search` 参数，在**每刊内部**检索与本文同主题的词组，看有无先例：

| 检索词 | 对应本文的什么 |
|---|---|
| `modality gap` | 核心概念 |
| `parameter-efficient fine-tuning` | 方法主线 |
| `LoRA vision-language` | 具体配置 |
| `vision-language alignment` | 领域 |

**判据**：若某刊近两年**有同类论文**，则该刊**会收这类工作**（有先例）；
若**零命中**，则 desk-reject 风险实质存在。

    python tools\_venue_topic_probe.py [--apply]
"""
from __future__ import annotations

import io
import json
import sys
import time
import urllib.parse
import urllib.request
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
OUT = REPO / "outputs" / "analysis" / "venue_topic_probe.json"

SOURCES = {
    "CVIU": "S185008460",
    "ESWA": "S13144211",
    "KBS": "S10169007",
    "IF": "S7560371",
    "IVC": "S143523412",
    "Neurocomputing": "S123456789",   # 占位，若错则脚本会跳过
}

QUERIES = [
    "modality gap",
    "parameter-efficient fine-tuning",
    "LoRA",
    "vision-language model alignment",
    "adapter fine-tuning cross-modal",
    "zero-shot robustness vision-language",
]


def fetch(url: str) -> dict:
    req = urllib.request.Request(url, headers={"User-Agent": "topic-probe/1.0 (research)"})
    with urllib.request.urlopen(req, timeout=60) as r:
        return json.loads(r.read().decode("utf-8"))


def main() -> int:
    apply = "--apply" in sys.argv
    res = {}
    for key, sid in SOURCES.items():
        print("=" * 96)
        print(f"  【{key}】{sid}")
        print("=" * 96)
        res[key] = {}
        for q in QUERIES:
            url = (f"https://api.openalex.org/works?filter=primary_location.source.id:{sid},"
                   f"from_publication_date:2023-01-01&search={urllib.parse.quote(q)}"
                   f"&per-page=5&select=id,title,publication_year")
            try:
                d = fetch(url)
            except Exception as e:
                print(f"  {q:<38} ❌ {e}")
                continue
            n = d.get("meta", {}).get("count", 0)
            titles = [(w.get("title") or "")[:96] for w in d.get("results", [])][:3]
            res[key][q] = {"count": n, "titles": titles}
            flag = "✅" if n > 0 else "—"
            print(f"  {flag} {q:<38} 命中 {n:>4}")
            for t in titles:
                print(f"        · {t}")
            time.sleep(0.25)
        print()
    if apply:
        OUT.parent.mkdir(parents=True, exist_ok=True)
        io.open(OUT, "w", encoding="utf-8", newline="").write(
            json.dumps(res, ensure_ascii=False, indent=1))
        print(f"  ✅ 已写 {OUT.relative_to(REPO)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
