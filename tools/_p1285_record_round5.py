# -*- coding: utf-8 -*-
r"""Record the round that closed the compliance gaps: A1 claim ledger, scoped data statement, margin proposition,
two more backbones, DTD/Food-101 intervals, and the prepared (but not pushed) public-mirror staging.

    python tools/_p1285_record_round5.py [--apply]
"""
from __future__ import annotations

import argparse
import io
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
HANDOFF = REPO / "HANDOFF.md"
MAP = REPO / "文件地图.md"
WHICH = REPO / "哪篇是哪篇.md"
NOVDOC = REPO / "docs" / "A1_NOVELTY_STEP1_2026-10-18.md"

NOVSEC = """

---

## 第 10 步（2026-10-18 19:35）：合规收尾 + 最后两项加料，A1 **53 页**

### 1. A1 claim ledger（**97/97 通过**）——顺手查出两处真错

新建 `tools/_claim_ledger_a1.py`：把 A1 引用的 97 个数字逐条绑定到「脚本 + 归档字段」并断言。首轮 85/87，暴露出两处**真实错误**：

| 错误 | 稿件原值 | 归档实测 | 处理 |
|---|---|---|---|
| DTD 冻结 gap | `1.019` | 1.01845… ⇒ 应为 **1.018**（四舍五入错） | 稿件改 3 处 |
| 逐轮 τ 与 top-1 的平均 Pearson | `0.90` | 0.9331 ⇒ 应为 **0.93** | 摘要 / 引言 / §epoch_sweep 各改 |

修正后 **97/97 全通过**；归档 `outputs/analysis/claim_ledger_a1.json`。

### 2. 数据可用性声明收窄（原先与归档不符）

原句声称"所有逐次记录与脚本均在公开仓库 + Zenodo 快照"——但快照（2026-10-13）**早于本轮全部新实验**。
现改为：快照覆盖**当时已有**的逐次记录与脚本；本轮新增分析（prompt 控制、更多基准与 retrieval 复现、监控评估）
在公开仓库中，**接收后将另立版本化快照**。标题页声明同步加注。

### 3. Proposition 5（正例判据）

给出"**何时可以相信一阶矩统计量**"：记 $\varepsilon_i=\max_c|\Delta s_i(c)-\bar\Delta_i|$，若某图 top-1 改变，则其 margin
$m_i\le2\varepsilon_i$。故一阶矩摘要只有在其能界定 $\varepsilon_i$（即干预对类别分数是**类中性**的）时才可用来认证精度。
这把批评变成可操作判据，并与 Prop 1（类中性平移）对接。

### 4. 另两个骨干 + DTD/Food-101 区间

- 匹配 gap 现覆盖 **5 个骨干**：CLIP B/32 **32.7**、**B/16 35.5**、**L/14 39.6** 点（$|\\Delta\\mathrm{CG}|\\le0.03$），
  OpenCLIP/SigLIP 各 **27.1**（需更大 gap 差 0.066/0.197）；控制表同步改为五骨干。
- DTD / Food-101 补 **95% bootstrap 区间**：spread 10.1 [8.1, 12.0] 与 12.1 [10.7, 13.3]；收缩增益 +17.8 [15.9, 19.7] 与
  +18.2 [17.1, 19.4]；附录表补两行，iNat 行由带符号区间改为**绝对值区间**。

### 5. 公开镜像：**已准备、未推送**（按操作者要求等投稿确认）

`tools/_p1284_prepare_public_mirror.py` 把 11 个新归档 + 11 个脚本复制进 `publish_clean/` 并打印复核命令；
**脚本自身不执行 commit/push**。投稿确认后运行它，再手动 commit + `push ssh-origin main`。

**A1 终态**：**53 页**（正文 ~46 + 附录）、0/0/0；PAA 包 6 文件；审计 `a1_paa` **READY grade A：pass=61 fail=0 warn=0**；
三个台账（A1 **97/97**、主 **96/96**、Paper A **76/76**）全通过。
"""

ENT = """> **🧾 2026-10-18 19:35 —— A1 合规收尾：新建 claim ledger（97/97，查出 2 处真错）、数据声明收窄、Proposition 5、五骨干、DTD/Food-101 区间**
>
> 1. **`tools/_claim_ledger_a1.py`**：97 条数字逐条绑定归档。首轮抓出两处真错并修：
>    **DTD 冻结 gap 1.019 → 1.018**（四舍五入错）、**逐轮 τ-top1 平均 Pearson 0.90 → 0.93**（摘要/引言/§epoch_sweep）。
> 2. **数据可用性声明收窄**：原句与归档不符（Zenodo 快照 10-13 早于本轮新实验）。改为"快照覆盖当时已有记录；
>    本轮新增分析在公开仓库，接收后另立版本化快照"；标题页同步。
> 3. **Proposition 5（margin 判据）**：top-1 改变 ⇒ margin $\\le2\\varepsilon_i$ ⇒ 一阶矩只有界定类中性程度才可信。
> 4. **第五个骨干 + 区间**：匹配 gap 五骨干（B/32 32.7、B/16 **35.5**、L/14 **39.6**；OpenCLIP/SigLIP 27.1@0.066/0.197）；
>    DTD/Food-101 补 95% 区间（10.1 [8.1,12.0]、12.1 [10.7,13.3]）。
> 5. **公开镜像已准备未推送**：`_p1284` 复制 11 归档 + 11 脚本到 `publish_clean/` 并打印复核命令，自身不 commit/push；
>    按操作者要求**等投稿确认后再推**。
>
> **A1 终态**：**53 页**、0/0/0；审计 **READY/A pass=61 fail=0 warn=0**；三台账 97/97、96/96、76/76 全过。
>

"""


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    a = ap.parse_args()
    if not a.apply:
        print("  (dry run)")
        return 0
    n = io.open(NOVDOC, encoding="utf-8").read()
    if "第 10 步" not in n:
        io.open(NOVDOC, "w", encoding="utf-8", newline="").write(n.rstrip("\n") + NOVSEC)
        print("  novelty doc appended")
    h = io.open(HANDOFF, encoding="utf-8").read()
    if "A1 合规收尾" not in h:
        i = h.find("# 项目交接文档")
        j = h.find("\n", i)
        io.open(HANDOFF, "w", encoding="utf-8", newline="").write(h[: j + 1] + "\n" + ENT.replace("\\n", "\n") + h[j + 1:])
        print("  handoff added")
    w = io.open(WHICH, encoding="utf-8").read()
    old = "5 基准复现 + 附录化** | 52 + 1 title page |"
    new = "5 基准复现 + 附录化 + Prop 5 + 五骨干匹配 gap** | 53 + 1 title page |"
    print(f"  which row: {w.count(old)}")
    if w.count(old) == 1:
        io.open(WHICH, "w", encoding="utf-8", newline="").write(w.replace(old, new, 1))
    m = io.open(MAP, encoding="utf-8").read()
    row = ("87. 🧾 **A1 合规收尾（2026-10-18 19:35）** —— 新建 **A1 claim ledger（97/97）**，查出并修正两处真错"
           "（DTD gap 1.019→**1.018**、平均 Pearson 0.90→**0.93**）；**数据可用性声明收窄**（快照 10-13 早于新实验，"
           "新增分析在公开仓库、接收后另立快照）；**Proposition 5（margin 判据）**；匹配 gap 扩到 **五骨干**"
           "（B/32 32.7、B/16 35.5、L/14 39.6、OpenCLIP/SigLIP 27.1）；DTD/Food-101 补 95% 区间。A1 **53 页**、"
           "审计 READY/A；**公开镜像已准备未推送**（`_p1284`）。\n")
    if "A1 合规收尾" not in m:
        anchor = "86. 🎨 **A1 剩余提升 C/D/E/F"
        idx = m.find(anchor)
        if idx >= 0:
            end = m.find("\n", idx)
            io.open(MAP, "w", encoding="utf-8", newline="").write(m[: end + 1] + row + m[end + 1:])
            print("  map row added")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
