# -*- coding: utf-8 -*-
r"""核 `_p235` 新评的 τ 与**归档**是否一致（2026-10-12）。

## 疑点

`lr0.0/seed42`：
- **归档** `eval_epoch{1,2,3,5,10}.json`：τ = 0.8327 / 0.8248 / 0.8228 / 0.8235 / 0.8233
- **我新评** `eval_epoch4.json`：τ = 0.7201
- **我新评** `eval_epoch{6,7,8}`：τ ≈ 0.708–0.709

**若归档与新评的 τ 不在同一尺度 → 数据不可混用，必须先查清。**

    python tools\_p237_check_tau_scale.py
"""
from __future__ import annotations

import glob
import io
import json
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
ROOT = REPO / "outputs" / "a1_class_aligned" / "lr0.0"


def main() -> int:
    print("=" * 92)
    print("① lr0.0/seed42 的 eval_epoch 文件（按修改时间）")
    print("=" * 92)
    for f in sorted(glob.glob(str(ROOT / "seed42" / "eval_epoch*.json"))):
        p = Path(f)
        d = json.loads(io.open(f, encoding="utf-8", errors="replace").read())
        import time
        mt = time.strftime("%m-%d %H:%M", time.localtime(p.stat().st_mtime))
        print(f"  {p.name:<20} ep={d.get('eval_epoch'):<3} τ={d.get('tau_final'):<22} "
              f"top1_50k={d.get('top1_50k'):<20} val_loss={round(d.get('val_loss') or 0, 4):<8} "
              f"改于 {mt}")

    print()
    print("=" * 92)
    print("② 与归档的 τ 轨迹（a1_tau_trajectory.json）对照")
    print("=" * 92)
    tp = REPO / "outputs" / "a1_tau_trajectory.json"
    if tp.exists():
        t = json.loads(io.open(tp, encoding="utf-8", errors="replace").read())
        print(f"  frozen: {t.get('frozen')}")
        for arm in ("both", "text_only"):
            print(f"  {arm}:")
            for r in t.get(arm, []):
                print(f"    ep{r['epoch']:<3} top1={r['top1']:<8} CG={r['CG']:<9} τ={r['tau']}")

    print()
    print("=" * 92)
    print("③ eval-only 用的模型构造代码（看是否套 EMA）")
    print("=" * 92)
    src = io.open(REPO / "tools" / "train_class_aligned.py",
                  encoding="utf-8", errors="replace").read().splitlines()
    for i, ln in enumerate(src, 1):
        if "eval_only" in ln or "ema" in ln.lower() or "compute_tau" in ln:
            print(f"  {i:4} {ln[:100]}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
