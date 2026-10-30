# -*- coding: utf-8 -*-
r"""核 `paper合` 那句的另两个数字：`24%`（full-FT 的 CG 增幅）与 `0.6`（零样本退化）（2026-10-12）。

## 待核句子

> *"Full fine-tuning increases CG by **24\%** and collapses zero-shot accuracy to near-chance
> levels (mean $2.6\%$ over 3 retrained seeds), while text-only LoRA **limits** CG increase to
> $+0.079$ and zero-shot degradation to **0.6** percentage points."*

**已确认 `+0.079` 出自 Route D（α=64，R@1=0.389）——错的配置。**
**本脚本**核另两个数字，并给出整句应改成什么。

    python tools\_p255_sentence_numbers.py [--apply]
"""
from __future__ import annotations

import argparse
import glob
import io
import json
import re
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
OUT = REPO / "outputs" / "analysis" / "sentence_numbers.json"

# 该句涉疑数字的候选来源
CANDIDATES = [
    ("outputs/master_results.json", None),
    ("outputs/analysis/strict_control_summary.json", None),
    ("outputs/analysis/recomputed_tables.json", None),
    ("outputs/layered_ft_results.json", None),
]


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    a = ap.parse_args()

    print("=" * 96)
    print("① full 微调的记录（找 24% 与 2.6%）")
    print("=" * 96)
    for f in glob.glob(str(REPO / "outputs" / "**" / "*.json"), recursive=True):
        if "lit_pool" in f:
            continue
        try:
            d = json.loads(io.open(f, encoding="utf-8", errors="replace").read())
        except Exception:
            continue
        txt = json.dumps(d, ensure_ascii=False)
        if re.search(r"full[_ -]?(fine|ft)", txt, re.I) and "0.26" in txt:
            rel = str(Path(f).relative_to(REPO))
            print(f"\n  ── {rel} ──")
            # 打印含 full 的记录
            def walk(o, path=""):
                if isinstance(o, dict):
                    s = json.dumps(o, ensure_ascii=False)
                    if re.search(r"full[_ -]?(fine|ft)", s, re.I) and len(o) < 40:
                        if any(k in o for k in ("cg_delta", "R1", "top1", "top1_50k")):
                            print(f"     {path[:40]:<42} {s[:200]}")
                            return
                    for k, v in o.items():
                        walk(v, path + "/" + k)
                elif isinstance(o, list):
                    for i, v in enumerate(o[:60]):
                        walk(v, path + f"[{i}]")
            walk(d)

    print()
    print("=" * 96)
    print("② 各候选归档里与 '24%' / '2.6%' / '0.6' 相关的字段")
    print("=" * 96)
    for f in ("outputs/layered_ft_results.json", "outputs/analysis/strict_control_summary.json",
              "outputs/analysis/recomputed_tables.json"):
        p = REPO / f
        if not p.exists():
            continue
        t = io.open(p, encoding="utf-8", errors="replace").read()
        print(f"\n  ── {f} ──")
        for pat, label in ((r"0\.26\d*", "≈0.26（24% 的可能来源）"),
                           (r"2\.6\d*", "≈2.6（near-chance）"),
                           (r"0\.6\d*", "≈0.6（零样本退化）"),
                           (r"full", "含 'full'")):
            ms = list(re.finditer(pat, t))
            print(f"     {label:<26} {len(ms)} 处"
                  + (f"  例: {t[max(0, ms[0].start() - 60):ms[0].start() + 50]!r}" if ms else ""))

    print()
    print("=" * 96)
    print("③ 结论：整句应怎么写")
    print("=" * 96)
    print("  `+0.079` 出自 Route D（α=64, R@1=0.389）→ **必须替换**")
    print("  正确候选：")
    print("    (a) tab:position 的 Flickr30k text-only = **−0.064**（PEFT 约定，R@1=0.627）")
    print("    (b) strict_control 5-seed text-only = **−0.0465 ± 0.0027**（严格冻结）")
    print("  且若句子主题是'text-only 限制 CG 增长'，(a)/(b) 都比 +0.079 更贴题。")

    if a.apply:
        OUT.parent.mkdir(parents=True, exist_ok=True)
        io.open(OUT, "w", encoding="utf-8", newline="").write(json.dumps(
            {"verdict": "replace +0.079",
             "candidates": {"tab_position_flickr30k_text_only": -0.064,
                            "strict_control_text_only_mean": -0.0465049147605896,
                            "strict_control_text_only_sd": 0.0026959439833470354},
             "source_0p079": "outputs/master_results.json -> route_d/d1_alpha64_text_r8"},
            ensure_ascii=False, indent=1))
        print(f"\n  ✅ 已写 {OUT.relative_to(REPO)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
