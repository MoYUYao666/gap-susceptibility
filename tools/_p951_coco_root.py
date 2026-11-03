# -*- coding: utf-8 -*-
r"""Let the sweep read COCO from a directory given on the command line.

The run takes its image ids from the caption file's iteration order: `ids = [i for i in by_img if ...]`,
so **the annotation file decides which images are trained on, and in what order**. On the cloud the same
files must therefore be used, not a fresh download, or the cloud run would train on a different subset
while looking identical. This adds `--coco-root` (default `REPO/coco`) so a small fixture carrying exactly
the needed 700 images and their annotations can be placed anywhere.

    python tools/_p951_coco_root.py [--apply]
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

ARG_RE = re.compile(r'( *ap\.add_argument\("--out-dir", type=str, default="",\n(?: .*\n)*?.*\)\n)')
ARG_NEW = ('    ap.add_argument("--coco-root", type=str, default="",\n'
           '                    help="directory holding annotations/captions_val2014.json and val2014/")\n')

DATA_OLD = ('    ann = json.loads((REPO / "coco" / "annotations" / "captions_val2014.json").read_text(\n'
            '        encoding="utf-8", errors="ignore"))\n')
DATA_NEW = ('    coco_root = Path(a.coco_root) if a.coco_root else (REPO / "coco")\n'
            '    ann = json.loads((coco_root / "annotations" / "captions_val2014.json").read_text(\n'
            '        encoding="utf-8", errors="ignore"))\n')

IMG_OLD = '    img_dir = REPO / "coco" / "val2014"\n'
IMG_NEW = '    img_dir = coco_root / "val2014"\n'


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    a = ap.parse_args()

    t = SCRIPT.read_text(encoding="utf-8")
    if "--coco-root" in t:
        print("  already patched")
        return 0
    for name, anchor in (("out-dir anchor", ARG_RE.search(t).group(0) if ARG_RE.search(t) else None),
                         ("annotation load", DATA_OLD), ("image dir", IMG_OLD)):
        assert anchor, f"{name} not found"
    m = ARG_RE.search(t)
    out = t[: m.end(1)] + ARG_NEW + t[m.end(1):]
    assert out.count(DATA_OLD) == 1 and out.count(IMG_OLD) == 1
    out = out.replace(DATA_OLD, DATA_NEW, 1).replace(IMG_OLD, IMG_NEW, 1)
    ast.parse(out)
    print("  added --coco-root; the annotation file and image directory now come from it")
    if not a.apply:
        print("  (dry run)")
        return 0
    SCRIPT.write_text(out, encoding="utf-8", newline="")
    check = SCRIPT.read_text(encoding="utf-8")
    assert "--coco-root" in check and "coco_root" in check and 'REPO / "coco"' not in check
    r = subprocess.run([PY, "-c", "import ast,io;ast.parse(io.open(r'" + str(SCRIPT)
                        + "',encoding='utf-8').read());print('ok')"], capture_output=True)
    assert r.returncode == 0, r.stderr.decode("utf-8", "replace")
    print("  written; parses on the sweep's interpreter")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
