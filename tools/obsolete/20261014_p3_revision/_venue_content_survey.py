# -*- coding: utf-8 -*-
r"""实证明查：候选刊**近年实际刊载内容**的主题分布（2026-10-07）。

## 为什么需要

`docs/PAPERA_VENUE_DECISION.md` 已完成 Guide 逐条对照，但 Guide 只给"研究领域"，
**不能回答"该刊实际收什么"**。CVIU 的 Guide 列有 "Data structures and representations" 与 "Theory"，
但**实际刊载可能以视觉任务为主**——这正是决定 desk-reject 风险的关键，必须用数据判。

## 方法

- 数据源：**OpenAlex API**（公开、无需 key；`https://api.openalex.org`）
- 取 **2024-01-01 起**的论文（`type:article`），每刊最多 300 篇，取标题（+摘要）做关键词分类
- **分类用关键词规则**（可复核、可重跑），并**同时输出未分类样本**供人工核对，避免"规则把结论做出来"

## 输出

每刊：总样本数、各类占比、代表性标题（每类 3 条）

    python tools\_venue_content_survey.py [--apply]
"""
from __future__ import annotations

import io
import json
import re
import sys
import time
import urllib.parse
import urllib.request
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
OUT = REPO / "outputs" / "analysis" / "venue_content_survey.json"

SOURCES = {
    "CVIU": "S185008460",
    "ESWA": None,      # 由脚本按刊名解析
    "KBS": None,
    "IF": None,
    "IVC": None,
}
NAMES = {
    "CVIU": "Computer Vision and Image Understanding",
    "ESWA": "Expert Systems with Applications",
    "KBS": "Knowledge-Based Systems",
    "IF": "Information Fusion",
    "IVC": "Image and Vision Computing",
}

# 分类规则：**先匹配先归类**（顺序有意义）
CATS = [
    # 与本文同类：表征/几何/理论
    ("representation_geometry",
     r"modalit|embedding|representation|latent space|feature space|geometry|alignment|"
     r"contrastive|vision-language|vision language|clip\b|theoretical|theory|convergence|"
     r"generalization bound|gradient|rank\b|spectral"),
    # 视觉任务（CVIU 主流）
    ("vision_task",
     r"detection|segment|tracking|recognition|classification of images|image classification|"
     r"super-resolution|denois|depth estimat|pose estimat|reconstruct|captioning|"
     r"retrieval|matching|optical flow|stereo|saliency|inpainting|style transfer|"
     r"face\b|gesture|action recognition|anomaly detection|counting|ocr|document"),
    # 应用系统（ESWA 主流）
    ("application_system",
     r"diagnos|prediction|forecast|fault|monitoring|control|recommend|decision support|"
     r"healthcare|medical|clinical|patient|energy|traffic|financial|stock|industry|"
     r"manufactur|supply chain|agricultur|remote sensing|smart grid"),
    # 生成模型
    ("generative",
     r"diffusion|gan\b|generative|synthes|text-to-image|large language model|\bllm"),
    # 安全/鲁棒
    ("safety_robustness",
     r"adversarial|robust|attack|privacy|federated|backdoor|poison|fairness|interpretab|explainab"),
]


def fetch(url: str) -> dict:
    req = urllib.request.Request(url, headers={"User-Agent": "venue-survey/1.0 (research)"})
    with urllib.request.urlopen(req, timeout=60) as r:
        return json.loads(r.read().decode("utf-8"))


def resolve(name: str) -> str | None:
    q = urllib.parse.quote(name)
    d = fetch(f"https://api.openalex.org/sources?search={q}&per-page=5")
    for s in d.get("results", []):
        if s["display_name"].lower() == name.lower():
            return s["id"].rsplit("/", 1)[-1]
    return d["results"][0]["id"].rsplit("/", 1)[-1] if d.get("results") else None


def works_for(sid: str, limit: int = 300) -> list[dict]:
    out, cursor = [], "*"
    while len(out) < limit:
        url = (f"https://api.openalex.org/works?filter=primary_location.source.id:{sid},"
               f"from_publication_date:2024-01-01,type:article&per-page=200&cursor={cursor}"
               f"&select=id,title,publication_year,abstract_inverted_index")
        d = fetch(url)
        res = d.get("results", [])
        if not res:
            break
        out += res
        cursor = d.get("meta", {}).get("next_cursor")
        if not cursor:
            break
        time.sleep(0.3)
    return out[:limit]


def abstract_of(w: dict) -> str:
    inv = w.get("abstract_inverted_index")
    if not inv:
        return ""
    pos = {}
    for word, idxs in inv.items():
        for i in idxs:
            pos[i] = word
    return " ".join(pos[k] for k in sorted(pos))


def classify(text: str) -> str:
    t = text.lower()
    for cat, pat in CATS:
        if re.search(pat, t):
            return cat
    return "other"


def main() -> int:
    apply = "--apply" in sys.argv
    limit = int(sys.argv[sys.argv.index("--n") + 1]) if "--n" in sys.argv else 300
    result = {}
    for key, sid in SOURCES.items():
        if not sid:
            sid = resolve(NAMES[key])
        print(f"  [{key}] source={sid} 取最多 {limit} 篇（2024-01-01 起）…")
        ws = works_for(sid, limit)
        cats, samples = {}, {}
        for w in ws:
            title = (w.get("title") or "").strip()
            if not title:
                continue
            text = title + " " + abstract_of(w)
            c = classify(text)
            cats[c] = cats.get(c, 0) + 1
            samples.setdefault(c, [])
            if len(samples[c]) < 3:
                samples[c].append(title[:150])
        n = sum(cats.values())
        result[key] = {"source_id": sid, "n": n, "cats": cats, "samples": samples}
        print(f"    样本 {n} 篇")
        for c, k in sorted(cats.items(), key=lambda x: -x[1]):
            print(f"      {c:<24} {k:>4}  ({100*k/max(n,1):.0f}%)")
        print()
    if apply:
        OUT.parent.mkdir(parents=True, exist_ok=True)
        io.open(OUT, "w", encoding="utf-8", newline="").write(
            json.dumps(result, ensure_ascii=False, indent=1))
        print(f"  ✅ 已写 {OUT.relative_to(REPO)}")
    else:
        print("  （预演；加 --apply 落盘）")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
