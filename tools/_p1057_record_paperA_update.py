# -*- coding: utf-8 -*-
r"""Record the Paper A update: the LLaVA section, the page counts, and the archive correction.

    python tools/_p1057_record_paperA_update.py [--apply]
"""
from __future__ import annotations

import argparse
import io
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
HANDOFF = REPO / "HANDOFF.md"
MAP = REPO / "文件地图.md"
MARK = "Paper A 更新：LLaVA 负结果"

ENT = """> **📄 2026-10-16 20:10 —— Paper A（`paper合/`）更新：新增补充 F 节（LLaVA-7B bf16 **负结果**）+ 归档元数据纠错；两版重编**
>
> 操作者指令：**「Paper合先更新」**，并在选项中选定 **1（把 LLaVA 结果写成跨模型局限/负结果）**。
>
> ### 一、⚠️ 先纠正我自己的一个错判（重要）
>
> 我先前对操作者说「今天的 LLaVA 结果与论文核心论点存在**张力**」——**这个说法不成立**，核对口径后：
>
> | 项 | Paper A（`src/gap_metrics.py`）| 我的 LLaVA 流水线 |
> |---|---|---|
> | CG | `‖μ_I−μ_T‖`（L2 归一化后）| 同 ✅ |
> | **DG** | **方差式 W₂：`sqrt(CG² + ‖σ_I−σ_T‖²)`** | **均值成对距离 − 两模态内距离** ❌ |
> | 文本侧 | 文本**编码器**输出 | LLM token 嵌入（**未排除图像 token**）❌ |
> | 量级 | DG\* 0.64–2.18 | DG\* **0.261** |
>
> ⇒ **两者不是同一可比量**，"text-only 零变化"很可能是**度量口径问题**，不是模型行为差异。
> **故按负结果+口径说明写入，而非作为反证。**
>
> ### 二、✅ 补充材料新增 **F 节**（`sections/supplement.tex`，+60 行）
>
> | 内容 | 值（来自 `outputs/llava_bf16_sites_cloud/`，12 条记录）|
> |---|---|
> | 协议 | LLaVA-1.5-7B、1500 训练/500 评测、3 epochs、batch 2、rank 8、**bf16**、3 seeds/arm |
> | Frozen | **+0.297% ± 0.000%** |
> | **Text-only** | **+0.297% ± 0.000%**（**与 frozen 逐位相同**：0.2619372457265854，六个 run 一致）|
> | Vision-only | **+13.333% ± 4.737%**（seed 间 +7.53 / +13.33 / +19.14）|
> | Both | **+6.068% ± 6.547%** |
> | 训练损失 | 1.55 → 0.39（证明适配器非惰性）|
> | **分辨率限制（诚实写明）** | frozen 不训练也从 **0.261161 → 0.261937**，即本流水线的可解释尺度约 **0.0008** ⇒ 无法分辨该量级的效应 |
> | **为何不算反证** | DG 定义不同、文本侧取法不同、起始量级差 2.5–8 倍 ⇒ 一个量上的 null 不等于另一个量上的 null |
>
> 正文 `sections/discussion.tex` 局限段**已加一句指向 F 节**（避免新节孤立）；`references.bib` **补入 `liu2023llava`**（原缺，否则未定义引用）。
>
> ### 三、✅ 编译结果（两版，均干净）
>
> | 版本 | 页数 | LaTeX 错误 | 未定义 ref/cite | Overfull |
> |---|---|---|---|---|
> | **NC**（`main_nc.pdf`）| **67** | **0** | **0** | 0 |
> | **Springer**（`main_springer.pdf`）| **49** | **0** | **0** | 0 |
>
> bib 审计：**48 个条目、48 个被引用键、0 缺失、0 未引用**。新节在两份 PDF 中均已核实（`pdftotext` 检出标题与表格数值）。
>
> ### 四、⚠️ 修掉一个**会让引用者写错精度**的归档缺陷
>
> `outputs/llava_bf16_sites_cloud/llava_sites.json` 里原本写着 **`"quantisation": "4-bit nf4"`** 与
> "4-bit is required to fit the 8.6 GB device"——**而这批 12 条记录实际是 bf16 跑的**。原因是脚本里这两个字段是
> **硬编码字符串**，加 `--precision bf16` 时没同步。
> **已修**：`tools/_p1052`（脚本改为按 `--precision` 生成）+ `tools/_p1053`（**就地修正归档**，保留原值于
> `_label_correction`，并逐一验证其余 3 个未触碰字段仍相等）⇒ 记录 `docs/archive_metadata_fix_2026-10-16.md`。
>
> ### 五、✅ 账本门禁：**96/96 通过**（原 80 + 新增 16 条 LLaVA）
>
> 新条目**避免自比自**（项目曾有"假门禁"教训）：**稿件值为字面量**，**实测值从逐条记录独立重算**，
> 并额外**与汇总文件 `llava_sites.json:runs[]` 逐位交叉校验 12/12**；另含结构性断言（text-only 与 frozen
> 末态逐位相同 = 3/3）与分塔参数（19,988,480 / 3,645,440 / 23,633,920）。
>
> ### 六、⏭️ 待办
>
> `paper合/NC_submission/` 里的投稿包（`Manuscript.pdf`、`latex_source.zip`）**尚未同步**这两处改动——
> 需操作者确认是否现在就刷新（刷新会改变投稿包内容）。
>
> **工具**：`_p1051`（账本）｜`_p1052`/`_p1053`（精度标签纠错）｜`_p1054`（账本 source 参数）｜`_p1055`（F 节）｜`_p1056`（引用+正文指向）｜`_p1057`（本条）。
>

"""


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    a = ap.parse_args()
    if not a.apply:
        print("  (dry run)")
        return 0
    hp = io.open(HANDOFF, encoding="utf-8").read()
    if MARK not in hp:
        i = hp.find("# 项目交接文档")
        j = hp.find("\n", i)
        hp = hp[: j + 1] + "\n" + ENT + hp[j + 1:]
        io.open(HANDOFF, "w", encoding="utf-8", newline="").write(hp)
        print("  handoff entry added")
    mp = io.open(REPO / "文件地图.md", encoding="utf-8").read()
    row = ("44. 📄 **Paper A 更新：补充 F 节（LLaVA-7B bf16 负结果）+ 归档纠错（2026-10-16 20:10）** —— "
           "新增 `sections/supplement.tex` **F 节**：LLaVA-1.5-7B、1500/500、3 epochs、rank 8、bf16、3 seeds；"
           "frozen **+0.297%±0.000%**、**text-only 与 frozen 逐位相同**（0.2619372457265854）、vision-only **+13.333%±4.737%**、"
           "both **+6.068%±6.547%**；**诚实写明**：本流水线 DG 定义（均值成对距离−模态内距离）与论文方差式 W₂ **不同**、"
           "文本侧取 LLM token 嵌入，量级差 2.5–8× ⇒ **不作反证**；且 frozen 不训练也移动 0.0008 ⇒ 为该量级的**分辨率上限**。"
           "正文局限段已指向 F 节；`references.bib` 补 `liu2023llava`。**编译**：**NC 67 页 / Springer 49 页，均 0 错误·0 未定义·0 Overfull**，"
           "bib 48/48。⚠️ **归档纠错**：`llava_sites.json` 原写 `4-bit nf4` 而实为 **bf16** ⇒ 已修脚本与归档（`_p1052`/`_p1053`）。"
           "**账本 96/96**（新增 16 条，含与汇总文件逐位交叉校验）。`NC_submission/` 投稿包**尚未同步**。详见 `HANDOFF.md` 顶部 20:10 条目。\n")
    anchor = "43. 🧹 **磁盘清理（2026-10-16 19:20）**"
    idx = mp.find(anchor)
    if idx >= 0:
        end = mp.find("\n", idx)
        mp = mp[: end + 1] + row + mp[end + 1:]
        io.open(REPO / "文件地图.md", "w", encoding="utf-8", newline="").write(mp)
        print("  map item added")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
