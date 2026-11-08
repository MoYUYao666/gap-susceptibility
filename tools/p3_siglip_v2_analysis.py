# -*- coding: utf-8 -*-
"""Analyse the authoritative full-protocol SigLIP rank-4 arms (2026-11-08 cloud run).

Reads the per-arm `results.json` files pulled from the cloud (`outputs/analysis/siglip_v2`) and compares them with
(a) the archived rank-8 protocol target and (b) the archived rank-4 cells available in `outputs/siglip_strict`.
Writes `outputs/analysis/p3_siglip_full_rank4_2026-11-08.json`.
"""
import glob
import io
import json
import os
import statistics as st

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC = os.path.join(REPO, "outputs", "analysis", "siglip_v2")
SOC = os.path.join(REPO, "outputs", "siglip_strict")
OUT = os.path.join(REPO, "outputs", "analysis", "p3_siglip_full_rank4_2026-11-08.json")
EXPECTED_R8 = {"text_only": 0.0664, "both": -0.0114, "vision_only": 0.0522}


def summarize(path):
    rows = []
    for p in sorted(glob.glob(os.path.join(path, "**", "results.json"), recursive=True)):
        d = json.load(io.open(p, encoding="utf-8"))
        tag = os.path.basename(os.path.dirname(p)).replace("s7_siglip_lora_r4_", "")
        seed = os.path.basename(os.path.dirname(os.path.dirname(p))).replace("seed", "")
        cg0 = (d.get("initial_gap") or {}).get("centroid_gap")
        cg1 = (d.get("final_gap") or {}).get("centroid_gap")
        r1 = (d.get("test_metrics") or {}).get("R@1")
        rows.append({"tag": tag, "seed": seed, "dCG": round(cg1 - cg0, 5) if (cg0 is not None and cg1 is not None) else None,
                     "R@1": round(r1, 4) if r1 is not None else None})
    return rows


def main():
    rows = summarize(SRC)
    arms = {}
    for tag in sorted({r["tag"] for r in rows}):
        sub = [r for r in rows if r["tag"] == tag]
        dcgs = [r["dCG"] for r in sub if r["dCG"] is not None]
        r1s = [r["R@1"] for r in sub if r["R@1"] is not None]
        arms[tag] = {"n": len(sub), "seeds": [r["seed"] for r in sub],
                     "dCG_mean": round(st.mean(dcgs), 5), "dCG_sd": round(st.stdev(dcgs), 5) if len(dcgs) > 1 else 0.0,
                     "R@1_mean": round(st.mean(r1s), 4), "R@1_sd": round(st.stdev(r1s), 4) if len(r1s) > 1 else 0.0,
                     "archived_rank8_target": EXPECTED_R8.get(tag)}
    # archived rank-4 cells (s7_*) for text_only / both
    arc = {}
    for p in sorted(glob.glob(os.path.join(SOC, "seed*", "s7_siglip_lora_r4_*", "results.json"))):
        d = json.load(io.open(p, encoding="utf-8"))
        tag = os.path.basename(os.path.dirname(p)).replace("s7_siglip_lora_r4_", "")
        cg0 = (d.get("initial_gap") or {}).get("centroid_gap")
        cg1 = (d.get("final_gap") or {}).get("centroid_gap")
        arc.setdefault(tag, []).append(round(cg1 - cg0, 5))
    archived_r4 = {t: {"n": len(v), "dCG_mean": round(st.mean(v), 5)}
                   for t, v in arc.items() if len(v) >= 3}
    report = {"generated": "2026-11-08",
              "protocol": {"model": "siglip-base-patch16-224", "rank": 4, "alpha": 8, "batch_size": 128,
                           "epochs": 10, "max_samples": 5000, "corpus": "Flickr30k full image set",
                           "strict_freeze": "only LoRA A/B trainable (authoritative experiments/siglip_experiments.py)"},
              "arms": arms, "per_arm": rows,
              "archived_rank4_s7": archived_r4,
              "notes": ("The archived target values (+0.0664 / -0.0114 / +0.0522) come from the rank-8 cells in "
                        "outputs/siglip_strict (s4/s6); the task requirement is rank 4. The restored rank-4 cells are "
                        "compared with the rank-4 s7 archive where available (text_only, both) and quoted against the "
                        "rank-8 target only to show that the qualitative ordering is preserved.")}
    io.open(OUT, "w", encoding="utf-8", newline="").write(json.dumps(report, indent=1, ensure_ascii=False))
    print(json.dumps({"arms": arms, "archived_rank4_s7": archived_r4}, indent=1, ensure_ascii=False))


if __name__ == "__main__":
    main()
