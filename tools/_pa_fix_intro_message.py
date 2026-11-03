# -*- coding: utf-8 -*-
r"""修正引言末尾重复出现的普适处方（2026-10-02）。

`introduction.tex:25` 与结论段重复了同一处方：

> "The central practical message remains simple---**protect the visual encoder, fine-tune the text
> modality**, and monitor the Distribution Gap---but now grounded in a dynamical theory that explains
> \\emph{why} this strategy works."

该处方已被 SigLIP 严格冻结对照否定其普适性（同预算同 seeds 同 rank：
CLIP text-only 更降间隙 t=+10.0；SigLIP **both** 更降间隙 t=−52.7）。
且 **both 在两架构上检索都更强** → "monitor the Distribution Gap" 作为唯一准则也不充分。

    python tools\_pa_fix_intro_message.py [--apply]
"""
from __future__ import annotations

import io
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
F = REPO / "paper合" / "sections" / "introduction.tex"

OLD = ("Together, these contributions establish a principled framework for understanding and predicting how "
       "parameter-efficient fine-tuning reshapes cross-modal representation geometry. The central practical "
       "message remains simple---protect the visual encoder, fine-tune the text modality, and monitor the "
       "Distribution Gap---but now grounded in a dynamical theory that explains \\emph{why} this strategy "
       "works.")

NEW = ("Together, these contributions establish a principled framework for understanding and predicting how "
       "parameter-efficient fine-tuning reshapes cross-modal representation geometry. The practical message "
       "is correspondingly qualified: where the encoders are InfoNCE-trained and the modality gap is the "
       "quantity of interest, adapting the text side while leaving the visual side alone is the safer "
       "default, and the dynamical theory explains why the dominant perturbation term vanishes in that "
       "configuration. Section~\\ref{sec:validation} shows that this default does not carry over to SigLIP "
       "unchanged, and that a smaller gap and better retrieval can point in different directions.")


def main() -> int:
    apply = "--apply" in sys.argv
    t = io.open(F, encoding="utf-8").read()
    c = t.count(OLD)
    if c != 1:
        print(f"  ⚠ 未命中（出现 {c} 次）")
        return 1
    print("  ✅ 命中引言末尾的普适处方")
    if apply:
        io.open(F, "w", encoding="utf-8", newline="").write(t.replace(OLD, NEW, 1))
        t2 = io.open(F, encoding="utf-8").read()
        assert "protect the visual encoder" not in t2, "断言失败：处方仍在"
        assert "does not carry over to SigLIP" in t2, "断言失败：未写入架构限定"
        print("  ✅ 已改并断言通过")
    else:
        print("  （预演，加 --apply 生效）")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
