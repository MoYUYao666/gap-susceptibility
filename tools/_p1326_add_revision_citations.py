# -*- coding: utf-8 -*-
r"""Backfill the citations identified by the 2026-10-19 literature check into the *local working copies*.

The submitted packages stay frozen (A1 -> PAA, Paper A -> Neurocomputing, P3 -> PRL); these edits are staged for the
revision round only. Three manuscripts are touched:

  A1   : Sharma & Saxena 2026 (arXiv:2609.36101) and Yaras et al. 2024 (arXiv:2412.07909), plus a differentiating
         paragraph in the modality-gap subsection and two bibliography entries.
  PaperA: Amblard's entry upgraded from the arXiv preprint to the IJMI journal version (DOI 10.1007/s13735-026-00423-w);
         two CLIP class-incremental-learning citations added, with one sentence in the gap subsection.
  P3   : StatLoRA (arXiv:2607.20205), IFCLoRA (arXiv:2607.22251) and LoRA-GA^2 (arXiv:2608.19800) added with a
         differentiating paragraph in the PEFT rank-allocation subsection.

    python tools/_p1326_add_revision_citations.py [--apply]
"""
from __future__ import annotations

import argparse
import io
import os

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

A1_MAIN = os.path.join(REPO, "paper_a1", "main.tex")
A1_RW = os.path.join(REPO, "paper_a1", "related_work.tex")
PA_BIB = os.path.join(REPO, "paper合", "references.bib")
PA_RW = os.path.join(REPO, "paper合", "sections", "related_work.tex")
P3_BIB = os.path.join(REPO, "paper3", "paper_ieee", "references.bib")
P3_RW = os.path.join(REPO, "paper3", "paper_ieee", "sections", "related_work.tex")

# ---------------------------------------------------------------- A1
A1_BIB = r"""
\bibitem[Sharma and Saxena, 2026]{sharma2026readout}
Sharma, A., Saxena, D. (2026). One geometry, different outcomes: readout-dependent effects of the modality gap in
vision-language models. arXiv:2609.36101.

\bibitem[Yaras et al., 2024]{yaras2026explaining}
Yaras, C., Chen, S., Wang, P., Qu, Q. (2024). Explaining and mitigating the modality gap in contrastive multimodal
learning. arXiv:2412.07909.
"""

A1_PAR = r"""
Two analyses sharpen this picture. Yaras et al.~\cite{yaras2026explaining} derive the gap from the gradient flow of the
contrastive objective, trace it to mismatched pairs and a learnable temperature, and report that closing the gap improves
retrieval. Sharma and Saxena~\cite{sharma2026readout} show that the image--text mean separation is approximately rank one
and decompose the similarity score along that direction, identifying a fixed offset that acts as a class bias in zero-shot
classification, a multiplicative ranking distortion under projection in retrieval, and a modality sort in mixed-modal
retrieval; they conclude that the effect of modifying the gap is readout-dependent. Our analysis is complementary but
statistical rather than geometric: we show that the gap, being a first-moment summary, cannot determine the ordering of any
similarity row, we bound the top-1 change that any such summary can hide by the margin mass, and we turn that bound into a
label-free certificate. The geometric account explains \emph{where} in the score the gap acts; the sufficiency statement
explains why matched gaps can hide tens of accuracy points, which no geometric decomposition alone delivers.
"""

A1_ANCHOR = ("Work that moves the \\emph{text}\ncluster as a means of manipulating the gap reports weak and inconsistent\n"
             "downstream effects \\cite{chowers2026}.")

# ---------------------------------------------------------------- Paper A
PA_AMB_OLD = r"""@article{amblard2025fill,
  title     = {Fill the Gap: Quantifying and Reducing the Modality Gap in
               Image-Text Representation Learning},
  author    = {Role, Fran{\c{c}}ois and Meyer, S{\'e}bastien and Amblard, Victor},
  journal   = {arXiv preprint arXiv:2505.03703},
  year      = {2025},
  doi       = {10.48550/arXiv.2505.03703},
}"""

PA_AMB_NEW = r"""@article{amblard2025fill,
  title     = {Quantifying and Reducing the Modality Gap in Both Contrastive and
               Generative Multimodal Vision--Language Models},
  author    = {Role, Fran{\c{c}}ois and Meyer, S{\'e}bastien and Amblard, Victor},
  journal   = {International Journal of Multimedia Information Retrieval},
  volume    = {15},
  number    = {4},
  year      = {2026},
  doi       = {10.1007/s13735-026-00423-w},
}"""

PA_BIB_ADD = r"""

@article{hu2026visualbranch,
  title   = {Visual Branch is What You Need for {CLIP}-based Class-Incremental Learning},
  author  = {Hu, Tao and Xie, Zhen-Hao and Guo, Jingcai and Zhan, De-Chuan and Zhou, Da-Wei},
  journal = {arXiv preprint arXiv:2609.37888},
  year    = {2026},
}

@article{he2026dulbe,
  title   = {Dual-Mode Low-Rank Learner with Bridge-Prototype Ensemble for Vision-Language Class-Incremental Learning},
  author  = {He, Chiyuan and Qiu, Zihuan and Meng, Fanman and Wang, Chao and Chen, Liangjiang and Xu, Linfeng and Wu,
             Qingbo and Li, Hongliang},
  journal = {arXiv preprint arXiv:2609.36759},
  year    = {2026},
}
"""

PA_PAR = r"""
The gap also decides which classifier to use at inference. Hu et al.~\cite{hu2026visualbranch} show that {CLIP} textual
weights deviate from visual class distributions because of the modality gap, and that constructing the incremental
classifier entirely in visual space is better; He et al.~\cite{he2026dulbe} bridge visual prototypes and text embeddings
through dual-mode low-rank updates to compensate for the textual decision boundary. Both observations are consistent with
our finding that the text and image clusters respond asymmetrically to adaptation.
"""

PA_ANCHOR = "\\subsection{Parameter-Efficient Fine-Tuning for VLMs}"

# ---------------------------------------------------------------- P3
P3_BIB_ADD = r"""

@article{gao2026statlora,
  title   = {Statistical Inference for Rank Allocation in Low-Rank Adaptation},
  author  = {Gao, Yihang and Tan, Vincent Y. F.},
  journal = {arXiv preprint arXiv:2607.20205},
  year    = {2026},
}

@article{zhang2026ifclora,
  title   = {{IFCLoRA}: Topology-Aware Rank Allocation for Parameter-Efficient Fine-Tuning},
  author  = {Zhang, Wei and Liu, Xinwu and Cheng, Yihang},
  journal = {arXiv preprint arXiv:2607.22251},
  year    = {2026},
}

@article{he2026loraga2,
  title   = {{LoRA-GA}$^2$: Low Rank Adaptation with Multi-step Gradient Adaptive Alignment},
  author  = {He, Haonan and Fan, Xinyue},
  journal = {arXiv preprint arXiv:2608.19800},
  year    = {2026},
}
"""

P3_PAR = r"""
More recent work continues this line. IFCLoRA~\cite{zhang2026ifclora} traces interventions on the frozen model to build a
module interaction graph and then allocates rank once, before fine-tuning; StatLoRA~\cite{gao2026statlora} casts allocation
as hypothesis testing and derives asymptotic guarantees for AdamW-type optimisers; LoRA-GA$^2$~\cite{he2026loraga2} probes
multi-step gradients and aligns the low-rank update with full fine-tuning. IFCLoRA is the closest in spirit, because it also
allocates before training; it nevertheless requires a calibration set and a graph-construction pass, whereas our rule is a
closed-form function of one gradient-geometry quantity, evaluated on the pretrained model, with no search, no calibration
set and no target-model gradient.
"""

P3_ANCHOR = ("F$^3$OCUS~\\cite{f3ocus2025} uses NTK eigenvalues for importance-based layer selection in federated VLM "
             "fine-tuning.")


def read(p):
    return io.open(p, encoding="utf-8").read()


def write(p, t):
    io.open(p, "w", encoding="utf-8", newline="").write(t)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    a = ap.parse_args()
    todo = []

    # ---- A1
    t = read(A1_MAIN)
    if "sharma2026readout" not in t:
        anchor = "\\end{thebibliography}"
        assert t.count(anchor) == 1, t.count(anchor)
        t = t.replace(anchor, A1_BIB.strip() + "\n\n" + anchor, 1)
        todo.append(("A1 bibliography", A1_MAIN, t))
    rw = read(A1_RW)
    if "sharma2026readout" not in rw:
        assert rw.count(A1_ANCHOR) == 1, rw.count(A1_ANCHOR)
        rw = rw.replace(A1_ANCHOR, A1_ANCHOR + "\n" + A1_PAR.strip() + "\n", 1)
        todo.append(("A1 related work", A1_RW, rw))

    # ---- Paper A
    b = read(PA_BIB)
    if "s13735-026-00423-w" not in b:
        assert b.count(PA_AMB_OLD) == 1, b.count(PA_AMB_OLD)
        b = b.replace(PA_AMB_OLD, PA_AMB_NEW, 1)
        b = b.rstrip("\n") + "\n" + PA_BIB_ADD.strip() + "\n"
        todo.append(("Paper A bibliography", PA_BIB, b))
    prw = read(PA_RW)
    if "hu2026visualbranch" not in prw:
        assert prw.count(PA_ANCHOR) == 1, prw.count(PA_ANCHOR)
        prw = prw.replace(PA_ANCHOR, PA_PAR.strip() + "\n\n" + PA_ANCHOR, 1)
        todo.append(("Paper A related work", PA_RW, prw))

    # ---- P3
    p3b = read(P3_BIB)
    if "gao2026statlora" not in p3b:
        p3b = p3b.rstrip("\n") + "\n" + P3_BIB_ADD.strip() + "\n"
        todo.append(("P3 bibliography", P3_BIB, p3b))
    p3rw = read(P3_RW)
    if "zhang2026ifclora" not in p3rw:
        assert p3rw.count(P3_ANCHOR) == 1, p3rw.count(P3_ANCHOR)
        p3rw = p3rw.replace(P3_ANCHOR, P3_ANCHOR + "\n" + P3_PAR.strip() + "\n", 1)
        todo.append(("P3 related work", P3_RW, p3rw))

    print(f"  edits pending: {len(todo)}")
    for name, path, _ in todo:
        print("   -", name, "->", os.path.relpath(path, REPO))
    if not a.apply:
        print("  (dry run)")
        return 0
    for _, path, content in todo:
        write(path, content)
    print("  written; now recompile the three manuscripts")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
