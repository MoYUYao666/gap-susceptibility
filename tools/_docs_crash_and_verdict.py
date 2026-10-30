# -*- coding: utf-8 -*-
r"""落账：执行器崩溃故障 + 同秩判定写入文件地图（2026-10-08 10:05）。

    python tools\_docs_crash_and_verdict.py [--apply]
"""
from __future__ import annotations

import io
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]

ENT = """> **🔴 2026-10-08 10:05 —— 执行器因**我自己写的文件名 bug** 崩溃，已修；同秩判定已出**
>
> ### 故障（实测，非推测）
>
> ```
> File "tools/_p20_serial_executor.py", line 230, in run_task
>     with io.open(tlog, "a", encoding="utf-8") as f:
> FileNotFoundError: [Errno 2] No such file or directory: 'A:_α_由梯度预测(trainer基座).log'
> ```
>
> **两个缺陷（都是我写的）**：
>
> | # | 缺陷 | 后果 |
> |---|---|---|
> | 1 | 任务名 `"A: α 由梯度预测(trainer基座)"` 含 **`:`**（Windows 文件名非法），而净化只去了空格与斜杠 | `io.open` 抛 `FileNotFoundError` |
> | 2 | **异常逃出 `main()` 的 for 循环** | **整个执行器退出** → **12 个 COCO 任务（36 h）全被丢弃** |
>
> **这是"一个任务的日志文件名错误 → 整条队列停摆"**，与昨夜"三个驱动撞车"同属**架构脆弱**。
>
> ### 修复（`tools/_p26_fix_executor_crash.py`）
>
> 1. **文件名净化**：只保留 `[0-9A-Za-z._-]` 与 CJK，其余替换为 `_`，限长 80
>    （实测：`'A: α 由梯度预测(trainer基座)'` → **`'A_由梯度预测_trainer基座'`**）；
> 2. **`main()` 循环包 `try/except`**：任一任务抛异常 → 记日志、标 `crashed`、**继续下一个**
>    （**绝不中断队列**）。
>
> **执行器已重启并正确跳过已完成 6 项**，现跑实验 A。
>
> ### 🎯 同秩判定（已成文，见上一条 HANDOFF）
>
> **在相同 rank（r4）、相同协议、相同样本量下**：
> `CLIP B/32` 与 `CLIP B/16` 的**最保护臂相同**（都是 `text_only`）→ **patch size 不影响排序**。
> 结论指向**预训练目标/语料**：四个 `text_only 最保护` 的骨干全是**对比式图文预训练**（WIT×3、LAION×1）；
> 两个 `both 最保护` 的骨干（SigLIP=sigmoid、BioCLIP=生物域）**都不是**。
>
> **论文原文 *"every patch-16 backbone puts both there"* 被证伪。** 改法待操作者确认（我建议按预训练分组）。
>
> ### 本阶段自错累计 13 次
>
> | 类型 | 次数 | 最近一例 |
> |---|---|---|
> | 判据类 | 6 | "文件存在即完成" |
> | 操作类 | 2 | 误杀过夜驱动 |
> | 设计类 | 3 | 样本量差 15 倍、动力学差 10 倍、同秩对照缺失 |
> | **代码类** | **2** | **`text=True` 未显式 UTF-8；任务名含 `:` 致队列崩溃** |
>
> **共同模式未变：用了方便的判据/写法，而非正确的。**
> **两条对策已固化**：① 判据事先写明并抽成单一函数；② **队列里任何单任务异常都不得中断队列**。
"""


def main() -> int:
    apply = "--apply" in sys.argv
    if not apply:
        print("  （预演）")
        return 0
    hp = REPO / "HANDOFF.md"
    t = io.open(hp, encoding="utf-8").read()
    if "执行器因" in t and "我自己写的文件名 bug" in t:
        print("  已记录，跳过")
        return 0
    i = t.find("# 项目交接文档")
    j = t.find("\n", i)
    io.open(hp, "w", encoding="utf-8", newline="").write(t[:j + 1] + "\n" + ENT + t[j + 1:])
    t2 = io.open(hp, encoding="utf-8").read()
    for k in ("文件名 bug", "FileNotFoundError", "绝不中断队列", "本阶段自错累计 13 次"):
        assert k in t2, f"断言失败：缺 {k}"
    print(f"  ✅ HANDOFF 已追加（{len(t2.splitlines())} 行）")

    # 文件地图：把同秩判定写入待办
    mp = REPO / "文件地图.md"
    m = io.open(mp, encoding="utf-8").read()
    MARK = "0F. 🎯 同秩判定已出"
    if MARK not in m:
        add = """
**0F. 🎯 同秩判定已出（2026-10-08）：**patch size 不是决定因素****

- **在相同 rank（r4）、相同协议、相同样本量下**：`CLIP B/32` 与 `CLIP B/16` 最保护臂**相同**（都 `text_only`）
  → **patch size 不影响排序**。
- **指向预训练**：四个 `text_only 最保护` 的骨干全是对比式图文预训练（WIT×3、LAION×1）；
  两个 `both 最保护` 的（SigLIP=sigmoid、BioCLIP=生物域）**都不是**。
- **论文原文 *"every patch-16 backbone puts both there"* 被证伪** → 改法待操作者确认（建议按预训练分组）。
- 证据：`outputs/analysis/samerank_verdict.json`、`tools/_p25_samerank_verdict.py`。
- ⚠️ **效应量异质**：CLIP B/32 r8 = 4.5 sd、CLIP B/32 r4 = 3.7 sd、CLIP B/16 r4 = 11.3 sd、
  **OpenCLIP r4 仅 2.1 sd（最弱）** → **稳健的是方向一致性（4/4），不是每个配置都显著**。

"""
        anchor = "## 七、当前真正待办（按优先级）\n"
        m2 = m.replace(anchor, anchor + add, 1)
        io.open(mp, "w", encoding="utf-8", newline="").write(m2)
        m3 = io.open(mp, encoding="utf-8").read()
        assert MARK in m3
        print(f"  ✅ 文件地图.md 已更新（{len(m3.splitlines())} 行）")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
