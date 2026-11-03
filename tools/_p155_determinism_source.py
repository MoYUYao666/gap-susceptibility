# -*- coding: utf-8 -*-
r"""查非确定性的来源：4-bit（bitsandbytes） vs bf16（2026-10-10）。

## 已知

- 改种子顺序后，**同 seed 42 两次仍不同**（cg_span 0.3041 vs 0.4073）；
- 但**第 1 epoch 的 loss 几乎相同**（1.38557 vs 1.38499）→ **批顺序已固定**，
  分歧来自**训练本身**。

## 假设

**bitsandbytes 的 NF4 反量化在 CUDA 上非确定**（已知问题）→ 4-bit 路径不可复现。
`text_only` 的归档是 **bf16**（`4bit=False`），若 bf16 确定，则：
- **科学对照应改用 bf16**（但 `vision_only` 在 bf16 下曾 OOM）；
- 或**如实把"训练不可逐位复现"写进 limitation**。

## 本脚本

**bf16 同 seed 跑两次（小配置）**，看是否逐位相同。

    python tools\_p155_determinism_source.py [--apply]
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
LOG = REPO / "outputs" / "_det_source.log"


def log(m: str) -> None:
    line = f"[{time.strftime('%m-%d %H:%M:%S')}] {m}"
    print(line, flush=True)
    with io.open(LOG, "a", encoding="utf-8") as f:
        f.write(line + "\n")


def run(seed: str, outdir: str, arm: str, cfg: list) -> bool:
    cmd = [PY, "-u", "tools/_p47_qwen_train.py", "--apply", *cfg,
           "--seed", seed, "--arms", arm, "--outdir", outdir]
    r = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8",
                       errors="replace", timeout=3 * 3600, cwd=str(REPO))
    if r.returncode != 0:
        err = next((l.strip() for l in (r.stderr or "").splitlines()
                    if "Error" in l), "")
        log(f"   ❌ rc={r.returncode} {err[:120]}")
    return r.returncode == 0


def compare(dirs, arm, seed):
    ds = []
    for d in dirs:
        f = REPO / d / f"{arm}_seed{seed}.json"
        if not f.exists():
            return None
        ds.append(json.loads(io.open(f, encoding="utf-8").read()))
    ident = all(x["cg_span"] == ds[0]["cg_span"] and x["dg_span"] == ds[0]["dg_span"]
                for x in ds)
    return ident, ds


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    a = ap.parse_args()

    # bf16 小配置（避免 OOM）：text_only 臂
    CFG_BF16 = ["--maxsamples", "400", "--epochs", "3", "--batch", "2"]
    print("=== 计划：bf16（无 --4bit）同 seed 42 跑两次，text_only 臂 ===")
    print(f"  配置：{' '.join(CFG_BF16)}")
    if not a.apply:
        print("  （预演）")
        return 0

    log("=" * 58)
    log("非确定性来源：bf16 两次对照")
    for tag, out in (("A", "outputs/_det_bf16A"), ("B", "outputs/_det_bf16B")):
        log(f"▶ bf16 第 {tag} 次 → {out}")
        if not run("42", out, "text_only", CFG_BF16):
            log(f"   ❌ {tag} 失败")
            return 1

    res = compare(["outputs/_det_bf16A", "outputs/_det_bf16B"], "text_only", "42")
    if res is None:
        log("❌ 结果文件缺失")
        return 1
    ident, ds = res
    print("\n=== bf16 两次比对 ===")
    for tag, d in zip("AB", ds):
        print(f"  {tag}: cg_span={d['cg_span']:.6f} dg_span={d['dg_span']:.6f}")
        print(f"     cg={[round(v, 5) for v in d['cg']]}")
    print(f"\n  → bf16 {'✅ **可逐位复现**' if ident else '❌ 仍不可复现'}")

    log(f"bf16 可复现: {'是' if ident else '否'}")
    log("=" * 58)
    print("\n=== 结论 ===")
    if ident:
        print("  ✅ 非确定性**来自 4-bit（bitsandbytes）** → 科学对照若换 bf16 即可复现")
        print("     但 `vision_only` 在 bf16 下曾 OOM（8 GB 限制）→ 需评估")
    else:
        print("  ❌ 连 bf16 也不可复现 → 需**如实把'训练不可逐位复现'写进 limitation**，")
        print("     并以**多种子均值±标准差**作为报告口径（本来就是这么做的）")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
