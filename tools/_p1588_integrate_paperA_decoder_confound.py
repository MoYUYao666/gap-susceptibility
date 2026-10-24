# -*- coding: utf-8 -*-
r"""Integrate the Paper A decoder-confound section, disambiguate the two tables' sign glyphs,
and repair the provenance mapping of `tab:vlm` / `tab:llava`.

Evidence: `docs/paperA_decoder_confound_paragraph.md` and `outputs/analysis/paperA_decoder_confound.json`
(built by `tools/_p1580_paperA_decoder_confound.py`).

    python tools/_p1588_integrate_paperA_decoder_confound.py [--apply]
"""
from __future__ import annotations

import argparse
import io
import json
import os

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
os.chdir(REPO)

SUPP = "paper合/sections/supplement.tex"

SECTION_H = r"""
\section*{H. What the two decoder experiments do and do not separate}
\label{sec:decoderconfound}

The two decoder experiments move the measured gap in opposite directions, and the difference is not
attributable to any single factor on this evidence. On Qwen2-VL-2B-Instruct a contrastive objective
narrows $DG^*$ under all three adaptation arms, by $98.57\pm0.44\%$ (both-position), $96.74\pm0.29\%$
(text-only) and $89.41\pm1.01\%$ (vision-only) over thirteen seeds with disjoint seed ranges, whereas on
LLaVA-1.5-7B a caption-generation objective widens it under all three, by $73.27\pm7.54\%$ (text-only),
$121.48\pm16.33\%$ (vision-only) and $95.66\pm7.91\%$ (both-position) over three seeds. Each model's own
sign is stable: it survives the change of text-side convention on LLaVA, no archived Qwen2-VL-2B run of any
construction increases the gap, and no arm mean changes sign when the seeds are resampled. The two
experiments, however, differ simultaneously in training objective, parameter scale ($2$B against $7$B),
pretraining family, dataset (Flickr30k against MS-COCO), training-set size ($320$ against $1500$ pairs) and
evaluation-set size ($320$ against $500$ pairs), so the sign cannot be assigned to the objective, to scale or
to the data here. Isolating it requires holding model, data, budget and adaptation-site specification fixed
and varying only the loss, which the present archive does not contain. The per-run records and this
decomposition are archived in \texttt{outputs/analysis/paperA\_decoder\_confound.json}.
"""

CAPTION_E_OLD = ("after $L_2$ normalisation, image-token pool against caption pool, with no projection; the reduction is relative to\n"
                 "the untrained model ($DG^* = 0.7778$, $\\mathrm{CG} = 0.7421$).")
CAPTION_E_NEW = ("after $L_2$ normalisation, image-token pool against caption pool, with no projection; the reduction is relative to\n"
                 "the untrained model ($DG^* = 0.7778$, $\\mathrm{CG} = 0.7421$) and a positive entry denotes a gap smaller than the\n"
                 "untrained model's.")

CAPTION_G_OLD = ("change is relative to the untrained model ($DG^* = 0.3566$). The objective is caption generation, so")
CAPTION_G_NEW = ("change is relative to the untrained model ($DG^* = 0.3566$) and a positive entry denotes a gap larger than the\n"
                 "untrained model's. The objective is caption generation, so")

PROV = {
    "tab:vlm": {
        "script": "tools/_p1164_verify_pull_analyze_e.py",
        "archive": "outputs/vlm_clean_summary.json",
        "archives": ["outputs/vlm_clean_summary.json", "outputs/vlm_clean_cloud/frozen_baseline.json"],
        "note": "per-arm means/sds from outputs/vlm_clean_cloud/{arm}_seed*.json (dg_star[2]); corrected in 2026-10-24 audit",
    },
    "tab:llava": {
        "script": "tools/_p1145_clean_gap_measure.py",
        "archive": "outputs/canonical_caption_metric.json",
        "archives": ["outputs/canonical_caption_metric.json"],
        "note": "runs.<tag>.clean.dg_star vs runs.frozen.clean.dg_star; corrected in 2026-10-24 audit",
    },
}
MAP_OLD = {
    '    "tab:vlm": (None, ["outputs/vlm_instruction_dynamics.json"]),':
        '    "tab:vlm": (None, ["outputs/vlm_clean_summary.json", "outputs/vlm_clean_cloud/frozen_baseline.json"]),',
    '    "tab:llava": (None, ["outputs/llava_instruction_dynamics.json"]),':
        '    "tab:llava": (None, ["outputs/canonical_caption_metric.json"]),',
}
MD_OLD = {
    "| `tab:llava` | `tools\\_p1432_provenance_map_paperA.py` | `outputs/llava_instruction_dynamics.json` | verified |":
        "| `tab:llava` | `tools\\_p1145_clean_gap_measure.py` | `outputs/canonical_caption_metric.json` | verified |",
    "| `tab:vlm` | `tools\\_p1432_provenance_map_paperA.py` | `outputs/vlm_instruction_dynamics.json` | verified |":
        "| `tab:vlm` | `tools\\_p1164_verify_pull_analyze_e.py` | `outputs/vlm_clean_summary.json` | verified |",
}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    a = ap.parse_args()

    t = io.open(SUPP, encoding="utf-8").read()
    assert "\\label{sec:decoderconfound}" not in t, "Section H already present"
    assert t.rstrip().endswith("construction for that reason."), "unexpected supplement tail"
    assert CAPTION_E_OLD in t and CAPTION_G_OLD in t, "caption patterns not found"
    t = t.replace(CAPTION_E_OLD, CAPTION_E_NEW, 1).replace(CAPTION_G_OLD, CAPTION_G_NEW, 1)
    t = t.rstrip() + "\n" + SECTION_H
    print("supplement: Section H appended, both table captions disambiguated")

    man = json.load(io.open("docs/provenance_manifest.json", encoding="utf-8"))
    floats = man["manuscripts"]["paperA"]["floats"]
    for f in floats:
        if f.get("label") in PROV:
            f.update(PROV[f["label"]])
            f["status"] = "verified"
    print("manifest json updated for tab:vlm / tab:llava")

    mp = io.open("tools/_p1432_provenance_map_paperA.py", encoding="utf-8").read()
    for old, new in MAP_OLD.items():
        assert old in mp, "mapping pattern not found: %s" % old
        mp = mp.replace(old, new, 1)
    print("mapping script updated")

    md = io.open("docs/PROVENANCE_MANIFEST_2026-10-20.md", encoding="utf-8").read()
    for old, new in MD_OLD.items():
        assert old in md, "manifest md row not found"
        md = md.replace(old, new, 1)
    print("manifest md updated")

    if a.apply:
        io.open(SUPP, "w", encoding="utf-8", newline="").write(t)
        json.dump(man, io.open("docs/provenance_manifest.json", "w", encoding="utf-8"), indent=1, ensure_ascii=False)
        io.open("tools/_p1432_provenance_map_paperA.py", "w", encoding="utf-8", newline="").write(mp)
        io.open("docs/PROVENANCE_MANIFEST_2026-10-20.md", "w", encoding="utf-8", newline="").write(md)
        print("applied")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())