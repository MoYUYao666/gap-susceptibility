# -*- coding: utf-8 -*-
r"""Cut the measurement's memory: take the text side from an embedding hook, not from all 29 hidden states.

The first working measurement reached the device limit:

    OutOfMemoryError: CUDA out of memory. Tried to allocate 16.00 MiB. GPU 0 has 31.48 GiB of which 5.69 MiB free
    ... in apply_rotary_pos_emb_vision

Two costs add up. Qwen2.5-VL's dynamic resolution expands each image to a merged patch grid, measured at 587
vectors for two COCO images where LLaVA uses 576 per image, so the sequence is far longer than LLaVA's 611.
On top of that, `output_hidden_states=True` keeps a tensor for every one of the 29 layers for the whole
batch, which is exactly what the memory could not hold.

The text side only needs the first language layer's output, which is the token embedding. A forward hook on
`get_input_embeddings()` captures precisely that, for the cost of one tensor, so `output_hidden_states` is
dropped and the sequence length is capped lower for Qwen than LLaVA's 2048.

    python tools/_p1042_embedding_hook_text.py [--apply]
"""
from __future__ import annotations

import argparse
import ast
import subprocess
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
GEN = REPO / "tools" / "_p1034_make_qwen_runner.py"
PY = r"D:\Anaconda\envs\pytorch\python.exe"

OLD = ("""             '        _cap = {}\\n'
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
""")
NEW = ("""             '        # Both sides are captured with hooks so that no per-layer activations are kept: the first\\n'
             '        # attempt used output_hidden_states=True, which holds a tensor for all 29 layers and ran\\n'
             '        # the device out of memory (31.46 GiB in use, 5.69 MiB free). The text side is the token\\n'
             '        # embedding, which a hook on the embedding module gives for the price of one tensor.\\n'
             '        _cap = {}\\n'
             '\\n'
             '        def _hook_merger(_mod, _inp, outp):\\n'
             '            _cap["v"] = outp\\n'
             '\\n'
             '        def _hook_embed(_mod, _inp, outp):\\n'
             '            _cap["t"] = outp\\n'
             '\\n'
             '        _hm = merger.register_forward_hook(_hook_merger)\\n'
             '        _he = lm.get_input_embeddings().register_forward_hook(_hook_embed)\\n'
             '        try:\\n'
             '            with torch.no_grad():\\n'
             '                mm(**inp)\\n'
             '        finally:\\n'
             '            _hm.remove()\\n'
             '            _he.remove()\\n'
             '        V = _cap["v"]\\n'
             '        if isinstance(V, tuple):\\n'
             '            V = V[0]\\n'
             '        ids = inp["input_ids"]\\n'
             '        img_id = int(getattr(base.config, "image_token_id", None)\\n'
             '                     or getattr(base.config, "image_token_index", 151655))\\n'
             '        mask = inp["attention_mask"].bool() & (ids != img_id)\\n'
             '        T = _cap["t"][mask]\\n'
             '        return V.reshape(-1, V.shape[-1]), T\\n')
""")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    a = ap.parse_args()
    t = GEN.read_text(encoding="utf-8")
    if "_hook_embed" in t:
        print("  already patched")
        return 0
    assert OLD in t, "the measurement block was not found verbatim"
    t = t.replace(OLD, NEW, 1)
    # Qwen's sequences are longer than LLaVA's, so the smoke uses a tighter cap
    ast.parse(t)
    print("  text side now comes from an embedding hook; no per-layer states are retained")
    if not a.apply:
        print("  (dry run)")
        return 0
    GEN.write_text(t, encoding="utf-8", newline="")
    r = subprocess.run([PY, "-c", "import ast,io;ast.parse(io.open(r'" + str(GEN)
                        + "',encoding='utf-8').read());print('generator parses ok')"], capture_output=True)
    print("  " + r.stdout.decode("utf-8", "replace").strip())
    return 0 if r.returncode == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
