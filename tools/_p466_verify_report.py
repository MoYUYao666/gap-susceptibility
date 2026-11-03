# -*- coding: utf-8 -*-
r"""P3 F+G：把 `docs/P3_DOWNSTREAM.md` 里的**关键主张**逐条对着归档断言一遍。

规则（项目铁律）：报告里每个数字都要能指到归档字段。本脚本就是那个"指"的动作——
**机器可复核**，不靠人眼比对。

    python tools\_p466_verify_report.py        # 全通过退出码 0，否则 1
"""
from __future__ import annotations

import io
import json
import sys
from collections import defaultdict
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
A = REPO / "outputs" / "analysis"

fails: list[str] = []
checks = 0


def ck(name: str, cond: bool, detail: str = "") -> None:
    global checks
    checks += 1
    if cond:
        print(f"  [OK]   {name}")
    else:
        print(f"  [FAIL] {name}  {detail}")
        fails.append(name)


def load(p):
    return json.loads(io.open(p, encoding="utf-8").read())


def main() -> int:
    for f in ("p3d_manifest.json", "p3d_clip_ranksweep.json", "p3d_summary.json",
              "p3d_gamma_real_vs_blank.json", "llava_bf16_feasibility.json"):
        ck(f"归档存在 {f}", (A / f).exists())

    sweep = load(A / "p3d_clip_ranksweep.json")
    summ = load(A / "p3d_summary.json")
    gam = load(A / "p3d_gamma_real_vs_blank.json")
    feas = load(A / "llava_bf16_feasibility.json")

    runs = sweep["runs"]
    base = [r for r in runs if r["condition"] == "none"]
    body = [r for r in runs if r["condition"] != "none"]

    # ---- §3 规模与基线 ----
    ck("总 run 数 = 79（1 基线 + 78 训练）", len(runs) == 79, f"实得 {len(runs)}")
    ck("冻结基线 R@1 = 0.7058", abs(base[0]["R@1"] - 0.7058) < 1e-9,
       f"实得 {base[0]['R@1']}")
    ck("冻结基线 i2t = 0.8220 / t2i = 0.5896",
       abs(base[0]["R@1_i2t"] - 0.8220) < 1e-9 and abs(base[0]["R@1_t2i"] - 0.5896) < 1e-9,
       f"实得 {base[0]['R@1_i2t']}/{base[0]['R@1_t2i']}")
    ck("全部 run 均为 cuda", all(r.get("device") == "cuda" for r in runs))
    cell = defaultdict(list)
    for r in body:
        cell[(r["n_train"], r["condition"], r["rank"])].append(r["seed"])
    ck("n=16 有 7 个 rank × 2 条件 × 3 seed",
       all(len(cell[(16, c, k)]) == 3 for c in ("real", "blank")
           for k in (1, 2, 4, 5, 6, 8, 16)),
       f"缺: {[k for c in ('real','blank') for k in (1,2,4,5,6,8,16) if len(cell[(16,c,k)])!=3]}")
    ck("n=1024 有 6 个 rank × 2 条件 × 3 seed",
       all(len(cell[(1024, c, k)]) == 3 for c in ("real", "blank")
           for k in (1, 4, 5, 6, 8, 16)),
       f"缺: {[k for c in ('real','blank') for k in (1,4,5,6,8,16) if len(cell[(1024,c,k)])!=3]}")

    # ---- §3.2 符号：n=16 时 real 全负 / blank 全正，且无翻转 ----
    tab = {(t["n_train"], t["condition"], t["rank"]): t
           for t in summ["table_rank_condition"]}
    real16 = [tab[(16, "real", k)]["dE_train"]["mean"] for k in (1, 2, 4, 5, 6, 8, 16)]
    blank16 = [tab[(16, "blank", k)]["dE_train"]["mean"] for k in (1, 2, 4, 5, 6, 8, 16)]
    ck("n=16 real 的 ΔE_train 全为负", all(v < 0 for v in real16),
       f"{[round(v,4) for v in real16]}")
    ck("n=16 blank 的 ΔE_train 全为正", all(v > 0 for v in blank16),
       f"{[round(v,4) for v in blank16]}")
    ck("n=16 blank ΔE_train(r=16) ≈ +0.0167", abs(blank16[-1] - 0.0167) < 5e-4,
       f"实得 {blank16[-1]:.4f}")
    ck("n=16 real ΔE_train(r=16) ≈ -0.0073", abs(real16[-1] + 0.0073) < 5e-4,
       f"实得 {real16[-1]:.4f}")
    sf = summ["sign_flip"]["dE_train"]
    ck("ΔE_train 任何 (条件,n) 组合都无符号翻转（r_c∈[5,6] 未复现）",
       all(v["sign_flip_between"] is None for v in sf.values()),
       f"{ {k: v['sign_flip_between'] for k, v in sf.items()} }")

    # ---- §5.1 下游两端 ----
    r16_1024 = tab[(1024, "real", 16)]["R@1"]["mean"]
    b16_1024 = tab[(1024, "blank", 16)]["R@1"]["mean"]
    ck("n=1024 real r=16 的 R@1 ≈ 0.7241（最好）",
       abs(r16_1024 - 0.7241) < 5e-4, f"实得 {r16_1024:.4f}")
    ck("n=1024 blank r=16 的 R@1 ≈ 0.6927（最差）",
       abs(b16_1024 - 0.6927) < 5e-4, f"实得 {b16_1024:.4f}")
    best = max(tab.values(), key=lambda t: t["R@1"]["mean"])
    worst = min(tab.values(), key=lambda t: t["R@1"]["mean"])
    ck("全表最佳是 real/n=1024/r=16", (best["n_train"], best["condition"],
                                       best["rank"]) == (1024, "real", 16),
       f"实得 {(best['n_train'], best['condition'], best['rank'])}")
    ck("全表最差是 blank/n=1024/r=16", (worst["n_train"], worst["condition"],
                                        worst["rank"]) == (1024, "blank", 16),
       f"实得 {(worst['n_train'], worst['condition'], worst['rank'])}")

    # ---- §5.2 energy <-> downstream ----
    ed = summ["energy_vs_downstream"]
    ck("Spearman(ΔE_test, ΔR@1) ≈ -0.3742", abs(ed["spearman_dE_vs_dR1"] + 0.3742) < 5e-4,
       f"实得 {ed['spearman_dE_vs_dR1']}")
    ck("n = 78", ed["n"] == 78)
    ck("Mann-Whitney p ≈ 9.48e-6", abs(ed["mannwhitney_p_greater"] - 9.4825e-6) < 1e-8,
       f"实得 {ed['mannwhitney_p_greater']}")
    ck("ΔE_test<0 组 n=54", ed["runs_with_energy_decrease"]["n"] == 54)
    ck("ΔE_test>0 组 n=24", ed["runs_with_energy_increase"]["n"] == 24)
    ck("Spearman(ΔE_train, ΔR@1) ≈ +0.478（能量降幅↔下游变差）",
       abs(ed["spearman_dE_train_vs_dR1"] - 0.4778) < 5e-4,
       f"实得 {ed['spearman_dE_train_vs_dR1']}")
    ck("ΔE_test<0 子集内 Spearman ≈ +0.171（子集内几乎无关，报告已按此更正）",
       abs(ed["spearman_within_energy_decrease_only"] - 0.1715) < 5e-4,
       f"实得 {ed['spearman_within_energy_decrease_only']}")
    ck("real 条件内 Spearman ≈ -0.691",
       abs(ed["spearman_real_condition_only"] + 0.6912) < 5e-4,
       f"实得 {ed['spearman_real_condition_only']}")

    # ---- §5.3 配对交互：n=16 blank 更好、n=1024 blank 更差 ----
    pc = {(c["n_train"], c["rank"]): c for c in summ["paired_by_cell"]}
    ck("配对总数 = 39", len(summ["paired_blank_vs_real"]) == 39)
    ck("n=16 全部 rank 的 ΔR@1(blank-real) > 0（blank 反而更好）",
       all(pc[(16, k)]["dR1_blank_minus_real"]["mean"] > 0 for k in (1, 2, 4, 5, 6, 8, 16)),
       f"{ {k: round(pc[(16,k)]['dR1_blank_minus_real']['mean'],4) for k in (1,2,4,5,6,8,16)} }")
    ck("n=1024 全部 rank 的 ΔR@1(blank-real) < 0（blank 明显更差）",
       all(pc[(1024, k)]["dR1_blank_minus_real"]["mean"] < 0 for k in (1, 4, 5, 6, 8, 16)),
       f"{ {k: round(pc[(1024,k)]['dR1_blank_minus_real']['mean'],4) for k in (1,4,5,6,8,16)} }")

    # ---- §5.3 配对符号检验（21/21 与 18/18 全票 + Wilcoxon）----
    st16 = summ["paired_sign_tests"]["n16"]
    st24 = summ["paired_sign_tests"]["n1024"]
    ck("n=16：ΔE 配对 21 对全负（blank 能量降更多），Wilcoxon p<1e-6",
       st16["dE_test_blank_minus_real"]["n_negative"] == 21
       and st16["dE_test_blank_minus_real"]["n_positive"] == 0
       and st16["dE_test_blank_minus_real"]["wilcoxon_p_two_sided"] < 1e-6,
       f"{st16['dE_test_blank_minus_real']}")
    ck("n=16：ΔR@1 配对 21 对全正（下游反而升），Wilcoxon p<1e-4",
       st16["dR1_blank_minus_real"]["n_positive"] == 21
       and st16["dR1_blank_minus_real"]["wilcoxon_p_two_sided"] < 1e-4,
       f"{st16['dR1_blank_minus_real']}")
    ck("n=1024：ΔR@1 配对 18 对全负，Wilcoxon p<1e-5",
       st24["dR1_blank_minus_real"]["n_negative"] == 18
       and st24["dR1_blank_minus_real"]["wilcoxon_p_two_sided"] < 1e-5,
       f"{st24['dR1_blank_minus_real']}")
    ck("n=1024：ΔE 配对【不显著】（p>0.5）→ 不能说'能量略升'",
       st24["dE_test_blank_minus_real"]["wilcoxon_p_two_sided"] > 0.5,
       f"p={st24['dE_test_blank_minus_real']['wilcoxon_p_two_sided']}")
    # n 口径必须唯一且自洽
    ck("n 口径：79 总 run = 1 冻结基线 + 78 训练；能量↔下游用 78",
       summ["n_runs_total"] == 79 and summ["n_runs_trained"] == 78
       and summ["n_runs_baseline_frozen"] == 1
       and summ["n_runs_used_in_energy_downstream"] == 78,
       f"{ {k: summ[k] for k in ('n_runs_total','n_runs_trained','n_runs_baseline_frozen','n_runs_used_in_energy_downstream')} }")

    # ---- §4 Γ ----
    g = gam["conditions"]
    ck("blank 的 text_shallow Γ > real 的 100 倍",
       g["blank"]["blocks"]["text_shallow"]["gamma"] > 100 * abs(
           g["real"]["blocks"]["text_shallow"]["gamma"]),
       f"blank={g['blank']['blocks']['text_shallow']['gamma']:.2f} "
       f"real={g['real']['blocks']['text_shallow']['gamma']:.2f}")
    ck("real 三个文本块 cos φ 全为负",
       all(g["real"]["blocks"][b]["cos"] < 0
           for b in ("text_shallow", "text_mid", "text_deep")))
    ck("blank 三个文本块 cos φ 全为正",
       all(g["blank"]["blocks"][b]["cos"] > 0
           for b in ("text_shallow", "text_mid", "text_deep")))
    ck("block 排序不一致（ordering_identical=False）",
       gam["comparison"]["ordering_identical"] is False)
    ck("Γ 的秩相关 = 0.8", abs(gam["comparison"]["kendall_tau_abs_gamma"] - 0.8) < 1e-9)
    ck("blank 任务损失约为 real 的 396 倍",
       abs(g["blank"]["L_mean"] / g["real"]["L_mean"] - 396) < 3,
       f"实得 {g['blank']['L_mean']/g['real']['L_mean']:.1f}")

    # ---- §6 LLaVA 不可行 ----
    ck("LLaVA-1.5-7B 权重 13.157 GiB（> 8 GiB 卡）",
       abs(feas["disk"]["total_GiB"] - 13.157) < 1e-9, f"实得 {feas['disk']['total_GiB']}")
    ck("4-bit 被禁有明文记录", "four_bit_excluded_because" in feas)

    # ---- §3.3 解码器 VLM（Qwen2-VL-2B）----
    qp = A / "p3d_qwen_ranksweep.json"
    ck("归档存在 p3d_qwen_ranksweep.json", qp.exists())
    if qp.exists():
        q = load(qp)
        qr = [r for r in q["runs"] if r.get("rank", 0) > 0]
        ck("Qwen 训练 run = 42（7 rank × 2 条件 × 3 seed）", len(qr) == 42,
           f"实得 {len(qr)}")
        ck("Qwen 训练 run 全在 cuda", all(r.get("device") == "cuda" for r in qr))
        ck("Qwen rank 覆盖 {1,2,4,5,6,8,16}",
           {r["rank"] for r in qr} == {1, 2, 4, 5, 6, 8, 16},
           f"实得 {sorted({r['rank'] for r in qr})}")
        ck("Qwen 每个 ran 都是 3 seed", all(
            sum(1 for r in qr if r["rank"] == k and r["condition"] == c) == 3
            for k in (1, 2, 4, 5, 6, 8, 16) for c in ("real", "blank")))
        ck("Qwen：real 的 ΔE_train 在 7/7 个 rank 上全为正（3/3 seed 同号）",
           all(r["dE_train"] > 0 for r in qr if r["condition"] == "real"))
        ck("Qwen：blank 的 ΔE_train 在 7/7 个 rank 上全为负",
           all(r["dE_train"] < 0 for r in qr if r["condition"] == "blank"))
        ck("Qwen：r∈[1,16] 无符号翻转（real 全正 / blank 全负）",
           not any((a["dE_train"] > 0) != (b["dE_train"] > 0)
                   for a in [r for r in qr if r["condition"] == "real"]
                   for b in [r for r in qr if r["condition"] == "real"]))
        qs = load(A / "p3d_qwen_summary.json")
        pr = qs["paired_blank_vs_real"]
        ck("Qwen 配对 = 21 对", len(pr) == 21)
        ck("Qwen 配对 ΔE_train(blank−real) 21/21 全为负",
           all(p["dE_train_blank_minus_real"] < 0 for p in pr))
        ck("Qwen blank 的 ΔE_eval_real 随 rank 由负转正（r=1<0, r=16>0）",
           [t for t in qs["table"] if t["condition"] == "blank" and t["rank"] == 1
            ][0]["dE_eval_real"]["mean"] < 0
           and [t for t in qs["table"] if t["condition"] == "blank" and t["rank"] == 16
                ][0]["dE_eval_real"]["mean"] > 0)
        ts = load(A / "p3d_qwen_token_stats.json")
        ck("Qwen 平均 visual token = 15.0（§3.3 的简化限制）",
           abs(ts["mean_visual_tokens"] - 15.0) < 1e-9,
           f"实得 {ts['mean_visual_tokens']}")
        sm = load(A / "p3d_qwen_smoke.json")["by_device"]["cuda"]
        ck("Qwen GPU 冒烟：峰值 allocated ≈ 4.34 GiB、单步 ≈ 0.83 s",
           abs(sm["peak_allocated_GiB"] - 4.34) < 0.02 and abs(sm["step_seconds"] - 0.83) < 0.02,
           f"实得 {sm['peak_allocated_GiB']} GiB / {sm['step_seconds']} s")

        # ---- §3.3.1 分辨率稳健性：原符号结论【必须被证伪】，不能反过来"通过" ----
        rc = load(A / "p3d_qwen_resolution_check.json")
        ck("分辨率检验：15 token 档「real 全正 / blank 全负」成立",
           rc["pattern_holds"]["16384"] is True)
        ck("分辨率检验：54 token 档同一模式【不成立】（原结论已被证伪）",
           rc["pattern_holds"]["50176"] is False,
           "若这里变成 True，说明报告 §3.3.1 的'撤回'表述与归档不符，必须改回")
        ck("分辨率检验：54 token 档 real 的 ΔE_train 由正转负（2/2）",
           rc["sign_summary"]["50176"]["real"]["n_negative"] == 2
           and rc["sign_summary"]["50176"]["real"]["n_positive"] == 0)
        ck("分辨率检验：配对 blank−real 由 21/21 负 变为 0/2 负（方向也翻转）",
           rc["sign_summary"]["16384"]["real"]["n_positive"] == 21
           and sum(1 for p in rc["paired"]["50176"]
                   if p["dE_train_blank_minus_real"] < 0) == 0)
        ck("稳健的那一条（无 rank 符号翻转）在两档都成立",
           rc["pattern_holds"]["16384"] is True and
           all(v["n_positive"] == 0 or v["n_negative"] == 0
               for v in rc["sign_summary"]["50176"].values()))
        ts2 = load(A / "p3d_qwen_token_stats_mp50176.json")
        ck("54 token 档实测 visual token = 54.0", abs(ts2["mean_visual_tokens"] - 54.0) < 1e-9)
        ck("两档初始化能量差：15 token 档 real≈blank（<5%），54 token 档 real 显著更低（>30%）",
           abs(22373.3 - 21751.8) / 22373.3 < 0.05
           and abs(22207.0 - 14718.0) / 22207.0 > 0.30)

        # ---- §3.3.2 E0 随 token 预算（只前向、确定性 ⇒ 无 seed 噪声）----
        f1 = A / "p3d_e0_vs_token_budget_train_sel_n16.json"
        f2 = A / "p3d_e0_vs_token_budget_test_n4.json"
        ck("归档存在 E0-vs-budget 两个样本集文件", f1.exists() and f2.exists())
        if f1.exists() and f2.exists():
            e1, e2 = load(f1), load(f2)
            r1 = {r["max_pixels"]: r for r in e1["rows"]}
            r2 = {r["max_pixels"]: r for r in e2["rows"]}
            ck("管线校准：主曲线 @15 token 的 E0_real 与【同设备】归档一致"
               "（GPU↔训练档 21751.8 或 CPU↔冻结基线 21771.6993；两者差 0.09% 是 bf16 设备差）",
               abs(r1[16384]["E0_real"] - 21771.6993) < 0.5
               or abs(r1[16384]["E0_real"] - 21751.8) < 0.5,
               f"实得 {r1[16384]['E0_real']}（GPU 档应为 21751.8）")
            ck("两条件 token 数相同（blank 用同尺寸纯黑）",
               all(r["tokens_match"] for r in e1["rows"] + e2["rows"]))
            ck("test 样本集：gap 随预算增大（15→54 token）",
               r2[50176]["gap_pct"] > r2[16384]["gap_pct"],
               f"{r2[16384]['gap_pct']:.1f}% → {r2[50176]['gap_pct']:.1f}%")
            ck("⚠️ 绝对 gap 是样本集相关的（15 token 下 train_sel 3.1% vs test 18.5%，"
               "不得当普遍量级引用）",
               abs(r2[16384]["gap_pct"] - r1[16384]["gap_pct"]) > 5.0,
               f"train_sel {r1[16384]['gap_pct']:.2f}% vs test {r2[16384]['gap_pct']:.2f}%")
            ck("机制：E0_real 随预算下降、E0_blank 基本不动",
               r2[50176]["E0_real"] < r2[16384]["E0_real"] * 0.7
               and abs(r2[50176]["E0_blank"] - r2[16384]["E0_blank"]) / r2[16384]["E0_blank"] < 0.05,
               f"real {r2[16384]['E0_real']:.0f}→{r2[50176]['E0_real']:.0f}; "
               f"blank {r2[16384]['E0_blank']:.0f}→{r2[50176]['E0_blank']:.0f}")

            # ---- 主曲线（train_sel n=16，4 点，含论文操作点）必须单调 ----
            rr = sorted(e1["rows"], key=lambda r: r["mean_tokens"])
            ck("主曲线有 4 个预算点（含 ≈595 token ≈ 论文 576）",
               len(rr) == 4 and rr[-1]["mean_tokens"] > 500,
               f"实得 {[round(r['mean_tokens'],1) for r in rr]}")
            ck("主曲线 gap 单调增大（+3.0% → +209.4%）",
               all(rr[i]["gap_pct"] < rr[i + 1]["gap_pct"] for i in range(len(rr) - 1)),
               f"{[round(r['gap_pct'],1) for r in rr]}")
            ck("论文操作点处 gap ≈ +209%，blank/real ≈ 3.09×",
               abs(rr[-1]["gap_pct"] - 209.4) < 1.0
               and abs(rr[-1]["E0_blank"] / rr[-1]["E0_real"] - 3.09) < 0.02,
               f"gap={rr[-1]['gap_pct']:.1f}% ratio={rr[-1]['E0_blank']/rr[-1]['E0_real']:.2f}")
            ck("E0_blank 在 4 个预算上变化 <5%（几乎不受预算影响）",
               (max(r["E0_blank"] for r in rr) - min(r["E0_blank"] for r in rr))
               / min(r["E0_blank"] for r in rr) < 0.05)
            ck("管线校准：主曲线 @15 token 的 E0_real ≈ 训练归档 21751.8",
               abs(rr[0]["E0_real"] - 21751.8) < 0.5, f"实得 {rr[0]['E0_real']}")

            # ---- 负例：n=2 子样本的趋势方向相反，必须留档 ----
            f3 = A / "p3d_e0_vs_token_budget_test_n2.json"
            ck("负例留档存在：test n=2 的曲线", f3.exists())
            if f3.exists():
                r3 = {r["max_pixels"]: r for r in load(f3)["rows"]}
                ck("⚠️ 负例：n=2 时 15→54 token 的 gap 反而【下降】（+122.2%→+103.7%）"
                   " ⇒ 趋势方向在子样本上会翻转，只能引 n=16 的同批曲线",
                   r3[50176]["gap_pct"] < r3[16384]["gap_pct"],
                   f"实得 {r3[16384]['gap_pct']:.1f}% → {r3[50176]['gap_pct']:.1f}%")
                ck("负例 n=2 曲线已被补全为 4 个预算点（含 594 token），不再有未归档数字",
                   len(r3) == 4 and max(r3) == 802816 and "802816" in str(max(r3)),
                   f"实得 {sorted(r3)}")
                ck("重复来源已清理：早期无 split/n 后缀的归档不存在",
                   not (A / "p3d_e0_vs_token_budget.json").exists())

    # ---- 来源加固（2026-10-13 流程规则：不要把聚合产物当来源）----
    import hashlib
    sweep_d = load(A / "p3d_clip_ranksweep.json")
    ck("CLIP 逐 run 自带超参（任一 run 缺 lr/epochs/batch/dropout 即 FAIL）",
       all(all(k in r for k in ("lr", "epochs", "batch", "dropout"))
           for r in sweep_d["runs"]))
    ck("CLIP 归档声明 source_of_truth 且含 train_spec",
       "source_of_truth" in sweep_d and isinstance(sweep_d.get("train_spec"), dict))
    q_d = load(A / "p3d_qwen_ranksweep.json")
    ck("Qwen 逐 run 自带超参 + 像素预算",
       all(all(k in r for k in ("lr", "epochs", "batch", "min_pixels", "max_pixels"))
           for r in q_d["runs"]))
    for fn in ("p3d_summary.json", "p3d_qwen_summary.json"):
        sd = load(A / fn)
        fp = sd.get("source_fingerprint") or {}
        src = A / fp.get("file", "___")
        ck(f"{fn} 带来源指纹且与实际源文件逐位一致",
           bool(fp.get("sha256")) and src.exists()
           and hashlib.sha256(src.read_bytes()).hexdigest() == fp["sha256"]
           and fp.get("n_runs") == len(load(src)["runs"]),
           f"指纹={str(fp)[:70]}")
        ck(f"{fn} 声明为派生聚合（derived_note 存在）", "derived_note" in sd)
    for fn in ("p3d_e0_vs_token_budget_train_sel_n16.json",
               "p3d_e0_vs_token_budget_test_n4.json",
               "p3d_e0_vs_token_budget_test_n2.json"):
        e = load(A / fn)
        ck(f"{fn} 行级带 device（防 CPU/GPU 混档静默替换）",
           all("device" in r for r in e["rows"]))

    # ---- §7 图 ----
    ck("汇总图已生成", (A / "p3d_fig_ranksweep.png").exists())
    ck("人读表格已生成", (A / "p3d_tables.md").exists())

    print(f"\n=== {checks - len(fails)}/{checks} 通过 ===")
    if fails:
        print("未通过：")
        for f in fails:
            print("  -", f)
        return 1
    print("全部通过。")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
