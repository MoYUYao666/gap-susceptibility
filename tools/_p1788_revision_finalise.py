# -*- coding: utf-8 -*-
r"""Revision finalisation: the approved cross-modal paragraph, then package-level checks and a staging hash freeze."""
import glob
import hashlib
import io
import json
import os
import subprocess
import zipfile

os.chdir(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
PKG = "SUBMISSION/PaperA_MachineLearning_revision"
d = json.load(io.open("outputs/analysis/paperA_crossmodal_esc50.json", encoding="utf-8"))
m, x, b = d["matched"], d["mismatched_captions"], d["bootstrap"]

PARA = r"""

One check outside the image--text setting is worth reporting as a boundary rather than as evidence. On an audio--text
contrastive backbone (CLAP, frozen, no adaptation), pairing 160 environmental recordings with their human-annotated
descriptions gives a gap-gradient that is carried almost entirely by the text tower: relative susceptibility
$%.3f$ for the text tower against $%.3f$ for the audio tower, with a bootstrap interval of $[%.3f, %.3f]$ over clips.
Shuffling the pairing raises the gap from $%.4f$ to $%.4f$ and collapses the text-tower gradient from $%.4f$ to $%.4f$
while the audio tower barely moves, which is the behaviour the mechanism predicts. We report this as a direction
consistency check, not as generality: it is one backbone, one corpus and no adaptation arms, so it cannot test the
ordering or the ODE, and the cross-modal claim we are willing to make is correspondingly narrow.
""" % (m["gamma_relative"]["text"], m["gamma_relative"]["audio"],
       b["text_gamma_ci95"][0], b["text_gamma_ci95"][1],
       m["dg"], x["dg"], m["grad_norm"]["text"], x["grad_norm"]["text"])

P6 = "paper合/reframed/sections/60_negative.tex"
t = io.open(P6, encoding="utf-8").read()
if "One check outside the image--text setting" not in t:
    io.open(P6, "w", encoding="utf-8", newline="").write(t.rstrip() + "\n" + PARA + "\n")
    print("negative-results section: cross-modal boundary paragraph added")
else:
    print("cross-modal paragraph already present")

# rebuild the revision package
env = dict(os.environ)
env["ML_PKG_DIR"] = os.path.abspath(PKG)
r = subprocess.run([r"D:\Anaconda\python.exe", "tools/_p1720_build_ml_package.py", "--apply"],
                   capture_output=True, text=True, env=env)
tail = [ln for ln in r.stdout.splitlines() if ("pages:" in ln or "RESULT" in ln or "round-trip" in ln or "FATAL" in ln)]
print("\n".join(tail) if tail else r.stdout[-1000:])
if r.returncode != 0:
    raise SystemExit("build failed")

# package-level checks
zpath = os.path.join(PKG, "LaTeXSource.zip")
with zipfile.ZipFile(zpath) as z:
    names = z.namelist()
    corrupt = z.testzip()
print("zip entries:", len(names), "| corrupt:", corrupt,
      "| underscore names:", [n for n in names if "_" in os.path.basename(n)][:3])

files = sorted(p for p in glob.glob(os.path.join(PKG, "*")) if os.path.isfile(p))
hashes = {}
for p in files:
    hashes[os.path.basename(p)] = hashlib.sha256(io.open(p, "rb").read()).hexdigest()
freeze = {"recorded_at": "2026-10-27", "package": "PaperA_MachineLearning_revision",
          "note": "staging package for the next submission attempt; not submitted yet, so this is a snapshot, not a freeze",
          "files": hashes, "n_files": len(hashes),
          "pages": 57}
io.open("docs/SUBMISSION_revision_snapshot_2026-10-27.json", "w", encoding="utf-8", newline="").write(
    json.dumps(freeze, indent=2, ensure_ascii=False))
print("hashes recorded:", len(hashes), "-> docs/SUBMISSION_revision_snapshot_2026-10-27.json")

# inventory row
INV = "docs/SUBMISSION_INVENTORY.md"
inv = io.open(INV, encoding="utf-8").read()
if "PaperA_MachineLearning_revision" not in inv:
    row = ("\n| `PaperA_MachineLearning_revision/` | Machine Learning (Springer) | next-attempt revision, "
           "**not submitted** | 57 pp (main 25 + appendix 32) | built clean, hashes in "
           "`docs/SUBMISSION_revision_snapshot_2026-10-27.json` |\n")
    io.open(INV, "w", encoding="utf-8", newline="").write(inv.rstrip() + "\n" + row)
    print("SUBMISSION_INVENTORY updated")
