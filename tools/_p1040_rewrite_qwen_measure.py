# -*- coding: utf-8 -*-
r"""Rewrite the Qwen runner generator's measurement substitution to match what the probe found.

The earlier substitution assumed the vision tower could be called by hand with `pixel_values`, which is true
for LLaVA and false for Qwen:

    TypeError: Qwen2_5_VisionTransformerPretrainedModel.forward() missing 1 required positional argument:
    'grid_thw'

The probe (`tools/_p1039`) recorded the facts that make a correct replacement possible: the processor returns
`image_grid_thw` alongside `pixel_values`, a forward hook on `model.visual.merger` captures a **tensor** of
shape (587, 3584) for two COCO images, and the model yields 29 hidden states of shape (2, 418, 3584). So the
measurement takes both sides from one full forward pass: the merger hook gives the projected vision features,
and hidden state 0 gives the text embeddings of the non-image tokens.

    python tools/_p1040_rewrite_qwen_measure.py [--apply]
"""
from __future__ import annotations

import argparse
import ast
import subprocess
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
GEN = REPO / "tools" / "_p1034_make_qwen_runner.py"
PY = r"D:\Anaconda\envs\pytorch\python.exe"

NEW_BLOCK = '''SIDES_OLD = ('        inner = getattr(base, "model", base)\\n'
             '        vision = getattr(inner, "vision_tower", None)\\n'
             '        projector = getattr(inner, "multi_modal_projector", None)\\n'
             '        lm = getattr(inner, "language_model", None)\\n'
             '        if vision is None or projector is None or lm is None:\\n'
             '            raise RuntimeError(f"could not locate the submodules on {type(inner).__name__}")\\n')
SIDES_NEW = ('        # Qwen2.5-VL cannot be measured the LLaVA way: its tower needs the patch grid of its\\n'
             '        # dynamic resolution, and calling it with pixel_values alone raises\\n'
             '        #   Qwen2_5_VisionTransformerPretrainedModel.forward() missing 1 required positional\\n'
             '        #   argument: \\'grid_thw\\'\\n'
             '        # The processor does return that grid (`image_grid_thw`, recorded by tools/_p1039), and a\\n'
             '        # hook on `visual.merger` captures the projected vision features: a plain tensor, measured\\n'
             '        # (587, 3584) for two COCO images. Both sides therefore come from one full forward pass.\\n'
             '        inner = getattr(base, "model", base)\\n'
             '        merger = getattr(getattr(inner, "visual", None), "merger", None)\\n'
             '        lm = getattr(inner, "language_model", None)\\n'
             '        if merger is None or lm is None:\\n'
             '            raise RuntimeError(f"could not locate the submodules on {type(inner).__name__}")\\n'
             '        _cap = {}\\n'
             '\\n'
             '        def _hook(_mod, _inp, outp):\\n'
             '            _cap["v"] = outp\\n'
             '\\n'
             '        _h = merger.register_forward_hook(_hook)\\n'
             '        try:\\n'
             '            with torch.no_grad():\\n'
             '                res = mm(**inp, output_hidden_states=True)\\n'
             '        finally:\\n'
             '            _h.remove()\\n'
             '        V = _cap["v"]\\n'
             '        if isinstance(V, tuple):\\n'
             '            V = V[0]\\n'
             '        ids = inp["input_ids"]\\n'
             '        img_id = int(getattr(base.config, "image_token_id", None)\\n'
             '                     or getattr(base.config, "image_token_index", 151655))\\n'
             '        mask = inp["attention_mask"].bool() & (ids != img_id)\\n'
             '        T = res.hidden_states[0][mask]\\n'
             '        return V.reshape(-1, V.shape[-1]), T\\n')
'''


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    a = ap.parse_args()
    lines = GEN.read_text(encoding="utf-8").splitlines(keepends=True)
    start = next(i for i, l in enumerate(lines) if l.startswith("SIDES_OLD = "))
    end = next(i for i, l in enumerate(lines) if l.startswith("def main() -> int:"))
    print(f"  replacing lines {start + 1}..{end} ({end - start} lines) with the probe-based version")
    out = "".join(lines[:start]) + NEW_BLOCK + "\n" + "".join(lines[end:])
    ast.parse(out)

    # the three replacement pairs are now SIDES only; the vision/projector text stays untouched
    if "TEXT_OLD" in out or "IMG2_OLD" in out:
        # keep them only if they still have matching constants defined
        pass
    if not a.apply:
        print("  (dry run)")
        return 0
    GEN.write_text(out, encoding="utf-8", newline="")
    r = subprocess.run([PY, "-c", "import ast,io;ast.parse(io.open(r'" + str(GEN)
                        + "',encoding='utf-8').read());print('generator parses ok')"], capture_output=True)
    print("  " + r.stdout.decode("utf-8", "replace").strip())
    if r.returncode != 0:
        print(r.stderr.decode("utf-8", "replace"))
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
