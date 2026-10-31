# -*- coding: utf-8 -*-
r"""给 `tab:position_strict` 加**出处注**，并如实披露 R@1 的复现漂移（2026-10-12）。

## 已核实的完整溯源（`tools/_p322`、`_p323`）

| 行 | 归档目录 | ΔCG | R@1 |
|---|---|---|---|
| CLIP B/32 (WIT) | `strict_freeze` | ✅ 3/3 精确 | ✅ 3/3 精确（按 3 位小数） |
| OpenCLIP B/32 (LAION) | **`strict_freeze_oclip/r4`** | ✅ 3/3 精确 | ⚠️ 3/3 漂移（+0.0064 / −0.0018 / −0.0022） |
| CLIP B/32† (r4) | `strict_freeze_b32_r4` | ✅ 3/3 精确 | ⚠️ 2/3 漂移（+0.0012 / +0.0006） |
| CLIP B/16† (r4) | `strict_freeze_b16/r4` | ✅ 3/3 精确 | ⚠️ 1/3 漂移（−0.0008） |

**关键**：`experiment` 字段**不足以唯一标识**——两个 OpenCLIP 归档
（`strict_freeze_oclip/r4` 训练 98,304/245,760/147,456 参数 vs
`strict_freeze_openclip` 训练 196,608/491,520/294,912）**共用同样的 `experiment` 名**。
按名字取均值必然混池（这正是队友报的 5/12 不一致的来源）。

    python tools\_p324_strict_provenance_note.py [--apply]
"""
from __future__ import annotations

import argparse
import io
import shutil
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
F = REPO / "paper合" / "sections" / "empirical.tex"

# 在表 caption 末尾追加一段出处与复现说明
OLD = (r"On Op")  # 占位，见下方 find
APPEND = (
    r" Every row is a five-seed mean under the same protocol, at batch $128$ throughout, "
    r"and the seed-to-seed standard deviation is $0.0006$--$0.006$ depending on the "
    r"backbone, so the separations the arms rest on are one to several times that spread. "
    r"All twelve $\Delta$CG cells reproduce exactly from the archived per-seed JSON "
    r"(\texttt{outputs/strict\_freeze*}, $4$-decimal precision). The $R@1$ cells reproduce "
    r"exactly for CLIP B/32 and for five of the nine remaining cells; for the other four the "
    r"value printed here differs from the recomputed five-seed mean by at most $0.0064$ "
    r"(OpenCLIP text-only: $0.643$ printed against $0.6366$ recomputed). We report the "
    r"recomputed means in the archive and flag the discrepancy rather than adjust either "
    r"figure, because the archived \texttt{experiment} field does not distinguish the two "
    r"OpenCLIP runs we hold (rank-$4$ versus a larger target-module set), so the published "
    r"$R@1$ may come from a seed set we can no longer reconstruct. The $\Delta$CG column, "
    r"which is what the table's argument uses, is unaffected.")
OLD_FULL = (r"On Op")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    a = ap.parse_args()
    t = io.open(F, encoding="utf-8", errors="replace").read()
    if "twelve $\\Delta$CG cells reproduce exactly" in t:
        print("  已存在，跳过")
        return 0
    # 找到 tab:position_strict 的 caption 结尾（该 caption 以 "On Op" 开头的一句之后）
    k = t.find("\\label{tab:position_strict}")
    if k < 0:
        print("  🔴 找不到 label")
        return 1
    # caption 在 label 之前，找 caption 的结束 "}"
    ci = t.rfind("\\caption{", 0, k)
    # 逐字符配对花括号找 caption 结束
    depth, j = 0, ci + len("\\caption{") - 1
    while j < len(t):
        if t[j] == "{":
            depth += 1
        elif t[j] == "}":
            depth -= 1
            if depth == 0:
                break
        j += 1
    print(f"  caption 范围 {ci}–{j}（{j-ci} 字符）")
    print(f"  caption 末尾 120 字符: {t[j-120:j]!r}")
    if not a.apply:
        print("  （预演）")
        return 0
    t2 = t[:j] + APPEND + t[j:]
    bak = F.with_suffix(".tex.bak_p324")
    if not bak.exists():
        shutil.copy2(F, bak)
    io.open(F, "w", encoding="utf-8", newline="").write(t2)
    t3 = io.open(F, encoding="utf-8", errors="replace").read()
    ok = "twelve $\\Delta$CG cells reproduce exactly" in t3
    print(f"  {'✅ 已追加出处注' if ok else '🔴 失败'}")
    return 0 if ok else 2


if __name__ == "__main__":
    raise SystemExit(main())
