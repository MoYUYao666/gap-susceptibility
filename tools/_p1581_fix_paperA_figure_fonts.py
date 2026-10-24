# -*- coding: utf-8 -*-
r"""Re-generate the Paper A figures so that their PDFs embed fonts as CID TrueType.

Root cause: ``tools/figure_style.py::apply_style`` never set ``pdf.fonttype``, so every
figure saved through ``figure_style.save`` was written with matplotlib's default Type 3
embedding.  ``apply_style`` now sets ``pdf.fonttype = 42`` (2026-10-24); this script
archives the old figures and re-runs the authoritative generator of each figure.

    python tools/_p1581_fix_paperA_figure_fonts.py --apply
"""
from __future__ import annotations

import argparse
import io
import os
import shutil
import subprocess
import sys
import time
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
os.chdir(REPO)
FIGDIR = REPO / "paper合" / "figures"
ARCHIVE = REPO / "_archive" / "paperA_figures_pre_fontfix_2026-10-24"

TARGETS = ["fig1", "fig1_ode_fits", "fig2", "fig2_v5_falsification", "fig3", "fig4",
           "fig4_effective_rank", "fig8a_rank_delta", "fig8b_budget", "fig8c_vision_untouched",
           "fig9a_noise_sweep", "fig9b_sigma0_control", "fig9c_ratio", "fig10_layered_ft",
           "fig12_zeroshot_more", "fig14_adapter_layered", "fig15_stratified_dg_r1"]

# authoritative generator per figure group, in application order
RUNS = [
    ("tools/_pa_rebuild_figs_rest.py", ["--apply"]),
    ("tools/_pa_split_appendix_figs.py", ["--apply"]),
    ("tools/_pa_rebuild_fig12.py", ["--apply"]),
    ("tools/_pa_fix_fig8c_fig14.py", ["--apply"]),
    ("tools/_pa_fig10_tall.py", ["--apply"]),
    ("tools/_pa_fig14_tall.py", []),
    ("tools/_p860_fig_stratified.py", ["--apply"]),
]


def fonts(path: Path) -> tuple[int, list[str]]:
    out = subprocess.run(["pdffonts", str(path)], capture_output=True, text=True).stdout
    rows = [l for l in out.splitlines()[2:] if l.strip()]
    t3 = sum(1 for l in rows if "Type 3" in l)
    return t3, [l.split()[0] for l in rows]


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    a = ap.parse_args()

    before = {t: (FIGDIR / (t + ".pdf")) for t in TARGETS if (FIGDIR / (t + ".pdf")).exists()}
    bad_before = [t for t, p in before.items() if fonts(p)[0]]
    print("figures with Type 3 before:", len(bad_before), "/", len(before))
    if not a.apply:
        return 0

    if not ARCHIVE.is_dir():
        ARCHIVE.mkdir(parents=True)
        n = 0
        for f in sorted(FIGDIR.glob("*.pdf")) + sorted(FIGDIR.glob("*.png")):
            shutil.copy2(f, ARCHIVE / f.name)
            n += 1
        print("archived %d figure files -> %s" % (n, ARCHIVE.relative_to(REPO).as_posix()))

    for script, flags in RUNS:
        t0 = time.time()
        r = subprocess.run([sys.executable, script] + flags, capture_output=True, text=True,
                           encoding="utf-8", errors="replace")
        tail = (r.stdout or "").strip().splitlines()[-2:]
        print("%-38s exit=%d  %5.1fs  %s" % (os.path.basename(script), r.returncode,
                                             time.time() - t0, " | ".join(tail)[:150]))
        if r.returncode != 0:
            print("   stderr tail:", (r.stderr or "")[-300:])

    print("\n== verification ==")
    problems = []
    for t in TARGETS:
        p = FIGDIR / (t + ".pdf")
        if not p.exists():
            problems.append((t, "missing"))
            continue
        t3, names = fonts(p)
        bad_names = [n for n in names if not (n.split("+")[-1].startswith(("TimesNewRoman", "STIX")))]
        status = "OK" if t3 == 0 and not bad_names else "PROBLEM"
        if status != "OK":
            problems.append((t, "type3=%d fonts=%s" % (t3, bad_names[:3])))
        print("  %-26s %-8s type3=%d fonts=%s" % (t, status, t3, ", ".join(names[:2])))
    print("\nproblems:", problems if problems else "none")
    return 1 if problems else 0


if __name__ == "__main__":
    raise SystemExit(main())