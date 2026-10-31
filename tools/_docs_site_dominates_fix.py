# -*- coding: utf-8 -*-
r"""落账：Paper A 侧解决"同一命题两处主张"（2026-10-07）。

操作者决定：**综述不改**；故只在 Paper A 侧处理。

**做法**：不引用在审综述（在审稿件引用麻烦），而是**引用综述所依据的 3 篇已发表文献**
（`zhang2023adalora` / `wang2024loraga` / `zanella2024cliplora`），
并新增一节 **"Placement Against Prior Work"** 把"位置 > 配置"定位为：

> 单骨干场景前人已有观察 → **我们跨 7 个骨干测到其边界**（是 patch size 决定的，非通用规律）→ **给出梯度流机制**

**书目取自综述**（作者本人已核对过的条目），**不从记忆编造**。

    python tools\_docs_site_dominates_fix.py [--apply]
"""
from __future__ import annotations

import io
import subprocess
import re
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]

ADD = r"""

---

## 七、`site dominates allocation` 的处理（2026-10-07，操作者决定"综述不改"）

### 问题

| | 综述（`-02402`，在审） | Paper A |
|---|---|---|
| 表述 | §3 首条 robust 结论：*"**site dominates allocation** … which site is trainable matters more than how a budget is divided within it"* | 摘要：*"**which part of the model is adapted matters more than how its adapters are configured**"* |
| 依据 | 文献归纳（引 3 篇） | 自己的 **204 个实验** |
| 互引 | ❌ 未引 Paper A | ❌ 未引综述 |

**同一命题、两处主张、互不引用** → 有被读成自我重复的风险。

### 决定与做法

**操作者：综述不改**（在审期间不动）。故**只在 Paper A 侧解决**。

**不引用在审综述**（在审稿件引用不当），改为**引用综述所依据的 3 篇已发表文献**：

| key | 书目（**取自综述，非记忆**） |
|---|---|
| `zhang2023adalora` | Zhang, Q., Chen, M., Bukharin, A., Karampatziakis, N. (2023). *AdaLoRA: Adaptive Budget Allocation for Parameter-Efficient Fine-Tuning.* ICLR |
| `wang2024loraga` | Wang, S., Yu, L., Li, J. (2024). *LoRA-GA: Low-Rank Adaptation with Gradient Approximation.* NeurIPS |
| `zanella2024cliplora` | Zanella, M., Ben Ayed, I. (2024). *Low-Rank Few-Shot Adaptation of Vision-Language Models.* CVPRW |

**新增一节 `Placement Against Prior Work`**（置于 Design Patterns 之前），要点：

1. **承认文献基础**：单骨干场景前人已论证"位置比预算分配更重要"；
2. **指出其边界**：那些报告**只在一个骨干、一个语料**上测量 → **未确立排序的普适性**；
3. **把贡献锐化**：我们把排序当作**待检验假设**，在 **7 个骨干**上用统一协议（优化器只见适配器矩阵）测量；
4. **给出机制**：测量显示排序**由 patch size 决定**，非视觉-语言适配的通用属性；理论节给出产生它的机制。

**→ 好处**：既**承认文献**（避免"不看文献"与自我重复），又**保住贡献**（直接测量 + 边界 + 机制）。

### 实测结果（编译后）

| 项 | 值 |
|---|---|
| bib 条目 | **44 → 47** |
| cites | **47 = bib 47**（缺失 0、未使用 0） |
| NC / Springer | **49 页 / 37 页**，0 错误，0 未定义引用 |
| 页越界（像素法） | **无** |
| 三条引用渲染 | ✅ 作者-年份格式（`Zhang et al. (2023); Wang et al. (2024); Zanella and Ben Ayed (2024)`） |
| 参考文献表 | ✅ 三条均在（CLIP-LoRA 那条标题首字母小写，属正常大小写转换） |

脚本：`tools/_pa_add_site_dominates_refs.py`（幂等、带断言）
"""


def main() -> int:
    apply = "--apply" in sys.argv
    if not apply:
        print("  （预演）")
        return 0

    # 交付件
    vp = REPO / "docs" / "PAPERA_VS_COMMENTARY.md"
    t = io.open(vp, encoding="utf-8").read()
    if "site dominates allocation` 的处理" not in t:
        io.open(vp, "w", encoding="utf-8", newline="").write(t.rstrip() + ADD)
        t2 = io.open(vp, encoding="utf-8").read()
        for k in ("Placement Against Prior Work", "44 → 47", "取自综述，非记忆", "patch size"):
            assert k in t2, f"断言失败：缺 {k}"
        print(f"  ✅ {vp.name} 已追加（{len(t2.splitlines())} 行）")

    # HANDOFF
    hp = REPO / "HANDOFF.md"
    h = io.open(hp, encoding="utf-8").read()
    ent = r"""> **✅ 2026-10-07 —— `site dominates allocation` 已在 **Paper A 侧**解决（操作者决定：综述不改）**
>
> **做法**：**不引用在审综述**（在审稿件引用不当），改为**引用综述所依据的 3 篇已发表文献**
> （AdaLoRA / LoRA-GA / CLIP-LoRA，**书目取自综述、非记忆**），并新增一节
> **`Placement Against Prior Work`**（置于 Design Patterns 前）：
>
> 1. **承认文献基础**——单骨干场景前人已论证"位置比预算分配更重要"；
> 2. **指出其边界**——那些报告**只在一个骨干、一个语料**上测量，**未确立排序的普适性**；
> 3. **把贡献锐化**——我们把它当**待检验假设**，在 **7 个骨干**上用统一协议测量；
> 4. **给出机制**——排序**由 patch size 决定**（非通用规律），理论节给出成因。
>
> **→ 既承认文献（避免"不看文献"与自我重复），又保住贡献（直接测量 + 边界 + 机制）。**
>
> **实测**：bib **44 → 47**｜**cites 47 = bib 47**（缺失 0、未使用 0）｜
> NC **49 页** / Springer **37 页**、0 错误、0 未定义引用｜**无页越界**｜
> 三条引用按作者-年份渲染（`Zhang et al. (2023); Wang et al. (2024); Zanella and Ben Ayed (2024)`）。
> 脚本：`tools/_pa_add_site_dominates_refs.py`（幂等、带断言）。详见 `docs/PAPERA_VS_COMMENTARY.md` §七。
"""
    if "已在 **Paper A 侧**解决" not in h:
        anchor = "> **⚖️ 2026-10-07 —— Paper A 与 PRL 综述的区别"
        i = h.find(anchor)
        assert i > 0, "未找到 HANDOFF 锚点"
        io.open(hp, "w", encoding="utf-8", newline="").write(h[:i] + ent + "\n" + h[i:])
        h2 = io.open(hp, encoding="utf-8").read()
        for k in ("Placement Against Prior Work", "44 → 47", "取自综述"):
            assert k in h2, f"HANDOFF 断言失败：缺 {k}"
        print(f"  ✅ HANDOFF 已追加（{len(h2.splitlines())} 行）")

    # 文件地图：更新待办 0
    fp = REPO / "文件地图.md"
    fm = io.open(fp, encoding="utf-8").read()
    old = "   另：综述（PRL）、P1（PR）、Paper A（CVIU/ESWA）**同属 Elsevier**，\n"
    if old in fm:
        new = (old + "   **✅ 已于 2026-10-07 处理（操作者决定综述不改）**：Paper A 新增 "
               "**`Placement Against Prior Work`** 节 + 引用 AdaLoRA/LoRA-GA/CLIP-LoRA 三条已发表文献，\n"
               "   把命题定位为「文献已有此说（单骨干）→ 我们跨 7 骨干测到其由 patch size 决定 → 给出机制」。\n"
               "   bib 44→47、cites 47=bib 47、编译 0 错误。脚本 `tools/_pa_add_site_dominates_refs.py`。\n")
        io.open(fp, "w", encoding="utf-8", newline="").write(fm.replace(old, new, 1))
        print("  ✅ 文件地图.md 待办 0 已更新")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
