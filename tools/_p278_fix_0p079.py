# -*- coding: utf-8 -*-
r"""修 `+0.079` 张冠李戴（R1.1/R3.1）（2026-10-12）。

## 证据（`tools/_p252`–`_p255`）

`+0.079` 的唯一出处是 `outputs/master_results.json` →
`experiments.route_d.d1_alpha64_text_r8`（**Route D，LoRA r=8，α=64**），
`cg_delta = 0.079171`，**`R1 = 0.389`**（正是审稿人点名的差结果）。

而原句主语是"**text-only LoRA 限制 CG 增长、零样本只掉 0.6 点**" → **张冠李戴**。

**正确候选**：
- `tab:position` 的 Flickr30k text-only（α=16 标准配置）= **−0.064**，R@1 = 0.627
  （`outputs/flickr30k/rq2_text_only/results.json`）
- 严格冻结 5-seed text-only = **−0.0465 ± 0.0027**
  （`outputs/analysis/strict_control_summary.json:configs.text_only.cg_delta_mean`）

    python tools\_p278_fix_0p079.py [--apply]
"""
from __future__ import annotations

import argparse
import glob
import io
import shutil
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]

OLD = (r"while text-only LoRA limits CG increase to $+0.079$ and zero-shot degradation to "
       r"$0.6$ percentage points.")
NEW = (r"while text-only LoRA \emph{reduces} the Centroid Gap ($-0.064$ against the frozen "
       r"model at $r=8$, $\alpha=16$; $R@1 = 0.627$) and costs $0.6$ percentage points of "
       r"ImageNet zero-shot accuracy. (An earlier version of this sentence quoted $+0.079$ "
       r"for the text-only arm; that value belongs to a different configuration, "
       r"$\alpha=64$, whose $R@1$ is $0.389$, and it is withdrawn.)")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    a = ap.parse_args()
    files = glob.glob(str(REPO / "paper合" / "sections" / "*.tex")) + \
        glob.glob(str(REPO / "paper合" / "main*.tex"))
    hit = 0
    for f in files:
        t = io.open(f, encoding="utf-8", errors="replace").read()
        n = t.count(OLD)
        if n == 0:
            continue
        print(f"  {Path(f).name}: 命中 {n}")
        hit += n
        if not a.apply:
            continue
        bak = Path(f).with_suffix(Path(f).suffix + ".bak_p278")
        if not bak.exists():
            shutil.copy2(f, bak)
        io.open(f, "w", encoding="utf-8", newline="").write(t.replace(OLD, NEW))
    if not a.apply:
        print("  （预演）")
        return 0
    print(f"\n  → 共改 {hit} 处")
    # 残留检查：$+0.079$ 只应出现在"撤回说明"里
    left = 0
    ok = True
    for f in files:
        t = io.open(f, encoding="utf-8", errors="replace").read()
        for m in __import__("re").finditer(r"\$\+0\.079\$", t):
            left += 1
            ctx = t[max(0, m.start() - 200):m.start() + 80]
            withdrawn = "withdrawn" in ctx or "earlier version" in ctx
            print(f"  {Path(f).name}: {'✅ 在撤回语境' if withdrawn else '🔴 非撤回语境'}")
            ok = ok and withdrawn
    print(f"  '$+0.079$' 出现 {left} 次（应仅为撤回说明）")
    return 0 if ok else 2


if __name__ == "__main__":
    raise SystemExit(main())
