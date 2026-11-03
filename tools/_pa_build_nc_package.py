# -*- coding: utf-8 -*-
r"""组建 Paper A 的 Neurocomputing 投稿包（`paper合/NC_submission/`）。

## 依据

- 模板：`elsarticle`（`main_nc.tex`，由 `tools/_pa_to_elsarticle.py` 生成，正文 8 个 `\input` 未改）
- 要求：`_guide_neurocomputing.txt` —— 摘要 ≤250 词、Highlights 3–5 条、**single anonymized**（无需匿名）、
  声明须在参考文献之前
- 参考实践：`备选/06_归档稿件/paper_ap3/`（同一作者已投 Neurocomputing 的 elsarticle 稿件）

## 打包内容

| 文件 | 用途 |
|---|---|
| `Manuscript.pdf` | 正文（含作者信息、声明、参考文献） |
| `Highlights.pdf` / `.txt` | Highlights（单独文件，Guide 要求） |
| `Cover Letter.pdf` | 投稿信 |
| `latex_source/` + `latex_source.zip` | LaTeX 源（含 cls/bst 不需要——Elsevier 提供；只打包自己的 tex/bib/图） |
| `README.md` | 上传对照表 |

    python tools\_pa_build_nc_package.py [--apply]
"""
from __future__ import annotations

import io
import shutil
import sys
import zipfile
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
PA = REPO / "paper合"
OUT = PA / "NC_submission"

FILES = [
    (PA / "main_nc.pdf", "Manuscript.pdf"),
    (PA / "highlights_nc.pdf", "Highlights.pdf"),
    (PA / "highlights_nc.txt", "Highlights.txt"),
    (PA / "cover_letter_nc.pdf", "Cover Letter.pdf"),
]

README = """# Paper A —— Neurocomputing 投稿包

> 稿件：*Protect, Don't Perturb: From Empirical Regularities to a Dynamical Theory of Cross-Modal
> Alignment under PEFT* ｜ 单作者 ｜ 模板：Elsevier `elsarticle`

## 上传对照

| 门户 item type | 文件 | 说明 |
|---|---|---|
| Manuscript | `Manuscript.pdf` | 49 页（`elsarticle[review]` 单栏双倍行距，送审用）；含作者信息与全部声明 |
| Highlights | `Highlights.pdf` 或 `Highlights.txt` | **单独文件**，5 条、最长 59 字符 |
| Cover Letter | `Cover Letter.pdf` | 2 页 |
| LaTeX source（可要求时） | `latex_source.zip` | 自己的 tex/bib/图；无需附 `elsarticle.cls`（Elsevier 提供） |

## 合规核验（对照 `_guide_neurocomputing.txt`）

| 条款 | 状态 |
|---|---|
| 摘要 ≤250 词 | ✅ **244 词**（从 PDF 实测） |
| Highlights 单独文件 | ✅ `Highlights.pdf` / `.txt`（5 条，≤85 字符） |
| single anonymized | ✅ 无需匿名，稿件含作者信息 |
| 声明须在参考文献**之前** | ✅ Data availability / Funding / Competing interests / CRediT / Generative AI |
| 参考文献条数 | ✅ 41 条，0 未定义引用 |
| 篇幅 | 无硬性上限条款（Guide 中带数字的只有摘要 250 词与作者简介 100 词） |

## 稿件特征（供填门户与写回复时参考）

- **核心主张**：由梯度流导出 *Gap Susceptibility* 与一阶 ODE；跨归档运行预测完整间隙轨迹，**R² 中位 0.97**。
- **最不同的一点（已如实写入正文与投稿信）**：严格冻结对照在 **CLIP 上支持"只适配文本侧"**
  （配对 t=+10.0），在 **SigLIP 上方向相反**（t=−52.7）→ **位置优势是架构依赖的，不是普适默认**。
- **第二点**：**both 在两架构上检索都更强** → 降间隙 ≠ 提检索。
- **开放问题（正文已标注）**：把方向相反归因于损失函数/编码器/嵌入维度中的哪一项，本轮无法分离。

## 未决事项

- ⏳ **投稿时点**：`paper合` 的实证部分与在审的 P1（`PR-D-26-10149`）同源，**建议等 P1 的决定**再定投稿时机；
  若 P1 被拒，`paper合` 即成为该工作线的主稿。
- ⏳ 若选用 OA 而非订阅制，需先确认 APC 来源（本项目既有结论：Elsevier 混合刊可走 Jisc 协议 £0）。
"""


def main() -> int:
    apply = "--apply" in sys.argv
    missing = [str(s) for s, _ in FILES if not s.exists()]
    if missing:
        print("  ❌ 缺源文件：")
        for m in missing:
            print("     " + m)
        return 1
    print(f"  待复制 {len(FILES)} 件")
    if apply:
        OUT.mkdir(parents=True, exist_ok=True)
        for src, name in FILES:
            shutil.copy2(src, OUT / name)
            print(f"    ✅ {name}  ({src.stat().st_size:,} B)")
        # LaTeX 源
        srcdir = OUT / "latex_source"
    # **先清空**：copytree(dirs_exist_ok=True) 只增不删，历次构建的旧图会累积
    # （2026-10-06 实测：残留 33 个已下线 PNG，使 zip 虚增 2 MB）
    if srcdir.exists():
        shutil.rmtree(srcdir)
        srcdir.mkdir(exist_ok=True)
        shutil.copy2(PA / "main_nc.tex", srcdir / "main_nc.tex")
        shutil.copy2(PA / "references.bib", srcdir / "references.bib")
        (srcdir / "sections").mkdir(exist_ok=True)
        for f in (PA / "sections").glob("*.tex"):
            shutil.copy2(f, srcdir / "sections" / f.name)
        shutil.copytree(PA / "figures", srcdir / "figures", dirs_exist_ok=True)
    # 排除下线图归档：投稿包里只应有稿件实际引用的图（2026-10-06）
    _arch = srcdir / "figures" / "_superseded"
    if _arch.exists():
        shutil.rmtree(_arch)
        print("    （已从投稿包排除 figures/_superseded/）")
        z = OUT / "latex_source.zip"
        with zipfile.ZipFile(z, "w", zipfile.ZIP_DEFLATED) as zf:
            for p in sorted(srcdir.rglob("*")):
                if p.is_file():
                    zf.write(p, p.relative_to(srcdir))
        print(f"    ✅ latex_source/ + latex_source.zip（{len([p for p in srcdir.rglob('*') if p.is_file()])} 文件）")
        (OUT / "README.md").write_text(README, encoding="utf-8")
        print("    ✅ README.md")
        print(f"\n  包目录：{OUT.relative_to(REPO)}")
        for p in sorted(OUT.iterdir()):
            sz = f"{p.stat().st_size:,} B" if p.is_file() else "[dir]"
            print(f"    {p.name:32s} {sz}")
    else:
        print("  （预演，加 --apply 生效）")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
