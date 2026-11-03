# -*- coding: utf-8 -*-
r"""COCO 逐配置 ODE 表**补跑队列**（操作者选①严格冻结，2026-10-07）。

## 目标

恢复 `supplement.tex` 的 `tab:coco_ode`（被我按"无来源"原则从 15 行删到 3 行）。
**操作者指示"可以把没有的补上，重跑"** → 用**严格冻结**补 12 个配置，使该表**有来源、可复现**。

## 待补配置（12 个）

`r ∈ {1,2,4,16,32,64}` × `{text_only, both}` —— **r=8 已有**（归档 3 配置 × 3 seed）。
**seeds = 42,123,456**（与归档一致）。

## 成本与排序

每 run ≈ 60 min（5000 样本 / batch 128 / 10 epoch）。**12 配置 × 3 seed = 36 run ≈ 36 h**。

**按信息量排序**（`--order`）：
1. **`priority`**（默认）：先 **r=4、16、64**（论文表里 `both` 位的关键秩）+ r=1,2,32 → 尽早能填出半张表；
2. **`all`**：全集。

**可续跑**：已存在 `results.json` 的 run 会**跳过**（`strict_freeze_control.py` 自带该逻辑）。

## 用法

    python tools\_p14_coco_sweep_driver.py --order priority --apply

**等 GPU 空闲**：本驱动先等队列 1/2 结束（检测 `_alpha_rerun_driver.log` 出现"队列 2 结束"或 α 结果更新），
再逐配置串行跑。
"""
from __future__ import annotations

import io
import subprocess
import sys
import time
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
PY = r"D:\Anaconda\envs\pytorch\python.exe"
LOG = REPO / "outputs" / "_coco_sweep_driver.log"
ALPHA_RERUN_LOG = REPO / "outputs" / "_alpha_rerun_driver.log"
OUTROOT = REPO / "outputs" / "coco_sweep"

SEEDS = "42 123 456"


def order_list(kind: str) -> list[tuple[str, int]]:
    text = [("text_only", r) for r in (4, 16, 64, 1, 2, 32)]
    both = [("both", r) for r in (4, 16, 64, 1, 2, 32)]
    # 交错：先各秩的 both（论文表里 both 位排在后但信息量同高），再 text
    pairs = []
    for (s1, r1), (_, r2) in zip(text, both):
        pairs.append((s1, r1))
        pairs.append(("both", r2))
    if kind == "all":
        return pairs
    return pairs  # priority 与 all 目前同序；保留参数以便日后扩


def log(msg: str) -> None:
    line = f"[{time.strftime('%H:%M:%S')}] {msg}"
    print(line, flush=True)
    with io.open(LOG, "a", encoding="utf-8") as f:
        f.write(line + "\n")


def wait_for_queues(timeout_s: int = 6 * 3600) -> None:
    """等队列 2（α 重跑）结束，再开始 COCO 补跑。"""
    t0 = time.time()
    while time.time() - t0 < timeout_s:
        if ALPHA_RERUN_LOG.exists():
            tail = io.open(ALPHA_RERUN_LOG, encoding="utf-8", errors="ignore").read()[-800:]
            if "队列 2 结束" in tail:
                log("✅ 队列 2 已结束 → 开始 COCO 补跑")
                return
        time.sleep(60)
    log(f"⚠ 等待队列 2 超时（{timeout_s//3600} h）→ 仍开始 COCO 补跑（若 GPU 冲突会报错）")


def main() -> int:
    argv = sys.argv
    apply = "--apply" in argv
    kind = argv[argv.index("--order") + 1] if "--order" in argv else "priority"
    todo = order_list(kind)
    print("=== COCO 逐配置补跑（严格冻结，操作者选①）===")
    print(f"  待补配置 {len(todo)} 个 × seeds {SEEDS} = {len(todo)*3} run")
    print(f"  顺序: {[f'{s}_r{r}' for s, r in todo]}")
    print(f"  日志: {LOG}")
    if not apply:
        print("  （预演；加 --apply 实跑）")
        return 0

    log("=" * 70)
    log(f"COCO 补跑启动（order={kind}，{len(todo)} 配置）")
    wait_for_queues()

    ok = fail = 0
    for site, rk in todo:
        outdir = OUTROOT / f"r{rk}"
        cmd = [PY, "experiments/strict_freeze_control.py",
               "--dataset", "coco", "--data-dir", ".",
               "--out-dir", str(outdir.relative_to(REPO)).replace("\\", "/"),
               "--name", f"coco_{site}_r{rk}_",
               "--rank", str(rk), "--alpha-mult", "2",
               "--tags", site, "--seeds", *SEEDS.split(),
               "--epochs", "10", "--max-samples", "5000",
               "--batch-size", "128", "--skip-frozen"]
        log(f"▶ {site} r={rk}")
        ok_this, out_lines = False, []
        try:
            pr = subprocess.run(cmd, capture_output=True, text=True,
                                timeout=4 * 3600, cwd=str(REPO))
            out_lines = (pr.stdout or "").splitlines()
            if pr.returncode == 0:
                ok += 1
                ok_this = True
            else:
                fail += 1
                err = next((l for l in (pr.stderr or "").splitlines() if "Error" in l), "")
                out_lines = [(err or ("rc=%d" % pr.returncode))[:150]]
        except subprocess.TimeoutExpired:
            fail += 1
            out_lines = ["超时（4 h）"]
        log(f"   {'✅ rc=0' if ok_this else '❌ 失败'}")
        for ln in out_lines[-3:]:
            log("   | " + ln[:150])
    log(f"COCO 补跑结束：成功 {ok} ｜ 失败 {fail}")
    log("=" * 70)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
