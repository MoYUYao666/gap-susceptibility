# -*- coding: utf-8 -*-
r"""精确核算 `tab:full_experiments` 的各类计数与合计（2026-10-05）。

## 关键：不要被 `\textbf{...}` 里的数字骗到

上一版脚本的 bug：正则只认 `& 数字`，而 Total 行写的是 `& \textbf{374} \\`，
**匹配不到数字** → Total 行既未被识别为 Total，又因行内 `XIV` 含"14"被**误当类别行**计入，
于是得出"求和 212"的**错误结论**。

正确做法：**先剥掉 `\textbf{}` 等命令，再匹配数字**。

    python tools\_verify_experiment_counts.py
"""
from __future__ import annotations

import io
import re
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
SUP = REPO / "paper合" / "sections" / "supplement.tex"
ODE_RUNS = 162


def main() -> int:
    t = io.open(SUP, encoding="utf-8").read()
    i = t.find("begin{longtable}")
    j = t.find("end{longtable}", i)
    tbl = t[i:j]

    def strip_cmds(s: str) -> str:
        s = re.sub(r"\\[a-zA-Z]+\*?(\[[^\]]*\])?(\{([^{}]*)\})?", r"\3", s)
        s = s.replace("$", "").replace("{", "").replace("}", "")
        return s

    rows: list[tuple[str, int, bool]] = []
    for line in tbl.splitlines():
        s = line.strip()
        if "&" not in s or not s.endswith("\\\\"):
            continue
        left, right = s.rsplit("&", 1)
        left_c, right_c = strip_cmds(left).strip(), strip_cmds(right).strip()
        m = re.search(r"(\d[\d,]*)", right_c)
        if not m:
            continue
        val = int(m.group(1).replace(",", ""))
        is_total = "total" in left_c.lower()
        rows.append((left_c, val, is_total))

    print("=== 目录表逐类 ===")
    cat_sum = 0
    tbl_total = None
    for label, val, is_total in rows:
        if is_total:
            tbl_total = val
            print(f"  {'[Total 行]':<10} {label:<48} {val}")
            continue
        cat_sum += val
        print(f"  {'':<10} {label:<48} {val}")

    print(f"\n  各类求和: **{cat_sum}**")
    print(f"  表中 Total: **{tbl_total}**")
    ok = cat_sum == tbl_total
    print(f"  → {'✅ 一致' if ok else f'❌ 不一致（{cat_sum} vs {tbl_total}）'}")

    # 严格冻结对照实测
    import glob
    n_sf = 0
    for pat, mult in (("outputs/strict_freeze/*/seed*/results.json", 1),
                      ("outputs/strict_freeze_rank/r*/*/seed*/results.json", 1),
                      ("outputs/strict_freeze_openclip/*/seed*/results.json", 1),
                      ("outputs/strict_freeze_openclip_rank/r4/*/seed*/results.json", 1),
                      ("outputs/siglip_strict/*/s4_siglip_lora_*/results.json", 1),
                      ("outputs/siglip_strict/*/s6_siglip_lora_vision_only/results.json", 1),
                      ("outputs/siglip_strict/*/s7_siglip_lora_r4_*/results.json", 1)):
        n_sf += len(glob.glob(str(REPO / pat)))

    print("\n=== 三段构成 ===")
    print(f"  目录表 14 类求和          : {cat_sum}")
    print(f"  ODE 拟合（validation 称） : {ODE_RUNS}")
    print(f"  严格冻结对照（实测）      : {n_sf}")
    print(f"  三者之和                  : {cat_sum + ODE_RUNS + n_sf}")
    print(f"  表中 Total                : {tbl_total}")
    grand = cat_sum + ODE_RUNS + n_sf
    assert tbl_total == grand, f"Total 行（{tbl_total}）≠ 三段之和（{grand}）"
    print("  ✅ Total = 目录表 + ODE + 严格冻结")

    print("\n=== 正文/摘要引用核对 ===")
    files = list((REPO / "paper合" / "sections").glob("*.tex")) + [REPO / "paper合" / "main_nc.tex",
                                                                   REPO / "paper合" / "main_springer.tex"]
    hits = 0
    for f in files:
        s = io.open(f, encoding="utf-8").read()
        for m in re.finditer(r"\b374\b", s):
            ctx = re.sub(r"\s+", " ", s[max(0, m.start() - 90):m.start() + 60])
            print(f"  [{f.name}] …{ctx}…")
            hits += 1
    print(f"  共 {hits} 处引用 374")
    stale = 0
    for f in files:
        s = io.open(f, encoding="utf-8").read()
        stale += len(re.findall(r"\b(?:117|278)\s+experiments", s))
    print(f"  残留旧计数（117/278 experiments）: {stale} 处 {'✅' if stale == 0 else '❌'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
