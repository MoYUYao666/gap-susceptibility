# -*- coding: utf-8 -*-
r"""反查：**"分析优先"的 PEFT / 模态间隙论文实际发在哪些刊**（2026-10-07，选项 3）。

## 为什么换方向

向前的四轮核查（`_venue_content_survey.py` 等）是**从刊侧问"你收不收这类"**，
受 OpenAlex 宽泛匹配所限，只能得到"方向性"结论。

**本轮改为从文献侧反查**：取近两年与本文同主题的论文，**统计它们的期刊分布**。
**有先例的刊 = 真会收**，且顺带得到"这些刊是否在免 APC 清单内"。

## 方法

- OpenAlex：检索本文主题词 → 取 `primary_location.source`（期刊名 + ISSN）
- 过滤 `type:article`、`from_publication_date:2024-01-01`
- **分别统计**：
  - 含 `modality gap` 的论文发在哪
  - 含 `parameter-efficient fine-tuning` + `vision-language` 的论文发在哪
- 与 `docs/OA_FUNDING_ROUTES.md` 的**免 APC 覆盖刊清单**交叉

    python tools\_venue_reverse_lookup.py [--apply]
"""
from __future__ import annotations

import collections
import io
import json
import sys
import time
import urllib.parse
import urllib.request
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
OUT = REPO / "outputs" / "analysis" / "venue_reverse_lookup.json"

# 与本文最贴的主题组合
QUERIES = {
    "modal gap": "modality gap vision-language",
    "PEFT+VLM": "parameter-efficient fine-tuning vision-language",
    "repr analysis": "representation analysis fine-tuning vision-language model",
    "LoRA geometry": "LoRA representation geometry analysis",
}

# 免 APC 覆盖刊（docs/OA_FUNDING_ROUTES.md §一 三分法清单 ①）
FREE = [
    "neurocomputing", "pattern recognition letters", "pattern recognition",
    "image and vision computing", "computer vision and image understanding",
    "neural networks", "expert systems with applications", "information fusion",
    "knowledge-based systems",
]


def fetch(url: str) -> dict:
    req = urllib.request.Request(url, headers={"User-Agent": "reverse-lookup/1.0"})
    with urllib.request.urlopen(req, timeout=60) as r:
        return json.loads(r.read().decode("utf-8"))


def main() -> int:
    apply = "--apply" in sys.argv
    per_q = 200
    res = {}
    for label, q in QUERIES.items():
        url = (f"https://api.openalex.org/works?search={urllib.parse.quote(q)}"
               f"&filter=from_publication_date:2024-01-01,type:article"
               f"&per-page={per_q}&select=id,title,publication_year,primary_location")
        try:
            d = fetch(url)
        except Exception as e:
            print(f"  [{label}] ❌ {e}")
            continue
        venues = collections.Counter()
        for w in d.get("results", []):
            pl = w.get("primary_location") or {}
            src = pl.get("source") or {}
            name = (src.get("display_name") or "(未知)").strip()
            venues[name] += 1
        res[label] = {"query": q, "total": d.get("meta", {}).get("count", 0),
                      "venues": venues.most_common(25)}
        print("=" * 96)
        print(f"  【{label}】query = {q!r}  ｜ 总命中 {res[label]['total']}")
        print("=" * 96)
        for name, n in venues.most_common(15):
            tag = "  🆓免APC" if name.lower() in FREE else ""
            print(f"    {n:>4}  {name[:68]}{tag}")
        print()
        time.sleep(0.3)
    if apply:
        OUT.parent.mkdir(parents=True, exist_ok=True)
        io.open(OUT, "w", encoding="utf-8", newline="").write(
            json.dumps(res, ensure_ascii=False, indent=1))
        print(f"  ✅ 已写 {OUT.relative_to(REPO)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
