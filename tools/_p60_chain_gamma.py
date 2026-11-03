# -*- coding: utf-8 -*-
r"""给补 seed 驱动加"完成后自动跑 `Γ_m`"（2026-10-09）。

## 为什么

操作者选的 A 是"等 `Γ_m` 完整测量后再定口径"。
补 seed 还剩 5 个 run（6–9 h）→ **让驱动跑完后自动接 `Γ_m`**，避免人工交接。

## 加什么

在 `main()` 的汇总前插入：

```python
run([PY, "tools/_p58_gamma_clip.py", "--apply"], ...)
```

并在日志里记录结果路径。

    python tools\_p60_chain_gamma.py [--apply]
"""
from __future__ import annotations

import ast
import io
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
F = REPO / "tools" / "_p56_add_seeds.py"

OLD = '''    log(f"补 seed 结束：成功 {ok} ｜ 失败 {fail}")
    log("=" * 66)'''
NEW = '''    log(f"补 seed 结束：成功 {ok} ｜ 失败 {fail}")

    # **自动接 `Γ_m` 完整测量**（操作者选 A：等它出来再定论文口径）
    log("─" * 66)
    log("▶ 接：Γ_m 完整测量（CLIP 三臂，含 cos）")
    try:
        r = subprocess.run([PY, "tools/_p58_gamma_clip.py", "--apply"],
                           capture_output=True, text=True, encoding="utf-8",
                           errors="replace", timeout=3600, cwd=str(REPO))
        for ln in (r.stdout or "").splitlines():
            if any(t in ln for t in ("Γ_v", "Γ_t", "已写", "‖∇")):
                log("   | " + ln.strip()[:150])
        log(f"   Γ_m 测量 rc={r.returncode}")
    except subprocess.TimeoutExpired:
        log("   ⚠ Γ_m 测量超时（1 h）")
    log("=" * 66)'''

OLD2 = '''    n = len(JOBS) * len(ARMS) * 2'''
NEW2 = '''    n = len(JOBS) * len(ARMS) * 2
    # 注意：已存在 results.json 的 run 会被跳过，故实际待跑数可能小于 n'''

OLD3 = '''    print(f"  seeds: {NEW_SEEDS} ｜ 共 {n} run ｜ 预估约 4 h")'''
NEW3 = '''    print(f"  seeds: {NEW_SEEDS} ｜ 计划 {n} run（**已完成的会被跳过**）")
    print("  跑完自动接：完整 Γ_m 测量（tools/_p58_gamma_clip.py）")'''


def main() -> int:
    apply = "--apply" in sys.argv
    t = io.open(F, encoding="utf-8").read()
    if "_p58_gamma_clip.py" in t:
        print("  已加，跳过")
        return 0
    for old, new, tag in ((OLD, NEW, "尾部串联"), (OLD2, NEW2, "注释"), (OLD3, NEW3, "提示")):
        c = t.count(old)
        if c != 1:
            print(f"  ❌ {tag} 未唯一命中（{c}）")
            return 1
        t = t.replace(old, new, 1)
    ast.parse(t)
    if not apply:
        print("  （预演）")
        return 0
    io.open(F, "w", encoding="utf-8", newline="").write(t)
    t2 = io.open(F, encoding="utf-8").read()
    assert "_p58_gamma_clip.py" in t2 and "已完成的会被跳过" in t2
    print("  ✅ 已加：补 seed 完成后自动接 Γ_m 完整测量")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
