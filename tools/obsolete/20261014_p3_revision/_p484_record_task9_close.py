# -*- coding: utf-8 -*-
r"""落账：task-9 收口 + "3/10"表述收紧 + 一类错误的归族（2026-10-13 12:40）。

    python tools\_p484_record_task9_close.py [--apply]
"""
from __future__ import annotations

import argparse
import io
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]

ENT = """> **🏁 2026-10-13 12:40 —— task-9 收口；"3/10 更优"改为"2 明显 + 1 噪声内"；并归纳出**一类**反复出现的错误**
>
> ### 一、成员更正 `20–43 → 11–28`（6 处落点），并**保留更替记录**
>
> | 量 | 旧（3-seed） | **现行（6-seed）** |
> |---|---|---|
> | Δ（`uniform` − `exp`） | 4,172.4 | **3,570.1** |
> | σ 池组间 sd | — | **3,010.1** → n ≈ **11.2** |
> | σ 池组内 sd 中位数 | — | **3,196.6** → n ≈ **12.6** |
> | σ 混合池 sd | 4,919.1 / 6,937.4 | **4,771.2** → n ≈ **28.0** |
> | **每方案所需 n** | ~~22–44~~ | **11–28** |
>
> **落点**：§4.3h 出处表（**出处同时改指逐 run glob**，不再指向会被重写的聚合文件）、结果行、
> R3.17 回复措辞、§4.3e 的判别力边界与两层证据表、§4.5 第 3 条。
> **并在报告里保留一条「数值更替记录」**（旧值标注作废 + 原因）—— 符合"过期结论要标注过期并给出新结论，不要静默覆盖"。**有意保留，我认可。**
>
> **⚠️ 它自查出根因**：终报是在**滚动总结里抄了早期版本**，而非从归档重算。
> **⇒ 这正是"转录"类缺陷（本阶段已多次）：从归档到文字之间有一次人工搬运。**
>
> ### 二、⭐ 它收紧了一处**我先前的表述过强**（我已在稿中改准）
>
> 我先前写 *"three of the ten random allocations averaging lower"*。**精确事实**：
>
> | 随机方案 | 均值 | 与 Γ-guided（+1477.5）之差 |
> |---|---|---|
> | `random_03` | **−1450.3** | **−2927.8** |
> | `random_05` | **−222.2** | **−1699.6** |
> | `random_11` | **+1741.3** | **+263.9** |
>
> **⇒ 按"均值低于 Γ-guided"算是 3 个；但按"差幅超过 Γ-guided 的组内 sd（1563）"算，
> 明显更优只有 2 个；`random_11` 的 +264 落在噪声内。**
> （另两个落噪声内的是 `random_07` +1345、`random_08` +1032。）
>
> **⇒ 稿中已改为**（`tools/_p483`，P3 编译 **14 页 / 0 错 / 0 未定义**）：
> *"Three of the ten allocations have a lower mean than the $\\Gamma$-guided arm, but only two of them
> by more than that arm's own seed-to-seed spread ($-2928$ and $-1700$); the third is lower by $264$,
> which is inside the noise, and **we count it as indistinguishable rather than as a win**."*
>
> ### 三、⭐ 归纳：本项目反复出现的一类错误 —— **把"名义上"当成"实际上"**
>
> | # | 名义 | 实际 | 谁犯 |
> |---|---|---|---|
> | ① | "n = 32 个评估样本" | **有效 n = seed 数 = 3**（同图同提示 ⇒ 逐位相同） | 成员自查 |
> | ② | "聚合产物是来源" | 它**每次被重写** ⇒ 字段路径**静默失效** | 成员自查 |
> | ③ | "14 个随机抽样" | **4 个与规则解重合** ⇒ 独立样本 10 个 | **我扩展的** |
> | ④ | "3/10 个随机方案更优" | **2 明显 + 1 噪声内** | **我**（成员收紧） |
> | ⑤ | "同秩/同预算比较" | 早期版本**跨 16× 容量**；latte"同分配内 seed 极差 14,331 > 方案间差 3,570" | 成员自查 |
>
> **共性**：**结构/标签给出的"名义单位"，不等于统计上有效的单位。**
> **⇒ 防御：凡涉及"个数/样本量/比较"，先问"这些单位在统计上等价吗？"**
> **（与本阶段另两条规则互补：全称否定须穷举；对照须先验证自身。）**
>
> ### 四、task-9 收口（成员与我一致）
>
> ```
> 无残留 20–43          OK      现行区间 11–28 已统一   OK
> 更替记录保留          OK      §4.2/§4.3 标"被取代"    OK
> 危害分级 错标>覆盖>重写  OK    错标检查器已引用        OK
> AdaLoRA lr 反转已记录  OK    matched-loss 反证已记录  OK
> 定位声明已写入        OK
> 分配数学单测        0 项失败
> 配置错标检查        7 个汇总归档 / 0 错标
> paper3/**          未改动        GPU 已交还（299 MiB）
> ```
>
> **报告 `docs/P3_EXPERIMENTS.md`：1219 行 / 79.2 KB。**
>
> ### 五、状态
>
> - **三个实验组全部收口**（task-9 / task-10 / task-11）
> - **P3 稿件**：**14 页** / 0 错 / 0 未定义；**累计修 26 处**
> - **PRL 硬约束**：**双栏 ≤7 页**（官方 Mandatory Submission Requirements）⇒ **待压缩 + 新建 Supplementary**
> - **剩余**：① 页数压缩 ② **33 条回复信正式文本** ③ 修订包重新生成
"""


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    a = ap.parse_args()
    if not a.apply:
        print("  （预演）")
        return 0
    hp = REPO / "HANDOFF.md"
    t = io.open(hp, encoding="utf-8").read()
    if "把\"名义上\"当成\"实际上\"" in t or "名义上" in t and "3/10 更优" in t:
        print("  已记录")
        return 0
    i = t.find("# 项目交接文档")
    j = t.find("\n", i)
    io.open(hp, "w", encoding="utf-8", newline="").write(t[:j + 1] + "\n" + ENT + t[j + 1:])
    t2 = io.open(hp, encoding="utf-8").read()
    for k in ("3/10 更优", "−2927.8", "把\"名义上\"当成\"实际上\"", "有效 n = seed 数", "累计修 26 处"):
        print(f"  {'✅' if k in t2 else '🔴'} {k}")
    print(f"  HANDOFF 行数 = {len(t2.splitlines())}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
