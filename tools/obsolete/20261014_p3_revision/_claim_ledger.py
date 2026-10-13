# -*- coding: utf-8 -*-
r"""**主张台账**：稿件每个关键数字 → 命名脚本 → 归档 JSON 字段（2026-10-07）。

## 为什么不用自动匹配

`tools/_reproducibility_gate.py` 的自动匹配**是假门禁**：
归档有 **122,161 个数值**，任何数字都能在 0.5% 容差内随机命中 → **145/145 通过纯属假象**。
（**这是我自己设计的工具，我否掉它**。）

## 正确做法

**人工核对**：每个数字**指名出处**（脚本 + JSON 字段），脚本**逐条断言**。
未列入台账的数字 = **未验证** → 必须补出处或从稿件删除。

**判据**：`assert` 全部通过 → 台账可信；任一条失败 → 该数字无来源，需处理。

    python tools\_claim_ledger.py [--apply]
"""
from __future__ import annotations

import glob
import io
import json
import statistics as st
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
OUT = REPO / "outputs" / "analysis" / "claim_ledger.json"

try:
    import numpy as np
except Exception:
    np = None


def grid_fit(t, y):
    t = np.asarray(t, float); y = np.asarray(y, float)
    dg0 = float(y[0]); r = y - dg0
    best = (float("nan"), float("nan"), float("inf"))
    for logb in np.linspace(np.log10(0.005), np.log10(20.0), 800):
        b = 10.0 ** logb
        u = 1.0 - np.exp(-b * t); den = float((u * u).sum())
        if den < 1e-12:
            continue
        a = float((u * r).sum()) / den
        resid = float(((r - a * u) ** 2).sum())
        if resid < best[2]:
            best = (a * b, b, resid)
    A, B, _ = best
    yh = dg0 + (A / B) * (1.0 - np.exp(-B * t))
    ss = float(((y - y.mean()) ** 2).sum())
    return float(A), float(B), 1.0 - float(((y - yh) ** 2).sum()) / ss if ss > 0 else float("nan")


def main() -> int:
    apply = "--apply" in sys.argv
    ok = bad = 0
    ledger = []

    def claim(name: str, manuscript: float, computed: float, source: str, tol=0.002):
        nonlocal ok, bad
        good = abs(manuscript - computed) <= tol
        ledger.append({"claim": name, "manuscript": manuscript, "computed": round(computed, 6),
                       "source": source, "pass": bool(good)})
        print(f"  {'✅' if good else '❌'} {name:<44} 稿件 {manuscript:<10} 实测 {computed:<10.6f} ← {source}")
        if good:
            ok += 1
        else:
            bad += 1

    # ── ① 严格冻结三臂（CLIP B/32）
    sc = json.loads(io.open(REPO / "outputs/analysis/strict_control_summary.json",
                            encoding="utf-8").read())
    claim("严格冻结 text_only CGΔ", -0.0465, sc["configs"]["text_only"]["cg_delta_mean"],
          "strict_control_summary.json:configs.text_only.cg_delta_mean")
    claim("严格冻结 both CGΔ", -0.0258, sc["configs"]["both"]["cg_delta_mean"],
          "...configs.both.cg_delta_mean")
    claim("严格冻结 vision_only CGΔ", +0.0106, sc["configs"]["vision_only"]["cg_delta_mean"],
          "...configs.vision_only.cg_delta_mean")

    # ── ①b 表格新增两行（同秩对照，2026-10-08 加入 tab:position_strict）──
    # 表值为 **5-seed 均值，batch 128**（2026-10-11 起；此前 3 seed，见表注）
    import statistics as _st
    NEW_ROWS = {
        "CLIP B/32@r4": ("outputs/strict_freeze_b32_r4",
                         {"text_only": (-0.030382, 0.621), "both": (-0.020375, 0.679),
                          "vision_only": (+0.016577, 0.670)}),
        "CLIP B/16@r4": ("outputs/strict_freeze_b16/r4",
                         {"text_only": (-0.016574, 0.651), "both": (+0.012357, 0.707),
                          "vision_only": (+0.037551, 0.686)}),
    }
    for _tag, (_root, _arms) in NEW_ROWS.items():
        for _arm, (_pcg, _pr1) in _arms.items():
            _fs = sorted(glob.glob(str(REPO / _root / _arm / "seed*" / "results.json")))
            assert _fs, f"缺归档: {_root}/{_arm}"
            _cgs, _r1s = [], []
            for _f in _fs:
                _d = json.loads(io.open(_f, encoding="utf-8").read())
                _cgs.append(_d["final_gap"]["centroid_gap"]
                            - _d["initial_gap"]["centroid_gap"])
                _r1s.append(_d["final_task_metrics"]["R@1"])
            _cg = _st.mean(_cgs)
            _r1 = _st.mean(_r1s)
            claim(f"{_tag} {_arm} CGΔ(3seed均值)", _pcg, _cg,
                  f"{_root}/{_arm}/*/results.json: mean over {len(_fs)} seeds", tol=0.0006)
            claim(f"{_tag} {_arm} R@1(3seed均值)", _pr1, _r1,
                  f"{_root}/{_arm}/*/results.json: mean over {len(_fs)} seeds", tol=0.002)

    # ── ①g 解码器 VLM（bf16, **5 seed**；2026-10-10 晚更新）──
    _vl = json.loads(io.open(REPO / "outputs/analysis/vlm_bf16_detail.json",
                             encoding="utf-8").read())
    for _arm, _rel, _sd, _cg in (
            ("text_only", 66.47, 8.32, 0.168),
            ("vision_only", 18.03, 8.78, 0.3919),
            ("both", 87.94, 5.35, 0.2913)):
        _s = _vl["summary"][_arm]
        claim(f"VLM {_arm} DG* 相对变化(%), n=13", _rel, _s["dg_rel_mean"],
              f"vlm_bf16_detail.json:summary.{_arm}.dg_rel_mean", tol=0.1)
        claim(f"VLM {_arm} DG* 相对变化 sd, n=13", _sd, _s["dg_rel_sd"],
              f"vlm_bf16_detail.json:summary.{_arm}.dg_rel_sd", tol=0.1)
        claim(f"VLM {_arm} CG 跨度均值, n=13", _cg, _s["cg_mean"],
              f"vlm_bf16_detail.json:summary.{_arm}.cg_mean", tol=0.001)
    # 逐 seed 的种子范围（论文表的 Seed range 列）
    for _arm, _lo, _hi in (("text_only", 47.8, 78.77), ("vision_only", 8.51, 35.72),
                           ("both", 73.14, 95.05)):
        _rels = _vl["summary"][_arm]["dg_rel"]
        claim(f"VLM {_arm} 种子下界(%)", _lo, min(_rels),
              f"vlm_bf16_detail.json:summary.{_arm}.dg_rel", tol=0.1)
        claim(f"VLM {_arm} 种子上界(%)", _hi, max(_rels),
              f"vlm_bf16_detail.json:summary.{_arm}.dg_rel", tol=0.1)

    # ── ①f 数据集翻转（严格冻结，r4；2026-10-10 COCO text_only 补齐）──
    _fl = json.loads(io.open(REPO / "outputs/analysis/dataset_flip_strict.json",
                             encoding="utf-8").read())
    for _k, _v in (("Flickr30k|text_only", -0.0304), ("Flickr30k|both", -0.0204),
                   ("COCO|text_only", -0.0430), ("COCO|both", -0.0877)):
        claim(f"r4 {_k} ΔCG", _v, _fl["r4"][_k]["mean"],
              f"dataset_flip_strict.json:r4.{_k}.mean", tol=0.001)
    for _k, _v in (("Flickr30k|text_only", 0.0039), ("COCO|both", 0.0026)):
        claim(f"r4 {_k} sd", _v, _fl["r4"][_k]["sd"],
              f"dataset_flip_strict.json:r4.{_k}.sd", tol=0.0005)
    # COCO text_only 全秩（论文新写的趋势句）
    _tr = [("r2", -0.0247), ("r8", -0.0690), ("r32", -0.1153), ("r64", -0.1359)]
    for _r, _v in _tr:
        _xs = []
        import glob as _g
        for _f in sorted(_g.glob(str(REPO / f"outputs/coco_sweep_text_only/{_r}/text_only/seed*/results.json"))):
            _d = json.loads(io.open(_f, encoding="utf-8").read())
            _xs.append(_d["final_gap"]["centroid_gap"] - _d["initial_gap"]["centroid_gap"])
        import statistics as _st
        claim(f"COCO text_only {_r} ΔCG", _v, _st.mean(_xs),
              f"coco_sweep_text_only/{_r}/text_only/seed*/results.json:mean", tol=0.001)

    # ── ①e 两处理论否证（2026-10-10 加入 discussion 的 Seventh / Eighth）──
    ap = json.loads(io.open(REPO / "outputs/analysis/alpha_precision.json",
                            encoding="utf-8").read())
    claim("f(DG0) 高精度合并值", 66.7, ap["pooled_f"]["mean"],
          "alpha_precision.json:pooled_f.mean", tol=0.2)
    claim("f(DG0) 标准误", 4.8, ap["pooled_f"]["se"],
          "alpha_precision.json:pooled_f.se", tol=0.1)
    claim("归档 alpha_fit", -2.7743e-3, ap["alpha_fit_archive"],
          "alpha_precision.json:alpha_fit_archive", tol=1e-6)
    claim("f_fit = alpha_fit/eta", -27.7, ap["f_fit_archive"],
          "alpha_precision.json:f_fit_archive", tol=0.1)
    dt = json.loads(io.open(REPO / "outputs/analysis/driving_trajectory.json",
                            encoding="utf-8").read())
    for _a, _paper in (("text_only", 10.8), ("vision_only", 10.2), ("both", 9.2)):
        claim(f"驱动项轨迹均值 {_a}", _paper, dt["trajectory_means"][_a],
              f"driving_trajectory.json:trajectory_means.{_a}", tol=0.1)
    claim("驱动项极差(%)", 16.5, dt["trajectory_mean_spread_pct"],
          "driving_trajectory.json:trajectory_mean_spread_pct", tol=0.2)
    _dv = json.loads(io.open(REPO / "outputs/analysis/driving_verdict.json",
                             encoding="utf-8").read())
    claim("实测 CGΔ 极差(%)", 277.0, _dv["cg_delta_spread_pct"],
          "driving_verdict.json:cg_delta_spread_pct", tol=2.0)

    # ── ①d dg_pred 偏差（2026-10-10 加入 discussion 的 Sixth limitation）──
    dp = json.loads(io.open(REPO / "outputs/analysis/dg_pred_bias.json",
                            encoding="utf-8").read())["verdict"]
    claim("dg_pred 实测/预测中位比", 2.44, dp["systematic_ratio_median"],
          "dg_pred_bias.json:verdict.systematic_ratio_median", tol=0.02)
    claim("dg_pred 极差比(预测/实测)", 3.33, dp["spread_ratio"],
          "dg_pred_bias.json:verdict.spread_ratio", tol=0.02)
    claim("dg_pred 预测极差", 0.223, dp["pred_spread"],
          "dg_pred_bias.json:verdict.pred_spread", tol=0.002)
    claim("dg_pred 实测极差", 0.067, dp["actual_spread"],
          "dg_pred_bias.json:verdict.actual_spread", tol=0.002)
    claim("dg_pred 相关系数", 0.225, dp["corr"],
          "dg_pred_bias.json:verdict.corr", tol=0.01)
    pr = json.loads(io.open(REPO / "outputs/theory/prospective/prospective_results.json",
                            encoding="utf-8").read())
    import statistics as _st
    _rels = [abs((r["alpha_pred"] - r["alpha_actual"]) / r["alpha_actual"]) for r in pr]
    claim("alpha 预测中位相对误差(%)", 34.0, _st.median(_rels) * 100,
          "prospective_results.json:median rel err of alpha_pred", tol=1.0)

    # ── ①c 解码器 VLM（实验 ④，2026-10-08 加入 discussion 与 supplement E 节）──
    qv = json.loads(io.open(REPO / "outputs/analysis/qwen_verdict.json",
                            encoding="utf-8").read())
    for _arm, _paper_rel in (("both", 0.838), ("text_only", 0.739), ("vision_only", 0.110)):
        claim(f"Qwen2-VL {_arm} DG* 相对降幅", _paper_rel,
              qv["rows"][_arm]["rel"], "qwen_verdict.json:rows.<arm>.rel", tol=0.002)
    claim("Qwen2-VL 三臂起点比", 3.4, qv["start_ratio"],
          "qwen_verdict.json:start_ratio", tol=0.06)
    for _arm, _paper_n in (("both", 14494912), ("text_only", 9232384), ("vision_only", 5262528)):
        claim(f"Qwen2-VL {_arm} n_trainable", float(_paper_n),
              float(qv["n_trainable"][_arm]) if "n_trainable" in qv
              else float(json.loads(io.open(
                  REPO / f"outputs/vlm_strictfreeze/4bit/{_arm}_seed42.json",
                  encoding="utf-8").read())["n_trainable"]),
              f"vlm_strictfreeze/4bit/{_arm}_seed42.json:n_trainable", tol=0.6)

    # ── ② ODE 台账（逐 run 拟合）
    led = json.loads(io.open(REPO / "outputs/analysis/ode_ledger.json", encoding="utf-8").read())
    sub = led["subsets"]
    claim("LoRA 全部 R²（55 run）", 0.949, sub["lora"]["mean"],
          "ode_ledger.json:subsets.lora.mean ← tools/_p1_ledger.py")
    claim("LoRA+Flickr30k R²（43 run）", 0.953, sub["lora_flickr"]["mean"], "...lora_flickr.mean")
    claim("LoRA+MS-COCO R²（6 run）", 0.903, sub["lora_coco"]["mean"], "...lora_coco.mean")
    claim("Adapter R²（30 run）", 0.6694, sub["adapter"]["mean"], "...adapter.mean")
    claim("full-FT R²（11 run）", 0.9217, sub["full_ft"]["mean"], "...full_ft.mean")

    # ── ③ 逐秩 R²（Flickr30k LoRA both 位）
    runs = led["runs"]
    for rk, want in ((2, 0.937), (64, 0.938)):
        sel = [r for r in runs if r["family"] == "lora" and r["top"] == "v1_trajectory"
               and r["site"] == "both" and r["rank"] == rk]
        claim(f"逐秩 both r={rk} R²", want, st.mean(x["R2"] for x in sel),
              f"ode_ledger.json:runs(both,r={rk})")

    # ── ④ COCO ODE 主张：**已于 2026-10-08 撤回**（操作者选 ③+①）
    #
    # 原断言（coco_text_r8=0.897 / coco_both_r8=0.910 / coco_full_ft=0.966）随
    # supplement 的 `tab:coco_ode` 一并删除。原因：那些系数拟合自**非严格冻结**的 run
    # （n_trainable=145,170,177），而严格冻结下 MS-COCO 的 DG* 几乎不动
    # （跨度 0.003–0.006，拟合 R² 0.12/0.68；同 run 的 CG R² 为 0.93）。
    # 论文明说不再为 MS-COCO 报告 ODE 系数，故此处**不再断言任何数字**。
    # 证据：tools/_p39_verify_dgstar_failure.py；HANDOFF 2026-10-08「DG* 框架失效」条。

    # ── ⑤ 梯度流恒等式（直接验证）
    gi = json.loads(io.open(REPO / "outputs/theory/gradflow_identity/identity_check.json",
                            encoding="utf-8").read())
    claim("梯度流恒等式 cos(预测,实测)", 0.9977, gi["cos_pred_vs_actual"],
          "gradflow_identity/identity_check.json:cos_pred_vs_actual")
    claim("梯度流恒等式 中位相对误差", 0.0270, gi["median_rel_err"],
          "...identity_check.json:median_rel_err")

    # ── ⑥ 编码器侧梯度（零梯度硬校验）
    es = json.loads(io.open(REPO / "outputs/theory/encoder_side/encoder_side.json",
                            encoding="utf-8").read())
    claim("text_only 视觉梯度范数", 0.0000, es["summary"]["text_only"]["norm_g_vision"],
          "encoder_side/encoder_side.json:summary.text_only.norm_g_vision")
    claim("vision_only 文本梯度范数", 0.0000, es["summary"]["vision_only"]["norm_g_text"],
          "...summary.vision_only.norm_g_text")
    claim("text_only 文本梯度范数", 13.51, es["summary"]["text_only"]["norm_g_text"],
          "...summary.text_only.norm_g_text", tol=0.02)

    # ── ⑦ 跨架构（OpenCLIP BitFit，正文 0.943）
    oc = json.loads(io.open(REPO / "outputs/theory/openclip/openclip_results.json",
                            encoding="utf-8").read())
    claim("OpenCLIP BitFit R² 均值", 0.943, st.mean(x["r_squared"] for x in oc),
          "openclip/openclip_results.json:mean(r_squared)")

    # ── ⑧ CLIP BitFit 边界情形（正文 0.30–0.84）
    bf = json.loads(io.open(REPO / "outputs/theory/bitfit/bitfit_results.json",
                            encoding="utf-8").read())
    rs = sorted(x["r_squared"] for x in bf)
    claim("CLIP BitFit R² 下界", 0.30, rs[0], "bitfit/bitfit_results.json:min(r_squared)", tol=0.005)
    claim("CLIP BitFit R² 上界", 0.84, rs[-1], "...max(r_squared)", tol=0.005)

    # ── ⑨ monitor DG（本轮新做的实验）
    mg = json.loads(io.open(REPO / "outputs/analysis/monitor_dg_check3.json",
                            encoding="utf-8").read())
    claim("初始 DG* vs 末态 R@1（r）", -0.708, mg["corr_dg0_r1"],
          "monitor_dg_check3.json:corr_dg0_r1 ← tools/_p3_monitor_dg3.py", tol=0.003)
    claim("DG/CG 最优 epoch 一致率", 0.42, mg["argmin_agree_rate"],
          "...argmin_agree_rate", tol=0.006)

    # ── ⑩ LOCO（LoRA 族内）
    lo = json.loads(io.open(REPO / "outputs/analysis/ode_loco2.json", encoding="utf-8").read())
    # 18 = **LoRA 族内**配置数（不是 per_config 的 33——那是全部方法）
    lora_confs = [k for k in lo.get("per_config", {}) if "/adapter" not in k and "full_ft" not in k]
    claim("LOCO LoRA 族内配置数", 18.0, float(len(lora_confs)),
          "ode_loco2.json:per_config(LoRA 子集) ← tools/_p1_ode_loco2.py", tol=0.6)

    print(f"\n  === 台账汇总 ===")
    print(f"  ✅ 通过 {ok} ｜ ❌ 失败 {bad} ｜ 共 {ok+bad} 条")
    if apply:
        OUT.parent.mkdir(parents=True, exist_ok=True)
        io.open(OUT, "w", encoding="utf-8", newline="").write(json.dumps(
            {"passed": ok, "failed": bad, "claims": ledger}, ensure_ascii=False, indent=1))
        print(f"  ✅ 已写 {OUT.relative_to(REPO)}")
    return 0 if bad == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
