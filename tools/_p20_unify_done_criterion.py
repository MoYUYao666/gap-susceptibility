# -*- coding: utf-8 -*-
r"""把"已完成"判据抽成**共享函数**，供 `run_task` 与 `--list` 共用（2026-10-08 02:52）。

## 问题

上一版只修了 `run_task` 里的判据，`--list` 仍用独立的 `d.exists()` → **两处不一致**：
`--list` 仍把 α 显示为"已完成"（实际是首跑旧文件）。

**同一判据出现在两处代码里 = 迟早不一致。** 抽成函数，消除重复。

    python tools\_p20_unify_done_criterion.py [--apply]
"""
from __future__ import annotations

import ast
import io
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
F = REPO / "tools" / "_p20_serial_executor.py"

HELPER = '''

def task_done(done: Path) -> tuple[bool, str]:
    """**唯一的"已完成"判据**（供 run_task 与 --list 共用）。

    为什么不能只看"文件存在"：α 的首跑结果文件在**重跑开始前**就已存在，
    只看存在性会把"未跑"误判为"已完成"，**静默丢数据**。
    （本项目同类教训：下载脚本的"目录非空即跳过"连败两次。）

    返回 (是否完成, 理由)。
    """
    if not (done.exists() and done.stat().st_size > 0):
        return False, "文件不存在"
    if done.name == "alpha_from_gradients.json":
        bak = done.with_name("alpha_from_gradients_maxsamp2000.json")
        if bak.exists():
            try:
                d = json.loads(io.open(done, encoding="utf-8").read())
                newer = done.stat().st_mtime > bak.stat().st_mtime
                if not (newer and d.get("max_samples") == 5000 and len(d.get("records", [])) >= 2):
                    return False, (f"仍是首跑（max_samples={d.get('max_samples')}, "
                                   f"晚于备份={newer}）")
            except Exception as e:
                return False, f"读结果失败（{e}）"
    return True, "合格"
'''

OLD_RUN = '''    # 完成判据：**不能只看文件存在**——α 的首跑结果文件在重跑开始前就已存在，
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

NEW_RUN = '''    finished, why = task_done(done)
    if finished:
        log(f"⏭ {name} 已完成（{why}）→ 跳过")
        return "skipped"
    if done.exists():
        log(f"   {name}: 输出存在但{why} → **需重跑**")'''

OLD_LIST = '''        for i, (n, c, d, t) in enumerate(q, 1):
            mark = "✅ 已完成" if (d.exists() and d.stat().st_size > 0) else "⏳ 待跑"
            print(f"  {i:>2}. {n:<24} {mark}")'''
NEW_LIST = '''        for i, (n, c, d, t) in enumerate(q, 1):
            fin, why = task_done(d)
            mark = "✅ 已完成" if fin else f"⏳ 待跑（{why}）"
            print(f"  {i:>2}. {n:<24} {mark}")'''


def main() -> int:
    apply = "--apply" in sys.argv
    t = io.open(F, encoding="utf-8").read()
    if "def task_done(" in t:
        print("  已抽成函数，跳过")
        return 0
    for old, new, tag in ((OLD_RUN, NEW_RUN, "run_task"),
                          (OLD_LIST, NEW_LIST, "--list")):
        if t.count(old) != 1:
            print(f"  ❌ {tag} 未唯一命中（{t.count(old)}）")
            return 1
        t = t.replace(old, new, 1)
        print(f"  ✅ {tag} 已改为共享判据")
    # 插入 helper（放在 gpu_used_mb 之后）
    anchor = "def gpu_used_mb() -> int:"
    i = t.find(anchor)
    j = t.find("\ndef ", i + 1)
    t = t[:j] + HELPER + t[j:]
    ast.parse(t)
    if not apply:
        print("  （预演）")
        return 0
    io.open(F, "w", encoding="utf-8", newline="").write(t)
    t2 = io.open(F, encoding="utf-8").read()
    assert t2.count("def task_done(") == 1
    assert t2.count("task_done(done)") == 1 and t2.count("task_done(d)") == 1
    print("  ✅ 已写入：`task_done()` 为唯一判据，两处共用")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
