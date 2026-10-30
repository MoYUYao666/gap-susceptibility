# -*- coding: utf-8 -*-
r"""把 BioCLIP 的 9 个严格冻结 run 计入实验总数（2026-10-06）。

## 计数链

| 组 | 原 | 补 BioCLIP 后 |
|---|---|---|
| 附录目录（13 类机理 117 + XIV 类严格冻结） | 212 | **117 + 104 = 221** |
| ODE 拟合 | 162 | 162 |
| **全文合计** | **374** | **383** |

**严格冻结**：95 → **104**（+9，BioCLIP rank 4 × 3 臂 × 3 seeds）。

## 为什么必须补

正文的设计模式① 现在引用 BioCLIP 的结果（`tab:position_strict` 有它的行），
**实验计数却把它排除在外**——与"计数应涵盖所报告的实验"不一致（上一轮刚修过这类问题）。

## 同时更新盘点脚本

`tools/_count_strictfreeze_runs.py` 原来**没有 BioCLIP 目录**，故合计 95。补上后应为 104。

    python tools\_pa_add_bioclip_count.py [--apply]
"""
from __future__ import annotations

import io
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
SEC = REPO / "paper合" / "sections"

OLD_N, NEW_N = 374, 383          # 全文合计
OLD_SF, NEW_SF = 95, 104         # 严格冻结
OLD_CAT, NEW_CAT = 212, 221      # 附录目录（117 + 严格冻结）


def main() -> int:
    apply = "--apply" in sys.argv
    n = 0

    # ① 盘点脚本：补 BioCLIP 组
    cs = REPO / "tools" / "_count_strictfreeze_runs.py"
    t = io.open(cs, encoding="utf-8").read()
    if "strict_freeze_bioclip" not in t:
        old = ('    ("SigLIP r4 两臂", "outputs/siglip_strict/*/s7_siglip_lora_r4_*/results.json"),\n')
        new = (old +
               '    ("BioCLIP r4 三臂", "outputs/strict_freeze_bioclip/run_log.txt"),\n')
        if old in t:
            print("  ✅ 盘点脚本：将补 BioCLIP 组（按 run_log 行数计）")
            n += 1

    print(f"\n  计数将更新：全文 {OLD_N} → {NEW_N} ｜ 严格冻结 {OLD_SF} → {NEW_SF} ｜ 目录 {OLD_CAT} → {NEW_CAT}")
    if not apply:
        print("  （预演）")
        return 0

    if old in t:
        io.open(cs, "w", encoding="utf-8", newline="").write(t.replace(old, new, 1))

    # ② 稿件：替换计数
    files = list(SEC.glob("*.tex")) + [REPO / "paper合" / "main_nc.tex",
                                       REPO / "paper合" / "main_springer.tex"]
    reps = [(str(OLD_N), str(NEW_N)), (str(OLD_CAT), str(NEW_CAT))]
    changed = {}
    for f in files:
        s = io.open(f, encoding="utf-8").read()
        o = s
        for a, b in reps:
            if a in s:
                s = s.replace(a, b)
        if s != o:
            io.open(f, "w", encoding="utf-8", newline="").write(s)
            changed[f.name] = True
    print(f"  ✅ 已更新 {len(changed)} 个文件：{sorted(changed)}")

    # ③ 目录表：XIV 类计数 95 → 104
    sup = SEC / "supplement.tex"
    s = io.open(sup, encoding="utf-8").read()
    if "Strict-Freezing Controls (three backbones, $r\\in[1,64]$) & 95" in s:
        s = s.replace("Strict-Freezing Controls (three backbones, $r\\in[1,64]$) & 95",
                      "Strict-Freezing Controls (four backbones, $r\\in[1,64]$) & 104")
        io.open(sup, "w", encoding="utf-8", newline="").write(s)
        print("  ✅ 目录表 XIV 类：95 → 104（并改 three → four backbones）")

    s2 = io.open(sup, encoding="utf-8").read()
    for k in (str(NEW_N), str(NEW_CAT), "104"):
        assert k in s2, f"supplement 断言失败：缺 {k}"
    # 残留检查
    left = 0
    for f in files:
        ss = io.open(f, encoding="utf-8").read()
        left += ss.count(str(OLD_N)) + ss.count(str(OLD_CAT))
    print(f"\n  {'✅' if left == 0 else '⚠'} 残留旧计数（{OLD_N}/{OLD_CAT}）: {left} 处")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
