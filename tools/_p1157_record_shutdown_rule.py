# -*- coding: utf-8 -*-
r"""Record the standing rule that cloud instances are shut down by the agent once the run is verified.

Operator instruction, 2026-10-17: "云端全部跑完并确认无误就关机哈，我就不手动关了，记录这个规则".

Written into `AGENTS.md` and `CLAUDE.md` so future sessions inherit it, and into `HANDOFF.md` as a dated entry.
The rule has a deliberate ordering: verified first, then shut down -- never shut down a host whose results are not
yet pulled back, because the data disk may not outlive the instance.

    python tools/_p1157_record_shutdown_rule.py [--apply]
"""
from __future__ import annotations

import argparse
import io
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
MARK = "云端跑完即关机"

SECTION = """## 🔴🔴 云端主机收尾规则（用户明确要求，2026-10-17 立）

> **"云端全部跑完并确认无误就关机哈，我就不手动关了，记录这个规则"** —— 2026-10-17 操作者原话

**云端任务结束后由 agent 负责关机，操作者不再手动关。**

**必须按此顺序（顺序不可颠倒）**：

1. **确认跑完**：进程已退出、没有 `ARM_FAILURES` / traceback；
2. **确认无误**：跑该阶段的全项校验（记录数、字段、样本量、适配器非空、分塔隔离等），**断言通过**；
3. **取回产物**：记录 JSON、适配器、分析结果**全部拉到本地**并逐文件校验大小；**任何还需要的东西都不能只留在云端**
   （数据盘未必随实例保留，旧实例已出现过"机器失联"）；
4. **只有以上三步完成后**才关机：
   ```bash
   sync && ( shutdown -h now || poweroff || /usr/bin/shutdown -h now )
   ```
   若容器内无权关机，则如实报告"需在 AutoDL 控制台停止"，**不得假装已关**；
5. **关机后验证**：端口探测应失败（`Test-NetConnection <host> -Port <port>` 返回 False），并在交接文档记一条"已关机"及时间。

**禁止**：结果未取回就关机；校验未过就关机；把"我以为跑完了"当成跑完。
"""

ENT = """> **🔴 2026-10-17 18:30 —— 记录规则：云端跑完并校验无误后由 agent 关机（操作者不再手动关）**
>
> 操作者原话：「云端全部跑完并确认无误就关机哈，我就不手动关了，记录这个规则」。
>
> **已写入 `AGENTS.md` / `CLAUDE.md`**（用户要求，最高优先级）。执行顺序**不可颠倒**：
>
> 1. 确认跑完（进程退出、无 `ARM_FAILURES`/traceback）→
> 2. 全项校验断言通过 → 
> 3. **产物全部取回本地并逐文件校验**（数据盘未必随实例保留；旧实例已出现过失联）→ 
> 4. 才执行 `sync && shutdown -h now`（无权关机则如实报告"需控制台停止"，不得假装已关）→ 
> 5. 关机后端口探测确认不可达，并在此文档记"已关机"时间。
>
> **禁止**：结果未取回就关、校验未过就关、把"以为跑完"当跑完。
>
> 本条规则与「所有数据必须要可复现有来源」一致：**取回并校验是关机的前置条件**。
>

"""


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    a = ap.parse_args()
    if not a.apply:
        print("  (dry run)")
        return 0
    for name in ("AGENTS.md", "CLAUDE.md"):
        f = REPO / name
        if not f.exists():
            print(f"  {name}: missing, skipped")
            continue
        t = io.open(f, encoding="utf-8").read()
        if MARK in t:
            print(f"  {name}: rule already present")
            continue
        io.open(f, "w", encoding="utf-8", newline="").write(t.rstrip("\n") + "\n\n" + SECTION)
        print(f"  {name}: shutdown rule appended")

    hp = io.open(REPO / "HANDOFF.md", encoding="utf-8").read()
    if "云端跑完并校验无误后由 agent 关机" not in hp:
        i = hp.find("# 项目交接文档")
        j = hp.find("\n", i)
        hp = hp[: j + 1] + "\n" + ENT + hp[j + 1:]
        io.open(REPO / "HANDOFF.md", "w", encoding="utf-8", newline="").write(hp)
        print("  HANDOFF entry added")
    else:
        print("  HANDOFF already has the entry")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
