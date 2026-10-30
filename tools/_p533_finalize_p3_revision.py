# -*- coding: utf-8 -*-
r"""收尾：更新 `文件地图.md` + 落账 P3 修订交付（2026-10-13）。

    python tools\_p533_finalize_p3_revision.py [--apply]
"""
from __future__ import annotations

import argparse
import io
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]

MAP_ADD = """
### P3 修订交付（PRL Revise，2026-10-13 完成）

- **路径**：`SUBMISSION/P3_PRL_revision/`（30 个文件）
- **稿件**（操作者选定档 ①）：
  - `manuscript/main.pdf` = **10 页投稿件**（`paper3/paper_ieee/main.tex`）
  - `manuscript/supplementary.pdf` = **5 页补充材料**（公理推导/证明/协议细节/逐 run 表/表图）
  - `manuscript/main_full.pdf` = **13 页完整版存档**（`main_full.tex` + `sections_full/`，**非投稿件**）
  - `manuscript/latex_source/` = **12 个 tex 源**（编辑部要求必须上传源文件）
- **回复信**：`response/P3_RESPONSE_LETTER.md`（41000+ 字符，**33/33 条覆盖**，可直接贴 EM 表单）+ `.txt`
- **依据**：`evidence/`（三组补实验报告 + 意见解析/结构化 JSON + 篇幅量化）
- **本阶段四项撤回/降级**：Γ 优于 uniform（撤回）｜phase transition 尖锐（降级为 bracketed）｜
  architecture-dependent（撤回）｜30× 方差比（撤回）
- **不利结果如实报告**：AdaLoRA 对称调 lr 后 ΔE 优于我们全部方案（−1468/−757 vs +1478）
- ⚠️ **提交前必办**（见包内 README）：cover letter 说明篇幅 vs Guide 的 7 页；上传 LaTeX 源；
  **Authorship Confirmation 以 item type Cover Letter 上传**（未照办 = AUTOMATIC REJECTION）；EM 表单逐条回复
"""

ENT = """> **🏁 2026-10-13 20:00 —— P3 修订**全部交付**：33/33 条正式回复信 + 10 页投稿件 + 5 页补充材料 + 30 文件修订包**
>
> ### 一、操作者选定篇幅档 ①（10 页）后的完整交付
>
> | 交付件 | 内容 | 页数/规模 |
> |---|---|---|
> | **`docs/P3_RESPONSE_LETTER.md`** | **33 条正式逐条回复** | **41,457 字符** |
> | **`SUBMISSION/P3_PRL_revision/`** | 修订包 | **30 个文件** |
> | `manuscript/main.pdf` | **投稿件** | **10 页 / 0 错 / 0 未定义** |
> | `manuscript/supplementary.pdf` | 补充材料 | **5 页** |
> | `manuscript/main_full.pdf` | 完整版存档 | **13 页** |
> | `manuscript/latex_source/` | LaTeX 源 | 12 个 tex |
>
> ### 二、✅ 回复信核验（`tools/_p530`）
>
> - **覆盖**：**33/33 条**都有对应小节，**无多出、无遗漏** ✅
> - **关键数字**：18 项抽查**全部在信中**（3.09×、7,237,632、57 runs、AdaLoRA −1468、
>   反转 $p=0.0055$、matched-loss 0.5872/0.5826、47 分位、反序 $p=0.2057$、置换 $p=0.100$、
>   $\\eta^2=0.989$、11–28 seeds、分层 $+0.172$、配对 21/21、β 出处 `runs[90]`、median 0.072、
>   Qwen 逐块 −871.4、corner +3607、54-token 反转）
> - **禁止回归的旧主张**：`reduces uncertainty by` **0**｜`sharp phase transition` **0**｜
>   `equal parameter budgets`（作为事实）**0**｜`removes the catastrophic tail` **0**
> - **`CLIP-derived` 1 处** —— **是更正性否定**：*"$\\beta = 0.137$ **is not a CLIP-derived constant**,
>   and the earlier text said it was"* ✅
> - **自我一致**：变更表标 4 条撤回/降级，结尾句已改为 *"**Four** of our claims did not survive them"*
>
> ### 三、回复信的结构（11 项变更 + 33 条逐条）
>
> **开头汇总表**列 11 项变更，标出**四项撤回/降级**：
> ① $\\Gamma$-guided 优于 uniform（**撤回**）② phase transition 尖锐（**降级**）
> ③ architecture-dependent（**撤回**）④ $30\\times$ 方差比（**撤回**）
> **并如实报告不利结果**：**AdaLoRA 对称调 lr 后 $\\Delta E$ 优于我们全部方案**。
>
> **逐条回复的纪律**（贯穿全文）：**每个数字都能指名脚本与归档字段**；
> **引用的来源用逐 run 文件而不指向会被重写的聚合文件**；
> **未做的明说未做**（HALoRA/IGU-LoRA/ShapLoRA/NTK 未实现；VQA/captioning 未跑；Hessian 未测；
> 第三个 VLM 家族未测；系统 batch-size 敏感性未做）。
>
> ### 四、⚠️ 提交前必办（已写进包内 README）
>
> 1. **cover letter 主动说明篇幅与 Guide 的关系**（Guide 第 1 条要求双栏 ≤7 页；本稿 10 页，
>    **原投稿 11 页且进了外审**）**并请编辑裁定** —— 回复信开头已写明
> 2. **上传 LaTeX 源文件**（`manuscript/latex_source/`）—— 编辑部明确：只交 PDF 会延误
> 3. **Authorship Confirmation** 必须在 EM 的 `Attach Files` 以 **item type `Cover Letter`** 上传
>    —— **Guide 第 4 条：未照办会 AUTOMATIC REJECTION**
> 4. **33 条回复要在 EM 表单里逐条填写**（不能只交 PDF）
>
> ### 五、本阶段全貌（可复核）
>
> | 项 | 数值 | 核验工具 |
> |---|---|---|
> | 累计修订 | **44 处** | — |
> | 撤回/降级的主张 | **4 项** | 回复信汇总表 |
> | 矛盾扫描（"需处理"） | **0 处** | `tools/_p497_scan_contradictions.py` |
> | 断头命令 | **0 处**（曾修 58 处） | `tools/_p515_fix_severed_final.py` |
> | 字面 `\\n` | **0** | `tools/_p503_fix_literal_n_correct.py` |
> | 编译 | **10 页 / 0 错 / 0 未定义** | `pdflatex` + `bibtex` |
> | 摘要词数 | **243 ≤ 250** | — |
> | 回复信覆盖 | **33/33** | `tools/_p530_verify_response_letter.py` |
>
> ### 六、剩余（非本阶段）
>
> - **提交动作本身**由操作者在 EM 完成（我无法代操作）
> - **deadline 2026-11-02**
"""


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    a = ap.parse_args()
    if not a.apply:
        print("  （预演）")
        return 0
    # 文件地图
    fm = REPO / "文件地图.md"
    t = io.open(fm, encoding="utf-8").read()
    if "P3 修订交付" not in t:
        io.open(fm, "w", encoding="utf-8", newline="").write(t.rstrip() + "\n" + MAP_ADD)
        print("  ✅ 文件地图已追加「P3 修订交付」")
    else:
        print("  文件地图已有该条目")
    t2 = io.open(fm, encoding="utf-8").read()
    print(f"  文件地图行数 = {len(t2.splitlines())}")

    # HANDOFF
    hp = REPO / "HANDOFF.md"
    t = io.open(hp, encoding="utf-8").read()
    if "P3 修订**全部交付" in t:
        print("  HANDOFF 已记录")
        return 0
    i = t.find("# 项目交接文档")
    j = t.find("\n", i)
    io.open(hp, "w", encoding="utf-8", newline="").write(t[:j + 1] + "\n" + ENT + t[j + 1:])
    t3 = io.open(hp, encoding="utf-8").read()
    for k in ("P3 修订**全部交付", "41,457", "33/33", "AUTOMATIC REJECTION", "Four"):
        print(f"  {'✅' if k in t3 else '🔴'} {k}")
    print(f"  HANDOFF 行数 = {len(t3.splitlines())}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
