# -*- coding: utf-8 -*-
r"""Widen Table S3's first two columns so the method names do not wrap.

Table S3 (a table*, text width 7.16 in = 18.2 cm) was given 1.6 + 3.7 + 1.9 + 1.7 + 1.7 cm = 10.6 cm of
columns, which is well short of the width available, and "IGU-LoRA [3]" and "GFAP (Ours)" wrapped onto
two lines in the first column. The first two columns are widened and the columns are spread so the table
reads as a full-width table rather than a narrow block.

    python tools/_p919_widen_table_s3.py [--apply]
"""
from __future__ import annotations

import argparse
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
SUPP = REPO / "paper3" / "paper_ieee" / "supplementary" / "supplementary.tex"
B = chr(92)
P = B + "raggedright" + B + "arraybackslash"

OLD = (">{" + P + "}p{1.6cm}\n"
       + "                    >{" + P + "}p{3.7cm}\n"
       + "                    >{" + P + "}p{1.9cm}\n"
       + "                    >{" + P + "}p{1.7cm}\n"
       + "                    >{" + P + "}p{1.7cm}@{}}")
NEW = (">{" + P + "}p{2.2cm}\n"
       + "                    >{" + P + "}p{4.4cm}\n"
       + "                    >{" + P + "}p{2.1cm}\n"
       + "                    >{" + P + "}p{2.0cm}\n"
       + "                    >{" + P + "}p{2.0cm}@{}}")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    a = ap.parse_args()

    t = SUPP.read_text(encoding="utf-8")
    if NEW in t:
        print("  already widened")
        return 0
    assert t.count(OLD) == 1, f"the Table S3 column block was found {t.count(OLD)} times"
    total = 2.2 + 4.4 + 2.1 + 2.0 + 2.0
    print(f"  Table S3 columns: 10.6 cm -> {total:.1f} cm (text width is 18.2 cm)")
    if not a.apply:
        print("  (dry run)")
        return 0
    SUPP.write_text(t.replace(OLD, NEW, 1), encoding="utf-8", newline="")
    print("  written")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
