# -*- coding: utf-8 -*-
r"""过夜串行驱动：**等前一个 GPU 实验结束，再启下一个**（2026-10-07，操作者选 A）。

## 为什么需要

**GPU 只有 8 GB**（实测 7.8/8.2 GB 被 α 实验占满）→ 实验必须串行。
过夜无人值守，故需要一个**轮询等待**的驱动器。

## 队列（按优先级）

| 序 | 实验 | 前提 | 产出 |
|---|---|---|---|
| 1 | **α 预测（both 臂）** | —— | `outputs/theory/alpha_from_gradients/alpha_from_gradients.json` |
| 2 | **③ CLIP B/16，rank 4**（最干净的 patch-size 对照） | `models/clip-vit-base-patch16` 就位 | `outputs/strict_freeze_b16/r4/` |
| 3 | **④ Qwen2-VL 三臂** | α/③ 结束 | `outputs/vlm_strictfreeze/` |

**设计原则**：
- **只等 JSON 落盘**（不用 sleep 猜时间）；
- 每步**单独超时上限**，超时则**跳过并记录**，不无限等；
- 全部动作**追加写日志**，便于次日核查。

    python tools\_p7_overnight_driver.py [--apply]
"""
from __future__ import annotations

import io
import json
import subprocess
import sys
import time
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
PY = r"D:\Anaconda\envs\pytorch\python.exe"
LOG = REPO / "outputs" / "_overnight_driver.log"
ALPHA = REPO / "outputs" / "theory" / "alpha_from_gradients" / "alpha_from_gradients.json"
B16 = REPO / "models" / "clip-vit-base-patch16"
B16_OUT = REPO / "outputs" / "strict_freeze_b16" / "r4"


def log(msg: str) -> None:
    line = f"[{time.strftime('%H:%M:%S')}] {msg}"
    print(line, flush=True)
    with io.open(LOG, "a", encoding="utf-8") as f:
        f.write(line + "\n")


def wait_for(path: Path, timeout_s: int, what: str) -> bool:
    t0 = time.time()
    while time.time() - t0 < timeout_s:
        if path.exists():
            try:
                if path.stat().st_size > 0:
                    log(f"✅ {what} 就绪（{path.name}）")
                    return True
            except Exception:
                pass
        time.sleep(30)
    log(f"⚠ {what} 等待超时（{timeout_s//60} min），跳过")
    return False


def run(cmd: list[str], what: str, timeout_s: int) -> bool:
    log(f"▶ 启动 {what}")
    log("   " + " ".join(cmd))
    try:
        r = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout_s, cwd=str(REPO))
        out = (r.stdout or "")[-600:]
        err = (r.stderr or "")[-400:]
        log(f"   {what} 结束 rc={r.returncode}")
        for ln in out.splitlines()[-8:]:
            log("   | " + ln[:160])
        if r.returncode != 0 and err:
            for ln in err.splitlines()[-5:]:
                log("   ! " + ln[:160])
        return r.returncode == 0
    except subprocess.TimeoutExpired:
        log(f"   ⚠ {what} 超时（{timeout_s//60} min）")
        return False


def main() -> int:
    apply = "--apply" in sys.argv
    if not apply:
        print("  （预演）")
        print(f"  队列: 等 α → 跑 CLIP B/16 r4 → 跑 Qwen2-VL 三臂")
        print(f"  日志: {LOG}")
        return 0

    log("=" * 70)
    log("过夜串行驱动启动")

    # ① 等 α 实验
    if wait_for(ALPHA, 3 * 3600, "α 预测"):
        try:
            d = json.loads(io.open(ALPHA, encoding="utf-8").read())
            log(f"   α 结果: corr={d.get('corr'):.4f} 中位相对误差={d.get('median_rel_err'):.4f} "
                f"passed={d.get('passed')}")
        except Exception as e:
            log(f"   ⚠ 读 α 结果失败: {e}")
    else:
        log("   （α 未完成，仍继续后续队列）")

    # ②a OpenCLIP B/32 × rank 4（patch-32 组 2→3，已验证可跑）
    run([PY, "experiments/strict_freeze_control.py",
         "--model", "models/openclip",
         "--out-dir", "outputs/strict_freeze_oclip/r4",
         "--name", "oclip_r4_", "--rank", "4", "--alpha-mult", "2",
         "--seeds", "42", "--epochs", "10", "--max-samples", "5000",
         "--batch-size", "128", "--skip-frozen"],
        "③a OpenCLIP B/32 rank4（三臂）", 3 * 3600)

    # ②b CLIP B/16 × rank 4（patch-16 组加固，需模型就位）
    if wait_for(B16, 1800, "CLIP B/16 模型"):
        run([PY, "experiments/strict_freeze_control.py",
             "--model", "models/clip-vit-base-patch16",
             "--out-dir", "outputs/strict_freeze_b16/r4",
             "--name", "b16_r4_", "--rank", "4", "--alpha-mult", "2",
             "--seeds", "42", "--epochs", "10", "--max-samples", "5000",
             "--batch-size", "128", "--skip-frozen"],
            "③ CLIP B/16 rank4（三臂）", 3 * 3600)
    else:
        log("   跳过 ③（模型未就位）")

    # ③ Qwen2-VL 三臂（前置：写出脚本）
    vlm = REPO / "tools" / "_p8_qwen_strictfreeze.py"
    if vlm.exists():
        run([PY, str(vlm), "--apply"], "④ Qwen2-VL 三臂", 5 * 3600)
    else:
        log(f"   跳过 ④（{vlm.name} 尚未就绪）")

    log("过夜串行驱动结束")
    log("=" * 70)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
