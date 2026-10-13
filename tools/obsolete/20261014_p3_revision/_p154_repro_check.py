# -*- coding: utf-8 -*-
r"""验证 `_p47_qwen_train.py` 改后可复现：同 seed 跑两次，逐位比对（2026-10-10）。

## 为什么要验

我把 `torch.manual_seed(seed)` 提到 `create_dataloaders` **之前**（原在之后）→
批顺序现在应只由 seed 决定。**但必须实测确认**，否则新 seed 的数据依然不可信
（CUDA 异步 kernel 仍可能引入非确定性）。

**判据**：两次 `identical=True`（`cg_span`、`dg_span`、逐 epoch 轨迹全部逐位相同）。

    python tools\_p154_repro_check.py [--apply]
"""
from __future__ import annotations

import argparse
import io
import json
import subprocess
import sys
import time
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
PY = sys.executable
LOG = REPO / "outputs" / "_vlm_repro_check.log"
CFG = ["--maxsamples", "400", "--epochs", "3", "--batch", "4", "--4bit"]


def log(m: str) -> None:
    line = f"[{time.strftime('%m-%d %H:%M:%S')}] {m}"
    print(line, flush=True)
    with io.open(LOG, "a", encoding="utf-8") as f:
        f.write(line + "\n")


def run(seed: str, outdir: str, arm: str) -> bool:
    cmd = [PY, "-u", "tools/_p47_qwen_train.py", "--apply", *CFG,
           "--seed", seed, "--arms", arm, "--outdir", outdir]
    r = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8",
                       errors="replace", timeout=3 * 3600, cwd=str(REPO))
    if r.returncode != 0:
        err = next((l.strip() for l in (r.stderr or "").splitlines()
                    if "Error" in l), "")
        log(f"   ❌ rc={r.returncode} {err[:120]}")
    return r.returncode == 0


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    ap.add_argument("--arm", default="vision_only")
    ap.add_argument("--seed", default="42")
    a = ap.parse_args()

    A, B = "outputs/_reproA", "outputs/_reproB"
    print(f"=== 计划：{a.arm} ｜ seed {a.seed} ｜ 两次独立进程 ===")
    print(f"  A → {A}   B → {B}")
    print(f"  配置：{' '.join(CFG)}")
    if not a.apply:
        print("  （预演）")
        return 0

    log("=" * 58)
    log(f"可复现性验证：{a.arm} seed {a.seed} × 2 次独立进程")
    for tag, out in (("A", A), ("B", B)):
        log(f"▶ 第 {tag} 次 → {out}")
        if not run(a.seed, out, a.arm):
            log(f"   ❌ {tag} 失败")
            return 1

    fa = REPO / A / f"{a.arm}_seed{a.seed}.json"
    fb = REPO / B / f"{a.arm}_seed{a.seed}.json"
    da = json.loads(io.open(fa, encoding="utf-8").read())
    db = json.loads(io.open(fb, encoding="utf-8").read())

    print("\n=== 逐位比对 ===")
    fields = ("cg_span", "dg_span")
    ident = True
    for k in fields:
        same = da[k] == db[k]
        ident &= same
        print(f"  {k:<10} A={da[k]!r}  B={db[k]!r}  {'✅' if same else '❌'}")
    for k in ("cg", "dg_star", "loss"):
        same = da[k] == db[k]
        ident &= same
        print(f"  {k:<10} {'✅ 逐位相同' if same else '❌ 不同'}")
        if not same:
            print(f"       A={[round(x, 5) for x in da[k]]}")
            print(f"       B={[round(x, 5) for x in db[k]]}")

    log(f"可复现: {'✅ 是' if ident else '❌ 否'}")
    log("=" * 58)

    print(f"\n=== 结论：{'✅ **改后可复现**（新 seed 数据可信）' if ident else '❌ **仍不可复现**'} ===")
    return 0 if ident else 2


if __name__ == "__main__":
    raise SystemExit(main())
