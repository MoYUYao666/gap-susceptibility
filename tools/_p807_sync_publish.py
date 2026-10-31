# -*- coding: utf-8 -*-
r"""Sync this session's code and result changes into the public repository, without tags.

Operator instruction: upload to GitHub on completion of the Paper A experiment work, and keep the
standing rule of never creating a new release or tag, because a new tag would make Zenodo mint
another DOI.

What changed and therefore needs to reach the repository:
  src/lora.py                 the adapter wrapper now freezes everything that is not an adapter
  src/trainer.py              checkpoints save every trainable parameter, not just the adapters
                              (the retrieval metric was reviewed and left as it was: the loop and the
                              chunked form measure different, both-correct things)
  src/dataset.py              the collate function keeps image_path so retrieval evaluation can
                              group captions by image
  tools/_p79*_*.py            the session's audit and rerun scripts
  tools/_p8*_*.py             the rank rerun, status reporter and roster scripts
  outputs/analysis/*.json     the recorded statistics behind the paper edits
  outputs/scaleup_coco/*.json the corrected scale-up runs
  outputs/rank_rerun/*.json   the rank reruns

Safety rules enforced before anything is copied or committed:
  - no manuscript artefacts (main*.tex/pdf, cover letters, title pages, highlights)
  - no weights or archives (.pt .pth .zip .safetensors ...)
  - no file of 100 MB or more
  - no deletions in the repository

    python tools/_p807_sync_publish.py --dry-run | --apply [--push]
"""
from __future__ import annotations

import argparse
import io
import re
import shutil
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
PC = REPO / "publish_clean"

ALLOW_TOP = ("tools", "outputs", "src", "exp", "experiments")

EXCLUDE_EXT = {".pt", ".pth", ".bin", ".safetensors", ".ckpt", ".onnx", ".h5", ".pkl",
               ".npz", ".npy", ".parquet", ".db", ".sqlite", ".zip", ".tar", ".gz",
               ".7z", ".rar", ".mp4", ".avi", ".mov", ".wav", ".mp3", ".log",
               ".docx", ".doc", ".bak", ".pyc"}
BAN = re.compile(r"(^|/)(main[^/]*\.(tex|pdf)|cover_letter[^/]*|title_page[^/]*|"
                 r"highlights[^/]*|.*\.bak.*|.*\.SUPERSEDED_BY.*)$", re.I)
# A manuscript artefact is a file that IS a manuscript or submission page. Analysis outputs are
# named after what they examine, so outputs/analysis/paperhe_highlights.json is a record of the
# paper's highlights, not the highlights file itself. Restrict the name test to files that would sit
# beside a manuscript, which is where the real artefacts live.
MANUSCRIPT_DIRS = re.compile(r"(^|/)(submission|paper[^/]*|nc_submission|prl_submission|"
                             r"latex_source|upload)(/|$)", re.I)
# One-off session scripts are not published. The repository tracks 199 tools and only seven of them
# are underscore-prefixed (shell helpers such as _cloud_bin.sh), while this working tree holds 1,501
# _*.py session scripts; the earlier syncs kept them out. The curated tools lack the session prefix,
# so this is what separates the two.
ONEOFF = re.compile(r"^tools/_p\d+[a-z]?_.*\.py$", re.I)
SKIP_DIRS = {"__pycache__", "obsolete", "outputs/_cloud_layout", "outputs/_probe",
             "outputs/_scope", "outputs/_verify", "outputs/_verify_ckpt",
             "outputs/_scaleup_coco_LOORA_NOT_FROZEN", "outputs/_scaleup_coco_SEEDS_42_43_44",
             "outputs/diag_lora", "outputs/long_run", "outputs/lr_sweep", "outputs/arm_compare",
             "outputs/lora_fixes", "outputs/trainer_loss_probe", "outputs/wire"}
# Files kept in the working tree as internal history but not published. The archive of the defective
# run is written down in HANDOFF and reproduced by re-running the script, so the paper does not
# depend on shipping it to the repository.
SKIP_FILES = {"outputs/analysis/_coco_scaleup_LOORA_NOT_FROZEN.json"}

SIZE_LIMIT = 100 * 1024 * 1024


def git(*args, cwd=PC):
    r = subprocess.run(["git"] + list(args), cwd=str(cwd), capture_output=True)
    return r.returncode, r.stdout.decode("utf-8", "replace"), r.stderr.decode("utf-8", "replace")


def admissible(p: Path, rel: str) -> tuple:
    """Return (ok, reason)."""
    if p.suffix.lower() in EXCLUDE_EXT:
        return False, f"excluded extension {p.suffix}"
    if BAN.search(rel):
        return False, "manuscript artefact or backup"
    if ONEOFF.match(rel):
        return False, "one-off session script"
    if (rel.startswith("tools/") and rel.endswith(".py")
            and Path(rel).name.startswith("_") and not (PC / rel).exists()):
        return False, "session script that the repository has never carried"
    if rel in SKIP_FILES:
        return False, "internal history, not published"
    for d in SKIP_DIRS:
        if f"/{d}/" in f"/{rel}" or rel.startswith(d + "/"):
            return False, f"skipped directory {d}"
    try:
        if p.stat().st_size >= SIZE_LIMIT:
            return False, "file is 100 MB or larger"
    except OSError:
        return False, "unreadable"
    return True, ""


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--apply", action="store_true")
    ap.add_argument("--push", action="store_true")
    a = ap.parse_args()
    if not a.apply:
        a.dry_run = True

    # collect candidates: recent changes under the allowed trees
    cands = []
    for top in ALLOW_TOP:
        root = REPO / top
        if not root.exists():
            continue
        for p in root.rglob("*"):
            if not p.is_file():
                continue
            rel = p.relative_to(REPO).as_posix()
            ok, why = admissible(p, rel)
            if not ok:
                continue
            dest = PC / rel
            if not dest.exists() or p.stat().st_mtime > dest.stat().st_mtime:
                cands.append((p, dest, rel))

    print("=" * 104)
    print(f"candidates to sync: {len(cands)}")
    print("=" * 104)
    by_top = {}
    for _, _, rel in cands:
        by_top[rel.split("/")[0]] = by_top.get(rel.split("/")[0], 0) + 1
    for k, v in sorted(by_top.items(), key=lambda kv: -kv[1]):
        print(f"  {k:<16} {v}")
    print()
    for _, _, rel in cands[:20]:
        print(f"     {rel}")
    if len(cands) > 20:
        print(f"     ... and {len(cands) - 20} more")

    # safety audit over what would land in the repository
    print()
    print("=" * 104)
    print("safety audit")
    print("=" * 104)
    bad = [rel for _, _, rel in cands if BAN.search(rel) or Path(rel).suffix.lower()
           in EXCLUDE_EXT]
    big = [rel for _, _, rel in cands
           if (REPO / rel).stat().st_size >= SIZE_LIMIT]
    print(f"  manuscript artefacts or forbidden extensions: {len(bad)}")
    print(f"  files of 100 MB or more: {len(big)}")
    print(f"  deletions: 0 (this script never removes)")
    if bad or big:
        print("  refusing to continue")
        return 1

    if a.dry_run:
        print()
        print("  (dry run; nothing copied, committed or pushed)")
        return 0

    copied = 0
    for src, dest, rel in cands:
        dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(src, dest)
        copied += 1
    print()
    print(f"  copied {copied} file(s) into publish_clean/")

    rc, out, err = git("add", "-A")
    rc, st, _ = git("status", "--porcelain")
    rows = [l for l in st.splitlines() if l.strip()]
    added = [l for l in rows if l.startswith("A ")]
    modified = [l for l in rows if l.startswith("M ")]
    deleted = [l for l in rows if l.startswith("D ")]
    print(f"  staged: {len(added)} added, {len(modified)} modified, {len(deleted)} deleted")
    if deleted:
        print("  !! unexpected deletions:")
        for d in deleted[:10]:
            print(f"     {d}")
        return 1

    manifests = [l for l in rows
                 if re.search(r"(^|/)(main[^/]*\.(tex|pdf)|cover_letter[^/]*|title_page[^/]*|"
                              r"highlights[^/]*)$", l.split(maxsplit=1)[-1].strip(), re.I)
                 and MANUSCRIPT_DIRS.search(l.split(maxsplit=1)[-1].strip())]
    print(f"  manuscript artefacts staged: {len(manifests)}")
    if manifests:
        for m in manifests[:10]:
            print(f"     {m}")
        return 1

    rc, out, err = git("commit", "-m",
                       "Fix the adapter scope, save the full trainable state, and add the "
                       "corrected COCO scale-up and rank reruns")
    print(f"  commit rc={rc}")
    print("  " + (out.strip().splitlines()[0] if out.strip() else err.strip()[:120]))

    rc, out, _ = git("log", "-1", "--pretty=%h | %s")
    print("  " + out.strip())

    if a.push:
        rc, out, err = git("push", "ssh-origin", "main")
        print()
        print(f"  push rc={rc}")
        for line in (out + err).strip().splitlines()[-4:]:
            print(f"     {line}")
        rc, out, _ = git("ls-remote", "ssh-origin", "main")
        print(f"  remote main: {out.split()[0] if out.split() else '?'}")
        rc, out, _ = git("ls-remote", "--tags", "ssh-origin")
        tags = [l.split("refs/tags/")[-1] for l in out.splitlines() if "refs/tags/" in l]
        print(f"  remote tags: {tags}   <- must be unchanged")
    else:
        print()
        print("  (committed locally; pass --push to publish)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
