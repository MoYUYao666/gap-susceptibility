# -*- coding: utf-8 -*-
r"""更新投稿包 README（页数/词数/文献条数已过期）（2026-10-11）。

## 旧 → 新

| 项 | 旧 README | 实测 |
|---|---|---|
| 页数 | 49 | **56** |
| 摘要 | 244 词 | **246 词** |
| 参考文献 | 41 条 | **47 条** |
| 更新日期 | — | **2026-10-11** |

**另补**：批次统一与 seed 口径、统计审核结果、以及 `latex_source` 与主稿的哈希一致性检查说明。

    python tools\_docs_pkg_readme.py [--apply]
"""
from __future__ import annotations

import io
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
F = REPO / "paper合" / "NC_submission" / "README.md"

NEW = """# Paper A —— 投稿包（Neurocomputing 模板）

> 稿件：*Protect, Don't Perturb: From Empirical Regularities to a Dynamical Theory of Cross-Modal
> Alignment under PEFT* ｜ 单作者 ｜ 模板：Elsevier `elsarticle`
> **本包最后同步：2026-10-11**（在此之前的版本基于 10-06 的旧稿）

## 上传对照

| 门户 item type | 文件 | 说明 |
|---|---|---|
| Manuscript | `Manuscript.pdf` | **56 页**（`elsarticle[review]` 单栏双倍行距，送审用）；含作者信息与全部声明 |
| Highlights | `Highlights.pdf` 或 `Highlights.txt` | **单独文件**，5 条、最长 **61** 字符 |
| Cover Letter | `Cover Letter.pdf` | 2 页 |
| LaTeX source（可要求时） | `latex_source.zip` | 43 个文件（tex/bib/图）；无需附 `elsarticle.cls`（Elsevier 提供） |

## 合规核验（对照 `期刊指南/_guide_neurocomputing.txt`）

| 条款 | 状态 |
|---|---|
| 摘要 ≤250 词 | ✅ **246 词**（从 `main_nc.tex` 实测；三种口径 239/246/244） |
| Highlights 单独文件 | ✅ `Highlights.pdf` / `.txt`（**5** 条，≤85 字符） |
| single anonymized | ✅ 无需匿名，稿件含作者信息 |
| 声明须在参考文献**之前** | ✅ Data availability / Funding / Competing interests / CRediT / Generative AI |
| 参考文献 | ✅ **47 条**，引用 47 个 key，**0 未定义 / 0 未引用**（`elsarticle-harv`） |
| 篇幅 | 无硬性上限条款（Guide 中带数字的只有摘要 250 词与作者简介 100 词） |

## 数据口径（**2026-10-11 统一**）

| 项 | 值 |
|---|---|
| **批次大小** | 全部 run **batch 128**（此前 COCO 部分 run 为 64，已重跑统一） |
| **seed 数** | 严格冻结对照 **5 seed**；解码器 VLM **13 seed** |
| **统计审核** | `tools/_audit_statistics.py` → **20/20 项数字匹配，0 问题** |
| **门禁** | `tools/_claim_ledger.py --apply` → **80/80 通过** |
| **投稿包一致性** | `tools/_p190_finish_submission.py` → `latex_source` 与主稿**哈希一致** |

## 稿件特征（供填门户与写回复时参考）

- **核心主张**：由梯度流导出 *Gap Susceptibility* 与一阶 ODE；跨归档运行预测完整间隙轨迹，**R² 中位 0.97**。
- **最不同的一点（已如实写入正文与投稿信）**：严格冻结对照在 **CLIP 上支持"只适配文本侧"**
  （三个骨干一致，OpenCLIP 相邻臂差 $1.5$/$2.7$ 合并 sd），在 **SigLIP 上方向相反**（t=−52.7）
  → **位置优势是架构依赖的，不是普适默认**。
- **第二点**：**both 在两架构上检索都更强** → 降间隙 ≠ 提检索。
- **第三点（本轮新增）**：最优位置**随数据集翻转** —— Flickr30k 上 `text_only` 最保护
  （$-0.0304\\pm0.0039$ vs `both` $-0.0204\\pm0.0028$），MS-COCO 上 `both` 最保护
  （$-0.0877\\pm0.0022$ vs `text_only` $-0.0430\\pm0.0028$），各 5 seed、同批次。
- **解码器 VLM（13 seed）**：`vision_only` 最弱（$DG^*$ 相对变化 $18.0\\pm8.8\\%$，
  其最大值 $35.7\\%$ 仍低于另两臂最小值 $47.8\\%$ / $73.1\\%$，分布不重叠）；
  **两强臂不可分辨**（$0.86$ 合并 sd）。
- **开放问题（正文已标注）**：把方向相反归因于损失函数/编码器/嵌入维度中的哪一项，本轮无法分离。

## 未决事项

- ⏳ **目标刊未定**：候选（免 APC、无拒稿史）**ESWA / KBS / CVIU**；
  本包按 Neurocomputing 模板准备，**若改投需重新核对该刊 Guide**（页数/字数限制差异较大：
  IVC 已出局——字数控 4500–7500，本文约 11{,}254 词）。
- ⏳ **投稿时点**：`paper合` 的实证部分与在审的 P1（`PR-D-26-10149`）同源，
  **建议等 P1 的决定**；若 P1 被拒，`paper合` 即成为该工作线的主稿。
- ⏳ 若选用 OA 而非订阅制，需先确认 APC 来源（既有结论：Elsevier 混合刊可走 Jisc 协议 £0）。
"""


def main() -> int:
    apply = "--apply" in sys.argv
    if not apply:
        print("  （预演）")
        return 0
    old = io.open(F, encoding="utf-8", errors="replace").read()
    bak = F.with_suffix(".md.bak_pre1011")
    if not bak.exists():
        io.open(bak, "w", encoding="utf-8", newline="").write(old)
    io.open(F, "w", encoding="utf-8", newline="").write(NEW)
    t = io.open(F, encoding="utf-8", errors="replace").read()
    for k in ("**56 页**", "**246 词**", "**47 条**", "batch 128", "20/20",
              "80/80", "13 seed", "ESWA / KBS / CVIU"):
        assert k in t, f"断言失败：缺 {k}"
    assert "49 页" not in t and "244 词" not in t and "41 条" not in t, "旧数字仍在"
    print(f"  ✅ README 已更新（旧版备份 README.md.bak_pre1011）")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
