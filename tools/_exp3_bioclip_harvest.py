# -*- coding: utf-8 -*-
r"""从 BioCLIP 运行日志中解析**已完成**的 run 并落盘（2026-10-06）。

## 为什么需要

`tools/_exp3_bioclip_strict.py` **只在全部 18 个 run 跑完时才写 `results.json`**
（——本身就是个设计缺陷：中途停止会丢掉全部结果）。操作者要求停止时已完成 **9 个 run**（rank 4 全部），
故从日志把结果抢救出来并落盘，避免重跑。

**已记录该缺陷，后续脚本应在每个 run 后即落盘。**

## 解析

日志行形如（严格冻结对照，每 run 一轮）：
```
  r4 text_only    seed=42    LoRA 层 36 ｜ 可训 294912
      → ΔCG=-0.3584（1.7969 → 1.4385）
```

    python tools\_exp3_bioclip_harvest.py [--apply]
"""
from __future__ import annotations

import io
import json
import re
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
OUT = REPO / "outputs" / "strict_freeze_bioclip"
LOG = REPO / "outputs" / "strict_freeze_bioclip" / "run_log.txt"

HEAD = re.compile(r"^\s*r(\d+)\s+(text_only|both|vision_only)\s+seed=(\d+)\s+LoRA 层 (\d+) ｜ 可训 (\d+)")
RES = re.compile(r"→\s*ΔCG=([+-][\d.]+)（([\d.]+)\s*→\s*([\d.]+)）")


def parse(text: str) -> list[dict]:
    rows, cur = [], None
    for line in text.splitlines():
        m = HEAD.search(line)
        if m:
            cur = dict(rank=int(m.group(1)), arm=m.group(2), seed=int(m.group(3)),
                       n_lora_layers=int(m.group(4)), n_trainable=int(m.group(5)))
            continue
        r = RES.search(line)
        if r and cur is not None:
            cur.update(delta_cg=float(r.group(1)), initial_cg=float(r.group(2)),
                       final_cg=float(r.group(3)))
            rows.append(cur)
            cur = None
    return rows


def main() -> int:
    apply = "--apply" in sys.argv
    if not LOG.exists():
        print(f"  ⚠ 日志不存在：{LOG.relative_to(REPO)}")
        print("     请先把 job 输出写入该文件（见 HANDOFF 的解析说明）。")
        return 1
    rows = parse(io.open(LOG, encoding="utf-8", errors="ignore").read())
    print(f"  从日志解析到 {len(rows)} 个完整 run")
    for r in rows:
        print(f"    r{r['rank']} {r['arm']:<12} seed={r['seed']:<5} "
              f"ΔCG={r['delta_cg']:+.4f}（{r['initial_cg']:.4f} → {r['final_cg']:.4f}）")

    import statistics as st
    summary = {}
    print("\n  === 按 (rank, 臂) 汇总 ===")
    for rk in sorted({r["rank"] for r in rows}):
        for arm in ("both", "text_only", "vision_only"):
            vs = [r["delta_cg"] for r in rows if r["rank"] == rk and r["arm"] == arm]
            if vs:
                summary[f"r{rk}_{arm}"] = dict(mean=round(st.mean(vs), 4),
                                               sd=round(st.stdev(vs), 4) if len(vs) > 1 else 0.0,
                                               n=len(vs))
                print(f"    r{rk} {arm:<12} ΔCG={st.mean(vs):+.4f} ± "
                      f"{(st.stdev(vs) if len(vs) > 1 else 0):.4f}  (n={len(vs)})")

    if apply:
        OUT.mkdir(parents=True, exist_ok=True)
        (OUT / "results_partial.json").write_text(json.dumps(
            {"model": "BioCLIP ViT-B/16 (models/oceanclip-0.15b/bioclip)",
             "note": "部分结果：操作者于 2026-10-06 要求停止，rank 4 已完成、rank 8 未完成。"
                     "由 tools/_exp3_bioclip_harvest.py 从运行日志解析落盘。",
             "protocol": {"max_samples": 5000, "epochs": 10, "batch": 128,
                          "alpha_mult": 2, "seeds": [42, 123, 456], "ranks_planned": [4, 8]},
             "completed_ranks": sorted({r["rank"] for r in rows}),
             "summary": summary, "records": rows}, indent=2, ensure_ascii=False),
            encoding="utf-8")
        p = OUT / "results_partial.json"
        d = json.loads(p.read_text(encoding="utf-8"))
        assert d["records"], "落盘为空"
        assert all(k.startswith("r4_") for k in d["summary"]), "summary 混入了非 rank4"
        print(f"\n  ✅ 已写 {p.relative_to(REPO)}（{len(d['records'])} 条记录）")
    else:
        print("\n  （预演，加 --apply 落盘）")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
