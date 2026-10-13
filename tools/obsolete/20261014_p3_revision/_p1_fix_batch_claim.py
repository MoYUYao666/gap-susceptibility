# -*- coding: utf-8 -*-
"""
The batch-size sentence was wrong for the earlier single runs.

Reverse-engineered from the archived step counts: the single Flickr30k LoRA runs behind
Table 2 and the cross-validation figure record 630 steps (63 per epoch), i.e. batch 64 on a
4,000-image training split, while the five-seed runs, the full-tuning seeds, the Adapter
experiments and the strict control all record 320 steps (32 per epoch), i.e. batch 128. The
methodology claimed 128 for everything.  The strict-versus-mixed comparison in the control
section uses the two five-seed sets, so it is batch-matched and the "within noise" statement
is unaffected.
"""
import io
import os
import sys

ROOT = r"D:\Realdesktop\Wan\Important\New"
P = os.path.join(ROOT, "paper", "sections", "methodology.tex")
OLD = "All experiments: batch size 128, 10 epochs, AdamW with learning rate $10^{-4}$, single NVIDIA RTX 4060 GPU."
NEW = ("All experiments draw on the same 5{,}000-image pool (an 80/10/10 split), run for 10 epochs "
       "with AdamW at $10^{-4}$ on a single NVIDIA RTX 4060 GPU, and evaluate the gap every two "
       "epochs. The batch size is 128 for the five-seed runs, the strict control and the Adapter "
       "experiments, and 64 for the earlier single-run comparisons reported in "
       "Table~\\ref{tab:position}; the archived step counts record the difference.")

src = io.open(P, encoding="utf-8").read()
if src.count(OLD) != 1:
    print("FAIL: methodology sentence not found exactly once")
    sys.exit(1)
io.open(P, "w", encoding="utf-8", newline="").write(src.replace(OLD, NEW, 1))
print("ok   batch-size sentence corrected")
