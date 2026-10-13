# -*- coding: utf-8 -*-
r"""验证 Crossref 能否拿到作者名单（先跑 1–3 条，再决定是否铺开 56 条）（2026-10-10）。

## 为什么要 Crossref

APA 第 7 版要求文末**列全作者**（≤20 位），而 A1 的 56 条多数只有第一作者 + `et al.`。
**按项目唯一原则，不能凭记忆补作者名** → 需权威源。**Crossref 是 DOI 注册机构，作者列表即出版商元数据。**

## 用法

    python tools\_p107_crossref_probe.py --apply
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
OUT = REPO / "outputs" / "analysis" / "crossref_probe.json"
API = "https://api.crossref.org/works"
UA = "A1-ref-audit/1.0 (mailto:contact@example.com)"

SAMPLES = [
    ("wortsman2022", "Robust fine-tuning of zero-shot models"),
    ("liang2022", "Mind the gap: Understanding the modality gap in multi-modal "
                  "contrastive representation learning"),
    ("yamaguchi2025", "Post-pre-training for modality alignment in vision-language "
                      "foundation models"),
]


def query(title: str, rows: int = 3) -> dict:
    q = urllib.parse.urlencode({"query.bibliographic": title, "rows": rows})
    req = urllib.request.Request(f"{API}?{q}", headers={"User-Agent": UA})
    with urllib.request.urlopen(req, timeout=40) as r:
        return json.loads(r.read().decode("utf-8"))


def main() -> int:
    apply = "--apply" in sys.argv
    print("=== Crossref 连通性 + 作者抽取（3 条样本）===")
    out = {}
    for key, title in SAMPLES:
        print(f"\n── [{key}] {title[:70]}")
        try:
            d = query(title)
        except Exception as e:
            print(f"   ❌ 请求失败: {str(e)[:160]}")
            out[key] = {"error": str(e)[:160]}
            continue
        items = d.get("message", {}).get("items", [])
        print(f"   返回 {len(items)} 条候选")
        for it in items[:2]:
            t = (it.get("title") or ["?"])[0]
            auth = it.get("author") or []
            names = "; ".join(
                f"{a.get('family','?')}, {a.get('given','?')}" for a in auth[:6])
            print(f"   • 标题: {t[:80]}")
            print(f"     作者 {len(auth)} 位: {names[:150]}")
            print(f"     DOI: {it.get('DOI')} ｜ 类型: {it.get('type')} ｜ "
                  f"年: {(it.get('issued', {}).get('date-parts') or [['?']])[0][0]}")
        out[key] = {"n_items": len(items),
                    "first": (items[0].get("title") or ["?"])[0] if items else None,
                    "n_authors": len((items[0].get("author") or [])) if items else 0}
        time.sleep(1)

    if apply:
        OUT.parent.mkdir(parents=True, exist_ok=True)
        io.open(OUT, "w", encoding="utf-8", newline="").write(
            json.dumps(out, ensure_ascii=False, indent=1))
        print(f"\n  ✅ 已写 {OUT.relative_to(REPO)}")

    ok = sum(1 for v in out.values() if v.get("n_authors"))
    print(f"\n=== 判定：{ok}/{len(SAMPLES)} 条拿到作者 ===")
    if ok == len(SAMPLES):
        print("  ✅ Crossref 可用 → 可铺开 56 条")
    elif ok:
        print("  ⚠️ 部分可用 → 需按条目类型分流（会议论文可能不在 Crossref）")
    else:
        print("  ❌ 不可用 → 需换源（DBLP / Semantic Scholar / OpenAlex）")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
