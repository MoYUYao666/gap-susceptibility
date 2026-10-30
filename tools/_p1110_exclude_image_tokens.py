# -*- coding: utf-8 -*-
r"""Fix the text-side pooling: the image tokens must be excluded, otherwise the metric compares a tensor with itself.

Found by the sanity check (`tools/_p1109`): on one batch of four pairs,

    sequence length 596, of which 576 are image tokens (id 32000)
    cos(I, T) = 0.99971 .. 0.99979
    || T_excluding_image - T_all || = 51 .. 56   (raw norms are ~60-70)

The text side averaged over **all** non-padding positions, which on a LLaVA sequence are mostly image tokens, so
the two sides were nearly the same pooled tensor and DG* came out at 4.3e-4 -- a self-comparison, not an
image-text distance. `tools/_p47_qwen_train.py` masks the vision range out of the text side and this rewrite
does the same.

Both occurrences of the text mask in the recomputation script are replaced, and the script asserts that the
replacement landed.

    python tools/_p1110_exclude_image_tokens.py [--apply]
"""
from __future__ import annotations

import argparse
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
TARGET = REPO / "tools" / "_p1107_run_canonical.py"

OLD = """    hid = out.hidden_states[-1]
    mask = inp["attention_mask"].unsqueeze(-1).to(hid.dtype)
    T = (hid * mask).sum(1) / mask.sum(1).clamp(min=1)
    tok = inp["input_ids"]
    vm = (tok == IMG_ID).unsqueeze(-1).to(hid.dtype)
    n = vm.sum(1)
    I = (hid * vm).sum(1) / n.clamp(min=1) if float(n.min()) > 0 else T
    return F.normalize(I.float(), p=2, dim=-1), F.normalize(T.float(), p=2, dim=-1)
"""

NEW = """    hid = out.hidden_states[-1]
    tok = inp["input_ids"]
    # The image tokens must be excluded from the text side. On a LLaVA sequence they are 576 of ~596
    # positions, so averaging over every non-padding position makes T almost the same tensor as I and the
    # metric degenerates into a self-comparison: measured cos(I,T) = 0.9997 and DG* = 4.3e-4, while the
    # difference between including and excluding them has norm 51-56 against raw norms of ~60-70.
    # `tools/_p47_qwen_train.py` masks the vision range out for the same reason.
    mask_txt = inp["attention_mask"].bool() & (tok != IMG_ID)
    m = mask_txt.unsqueeze(-1).to(hid.dtype)
    T = (hid * m).sum(1) / m.sum(1).clamp(min=1)
    vm = (tok == IMG_ID).unsqueeze(-1).to(hid.dtype)
    n = vm.sum(1)
    I = (hid * vm).sum(1) / n.clamp(min=1) if float(n.min()) > 0 else T
    return F.normalize(I.float(), p=2, dim=-1), F.normalize(T.float(), p=2, dim=-1)
"""


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    a = ap.parse_args()
    t = TARGET.read_text(encoding="utf-8")
    if "mask_txt" in t:
        print("  already fixed")
        return 0
    assert t.count(OLD) == 1, f"expected one occurrence, found {t.count(OLD)}"
    t = t.replace(OLD, NEW, 1)
    print("  text-side mask now excludes the image tokens")
    if not a.apply:
        print("  (dry run)")
        return 0
    TARGET.write_text(t, encoding="utf-8", newline="")
    import ast
    ast.parse(t)
    check = TARGET.read_text(encoding="utf-8")
    assert "tok != IMG_ID" in check and "mask_txt" in check
    print("  written and verified")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
