# -*- coding: utf-8 -*-
r"""落实操作者的**唯一原则**：所有数据必须可复现、有来源（2026-10-07）。

## 原则（最高优先级）

> **"所有数据必须要可复现有来源"**

## 本轮做了什么

1. **删除假门禁**：`tools/_reproducibility_gate.py` 用"在归档里模糊匹配数字"判定可复现——
   归档有 **122,161 个数值**，任何数字都能在 0.5% 容差内随机命中 → **145/145 通过是假象**。
   **改为**：`tools/_claim_ledger.py` —— **人工指名出处**（脚本 + JSON 字段），逐条断言。
2. **按原则删掉无来源数据**：`supplement.tex` 的 COCO 表 **15 行 → 3 行**
   （归档只有 3 配置 × 3 seed；其余 12 行在任何归档中都不存在）。
3. **把原则写进 `AGENTS.md`**（项目最高约束文件）与交接文档。

## 台账覆盖（24 条，全通过）

| 类别 | 条数 |
|---|---|
| 严格冻结三臂 CGΔ | 3 |
| ODE R²（LoRA/Flickr/COCO/Adapter/full-FT） | 5 |
| 逐秩 R² | 2 |
| COCO 三配置 R² | 3 |
| 梯度流恒等式（cos、中位误差） | 2 |
| 编码器侧零梯度（硬校验） | 3 |
| OpenCLIP / CLIP BitFit | 3 |
| monitor DG（本轮新实验） | 2 |
| LOCO 配置数 | 1 |

    python tools\_docs_reproducibility_principle.py [--apply]
"""
from __future__ import annotations

import io
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]

AGENTS_ADD = """
## 🔴🔴 唯一原则（用户明确要求，最高优先级）

> **"所有数据必须要可复现有来源。"** —— 2026-10-07 操作者原话

**含义（无例外）**：

1. 稿件/报告里的**每一个数字**，都必须能**指名**：(a) 产出它的**脚本**，(b) 承载它的**归档文件与字段**；
2. **"看起来对"不等于"有来源"**：不得用近似、推断、他人转述、或"应该是这个量级"来填数；
3. **无法给出来源的数字，一律删除**（而非保留待查）——因为读者无法区分"暂时没找到"与"编造"；
4. **第三方数字**（如审稿周期）**必须标注来源**（官网/社区/第三方），不得与自有实测混列；
5. **自动模糊匹配不算验证**：归档规模大时任何数字都能随机命中（本项目已有一次假门禁的教训：
   `tools/_reproducibility_gate.py` 以 0.5% 容差在 122,161 个归档数值里搜 → 145/145 通过，**纯属假象**）。
   **正确做法**：`tools/_claim_ledger.py` —— **人工指名出处 + 逐条断言**。

**门禁**：`python tools\\_claim_ledger.py --apply`（24 条关键主张，全通过才算过）。
"""


def main() -> int:
    apply = "--apply" in sys.argv
    if not apply:
        print("  （预演）")
        return 0

    # ① 假门禁：就地标注作废（不删文件，保留教训）
    gp = REPO / "tools" / "_reproducibility_gate.py"
    if gp.exists():
        t = io.open(gp, encoding="utf-8").read()
        if "本工具已作废" not in t:
            t = t.replace('r"""**可复现门禁**：',
                          'r"""**⚠️ 本工具已作废（2026-10-07）——它给出的是假门禁。**\n\n'
                          '实测：归档有 122,161 个数值，任何数字都能在 0.5% 容差内随机命中 →\n'
                          '**145/145"通过"纯属假象**。正确做法见 `tools/_claim_ledger.py`（人工指名出处 + 逐条断言）。\n\n'
                          'r"""**可复现门禁**：', 1)
            io.open(gp, "w", encoding="utf-8", newline="").write(t)
            print("  ✅ _reproducibility_gate.py 已就地标注作废（保留教训）")

    # ② 原则写入 AGENTS.md
    ap = REPO / "AGENTS.md"
    a = io.open(ap, encoding="utf-8").read()
    if "唯一原则（用户明确要求，最高优先级）" not in a:
        i = a.find("## 🔴 阶段收尾规则")
        assert i > 0, "未找到 AGENTS.md 插入锚点"
        io.open(ap, "w", encoding="utf-8", newline="").write(a[:i] + AGENTS_ADD.strip() + "\n\n" + a[i:])
        a2 = io.open(ap, encoding="utf-8").read()
        for k in ("所有数据必须要可复现有来源", "_claim_ledger.py", "无法给出来源的数字，一律删除"):
            assert k in a2, f"AGENTS 断言失败：缺 {k}"
        print(f"  ✅ AGENTS.md 已写入唯一原则（{len(a2.splitlines())} 行）")

    # ③ HANDOFF
    hp = REPO / "HANDOFF.md"
    h = io.open(hp, encoding="utf-8").read()
    if "唯一原则：所有数据必须可复现" not in h:
        ent = """> **🔴🔴 2026-10-07 —— 唯一原则确立：**"所有数据必须要可复现有来源"**（操作者原话）**
>
> ### 本轮据此做的三件事
>
> | # | 动作 | 依据 |
> |---|---|---|
> | 1 | **删除假门禁**：`_reproducibility_gate.py` 以 0.5% 容差在 **122,161 个归档数值**里搜 → **145/145 "通过"纯属假象** | 我否掉自己的工具 |
> | 2 | **按原则删无来源数据**：`supplement.tex` 的 **COCO 表 15 行 → 3 行**（归档只有 3 配置 × 3 seed；其余 12 行在任何归档中都不存在） | 删而非留 |
> | 3 | **建立人工台账**：`tools/_claim_ledger.py` —— **24 条关键主张**，每条**指名脚本 + JSON 字段**，**逐条断言** → **24/24 通过** | 可复核 |
>
> ### 台账覆盖（`outputs/analysis/claim_ledger.json`）
>
> 严格冻结三臂 CGΔ（3）｜ODE R²（5）｜逐秩 R²（2）｜COCO 三配置（3）｜
> 梯度流恒等式 cos/中位误差（2）｜编码器侧零梯度硬校验（3）｜OpenCLIP 与 CLIP BitFit（3）｜
> monitor DG 新实验（2）｜LOCO 配置数（1）
>
> ### 原则已写入 `AGENTS.md`（最高优先级）
>
> 五条含义：① 每个数字**指名脚本 + 归档字段**；② **"看起来对" ≠ "有来源"**；
> ③ **无来源的数字一律删除**（而非保留待查）；④ 第三方数字**必须标注来源**；
> ⑤ **自动模糊匹配不算验证**（附本次假门禁教训）。
>
> **门禁命令**：`python tools\\_claim_ledger.py --apply`（全通过才算过）。
"""
        i = h.find("# 项目交接文档")
        j = h.find("\n", i)
        io.open(hp, "w", encoding="utf-8", newline="").write(h[:j + 1] + "\n" + ent + h[j + 1:])
        h2 = io.open(hp, encoding="utf-8").read()
        for k in ("所有数据必须要可复现有来源", "145/145", "COCO 表 15 行 → 3 行", "_claim_ledger.py"):
            assert k in h2, f"HANDOFF 断言失败：缺 {k}"
        print(f"  ✅ HANDOFF 已追加（{len(h2.splitlines())} 行）")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
