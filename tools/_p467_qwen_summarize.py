# -*- coding: utf-8 -*-
r"""P3 G 组（解码器 VLM 档）：汇总 `_p464` 的 Qwen2-VL-2B rank sweep。

只读 `outputs/analysis/p3d_qwen_ranksweep.json`，不引入任何外部数字。
报告里 §3.3 那张表就由本脚本产出。

    python tools\_p467_qwen_summarize.py [--apply]
"""
from __future__ import annotations

import argparse
import io
import json
import statistics as st
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
SRC = REPO / "outputs" / "analysis" / "p3d_qwen_ranksweep.json"
OUT = REPO / "outputs" / "analysis" / "p3d_qwen_summary.json"


def agg(vals):
    vals = [v for v in vals if v is not None]
    if not vals:
        return None
    return {"mean": sum(vals) / len(vals),
            "std": (st.stdev(vals) if len(vals) > 1 else 0.0), "n": len(vals)}


def fingerprint(path: Path, n: int) -> dict:
    """来源指纹：sha256 + 条数。派生聚合必须带，用于锁定引用时的口径。"""
    import hashlib
    return {"file": path.name, "sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
            "n_runs": n}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    ap.add_argument("--src", default=None, help="归档路径（默认主结果；稳健性档传 _mp50176.json）")
    a = ap.parse_args()

    global SRC, OUT
    if a.src:
        SRC = Path(a.src)
        if not SRC.is_absolute():
            SRC = REPO / SRC
        OUT = SRC.with_name(SRC.stem + "_summary.json")
    if not SRC.exists():
        print("!! 还没有 p3d_qwen_ranksweep.json")
        return 1
    d = json.loads(io.open(SRC, encoding="utf-8").read())
    base = [r for r in d["runs"] if r.get("rank") == 0]
    runs = [r for r in d["runs"]
            if r.get("condition") not in (None, "none") and r.get("rank", 0) > 0
            and r.get("dE_train") is not None]
    print(f"=== Qwen2-VL-2B rank sweep 汇总 ===")
    print(f"  归档总 run {len(d['runs'])} 条；其中冻结基线 {len(base)} 条、"
          f"可用的训练 run {len(runs)} 条")
    if base:
        b0 = base[0]
        e0 = (b0.get("E_train_epochs") or [None])[0]
        ee = (b0.get("E_eval_real_epochs") or [None])[0]
        print(f"  冻结基线（rank=0, device={b0.get('device')}）："
              f"E_train={e0}  E_eval_real={ee}")
    if not runs:
        print("  （还没有训练 run）")
        return 1

    cell = defaultdict(lambda: {"dEt": [], "dEe": [], "E0": [], "E1": [], "loss": []})
    for r in runs:
        k = (r["condition"], r["n_train"], r["rank"])
        cell[k]["dEt"].append(r.get("dE_train"))
        cell[k]["dEe"].append(r.get("dE_eval_real"))
        cell[k]["E0"].append((r.get("E_train_epochs") or [None])[0])
        cell[k]["E1"].append((r.get("E_train_epochs") or [None])[-1])
        cell[k]["loss"].append((r.get("loss_epochs") or [None])[-1])
    table = []
    for (cond, n, rank) in sorted(cell, key=lambda x: (x[0], x[1], x[2])):
        c = cell[(cond, n, rank)]
        table.append({"condition": cond, "n_train": n, "rank": rank,
                      "dE_train": agg(c["dEt"]), "dE_eval_real": agg(c["dEe"]),
                      "E_train_0": agg(c["E0"]), "E_train_final": agg(c["E1"]),
                      "loss_final": agg(c["loss"]), "seeds": len(c["dEt"])})
        t = table[-1]
        print(f"  {cond:<6} n={n:<4} r={rank:<3} seeds={t['seeds']}  "
              f"E_train {t['E_train_0']['mean']:.1f} → {t['E_train_final']['mean']:.1f}  "
              f"dE_train={t['dE_train']['mean']:+.1f}±{t['dE_train']['std']:.1f}  "
              f"dE_eval_real={t['dE_eval_real']['mean']:+.1f}±{t['dE_eval_real']['std']:.1f}")

    # 配对：同 (rank, n, seed) 下的 blank − real
    idx = {(r["condition"], r["n_train"], r["rank"], r["seed"]): r for r in runs}
    paired = []
    for (cond, n, rank, seed), r in sorted(idx.items()):
        if cond != "real":
            continue
        b = idx.get(("blank", n, rank, seed))
        if b is None:
            continue
        paired.append({"rank": rank, "n_train": n, "seed": seed,
                       "dE_train_blank_minus_real": (b.get("dE_train") or 0)
                       - (r.get("dE_train") or 0),
                       "dE_eval_blank_minus_real": (b.get("dE_eval_real") or 0)
                       - (r.get("dE_eval_real") or 0)})
    if paired:
        de = [p["dE_train_blank_minus_real"] for p in paired]
        dee = [p["dE_eval_blank_minus_real"] for p in paired]
        print(f"\n  配对（blank−real）n_pairs={len(paired)}："
              f"ΔE_train {sum(de)/len(de):+.1f}，ΔE_eval_real {sum(dee)/len(dee):+.1f}")
        for p in paired:
            print(f"    r={p['rank']:<3} s={p['seed']}  "
                  f"ΔE_train={p['dE_train_blank_minus_real']:+.1f}  "
                  f"ΔE_eval={p['dE_eval_blank_minus_real']:+.1f}")

    if not a.apply:
        print("\n（预演；加 --apply 写文件）")
        return 0
    res = {"experiment": "p3d_qwen_ranksweep_summary",
           "script": "tools/_p467_qwen_summarize.py",
           "generated_at_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
           "source": f"outputs/analysis/{SRC.name}",
           "source_fingerprint": fingerprint(SRC, len(d["runs"])),
           "derived_note": ("派生聚合，每次运行都会重算；引用请落到 "
                            f"{SRC.name} :: runs[*]（只增不改）并用 sha256 锁定口径"),
           "n_runs": len(runs), "table": table, "paired_blank_vs_real": paired}
    io.open(OUT, "w", encoding="utf-8", newline="").write(
        json.dumps(res, ensure_ascii=False, indent=1))
    print(f"\n  ✅ 已写 {OUT.relative_to(REPO)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
