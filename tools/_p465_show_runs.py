# -*- coding: utf-8 -*-
r"""小工具：打印 rank-sweep 归档里每条 run 的关键字段与耗时。

兼容两种 schema：
  - `_p461`（CLIP）：含 `arm` / `dE_test` / `R@1`
  - `_p464`（Qwen2-VL-2B）：含 `dE_eval_real` / `E_train_epochs`

    python tools\_p465_show_runs.py [归档路径]
"""
from __future__ import annotations

import io
import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
p = Path(sys.argv[1]) if len(sys.argv) > 1 else REPO / "outputs/analysis/p3d_clip_ranksweep.json"
d = json.loads(io.open(p, encoding="utf-8").read())
runs = d["runs"]
print(f"{p.name}: {len(runs)} runs, "
      f"protocol={json.dumps(d.get('protocol', {}), ensure_ascii=False)[:220]}")
is_clip = bool(runs) and "arm" in runs[0]
tot = 0.0
if is_clip:
    print(f"{'rank':>4} {'arm':<6} {'cond':<6} {'n':>5} {'seed':>5} {'sec':>7} "
          f"{'dE_train':>10} {'dE_test':>10} {'R@1':>7} {'i2t':>7} {'t2i':>7} {'dev':<5}")
    for r in runs:
        tot += r.get("seconds", 0)
        print(f"{r['rank']:>4} {r['arm']:<6} {r['condition']:<6} {r['n_train']:>5} "
              f"{r['seed']:>5} {r.get('seconds', 0):>7.1f} "
              f"{str(r.get('dE_train')):>10} {r['dE_test']:>10.4f} "
              f"{r['R@1']:>7.4f} {r['R@1_i2t']:>7.4f} {r['R@1_t2i']:>7.4f} "
              f"{str(r.get('device', '?')):<5}")
else:
    print(f"{'rank':>4} {'cond':<6} {'n':>5} {'seed':>5} {'sec':>7} "
          f"{'E0':>10} {'E1':>10} {'dE_train':>10} {'dE_eval_real':>13} {'dev':<5}")
    for r in runs:
        tot += r.get("seconds", 0)
        e = r.get("E_train_epochs") or [None, None]
        e0 = f"{e[0]:.1f}" if e[0] is not None else "n/a"
        e1 = f"{e[-1]:.1f}" if e[-1] is not None else "n/a"
        dt = f"{r['dE_train']:+.1f}" if r.get("dE_train") is not None else "n/a"
        de = f"{r['dE_eval_real']:+.1f}" if r.get("dE_eval_real") is not None else "n/a"
        print(f"{r['rank']:>4} {r['condition']:<6} {r['n_train']:>5} "
              f"{r['seed']:>5} {r.get('seconds', 0):>7.1f} "
              f"{e0:>10} {e1:>10} {dt:>10} {de:>13} {str(r.get('device', '?')):<5}")
print(f"累计 run 内耗时 {tot:.0f}s")
