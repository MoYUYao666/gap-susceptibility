#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""_p44g_show_version_text_hits.py -- print the text-level version hits that the
exhaustive scan found, so the report can state exactly which CUDA/PyTorch traces
exist in the archive (and which do not)."""
import json, os
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
D = json.load(open(os.path.join(ROOT, "outputs/analysis/p3_reproducibility.json"), encoding="utf-8"))
sc = D["exhaustive_version_record_scan"]
print("files scanned: %d (json %d)" % (sc["files_scanned"], sc["json_files_scanned"]))
print("\n--- KEY-LEVEL HITS (%d) ---" % len(sc["key_level_hits"]))
for h in sc["key_level_hits"]:
    print("  %-70s %s" % (h["path"], h["fields"]))
print("\n--- TEXT-LEVEL HITS (%d) ---" % len(sc["text_level_hits"]))
for h in sc["text_level_hits"]:
    print("  %-70s n=%-4d %s" % (h["path"], h["n_matches"], h["samples"][:4]))
