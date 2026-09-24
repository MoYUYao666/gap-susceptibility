# -*- coding: utf-8 -*-
"""
P1 patch A9:
  (a) bibliography: Connector-S published at IJCAI 2025 (verified: ijcai.org/proceedings/2025/1202,
      DOI 10.24963/ijcai.2025/1202); GTMA has an IEEE Xplore version (doc 11463397) whose
      venue could not be verified -> recorded as a note rather than guessed.
  (b) related_work.tex:20 and visual_fragility.tex:12 used zhu2026fi -- an LLM-vulnerability
      paper -- as direct evidence about vision encoders; the transfer is now stated.
  (c) visual_fragility.tex:8 said yi2025decipher "proved" dimension collapse causes the gap.
"""
import io
import os
import sys

ROOT = r"D:\Realdesktop\Wan\Important\New"
EDITS = [
    # ---- (a) Connector-S -> IJCAI 2025 ----
    ("paper/references.bib",
     "@article{zhu2025connector,\n  title     = {Connector-{S}: A Survey of Connectors in Multi-modal Large\n               Language Models},\n  author    = {Zhu, Xun and Zhang, Zheng and Chen, Xi and Shi, Yiming\n               and Li, Miao and Wu, Ji},\n  journal   = {arXiv preprint arXiv:2502.11453},\n  year      = {2025},\n  doi       = {10.48550/arXiv.2502.11453},\n}",
     "@inproceedings{zhu2025connector,\n  title     = {Connector-{S}: A Survey of Connectors in Multi-modal Large\n               Language Models},\n  author    = {Zhu, Xun and Zhang, Zheng and Chen, Xi and Shi, Yiming\n               and Li, Miao and Wu, Ji},\n  booktitle = {Proceedings of the Thirty-Fourth International Joint Conference on\n               Artificial Intelligence (IJCAI)},\n  year      = {2025},\n  doi       = {10.24963/ijcai.2025/1202},\n}"),
    # ---- (a) GTMA published-version note ----
    ("paper/references.bib",
     "  journal   = {arXiv preprint arXiv:2512.18504},\n  year      = {2025},\n  doi       = {10.48550/arXiv.2512.18504},\n}",
     "  journal   = {arXiv preprint arXiv:2512.18504},\n  year      = {2025},\n  doi       = {10.48550/arXiv.2512.18504},\n  note      = {Published version: IEEE Xplore, document 11463397 (title: {GTMA}:\n               Dynamic Representation Optimization for {OOD} {VLMs})},\n}"),
    # ---- (b) zhu2026fi: state the transfer ----
    ("paper/sections/related_work.tex",
     "\\cite{zhu2026fi} identified that a small subset of parameters disproportionately contributes to model brittleness.",
     "\\cite{zhu2026fi} identified, in the LLM setting, that a small subset of parameters disproportionately contributes to model brittleness---a mechanism we conjecture transfers to vision encoders."),
    ("paper/sections/visual_fragility.tex",
     "a small subset of high-sensitivity parameters contributing disproportionately to brittleness~\\cite{zhu2026fi}.",
     "a small subset of high-sensitivity parameters contributing disproportionately to brittleness in the LLM setting~\\cite{zhu2026fi}, which we conjecture transfers to vision encoders."),
    # ---- (c) "proved" -> attributes ----
    ("paper/sections/visual_fragility.tex",
     "\\textbf{Dimensional collapse asymmetry.}~\\cite{yi2025decipher} proved that dimension collapse causes the modality gap.",
     "\\textbf{Dimensional collapse asymmetry.}~\\cite{yi2025decipher} attributes the modality gap to dimension collapse."),
]
fails = []
for rel, old, new in EDITS:
    p = os.path.join(ROOT, rel.replace("/", os.sep))
    src = io.open(p, encoding="utf-8").read()
    n = src.count(old)
    if n != 1:
        fails.append("%s: found %d :: %s" % (rel, n, old[:60]))
        print("FAIL %s (%d)" % (rel, n))
        continue
    io.open(p, "w", encoding="utf-8", newline="").write(src.replace(old, new, 1))
    print("ok   %s" % rel)
if fails:
    print(fails)
    sys.exit(1)
print("PATCH A9 APPLIED")
