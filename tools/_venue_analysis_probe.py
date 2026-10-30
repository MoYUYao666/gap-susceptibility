# -*- coding: utf-8 -*-
r"""实证明查（终）：**区分"方法应用"与"表征分析"**（2026-10-07）。

## 前两轮的结论与不足

- `_venue_content_survey.py`：关键词分类**有假阳性**（`rank`/`convergence`/`embedding`），
  且 CVIU 的"表征类"样本**全是视觉任务**（只是提到 embedding）→ **方法不可靠**。
- `_venue_topic_probe.py`：CVIU/ESWA **均有大量 VLM+PEFT 先例**（48/239 篇），
  但**标题都是"方法应用到具体视觉任务"**（segmentation / parsing / inpainting）。

**仍缺的一问**：这些刊**有没有"分析表征几何本身"的论文**（如本文），
而**不是**"把方法用在某个视觉任务上"？

## 本轮方法

用**分析类措辞**检索（而非任务类措辞），并**并列任务类**作对照：

| 组 | 检索词 | 若命中说明 |
|---|---|---|
| **分析类**（本文类型） | `analysis of representation geometry`、`empirical study fine-tuning`、`why does fine-tuning`、`understanding representation collapse` | 该刊收**分析型**论文 |
| **任务类**（对照） | `semantic segmentation CLIP`、`object detection adaptation` | 该刊主流 |

**判据**：**若分析类近零命中而任务类大量命中** → 该刊虽收同技术，但**倾向要求落到具体视觉任务**
→ 本文**须重新包装或改投**。

    python tools\_venue_analysis_probe.py [--apply]
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
OUT = REPO / "outputs" / "analysis" / "venue_analysis_probe.json"

SOURCES = {"CVIU": "S185008460", "ESWA": "S13144211", "KBS": "S10169007"}

GROUPS = {
    "分析类（本文类型）": [
        "analysis of representation geometry",
        "empirical study of fine-tuning",
        "understanding representation collapse",
        "how fine-tuning affects representations",
    ],
    "任务类（对照）": [
        "semantic segmentation vision-language",
        "object detection adaptation CLIP",
        "image classification fine-tuning",
    ],
}


def fetch(url: str) -> dict:
    req = urllib.request.Request(url, headers={"User-Agent": "analysis-probe/1.0"})
    with urllib.request.urlopen(req, timeout=60) as r:
        return json.loads(r.read().decode("utf-8"))


def main() -> int:
    apply = "--apply" in sys.argv
    res = {}
    for key, sid in SOURCES.items():
        print("=" * 96)
        print(f"  【{key}】")
        print("=" * 96)
        res[key] = {}
        for gname, qs in GROUPS.items():
            print(f"  ── {gname} ──")
            tot = 0
            for q in qs:
                url = (f"https://api.openalex.org/works?filter=primary_location.source.id:{sid},"
                       f"from_publication_date:2023-01-01&search={urllib.parse.quote(q)}"
                       f"&per-page=3&select=id,title,publication_year")
                try:
                    d = fetch(url)
                except Exception as e:
                    print(f"     {q:<42} ❌ {e}")
                    continue
                n = d.get("meta", {}).get("count", 0)
                tot += n
                res[key][q] = {"count": n,
                               "titles": [(w.get("title") or "")[:92] for w in d.get("results", [])]}
                print(f"     {q:<42} {n:>4}")
                for t in res[key][q]["titles"][:2]:
                    print(f"         · {t}")
                time.sleep(0.25)
            res[key][gname + "_total"] = tot
            print(f"     → 小计 {tot}")
            print()
    if apply:
        OUT.parent.mkdir(parents=True, exist_ok=True)
        io.open(OUT, "w", encoding="utf-8", newline="").write(
            json.dumps(res, ensure_ascii=False, indent=1))
        print(f"  ✅ 已写 {OUT.relative_to(REPO)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
