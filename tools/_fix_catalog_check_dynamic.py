# -*- coding: utf-8 -*-
r"""把 `tools/_check_catalog_sum.py` 的硬编码计数改为动态（2026-10-06）。

## 问题

该脚本的"三段口径"一行**硬编码**了 `95`、`162`、`374`：

```
正文三段口径（目录 + ODE 162 + 严格冻结 95）= 374
```

计数一旦变化（本次 BioCLIP 计入后 95→104、374→383），**该行就会报出过期数字**——
这正是本项目反复出现的"**硬编码数字与实测脱节**"问题的又一处。

## 改法

- **严格冻结 run 数**：改为**从 `outputs/` 实测统计**
- **ODE 拟合数**：从 `validation.tex` 的正文里正则抽取（它是论文自己声明的）
- **全文合计**：从稿件的三个数字里抽取（目录表的 Total、ODE 数、严格冻结数）

    python tools\_fix_catalog_check_dynamic.py [--apply]
"""
from __future__ import annotations

import io
import re
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
F = REPO / "tools" / "_check_catalog_sum.py"

OLD = '''    print("\\n=== 判定 ===")
    print(f"  改动前：求和 {so} ｜ Total {total_o} ｜ 正文称 117 个")
    print(f"  改动后：求和 {s} ｜ Total {total} ｜ 正文称 374 个")
    print()
    if so == total_o:
        print("  ✅ 原表自洽（求和 = Total）。")
    else:
        print(f"  ⚠ 原表本身就不自洽：求和 {so} ≠ Total {total_o}")
    print(f"  新增严格冻结 95 → 正确 Total 应为 **{so + 95}**（若保持原口径）")
    print(f"  正文三段口径（目录 + ODE 162 + 严格冻结 95）= **{so + 162 + 95}**")
    return 0'''

NEW = '''    print("\\n=== 判定（数字均动态读取，不硬编码）===")
    print(f"  改动前：求和 {so} ｜ Total {total_o}")
    print(f"  改动后：求和 {s} ｜ Total {total} ｜ {'✅ 自洽' if s == total else '❌ 不自洽'}")

    # ── 动态统计严格冻结 run 数（不再硬编码）
    import glob as _glob
    sf_groups = [
        "outputs/strict_freeze/*/seed*/results.json",
        "outputs/strict_freeze_rank/r*/*/seed*/results.json",
        "outputs/strict_freeze_openclip/*/seed*/results.json",
        "outputs/strict_freeze_openclip_rank/r4/*/seed*/results.json",
        "outputs/siglip_strict/*/s4_siglip_lora_*/results.json",
        "outputs/siglip_strict/*/s6_siglip_lora_vision_only/results.json",
        "outputs/siglip_strict/*/s7_siglip_lora_r4_*/results.json",
    ]
    n_sf_files = sum(len(_glob.glob(str(REPO / g))) for g in sf_groups)
    # BioCLIP 的结果在部分结果文件里（run_log 解析而来）
    bio = REPO / "outputs" / "strict_freeze_bioclip" / "results_partial.json"
    n_bio = 0
    if bio.exists():
        import json as _json
        n_bio = len(_json.loads(bio.read_text(encoding="utf-8")).get("records") or [])
    n_sf = n_sf_files + n_bio

    # ── 动态读 ODE 拟合数（论文自己声明）
    va = io.open(REPO / "paper合" / "sections" / "validation.tex", encoding="utf-8").read()
    m_ode = re.search(r"(?:fit the ODE on|across)\\s+(\\d+)\\s+experiments", va)
    n_ode = int(m_ode.group(1)) if m_ode else None

    # ── 动态读全文合计（摘要）
    ab = io.open(REPO / "paper合" / "main_nc.tex", encoding="utf-8").read()
    m_tot = re.search(r"(?:spans|across)\\s+(\\d+)\\s*\\n?\\s*experiments", ab)
    n_tot = int(m_tot.group(1)) if m_tot else None

    print(f"\\n  实测严格冻结 run : {n_sf}（各骨干 {n_sf_files} + BioCLIP {n_bio}）")
    print(f"  论文声明 ODE 拟合 : {n_ode}")
    print(f"  附录目录求和      : {s}")
    print(f"  摘要声明全文合计  : {n_tot}")
    if None not in (n_ode, n_tot):
        expect = s + n_ode
        ok = expect == n_tot
        print(f"  目录 + ODE = {s} + {n_ode} = {expect} ｜ 摘要称 {n_tot}"
              f"  → {'✅ 一致' if ok else '❌ 不一致'}")
        if ok and n_sf != s - 117:
            print(f"  ⚠ 严格冻结实测 {n_sf} 与目录表隐含的 {s - 117} 不符——目录表 XIV 类需核对")
        elif ok:
            print(f"  ✅ 严格冻结实测 {n_sf} = 目录表隐含值（{s} − 117）")
    return 0'''


def main() -> int:
    apply = "--apply" in sys.argv
    t = io.open(F, encoding="utf-8").read()
    if "动态统计严格冻结" in t:
        print("  已改，跳过")
        return 0
    c = t.count(OLD)
    if c != 1:
        print(f"  ⚠ 未唯一命中（{c} 次）")
        return 1
    print("  ✅ 命中硬编码段")
    if apply:
        io.open(F, "w", encoding="utf-8", newline="").write(t.replace(OLD, NEW, 1))
        t2 = io.open(F, encoding="utf-8").read()
        for k in ("动态统计严格冻结", "results_partial.json", "不硬编码"):
            assert k in t2, f"断言失败：缺 {k}"
        assert "严格冻结 95" not in t2
        print("  ✅ 已改为动态并断言通过")
    else:
        print("  （预演）")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
