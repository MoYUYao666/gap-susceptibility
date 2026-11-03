# -*- coding: utf-8 -*-
r"""修 `_p20_serial_executor.py` 的"已完成"判据（2026-10-08 02:50）。

## Bug

执行器对 α 任务判"✅ 已完成"，但那是**首跑（`max_samples=2000`）的旧结果文件**——
重跑（5000 样本）**尚未写盘**（实测：结果 mtime 23:19:23，备份 mtime 01:51:53）。

**根因**：判据只查"文件存在且非空"，而**该文件在重跑开始前就已存在**（首跑留下的）。

**这是"存在性判据"的经典错误**——本项目已因同类错误连栽两次：
- 下载脚本的"目录非空即跳过" → 连败两次；
- 现在执行器的"文件存在即完成" → 会把未跑的任务标成完成，**静默丢数据**。

## 修法

判据改为：
1. 若存在**首跑备份** `alpha_from_gradients_maxsamp2000.json` → 要求**结果文件 mtime 晚于备份**
   且 `max_samples == 5000`（读 JSON 核对，不只看时间）；
2. 其余任务仍用"文件存在且非空"（它们的输出文件是任务**新写**的，不存在歧义）。

    python tools\_p20_fix_done_criterion.py [--apply]
"""
from __future__ import annotations

import ast
import io
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
F = REPO / "tools" / "_p20_serial_executor.py"

OLD = '''    if done.exists() and done.stat().st_size > 0:
        log(f"⏭ {name} 已完成（{done.name} 存在）→ 跳过")
        return "skipped"'''

NEW = '''    # 完成判据：**不能只看文件存在**——α 的首跑结果文件在重跑开始前就已存在，
    # 只看存在性会把"未跑"误判为"已完成"（本项目已有同类教训：下载脚本的"目录非空即跳过"）。
    if done.exists() and done.stat().st_size > 0:
        ok = True
        if done.name == "alpha_from_gradients.json":
            bak = done.with_name("alpha_from_gradients_maxsamp2000.json")
            if bak.exists():
                try:
                    d = json.loads(io.open(done, encoding="utf-8").read())
                    newer = done.stat().st_mtime > bak.stat().st_mtime
                    ok = bool(newer and d.get("max_samples") == 5000
                              and len(d.get("records", [])) >= 2)
                    if not ok:
                        log(f"⏭ 检查 {name}: 结果文件存在但仍是首跑（max_samples="
                            f"{d.get('max_samples')}, 备份更新={not newer}）→ **需重跑**")
                except Exception as e:
                    log(f"⚠ {name}: 读结果失败（{e}）→ 视为需重跑")
                    ok = False
        if ok:
            log(f"⏭ {name} 已完成（{done.name} 存在且合格）→ 跳过")
            return "skipped"'''

# json 需已导入（文件顶部已有 import json）


def main() -> int:
    apply = "--apply" in sys.argv
    t = io.open(F, encoding="utf-8").read()
    if "不能只看文件存在" in t:
        print("  已修，跳过")
        return 0
    c = t.count(OLD)
    print(f"  命中 {c} 次")
    if c != 1:
        return 1
    if not apply:
        print("  （预演）")
        return 0
    new = t.replace(OLD, NEW, 1)
    ast.parse(new)
    io.open(F, "w", encoding="utf-8", newline="").write(new)
    t2 = io.open(F, encoding="utf-8").read()
    assert "不能只看文件存在" in t2 and "max_samples\") == 5000" in t2
    print("  ✅ 已修：α 任务须核对 max_samples==5000 且结果晚于备份")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
