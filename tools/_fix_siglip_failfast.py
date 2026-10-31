# -*- coding: utf-8 -*-
r"""给 `tools/_run_siglip_r4.py` 加**连续失败即停**（2026-10-04）。

## 为什么

2026-10-04 上午 GPU 进入故障态后，`_run_siglip_r4.py` **仍把剩下 8 个 run 逐个跑完**
（每个立即失败），白耗约 20 分钟并刷屏。**GPU 故障时应尽早停下并报告**，而不是硬撞。

## 改法

累计**连续失败**计数：达到 `MAX_CONSEC=2` 即 `break` 并打印醒目提示
（含"检查 GPU：nvidia-smi / 稍后重试"）。任一 run 成功则把计数清零。

    python tools\_fix_siglip_failfast.py [--apply]
"""
from __future__ import annotations

import io
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
F = REPO / "tools" / "_run_siglip_r4.py"

OLD = '''    for t, s in todo:
        outdir = "outputs/siglip_strict/seed%s" % s'''
NEW = '''    MAX_CONSEC = 2          # 连续失败这么多次就停（GPU 故障时不硬撞）
    consec = 0
    for t, s in todo:
        outdir = "outputs/siglip_strict/seed%s" % s'''

OLD2 = '''        # 落盘位置校验：必须在期望路径
        if not dest(t, s).exists():
            print("  ❌ 结果未落在期望路径：%s" % dest(t, s).relative_to(REPO), flush=True)'''
NEW2 = '''        # 落盘位置校验：必须在期望路径
        ok = dest(t, s).exists()
        if not ok:
            print("  ❌ 结果未落在期望路径：%s" % dest(t, s).relative_to(REPO), flush=True)
        consec = 0 if ok else consec + 1
        if consec >= MAX_CONSEC:
            print("\\n  🛑 连续 %d 次失败 —— GPU 可能处于故障态，**停止本批**。" % consec, flush=True)
            print("     请检查：nvidia-smi（报错/掉卡？）｜ 是否有其他训练在并发占用？", flush=True)
            print("     恢复后用同一命令续跑（幂等）：python tools/_run_siglip_r4.py --apply", flush=True)
            break'''
OLD3 = '''    done = len(glob.glob(str(REPO / "outputs/siglip_strict/*/s7_siglip_lora_r4_*/results.json")))'''
NEW3 = '''    done = len(glob.glob(str(REPO / "outputs/siglip_strict/*/s7_siglip_lora_r4_*/results.json")))'''


def main() -> int:
    apply = "--apply" in sys.argv
    t = io.open(F, encoding="utf-8").read()
    if "MAX_CONSEC" in t:
        print("  已含 MAX_CONSEC，跳过")
        return 0
    n = 0
    for old, new, why in ((OLD, NEW, "加连续失败计数"),
                          (OLD2, NEW2, "失败即累计并在阈值处停止")):
        c = t.count(old)
        if c == 1:
            print("  ✅ %s" % why)
            if apply:
                t = t.replace(old, new, 1)
            n += 1
        else:
            print("  ⚠ %s：命中 %d 次" % (why, c))
    if apply and n == 2:
        io.open(F, "w", encoding="utf-8", newline="").write(t)
        t2 = io.open(F, encoding="utf-8").read()
        assert "MAX_CONSEC = 2" in t2 and "GPU 可能处于故障态" in t2
        print("\n  ✅ 已改并断言通过")
    else:
        print("\n  %d/2" % n + ("（预演）" if not apply else ""))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
