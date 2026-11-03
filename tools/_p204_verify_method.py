# -*- coding: utf-8 -*-
r"""核实方法学审稿人（`docs/A1_ADVERSARIAL_METHOD.md`）的 5 条关键指控（2026-10-12）。

| # | 指控 | 核实 |
|---|---|---|
| 1 | **Simpson 悖论**：池化 Spearman 0.786 由组间差异产生，组内是 −0.5 | 从 `a1_h_offset.json` 独立重算 |
| 2 | `a1_rr_e3_benchmarks.json` 里 **tau 与 tau_pred_exact 完全相同** | 读该文件逐条对比 |
| 3 | 留出检验 R²=0.371/0.378，OpenCLIP 为**负**且被当"小样本假象"打发 | 读论文 + 归档 |
| 4 | `highlights.tex:14` 仍是**未加限定的** "r = 1.000" | 读该文件 |
| 5 | 检索**不**跟随 gap（Spearman(CG,R@1) = −0.389） | 从归档重算 |

    python tools\_p204_verify_method.py [--apply]
"""
from __future__ import annotations

import argparse
import glob
import io
import json
import statistics as st
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
OUT = REPO / "outputs" / "analysis" / "a1_method_verify.json"


def spearman(xs, ys):
    def rank(v):
        s = sorted(range(len(v)), key=lambda i: v[i])
        r = [0.0] * len(v)
        for pos, i in enumerate(s):
            r[i] = pos + 1
        return r
    rx, ry = rank(xs), rank(ys)
    n = len(xs)
    mx, my = st.mean(rx), st.mean(ry)
    num = sum((rx[i] - mx) * (ry[i] - my) for i in range(n))
    den = (sum((a - mx) ** 2 for a in rx) * sum((b - my) ** 2 for b in ry)) ** 0.5
    return num / den if den else float("nan")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    a = ap.parse_args()
    res = {}

    print("=" * 88)
    print("① 核实 Simpson 悖论：a1_h_offset.json 的检查点 (tau5, top1)")
    print("=" * 88)
    p = REPO / "outputs" / "a1_h_offset.json"
    if p.exists():
        d = json.loads(io.open(p, encoding="utf-8", errors="replace").read())
        print(f"  顶层键: {list(d.keys())[:14]}")
        # 找含 tau / top1 的记录
        recs = []
        def walk(o, path=""):
            if isinstance(o, dict):
                keys = {k.lower() for k in o}
                if any("tau" in k for k in keys) and any(
                        ("top1" in k or "acc" in k or "top_1" in k) for k in keys):
                    recs.append((path, o))
                for k, v in o.items():
                    walk(v, path + "/" + k)
            elif isinstance(o, list):
                for i, v in enumerate(o[:40]):
                    walk(v, path + f"[{i}]")
        walk(d)
        print(f"  含 (tau, top1) 的记录: {len(recs)} 处")
        for path, r in recs[:3]:
            print(f"    {path}: {json.dumps(r, ensure_ascii=False)[:220]}")
        res["offset_records"] = len(recs)
    else:
        print("  ❌ 无该文件")

    print()
    print("=" * 88)
    print("② 核实 tau 与 tau_pred_exact 是否相同（a1_rr_e3_benchmarks.json）")
    print("=" * 88)
    p2 = REPO / "outputs" / "a1_rr_e3_benchmarks.json"
    if p2.exists():
        d = json.loads(io.open(p2, encoding="utf-8", errors="replace").read())
        txt = json.dumps(d, ensure_ascii=False)
        print(f"  文件 {len(txt)} 字符")
        print(f"  含 'tau_pred_exact': {'✅' if 'tau_pred_exact' in txt else '❌'}")
        # 逐个 benchmark 对比
        def find_pairs(o, path=""):
            out = []
            if isinstance(o, dict):
                ks = list(o.keys())
                tk = [k for k in ks if k.lower() in ("tau", "tau5", "tau_final")]
                pk = [k for k in ks if "pred" in k.lower()]
                if tk and pk:
                    out.append((path, {k: o[k] for k in tk + pk}))
                for k, v in o.items():
                    out += find_pairs(v, path + "/" + k)
            elif isinstance(o, list):
                for i, v in enumerate(o):
                    out += find_pairs(v, path + f"[{i}]")
            return out
        pairs = find_pairs(d)
        print(f"  含 (tau, *pred*) 的节点: {len(pairs)}")
        same = 0
        for path, kv in pairs[:12]:
            vals = [v for v in kv.values() if isinstance(v, (int, float))]
            identical = len(set(vals)) == 1 if vals else None
            if identical:
                same += 1
            print(f"    {path[:52]:<52} {kv}  {'← 完全相同' if identical else ''}")
        print(f"  → 完全相同的节点: {same}/{len(pairs[:12])}")
        res["identical_tau_pred"] = same
    else:
        print("  ❌ 无该文件")

    print()
    print("=" * 88)
    print("④ 核实 highlights.tex 的 r=1.000 是否加了限定")
    print("=" * 88)
    h = REPO / "paper_a1" / "highlights.tex"
    if h.exists():
        t = io.open(h, encoding="utf-8", errors="replace").read()
        for ln in t.splitlines():
            if ln.strip().startswith("\\item"):
                mark = "🔴 未限定" if ("1.000" in ln and "self-consist" not in ln.lower()) else ""
                print(f"    {ln.strip()[:100]}  {mark}")
        res["highlights_unhedged_r1000"] = ("1.000" in t
                                            and "self-consist" not in t.lower())
    else:
        print("  ❌ 无该文件")

    print()
    print("=" * 88)
    print("⑤ 核实检索是否跟随 gap（论文正文声称『retrieval R@1 responds to the gap』）")
    print("=" * 88)
    print("  （需从归档逐条件取 (CG, R@1)；此处只报文件可用性）")
    for f in ("outputs/a1_h_bootstrap.json", "outputs/a1_full_results.json",
              "outputs/a1_baseline_metrics.json"):
        p3 = REPO / f
        print(f"    {f:<42} {'✅' if p3.exists() else '❌'}")

    if a.apply:
        OUT.parent.mkdir(parents=True, exist_ok=True)
        io.open(OUT, "w", encoding="utf-8", newline="").write(
            json.dumps(res, ensure_ascii=False, indent=1))
        print(f"\n  ✅ 已写 {OUT.relative_to(REPO)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
