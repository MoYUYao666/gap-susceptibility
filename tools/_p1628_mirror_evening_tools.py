# -*- coding: utf-8 -*-
"""Add this evening's helper tools to the mirror list (no manuscripts, code only)."""
import io
import os

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
os.chdir(REPO)

FILES = [
    "tools/_p1617_manifest_vqa451.py",   # kept for provenance of the manifest edit
    "tools/_p1620_close_h2_consistency.py",
    "tools/_p1622_add_min_margin.py",
    "tools/_p1623_fetch_encoders_local.py",
    "tools/_p1624_repair_s28_margin.py",
    "tools/_p1627_rebuild_next_revision.py",
    "cloud_next/chain_after_p2.ps1",
]
p = "tools/_p1284_prepare_public_mirror.py"
t = io.open(p, encoding="utf-8").read()
anchor = '    "cloud_p3/run_cloud_final.sh",\n'
need = [x for x in FILES if x not in t and os.path.exists(x)]
if need:
    assert t.count(anchor) == 1
    io.open(p, "w", encoding="utf-8", newline="").write(
        t.replace(anchor, anchor + "".join('    "%s",\n' % x for x in need), 1))
    print("mirror list +", len(need))
else:
    print("nothing to add")