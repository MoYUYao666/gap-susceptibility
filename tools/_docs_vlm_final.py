# -*- coding: utf-8 -*-
r"""收尾：更新风险清单 C3、页数、并落账（2026-10-10）。

    python tools\_docs_vlm_final.py [--apply]
"""
from __future__ import annotations

import argparse
import io
import re
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]

ENT = """> **✅ 2026-10-10 —— 处置完成（操作者选 A）：解码器 VLM 那节改为**3 seed bf16 如实报告**；`paper合` 门禁 83/83**
>
> ### 一、改了什么
>
> | 文件 | 改动 |
> |---|---|
> | `paper合/sections/supplement.tex` | **协议段**：batch 2、**bf16**、**3 seed**；删掉"bf16 不可行"的不准确表述<br>**`tab:vlm`**：换为 $DG^*$ 相对变化 $+85.2\\pm11.2$ / $+66.8\\pm6.5$ / $+12.4\\pm4.7\\%$，加 **Seed range** 与 **CG span** 两列<br>**新增一段**：4-bit 不可复现（同 seed $0.304$/$0.407$）、bf16 逐位可复现、种子波动为何使排序翻转<br>**收尾段**：去掉"best site 不迁移"的断言（$0.23$ sd 不显著） |
> | `paper合/sections/discussion.tex` | **Second limitation** 改写：`vision_only` 仍最弱（$4.9$ sd），但 **`both` 与 `text_only` 不可分辨**（$0.23$ sd）；原 4-bit 单 seed 数字是种子运气；4-bit 不可复现 |
>
> **备份**：`supplement.tex.bak_vlm`｜`discussion.tex.bak_vlm`
>
> ### 二、编译与门禁
>
> | 稿 | 页数 | 错误 | 未定义 | Overfull |
> |---|---|---|---|---|
> | Springer | **40** | 0 | 0 | 0 |
> | **NC** | **56**（原 55） | 0 | 0 | 0 |
>
> **门禁：83/83 通过**（新增 17 条 VLM 主张）｜退出码 0
> **残留检查**（`tools/_p160_check_stale_vlm.py`）：旧数字/旧主张 **0 命中** ✅
>
> ### 三、C3 风险项的**新状态**
>
> | 项 | 旧 | 新 |
> |---|---|---|
> | 模型数 | 1 | 1（未变） |
> | **seed 数** | **1** | **3** ✅ |
> | 精度 | 4-bit（**不可复现**） | **bf16（逐位可复现）** ✅ |
> | 结论 | "both 最好" | **两强臂不可分辨；只有 `vision_only` 最弱** |
> | 规模 | 400 样本 / 3 epoch | 同（未变，已如实标注） |
>
> ### 四、这一轮暴露的方法学问题（**已写进 limitation**）
>
> **4-bit 量化（bitsandbytes NF4）不可逐位复现**：同 seed 同配置两次，`cg_span` = $0.304$ vs $0.407$；
> **bf16 逐位相同**（$0.110\\,064$ 两次）。**旧 `tab:vlm` 的 4-bit 单 seed 数字无法被任何人重放。**
>
> **且论文其余部分仍有 4-bit**（视觉侧各臂）→ limitation 已写明
> *"whether four-bit quantisation materially changes the ordering on the dual-encoder backbones … is not
> something we have established"*。
"""


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    a = ap.parse_args()

    # ① 风险清单 C3
    f = REPO / "docs" / "PAPERA_REVIEWER_RISKS.md"
    if f.exists():
        t = io.open(f, encoding="utf-8", errors="replace").read()
        new_c3 = ("| **C3** | **解码器 VLM 为单模型、单 seed、规模小** | "
                  "**2026-10-10 已补到 3 seed（bf16，逐位可复现）**；"
                  "结论修正为「`vision_only` 仍最弱（4.9 sd），两强臂不可分辨（0.23 sd）」；"
                  "**仍为单模型、400 样本/3 epoch** |")
        m = re.search(r"\|\s*\*\*C3\*\*\s*\|[^\n]*", t)
        if m:
            t2 = t[:m.start()] + new_c3 + t[m.end():]
            if a.apply:
                io.open(f, "w", encoding="utf-8", newline="").write(t2)
                print("  ✅ 风险清单 C3 已更新")
        else:
            print("  ⚠️ 未找到 C3 行")

    # ② 文件地图页数
    fm = REPO / "文件地图.md"
    if fm.exists():
        t = io.open(fm, encoding="utf-8", errors="replace").read()
        old = ("**Springer 版 40 页｜NC 版 55 页**")
        if old in t:
            t2 = t.replace(old, "**Springer 版 40 页｜NC 版 56 页**（2026-10-10 晚更新）", 1)
            if a.apply:
                io.open(fm, "w", encoding="utf-8", newline="").write(t2)
                print("  ✅ 文件地图页数已更新（55 → 56）")
        elif "NC 版 56 页" in t:
            print("  文件地图已是最新")
        else:
            print("  ⚠️ 未找到页数锚点")

    # ③ HANDOFF
    hp = REPO / "HANDOFF.md"
    t = io.open(hp, encoding="utf-8").read()
    if "处置完成（操作者选 A）" in t:
        print("  HANDOFF 已记录，跳过")
        return 0
    if not a.apply:
        print("  （预演）")
        return 0
    i = t.find("# 项目交接文档")
    j = t.find("\n", i)
    io.open(hp, "w", encoding="utf-8", newline="").write(t[:j + 1] + "\n" + ENT + t[j + 1:])
    t2 = io.open(hp, encoding="utf-8").read()
    for k in ("处置完成（操作者选 A）", "83/83", "**56**", "不可逐位复现", "4.9 sd", "0.23 sd"):
        assert k in t2, f"断言失败：缺 {k}"
    print(f"  ✅ HANDOFF 已追加（{len(t2.splitlines())} 行）")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
