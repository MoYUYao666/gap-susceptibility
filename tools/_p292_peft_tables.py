# -*- coding: utf-8 -*-
r"""PR R1.6 -- render the LoRA/Adapter learning-rate grid and its comparison with the full-FT
sweep into the tables quoted verbatim in `docs/PR_FAIRNESS_FIX2.md`.

Inputs : outputs/analysis/pr_peft_lr_sweep.json        (tools/_p291_peft_lr_sweep.py)
         outputs/analysis/pr_fullft_lr_sweep_full.json (task-5, for the comparison)
Outputs: outputs/analysis/pr_peft_tables.md
         outputs/analysis/pr_peft_verdict.json

    python tools\_p292_peft_tables.py            # dry run (print only)
    python tools\_p292_peft_tables.py --apply
"""
from __future__ import annotations

import argparse
import io
import json
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
PEFT = REPO / "outputs" / "analysis" / "pr_peft_lr_sweep.json"
FULLFT = REPO / "outputs" / "analysis" / "pr_fullft_lr_sweep_full.json"
OUT_MD = REPO / "outputs" / "analysis" / "pr_peft_tables.md"
OUT_JSON = REPO / "outputs" / "analysis" / "pr_peft_verdict.json"


def rel(p) -> str:
    try:
        return Path(p).resolve().relative_to(REPO).as_posix()
    except ValueError:
        return str(p)


def f(x, nd=2, signed=False):
    if x is None:
        return "n/a"
    return ("%+.*f" if signed else "%.*f") % (nd, x)


def ms(mean, sd, nd=2, signed=False):
    if mean is None:
        return "n/a"
    if sd is None:
        return f(mean, nd, signed)
    return "%s +/- %s" % (f(mean, nd, signed), f(sd, nd))


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    ap.add_argument("--src", default=str(PEFT))
    args = ap.parse_args()

    src = Path(args.src)
    if not src.is_absolute():
        src = REPO / src
    d = json.load(io.open(src, encoding="utf-8"))
    assert d["meta"]["status"].startswith("complete"), \
        "sweep status is %s; refusing to render tables" % d["meta"]["status"]
    fr = d["frozen"]
    fzs = fr["zero_shot"]["top1_pct"]
    fcg = fr["gap_retrieval"]["CG"]
    fdg = fr["gap_retrieval"]["DG"]
    fr1 = fr["gap_retrieval"]["R@1_mean"]
    ok = [r for r in d["runs"] if not r.get("error")]
    n_err = len(d["runs"]) - len(ok)
    L: list[str] = []
    V: dict = {"frozen": fr, "grid": {}, "vs_fullft": {}}
    L.append("# PR R1.6 -- LoRA / Adapter learning-rate grid (last open fairness item)\n")
    L.append("Source: `%s` (producing script `%s`, status `%s`, %d runs, %d failed). "
             "Frozen baseline: zero-shot %.2f %%, CG %.4f, DG %.4f, R@1 %.4f "
             "(`frozen`; identical protocol to the full-FT sweep, source "
             "`%s`).\n" % (rel(src), d["meta"]["script"], d["meta"]["status"], len(d["runs"]),
                           n_err, fzs, fcg, fdg, fr1, fr.get("_source", "n/a")))
    L.append("Protocol (`meta.protocol`): %s, batch %d, %s, %d epochs, AdamW (wd %.2f), cosine "
             "per step, grad clip %.1f; evaluation reused from "
             "`tools/_p263_fullft_lr_sweep.py` (zero-shot on the same %d ImageNet-1K images, "
             "CG/DG via `src/gap_metrics`, R@1 on the same %d Flickr30k val pairs).\n"
             % (d["meta"]["protocol"]["train"], d["meta"]["protocol"]["batch"],
                d["meta"]["protocol"]["amp"], d["meta"]["protocol"]["epochs"],
                d["meta"]["protocol"]["weight_decay"], d["meta"]["protocol"]["grad_clip"],
                d["meta"]["protocol"]["zero_shot_eval_images"],
                fr["gap_retrieval"]["n_pairs"]))

    # ------------------------------------------------------------------ T1
    L.append("\n## T1 -- code-level PEFT proof (`runs[*].peft_proof`)\n")
    L.append("| config | trainable | expected (architecture) | fraction of model | "
             "non-PEFT params frozen | n modules | wrapped originals frozen |")
    L.append("|---|---|---|---|---|---|---|")
    seen = set()
    for r in ok:
        p = r["peft_proof"]
        if p["config"] in seen:
            continue
        seen.add(p["config"])
        L.append("| `%s` | %d | %d | %.6f | %s | %d | %s |"
                 % (p["config"], p["n_trainable_params"], p["n_trainable_expected_literal"],
                    p["trainable_fraction"], p["all_non_peft_parameters_frozen"],
                    p["n_peft_modules"], p["wrapped_original_modules_frozen"]))
        V["grid"].setdefault(p["config"], {})["peft_proof"] = p

    # ------------------------------------------------------------------ T2
    L.append("\n## T2 -- grid: every run (`runs[*].final`)\n")
    L.append("| config | lr | seed | zero-shot top-1 %% | vs frozen (pp) | CG | dCG | dDG | "
             "R@1 | final train loss |")
    L.append("|---|---|---|---|---|---|---|---|---|---|")
    for r in sorted(ok, key=lambda x: (x["config"], x["lr"], x["seed"])):
        L.append("| %s | %g | %d | %.2f | %s | %.4f | %s | %s | %.4f | %.4f |"
                 % (r["config"], r["lr"], r["seed"],
                    r["final"]["zero_shot_imagenet1k_top1_pct"],
                    f(r["final"]["zero_shot_imagenet1k_top1_pct"] - fzs, 2, True),
                    r["final"]["CG"], f(r["final"]["CG"] - fcg, 4, True),
                    f(r["final"]["DG"] - fdg, 4, True), r["final"]["R@1_mean"],
                    r["final_train_loss"]))
    V["grid"] = {k: v for k, v in V["grid"].items()}
    V["per_run"] = [{"config": r["config"], "lr": r["lr"], "seed": r["seed"],
                     "zero_shot_top1_pct": r["final"]["zero_shot_imagenet1k_top1_pct"],
                     "dCG": round(r["final"]["CG"] - fcg, 4),
                     "dDG": round(r["final"]["DG"] - fdg, 4),
                     "R@1_mean": r["final"]["R@1_mean"],
                     "final_train_loss": r["final_train_loss"],
                     "post_injection_CG": r.get("post_injection_gap_retrieval", {}).get("CG")}
                    for r in sorted(ok, key=lambda x: (x["config"], x["lr"], x["seed"]))]

    # ------------------------------------------------------------------ T3
    L.append("\n## T3 -- per (config, lr) means (`analysis.grid`)\n")
    L.append("| config@lr | n seeds | zero-shot top-1 % (mean +/- sd) | dCG (mean +/- sd) | "
             "dDG (mean +/- sd) | R@1 (mean +/- sd) |")
    L.append("|---|---|---|---|---|---|")
    for key, a in sorted(d["analysis"].get("grid", {}).items()):
        L.append("| `%s` | %d | %s | %s | %s | %s |"
                 % (key, a["n_seeds"],
                    ms(a["zero_shot_top1_pct_mean"], a["zero_shot_top1_pct_sd"]),
                    ms(a["dCG_mean"], a["dCG_sd"], 4, True),
                    ms(a["dDG_mean"], a["dDG_sd"], 4, True),
                    ms(a["R@1_mean"], a["R@1_sd"], 4)))
    V["grid_cells"] = d["analysis"].get("grid", {})

    # ------------------------------------------------------------------ T4
    L.append("\n## T4 -- post-injection geometry (`runs[*].post_injection_gap_retrieval`)\n")
    L.append("LoRA is identity at initialisation (B = 0); the bottleneck Adapter is NOT "
             "(`up.bias` is non-zero), so insertion alone moves the geometry. This is the state "
             "the paper's `delta_old` convention measures from.\n")
    L.append("| config | post-injection CG | post-injection dCG vs frozen | post-injection R@1 |")
    L.append("|---|---|---|---|")
    seen = set()
    for r in ok:
        if r["config"] in seen:
            continue
        seen.add(r["config"])
        g = r.get("post_injection_gap_retrieval") or {}
        L.append("| %s | %s | %s | %s |"
                 % (r["config"], f(g.get("CG"), 4), f((g.get("CG") or 0) - fcg, 4, True),
                    f(g.get("R@1_mean"), 4)))
        V["grid"][r["config"]]["post_injection"] = g

    # ------------------------------------------------------------------ T5
    L.append("\n## T5 -- best lr per configuration and the comparison with full fine-tuning "
             "(`analysis.best`, `analysis.vs_fullft`)\n")
    best = d["analysis"].get("best") or {}
    if best:
        L.append("| config | best lr by zero-shot | best lr by CG | n runs |")
        L.append("|---|---|---|---|")
        for c, b in sorted((best.get("best_lr_per_config") or {}).items()):
            L.append("| %s | %g | %g | %d |" % (c, b["best_zero_shot"], b["best_dCG"],
                                                b["n_runs"]))
        br = best.get("best_run_by_zero_shot", {})
        L.append("\nBest PEFT run overall by zero-shot: **%s @ lr %g (seed %d) = %.2f %%, "
                 "dCG %s, R@1 %.4f** (`analysis.best.best_run_by_zero_shot`).\n"
                 % (br.get("config"), br.get("lr"), br.get("seed"),
                    br.get("zero_shot_top1_pct"), f(br.get("dCG"), 4, True),
                    br.get("R@1_mean")))
    vs = d["analysis"].get("vs_fullft") or {}
    if vs:
        L.append("| quantity | full fine-tuning (best lr) | best LoRA/Adapter | delta (PEFT - FT) |")
        L.append("|---|---|---|---|")
        db = vs["delta_best_peft_minus_best_fullft"]
        L.append("| lr | %g | %s @ %g | -- |"
                 % (vs["fullft_best_lr"], br.get("config"), br.get("lr")))
        L.append("| zero-shot top-1 %% | %.2f | %.2f | %s pp |"
                 % (vs["fullft_best_zero_shot_top1_pct"], br.get("zero_shot_top1_pct"),
                    f(db["zero_shot_pp"], 2, True)))
        L.append("| dCG | %s | %s | %s |"
                 % (f(vs["fullft_best_dCG"], 4, True), f(br.get("dCG"), 4, True),
                    f(db["dCG"], 4, True)))
        L.append("| R@1 | %.4f | %.4f | %s |"
                 % (vs["fullft_best_R@1"], br.get("R@1_mean"), f(db["R@1"], 4, True)))
        L.append("\nFull-FT per-lr reference (`analysis.vs_fullft.fullft_per_lr`, from "
                 "`%s`):\n" % rel(FULLFT))
        L.append("| lr | zero-shot % (mean +/- sd) | dCG | R@1 |")
        L.append("|---|---|---|---|")
        for lr, a in sorted(vs["fullft_per_lr"].items(), key=lambda kv: float(kv[0])):
            L.append("| %s | %s | %s | %.4f |"
                     % (lr, ms(a["zero_shot_top1_pct_mean"], a["zero_shot_top1_pct_sd"]),
                        f(a["dCG_mean"], 4, True), a["R@1_mean_of_runs"]))
        L.append("\nInterpretation rule (`analysis.vs_fullft.interpretation_rule`): %s.\n"
                 % vs["interpretation_rule"])
    V["best"] = best
    V["vs_fullft"] = vs

    # ------------------------------------------------------------------ T6
    L.append("\n## T6 -- per-epoch train loss (`runs[*].history.train_loss`)\n")
    L.append("| config | lr | seed | " + " | ".join("ep%d" % i for i in range(1, 11)) + " |")
    L.append("|---|---|---|" + "---|" * 10)
    for r in sorted(ok, key=lambda x: (x["config"], x["lr"], x["seed"])):
        tl = r["history"]["train_loss"]
        L.append("| %s | %g | %d | %s |"
                 % (r["config"], r["lr"], r["seed"],
                    " | ".join("%.3f" % v for v in tl)))

    L.append("\n---\nRendered by `tools/_p292_peft_tables.py` from `%s`.\n" % rel(src))
    md = "\n".join(L) + "\n"
    print(md)
    if args.apply:
        io.open(OUT_MD, "w", encoding="utf-8", newline="").write(md)
        io.open(OUT_JSON, "w", encoding="utf-8", newline="").write(
            json.dumps({"source": rel(src), "script": "tools/_p292_peft_tables.py", **V},
                       ensure_ascii=False, indent=1))
        print("wrote %s" % OUT_MD.relative_to(REPO))
        print("wrote %s" % OUT_JSON.relative_to(REPO))
    else:
        print("(dry run; add --apply)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
