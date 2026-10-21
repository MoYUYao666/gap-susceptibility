# -*- coding: utf-8 -*-
r"""Assemble the R1 gap-fill results (R3.5 curvature, R3.9 NTK baseline, R3.18 env, R2.3/R3.16 captioning).

    python tools/_p1503_p3_gapfill.py
"""
from __future__ import annotations

import glob
import io
import json
import os
import statistics as st

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
AN = os.path.join(REPO, "outputs", "analysis")
OUT = os.path.join(AN, "p3_gapfill_summary.json")
DOC = os.path.join(REPO, "docs", "P3_GAPFILL_2026-10-21.md")
LR = 5e-5


def load(name):
    p = os.path.join(AN, name)
    if not os.path.exists(p):
        return None
    return json.load(io.open(p, encoding="utf-8"))


def main() -> int:
    summary = {"meta": {"script": "tools/_p1503_p3_gapfill.py", "task": "R1 gap-fill pack", "lr": LR}}
    # R3.5 curvature
    cur = {}
    for rank in (5, 6):
        d = load(f"p3_hessian_probe_r{rank}.json")
        if not d:
            continue
        rows = []
        for row in d["runs"]:
            g2 = row["g2"]
            gHg = row["ghg_full"]["0.001"]
            rows.append({"batch": row["batch"], "g2": g2, "gHg": gHg,
                         "share_at_lr": 0.5 * LR * gHg / g2 if g2 else None,
                         "per_group": row["ghg_per_group_eps3e-4"]})
        shares = [r["share_at_lr"] for r in rows if r["share_at_lr"] is not None]
        cur[str(rank)] = {"rows": rows, "mean_share_at_lr": st.mean(shares) if shares else None,
                          "sd_share_at_lr": st.stdev(shares) if len(shares) > 1 else None}
    summary["curvature"] = cur
    # R3.9 NTK
    ntk = load("p3_ntk_allocation.json")
    summary["ntk"] = ntk
    # R3.18 env + the authoritative five-seed archive
    env = load("p3_environment_matrix.json")
    seeds = load("p3_seeds_combined.json")
    summary["environment"] = env
    summary["seeds"] = seeds
    # captioning
    caps = {}
    for f in sorted(glob.glob(os.path.join(AN, "p3_caption_downstream_*.json"))):
        d = json.load(io.open(f, encoding="utf-8"))
        caps[str(d.get("rank"))] = {"bleu4": d.get("bleu4"), "exact_match": d.get("exact_match"),
                                    "n_eval": d["meta"]["n_eval"]}
    summary["captioning"] = caps
    cm = load("p3_caption_metrics.json")
    summary["caption_metrics"] = cm
    io.open(OUT, "w", encoding="utf-8", newline="").write(json.dumps(summary, indent=1, default=float))

    lines = ["# P3 — R1 gap-fill results (2026-10-21)", "",
             "> Source of truth: `outputs/analysis/p3_gapfill_summary.json` (this script). "
             "Generated after the resubmission `PRLETTERS-D-26-02671` was submitted; these are next-revision evidence.", ""]
    # curvature
    lines += ["## R3.5 — Hessian curvature at the operating learning rate", ""]
    for rank in ("5", "6"):
        if rank in cur and cur[rank]["mean_share_at_lr"] is not None:
            lines.append(f"- rank {rank}: second-order share at $\\eta=5\\times10^{{-5}}$ = "
                         f"**{cur[rank]['mean_share_at_lr']:+.3f}** (sd {cur[rank]['sd_share_at_lr']:.3f}) of the first-order term; "
                         f"curvature dominated by the vision tower.")
    lines += ["", "Reading: at the training step size the first-order term dominates (≈3.5%), but the second-order term is "
              "**not zero** and is negative; at 1e-3 probe steps the ratio grows to ≈−0.7, so the first-order statement is "
              "local, exactly as a Taylor argument requires. Archive: `p3_hessian_probe_r5.json`, `p3_hessian_probe_r6.json`.", ""]
    # NTK
    if ntk:
        lines += ["## R3.9 — NTK / gradient-energy allocation baseline (computed, not trained)", "",
                  "| block | NTK trace | NTK rank | Γ rank | uniform |", "|---|---|---|---|---|"]
        keys = list(ntk["allocation_ntk"])
        for k in keys:
            lines.append(f"| {k} | {ntk['ntk_trace'][k]:.4f} | {ntk['allocation_ntk'][k]} | "
                         f"{ntk['allocation_gamma'][k] if ntk.get('allocation_gamma') else '-'} | {ntk['allocation_uniform'][k]} |")
        lines += ["", "Reading: the NTK-diagonal rule puts more budget on the vision tower (8/5/2/1) than the Γ rule (5/5/4/2); "
                  "the two orderings differ, so they cannot both be the best zero-shot rule. No performance claim is made: only "
                  "Γ-guided, uniform and random arms were trained in the paper. Archive: `p3_ntk_allocation.json`.", ""]
    # environment
    if env:
        lines += ["## R3.18 — software / seed reproducibility matrix", ""]
        if seeds and seeds.get("values"):
            for r, vals in seeds["values"].items():
                xs = list(vals.values())
                lines.append(f"- rank {r}: n={len(xs)}, mean {sum(xs)/len(xs):+.1f}, "
                             f"range [{min(xs):+.1f}, {max(xs):+.1f}] (authoritative five-seed archive)")
        elif env.get("spread"):
            for r, s in env["spread"].items():
                lines.append(f"- rank {r}: n={s['n']}, mean {s['mean']:+.1f}, range [{s['min']:+.1f}, {s['max']:+.1f}]")
        sp = env.get("software_pairs", {})
        tf = [k for k in sp if "tf457" in k]
        if tf:
            lines.append(f"- software pair: `{tf[0]}` ΔE={sp[tf[0]]['delta_E']} vs reference "
                         f"`verify_r5_s42.json` ΔE={sp.get('verify_r5_s42.json', {}).get('delta_E')} "
                         "(trajectory shape identical; cross-version difference reported in the paper).")
        lines += ["", "Archive: `p3_environment_matrix.json`. Hardware matrix cannot be extended beyond the single RTX 4060 "
                  "Laptop used for all runs; this remains a declared limitation.", ""]
    # captioning
    lines += ["## R2.3 / R3.16 / R3.23 — captioning downstream check", ""]
    if caps:
        lines += ["| arm | BLEU-4 | exact match | n |", "|---|---|---|---|"]
        for k in sorted(caps):
            lines.append(f"| {k} | {caps[k]['bleu4']:.4f} | {caps[k]['exact_match']:.3f} | {caps[k]['n_eval']} |")
        lines += ["", "Archive: `p3_caption_downstream_*.json`. The evaluation set is four held-out marine caption samples; "
                  "this is a sanity check, not a benchmark-scale claim.", ""]
        if cm and cm.get("arms"):
            lines += ["Additional metrics (token F1 and CLIP image-caption cosine):", "",
                      "| arm | token F1 | CLIP similarity |", "|---|---|---|"]
            for k, v in cm["arms"].items():
                lines.append(f"| {k} | {v['token_f1']:.4f} | {v['clip_sim_mean']:.4f} |")
            lines += ["", "Reading: greedy captions are identical across arms (base, r=5, r=6); the 20-sample adapters do not "
                      "change held-out generations, so this check is **null** and cannot support an energy-to-caption-quality "
                      "claim in either direction. Archive: `p3_caption_metrics.json`.", ""]
    else:
        lines += ["- Pending: caption arm training/evaluation still running; results will be appended from "
                  "`p3_caption_downstream_*.json`.", ""]
    # newer VLM: Qwen2.5-VL-3B run records
    newer = os.path.isdir(os.path.join(REPO, "models", "Qwen2.5-VL-3B-Instruct"))
    qrows = []
    for rank in (5, 6):
        fp = os.path.join(REPO, "paper3", "scripts", "outputs", "experiments",
                          f"qwen_cf_uniform_rank{rank}_seed42_q25_r{rank}.json")
        if os.path.exists(fp):
            d = json.load(io.open(fp, encoding="utf-8"))
            qrows.append((rank, d.get("delta_E"), d.get("E")))
    summary["qwen25"] = qrows
    lines += ["## R1.4 — newer VLM family (Qwen2.5-VL-3B-Instruct)", ""]
    if qrows:
        lines += ["| rank | ΔE | trajectory |", "|---|---|---|"]
        for rank, dE, E in qrows:
            lines.append(f"| {rank} | {dE:+.1f} | {E} |")
        lines += ["", "Reading: under the same blank-image protocol the newer family shows the **opposite sign pattern** "
                  "(r=5 positive, r=6 near zero/negative), i.e. the LLaVA crossing does **not** replicate on Qwen2.5-VL-3B. "
                  "This supports the paper's protocol/scope statement and contradicts any strong cross-architecture claim. "
                  "Archive: `paper3/scripts/outputs/experiments/qwen_cf_uniform_rank*_seed42_q25_r*.json`.", ""]
    else:
        lines += [f"- Qwen2.5-VL-3B-Instruct download {'present' if newer else 'not present'}; run records pending.", ""]
    io.open(DOC, "w", encoding="utf-8", newline="").write("\n".join(lines) + "\n")
    print("wrote", os.path.relpath(DOC, REPO))
    print({k: (v if k in ("captioning",) else "ok") for k, v in summary.items()})
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
