# -*- coding: utf-8 -*-
r"""文件夹整理：A + B + C + D（2026-10-06，操作者确认"可以"）。

## 做了什么

| 项 | 动作 |
|---|---|
| **A** | 新建 `期刊指南/`，收走 7 个指南文件；**删除 1 个重复**（`_guide_oe_new.bak` 与 `_guide_oe.txt` SHA256 相同） |
| **B** | 3 个 qwen JSON → `outputs/qwen_cf/`（**outputs 里无副本，是唯一份，故只移动不删**） |
| **C** | `待跑实验清单.md` → `docs/`；`run_a1_h_resume.ps1` → `tools/` |
| **D** | 给 9 个 `paper*` 目录各加 `README_是哪篇.md`（进去即见） |

**E（清 `.git-rewrite` 等）未做**——留待操作者看内容后再定。
**F（改 `paper*` 目录名）不做**——14+ 脚本按字面路径打开它们。

## 关键：移动必须同步改引用

代码里硬编码根目录文件的只有 **1 处**：`tools/_ap3_compliance_quickcheck.py:16`
（`GUIDE = REPO / "_guide_neurocomputing.txt"`）→ 移动到 `期刊指南/` 后**必须改**。
文档引用（`文件地图.md`、`HANDOFF.md`）按项目规则"追加+标注"，此处**只改当前状态表**。

    python tools\_reorganize_folders.py [--apply]
"""
from __future__ import annotations

import hashlib
import io
import shutil
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
GUIDE_DIR = REPO / "期刊指南"

GUIDES = ["_guide.txt", "_guide_ivc.txt", "_guide_neurocomputing.txt", "_guide_oe.txt",
          "_oe_guide.txt", "_guide_ocean_engineering.pdf",
          "Guide for authors - Neurocomputing - ISSN 0925-2312 _ ScienceDirect.com by Elsevier.pdf",
          "Guide for authors - Pattern Recognition Letters - ISSN 0167-8655 _ ScienceDirect.com by Elsevier.pdf"]
DUPE = "_guide_oe_new.bak"
DUPE_OF = "_guide_oe.txt"
QWEN = ["qwen_cf_2b_theory_rank8_seed42.json", "qwen_cf_2b_uniform_rank4_seed42.json",
        "qwen_cf_2b_violation_rank8_seed42.json"]

PAPER_README = {
    "paper": ("P1", "Protect, Don't Perturb: Cross-Modal Alignment under PEFT of Vision-Language Models",
              "**Pattern Recognition**", "`PR-D-26-10149`",
              "**Required Reviews Completed**（状态日期 2026-10-04）",
              "主文件 `main_nn.tex`（43 页）",
              "⚠️ **它的决定是 `paper合/` 投稿时点的唯一变量。**"),
    "paper2": ("P2", "（P1 的姊妹工作，已合并）", "—", "—",
               "已合并进 `paper合/`", "主文件 `main.tex`（16 页，`cas-sc` 模板）",
               "本目录保留为单独版。"),
    "paper3": ("P3", "Gradient Structure Laws as Predictors of PEFT Design", "**Pattern Recognition Letters**",
               "`PRLETTERS-D-26-02378`", "**Under Review**（2026-09-26 投，Regular Article）",
               "主文件 `paper_ieee/main.tex`（11 页）；另有 `paper/`、`paper_ICLR_backup/`（各 12 页）",
               "⚠️ **P3 已投出去，这使 `paper_ap3/` 不可投**（一稿两投）。"),
    "paper_a1": ("A1", "（A1 方向稿）", "Neurocomputing 方向", "—",
                 "**不在推进队列**", "主文件 `main.tex`（40 页）；`main_zh.tex` 中文版（22 页）",
                 "当前无动作。"),
    "paper_a2": ("A2 / A23", "（海洋·声呐方向）", "**IEEE Journal of Oceanic Engineering**", "`26-0663`",
                 "已投", "主文件 `main.tex`（66 页）；`main_ieee.tex`（64 页，IEEEtran）；`main_zh.tex`（46 页）",
                 "当前无动作。"),
    "paper_ap3": ("ap3 = P1 + P2 + P3 合并稿", "—", "—", "—",
                  "⚠️ **不可投**（方案 B：保留作技术参考）", "主文件 `main.tex`（86 页）",
                  "**原因：含 P3 内容，而 P3 已投 PRL 在审 → 一稿两投；去掉 P3 后等同 `paper合/`。**"
                  "详见目录内 `⚠️_不可投_READ_ME.md`。"),
    "paper_review": ("PRL Commentary（评论/综述）", "（评论文章）", "**Pattern Recognition Letters**",
                     "`PRLETTERS-D-26-02402`", "**Under Review**（2026-09-28 投）",
                     "本目录为工作版；PRL 格式版见 `paper_review_prl/`", "当前无动作。"),
    "paper_review_prl": ("PRL Commentary 的 PRL 格式版", "—", "**Pattern Recognition Letters**",
                         "`PRLETTERS-D-26-02402`", "**Under Review**",
                         "主文件 `main_prl.tex`（**7 页**，上限 7）；`UPLOAD/` 6 件 + Authorship Confirmation 表",
                         "投稿材料已上传并确认。"),
    "paper合": ("⭐ **Paper A = P1 + P2 合并稿（当前在编主稿）**",
                "（P1+P2 合并，目标 Neurocomputing）", "**Neurocomputing**", "（未投）",
                "⏳ **投稿时点等 P1 的决定**",
                "主文件 `main_nc.tex`（**45 页**，Elsevier `elsarticle`）；Springer 版 `main_springer.tex`（33 页）",
                "投稿包 `NC_submission/` **已就绪**（Manuscript / Highlights / Cover Letter / latex_source / README）。"),
}


def sha(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


def main() -> int:
    apply = "--apply" in sys.argv
    plan: list[str] = []

    # ── A：去重 + 建指南目录
    dp, op = REPO / DUPE, REPO / DUPE_OF
    if dp.exists() and op.exists():
        same = sha(dp) == sha(op)
        plan.append(f"A 删除重复 {DUPE}（与 {DUPE_OF} 同哈希: {same}）")
        assert same, "两者哈希不同，**不可删**"
    moves_a = [(g, GUIDE_DIR / g) for g in GUIDES if (REPO / g).exists()]
    plan.append(f"A 移动 {len(moves_a)} 个指南 → 期刊指南/")

    # ── B / C
    moves_b = [(q, REPO / "outputs" / "qwen_cf" / q) for q in QWEN if (REPO / q).exists()]
    moves_c = [(n, d) for n, d in (("待跑实验清单.md", REPO / "docs" / "待跑实验清单.md"),
                                   ("run_a1_h_resume.ps1", REPO / "tools" / "run_a1_h_resume.ps1"))
               if (REPO / n).exists()]
    plan.append(f"B 移动 {len(moves_b)} 个 qwen JSON → outputs/qwen_cf/")
    plan.append(f"C 移动 {len(moves_c)} 个文件 → docs/ 与 tools/")
    plan.append(f"D 为 {len(PAPER_README)} 个 paper* 目录各写 README_是哪篇.md")

    print("=== 计划 ===")
    for l in plan:
        print("  " + l)

    if not apply:
        print("\n  （预演，加 --apply 执行）")
        return 0

    # ── 执行 A
    if dp.exists() and op.exists():
        assert sha(dp) == sha(op)
        dp.unlink()
        print(f"  ✅ 已删重复 {DUPE}")
    GUIDE_DIR.mkdir(exist_ok=True)
    for src, dst in moves_a:
        shutil.move(str(src), str(dst))
    print(f"  ✅ 已移动 {len(moves_a)} 个指南 → 期刊指南/")

    # ── 执行 B
    (REPO / "outputs" / "qwen_cf").mkdir(parents=True, exist_ok=True)
    for src, dst in moves_b:
        shutil.move(str(src), str(dst))
    print(f"  ✅ 已移动 {len(moves_b)} 个 qwen JSON → outputs/qwen_cf/")

    # ── 执行 C
    for src, dst in moves_c:
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.move(str(src), str(dst))
    print(f"  ✅ 已移动 {len(moves_c)} 个文件")

    # ── 修硬编码引用（唯一 1 处）
    cq = REPO / "tools" / "_ap3_compliance_quickcheck.py"
    t = io.open(cq, encoding="utf-8").read()
    old = 'GUIDE = REPO / "_guide_neurocomputing.txt"'
    new = 'GUIDE = REPO / "期刊指南" / "_guide_neurocomputing.txt"'
    if old in t:
        io.open(cq, "w", encoding="utf-8", newline="").write(t.replace(old, new, 1))
        t2 = io.open(cq, encoding="utf-8").read()
        assert new in t2 and 'REPO / "_guide_neurocomputing.txt"' not in t2
        print("  ✅ 已修 _ap3_compliance_quickcheck.py 的指南路径")
        # 校验能被 Python 解析且文件存在
        import ast
        ast.parse(t2)
        assert (REPO / "期刊指南" / "_guide_neurocomputing.txt").exists(), "移动后指南文件不在新位置"

    # ── 执行 D
    for d, (who, title, venue, idn, status, files, note) in PAPER_README.items():
        dp2 = REPO / d
        if not dp2.exists():
            continue
        body = (f"# 本目录是：{who}\n\n"
                f"> 由 `tools/_reorganize_folders.py` 生成 ｜ 目录索引见根目录 **`哪篇是哪篇.md`**\n\n"
                f"| 项 | 内容 |\n|---|---|\n"
                f"| **是哪篇** | {who} |\n"
                f"| 标题 | {title} |\n"
                f"| 投的期刊 | {venue} |\n"
                f"| 稿号 | {idn} |\n"
                f"| **当前状态** | {status} |\n"
                f"| 主文件 | {files} |\n"
                f"| 备注 | {note} |\n")
        io.open(dp2 / "README_是哪篇.md", "w", encoding="utf-8", newline="").write(body)
    print(f"  ✅ 已写 {len(PAPER_README)} 个 README_是哪篇.md")

    # ── 核对
    print("\n=== 核对 ===")
    left = [g for g in GUIDES if (REPO / g).exists()] + [q for q in QWEN if (REPO / q).exists()]
    print(f"  根目录残留待移文件: {len(left)} {'✅' if not left else left}")
    n_readme = len(list(REPO.glob("paper*/README_是哪篇.md")))
    print(f"  paper* 目录 README 数: {n_readme} {'✅' if n_readme == 9 else '⚠ 应为 9'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
