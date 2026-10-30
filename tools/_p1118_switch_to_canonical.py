# -*- coding: utf-8 -*-
r"""Make the training sweep measure the canonical DG*/CG, and record it per run.

Operator decision 2026-10-17: option A -- retrain the twelve runs. Before spending 7.5 hours, the measurement
inside the sweep must produce the quantity the paper and the ODE use, and it must save real weights (the filter
is already fixed in `tools/_p1115`).

What changes here, and only this:

* `_sides` now does one full forward pass and takes the **last hidden state**, mean-pooling over the image-token
  positions for the vision side and over the **non-image** positions for the text side. The previous version
  called the vision tower by hand and compared projected features against token embeddings, and the text side
  still contained the image tokens -- which is what made the frozen metric a self-comparison (cos(I,T)=0.9997).
* `_gap_metrics` now computes the canonical trio from `src/dg_star_tracker.py`:
      DG*  = mean_i || I_i - T_i ||^2      (paired, squared)
      CG   = || mean_i I_i - mean_i T_i ||
      DG_e = sqrt(CG^2 + || sigma_I - sigma_T ||^2)
* the old definition is kept, under `legacy_*` keys, so the numbers stay comparable with the archived twelve.
* each record gains `dg_star`, `cg`, `dg_empirical` (and the legacy pair), so no post-hoc adapter loading is
  needed -- the whole reason the previous plan failed.

    python tools/_p1118_switch_to_canonical.py [--apply]
"""
from __future__ import annotations

import argparse
import ast
import re
import subprocess
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
SCRIPT = REPO / "tools" / "_p820_llava_sites.py"
PY = r"D:\Anaconda\envs\pytorch\python.exe"

NEW_SIDES = '''    def _sides(mm, batch_ids):
        """Canonical intra-batch sides: last hidden state, pooled per modality, L2-normalised.

        This replaces an earlier version that called the vision tower by hand and compared its projected output
        against token embeddings. That definition differed from the paper's in two ways, and the second one broke
        it: the text side averaged over every non-padding position, which on a LLaVA sequence means 576 image
        tokens out of ~596, so T was almost the same tensor as I (measured cos(I,T) = 0.9997) and DG* came out at
        4.3e-4 -- a self-comparison rather than an image-text distance.

        The definition here is the one in `src/dg_star_tracker.py`, applied with the pooling convention of
        `tools/_p47_qwen_train.py`: image tokens pooled for the vision side, non-image positions for the text side.
        """
        inp = make_batch(batch_ids, with_labels=False)
        inp = {k: (v.to(0) if hasattr(v, "to") else v) for k, v in inp.items()}
        with torch.no_grad():
            out = mm(**inp, output_hidden_states=True)
        hid = out.hidden_states[-1].float()
        tok = inp["input_ids"]
        img_id = int(getattr(getattr(mm, "config", None), "image_token_index", 32000))
        vm = (tok == img_id)
        txt_m = inp["attention_mask"].bool() & ~vm
        vm_f = vm.unsqueeze(-1).to(hid.dtype)
        txt_f = txt_m.unsqueeze(-1).to(hid.dtype)
        n_vis = vm_f.sum(1)
        I = (hid * vm_f).sum(1) / n_vis.clamp(min=1)
        T = (hid * txt_f).sum(1) / txt_f.sum(1).clamp(min=1)
        import torch.nn.functional as F
        return F.normalize(I, p=2, dim=-1), F.normalize(T, p=2, dim=-1)

'''

NEW_GAP = '''    def _gap_metrics(A, B):
        """The canonical trio from src/dg_star_tracker.py:compute, plus the legacy definition.

        `A` and `B` are already L2-normalised and row-aligned, so index i is the same image-caption pair on both
        sides -- which is what makes DG* a *paired* distance.
        """
        dg_star = float(((A - B) ** 2).sum(dim=-1).mean())
        cg = float((A.mean(0) - B.mean(0)).norm())
        var_term = float((A.std(dim=0) - B.std(dim=0)).norm() ** 2)
        dg_emp = (cg ** 2 + var_term) ** 0.5
        # legacy: mean cross-modal distance minus the two within-modality distances (the archived definition)
        legacy = float(torch.cdist(A, B).mean() - 0.5 * (torch.cdist(A, A).mean()
                                                         + torch.cdist(B, B).mean()))
        return cg, legacy, dg_star, dg_emp

'''


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    a = ap.parse_args()
    t = SCRIPT.read_text(encoding="utf-8")
    if "dg_star = float(" in t:
        print("  already switched")
        return 0

    # replace _gap_metrics
    m = re.search(r"    def _gap_metrics\(A, B\):\n(?:.*\n)*?        return cg, dg\n\n", t)
    assert m, "_gap_metrics not found"
    t = t[: m.start()] + NEW_GAP + t[m.end():]

    # replace _sides
    m = re.search(r"    def _sides\(mm, batch_ids\):\n(?:.*\n)*?        return V\.reshape\(-1, V\.shape\[-1\]\), T\n\n", t)
    assert m, "_sides not found"
    t = t[: m.start()] + NEW_SIDES + t[m.end():]

    # measure(): collect the canonical trio as well
    old_meas = """                cg, dg = _gap_metrics(V, T)
                cgs.append(cg)
                dgs.append(dg)
                n += len(chunk)
        if was_training:
            mm.train()
        return (st.mean(cgs) if cgs else None, st.mean(dgs) if dgs else None, n)
"""
    new_meas = """                cg, legacy, dg_star, dg_emp = _gap_metrics(V, T)
                cgs.append(cg)
                legacys.append(legacy)
                dg_stars.append(dg_star)
                dg_emps.append(dg_emp)
                n += len(chunk)
        if was_training:
            mm.train()
        mean = lambda xs: st.mean(xs) if xs else None
        return {"cg": mean(cgs), "legacy_dg": mean(legacys),
                "dg_star": mean(dg_stars), "dg_empirical": mean(dg_emps), "n": n}
"""
    assert t.count(old_meas) == 1, "measure return block not found once"
    t = t.replace(old_meas, new_meas, 1)
    t = t.replace("        cgs, dgs, n = [], [], 0\n",
                  "        cgs, legacys, dg_stars, dg_emps, n = [], [], [], [], 0\n", 1)

    ast.parse(t)
    print("  canonical metric wired into _sides / _gap_metrics / measure()")
    if not a.apply:
        print("  (dry run)")
        return 0
    SCRIPT.write_text(t, encoding="utf-8", newline="")
    r = subprocess.run([PY, "-c", "import ast,io;ast.parse(io.open(r'" + str(SCRIPT)
                        + "',encoding='utf-8').read());print('local parse ok')"], capture_output=True)
    print("  " + r.stdout.decode("utf-8", "replace").strip())
    if r.returncode != 0:
        print(r.stderr.decode("utf-8", "replace"))
        return 1
    check = SCRIPT.read_text(encoding="utf-8")
    for needle in ("dg_star = float(", "output_hidden_states=True", "legacy_dg", "tok == img_id"):
        print(f"    {needle:<28} {needle in check}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
