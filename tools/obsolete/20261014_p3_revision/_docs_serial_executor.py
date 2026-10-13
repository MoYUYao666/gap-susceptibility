# -*- coding: utf-8 -*-
r"""落账：串行执行器架构修复（2026-10-08 03:10）。

    python tools\_docs_serial_executor.py [--apply]
"""
from __future__ import annotations

import io
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]

ENT = """> **🔧 2026-10-08 03:10 —— 过夜暴露的**架构缺陷**与修复：统一串行执行器**
>
> ### 昨夜实际发生了什么（从日志复盘）
>
> | 时刻 | 事件 |
> |---|---|
> | 23:05 | 过夜驱动启动 |
> | 23:19 | α 首跑完成（corr=0.664，passed=False） |
> | 23:41 | **③a OpenCLIP 完成 ✅**（规律复现） |
> | 23:41 | ③b CLIP B/16 启动 |
> | 23:51 | 队列 2 启动（等 ③b） |
> | 23:57 | 队列 3（COCO）启动（等队列 2） |
> | **01:51** | **队列 2 等 ③b 超时（120 min）→ 仍启动 α 重跑** |
> | **01:51** | **③b 仍在跑（both 臂）→ 两实验争 8 GB 显存** |
> | **02:41** | **过夜驱动硬超时（180 min）→ ③b 被判超时** |
>
> ### 三个架构缺陷（**全部是设计错误，非偶发**）
>
> | # | 缺陷 | 后果 |
> |---|---|---|
> | 1 | **三个驱动各看各的信号**（不同文件、不同超时） | **必然撞车**：队列 2 在 ③b 未完成时启动 α 重跑 |
> | 2 | **硬超时不杀子进程** | 超时后子进程**继续训练**（孤儿占 GPU） |
> | 3 | **`subprocess.run(capture_output=True)`** | stdout 捕获在内存**不落盘** → 跑到哪一步**无从得知** |
>
> ### 修复：`tools/_p20_serial_executor.py`（**单写者**）
>
> | 设计 | 做法 |
> |---|---|
> | **单写者** | **一个**执行器按序跑全部任务，任务间不并行 |
> | **超时即杀** | `Popen(start_new_session=True)` → 超时 `os.killpg` **杀整组**（含 spawn 的子进程） |
> | **实时日志** | stdout/stderr **逐行追加落盘**（`outputs/_serial_logs/*.log`） |
> | **等 GPU 不丢任务** | GPU 忙时**轮询等待**（上限 8 h）——**等 GPU 是正常等待，不是失败** |
> | **不重复启动** | 启动前按**命令行精确匹配**是否已有同任务在跑 → 有则等它结束 |
> | **可续跑** | 已有合格结果的任务跳过 |
>
> ### 🐛 开发过程中被**实测**抓出的四个 bug（都是我自己写的）
>
> | # | Bug | 抓出的方式 |
> |---|---|---|
> | 1 | **"文件存在即完成"** 判据 → α 被误判"已完成"（实为首跑旧文件） | `--list` 输出与事实不符 |
> | 2 | **同一判据写在两处**（`run_task` 与 `--list`）→ 修了一处另一处仍错 | 修完后 `--list` 未变 |
> | 3 | **GPU 忙时"跳过任务"** → 首任务被**永久丢弃**、队列停摆（静默丢数据） | 读代码发现 |
> | 4 | **`running_pids` 返回空** —— `text=True` 用 GBK 解码，遇中文路径 `UnicodeDecodeError` | **单独跑函数实测**（未只信"已加上"） |
>
> **Bug 4 与昨夜驱动 stderr 刷屏的 `UnicodeDecodeError` 是同一根因。**
> **教训**：Windows 上任何 `capture_output=True, text=True` **必须显式给 `encoding="utf-8"`**。
>
> ### 现在的状态
>
> ```
> [02:44:08] ⚠ 启动时 GPU 已被占 7386 MB —— 本执行器会等待
> [02:44:08]    α重跑(5000样本): 输出存在但仍是首跑（max_samples=2000）→ 需重跑
> [02:44:08] ⏳ α重跑(5000样本): 已有同任务在跑（PID [46628]）→ 等它结束，不重复启动
> ```
>
> ### 队列（15 项，串行）
>
> 1. **α 重跑**（5000 样本，进行中）
> 2. **③b `both`**、3. **③b `vision_only`**（CLIP B/16 缺的两臂）
> 4–15. **COCO 12 配置 × 3 seed**（严格冻结，操作者选①）
"""


def main() -> int:
    apply = "--apply" in sys.argv
    if not apply:
        print("  （预演）")
        return 0
    gpu = subprocess.run(["nvidia-smi", "--query-gpu=memory.used,utilization.gpu",
                          "--format=csv,noheader"], capture_output=True, text=True,
                         encoding="utf-8", errors="replace").stdout.strip()
    body = ENT.replace("> ### 现在的状态", "> ### 现在的状态（GPU " + gpu + "）")
    hp = REPO / "HANDOFF.md"
    t = io.open(hp, encoding="utf-8").read()
    if "统一串行执行器" in t:
        print("  已记录，跳过")
        return 0
    i = t.find("# 项目交接文档")
    j = t.find("\n", i)
    io.open(hp, "w", encoding="utf-8", newline="").write(t[:j + 1] + "\n" + body + t[j + 1:])
    t2 = io.open(hp, encoding="utf-8").read()
    for k in ("统一串行执行器", "必然撞车", "杀整组", "UnicodeDecodeError", "不重复启动"):
        assert k in t2, f"断言失败：缺 {k}"
    print(f"  ✅ HANDOFF 已追加（{len(t2.splitlines())} 行）")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
