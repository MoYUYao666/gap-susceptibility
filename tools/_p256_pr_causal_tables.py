# -*- coding: utf-8 -*-
r"""PR R1.3/R2.4/R3.3 -- render `outputs/analysis/pr_relative_perturbation.json` into the tables
quoted verbatim in `docs/PR_CAUSAL_FIX.md` (every number carries its JSON field path).

Input : outputs/analysis/pr_relative_perturbation.json  (meta.status must be "complete")
Output: outputs/analysis/pr_relative_perturbation_tables.md
        outputs/analysis/pr_relative_perturbation_verdict.json

    python tools\_p256_pr_causal_tables.py            # dry run (print only)
    python tools\_p256_pr_causal_tables.py --apply    # write the two files
"""
from __future__ import annotations

import argparse
import io
import json
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
SRC = REPO / "outputs" / "analysis" / "pr_relative_perturbation.json"
OUT_MD = REPO / "outputs" / "analysis" / "pr_relative_perturbation_tables.md"
OUT_JSON = REPO / "outputs" / "analysis" / "pr_relative_perturbation_verdict.json"


def rel(p) -> str:
    """Path relative to the repo when possible, else the raw string."""
    try:
        return Path(p).resolve().relative_to(REPO).as_posix()
    except ValueError:
        return str(p)


def f(x, nd=3, signed=False):
    if x is None:
        return "n/a"
    return ("%+.*f" if signed else "%.*f") % (nd, x)


def ms(s, nd=2, signed=False):
    """mean +/- sd from a summarise() dict."""
    if not s or s.get("n", 0) == 0 or s.get("mean") is None:
        return "n/a"
    if s.get("sd") is None:
        return f(s["mean"], nd, signed)
    return "%s +/- %s" % (f(s["mean"], nd, signed), f(s["sd"], nd))


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    ap.add_argument("--src", default=str(SRC))
    args = ap.parse_args()

    src = Path(args.src)
    if not src.is_absolute():
        src = REPO / src
    d = json.load(io.open(src, encoding="utf-8"))
    assert d["meta"]["status"] == "complete", \
        "refusing to render tables from a %s run" % d["meta"]["status"]
    rows = [r for r in d["rows"] if "error" not in r]
    g = d["weight_geometry"]
    A = d["analysis"]
    seeds = d["meta"]["seeds"]
    levels = d["meta"]["levels"]
    nseeds = len(seeds)
    L: list[str] = []
    V = {}

    L.append("# PR R1.3 / R2.4 / R3.3 -- parameter-matched perturbation tables\n")
    L.append("Source: `%s` (producing script `%s`, status `%s`, %d conditions, %d errors, "
             "%d seeds, model `%s`, %d evaluation images).\n"
             % (rel(src), d["meta"]["script"], d["meta"]["status"], len(d["rows"]),
                len(d["errors"]), nseeds, d["meta"]["model"],
                d["meta"]["data"]["n_images"]))
    L.append("Baseline on the evaluation set: R@1(i2t) = %s, R@1(t2i) = %s, CG = %s, DG = %s "
             "(`baseline`).\n" % (f(d["baseline"]["R1"]["R@1_i2t"], 4),
                                  f(d["baseline"]["R1"]["R@1_t2i"], 4),
                                  f(d["baseline"]["CG"], 4), f(d["baseline"]["DG"], 4)))

    def r2(a, b):
        return "%.3f" % (a / b) if b else "n/a"

    # ---------------------------------------------------------------- T1
    L.append("\n## T1 -- weight geometry of the two towers (`weight_geometry.<tower>`)\n")
    L.append("| quantity | vision | text | ratio V/T |")
    L.append("|---|---|---|---|")
    L.append("| injected tensors (`n_injected_tensors`) | %d | %d | %s |"
             % (g["vision"]["n_injected_tensors"], g["text"]["n_injected_tensors"],
                r2(g["vision"]["n_injected_tensors"], g["text"]["n_injected_tensors"])))
    L.append("| injected parameters (`n_injected_params`) | %d | %d | %s |"
             % (g["vision"]["n_injected_params"], g["text"]["n_injected_params"],
                r2(g["vision"]["n_injected_params"], g["text"]["n_injected_params"])))
    L.append("| tower parameters (`n_total_params`) | %d | %d | %s |"
             % (g["vision"]["n_total_params"], g["text"]["n_total_params"],
                r2(g["vision"]["n_total_params"], g["text"]["n_total_params"])))
    L.append("| injected share of tower parameters | %.3f | %.3f | -- |"
             % (g["vision"]["n_injected_params"] / g["vision"]["n_total_params"],
                g["text"]["n_injected_params"] / g["text"]["n_total_params"]))
    L.append("| ||W_inj||_F (`frob_injected`) | %.3f | %.3f | %s |"
             % (g["vision"]["frob_injected"], g["text"]["frob_injected"],
                r2(g["vision"]["frob_injected"], g["text"]["frob_injected"])))
    L.append("| ||W_inj||_F / ||W_enc+proj||_F (`injected_share_of_all_frob`) | %.4f | %.4f | -- |"
             % (g["vision"]["injected_share_of_all_frob"],
                g["text"]["injected_share_of_all_frob"]))
    L.append("| RMS of injected weights (`rms_injected`) | %.5f | %.5f | %.3f |"
             % (g["vision"]["rms_injected"], g["text"]["rms_injected"],
                g["vision"]["rms_injected"] / g["text"]["rms_injected"]))
    L.append("| expected tower-level rel. perturbation per unit sigma "
             "(`expected_rel_at_unit_sigma_injected`) | %.5f | %.5f | %.4f |"
             % (g["vision"]["expected_rel_at_unit_sigma_injected"],
                g["text"]["expected_rel_at_unit_sigma_injected"],
                g["vision"]["expected_rel_at_unit_sigma_injected"]
                / g["text"]["expected_rel_at_unit_sigma_injected"]))

    # ---------------------------------------------------------------- T2
    L.append("\n## T2 -- the same sigma is not the same relative perturbation "
             "(`weight_geometry.<tower>.by_kind[*].expected_rel_at_unit_sigma`)\n")
    L.append("Expected per-tensor relative perturbation ||dW_i||_F/||W_i||_F produced by the "
             "archived injector at sigma = 1 (its noise sd is 1*std(W_i)); multiply by any "
             "sigma. LayerNorm weights receive ~10x less relative perturbation than the "
             "attention/MLP weight matrices at the same sigma.\n")
    kinds = sorted(set(g["vision"]["by_kind"]) | set(g["text"]["by_kind"]),
                   key=lambda k: -g["text"]["by_kind"].get(k, {}).get("frob", 0))
    L.append("| tensor kind | vision | text | vision/text | params (V) | params (T) |")
    L.append("|---|---|---|---|---|---|")
    for k in kinds:
        v = g["vision"]["by_kind"].get(k, {}).get("expected_rel_at_unit_sigma")
        t = g["text"]["by_kind"].get(k, {}).get("expected_rel_at_unit_sigma")
        L.append("| `%s` | %s | %s | %s | %s | %s |"
                 % (k, f(v, 4), f(t, 4), r2(v, t) if (v and t) else "n/a",
                    g["vision"]["by_kind"].get(k, {}).get("n_params", "-"),
                    g["text"]["by_kind"].get(k, {}).get("n_params", "-")))
    L.append("\nRealized per-block relative perturbation at the archived sigma = 0.3 "
             "(`rows[*].rel_realized_by_block`), spread over the 12 blocks:\n")
    L.append("| tower | min | mean | max | max/min |")
    L.append("|---|---|---|---|---|")
    for tw in ("vision", "text"):
        rr = [x for x in rows if x["protocol"] == "abs_std" and x["tower"] == tw
              and abs(x["level"] - 0.3) < 1e-12][0]
        b = list(rr["rel_realized_by_block"].values())
        L.append("| %s | %.4f | %.4f | %.4f | %.2f |"
                 % (tw, min(b), sum(b) / len(b), max(b), max(b) / min(b)))
    L.append("\nLayerNorm share of the injected Frobenius norm "
             "(`weight_geometry.<tower>.by_kind[*].frob`):\n")
    L.append("| tower | LayerNorm weights | all LayerNorm params (weights + biases) | "
             "attention/MLP weights |")
    L.append("|---|---|---|---|")
    V["layernorm_frob_share"] = {}
    for tw in ("vision", "text"):
        tot = g[tw]["frob_injected"] ** 2
        lnw = sum(x["frob"] ** 2 for k, x in g[tw]["by_kind"].items()
                  if k.startswith("layer_norm") and k.endswith(".weight"))
        ln = sum(x["frob"] ** 2 for k, x in g[tw]["by_kind"].items()
                 if k.startswith("layer_norm"))
        am = sum(x["frob"] ** 2 for k, x in g[tw]["by_kind"].items()
                 if (k.endswith(".weight") and not k.startswith("layer_norm")))
        L.append("| %s | %.4f | %.4f | %.4f |" % (tw, lnw / tot, ln / tot, am / tot))
        V["layernorm_frob_share"][tw] = {"ln_weights": lnw / tot, "all_ln_params": ln / tot,
                                         "attn_mlp_weights": am / tot,
                                         "by_kind_frob_sq_denominator": tot}

    # ---------------------------------------------------------------- T3
    L.append("\n## T3 -- the relative budget each protocol actually delivers "
             "(`rows[*].rel_injected`, `rows[*].rel_realized_stats`)\n")
    L.append("`rel_layer` and `rel_uniform` are matched by construction (V/T = 1.0000); the two "
             "equal-absolute protocols are not. Per-tensor columns are means over the 192 "
             "injected tensors of one seed (the draw-to-draw spread is < 1%).\n")
    L.append("| protocol | level | tower-level rel (V) | tower-level rel (T) | V/T | "
             "per-tensor rel V (mean +/- sd) | per-tensor rel T (mean +/- sd) |")
    L.append("|---|---|---|---|---|---|---|")
    for proto in ("rel_layer", "abs_std", "abs_raw", "rel_uniform"):
        if proto not in levels:
            continue
        for lv in levels[proto]:
            if lv == 0.0:
                continue
            out = []
            for tw in ("vision", "text"):
                rs = [x for x in rows if x["protocol"] == proto and x["tower"] == tw
                      and abs(x["level"] - lv) < 1e-15]
                if not rs:
                    out.append(None)
                    continue
                out.append((sum(x["rel_injected"] for x in rs) / len(rs),
                            ms(rs[0]["rel_realized_stats"], 4)))
            if out[0] and out[1]:
                L.append("| %s | %.4g | %.5f | %.5f | %.4f | %s | %s |"
                         % (proto, lv, out[0][0], out[1][0], out[0][0] / out[1][0],
                            out[0][1], out[1][1]))

    # ---------------------------------------------------------------- T4
    L.append("\n## T4 -- R@1(i2t) degradation under matched relative budgets "
             "(`analysis.per_level.rel_layer[*]`)\n")
    L.append("| r | vision drop %% (mean +/- sd) | text drop %% (mean +/- sd) | "
             "ratio of means | paired ratio per seed (mean +/- sd) | seeds V>T | "
             "seeds V>50%% | seeds T>50%% |")
    L.append("|---|---|---|---|---|---|---|---|")
    for lv in levels["rel_layer"]:
        if lv == 0.0 or repr(lv) not in A["per_level"]["rel_layer"]:
            continue
        pl = A["per_level"]["rel_layer"][repr(lv)]
        L.append("| %.3g | %s | %s | %s | %s | %d/%d | %d | %d |"
                 % (lv, ms(pl["vision_drop_i2t"]), ms(pl["text_drop_i2t"]),
                    f(pl["ratio_of_means"], 3),
                    ms({"n": pl["n_seeds"], "mean": pl["paired_ratio_mean"],
                        "sd": pl["paired_ratio_sd"]}, 3),
                    pl["n_seeds_vision_gt_text"], pl["n_seeds"],
                    pl["n_seeds_vision_drop_gt_50pct"], pl["n_seeds_text_drop_gt_50pct"]))
    V["rel_layer_per_level"] = {repr(lv): A["per_level"]["rel_layer"][repr(lv)]
                                for lv in levels["rel_layer"] if lv != 0.0
                                and repr(lv) in A["per_level"]["rel_layer"]}

    # ---------------------------------------------------------------- T5
    L.append("\n## T5 -- all four protocols: ratio of mean drops and CG/DG "
             "(`analysis.per_level.*`)\n")
    L.append("| protocol | level | vision drop % | text drop % | ratio | vision CG | text CG | "
             "vision DG | text DG |")
    L.append("|---|---|---|---|---|---|---|---|---|")
    for proto in ("rel_layer", "rel_uniform", "abs_std", "abs_raw"):
        for lv in levels.get(proto, []):
            if lv == 0.0 or repr(lv) not in A["per_level"].get(proto, {}):
                continue
            pl = A["per_level"][proto][repr(lv)]
            L.append("| %s | %.4g | %s | %s | %s | %s | %s | %s | %s |"
                     % (proto, lv, ms(pl["vision_drop_i2t"], 2), ms(pl["text_drop_i2t"], 2),
                        f(pl["ratio_of_means"], 3), ms(pl["vision_CG"], 4),
                        ms(pl["text_CG"], 4), ms(pl["vision_DG"], 4), ms(pl["text_DG"], 4)))

    # ---------------------------------------------------------------- T6
    L.append("\n## T6 -- headline: pooled fragility ratio and matched-drop budget ratio "
             "(`analysis.headline.*`)\n")
    L.append("Pooled per-(seed, level) ratio = vision drop / text drop. "
             "`levels_nonsaturated` = levels where both tower means lie in [1%, 90%]. "
             "Budget ratio = relative budget (r, or sigma for abs_*) needed for the same drop, "
             "text / vision; **> 1 means vision is the more fragile tower**.\n")
    L.append("| protocol | pooled ratio (nonsaturated) | pooled ratio (all levels) | "
             "budget @5% drop | budget @10% drop | budget @20% drop |")
    L.append("|---|---|---|---|---|---|")
    V["headline"] = {}
    for proto in ("rel_layer", "rel_uniform", "abs_std", "abs_raw"):
        h = A["headline"].get(proto)
        if not h:
            continue
        ns = h["matched_relative_fragility"].get("levels_nonsaturated", {})
        al = h["matched_relative_fragility"].get("all_levels", {})
        b = {}
        for t in ("drop_5_pct", "drop_10_pct", "drop_20_pct"):
            s = h["matched_drop_budget_ratio"][t]["budget_ratio_text_over_vision"]
            b[t] = (ms(s, 3), h["matched_drop_budget_ratio"][t]["n_seeds_bracketed"])
        L.append("| %s | %s (n=%d) | %s (n=%d) | %s (%d/%d) | %s (%d/%d) | %s (%d/%d) |"
                 % (proto,
                    ms({"n": ns.get("n_pairs", 0), "mean": ns.get("ratio_mean"),
                        "sd": ns.get("ratio_sd")}, 3), ns.get("n_pairs", 0),
                    ms({"n": al.get("n_pairs", 0), "mean": al.get("ratio_mean"),
                        "sd": al.get("ratio_sd")}, 3), al.get("n_pairs", 0),
                    b["drop_5_pct"][0], b["drop_5_pct"][1], nseeds,
                    b["drop_10_pct"][0], b["drop_10_pct"][1], nseeds,
                    b["drop_20_pct"][0], b["drop_20_pct"][1], nseeds))
        V["headline"][proto] = {
            "levels_used_nonsaturated": h["levels_used_for_pooled_ratio"],
            "pooled_ratio_nonsaturated": ns, "pooled_ratio_all_levels": al,
            "matched_drop_budget_ratio_text_over_vision": h["matched_drop_budget_ratio"],
            "ratio_of_means_per_level": h["levels"],
        }

    # ---------------------------------------------------------------- T7
    L.append("\n## T7 -- per-seed R@1 drops at the informative levels "
             "(`rows[*].drop_pct_i2t`, seeds %s)\n" % seeds)
    L.append("| protocol | level | tower | " + " | ".join("seed %d" % s for s in seeds) + " |")
    L.append("|---|---|---|" + "---|" * nseeds)
    V["per_seed"] = {}
    for proto, lvs in (("rel_layer", [0.03, 0.06, 0.1, 0.2]),
                       ("rel_uniform", [0.01, 0.02, 0.03, 0.05]),
                       ("abs_std", [0.1, 0.2, 0.3]),
                       ("abs_raw", [lv for lv in levels.get("abs_raw", []) if lv != 0.0][:3])):
        for lv in lvs:
            hits = [x for x in rows if x["protocol"] == proto and abs(x["level"] - lv) < 1e-15]
            if not hits:
                continue
            for tw in ("vision", "text"):
                rs = {x["seed"]: x for x in hits if x["tower"] == tw}
                if len(rs) != nseeds:
                    continue
                vals = [rs[s]["drop_pct_i2t"] for s in seeds]
                V["per_seed"].setdefault(proto, {})["%.6g_%s" % (lv, tw)] = vals
                L.append("| %s | %.4g | %s | %s |"
                         % (proto, lv, tw, " | ".join("%+.2f" % v for v in vals)))

    # ---------------------------------------------------------------- T8
    L.append("\n## T8 -- same tower-level relative budget, different per-tensor allocation "
             "(`rows`, paired by seed)\n")
    L.append("`abs_raw` uses sigma = r * rms(vision injected weights), so the VISION tower's "
             "tower-level relative budget equals r in both protocols -- yet the two protocols "
             "spread that budget differently over the 192 tensors (abs_raw: nearly all of it on "
             "the small-norm attention/MLP matrices; rel_layer: an equal *relative* share on "
             "every tensor including the LayerNorm weights that carry most of ||W_inj||_F). "
             "Same seed = same random direction.\n")
    rms_v = g["vision"]["rms_injected"]
    L.append("| r (tower-level rel, vision) | tower | drop % rel_layer | drop % abs_raw | "
             "paired difference (rel_layer - abs_raw) |")
    L.append("|---|---|---|---|---|")
    V["allocation_check"] = {}
    for abs_lv in levels.get("abs_raw", []):
        if abs_lv == 0.0:
            continue
        r_implied = abs_lv / rms_v
        match = [lv for lv in levels["rel_layer"] if abs(lv - r_implied) < 1e-9]
        if not match:
            continue
        r = match[0]
        for tw in ("vision", "text"):
            a = {x["seed"]: x["drop_pct_i2t"] for x in rows
                 if x["protocol"] == "rel_layer" and x["tower"] == tw
                 and abs(x["level"] - r) < 1e-15}
            b = {x["seed"]: x["drop_pct_i2t"] for x in rows
                 if x["protocol"] == "abs_raw" and x["tower"] == tw
                 and abs(x["level"] - abs_lv) < 1e-15}
            common = sorted(set(a) & set(b))
            if not common:
                continue
            da = [a[s] for s in common]
            db = [b[s] for s in common]
            dd = [x - y for x, y in zip(da, db)]

            def summ(v):
                if not v:
                    return {"n": 0}
                m = sum(v) / len(v)
                return {"n": len(v), "mean": m,
                        "sd": (sum((x - m) ** 2 for x in v) / (len(v) - 1)) ** 0.5
                              if len(v) > 1 else None}

            L.append("| %.3g | %s | %s | %s | %s |"
                     % (r, tw, ms(summ(da), 2), ms(summ(db), 2), ms(summ(dd), 2, True)))
            V["allocation_check"]["%.6g_%s" % (r, tw)] = {
                "sigma_abs_raw": abs_lv, "rms_vision_injected": rms_v,
                "rel_layer_drop": da, "abs_raw_drop": db, "difference": dd,
                "n_seeds": len(common)}

    L.append("\n---\nRendered by `tools/_p256_pr_causal_tables.py` from `%s` "
             "(sha1 of the producing script: `%s`).\n"
             % (rel(src), d["meta"]["script_sha1"]))
    md = "\n".join(L) + "\n"

    print(md)
    if args.apply:
        io.open(OUT_MD, "w", encoding="utf-8", newline="").write(md)
        io.open(OUT_JSON, "w", encoding="utf-8", newline="").write(
            json.dumps({"source": rel(src),
                        "script": "tools/_p256_pr_causal_tables.py",
                        "producer_script": d["meta"]["script"],
                        "producer_script_sha1": d["meta"]["script_sha1"],
                        "baseline": d["baseline"], **V}, ensure_ascii=False, indent=1))
        print("wrote %s" % OUT_MD.relative_to(REPO))
        print("wrote %s" % OUT_JSON.relative_to(REPO))
    else:
        print("(dry run; add --apply)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
