# -*- coding: utf-8 -*-
r"""**A1 claim ledger** - every number A1 cites must name the script and the archive field that produces it.

Paper A and the main ledger already have this gate; A1 did not. Each entry below is asserted against the archive at run
time; a failure means the manuscript number has no source (fix the manuscript or the archive, never the tolerance).

    python tools/_claim_ledger_a1.py [--apply]
"""
from __future__ import annotations

import io
import json
import statistics
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
A = REPO / "outputs" / "analysis"
OUT = A / "claim_ledger_a1.json"

ok = bad = 0
LEDGER = []


def load(path):
    return json.loads(io.open(REPO / path, encoding="utf-8").read())


def claim(name, ms, computed, source, nd=2):
    global ok, bad
    ms_f, cmp_f = float(ms), float(computed)
    tol = max(1e-12, (10.0 ** (-nd)) * 0.75 * max(1.0, abs(ms_f)))
    good = abs(ms_f - cmp_f) <= tol
    LEDGER.append({"claim": name, "manuscript": ms, "computed": round(float(computed), 6),
                   "source": source, "pass": bool(good)})
    print(("  PASS " if good else "  FAIL ") + f"{name:<52} ms={ms!r:<10} computed={computed:<12.6f} <- {source}")
    ok += 1 if good else 0
    bad += 0 if good else 1


def main() -> int:
    ap = "--apply" in sys.argv

    # ---- matched-gap control on ImageNet-5k (CLIP B/32)
    fam = load("outputs/analysis/a1_matched_gap_families.json")
    claim("frozen CG", 0.855, fam["frozen"]["CG"], "a1_matched_gap_families.json:frozen.CG", 3)
    claim("frozen top-1", 59.1, fam["frozen"]["top1"], "...:frozen.top1", 1)
    b = fam["max_matched_gap_spread_tol003"]
    claim("matched-gap spread (tol 0.03)", 32.7, b["spread"], "...:max_matched_gap_spread_tol003.spread", 1)
    claim("matched-gap dCG", 0.028, b["dCG"], "...:max_matched_gap_spread_tol003.dCG", 3)
    claim("matched pair a CG (T 0.5)", 0.426, b["a"]["CG"], "...:tol003.a.CG", 3)
    claim("matched pair a top-1", 46.8, b["a"]["top1"], "...:tol003.a.top1", 1)
    claim("matched pair b CG (T 2)", 0.398, b["b"]["CG"], "...:tol003.b.CG", 3)
    claim("matched pair b top-1", 14.1, b["b"]["top1"], "...:tol003.b.top1", 1)
    claim("matched-gap spread (tol 0.05)", 52.1, fam["max_matched_gap_spread_tol005"]["spread"],
          "...:max_matched_gap_spread_tol005.spread", 1)

    # ---- cross-model replication
    cm = load("outputs/analysis/a1_matched_gap_crossmodel.json")["models"]
    claim("OpenCLIP frozen CG", 0.791, cm["openclip"]["frozen"]["CG"], "...crossmodel:openclip.frozen.CG", 3)
    claim("OpenCLIP frozen top-1", 62.4, cm["openclip"]["frozen"]["top1"], "...:openclip.frozen.top1", 1)
    claim("SigLIP frozen CG", 1.116, cm["siglip"]["frozen"]["CG"], "...:siglip.frozen.CG", 3)
    claim("SigLIP frozen top-1", 73.3, cm["siglip"]["frozen"]["top1"], "...:siglip.frozen.top1", 1)
    T_open = {r["param"]: r for r in cm["openclip"]["rows"] if r["family"] == "T"}
    T_sig = {r["param"]: r for r in cm["siglip"]["rows"] if r["family"] == "T"}
    claim("OpenCLIP matched pair dCG", 0.066, T_open[0.5]["CG"] - T_open[2]["CG"], "...:openclip T 0.5 - T 2 CG", 3)
    claim("OpenCLIP matched pair spread", 27.1, T_open[0.5]["top1"] - T_open[2]["top1"], "...:openclip T top-1 gap", 1)
    claim("SigLIP matched pair dCG", 0.197, T_sig[0.5]["CG"] - T_sig[2]["CG"], "...:siglip T 0.5 - T 2 CG", 3)
    claim("SigLIP matched pair spread", 27.1, T_sig[0.5]["top1"] - T_sig[2]["top1"], "...:siglip T top-1 gap", 1)
    # contraction gains
    for tag, model_frozen, expected in (("clip", fam["frozen"], 19.0),):
        pass
    P_fam = {r["param"]: r for r in fam["rows"] if r["family"] == "P"}
    claim("CLIP contraction gain", 19.0, P_fam[0.5]["top1"] - fam["frozen"]["top1"], "...families:P 0.5 - frozen", 1)
    P_open = {r["param"]: r for r in cm["openclip"]["rows"] if r["family"] == "P"}
    claim("OpenCLIP contraction gain", 19.4, P_open[0.5]["top1"] - cm["openclip"]["frozen"]["top1"], "...:openclip P 0.5 - frozen", 1)
    P_sig = {r["param"]: r for r in cm["siglip"]["rows"] if r["family"] == "P"}
    claim("SigLIP contraction gain", 15.0, P_sig[0.5]["top1"] - cm["siglip"]["frozen"]["top1"], "...:siglip P 0.5 - frozen", 1)

    # ---- random-direction control
    rd = load("outputs/analysis/a1_random_direction_gap.json")["summary"]
    claim("random directions", 200, rd["n_directions"], "...random_direction:summary.n_directions", 0)
    claim("random CG matched mean", 0.858, rd["CG_matched"]["mean"], "...:summary.CG_matched.mean", 3)
    claim("random top-1 range", 2.5, rd["top1"]["range"], "...:summary.top1.range", 1)
    claim("random tau min", 0.70, rd["tau"]["min"], "...:summary.tau.min", 2)
    claim("random tau max", 0.90, rd["tau"]["max"], "...:summary.tau.max", 2)
    claim("random tau-top1 correlation", 0.60, rd["corr_tau_top1"], "...:summary.corr_tau_top1", 2)

    # ---- second dataset (DTD, Food-101)
    sec = load("outputs/analysis/a1_matched_gap_second_dataset.json")["benchmarks"]
    claim("DTD frozen CG", 1.018, sec["dtd"]["frozen"]["CG"], "...second_dataset:dtd.frozen.CG", 3)
    claim("DTD frozen top-1", 41.6, sec["dtd"]["frozen"]["top1"], "...:dtd.frozen.top1", 1)
    claim("DTD matched spread (0.03)", 10.1, sec["dtd"]["max_matched_gap_spread_tol003"]["spread"], "...:dtd tol003", 1)
    claim("DTD matched spread (0.05)", 15.1, sec["dtd"]["max_matched_gap_spread_tol005"]["spread"], "...:dtd tol005", 1)
    claim("Food-101 frozen CG", 0.953, sec["food101"]["frozen"]["CG"], "...:food101.frozen.CG", 3)
    claim("Food-101 frozen top-1", 80.6, sec["food101"]["frozen"]["top1"], "...:food101.frozen.top1", 1)
    claim("Food-101 matched spread (0.03)", 12.1, sec["food101"]["max_matched_gap_spread_tol003"]["spread"], "...:food101 tol003", 1)
    claim("Food-101 matched spread (0.05)", 42.1, sec["food101"]["max_matched_gap_spread_tol005"]["spread"], "...:food101 tol005", 1)
    claim("Food-101 widest pair dCG", 0.034, sec["food101"]["max_matched_gap_spread_tol005"]["dCG"], "...:food101 tol005 dCG", 3)

    # ---- further benchmarks with intervals
    mb = load("outputs/analysis/a1_more_benchmarks.json")["benchmarks"]
    im = mb["imagenet5k"]
    claim("flagship spread (recomputed)", 32.7, im["widest_matched_pair"]["spread"], "...more_benchmarks:imagenet5k.spread", 1)
    claim("flagship CI lower", 31.3, im["widest_matched_pair"]["ci95"][0], "...:imagenet5k.ci95[0]", 1)
    claim("flagship CI upper", 33.9, im["widest_matched_pair"]["ci95"][1], "...:imagenet5k.ci95[1]", 1)
    claim("contraction gain (imagenet)", 19.0, im["contraction"]["top1_gain"], "...:imagenet5k.contraction.top1_gain", 1)
    claim("iNat images", 720, mb["inat_wild"]["n_images"], "...:inat_wild.n_images", 0)
    claim("iNat classes", 50, mb["inat_wild"]["n_classes"], "...:inat_wild.n_classes", 0)
    claim("iNat frozen top-1", 10.6, mb["inat_wild"]["frozen"]["top1"], "...:inat_wild.frozen.top1", 1)
    claim("iNat matched spread", 2.6, mb["inat_wild"]["widest_matched_pair"]["spread"], "...:inat_wild.spread", 1)
    claim("iNat contraction gain", 3.2, mb["inat_wild"]["contraction"]["top1_gain"], "...:inat_wild.contraction", 1)
    claim("rare-species classes", 398, mb["rare_species"]["n_classes"], "...:rare_species.n_classes", 0)
    claim("rare-species frozen top-1", 26.9, mb["rare_species"]["frozen"]["top1"], "...:rare_species.frozen.top1", 1)
    claim("rare-species matched spread", 21.0, mb["rare_species"]["widest_matched_pair"]["spread"], "...:rare_species.spread", 1)
    claim("rare-species contraction gain", 9.9, mb["rare_species"]["contraction"]["top1_gain"], "...:rare_species.contraction", 1)

    # ---- prompt-template control
    pt = load("outputs/analysis/a1_prompt_template_gap.json")["models"]
    claim("prompt CG spread (max, OpenCLIP)", 0.094, pt["openclip"]["cg_spread"], "...prompt_template_gap:openclip.cg_spread", 3)
    claim("prompt CG spread (SigLIP)", 0.025, pt["siglip"]["cg_spread"], "...:siglip.cg_spread", 3)
    claim("prompt top-1 range (max)", 4.9, max(v["top1_max"] - v["top1_min"] for v in pt.values()),
          "...:max top1 range across backbones", 1)
    claim("prompt/tolerance ratio", 3.4, pt["openclip"]["cg_spread"] / 0.028, "...:openclip.cg_spread / 0.028", 1)

    # ---- k recommendation
    tk = load("outputs/analysis/a1_tau_k.json")["summary"]
    claim("mean eta (tau5 - tau10)", 0.040, -tk["mean_gain"], "...a1_tau_k.json:summary.mean_gain (negated)", 3)
    claim("minimum template rank correlation", 0.95, tk["min_spearman"], "...:summary.min_spearman", 2)

    # ---- threshold transfer
    th = load("outputs/analysis/a1_threshold_transfer.json")
    s = th["summary"]
    ba = [x for x in s["transfer_balanced_accuracy"] if x is not None]
    claim("frozen CG ratio", 1.41, s["frozen_CG_ratio"], "...threshold_transfer:summary.frozen_CG_ratio", 2)
    claim("SigLIP frozen CG (thresholds)", 1.116, th["settings"]["siglip_imagenet5k"]["CG"], "...:settings.siglip.CG", 3)
    claim("SigLIP frozen top-1 (thresholds)", 73.3, th["settings"]["siglip_imagenet5k"]["top1"], "...:settings.siglip.top1", 1)
    claim("CLIP frozen CG (thresholds)", 0.855, th["settings"]["clip_imagenet5k"]["CG"], "...:settings.clip.CG", 3)
    claim("CLIP frozen top-1 (thresholds)", 59.1, th["settings"]["clip_imagenet5k"]["top1"], "...:settings.clip.top1", 1)
    claim("transfer BA median", 0.458, statistics.median(ba), "...:summary.transfer BA median", 3)
    claim("transfers below chance", 10, sum(1 for x in ba if x < 0.5), "...:count BA < 0.5", 0)
    claim("worst transfer BA", 0.188, min(ba), "...:min BA", 3)

    # ---- monitoring protocol
    mon = load("outputs/analysis/a1_monitor_protocol.json")
    sm = mon["summary"]
    claim("oracle mean top-1", 59.49, sm["oracle"]["mean_top1"], "...monitor_protocol:summary.oracle.mean_top1", 2)
    claim("tau-max mean regret", 0.05, sm["argmax_tau"]["mean_regret"], "...:summary.argmax_tau.mean_regret", 2)
    claim("last-epoch mean regret", 2.35, sm["last_epoch"]["mean_regret"], "...:summary.last_epoch.mean_regret", 2)
    claim("CUSUM mean regret", 0.14, sm["cusum"]["mean_regret"], "...:summary.cusum.mean_regret", 2)
    claim("CUSUM threshold h", 6.0, mon["cusum"]["h_median_loo"], "...:cusum.h_median_loo", 1)
    un = load("outputs/analysis/a1_monitor_uncertainty.json")
    claim("tau-max regret CI lower", 0.00, un["rules"]["argmax_tau"]["ci95"][0], "...monitor_uncertainty:argmax_tau.ci95[0]", 2)
    claim("tau-max regret CI upper", 0.14, un["rules"]["argmax_tau"]["ci95"][1], "...:argmax_tau.ci95[1]", 2)
    claim("last-epoch regret CI lower", 1.65, un["rules"]["last_epoch"]["ci95"][0], "...:last_epoch.ci95[0]", 2)
    claim("tau-max advantage", 2.30, un["tau_max_advantage_over_last"]["mean"], "...:tau_max_advantage.mean", 2)
    claim("tau-max advantage CI lower", 1.56, un["tau_max_advantage_over_last"]["ci95"][0], "...:advantage.ci95[0]", 2)
    claim("tau-max advantage CI upper", 3.09, un["tau_max_advantage_over_last"]["ci95"][1], "...:advantage.ci95[1]", 2)

    # ---- retrieval evidence
    rt = load("outputs/analysis/a1_retrieval_evidence.json")
    rb = rt["widest_matched_pair_tol003"]
    claim("retrieval pairs", 536, rt["n_pairs"], "...a1_retrieval_evidence:n_pairs", 0)
    claim("retrieval matched dCG", 0.016, rb["dCG"], "...:widest_matched_pair_tol003.dCG", 3)
    claim("retrieval R@1 low", 8.96, rb["a"]["R1"], "...:tol003.a.R1", 2)
    claim("retrieval R@1 high", 70.71, rb["b"]["R1"], "...:tol003.b.R1", 2)
    claim("retrieval R@1 spread", 61.8, rb["spread"], "...:tol003.spread", 1)
    claim("retrieval tau-R@1 correlation", -0.17, rt["correlation"]["tau_vs_R1"], "...:correlation.tau_vs_R1", 2)
    claim("retrieval CG-R@1 correlation", -0.23, rt["correlation"]["CG_vs_R1"], "...:correlation.CG_vs_R1", 2)

    # ---- two further backbones and DTD/Food-101 intervals (final round)
    mbb = load("outputs/analysis/a1_matched_gap_morebackbones.json")["models"]
    claim("CLIP B/16 matched spread", 35.5, mbb["clip16"]["max_matched_gap_spread_tol003"]["spread"],
          "...matched_gap_morebackbones:clip16.spread", 1)
    claim("CLIP L/14 matched spread", 39.6, mbb["vitl"]["max_matched_gap_spread_tol003"]["spread"],
          "...:vitl.spread", 1)
    claim("CLIP B/16 frozen top-1", 64.1, mbb["clip16"]["frozen"]["top1"], "...:clip16.frozen.top1", 1)
    claim("CLIP L/14 frozen top-1", 70.5, mbb["vitl"]["frozen"]["top1"], "...:vitl.frozen.top1", 1)
    claim("DTD spread CI lower (abs)", 8.1, abs(mb["dtd"]["widest_matched_pair"]["ci95"][1]),
          "...more_benchmarks:dtd.ci95 abs lower", 1)
    claim("DTD spread CI upper (abs)", 12.0, abs(mb["dtd"]["widest_matched_pair"]["ci95"][0]),
          "...:dtd.ci95 abs upper", 1)
    claim("Food-101 spread CI lower (abs)", 10.7, abs(mb["food101"]["widest_matched_pair"]["ci95"][1]),
          "...:food101.ci95 abs lower", 1)
    claim("Food-101 spread CI upper (abs)", 13.3, abs(mb["food101"]["widest_matched_pair"]["ci95"][0]),
          "...:food101.ci95 abs upper", 1)
    claim("DTD contraction gain", 17.8, mb["dtd"]["contraction"]["top1_gain"], "...:dtd.contraction", 1)
    claim("Food-101 contraction gain", 18.2, mb["food101"]["contraction"]["top1_gain"], "...:food101.contraction", 1)

    # ---- dense sweep, real checkpoints, lower bound (novelty round b)
    dense = load("outputs/analysis/a1_matched_gap_dense.json")["models"]
    d_spreads = {tag: v["matched_tol003"]["spread"] for tag, v in dense.items() if v.get("matched_tol003")}
    claim("dense spread CLIP B/32", 50.6, d_spreads["clip32"], "...a1_matched_gap_dense:clip32", 1)
    claim("dense spread CLIP B/16", 54.4, d_spreads["clip16"], "...:clip16", 1)
    claim("dense spread OpenCLIP", 48.0, d_spreads["openclip"], "...:openclip", 1)
    claim("dense spread SigLIP", 7.7, d_spreads["siglip"], "...:siglip", 1)
    claim("dense spread CLIP L/14", 62.0, d_spreads["vitl"], "...:vitl", 1)
    rp = load("outputs/analysis/a1_real_checkpoint_pairs.json")
    claim("real checkpoint pairs", 31, len(rp["pairs"]), "...a1_real_checkpoint_pairs:pairs", 0)
    claim("widest real pair spread", 6.6, rp["pairs"][0]["dtop1"], "...:pairs[0].dtop1", 1)
    claim("widest real pair dCG", 0.002, rp["pairs"][0]["dCG"], "...:pairs[0].dCG", 3)
    claim("DTD within-dataset spread", 2.2, rp["within_dataset"]["dtd"]["widest_pair_at_0.01"][0],
          "...:within_dataset.dtd", 1)
    claim("DTD within-dataset dCG", 0.001, rp["within_dataset"]["dtd"]["widest_pair_at_0.01"][1],
          "...:within_dataset.dtd dCG", 3)
    lb = load("outputs/analysis/a1_lower_bound_constants.json")
    claim("class-spread constant L", 1.013, lb["text_embedding_spread_L"], "...a1_lower_bound_constants:L", 3)
    mm = load("outputs/analysis/a1_margin_mass.json")
    claim("margin mass at eps=0.01", 0.681, mm["correlation_with_top1"] and
          next(r for r in mm["rows"] if r["family"] == "frozen")["mass_eps_0.01"],
          "...a1_margin_mass:frozen.mass_eps_0.01", 3)
    claim("margin mass at eps=0.02", 0.875, next(r for r in mm["rows"] if r["family"] == "frozen")["mass_eps_0.02"],
          "...:frozen.mass_eps_0.02", 3)
    claim("mass(0.01) vs top-1 correlation", -0.996, mm["correlation_with_top1"]["mass_eps_0.01"],
          "...:correlation_with_top1.mass_eps_0.01", 3)
    claim("CG vs top-1 correlation (same pool)", -0.154, mm["correlation_with_top1"]["CG"],
          "...:correlation_with_top1.CG", 3)

    # ---- statistic showdown and robustness (final round)
    sd = load("outputs/analysis/a1_statistic_showdown.json")["correlation_with_top1"]
    claim("showdown CG classification r", -0.154, sd["classification"]["CG"], "...a1_statistic_showdown:cls.CG", 3)
    claim("showdown CG retrieval r", -0.223, sd["retrieval"]["CG"], "...:ret.CG", 3)
    claim("showdown tau classification r", 0.832, sd["classification"]["tau5"], "...:cls.tau5", 3)
    claim("showdown tau retrieval r", -0.143, sd["retrieval"]["tau5"], "...:ret.tau5", 3)
    claim("showdown M(0.01) classification r", -0.996, sd["classification"]["mass_0.01"], "...:cls.mass_0.01", 3)
    claim("showdown M(0.01) retrieval r", -0.970, sd["retrieval"]["mass_0.01"], "...:ret.mass_0.01", 3)
    claim("showdown M(0.02) classification r", -0.988, sd["classification"]["mass_0.02"], "...:cls.mass_0.02", 3)
    claim("showdown M(0.02) retrieval r", -0.921, sd["retrieval"]["mass_0.02"], "...:ret.mass_0.02", 3)
    rb = load("outputs/analysis/a1_robustness.json")
    claim("half-sample spread first", 32.7, rb["half_sample"]["first"]["widest_spread_at_0.03"],
          "...a1_robustness:half_sample.first", 1)
    claim("half-sample spread second", 32.6, rb["half_sample"]["second"]["widest_spread_at_0.03"],
          "...:half_sample.second", 1)
    bp = rb["real_pair_binomial"]
    claim("real pair difference", 6.64, bp["difference"], "...:real_pair_binomial.difference", 2)
    claim("real pair standard error", 0.99, bp["se"], "...:real_pair_binomial.se", 2)
    claim("real pair CI lower", 4.70, bp["ci95"][0], "...:real_pair_binomial.ci95[0]", 2)
    claim("real pair CI upper", 8.58, bp["ci95"][1], "...:real_pair_binomial.ci95[1]", 2)
    claim("real pair z", 6.7, bp["z"], "...:real_pair_binomial.z", 1)

    # ---- Williams tests and selection rule (strengthening round 3)
    wt = load("outputs/analysis/a1_williams_tests.json")
    claim("Williams CG vs M classification t", 7.2, wt["classification"]["williams"]["CG vs M(0.01)"]["t"],
          "...a1_williams_tests:classification.CG vs M(0.01).t", 1)
    claim("Williams CG vs M classification p", 4.7e-06, wt["classification"]["williams"]["CG vs M(0.01)"]["p"],
          "...:classification.CG vs M(0.01).p", 4)
    claim("Williams CG vs M retrieval t", 6.1, wt["retrieval"]["williams"]["CG vs M(0.01)"]["t"],
          "...:retrieval.CG vs M(0.01).t", 1)
    claim("Williams CG vs M retrieval p", 2.6e-05, wt["retrieval"]["williams"]["CG vs M(0.01)"]["p"],
          "...:retrieval.CG vs M(0.01).p", 4)
    claim("Williams CG vs tau classification p", 7.2e-05, wt["classification"]["williams"]["CG vs tau"]["p"],
          "...:classification.CG vs tau.p", 4)
    claim("Williams CG vs tau retrieval p", 0.75, wt["retrieval"]["williams"]["CG vs tau"]["p"],
          "...:retrieval.CG vs tau.p", 2)
    sel = load("outputs/analysis/a1_selection_rule.json")["selection"]
    claim("selection oracle top-1 (synthetic)", 78.1, sel["synthetic_configs"]["oracle_top1"],
          "...a1_selection_rule:synthetic_configs.oracle_top1", 1)
    claim("min-CG regret (synthetic)", 44.4, sel["synthetic_configs"]["rules"]["min_CG"]["regret"],
          "...:synthetic_configs.rules.min_CG.regret", 1)
    claim("min-M regret (synthetic)", 0.0, sel["synthetic_configs"]["rules"]["min_M(0.01)"]["regret"],
          "...:synthetic_configs.rules.min_M(0.01).regret", 1)
    tl = sel["templates"]
    claim("template regret min-M CLIP B/32", 1.7, tl["clip32"]["rules"]["min_mass_0.01"]["regret"],
          "...:templates.clip32.rules.min_mass_0.01.regret", 1)
    claim("template regret default CLIP B/32", 1.0, tl["clip32"]["rules"]["default_template"]["regret"],
          "...:templates.clip32.rules.default_template.regret", 1)
    claim("template rho CLIP B/32", -0.71, tl["clip32"]["spearman_mass_top1"], "...:templates.clip32.rho", 2)

    # ---- real fine-tuning campaign and per-epoch monitor
    ca = load("outputs/analysis/a1_campaign_analysis.json")
    claim("campaign runs", 18, ca["n_runs"], "...a1_campaign_analysis:n_runs", 0)
    claim("campaign checkpoints", 72, ca["n_checkpoints"], "...:n_checkpoints", 0)
    claim("campaign pairs at 0.03", 670, ca["pairs"]["n_pairs_at_tol"]["0.03"], "...:pairs.n_pairs_at_tol.0.03", 0)
    claim("campaign pairs at 0.01", 254, ca["pairs"]["n_pairs_at_tol"]["0.01"], "...:pairs.n_pairs_at_tol.0.01", 0)
    claim("campaign widest pair spread", 48.5, ca["pairs"]["widest"]["all"]["dtop1"], "...:widest.all.dtop1", 1)
    claim("campaign widest pair dCG", 0.0242, ca["pairs"]["widest"]["all"]["dCG"], "...:widest.all.dCG", 4)
    claim("campaign widest pair CI low", -47.0, ca["pairs"]["widest"]["all"]["ci95_of_dtop1"][0],
          "...:widest.all.ci95[0]", 1)
    claim("campaign widest pair CI high", -50.0, ca["pairs"]["widest"]["all"]["ci95_of_dtop1"][1],
          "...:widest.all.ci95[1]", 1)
    claim("campaign within-run spread", 19.6, ca["pairs"]["widest"]["within_run"]["dtop1"], "...:widest.within.dtop1", 1)
    claim("campaign within-run dCG", 0.0125, ca["pairs"]["widest"]["within_run"]["dCG"], "...:widest.within.dCG", 4)
    claim("campaign correlate CG", 0.577, ca["correlation"]["CG"], "...:correlation.CG", 3)
    claim("campaign correlate tau", 0.987, ca["correlation"]["tau5"], "...:correlation.tau5", 3)
    claim("campaign correlate M(0.01)", -0.987, ca["correlation"]["M(0.01)"], "...:correlation.M(0.01)", 3)
    claim("campaign correlate M(0.02)", -0.908, ca["correlation"]["M(0.02)"], "...:correlation.M(0.02)", 3)
    claim("campaign min-M regret", 0.06, ca["selection"]["summary"]["min_M(0.01)"]["mean_regret"],
          "...:selection.summary.min_M(0.01)", 2)
    claim("campaign tau regret", 0.0, ca["selection"]["summary"]["max_tau5"]["mean_regret"],
          "...:selection.summary.max_tau5", 2)
    claim("campaign min-CG regret", 5.65, ca["selection"]["summary"]["min_CG"]["mean_regret"],
          "...:selection.summary.min_CG", 2)
    claim("campaign last-epoch regret", 13.8, ca["selection"]["summary"]["last_epoch"]["mean_regret"],
          "...:selection.summary.last_epoch", 1)

    # ---- upgrade round: template robustness, real retrieval, within-run, cross-domain, stopping scope
    tpl = load("outputs/analysis/a1_margin_templates.json")
    m_sp, cg_sp, r_m, r_cg = [], [], [], []
    for _tag, _v in tpl["models"].items():
        _top = [r["top1"] for r in _v["rows"]]
        _m = [r["mass_0.01"] for r in _v["rows"]]
        _cg = [r["CG"] for r in _v["rows"]]
        _n = len(_top)
        _mean = lambda x: sum(x) / len(x)
        _cov = sum((a - _mean(_top)) * (b - _mean(_m)) for a, b in zip(_top, _m))
        _sx = (sum((a - _mean(_top)) ** 2 for a in _top)) ** 0.5
        _sy = (sum((b - _mean(_m)) ** 2 for b in _m)) ** 0.5
        r_m.append(_cov / (_sx * _sy))
        _cov2 = sum((a - _mean(_top)) * (b - _mean(_cg)) for a, b in zip(_top, _cg))
        _sy2 = (sum((b - _mean(_cg)) ** 2 for b in _cg)) ** 0.5
        r_cg.append(_cov2 / (_sx * _sy2))
        m_sp.append(max(_m) - min(_m))
        cg_sp.append(max(_cg) - min(_cg))
    claim("template M(0.01) spread min", 0.032, min(m_sp), "...a1_margin_templates", 3)
    claim("template M(0.01) spread max", 0.047, max(m_sp), "...a1_margin_templates", 3)
    claim("template CG spread min", 0.025, min(cg_sp), "...a1_margin_templates", 3)
    claim("template CG spread max", 0.094, max(cg_sp), "...a1_margin_templates", 3)
    claim("template r(M,top1) min", -0.91, min(r_m), "...a1_margin_templates", 2)
    claim("template r(M,top1) max", -0.84, max(r_m), "...a1_margin_templates", 2)
    claim("template r(CG,top1) min", -0.16, min(r_cg), "...a1_margin_templates", 2)
    claim("template r(CG,top1) max", 0.20, max(r_cg), "...a1_margin_templates", 2)
    ret = load("outputs/analysis/a1_retrieval_realfinetune.json")
    claim("retrieval real frozen R@1", 18.4, ret["frozen"]["R@1_i2t"], "...a1_retrieval_realfinetune:frozen", 1)
    _rows = [c for ck in ret["runs"].values() for c in ck]
    claim("retrieval real best R@1", 29.4, max(c["R@1_i2t"] for c in _rows), "...a1_retrieval_realfinetune", 1)
    claim("retrieval real min CG", 0.49, min(c["CG"] for c in _rows), "...a1_retrieval_realfinetune", 2)
    claim("retrieval real checkpoints", 18, len(_rows), "...a1_retrieval_realfinetune", 0)
    wr = load("outputs/analysis/a1_showdown_within_run.json")["within_run_pearson"]
    claim("within-run r(M)", -0.99, wr["M(0.01)"]["mean"], "...a1_showdown_within_run", 2)
    claim("within-run r(tau)", 0.99, wr["tau5"]["mean"], "...a1_showdown_within_run", 2)
    claim("within-run r(CG)", -0.43, wr["CG"]["mean"], "...a1_showdown_within_run", 2)
    cr = load("outputs/analysis/a1_campaign_crossdomain.json")
    _crows = [c for ck in cr["runs"].values() for c in ck]
    claim("cross-domain top1 min", 44.4, min(c["top1"] for c in _crows), "...a1_campaign_crossdomain", 1)
    claim("cross-domain top1 max", 54.6, max(c["top1"] for c in _crows), "...a1_campaign_crossdomain", 1)
    cert = load("outputs/analysis/a1_certificate_rule.json")
    claim("stopping rule mean regret", 2.77, cert["recommended"]["mean_regret"], "...a1_certificate_rule", 2)
    claim("last-epoch mean regret", 13.8, cert["baselines"]["last_epoch"]["mean_regret"], "...a1_certificate_rule", 1)
    claim("first-epoch mean regret", 0.0, cert["baselines"]["first_epoch"]["mean_regret"], "...a1_certificate_rule", 2)
    it = load("outputs/analysis/a1_certificate_interior.json")
    _irows = [c for ck in it["runs"].values() for c in ck]
    claim("interior control runs", 4, len(it["runs"]), "...a1_certificate_interior", 0)
    claim("interior control n", 24, len(_irows), "...a1_certificate_interior", 0)

    # ---- interior-optimum monitoring validation (v2: 2 backbones x 2 datasets x 3 seeds x 10 epochs)
    mon = load("outputs/analysis/a1_monitor_interior_v2.json")
    rules = load("outputs/analysis/a1_monitor_interior_v2_rules.json")
    _n = rules["correlation"]["n_checkpoints"]
    claim("interior v2 checkpoints", 120, _n, "...a1_monitor_interior_v2_rules", 0)
    claim("interior v2 r(M,top1)", -0.986, rules["correlation"]["pooled_M"], "...a1_monitor_interior_v2_rules", 3)
    claim("interior v2 r(CG,top1)", 0.781, rules["correlation"]["pooled_CG"], "...a1_monitor_interior_v2_rules", 3)
    claim("interior v2 min-M mean regret", 0.41, rules["rules"]["minM"]["mean_regret"], "...a1_monitor_interior_v2_rules", 2)
    claim("interior v2 seq-M 0.01 mean regret", 0.50, rules["rules"]["seqM0.01"]["mean_regret"],
          "...a1_monitor_interior_v2_rules", 2)
    claim("interior v2 min-CG mean regret", 1.53, rules["rules"]["minCG"]["mean_regret"],
          "...a1_monitor_interior_v2_rules", 2)
    claim("interior v2 last-epoch mean regret", 0.60, rules["rules"]["last"]["mean_regret"],
          "...a1_monitor_interior_v2_rules", 2)
    claim("interior v2 first-epoch mean regret", 3.54, rules["rules"]["first"]["mean_regret"],
          "...a1_monitor_interior_v2_rules", 2)
    claim("interior v2 gap rule mean regret", 1.68, rules["rules"]["seqCG0.01"]["mean_regret"],
          "...a1_monitor_interior_v2_rules", 2)

    # ---- early-stopping baselines (3 datasets x 2 seeds x 10 epochs)
    base = load("outputs/analysis/a1_stopping_baselines_rules.json")
    claim("baseline checkpoints", 60, base["correlation"]["n"], "...a1_stopping_baselines_rules", 0)
    claim("baseline min-M mean regret", 0.18, base["rules"]["minM"]["mean_regret"]
          if "minM" in base["rules"] else base["rules"]["min_M"]["mean_regret"], "...a1_stopping_baselines_rules", 2)
    claim("baseline max-softmax mean regret", 2.80, base["rules"]["max_softmax"]["mean_regret"],
          "...a1_stopping_baselines_rules", 2)
    claim("baseline max-logit mean regret", 3.15, base["rules"]["max_logit"]["mean_regret"],
          "...a1_stopping_baselines_rules", 2)
    claim("baseline entropy mean regret", 3.96, base["rules"]["min_entropy"]["mean_regret"],
          "...a1_stopping_baselines_rules", 2)
    claim("baseline energy mean regret", 4.18, base["rules"]["min_energy"]["mean_regret"],
          "...a1_stopping_baselines_rules", 2)
    claim("baseline first-epoch mean regret", 9.52, base["rules"]["first"]["mean_regret"],
          "...a1_stopping_baselines_rules", 2)
    claim("baseline last-epoch mean regret", 3.63, base["rules"]["last"]["mean_regret"],
          "...a1_stopping_baselines_rules", 2)

    # ---- expanded-set monitoring comparison (extra seeds + fourth domain)
    comb = load("outputs/analysis/a1_monitor_combined.json")
    _r = comb["rules"]
    claim("combined runs", 20, comb["n_runs"], "...a1_monitor_combined", 0)
    claim("combined checkpoints", 200, comb["correlation"]["n_checkpoints"], "...a1_monitor_combined", 0)
    claim("combined min-M mean regret", 1.70, _r["minM"]["mean_regret"], "...a1_monitor_combined", 2)
    claim("combined min-M max regret", 10.00, _r["minM"]["max_regret"], "...a1_monitor_combined", 2)
    claim("combined last-epoch mean regret", 1.32, _r["last"]["mean_regret"], "...a1_monitor_combined", 2)
    claim("combined first-epoch mean regret", 7.25, _r["first"]["mean_regret"], "...a1_monitor_combined", 2)
    claim("combined sequential mean regret", 3.82, _r["seqM"]["mean_regret"], "...a1_monitor_combined", 2)
    claim("combined entropy mean regret", 1.91, _r["minEntropy"]["mean_regret"], "...a1_monitor_combined", 2)
    claim("combined max-softmax mean regret", 2.26, _r["maxSoftmax"]["mean_regret"], "...a1_monitor_combined", 2)
    claim("combined max-logit mean regret", 3.91, _r["maxLogit"]["mean_regret"], "...a1_monitor_combined", 2)
    claim("combined energy mean regret", 3.74, _r["minEnergy"]["mean_regret"], "...a1_monitor_combined", 2)
    claim("combined pooled r(M)", -0.977, comb["correlation"]["pooled_M"], "...a1_monitor_combined", 3)

    # ---- split-size stratified monitoring diagnosis
    split = load("outputs/analysis/a1_monitor_split_diagnosis.json")
    _s, _l = split["summary"]["small"], split["summary"]["large"]
    claim("large-split runs", 16, _l["n_runs"], "...a1_monitor_split_diagnosis", 0)
    claim("large-split min-M mean regret", 0.58, _l["mean_regret_minM"], "...a1_monitor_split_diagnosis", 2)
    claim("large-split last-epoch mean regret", 0.52, _l["mean_regret_last_epoch"], "...a1_monitor_split_diagnosis", 2)
    claim("large-split first-epoch mean regret", 3.55, _l["mean_regret_first_epoch"], "...a1_monitor_split_diagnosis", 2)
    claim("small-split runs", 4, _s["n_runs"], "...a1_monitor_split_diagnosis", 0)
    claim("small-split min-M mean regret", 6.18, _s["mean_regret_minM"], "...a1_monitor_split_diagnosis", 2)
    claim("small-split last-epoch mean regret", 4.51, _s["mean_regret_last_epoch"], "...a1_monitor_split_diagnosis", 2)
    claim("small-split min-M regret in SE", 1.08, _s["mean_regret_minM_in_SE"], "...a1_monitor_split_diagnosis", 2)

    # ---- epoch sweep correlation (manuscript abstract/intro/epoch subsection)
    import collections
    import numpy as np
    swe = load("outputs/a1_epoch_sweep.json")
    traj = collections.defaultdict(list)
    for c in swe["checkpoints"]:
        traj[(c["dataset"], c["seed"])].append(c)
    pears = []
    for v in traj.values():
        v = sorted(v, key=lambda r: r["epoch"])
        t = np.array([r["tau5"] for r in v])
        y = np.array([r.get("top1_5k", r.get("top1")) for r in v])
        pears.append(float(np.corrcoef(t, y)[0, 1]))
    claim("epoch-sweep mean Pearson", 0.93, float(np.mean(pears)), "a1_epoch_sweep.json: mean per-trajectory Pearson", 2)

    # ---- boundary law across benchmarks
    cb = load("outputs/analysis/a1_crossbenchmark_closed_form.json")["benchmarks"]
    ks = [v["k_best_this_benchmark"] for v in cb.values()]
    maes = [v["mae_k055"] for v in cb.values()]
    claim("boundary k min", 0.36, min(ks), "...crossbenchmark:k_best_this_benchmark min", 2)
    claim("boundary k max", 0.98, max(ks), "...:k_best_this_benchmark max", 2)
    claim("boundary MAE min", 0.079, min(maes), "...:mae_k055 min", 3)
    claim("boundary MAE max", 0.120, max(maes), "...:mae_k055 max", 3)

    # ---- manuscript-level counts
    tex = io.open(REPO / "paper_a1" / "main.tex", encoding="utf-8").read()
    import re
    abs_m = re.search(r"\\begin\{abstract\}(.*?)\\end\{abstract\}", tex, re.S)
    sys.path.insert(0, str(REPO))
    from tools.paper_audit.texutil import count_words
    words = count_words(abs_m.group(1)) if abs_m else 0
    claim("abstract words (audit counter)", 243, words, "paper_a1/main.tex abstract, texutil.count_words", 0)
    kw = re.search(r"\\begin\{keyword\}(.*?)\\end\{keyword\}", tex, re.S)
    n_kw = len([x for x in kw.group(1).split(r"\sep") if x.strip()]) if kw else 0
    claim("keywords", 5, n_kw, "paper_a1/main.tex keyword env", 0)

    print(f"\n  A1 claims: {ok} pass / {bad} fail / {ok + bad} total")
    payload = {"manuscript": "paper_a1", "claims": LEDGER, "pass": ok, "fail": bad}
    if ap:
        io.open(OUT, "w", encoding="utf-8", newline="").write(json.dumps(payload, indent=1))
        print("  wrote", OUT.relative_to(REPO))
    return 0 if bad == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
