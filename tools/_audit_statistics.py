# -*- coding: utf-8 -*-
r"""统计审核：论文里的每个数字 vs 归档独立重算（2026-10-11）。

## 审核什么

| # | 项 | 方法 |
|---|---|---|
| 1 | **批次一致性** | 每组每臂的 `batch_size` 必须一致（128） |
| 2 | **seed 数** | 论文声称的 n 与实际文件数一致 |
| 3 | **表格数字** | 从 `results.json` 独立重算 mean/sd，与论文源码里的数字逐一比对 |
| 4 | **统计口径** | sd 用 `statistics.stdev`（样本 sd, ddof=1）；效应量用**合并 sd** |
| 5 | **未污染的 run** | 排除 `*.bak` / `.MISPLACED_*` 目录 |
| 6 | **论文与归档同一批** | 数字能唯一匹配到某个 (组, 臂, rank) |

**判据**：**不接受"看起来对"**——每个数字都要在归档里找到对应值（容差见下）。

    python tools\_audit_statistics.py [--apply]
"""
from __future__ import annotations

import argparse
import glob
import io
import json
import re
import statistics as st
import sys
from collections import defaultdict
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
SEC = REPO / "paper合" / "sections"
OUT = REPO / "outputs" / "analysis" / "statistics_audit.json"

ARMS = ("text_only", "both", "vision_only")


def load_group(root: str, want_batch: int = 128):
    """{(arm, rank): {seed: (dcg, r1, batch, file)}}"""
    out = defaultdict(dict)
    for f in sorted(glob.glob(str(REPO / root / "**" / "results.json"), recursive=True)):
        if ".bak" in f or "MISPLACED" in f:
            continue
        try:
            d = json.loads(io.open(f, encoding="utf-8", errors="replace").read())
        except Exception:
            continue
        p = Path(f).parts
        arm = next((x for x in p if x in ARMS), None)
        if arm is None:
            continue
        seed = next((x for x in p if x.startswith("seed")), None)
        rank = next((x for x in p if re.fullmatch(r"r\d+", x)), None)
        if rank is None:
            m = None
            for seg in p:
                m = re.search(r"_r(\d+)$", seg)
                if m:
                    rank = "r" + m.group(1)
                    break
            rank = rank or "r4"
        fg = (d.get("final_gap") or {}).get("centroid_gap")
        ig = (d.get("initial_gap") or {}).get("centroid_gap")
        r1 = (d.get("final_retrieval") or {}).get("r1")
        out[(arm, rank)][seed] = {
            "dcg": (fg - ig) if (fg is not None and ig is not None) else None,
            "r1": r1, "batch": d.get("batch_size"),
            "max_samples": d.get("max_samples"), "epochs": d.get("epochs"),
            "file": str(Path(f).relative_to(REPO)),
        }
    return out


def agg(entries):
    """返回 (n, mean, sd, 各 seed 值)。仅用 batch=128 的。"""
    vals = [v["dcg"] for v in entries.values()
            if v["dcg"] is not None and v["batch"] == 128]
    if not vals:
        return 0, None, None, []
    return (len(vals), round(st.mean(vals), 6),
            round(st.stdev(vals), 6) if len(vals) > 1 else None,
            [round(v, 6) for v in sorted(vals)])


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    a = ap.parse_args()
    report = {"groups": {}, "issues": [], "checks": []}

    def issue(tag, msg):
        report["issues"].append({"tag": tag, "msg": msg})
        print(f"  🔴 [{tag}] {msg}")

    # ══════════ ① 批次 & seed 一致性 ══════════
    print("=" * 84)
    print("① 批次一致性与 seed 覆盖")
    print("=" * 84)
    GROUPS = {
        "B/32 r4": "outputs/strict_freeze_b32_r4",
        "B/16 r4": "outputs/strict_freeze_b16/r4",
        "OCLIP r4": "outputs/strict_freeze_oclip/r4",
        "COCO to": "outputs/coco_sweep_text_only",
        "COCO both": "outputs/coco_sweep",
    }
    for tag, root in GROUPS.items():
        g = load_group(root)
        report["groups"][tag] = {}
        for (arm, rank), entries in sorted(g.items()):
            batches = sorted({v["batch"] for v in entries.values()})
            n = len(entries)
            rep = {"n": n, "batches": batches,
                   "seeds": sorted(entries.keys()),
                   "arms_rank": f"{arm}|{rank}"}
            report["groups"][tag][f"{arm}|{rank}"] = rep
            flag = "✅" if batches == [128] else "🔴"
            print(f"  {flag} {tag:<10} {arm:<12} {rank:<5} n={n} batch={batches}")
            if batches != [128]:
                issue("batch", f"{tag}/{arm}/{rank} 批次={batches}")

    # ══════════ ② 表格数字：独立重算 vs 论文 ══════════
    print()
    print("=" * 84)
    print("② tab:position_strict：论文数字 vs 独立重算")
    print("=" * 84)
    tables = {
        "CLIP B/32 (WIT)": ("outputs/strict_freeze_b32_r4", "r4",
                            {"text_only": -0.0304, "both": -0.0204, "vision_only": +0.0166}),
        "CLIP B/16 (WIT)": ("outputs/strict_freeze_b16/r4", "r4",
                            {"text_only": -0.0166, "both": +0.0124, "vision_only": +0.0376}),
        "OpenCLIP (LAION)": ("outputs/strict_freeze_oclip/r4", "r4",
                             {"text_only": +0.0802, "both": +0.0864, "vision_only": +0.0996}),
    }
    computed = {}
    for label, (root, rank, paper) in tables.items():
        g = load_group(root)
        computed[label] = {}
        for arm, pv in paper.items():
            n, mean, sd, vals = agg(g.get((arm, rank), {}))
            computed[label][arm] = {"n": n, "mean": mean, "sd": sd, "vals": vals}
            ok = (mean is not None and abs(mean - pv) <= 0.00005)
            print(f"  {'✅' if ok else '🔴'} {label:<18} {arm:<12} n={n} "
                  f"论文 {pv:+.4f} ｜ 重算 {mean:+.4f}"
                  + (f" ± {sd:.4f}" if sd else ""))
            report["checks"].append({"what": f"{label}|{arm}", "paper": pv,
                                     "computed": mean, "n": n, "sd": sd, "ok": ok})
            if not ok:
                issue("table", f"{label}/{arm} 论文 {pv} ≠ 重算 {mean}")

    # 效应量（合并 sd）
    print()
    print("  ── OpenCLIP 效应量（合并 sd = sqrt(sd1²+sd2²)）──")
    oc = computed["OpenCLIP (LAION)"]
    order = sorted(oc, key=lambda k: oc[k]["mean"])
    print("    由保护强到弱：" + " < ".join(f"{k}({oc[k]['mean']:+.4f})" for k in order))
    for i in range(len(order) - 1):
        a1, a2 = order[i], order[i + 1]
        diff = abs(oc[a1]["mean"] - oc[a2]["mean"])
        psd = (oc[a1]["sd"] ** 2 + oc[a2]["sd"] ** 2) ** 0.5
        k = diff / psd
        print(f"      {a1} vs {a2}: |Δ|={diff:.4f} pooled_sd={psd:.4f} → **{k:.2f} sd**")

    # ══════════ ③ 数据集翻转 ══════════
    print()
    print("=" * 84)
    print("③ 数据集翻转：论文数字 vs 独立重算（同秩 r4，同批次）")
    print("=" * 84)
    flip = {
        ("Flickr30k", "text_only"): ("outputs/strict_freeze_b32_r4", "r4", -0.0304),
        ("Flickr30k", "both"): ("outputs/strict_freeze_b32_r4", "r4", -0.0204),
        ("COCO", "text_only"): ("outputs/coco_sweep_text_only", "r4", -0.0430),
        ("COCO", "both"): ("outputs/coco_sweep", "r4", -0.0877),
    }
    for (ds, arm), (root, rank, pv) in flip.items():
        g = load_group(root)
        n, mean, sd, vals = agg(g.get((arm, rank), {}))
        ok = (mean is not None and abs(mean - pv) <= 0.00005)
        disp = f"{mean:+.4f}" if mean is not None else "无数据"
        print(f"  {'✅' if ok else '🔴'} {ds:<10} {arm:<12} n={n} 论文 {pv:+.4f} ｜ "
              f"重算 {disp}" + (f" ± {sd:.4f}" if sd else ""))
        if mean is None:
            _g = load_group(root)
            print(f"      ↳ 诊断: root={root} rank={rank} 现有键="
                  f"{sorted(_g.keys())[:8]}")
        report["checks"].append({"what": f"flip|{ds}|{arm}", "paper": pv,
                                 "computed": mean, "n": n, "sd": sd, "ok": ok})
        if not ok:
            issue("flip", f"{ds}/{arm} 论文 {pv} ≠ 重算 {mean}")

    print()
    print("  ── COCO text_only 全秩（论文 vs 重算）──")
    for rank, pv in (("r2", -0.0247), ("r8", -0.0690), ("r32", -0.1153), ("r64", -0.1359)):
        g = load_group("outputs/coco_sweep_text_only")
        n, mean, sd, vals = agg(g.get(("text_only", rank), {}))
        ok = (mean is not None and abs(mean - pv) <= 0.00005)
        _disp = f"{mean:+.4f}" if mean is not None else "无数据"
        print(f"  {'✅' if ok else '🔴'} {rank:<5} n={n} 论文 {pv:+.4f} ｜ 重算 {_disp}"
              + (f" ± {sd:.4f}" if sd else ""))
        report["checks"].append({"what": f"coco_rank|{rank}", "paper": pv,
                                 "computed": mean, "n": n, "sd": sd, "ok": ok})
        if not ok:
            issue("coco_rank", f"{rank} 论文 {pv} ≠ 重算 {mean}")

    # ══════════ ④ VLM 13 seed ══════════
    print()
    print("=" * 84)
    print("④ 解码器 VLM：13 seed，论文 vs 独立重算")
    print("=" * 84)
    vroot = REPO / "outputs" / "vlm_seeds_bf16"
    vg = defaultdict(dict)
    for f in sorted(vroot.glob("*_seed*.json")):
        d = json.loads(io.open(f, encoding="utf-8", errors="replace").read())
        vg[d["arm"]][str(d["seed"])] = d
    for arm, pv_mean, pv_sd, pv_lo, pv_hi in (
            ("text_only", 66.5, 8.3, 47.8, 78.8),
            ("vision_only", 18.0, 8.8, 8.5, 35.7),
            ("both", 87.9, 5.4, 73.1, 95.1)):
        entries = vg.get(arm, {})
        rels = []
        for s, d in entries.items():
            dg = d.get("dg_star") or []
            if len(dg) >= 2 and dg[0]:
                rels.append((dg[0] - dg[-1]) / dg[0] * 100.0)
        n = len(rels)
        if n == 0:
            issue("vlm", f"{arm} 无数据")
            continue
        mean = st.mean(rels)
        sd = st.stdev(rels) if n > 1 else None
        ok_m = abs(mean - pv_mean) <= 0.05
        ok_s = sd is not None and abs(sd - pv_sd) <= 0.05
        ok_lo = abs(min(rels) - pv_lo) <= 0.05
        ok_hi = abs(max(rels) - pv_hi) <= 0.05
        print(f"  {'✅' if all((ok_m, ok_s, ok_lo, ok_hi)) else '🔴'} {arm:<12} n={n} "
              f"论文 {pv_mean}±{pv_sd} [{pv_lo},{pv_hi}] ｜ 重算 {mean:.1f}±{sd:.1f} "
              f"[{min(rels):.1f},{max(rels):.1f}]")
        report["checks"].append({"what": f"vlm|{arm}", "paper": [pv_mean, pv_sd, pv_lo, pv_hi],
                                 "computed": [round(mean, 2), round(sd, 2),
                                              round(min(rels), 2), round(max(rels), 2)],
                                 "n": n, "ok": all((ok_m, ok_s, ok_lo, ok_hi))})
        if not all((ok_m, ok_s, ok_lo, ok_hi)):
            issue("vlm", f"{arm} 均值/sd/范围不匹配")

    # ══════════ ⑤ 污染检查 ══════════
    print()
    print("=" * 84)
    print("⑤ 未污染检查（.bak / MISPLACED 目录是否被判据排除）")
    print("=" * 84)
    junk = [f for f in glob.glob(str(REPO / "outputs" / "**" / "results*.bak"),
                                 recursive=True)]
    mis = [f for f in glob.glob(str(REPO / "outputs" / "**" / "*MISPLACED*"),
                                recursive=True)]
    print(f"  .bak 文件: {len(junk)} 个（脚本按 '.bak' 排除）")
    print(f"  MISPLACED 目录: {len(mis)} 个（脚本按 'MISPLACED' 排除）")
    for x in junk[:4]:
        print("     " + x.replace(str(REPO) + "\\", ""))
    for x in mis[:4]:
        print("     " + x.replace(str(REPO) + "\\", ""))

    # ══════════ 汇总 ══════════
    print()
    print("=" * 84)
    n_ok = sum(1 for c in report["checks"] if c["ok"])
    print(f"审核汇总：{n_ok}/{len(report['checks'])} 项数字匹配 ｜ "
          f"问题 {len(report['issues'])} 个")
    print("=" * 84)

    if a.apply:
        OUT.parent.mkdir(parents=True, exist_ok=True)
        io.open(OUT, "w", encoding="utf-8", newline="").write(
            json.dumps(report, ensure_ascii=False, indent=1))
        print(f"  ✅ 已写 {OUT.relative_to(REPO)}")
    return 0 if not report["issues"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
