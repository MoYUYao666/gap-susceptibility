# -*- coding: utf-8 -*-
r"""补最后 4 条（作者检索 + arXiv 页）（2026-10-10）。

## 4 条的性质（实测）

| key | 为何未解析 | 补法 |
|---|---|---|
| `hu2022lora` | 原版 **LoRA** 论文（ICLR 2022），OpenAlex 标题检索被 QA-LoRA 等挤掉 | **原 bibitem 写了 "E.~J. Hu et al."** → 用作者检索 + ICLR 2022 定位；或取 arXiv `2106.09685` |
| `huh2024platonic` | ICML 2024 **Position paper**，OpenAlex 收录的是标题相近的**别的**论文 | 作者 `M.~Huh`（已知）→ 作者检索 |
| `imod` | **CVPR 2026**（新，未索引） | 原 bibitem 只有 `M.~Zhang et al.` → **无法补全，标 UNAVAILABLE** |
| `wan2026protect` | **在投**（Pattern Recognition，无公开记录） | 作者即本文作者 **H.~Wan** → 手动填 |

**原则：缺作者名就标 UNAVAILABLE，不猜。**

    python tools\_p115_fill_last4.py --apply
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
OUT = REPO / "outputs" / "analysis" / "a1_refs_openalex.json"
UA = "A1-ref-audit/1.0 (mailto:contact@example.com)"


def get(url: str):
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    with urllib.request.urlopen(req, timeout=45) as r:
        return json.loads(r.read().decode("utf-8"))


def by_doi(doi: str):
    d = get(f"https://api.openalex.org/works/https://doi.org/{urllib.parse.quote(doi)}")
    return d


def by_title_author(title: str, author: str):
    q = urllib.parse.urlencode({"search": f"{title} {author}", "per-page": 5,
                                "mailto": "contact@example.com"})
    return get(f"https://api.openalex.org/works?{q}")


def authors_of(w):
    out = []
    for a in (w.get("authorships") or []):
        nm = (a.get("author") or {}).get("display_name", "")
        if nm:
            p = nm.split()
            out.append({"family": p[-1], "given": " ".join(p[:-1]), "display": nm})
    return out


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    a = ap.parse_args()

    # ① LoRA：arXiv 2106.09685
    print("=== ① hu2022lora（LoRA, ICLR 2022）按 arXiv DOI 查 ===")
    lora = None
    for doi in ("10.48550/arXiv.2106.09685",):
        try:
            w = by_doi(doi)
            au = authors_of(w)
            print(f"   {w.get('title','?')[:70]}")
            print(f"   作者 {len(au)} 位: {', '.join(x['display'] for x in au[:4])}")
            lora = {"method": "openalex(doi)", "openalex_id": w.get("id"),
                    "openalex_title": w.get("title"), "year": w.get("publication_year"),
                    "n_authors": len(au), "authors": au}
        except Exception as e:
            print(f"   ❌ {doi}: {str(e)[:100]}")
        time.sleep(0.4)

    # ② Platonic：标题 + 作者
    print("\n=== ② huh2024platonic 按『标题 + Huh』查 ===")
    plat = None
    try:
        d = by_title_author("Platonic representation hypothesis", "Huh")
        for w in (d.get("results") or [])[:5]:
            au = authors_of(w)
            print(f"   • {(w.get('title') or '?')[:66]} ｜ 作者 {len(au)} 位 ｜ "
                  f"{w.get('publication_year')}")
            if "platonic" in (w.get("title") or "").lower() and len(au) >= 2:
                plat = {"method": "openalex(title+author)", "openalex_id": w.get("id"),
                        "openalex_title": w.get("title"),
                        "year": w.get("publication_year"),
                        "n_authors": len(au), "authors": au}
                print(f"       ✅ 采用：{', '.join(x['display'] for x in au[:4])}")
                break
    except Exception as e:
        print(f"   ❌ {str(e)[:100]}")

    res = json.loads(io.open(OUT, encoding="utf-8").read())
    rmap = {r["key"]: r for r in res}
    if lora:
        rmap["hu2022lora"].update(lora)
        print("\n  ✅ hu2022lora 已补")
    if plat:
        rmap["huh2024platonic"].update(plat)
        print("  ✅ huh2024platonic 已补")

    # ③ 在投那篇：作者即本人，按已知信息填（**不猜**）
    rmap["wan2026protect"].update({
        "method": "manual(known)",
        "authors": [{"family": "Wan", "given": "Hongrui", "display": "Hongrui Wan"}],
        "n_authors": 1, "year": 2026,
        "note": "在投（Pattern Recognition，under review）；作者即本文作者，非检索所得",
    })
    # ④ CVPR 2026 那篇：无法补全
    rmap["imod"].update({
        "method": "UNAVAILABLE", "authors": [],
        "note": "CVPR 2026，OpenAlex 未索引；原 bibitem 仅记 'M.~Zhang et al.'，"
                "**不猜其余作者**",
    })

    if a.apply:
        io.open(OUT, "w", encoding="utf-8", newline="").write(
            json.dumps(list(rmap.values()), ensure_ascii=False, indent=1))
        ok = [r for r in rmap.values() if r.get("authors")]
        print(f"\n=== 最终 {len(ok)}/{len(rmap)} 条有作者 ===")
        no = [r for r in rmap.values() if not r.get("authors")]
        for r in no:
            print(f"  ⚠ [{r['key']}] {r.get('method')} ｜ {r.get('note','')[:80]}")
        print(f"  ✅ 已写 {OUT.relative_to(REPO)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
