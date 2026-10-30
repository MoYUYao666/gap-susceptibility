# -*- coding: utf-8 -*-
r"""清理 `_p472` 早期命名遗留：确认旧文件的行**已被新文件覆盖**后再删除。

背景：`_p472` 最初把结果写进 `p3d_e0_vs_token_budget.json`（无 split/n 后缀）；
后来改成按 `(split, n)` 分文件（`..._test_n2.json` 等），旧文件成了重复来源。
**重复来源本身就是风险**（两处数字哪天不一致，没人知道该信哪个）。

本脚本**先逐行比对**，只有旧文件的每一行都能在新文件里找到**完全相同**的值（max_pixels /
mean_tokens / E0_real / E0_blank / gap_pct 全部一致）才删除；否则拒绝并退出 1。

    python tools\_p473_dedupe_legacy.py [--apply]
"""
from __future__ import annotations

import argparse
import io
import json
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
A = REPO / "outputs" / "analysis"
LEGACY = A / "p3d_e0_vs_token_budget.json"
NEW = A / "p3d_e0_vs_token_budget_test_n2.json"
KEY = ("max_pixels", "mean_tokens", "E0_real", "E0_blank", "gap_pct")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    a = ap.parse_args()

    print(f"旧文件: {LEGACY}")
    print(f"新文件: {NEW}")
    if not LEGACY.exists() or not NEW.exists():
        print("!! 缺文件，什么都不做")
        return 1

    old = json.loads(io.open(LEGACY, encoding="utf-8").read())["rows"]
    new = json.loads(io.open(NEW, encoding="utf-8").read())["rows"]
    new_sig = {tuple(round(r[k], 6) if isinstance(r[k], float) else r[k] for k in KEY) for r in new}

    missing = []
    for r in old:
        sig = tuple(round(r[k], 6) if isinstance(r[k], float) else r[k] for k in KEY)
        print(f"  旧行 max_pixels={r['max_pixels']:<8} gap={r['gap_pct']:+.4f}% → "
              f"{'已被新文件覆盖' if sig in new_sig else '**新文件里没有**'}")
        if sig not in new_sig:
            missing.append(r["max_pixels"])

    if missing:
        print(f"\n!! 旧文件有 {len(missing)} 行未被覆盖（max_pixels={missing}），**拒绝删除**。")
        return 1

    print(f"\n✅ 旧文件的 {len(old)} 行全部能在新文件（{len(new)} 行）中找到完全相同的值。")
    if not a.apply:
        print("（预演；加 --apply 才删除）")
        return 0
    LEGACY.unlink()
    print(f"✅ 已删除重复来源 {LEGACY.name}；现在 `_p472` 的结果只有 "
          f"`p3d_e0_vs_token_budget_{{split}}_n{{n}}.json` 一种命名。")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
