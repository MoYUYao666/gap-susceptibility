# -*- coding: utf-8 -*-
r"""看解码器 VLM 三臂的配置是否可比 + 补 seed 的可行性估算（2026-10-10）。

    python tools\_p151_vlm_arms_table.py [--apply]
"""
from __future__ import annotations

import argparse
import glob
import io
import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
OUT = REPO / "outputs" / "analysis" / "vlm_seed_feasibility.json"


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    a = ap.parse_args()

    rows = []
    for f in sorted(glob.glob(str(REPO / "outputs/vlm_strictfreeze/**/*_seed*.json"),
                              recursive=True)):
        d = json.loads(io.open(f, encoding="utf-8", errors="replace").read())
        rows.append({
            "file": str(Path(f).relative_to(REPO)),
            "arm": d.get("arm"), "seed": d.get("seed"),
            "4bit": d.get("4bit"), "batch": d.get("batch"),
            "epochs": d.get("epochs"), "max_samples": d.get("max_samples"),
            "n_lang": d.get("n_lang"), "n_vis": d.get("n_vis"),
            "n_trainable": d.get("n_trainable"),
            "elapsed_sec": d.get("elapsed_sec"),
            "cg_span": d.get("cg_span"), "dg_span": d.get("dg_span"),
            "n_epochs_logged": len(d.get("cg") or []),
        })

    print("=== 三臂配置对比 ===")
    hdr = f"{'arm':<12}{'seed':<6}{'4bit':<7}{'batch':<7}{'ep':<4}{'samples':<9}" \
          f"{'n_trainable':<13}{'耗时(s)':<9}{'cg_span':<10}{'dg_span':<10}"
    print("  " + hdr)
    for r in sorted(rows, key=lambda x: (str(x["arm"]), str(x["seed"]))):
        print("  " + f"{str(r['arm']):<12}{str(r['seed']):<6}{str(r['4bit']):<7}"
              f"{str(r['batch']):<7}{str(r['epochs']):<4}{str(r['max_samples']):<9}"
              f"{str(r['n_trainable']):<13}{str(r['elapsed_sec']):<9}"
              f"{r['cg_span'] if r['cg_span'] is None else round(r['cg_span'], 4)!s:<10}"
              f"{r['dg_span'] if r['dg_span'] is None else round(r['dg_span'], 4)!s:<10}")

    # 只算"完整配置"（400 样本 3 epoch）
    full = [r for r in rows if r["max_samples"] == 400 and r["epochs"] == 3]
    print(f"\n=== 完整配置的 run: {len(full)} 个 ===")
    tot = 0.0
    for r in full:
        print(f"  {r['arm']:<12} seed {r['seed']} ｜ {r['elapsed_sec']} s "
              f"｜ 4bit={r['4bit']}")
        if r["elapsed_sec"]:
            tot += r["elapsed_sec"]
    if full:
        avg = tot / len(full)
        print(f"\n  平均单 run: **{avg:.0f} s（{avg/60:.1f} min）**")
        for n_seed, n_arm in ((2, 3), (3, 3)):
            runs = n_seed * n_arm
            print(f"  补 {n_seed} 个新 seed × {n_arm} 臂 = {runs} run "
                  f"→ **约 {runs * avg / 3600:.1f} 小时**")

    # 可比性检查
    print("\n=== 可比性检查 ===")
    arms_full = {r["arm"] for r in full}
    cfg = {(r["batch"], r["max_samples"], r["epochs"], r["4bit"]) for r in full}
    print(f"  含完整配置的臂: {sorted(arms_full)}")
    print(f"  配置集合: {cfg}")
    print(f"  → {'✅ 三臂同配置，可比' if len(cfg) == 1 and len(arms_full) == 3 else '⚠️ 配置不一致，需核对'}")

    if a.apply:
        OUT.parent.mkdir(parents=True, exist_ok=True)
        io.open(OUT, "w", encoding="utf-8", newline="").write(json.dumps(
            {"rows": rows, "full_runs": len(full),
             "avg_sec": round(tot / len(full), 1) if full else None,
             "arms_full": sorted(arms_full), "configs": [list(c) for c in cfg]},
            ensure_ascii=False, indent=1))
        print(f"\n  ✅ 已写 {OUT.relative_to(REPO)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
