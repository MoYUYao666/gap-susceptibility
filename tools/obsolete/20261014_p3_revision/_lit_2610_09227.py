# -*- coding: utf-8 -*-
r"""核 `2610.09227` 与本稿的关系（引用/被引用/主题近邻）（2026-10-12）。

**为什么要核**：它的摘要说"用量化引起的**表示漂移**作为无标签信号**排序配置**，
与留出检索质量的 macro Spearman 达 0.911"——**方法论上与本稿"τ 作为无标签监控信号"同构**。
必须查清：① 它是否引用本稿/团队工作；② 主题近邻是否说明有人在做同一条线。

    python tools\_lit_2610_09227.py [--apply]
"""
from __future__ import annotations

import argparse
import io
import json
import sys
import time
import urllib.parse
import urllib.request
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
OUT = REPO / "outputs" / "analysis" / "lit_2610_09227.json"
MAILTO = "contact@example.com"
AX = "2610.09227"


def get(url: str, tries: int = 3):
    for i in range(tries):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": f"lit ({MAILTO})"})
            with urllib.request.urlopen(req, timeout=45) as r:
                return json.loads(r.read().decode("utf-8", "replace"))
        except Exception as e:
            if i == tries - 1:
                return {"error": f"{type(e).__name__}: {e}"}
            time.sleep(3)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    a = ap.parse_args()
    res = {}

    # ① arXiv 元数据（含 references 需要 Semantic Scholar）
    print("=" * 92)
    print(f"① {AX} 的 OpenAlex 记录（含引用列表）")
    print("=" * 92)
    d = get("https://api.openalex.org/works?filter=locations.landing_page_url.search:"
            f"{AX}&per_page=3&mailto={MAILTO}")
    if "error" in d:
        # 退回：按标题搜
        d = get("https://api.openalex.org/works?search="
                + urllib.parse.quote("Quantize by Drift Label-Free Mixed-Precision "
                                     "Post-Training Quantization Text Embedders")
                + f"&per_page=3&mailto={MAILTO}")
    if "error" in d:
        print(f"  🔴 {d['error']}")
    else:
        for w in d.get("results", [])[:3]:
            print(f"  {w.get('title')}")
            print(f"    DOI {w.get('doi')} ｜ 年 {w.get('publication_year')} ｜ "
                  f"被引 {w.get('cited_by_count')}")
            print(f"    n_references {len(w.get('referenced_works') or [])}")
            res["openalex"] = {"title": w.get("title"), "doi": w.get("doi"),
                               "year": w.get("publication_year"),
                               "cited_by": w.get("cited_by_count"),
                               "n_refs": len(w.get("referenced_works") or [])}

    # ② 本稿的 4 篇关键文献是否被它引用（用 OpenAlex 反查 citing）
    print()
    print("=" * 92)
    print("② 本稿关键文献的「被引」里是否出现该文 / 该团队")
    print("=" * 92)
    KEYS = {
        "wan2026protect": "Protect, Don't Perturb Cross-Modal Alignment PEFT",
        "schrodi2025two": "Two Effects One Trigger Modality Gap Object Bias",
        "fahim2024contrastive": "It's Not a Modality Gap Contrastive",
        "niss2025iimm": "Inter-Intra Modal Measure Predictive Lens Fine-Tuning",
    }
    for key, title in KEYS.items():
        d2 = get("https://api.openalex.org/works?search=" + urllib.parse.quote(title)
                 + f"&per_page=1&mailto={MAILTO}")
        if "error" in d2 or not d2.get("results"):
            print(f"  🔴 {key}: 查不到")
            continue
        w = d2["results"][0]
        wid = w["id"].split("/")[-1]
        print(f"  {key}: {w.get('title')[:60]} ｜ 被引 {w.get('cited_by_count')}")
        time.sleep(1)
        # 看引用它的论文里有没有 2610 或该团队
        d3 = get(f"https://api.openalex.org/works?filter=cites:{wid}&per_page=50"
                 f"&mailto={MAILTO}")
        hits = []
        if "error" not in d3:
            for c in d3.get("results", []):
                t = (c.get("title") or "")
                au = " ".join((x.get("author") or {}).get("display_name", "")
                              for x in (c.get("authorships") or [])[:3])
                if "drift" in t.lower() or "quantiz" in t.lower() or "Han" in au:
                    hits.append((t, au, c.get("publication_year")))
        print(f"     引用它的 {len(d3.get('results', []))} 篇中，"
              f"含 drift/quantiz/Han 的: {len(hits)}")
        for t, au, y in hits[:3]:
            print(f"       [{y}] {t[:70]} — {au[:44]}")
        res[key] = {"cited_by": w.get("cited_by_count"),
                    "n_citing_checked": len(d3.get("results", [])),
                    "relevant_citing": hits}
        time.sleep(1)

    print()
    print("=" * 92)
    print("③ 结论")
    print("=" * 92)
    print("  （人工判定：该文是否有引用本稿/团队工作 → 若有，须在 Related Work 回应）")

    if a.apply:
        OUT.parent.mkdir(parents=True, exist_ok=True)
        io.open(OUT, "w", encoding="utf-8", newline="").write(
            json.dumps(res, ensure_ascii=False, indent=1))
        print(f"\n  ✅ 已写 {OUT.relative_to(REPO)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
