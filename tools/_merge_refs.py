# -*- coding: utf-8 -*-
"""合并各工作流的文献候选，并去重。

读 `paper_review/refs_candidates_*.json`，按 key 去重（保留首次出现，合并 notes），
输出 `paper_review/refs_all.json` 供 `tools/_verify_citations.py` 核验。

    python tools/_merge_refs.py
"""
from __future__ import annotations

import json
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
DIR = REPO / "paper_review"
OUT = DIR / "refs_all.json"


def key_of(e: dict) -> str:
    return (e.get("key") or "").strip().lower()


def main() -> int:
    files = sorted(DIR.glob("refs_candidates_*.json"))
    if not files:
        print("没有找到 refs_candidates_*.json")
        return 1

    merged: dict[str, dict] = {}
    per_file: dict[str, int] = {}
    for f in files:
        try:
            data = json.loads(f.read_text(encoding="utf-8"))
        except Exception as e:
            print(f"  ❌ {f.name} 解析失败: {e}")
            continue
        if isinstance(data, dict):
            data = data.get("references", [])
        per_file[f.name] = len(data)
        for e in data:
            k = key_of(e)
            if not k:
                k = (e.get("title") or "")[:40].lower()
            if k in merged:
                # 合并 claim_used_for，保留已有元数据
                old = merged[k]
                c1, c2 = old.get("claim_used_for", ""), e.get("claim_used_for", "")
                if c2 and c2 not in c1:
                    old["claim_used_for"] = (c1 + " ｜ " + c2).strip(" ｜")
                # 补全缺失字段
                for fld in ("doi", "arxiv_id", "year", "venue"):
                    if not old.get(fld) and e.get(fld):
                        old[fld] = e[fld]
            else:
                merged[k] = dict(e)

    out = list(merged.values())
    OUT.write_text(json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8")

    print("各文件条数：")
    for name, n in per_file.items():
        print(f"  {name:<32} {n}")
    total_raw = sum(per_file.values())
    print(f"\n原始合计 {total_raw} → 去重后 {len(out)}（合并 {total_raw - len(out)} 条重复）")
    print(f"写出 {OUT.relative_to(REPO)}")

    # 字段完整度自检
    no_id = [e.get("key") for e in out if not (e.get("doi") or e.get("arxiv_id"))]
    print(f"\n⚠️ 无 DOI 也无 arXiv id 的条目 {len(no_id)} 条（只能靠题名检索，核验置信度较低）：")
    for k in no_id[:15]:
        print(f"    - {k}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
