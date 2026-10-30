# -*- coding: utf-8 -*-
r"""落账：A1 已投出 **Neural Networks**，稿号 `NEUNET-D-26-09426`（2026-10-12）。

## 已核实（从投稿系统生成的 PDF `docs/_inbox/NEUNET-D-26-09426.pdf` 逐字提取）

| 字段 | 值 |
|---|---|
| 期刊 | **Neural Networks** |
| 稿号 | **`NEUNET-D-26-09426`** |
| Article Type | **Article** |
| **Section/Category** | **Mathematical and Computational Analysis** |
| Keywords | modality gap, zero-shot classification, order preservation, cross-modal alignment, fine-tuning |
| 通讯作者 | **Hongrui Wan**（University of Southampton, UK） |
| 投稿日期 | **12 October 2026** |
| 系统 | Editorial Manager（Aries / iTextSharp） |
| 文件 | 51 页（含系统首页 + Cover letter） |

**提取方式**：`pdftotext -layout` → `docs/_inbox/_extract.txt`（156,854 字符）；
首页字段逐字命中，**非推断**。

## 意义

- **A1 的 Elsevier ATS 转投已完成**（此前 `NEUCOM-D-26-20952` 于 2026-10-10 桌面拒稿；
  转投窗口原定 **2026-11-08 23:59** 前确认 → **已在窗口内完成**）。
- **Section/Category 落在 `Mathematical and Computational Analysis`**，
  与 Lead 的建议一致（理由：A1 是**分析型**工作——τ 与 gap 的诊断量对比、34 个扰动条件、
  17 个检查点、偏差场机制、五组界定监测主张边界的加固实验；非新算法/新系统）。
- **A1 状态由"待投"变为"在审"**。

## 连带影响（须一并落账）

1. **`paper合`（Paper A）尚未投稿** → 其 cover letter 若提及 A1，**须更新为"已投 Neural Networks（`NEUNET-D-26-09426`）"**，
   并**披露同出版商关系**（Elsevier）。
2. **`paper_ap3/`**：P1 拒稿后重复投稿红线已解除，但**仍含 P3 内容**（P3 在 PRL 在审）
   → 与 P3 的重叠**仍须先处理**。
3. **同出版商在审清单更新**：`NEUNET-D-26-09426`（Neural Networks, Elsevier）、
   `PRLETTERS-D-26-02378`（PRL, Elsevier）、`PRLETTERS-D-26-02402`（PRL, Elsevier）、
   `26-0663`（IEEE JOE）。
"""


def main() -> int:
    import sys
    if "--apply" not in sys.argv:
        print("  （预演）")
        return 0
    import io
    from pathlib import Path
    REPO = Path(__file__).resolve().parents[1]

    # ① HANDOFF
    hp = REPO / "HANDOFF.md"
    t = io.open(hp, encoding="utf-8").read()
    if "NEUNET-D-26-09426" in t:
        print("  HANDOFF 已记录")
    else:
        ent = ("> **📮 2026-10-12 —— A1 已投出 **Neural Networks**，稿号 "
               "`NEUNET-D-26-09426`（提交日期 12 October 2026）**\n>\n")
        for line in ENT.splitlines():
            ent += "> " + line + "\n" if line.strip() else ">\n"
        i = t.find("# 项目交接文档")
        j = t.find("\n", i)
        io.open(hp, "w", encoding="utf-8", newline="").write(t[:j + 1] + "\n" + ent + t[j + 1:])
        print("  ✅ HANDOFF 已追加")

    # ② 文件地图
    mp = REPO / "文件地图.md"
    if mp.exists():
        m = io.open(mp, encoding="utf-8").read()
        if "NEUNET-D-26-09426" in m:
            print("  文件地图 已记录")
        else:
            ent = ("> **📮 2026-10-12 —— A1 已投 Neural Networks：`NEUNET-D-26-09426`**（Article；\n"
                   "> Section/Category = **Mathematical and Computational Analysis**；提交日期 12 October 2026）。\n"
                   "> 原 `NEUCOM-D-26-20952`（Neurocomputing）已于 2026-10-10 桌面拒稿；\n"
                   "> **ATS 转投窗口（原定 11-08 截止）已在窗口内完成**。\n")
            i = m.find("\n")
            io.open(mp, "w", encoding="utf-8", newline="").write(m[:i + 1] + "\n" + ent + m[i + 1:])
            print("  ✅ 文件地图 已追加")

    # ③ 投稿包 README
    r = REPO / "SUBMISSION" / "A1_NeuralNetworks" / "README.md"
    if r.exists():
        rt = io.open(r, encoding="utf-8").read()
        if "NEUNET-D-26-09426" not in rt:
            rt = rt.replace(
                "| 目标刊 | **Neural Networks**（ISSN 0893-6080），`main.tex` 的 `\\journal{}` 已是该刊 |",
                "| 目标刊 | **Neural Networks**（ISSN 0893-6080），`main.tex` 的 `\\journal{}` 已是该刊 |\n"
                "| **稿号** | 🎉 **`NEUNET-D-26-09426`** |\n"
                "| **状态** | 🔄 **已投出，在审**（提交日期 **12 October 2026**；Article；"
                "Section/Category = **Mathematical and Computational Analysis**） |")
            rt = rt.replace(
                "| **截止** | ⚠️ **2026-11-08 23:59（须在此前确认转投）** |",
                "| ~~截止~~ | ✅ **已在窗口内完成转投**（原定 2026-11-08 23:59 前确认） |")
            io.open(r, "w", encoding="utf-8", newline="").write(rt)
            print("  ✅ A1 README 已更新")
        else:
            print("  A1 README 已记录")

    # ④ SUBMISSION 总索引
    ix = REPO / "SUBMISSION" / "README.md"
    if ix.exists():
        it = io.open(ix, encoding="utf-8").read()
        it = it.replace(
            "| `A1_NeuralNetworks/` | **A1** | Neural Networks | —（未投） | ⚠️ **ATS 转投须 2026-11-08 23:59 前确认** | 42 |",
            "| `A1_NeuralNetworks/` | **A1** | Neural Networks | **`NEUNET-D-26-09426`** | 🔄 **已投出，在审**（12 Oct 2026；Category = Math. & Comp. Analysis） | 42 |")
        io.open(ix, "w", encoding="utf-8", newline="").write(it)
        print("  ✅ SUBMISSION/README.md 已更新")

    # 核对
    t2 = io.open(hp, encoding="utf-8").read()
    for k in ("NEUNET-D-26-09426", "Mathematical and Computational Analysis", "12 October 2026"):
        print(f"  {'✅' if k in t2 else '🔴'} HANDOFF 含 {k}")
    print(f"  HANDOFF 行数 = {len(t2.splitlines())}")
    return 0


ENT = r"""**已核实**（从投稿系统生成的 PDF `docs/_inbox/NEUNET-D-26-09426.pdf` 逐字提取，
`pdftotext -layout` → `docs/_inbox/_extract.txt`，156,854 字符；**非推断**）

| 字段 | 值 |
|---|---|
| 期刊 | **Neural Networks** |
| 稿号 | **`NEUNET-D-26-09426`** |
| Article Type | **Article** |
| **Section/Category** | **Mathematical and Computational Analysis** |
| Keywords | modality gap, zero-shot classification, order preservation, cross-modal alignment, fine-tuning |
| 通讯作者 | **Hongrui Wan**（University of Southampton, UK） |
| 投稿日期 | **12 October 2026** |
| 文件 | 51 页（含系统首页 + Cover letter） |

**意义**

- **A1 的 Elsevier ATS 转投已完成**：`NEUCOM-D-26-20952`（Neurocomputing）2026-10-10 桌面拒稿，
  转投窗口原定 **2026-11-08 23:59** 前确认 → **已在窗口内完成**，A1 状态由"待投"→"**在审**"。
- **Section/Category 落在 `Mathematical and Computational Analysis`**（与 Lead 建议一致）：
  A1 是**分析型**工作（τ 与 gap 的诊断量对比、34 个扰动条件、17 个检查点、偏差场机制、
  五组界定监测主张边界的加固实验），非新算法/新系统。

**连带影响（须一并处理）**

1. **`paper合`（Paper A）尚未投稿** → 其 cover letter 若提及 A1，**须更新为"已投 Neural Networks
   （`NEUNET-D-26-09426`）"**，并**披露同出版商关系**（Elsevier）。
2. **`paper_ap3/`**：P1 拒稿后重复投稿红线已解除，但**仍含 P3 内容**（P3 在 PRL 在审）
   → 与 P3 的重叠**仍须先处理**。
3. **同出版商在审清单**：`NEUNET-D-26-09426`（Neural Networks, Elsevier）、
   `PRLETTERS-D-26-02378`（PRL, Elsevier）、`PRLETTERS-D-26-02402`（PRL, Elsevier）、
   `26-0663`（IEEE JOE）。"""


if __name__ == "__main__":
    raise SystemExit(main())
