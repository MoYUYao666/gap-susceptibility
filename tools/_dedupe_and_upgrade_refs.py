# -*- coding: utf-8 -*-
r"""按 DOI 去重，并把"标注 arXiv 但其实有正式发表版"的条目升级为 Crossref 权威元数据。

动机（两类真实问题）：
  1. **重复条目**：不同工作流用不同 key 收了同一篇（如 MMBench 同时以 `liu2024mmbench`
     与 `liu2025mmbench` 存在，共用 DOI `10.1007/978-3-031-72658-3_13`）→ 入表会重复；
  2. **venue 降级**：条目 `venue="arXiv"` 但 `doi` 是正式 DOI（如 dodge2019showyourwork
     的 `10.18653/v1/d19-1224` = EMNLP 2019）→ 应据 Crossref 升级，否则参考文献里
     会**把已发表论文写成预印本**。

规则：
  · 以 DOI（小写）为去重键；无 DOI 时退回 arxiv_id；再退回标题。
  · 同组内**保留能被 Crossref 确认的那条元数据**；键名统一取"较新/较完整"者。
  · 只改元数据（venue/year/key），**不改标题**（标题以 Crossref 为准时同步修正）。
  · 输出 `refs_all.json`（覆盖）+ `dedup_report.md`（记录合并了谁、改了什么）。

    python tools/_dedupe_and_upgrade_refs.py
"""
from __future__ import annotations

import importlib.util
import json
from collections import defaultdict
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
DIR = REPO / "paper_review"
spec = importlib.util.spec_from_file_location("vc", REPO / "tools" / "_verify_citations.py")
vc = importlib.util.module_from_spec(spec)
spec.loader.exec_module(vc)


def group_key(e: dict) -> str:
    doi = (e.get("doi") or "").strip().lower()
    if doi and "arxiv" not in doi:
        return "doi:" + doi
    aid = (e.get("arxiv_id") or "").strip()
    if aid:
        return "arxiv:" + aid.lower()
    if doi:
        return "doi:" + doi
    return "title:" + (e.get("title") or "").strip().lower()[:60]


def main() -> int:
    refs = json.loads((DIR / "refs_all.json").read_text(encoding="utf-8"))
    groups: dict[str, list[dict]] = defaultdict(list)
    for e in refs:
        groups[group_key(e)].append(e)

    merged, changes = [], []
    for gk, items in groups.items():
        if len(items) == 1:
            merged.append(items[0])
            continue

        # 取"有正式 DOI 且能 Crossref 确认"的权威元数据
        authority = None
        for e in items:
            doi = (e.get("doi") or "").strip()
            if doi and "arxiv" not in doi.lower():
                m = vc.crossref_by_doi(doi)
                if m:
                    authority = vc.cr_norm(m)
                    authority["doi"] = doi
                    break

        # 键名：优先取年份较大者（通常更贴近正式版）
        items_sorted = sorted(items, key=lambda x: (x.get("year") or 0), reverse=True)
        keep = dict(items_sorted[0])
        dropped = [e.get("key") for e in items if e.get("key") != keep.get("key")]

        before = {k: keep.get(k) for k in ("key", "venue", "year", "doi")}
        if authority:
            if authority.get("venue"):
                keep["venue"] = "ECCV" if "Lecture Notes" in authority["venue"] and "MMBench" in (keep.get("title") or "") else authority["venue"]
            if authority.get("year"):
                keep["year"] = authority["year"]
            keep["doi"] = authority["doi"]
            keep["venue_source"] = "Crossref（据正式 DOI）"
        # 合并 claim
        claims = []
        for e in items:
            c = (e.get("claim_used_for") or "").strip()
            if c and c not in claims:
                claims.append(c)
        if claims:
            keep["claim_used_for"] = " ｜ ".join(claims)
        keep["merged_from"] = dropped
        after = {k: keep.get(k) for k in ("key", "venue", "year", "doi")}
        merged.append(keep)
        if before != after or dropped:
            changes.append({"kept": keep.get("key"), "dropped": dropped,
                            "before": before, "after": after})

    (DIR / "refs_all.json").write_text(json.dumps(merged, ensure_ascii=False, indent=2), encoding="utf-8")

    print(f"条目数：{len(refs)} → {len(merged)}（合并 {len(refs) - len(merged)} 条）\n")
    print("=== 合并/升级明细 ===")
    for c in changes:
        print(f"  保留 `{c['kept']}`，并入 {c['dropped']}")
        print(f"     前: {c['before']}")
        print(f"     后: {c['after']}")

    lines = ["# 去重与 venue 升级报告", "",
             f"条目数 **{len(refs)} → {len(merged)}**（合并 {len(refs) - len(merged)} 条）", ""]
    if changes:
        lines += ["| 保留 key | 并入 | 改动前 | 改动后 |", "|---|---|---|---|"]
        for c in changes:
            lines.append(f"| `{c['kept']}` | {', '.join('`' + d + '`' for d in c['dropped'])} | "
                         f"{c['before']} | {c['after']} |")
    else:
        lines.append("无需合并或升级。")
    (DIR / "dedup_report.md").write_text("\n".join(lines), encoding="utf-8")
    print(f"\n写出 {(DIR / 'dedup_report.md').relative_to(REPO)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
