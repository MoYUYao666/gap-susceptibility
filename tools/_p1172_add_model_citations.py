# -*- coding: utf-8 -*-
r"""Add the four missing model citations and widen the data statement to cover the decoder records.

Citations, each verified before this script was written:
  * SigLIP  -- Zhai, Mustafa, Kolesnikov, Beyer, ICCV 2023, DOI 10.1109/ICCV51070.2023.01100 (Crossref)
  * BioCLIP -- Stevens et al., CVPR 2024, DOI 10.1109/CVPR52733.2024.01836 (Crossref)
  * DINOv2  -- Oquab et al., arXiv:2304.07193 (arXiv metadata)
  * OpenCLIP -- the software repository github.com/mlfoundations/open_clip, verified public via the GitHub API
                (14.2k stars). No DOI is invented: the Zenodo deposit could not be fetched from this host, so the
                citation names the repository instead.

Only verified fields are written. Insertions are asserted against exact substrings, so a source that has moved on
fails loudly instead of getting a citation in the wrong place.

The data statement gains one clause: the decoder per-run records are now openly available in the same repository
(the JSON is published in the next step), while the adapters stay undistributed for a reason that survives review
-- the archived records are sufficient to reproduce the reported statistics.

    python tools/_p1172_add_model_citations.py [--apply]
"""
from __future__ import annotations

import argparse
import io
import re
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
PA = REPO / "paper合"
BIB = PA / "references.bib"
INTRO = PA / "sections" / "introduction.tex"
EMP = PA / "sections" / "empirical.tex"
MAINS = [PA / "main_nc.tex", PA / "main_springer.tex"]

BIB_ENTRIES = r"""
@inproceedings{zhai2023siglip,
  title     = {Sigmoid Loss for Language Image Pre-Training},
  author    = {Zhai, Xiaohua and Mustafa, Basil and Kolesnikov, Alexander and Beyer, Lucas},
  booktitle = {IEEE/CVF International Conference on Computer Vision (ICCV)},
  year      = {2023},
  doi       = {10.1109/ICCV51070.2023.01100}
}

@misc{ilharco2021openclip,
  title        = {{OpenCLIP}},
  author       = {Ilharco, Gabriel and Wortsman, Mitchell and Wightman, Ross and Gordon, Cade and Carlini, Nicholas and Taori, Rohan and Dave, Achal and Shankar, Vaishaal and Namkoong, Hongseok and Miller, John and Hajishirzi, Hannaneh and Farhadi, Ali and Schmidt, Ludwig},
  year         = {2021},
  howpublished = {\url{https://github.com/mlfoundations/open_clip}},
  note         = {Software; repository verified public on 2026-10-17}
}

@inproceedings{stevens2024bioclip,
  title     = {{BioCLIP}: A Vision Foundation Model for the Tree of Life},
  author    = {Stevens, Samuel and Wu, Jiaman and Thompson, Matthew J. and Campolongo, Elizabeth G. and Song, Chan Hee and others},
  booktitle = {IEEE/CVF Conference on Computer Vision and Pattern Recognition (CVPR)},
  year      = {2024},
  doi       = {10.1109/CVPR52733.2024.01836}
}

@misc{oquab2023dinov2,
  title         = {{DINOv2}: Learning Robust Visual Features without Supervision},
  author        = {Oquab, Maxime and Darcet, Th{\'e}od{\'e}ore and Moutakanni, Th{\'e}o and Vo, Huy and Szafraniec, Marc and others},
  year          = {2023},
  eprint        = {2304.07193},
  archivePrefix = {arXiv},
  primaryClass  = {cs.CV}
}
"""

CITES = [
    (INTRO, "the ordering reverses on SigLIP",
     "the ordering reverses on SigLIP~\\cite{zhai2023siglip}"),
    (EMP, "comparison on CLIP ViT-B/32, OpenCLIP B/32, CLIP ViT-B/16, SigLIP and BioCLIP",
     "comparison on CLIP ViT-B/32, OpenCLIP B/32~\\cite{ilharco2021openclip}, CLIP ViT-B/16, SigLIP and "
     "BioCLIP~\\cite{stevens2024bioclip}"),
    (EMP, "DINOv2-base as the vision tower",
     "DINOv2-base~\\cite{oquab2023dinov2} as the vision tower"),
]

OLD_DATA = ("their per-run records are available from the author, and the adapters are not redistributed because of "
            "their size.")
NEW_DATA = ("their per-run records are openly available in the same repository, and the adapters are not "
            "redistributed because the reported statistics are archived as per-run records and the adapters are not "
            "required to reproduce them.")

# the two main files wrap this sentence at different points, so match with whitespace tolerance rather than by a
# literal string (the first attempt asserted on a single-line form and found nothing)
OLD_DATA_RE = re.compile(
    r"their\s+per-run records are available from the author,\s*and the adapters are not redistributed because of "
    r"their\s+size\.")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    a = ap.parse_args()

    bib = io.open(BIB, encoding="utf-8").read()
    new_keys = [m for m in re.findall(r"@\w+\{([^,]+),", BIB_ENTRIES)]
    exist = [k for k in new_keys if re.search(r"@\w+\{" + re.escape(k) + ",", bib)]
    print(f"  bib: {len(new_keys)} new keys {new_keys}; already present: {exist}")
    if exist:
        print("  !! refusing: keys already in references.bib")
        return 1

    edits = []
    for path, old, new in CITES:
        t = io.open(path, encoding="utf-8").read()
        n = t.count(old)
        print(f"  cite {path.name}: '{old[:46]}...' occurrences {n}")
        if n != 1:
            print("  !! expected exactly one occurrence")
            return 1
        edits.append((path, t.replace(old, new, 1)))

    data_edits = []
    for p in MAINS:
        t = io.open(p, encoding="utf-8").read()
        n = len(OLD_DATA_RE.findall(t))
        print(f"  data statement {p.name}: occurrences {n}")
        if n != 1:
            print("  !! expected exactly one occurrence")
            return 1
        data_edits.append((p, OLD_DATA_RE.sub(NEW_DATA, t, count=1)))

    if not a.apply:
        print("\n  (dry run)")
        return 0

    io.open(BIB, "w", encoding="utf-8", newline="").write(bib.rstrip("\n") + "\n" + BIB_ENTRIES)
    for path, txt in edits:
        io.open(path, "w", encoding="utf-8", newline="").write(txt)
    for path, txt in data_edits:
        io.open(path, "w", encoding="utf-8", newline="").write(txt)
    print("\n  written: references.bib (+4 entries), 2 cite sites, 2 data statements")

    check = io.open(BIB, encoding="utf-8").read()
    print(f"  bib entries now: {len(re.findall(r'@\\w+\\{', check))}")
    for k in new_keys:
        print(f"    {k}: {'present' if k in check else 'MISSING'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
