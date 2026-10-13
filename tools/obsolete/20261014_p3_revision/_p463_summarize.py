# -*- coding: utf-8 -*-
r"""P3 F+G 组：把 `_p461` 的 rank sweep 汇总成**可引用表格与结论**（2026-10-12）。

只读 `outputs/analysis/p3d_clip_ranksweep.json`，不引入任何外部数字。

## 产出的三张表

1. **rank × 条件**：`dE_test`（真实 test 图上的对齐能量变化）与下游 `R@1` / `R@1_i2t`。
   → 回答 R3.14（真实图文下 rank transition 是否成立）
2. **blank vs real**：同 rank、同 n、同 seed 的配对比较。
   → 回答 R3.13（blank 是否 substantially simplify）
3. **能量变化 ↔ 下游变化**：把每个 run 的 `dE_test` 与 `ΔR@1`（相对冻结基线）
   配对，做符号检验 + 秩相关。
   → 回答 R1.3 / R2.3 / R3.15 / R3.16（energy 是否与真实下游表现相关）

    python tools\_p463_summarize.py [--apply]
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
SRC = REPO / "outputs" / "analysis" / "p3d_clip_ranksweep.json"
OUT = REPO / "outputs" / "analysis" / "p3d_summary.json"
MD = REPO / "outputs" / "analysis" / "p3d_tables.md"
FIG = REPO / "outputs" / "analysis" / "p3d_fig_ranksweep.png"


def agg(vals):
    vals = [v for v in vals if v is not None]
    if not vals:
        return None
    return {"mean": sum(vals) / len(vals),
            "std": (st.stdev(vals) if len(vals) > 1 else 0.0), "n": len(vals)}


def fingerprint(path: Path, n: int) -> dict:
    """来源指纹：文件 sha256 + 条数。

    派生聚合**必须**带上它——否则源归档日后被追加 run，这份 summary 的数字会静默变化，
    而引用者无从察觉（2026-10-13 流程规则：不要把聚合产物当来源）。
    """
    import hashlib
    return {"file": path.name, "sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
            "n_runs": n}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    a = ap.parse_args()

    d = json.loads(io.open(SRC, encoding="utf-8").read())
    runs = [r for r in d["runs"] if r["condition"] != "none"]
    base = [r for r in d["runs"] if r["condition"] == "none"]
    if not runs:
        print("!! 还没有 sweep 结果（runs 为空）")
        return 1
    baseline_r1 = base[0]["R@1"] if base else None
    baseline_r1_i2t = base[0]["R@1_i2t"] if base else None
    print(f"=== P3 F+G 汇总 === {len(runs)} run（+{len(base)} 冻结基线）")
    print(f"  冻结基线 R@1={baseline_r1:.4f} (i2t {baseline_r1_i2t:.4f})")

    # ---------- 表 1：rank × (condition, n) ----------
    cell = defaultdict(lambda: {"dE": [], "R@1": [], "R@1_i2t": [], "E0": [],
                                "dE_tr": [], "dE_ev": []})
    for r in runs:
        k = (r["condition"], r["n_train"], r["rank"])
        cell[k]["dE"].append(r["dE_test"])
        cell[k]["R@1"].append(r["R@1"])
        cell[k]["R@1_i2t"].append(r["R@1_i2t"])
        cell[k]["E0"].append(r["E_test_0"])
        if r.get("dE_train") is not None:
            cell[k]["dE_tr"].append(r["dE_train"])
    table = []
    for (cond, n, rank) in sorted(cell, key=lambda x: (x[0], x[1], x[2])):
        c = cell[(cond, n, rank)]
        table.append({"condition": cond, "n_train": n, "rank": rank,
                      "dE_train": agg(c["dE_tr"]),
                      "dE_test": agg(c["dE"]), "R@1": agg(c["R@1"]),
                      "R@1_i2t": agg(c["R@1_i2t"]), "E_test_0": agg(c["E0"]),
                      "dR@1_vs_frozen": agg([v - baseline_r1 for v in c["R@1"]])})

    # ---------- 秩翻转检测（每个 condition×n 的 rank 序列上找 dE 由负转正的最小 rank）----------
    flips = {}
    for key_name, col in (("dE_train", "dE_train"), ("dE_test", "dE_test")):
        per = {}
        for cond in sorted({r["condition"] for r in runs}):
            for n in sorted({r["n_train"] for r in runs}):
                seq = [(t["rank"], t[col]["mean"]) for t in table
                       if t["condition"] == cond and t["n_train"] == n and t[col]]
                seq.sort()
                if len(seq) < 2:
                    continue
                flip = None
                for i in range(1, len(seq)):
                    if seq[i - 1][1] <= 0 < seq[i][1]:
                        flip = [seq[i - 1][0], seq[i][0]]
                        break
                per[f"{cond}_n{n}"] = {"ranks": [s[0] for s in seq],
                                       "dE": [round(s[1], 4) for s in seq],
                                       "sign_flip_between": flip}
        flips[key_name] = per

    # ---------- 表 2：blank vs real 配对 ----------
    idx = {(r["condition"], r["n_train"], r["rank"], r["seed"], r["arm"]): r for r in runs}
    paired = []
    for (cond, n, rank, seed, arm), r in sorted(idx.items()):
        if cond != "real":
            continue
        b = idx.get(("blank", n, rank, seed, arm))
        if b is None:
            continue
        paired.append({"n_train": n, "rank": rank, "seed": seed,
                       "dE_real": r["dE_test"], "dE_blank": b["dE_test"],
                       "R1_real": r["R@1"], "R1_blank": b["R@1"],
                       "dR1_blank_minus_real": b["R@1"] - r["R@1"],
                       "dE_blank_minus_real": b["dE_test"] - r["dE_test"],
                       "E0_real": r["E_test_0"], "E0_blank": b["E_test_0"]})

    # 按 (n_train, rank) 汇总配对差
    pc = defaultdict(lambda: {"dE": [], "R1": [], "E0": []})
    for p in paired:
        k = (p["n_train"], p["rank"])
        pc[k]["dE"].append(p["dE_blank_minus_real"])
        pc[k]["R1"].append(p["dR1_blank_minus_real"])
        pc[k]["E0"].append(p["E0_blank"] - p["E0_real"])
    paired_by_cell = [{"n_train": k[0], "rank": k[1],
                       "dE_blank_minus_real": agg(v["dE"]),
                       "dR1_blank_minus_real": agg(v["R1"]),
                       "dE0_blank_minus_real": agg(v["E0"])}
                      for k, v in sorted(pc.items())]

    # ---------- 符号反转检验（每个训练量一个配对检验，不跨 n 混合）----------
    def paired_test(diffs):
        """配对差的均值/中位数/符号计数 + Wilcoxon 符号秩 p（双尾）。"""
        d = [v for v in diffs if v is not None]
        if len(d) < 5:
            return None
        pos = sum(1 for v in d if v > 0)
        neg = sum(1 for v in d if v < 0)
        out = {"n_pairs": len(d), "mean": sum(d) / len(d),
               "median": sorted(d)[len(d) // 2],
               "n_positive": pos, "n_negative": neg,
               "std": (st.stdev(d) if len(d) > 1 else 0.0)}
        try:
            from scipy.stats import wilcoxon
            if pos + neg >= 1:
                out["wilcoxon_p_two_sided"] = float(wilcoxon(d).pvalue)
        except Exception:
            out["wilcoxon_p_two_sided"] = None
        # 与 0 的 t 检验（配对）
        try:
            from scipy.stats import ttest_1samp
            out["ttest_p_two_sided"] = float(ttest_1samp(d, 0.0).pvalue)
        except Exception:
            out["ttest_p_two_sided"] = None
        return out

    sign_tests = {}
    for n in sorted({p["n_train"] for p in paired}):
        sub = [p for p in paired if p["n_train"] == n]
        sign_tests[f"n{n}"] = {
            "dE_test_blank_minus_real": paired_test([p["dE_blank_minus_real"] for p in sub]),
            "dR1_blank_minus_real": paired_test([p["dR1_blank_minus_real"] for p in sub]),
        }

    # ---------- 表 3：能量变化 ↔ 下游变化 ----------
    pairs = [(r["dE_test"], r["R@1"] - baseline_r1) for r in runs]
    x = [p[0] for p in pairs]
    y = [p[1] for p in pairs]
    # 训练集自身能量变化（= 论文 ΔE 的直接类比）与下游变化
    pairs_tr = [(r["dE_train"], r["R@1"] - baseline_r1) for r in runs
                if r.get("dE_train") is not None]

    def spearman(a_, b_):
        def ranks(v):
            o = sorted(range(len(v)), key=lambda i: v[i])
            rk = [0.0] * len(v)
            i = 0
            while i < len(o):
                j = i
                while j + 1 < len(o) and v[o[j + 1]] == v[o[i]]:
                    j += 1
                for t in range(i, j + 1):
                    rk[o[t]] = (i + j) / 2.0
                i = j + 1
            return rk
        rx, ry = ranks(a_), ranks(b_)
        mx, my = sum(rx) / len(rx), sum(ry) / len(ry)
        num = sum((p - mx) * (q - my) for p, q in zip(rx, ry))
        dx = sum((p - mx) ** 2 for p in rx) ** 0.5
        dy = sum((q - my) ** 2 for q in ry) ** 0.5
        return num / (dx * dy) if dx > 0 and dy > 0 else float("nan")

    rho = spearman(x, y)
    rho_tr = spearman([p[0] for p in pairs_tr], [p[1] for p in pairs_tr]) if len(pairs_tr) > 2 else None
    # 子集内相关：整体 Spearman 会被"符号分组"驱动，故必须单独报子集内的值
    dec_pairs = [(p[0], p[1]) for p in pairs if p[0] < 0]
    rho_dec = (spearman([p[0] for p in dec_pairs], [p[1] for p in dec_pairs])
               if len(dec_pairs) > 2 else None)
    real_only = [(r["dE_test"], r["R@1"] - baseline_r1) for r in runs
                 if r["condition"] == "real"]
    rho_real = (spearman([p[0] for p in real_only], [p[1] for p in real_only])
                if len(real_only) > 2 else None)
    dec = [yy for xx, yy in pairs if xx < 0]
    inc = [yy for xx, yy in pairs if xx > 0]
    energy_down = {"n": len(dec), "mean_dR1": (sum(dec) / len(dec)) if dec else None}
    energy_up = {"n": len(inc), "mean_dR1": (sum(inc) / len(inc)) if inc else None}
    mw_p = None
    try:
        from scipy.stats import mannwhitneyu
        if dec and inc:
            mw_p = float(mannwhitneyu(dec, inc, alternative="greater").pvalue)
    except Exception:
        pass

    result = {
        "experiment": "p3d_clip_ranksweep_summary",
        "script": "tools/_p463_summarize.py",
        "generated_at_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "source": "outputs/analysis/p3d_clip_ranksweep.json",
        "source_fingerprint": fingerprint(SRC, len(json.loads(
            io.open(SRC, encoding="utf-8").read())["runs"])),
        "derived_note": ("本文件是**派生聚合**，每次运行都会重算；引用具体数字请落到"
                         "p3d_clip_ranksweep.json :: runs[*]（只增不改），"
                         "并用 source_fingerprint.sha256 锁定当时的口径"),
        "n_runs_total": len(json.loads(io.open(SRC, encoding="utf-8").read())["runs"]),
        "n_runs_trained": len(runs),
        "n_runs_baseline_frozen": len(base),
        "n_runs_used_in_energy_downstream": len(pairs),
        "baseline_R@1": baseline_r1,
        "baseline_R@1_i2t": baseline_r1_i2t,
        "table_rank_condition": table,
        "sign_flip": flips,
        "paired_blank_vs_real": paired,
        "paired_by_cell": paired_by_cell,
        "paired_sign_tests": sign_tests,
        "energy_vs_downstream": {
            "spearman_dE_vs_dR1": rho, "n": len(pairs),
            "spearman_dE_train_vs_dR1": rho_tr, "n_train_pairs": len(pairs_tr),
            "spearman_within_energy_decrease_only": rho_dec, "n_energy_decrease": len(dec_pairs),
            "spearman_real_condition_only": rho_real, "n_real": len(real_only),
            "runs_with_energy_decrease": energy_down,
            "runs_with_energy_increase": energy_up,
            "mannwhitney_p_greater": mw_p,
        },
    }

    # ---------- 打印 ----------
    print("\n--- 表 1: rank × 条件（dE_train / dE_test / R@1，mean±std over seeds）---")
    for cond in sorted({t["condition"] for t in table}):
        for n in sorted({t["n_train"] for t in table}):
            rows = [t for t in table if t["condition"] == cond and t["n_train"] == n]
            if not rows:
                continue
            print(f"  [{cond}, n={n}]")
            for t in rows:
                de, r1, dtr = t["dE_test"], t["R@1"], t["dE_train"]
                s_tr = (f"{dtr['mean']:+9.4f}±{dtr['std']:7.4f}" if dtr
                        else "      n/a     ")
                print(f"    r={t['rank']:<3} dE_train={s_tr}  "
                      f"dE_test={de['mean']:+9.4f}±{de['std']:7.4f}  "
                      f"R@1={r1['mean']:.4f}±{r1['std']:.4f}  "
                      f"dR@1={t['dR@1_vs_frozen']['mean']:+.4f}")

    print("\n--- 秩翻转（dE 由 ≤0 转 >0 的最小 rank 区间）---")
    for cn, per in flips.items():
        for k, v in per.items():
            print(f"  [{cn}] {k:<12} 翻转区间={v['sign_flip_between']}  dE={v['dE']}")

    print("\n--- 表 2: blank vs real 配对（同类配置、同 seed）---")
    if paired:
        mdE = [p["dE_blank_minus_real"] for p in paired]
        mR1 = [p["dR1_blank_minus_real"] for p in paired]
        print(f"  n_pairs={len(paired)}  blank−real: dE {sum(mdE)/len(mdE):+.4f}, "
              f"R@1 {sum(mR1)/len(mR1):+.4f}")
        print("  按 (n, rank) 汇总：")
        for c in paired_by_cell:
            print(f"    n={c['n_train']:<5} r={c['rank']:<3} "
                  f"dE_blank−real={c['dE_blank_minus_real']['mean']:+.4f}"
                  f"±{c['dE_blank_minus_real']['std']:.4f}  "
                  f"dR@1={c['dR1_blank_minus_real']['mean']:+.4f}"
                  f"±{c['dR1_blank_minus_real']['std']:.4f}")
        print("  符号检验（按训练量，不跨 n 混合）：")
        for k, v in sign_tests.items():
            for name, t in v.items():
                if not t:
                    continue
                print(f"    {k} {name:<28} mean={t['mean']:+.5f} "
                      f"median={t['median']:+.5f} (+{t['n_positive']}/-{t['n_negative']}) "
                      f"wilcoxon p={t.get('wilcoxon_p_two_sided')}")

    print("\n--- 表 3: 能量变化 ↔ 下游变化 ---")
    print(f"  Spearman(dE_test, dR@1) = {rho:+.4f}  (n={len(pairs)})")
    print(f"  ├ 只在 ΔE_test<0 的 run 内: rho = {rho_dec}  (n={len(dec_pairs)})")
    print(f"  ├ 只看 real 条件的 run    : rho = {rho_real}  (n={len(real_only)})")
    print(f"  └ Spearman(dE_train, dR@1) = {rho_tr}  (n={len(pairs_tr)})")
    print(f"  dE<0 的 run: n={energy_down['n']}, 平均 dR@1={energy_down['mean_dR1']}")
    print(f"  dE>0 的 run: n={energy_up['n']}, 平均 dR@1={energy_up['mean_dR1']}")
    print(f"  Mann-Whitney（dE<0 的 dR@1 更大）p = {mw_p}")

    if not a.apply:
        print("\n（预演；加 --apply 写文件）")
        return 0

    io.open(OUT, "w", encoding="utf-8", newline="").write(
        json.dumps(result, ensure_ascii=False, indent=1))
    lines = ["# P3 F+G 补实验汇总（自动生成，勿手改）", "",
             f"来源：`{result['source']}`；脚本 `{result['script']}`；"
             f"生成 {result['generated_at_utc']}", "",
             f"冻结基线 R@1 = {baseline_r1:.4f}（i2t {baseline_r1_i2t:.4f}）", "",
             "## 表 1 rank × 条件", "",
             "| 条件 | n_train | rank | dE_train | dE_test | R@1 | R@1_i2t | ΔR@1 vs 冻结 |",
             "|---|---|---|---|---|---|---|---|"]
    for t in table:
        dtr = t["dE_train"]
        s_tr = (f"{dtr['mean']:+.4f}±{dtr['std']:.4f}" if dtr else "n/a")
        lines.append(f"| {t['condition']} | {t['n_train']} | {t['rank']} | {s_tr} | "
                     f"{t['dE_test']['mean']:+.4f}±{t['dE_test']['std']:.4f} | "
                     f"{t['R@1']['mean']:.4f}±{t['R@1']['std']:.4f} | "
                     f"{t['R@1_i2t']['mean']:.4f} | "
                     f"{t['dR@1_vs_frozen']['mean']:+.4f} |")
    lines += ["", "## 秩翻转", "", "| 能量口径 | 配置 | dE 序列 | 翻转区间 |", "|---|---|---|---|"]
    for cn, per in flips.items():
        for k, v in per.items():
            lines.append(f"| {cn} | {k} | {v['dE']} | {v['sign_flip_between']} |")
    lines += ["", "## 表 3 能量 ↔ 下游", "",
              f"- Spearman(ΔE_test, ΔR@1) = **{rho:+.4f}** (n={len(pairs)})",
              f"- Spearman(ΔE_train, ΔR@1) = **{rho_tr}** (n={len(pairs_tr)})",
              f"- ΔE<0 的 run：n={energy_down['n']}，平均 ΔR@1 = "
              f"{energy_down['mean_dR1']:+.4f}" if energy_down["mean_dR1"] is not None
              else "- ΔE<0 的 run：无",
              f"- ΔE>0 的 run：n={energy_up['n']}，平均 ΔR@1 = "
              f"{energy_up['mean_dR1']:+.4f}" if energy_up["mean_dR1"] is not None
              else "- ΔE>0 的 run：无",
              f"- Mann-Whitney p = {mw_p}"]
    io.open(MD, "w", encoding="utf-8", newline="").write("\n".join(lines) + "\n")

    # ---------- 图 ----------
    try:
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
        conds = sorted({t["condition"] for t in table})
        ns = sorted({t["n_train"] for t in table})
        fig, axes = plt.subplots(1, 3, figsize=(15, 4.2))
        for cond in conds:
            for n, ls in zip(ns, ["-o", "--s", ":^", "-.d"]):
                rows = sorted([t for t in table if t["condition"] == cond
                               and t["n_train"] == n], key=lambda t: t["rank"])
                if not rows:
                    continue
                axes[0].errorbar([t["rank"] for t in rows],
                                 [t["dE_train"]["mean"] if t["dE_train"] else 0.0
                                  for t in rows],
                                 yerr=[t["dE_train"]["std"] if t["dE_train"] else 0.0
                                       for t in rows],
                                 fmt=ls, label=f"{cond} n={n}", capsize=2)
                axes[1].errorbar([t["rank"] for t in rows],
                                 [t["R@1"]["mean"] for t in rows],
                                 yerr=[t["R@1"]["std"] for t in rows],
                                 fmt=ls, label=f"{cond} n={n}", capsize=2)
        axes[0].axhline(0, color="k", lw=0.8)
        axes[0].set_xscale("log", base=2); axes[0].set_xlabel("LoRA rank r")
        axes[0].set_ylabel(r"$\Delta E_{\rm train}$ (on the run's own condition)")
        axes[0].set_title("Alignment energy change vs rank", fontsize=10)
        axes[1].set_xscale("log", base=2); axes[1].set_xlabel("LoRA rank r")
        axes[1].set_ylabel("Flickr30k R@1 (i2t+t2i)/2")
        axes[1].set_title("Downstream retrieval vs rank", fontsize=10)
        if baseline_r1:
            axes[1].axhline(baseline_r1, color="k", lw=0.8, ls=":",
                            label="frozen baseline")
        axes[2].scatter(x, y, s=12)
        axes[2].axhline(0, color="k", lw=0.8); axes[2].axvline(0, color="k", lw=0.8)
        axes[2].set_xlabel(r"$\Delta E_{\rm test}$ (held-out real test images)")
        axes[2].set_ylabel(r"$\Delta$R@1 vs frozen")
        axes[2].set_title(f"Energy change vs downstream change\n"
                          f"Spearman = {rho:+.3f} (overall, n={len(pairs)}); "
                          f"within $\\Delta E<0$: {rho_dec:+.3f}", fontsize=9)
        for ax in axes[:2]:
            ax.legend(fontsize=7); ax.grid(alpha=0.3)
        axes[2].grid(alpha=0.3)
        fig.suptitle("P3 F+G: CLIP ViT-B/32 rank sweep, real image-text vs blank",
                     fontsize=11)
        fig.tight_layout()
        fig.savefig(FIG, dpi=150)
        print(f"  ✅ 图已写 {FIG.relative_to(REPO)}")
    except Exception as e:
        print(f"  ⚠️ 画图失败（不影响 JSON/MD）：{type(e).__name__}: {e}")

    print(f"\n  ✅ 已写 {OUT.relative_to(REPO)} 与 {MD.relative_to(REPO)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
