# -*- coding: utf-8 -*-
r"""Add the 2026-11-02 literature-scan references to the live manuscript sources.

Idempotent: every insertion checks a marker and every anchor is asserted before any file is written, so a second
run is a no-op. Nothing under SUBMISSION/ is touched (frozen packages stay frozen); this edits the working sources
that will feed the next revision of each manuscript.

Usage
  python tools/_p1900_scan_refs_2026_11_02.py
"""
import io
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


# ----------------------------------------------------------------------------- helpers
def read(path):
    return io.open(os.path.join(ROOT, path), encoding="utf-8").read()


def write(path, text):
    io.open(os.path.join(ROOT, path), "w", encoding="utf-8", newline="").write(text)


def plan_append(path, marker, text):
    """Append text once, if marker is absent."""
    return ("append", path, marker, text)


def plan_replace(path, marker, anchor, replacement):
    """Replace anchor (must occur exactly once) with replacement, once."""
    return ("replace", path, marker, (anchor, replacement))


BIB_ENTRIES = {
    "uotgap2026": r"""@article{uotgap2026,
  author  = {Yang, Zonglin and Ma, Huilan and Zheng, Xudan and Xie, Yuejun},
  title   = {{UOT-Gap}: A Variational Principle for the Modality Gap in Vision-Language Models via Unbalanced Optimal Transport},
  journal = {arXiv preprint arXiv:2609.10224},
  year    = {2026},
  doi     = {10.48550/arXiv.2609.10224}
}""",
    "beyondgap2026": r"""@inproceedings{beyondgap2026,
  author    = {Yan, Hanqi and Cui, Xiangxiang and Yin, Lu and Gu, Jindong and Liang, Paul Pu and He, Yulan and Wang, Yifei},
  title     = {Beyond Cross-Modal Alignment: Measuring and Leveraging Modality Gap in Vision-Language Models},
  booktitle = {Findings of the Association for Computational Linguistics: ACL 2026},
  pages     = {12123--12138},
  year      = {2026},
  doi       = {10.18653/v1/2026.findings-acl.588}
}""",
    "convergent2026": r"""@article{convergent2026,
  author  = {Anonymous},
  title   = {The Convergent Representation of Vision-Language Contrastive Learning: Geometry, Modality Gap and Shared Space Alignment},
  journal = {HAL preprint hal-05611582},
  year    = {2026},
  note    = {HAL: hal-05611582}
}""",
    "artifactaudit2026": r"""@article{artifactaudit2026,
  author  = {Tang, Haolun and Zhan, Jingyi and Feng, Yan and Chen, Zhipeng},
  title   = {An Artifact Audit of Budget-Dependent {LoRA} Rank Comparisons},
  journal = {Research Square preprint},
  year    = {2026},
  doi     = {10.21203/rs.3.rs-10426794/v1}
}""",
    "variablerank2026": r"""@inproceedings{variablerank2026,
  author    = {Ploner, Max and Akbik, Alan},
  title     = {Variable-Rank Adaptation: A Comprehensive Survey of Rank Budgeting {LoRA} Variants},
  booktitle = {Findings of the Association for Computational Linguistics: EMNLP 2026},
  pages     = {52150--52172},
  year      = {2026},
  doi       = {10.18653/2026.findings-emnlp.2430}
}""",
    "rsra2026": r"""@article{rsra2026,
  author  = {Liu, Jiaqi and Kang, Haidong and Zhao, Qihui and Yu, Guo and Wang, Jingchao},
  title   = {{RSRA}: Training-Free Probing of Representation Sensitivity for Efficient {LoRA} Rank Allocation},
  journal = {arXiv preprint arXiv:2607.09757},
  year    = {2026},
  doi     = {10.48550/arXiv.2607.09757}
}""",
    "gradimpgrpo2026": r"""@inproceedings{gradimpgrpo2026,
  author    = {Sawant, Yash Ganpat},
  title     = {When Gradient Importance Lies: Adaptive {LoRA} Rank Allocation Fails Under {GRPO}},
  booktitle = {Proceedings of the Seventh Workshop on Insights from Negative Results in NLP},
  pages     = {110--114},
  year      = {2026},
  doi       = {10.18653/2026.insights-1.14}
}""",
    "photogrammetricrecord2026": r"""@article{photogrammetricrecord2026,
  author  = {Zhou, Yue and Zhong, Zhihang and Feng, Litong and Zhang, Wayne and Jiang, Xue and Yan, Junchi and Yang, Xue},
  title   = {Towards Vision-Language Geo-Foundation Models: A Survey},
  journal = {The Photogrammetric Record},
  volume  = {41},
  year    = {2026},
  doi     = {10.1111/phor.70066}
}""",
}

OPS = []

# --------------------------------------------------------------------- Paper A (paper合)
OPS += [
    plan_append("paper合/references.bib", "@article{uotgap2026,", "\n" + BIB_ENTRIES["uotgap2026"] + "\n"),
    plan_append("paper合/references.bib", "@inproceedings{beyondgap2026,", "\n" + BIB_ENTRIES["beyondgap2026"] + "\n"),
    plan_append("paper合/references.bib", "@article{convergent2026,", "\n" + BIB_ENTRIES["convergent2026"] + "\n"),
    plan_replace(
        "paper合/sections/related_work.tex",
        "uotgap2026",
        "which produces the better retrieval need not be the same site at all.",
        "which produces the better retrieval need not be the same site at all. Two 2026 accounts extend the "
        "measurement side of that argument: UOT-Gap~\\cite{uotgap2026} decomposes the gap with unbalanced optimal "
        "transport into distributional and pairwise contributions that relate to retrieval, and~\\cite{beyondgap2026} "
        "measure the gap and ask when it is useful rather than harmful; a geometric account of shared-space convergence "
        "appears in~\\cite{convergent2026}. None of the three varies the adaptation site with the backbone frozen, which "
        "is the manipulation used here.",
    ),
]

# ------------------------------------------------------------------------ P3 (paper3)
OPS += [
    plan_append("paper3/paper_ieee/references.bib", "@article{artifactaudit2026,", "\n" + BIB_ENTRIES["artifactaudit2026"] + "\n"),
    plan_append("paper3/paper_ieee/references.bib", "@inproceedings{variablerank2026,", "\n" + BIB_ENTRIES["variablerank2026"] + "\n"),
    plan_append("paper3/paper_ieee/references.bib", "@article{rsra2026,", "\n" + BIB_ENTRIES["rsra2026"] + "\n"),
    plan_append("paper3/paper_ieee/references.bib", "@inproceedings{gradimpgrpo2026,", "\n" + BIB_ENTRIES["gradimpgrpo2026"] + "\n"),
    plan_replace(
        "paper3/paper_ieee/sections/related_work.tex",
        "rsra2026",
        "IGU-LoRA~\\cite{igulora2025} applies integrated gradients for pathwise sensitivity estimation.",
        "IGU-LoRA~\\cite{igulora2025} applies integrated gradients for pathwise sensitivity estimation; "
        "RSRA~\\cite{rsra2026} instead probes representation sensitivity without training, and the variable-rank "
        "family is now surveyed in~\\cite{variablerank2026}.",
    ),
    plan_replace(
        "paper3/paper_ieee/sections/discussion.tex",
        "artifactaudit2026",
        "was an artefact of the token budget, not of the architecture.",
        "was an artefact of the token budget, not of the architecture. A concurrent audit of budget-dependent rank "
        "comparisons~\\cite{artifactaudit2026} reaches the same conclusion from the other direction, and a "
        "negative-results study reports that gradient-importance-based allocation fails under "
        "GRPO~\\cite{gradimpgrpo2026}.",
    ),
]

# ------------------------------------------------------------------------- A1 (paper_a1)
A1_BIB = r"""
\bibitem[Xu, 2026]{xu2026modalitygap}
Xu, Y., Wang, Y., Wu, Z., Song, K., Lin, J., \& Shen, Z. (2026). Do vision-language models truly perform vision reasoning? A rigorous study of the modality gap. arXiv:2604.16256. DOI: 10.48550/arXiv.2604.16256.
\bibitem[Yan, 2026]{yan2026beyondgap}
Yan, H., Cui, X., Yin, L., Gu, J., Liang, P. P., He, Y., \& Wang, Y. (2026). Beyond cross-modal alignment: measuring and leveraging modality gap in vision-language models. Findings of ACL 2026, pp.~12123--12138. DOI: 10.18653/v1/2026.findings-acl.588.
"""
OPS += [
    plan_replace("paper_a1/main.tex", "xu2026modalitygap", "\\end{thebibliography}", A1_BIB + "\\end{thebibliography}"),
    plan_replace(
        "paper_a1/related_work.tex",
        "xu2026modalitygap",
        "We show that order statistics of the class-relative similarity structure---not gap magnitude---are the operative quantity for zero-shot health under perturbation.",
        "We show that order statistics of the class-relative similarity structure---not gap magnitude---are the "
        "operative quantity for zero-shot health under perturbation. Concurrent work measures what the gap does on "
        "reasoning tasks~\\cite{xu2026modalitygap} and asks when it is useful rather than "
        "harmful~\\cite{yan2026beyondgap}; both are consistent with treating the gap as a descriptive rather than a "
        "normative quantity, which is the position this paper formalizes.",
    ),
]

# ------------------------------------------------------------------------- A2 (paper_a2)
A2_BIB = r"""
\bibitem{sonarllm2026}
C. Su, L. Ma, L. Dong, G. Tang, W. Yin, H. Chen, Z. Yu, ``SonarLLM: a native sonar--optical multimodal large language model for underwater perception,'' arXiv:2608.24325, 2026.
\bibitem{alam2026robust}
M. A. U. Alam, ``Robust cross-modal foundation model perception for underwater robots under degraded visual conditions,'' arXiv:2608.19710, 2026.
"""
OPS += [
    plan_replace("paper_a2/main_ieee.tex", "sonarllm2026", "\\end{thebibliography}", A2_BIB + "\\end{thebibliography}"),
    plan_replace(
        "paper_a2/main_ieee.tex",
        "sonarllm2026",
        "it is the question this paper answers.",
        "it is the question this paper answers. Native sonar--optical multimodal models have begun to "
        "appear~\\cite{sonarllm2026}, and cross-modal foundation-model perception under degraded visibility has been "
        "benchmarked~\\cite{alam2026robust}; neither reports an alignment-health diagnostic.",
    ),
]

# ---------------------------------------------------------------- survey (paper_rsvlm_survey)
OPS += [
    plan_append("paper_rsvlm_survey/isprsj/References.bib", "@article{photogrammetricrecord2026,", "\n" + BIB_ENTRIES["photogrammetricrecord2026"] + "\n"),
    plan_replace(
        "paper_rsvlm_survey/isprsj/01_introduction.tex",
        "photogrammetricrecord2026",
        "document the resulting model zoo and dataset catalogue~\\cite{xiangvisionlanguage2024,luvision2025,xiaofoundation2025,wengvisionlanguage2025}.",
        "document the resulting model zoo and dataset catalogue~\\cite{xiangvisionlanguage2024,luvision2025,xiaofoundation2025,wengvisionlanguage2025}, "
        "including a 2026 survey of geospatial vision--language foundation models~\\cite{photogrammetricrecord2026}, "
        "a survey of data-driven remote-sensing vision--language models~\\cite{zhoudatadriven2026} and a survey of "
        "spatiotemporal vision--language models~\\cite{liuremote2025}.",
    ),
]


def main():
    # pass 1: validate every op
    problems = []
    for kind, path, marker, payload in OPS:
        text = read(path)
        if marker in text:
            continue
        if kind == "replace":
            anchor = payload[0]
            if text.count(anchor) != 1:
                problems.append("%s: anchor occurs %d times: %r" % (path, text.count(anchor), anchor[:60]))
    if problems:
        print("ABORT: anchors not unique/present")
        for p in problems:
            print("  -", p)
        return 1

    # pass 2: apply
    changed = {}
    skipped = 0
    for kind, path, marker, payload in OPS:
        text = changed.get(path, read(path))
        if marker in text:
            skipped += 1
            continue
        if kind == "append":
            text = text.rstrip() + payload
        else:
            anchor, replacement = payload
            text = text.replace(anchor, replacement, 1)
        changed[path] = text
    for path, text in changed.items():
        write(path, text)
        print("updated:", path)
    print("ops applied:", len(changed), "files | already present:", skipped)
    return 0


if __name__ == "__main__":
    sys.exit(main())
