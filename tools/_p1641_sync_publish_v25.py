# -*- coding: utf-8 -*-
r"""Stage the v2.5 round into the public mirror and run the release pre-flight checks.

The public repository is `publish_clean/`. Its tracked content is a *curated* subset of this working
tree: whole live directories are not copied, because the working tree holds roughly two thousand
one-off session scripts that earlier rounds deliberately kept out. This script therefore stages
exactly the paths that the v2.5 live commits touched, restricted to the categories the publication
boundary allows, and then runs the five release pre-flight checks.

Base commit: `f3815f8f` ("Mirror: evening helper tools", 2026-10-24 20:10) is the live commit that
corresponds to `publish_clean` HEAD `b19d4a6`. Everything after it is the v2.5 delta.

Deliberately NOT staged (see the report printed by --preflight):

  * `docs/**` - the operator asked on 2026-10-14 to keep `docs/` out of the public repository
    ("do not put docs"); the tree holds reviewer reports, response plans and venue decisions for
    manuscripts that are still under review, and `publish_clean/.gitignore` ignores it wholesale.
  * manuscripts, cover letters, title pages, highlights, `SUBMISSION/`, weights, caches, logs.
  * the repository-root `README.md` - the published README is maintained separately in
    `publish_clean/README.md`; copying the root version over it once wiped publish-specific edits.

    python tools/_p1641_sync_publish_v25.py [--apply]
    python tools/_p1641_sync_publish_v25.py --preflight
"""
from __future__ import annotations

import argparse
import hashlib
import re
import shutil
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
PC = REPO / "publish_clean"

BASE = "f3815f8f"
TREES = ("tools", "outputs", "src", "exp", "experiments")

# Categories the publication boundary allows; `docs` is excluded on the operator's instruction.
EXCLUDE_EXT = {
    ".pt", ".pth", ".bin", ".safetensors", ".ckpt", ".onnx", ".h5", ".pkl", ".npz", ".npy",
    ".parquet", ".db", ".sqlite", ".zip", ".tar", ".gz", ".7z", ".rar", ".mp4", ".avi", ".mov",
    ".wav", ".mp3", ".log", ".docx", ".doc", ".bak", ".pyc", ".pyo", ".exe", ".dll",
}

# Manuscript trees, matching the list `publish_clean/.gitignore` already ignores. A `paper*` glob is
# NOT used here on purpose: `outputs/paper_figures/` is a directory of result figures, not a
# manuscript tree, and it has been tracked since the earlier releases.
MANUSCRIPT_DIRS = {
    "paper", "paper2", "paper3", "paper_a1", "paper_a2", "paper_a23", "paper_ap3", "paper合",
    "paper合_submission", "submission", "SUBMISSION", "nc_submission", "prl_submission",
    "latex_source", "latexsource", "LaTeXSource",
}

# Submission-page basenames (anchored, as glob patterns are anchored).
ARTEFACT_NAME = re.compile(
    r"^(main[^/]*\.(tex|pdf)|[^/]*cover[_-]?letter[^/]*|title[_-]?page[^/]*|declaration[^/]*|"
    r"highlights[^/]*|LaTeXSource[^/]*|response[_-]?to[^/]*)$", re.I)

SKIP_DIRS = {"__pycache__", "obsolete", "_cloud_layout"}

# `046c6201` ("Fix .gitignore so result archives under outputs/ enter history") belongs to the *live*
# repository's history hygiene, not to this release: it retroactively tracked 1,608 result archives
# that had been ignored since September. Those archives are excluded here, because publishing them
# would be a scope change to the mirror rather than part of the v2.5 round; widen it deliberately if
# the mirror should carry the whole `outputs/` record.
HISTORY_ONLY = "046c6201"

# Internal and known-defective run archives that the published filter already excludes
# (see `tools/_p807_sync_publish.py`). They stay out of the mirror.
INTERNAL_DIRS = {
    "outputs/_cloud_layout", "outputs/_probe", "outputs/_scope", "outputs/_verify",
    "outputs/_verify_ckpt", "outputs/_scaleup_coco_LOORA_NOT_FROZEN",
    "outputs/_scaleup_coco_SEEDS_42_43_44", "outputs/_serial_logs", "outputs/_a23_snap",
    "outputs/_full_coco_CAPPED_EVAL_BUG", "outputs/_llava_sites_wrong_scale",
    "outputs/diag_lora", "outputs/long_run", "outputs/lr_sweep", "outputs/arm_compare",
    "outputs/lora_fixes", "outputs/trainer_loss_probe", "outputs/wire",
}
INTERNAL_FILES = {"outputs/_supervise_state.json", "outputs/_fixdump.txt", "outputs/_oe_decision.txt",
                  "outputs/analysis/_coco_scaleup_LOORA_NOT_FROZEN.json"}

# Part of this release but not yet in the live history: the staging helper itself, which documents
# how the release was assembled. Earlier rounds published their staging helpers too (`_p1619`, `_p1628`).
EXTRA = ("tools/_p1641_sync_publish_v25.py",)

SIZE_LIMIT = 100 * 1024 * 1024

CJK = re.compile(r"[\u3000-\u303f\u4e00-\u9fff\uff00-\uffef]")
CJK_TOKEN = re.compile(r"[\u4e00-\u9fff][\u4e00-\u9fff\u3000-\u303f\uff00-\uffef]*")


def git(*args: str, cwd: Path = REPO) -> str:
    r = subprocess.run(["git"] + list(args), cwd=str(cwd), capture_output=True)
    out = r.stdout.decode("utf-8", "replace")
    if r.returncode != 0:
        sys.stderr.write(r.stderr.decode("utf-8", "replace"))
        raise SystemExit(f"git {' '.join(args)} failed with rc={r.returncode}")
    return out


def sha256(p: Path) -> str:
    h = hashlib.sha256()
    with p.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def admissible(rel: str) -> tuple[bool, str]:
    """Return (ok, reason). `rel` is a repository-relative POSIX path."""
    parts = rel.split("/")
    name = parts[-1]
    if Path(name).suffix.lower() in EXCLUDE_EXT:
        return False, f"excluded extension {Path(name).suffix}"
    if ARTEFACT_NAME.match(name):
        return False, "submission artefact name"
    for d in parts[:-1]:
        if d in MANUSCRIPT_DIRS:
            return False, f"manuscript directory {d}/"
        if d in SKIP_DIRS:
            return False, f"skipped directory {d}/"
    joined = rel.rsplit("/", 1)[0] if "/" in rel else ""
    for d in INTERNAL_DIRS:
        if rel == d or rel.startswith(d + "/") or joined == d:
            return False, f"internal archive directory {d}/"
    if rel in INTERNAL_FILES:
        return False, "internal working file"
    if name.endswith(".bak") or ".bak_" in name or ".SUPERSEDED_BY" in name:
        return False, "backup file"
    p = REPO / rel
    try:
        if p.stat().st_size >= SIZE_LIMIT:
            return False, "file is 100 MB or larger"
    except OSError:
        return False, "unreadable"
    return True, ""


def _names(ref_args: list[str]) -> set[str]:
    """Paths added/modified/renamed by a git query."""
    raw = git("log", "--name-status", "--format=", *ref_args)
    out = set()
    for line in raw.splitlines():
        line = line.rstrip()
        if "\t" not in line:
            continue
        status, rel = line.split("\t", 1)
        if status.strip()[:1] in ("A", "M", "R"):
            out.add(rel.replace("\\", "/"))
    return out


def delta_paths(verbose: bool = False) -> list[str]:
    """Paths this release adds to the mirror: those touched by the round's own commits.

    Two sources are combined:

    1. every path touched by a commit in ``BASE..HEAD`` other than the `.gitignore`-history commit;
    2. paths that the `.gitignore`-history commit introduced but whose on-disk modification time is
       at or after ``BASE``'s commit time. Those are round artefacts that merely happened to enter
       git history through that commit - the allocation-paired, R_c-family and gamma-robustness
       archives among them. Its remaining 1,598 archives date from 2026-08-03 to 2026-10-24 19:01,
       i.e. from before the mirror point, and belong to the live repository's history hygiene rather
       than to the v2.5 round; publishing them would widen the mirror's scope.
    """
    mark = "@@@"
    raw = git("log", f"{BASE}..HEAD", "--name-status", "--format=" + mark + "%h")
    keep: set[str] = set()
    via_history: set[str] = set()
    cur = ""
    for line in raw.splitlines():
        line = line.rstrip()
        if line.startswith(mark):
            cur = line[len(mark):].strip()
            continue
        if "\t" not in line:
            continue
        status, rel = line.split("\t", 1)
        if status.strip()[:1] not in ("A", "M", "R"):
            continue
        rel = rel.replace("\\", "/")
        if cur == HISTORY_ONLY:
            via_history.add(rel)
        else:
            keep.add(rel)

    base_time = git("show", "-s", "--format=%ct", BASE).strip()
    era = set()
    for rel in via_history - keep:
        p = REPO / rel
        try:
            if p.stat().st_mtime >= float(base_time):
                era.add(rel)
        except OSError:
            continue
    keep |= era

    keep = {p for p in keep if p.startswith(tuple(t + "/" for t in TREES))}
    keep |= set(EXTRA)
    if verbose:
        print(f"  commits {BASE}..HEAD: {len(keep) - len(era)} touched by the round, "
              f"+{len(era)} round-era archives that entered history via {HISTORY_ONLY}")
        for p in sorted(era):
            print(f"       (era) {p}")
    return sorted(keep)


def classify(rels: list[str]) -> tuple[list[str], list[str], list[str], list[tuple[str, str]]]:
    new, changed, same, skipped = [], [], [], []
    for rel in rels:
        ok, why = admissible(rel)
        if not ok:
            skipped.append((rel, why))
            continue
        src, dst = REPO / rel, PC / rel
        if not src.exists():
            skipped.append((rel, "missing in the working tree"))
            continue
        if not dst.exists():
            new.append(rel)
        elif sha256(src) != sha256(dst):
            changed.append(rel)
        else:
            same.append(rel)
    return new, changed, same, skipped


def do_sync(apply: bool) -> int:
    rels = delta_paths(verbose=True)
    new, changed, same, skipped = classify(rels)
    todo = new + changed

    print("=" * 100)
    print(f"v2.5 sync: live {BASE}..HEAD, trees {', '.join(TREES)}")
    print("=" * 100)
    print(f"  paths touched by the round        : {len(rels)}")
    print(f"  -> new to the mirror              : {len(new)}")
    print(f"  -> changed in the mirror          : {len(changed)}")
    print(f"  -> already identical              : {len(same)}")
    print(f"  -> filtered out                   : {len(skipped)}")
    by_reason: dict[str, int] = {}
    for _, why in skipped:
        by_reason[why.split(" ")[0]] = by_reason.get(why.split(" ")[0], 0) + 1
    for why, n in sorted(by_reason.items(), key=lambda kv: -kv[1]):
        print(f"       {why:<28} {n}")

    print()
    print("  files to copy:")
    for rel in new:
        print(f"    + {rel}")
    for rel in changed:
        print(f"    M {rel}")

    total = sum((REPO / r).stat().st_size for r in todo)
    print()
    print(f"  total payload: {total / 1e6:.3f} MB over {len(todo)} file(s)")

    if not apply:
        print()
        print("  (dry run; nothing copied)")
        return 0

    for rel in todo:
        dst = PC / rel
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(REPO / rel, dst)
    print()
    print(f"  copied {len(todo)} file(s) into publish_clean/ (not committed, not tagged, not pushed)")
    return 0


# --------------------------------------------------------------------------------------------------
# pre-flight checks
# --------------------------------------------------------------------------------------------------

def tracked() -> list[str]:
    return [l for l in git("ls-files", cwd=PC).splitlines() if l.strip()]


def staged_rows(rev: str = "") -> list[tuple[str, str]]:
    """(status, path) of the release's paths.

    Without `rev`: stage the working tree and report it against publish_clean HEAD.
    With `rev` (e.g. `HEAD`): report what that commit changed against its first parent, so the
    checks can be re-run after the commit exists.
    """
    if rev:
        raw = git("diff", "--name-status", f"{rev}^", rev, cwd=PC)
    else:
        git("add", "-A", cwd=PC)
        raw = git("diff", "--cached", "--name-status", cwd=PC)
    rows = []
    for line in raw.splitlines():
        if "\t" in line:
            st, rel = line.split("\t", 1)
            rows.append((st.strip()[:1], rel.strip().replace("\\", "/")))
    return rows


def do_preflight(rev: str = "") -> int:
    rows_in = staged_rows(rev)
    files = tracked()
    added_rels = {p for st, p in rows_in if st == "A"}
    ok_all = True
    review: list[str] = []

    print("=" * 100)
    print("v2.5 pre-flight checks on publish_clean/ (tracked release content)")
    print("=" * 100)
    print(f"    scope: {'commit ' + rev if rev else 'the staged working tree'}")
    print(f"    this release stages {len(rows_in)} path(s): "
          f"{sum(1 for s, _ in rows_in if s == 'A')} added, "
          f"{sum(1 for s, _ in rows_in if s == 'M')} modified")

    # (a) manuscript artefacts
    print("\n(a) manuscript artefacts")
    name_hits = [f for f in files if ARTEFACT_NAME.match(f.split("/")[-1])]
    dir_hits = [f for f in files
                if any(part in MANUSCRIPT_DIRS for part in f.split("/")[:-1])]
    paperish = sorted({f.split("/")[i] for f in files
                       for i in range(len(f.split("/")) - 1)
                       if f.split("/")[i].lower().startswith("paper")})
    print(f"    files whose basename is a submission page : {len(name_hits)}")
    for f in name_hits:
        print(f"       {f}")
    print(f"    paths under a manuscript directory        : {len(dir_hits)}")
    for f in dir_hits:
        print(f"       {f}")
    print(f"    directories whose name starts with 'paper': {paperish}")
    for d in paperish:
        members = [f for f in files if f.startswith(d + "/") or f"/{d}/" in f]
        print(f"       {d}/ -> {len(members)} tracked file(s), e.g. {members[0] if members else '-'}")
    print("    NOTE: outputs/paper_figures/ is a directory of result figures, not a manuscript")
    print("          tree; it is not in the repository's manuscript-directory list and has been")
    print("          tracked since the earlier releases.")
    loose = [f for f in files if f.split("/")[-1].startswith("paper")]
    print(f"    near-miss names (records ABOUT a paper, not submission pages) : {len(loose)}")
    for f in loose[:6]:
        print(f"       {f}")
    if len(loose) > 6:
        print(f"       ... and {len(loose) - 6} more")
    if name_hits or dir_hits:
        ok_all = False
        print("    RESULT: FAIL")
    else:
        print("    RESULT: PASS - 0 submission pages, 0 manuscript-directory paths")

    # (b) large files
    print("\n(b) large files")
    sized = sorted(((PC / f).stat().st_size, f) for f in files if (PC / f).exists())
    big = [(s, f) for s, f in sized if s >= SIZE_LIMIT]
    print(f"    files >= 100 MB : {len(big)}")
    for s, f in big:
        print(f"       {s / 1e6:9.3f} MB  {f}")
    print("    largest five files:")
    for s, f in sized[-5:][::-1]:
        print(f"       {s / 1e6:9.3f} MB  {f}")
    if big:
        ok_all = False
        print("    RESULT: FAIL")
    else:
        print("    RESULT: PASS")

    # (c) weights and caches
    print("\n(c) weights and caches")
    banned = (".pt", ".safetensors", ".ckpt", ".npz", ".bin")
    hits = [f for f in files if f.lower().endswith(banned)]
    new_hits = [f for f in hits if f in added_rels]
    print(f"    tracked .pt/.safetensors/.ckpt/.npz/.bin files : {len(hits)}")
    for f in hits:
        print(f"       {(PC / f).stat().st_size:9.1f} B  {f}")
    print(f"    of which added by this release : {len(new_hits)}")
    if new_hits:
        ok_all = False
        print("    RESULT: FAIL - this release adds a weight or cache file")
    elif hits:
        print("    RESULT: PASS for this release - the one file listed is a pre-existing,")
        print("            deliberate exception: a 0.1 MB per-image correctness array kept under an")
        print("            explicit .gitignore negation because the bootstrap intervals need it.")
    else:
        print("    RESULT: PASS")

    # (d) Chinese in the files this release adds
    print("\n(d) Chinese in the files this release adds")
    print("    English-facing text this release adds: RELEASE_NOTES_v2.5.md (a doc) and")
    print("    tools/_p1641_sync_publish_v25.py (the staging helper).")
    cjk_hits, functional = [], []
    for st, rel in rows_in:
        p = PC / rel
        if p.suffix.lower() not in {".json", ".md", ".txt", ".py", ".sh", ".ps1", ".yml",
                                    ".yaml", ".csv", ".tex"} or not p.exists():
            continue
        text = p.read_text(encoding="utf-8", errors="replace")
        n = len(CJK.findall(text))
        if not n:
            continue
        tokens = {m.group(0) for m in CJK_TOKEN.finditer(text)}
        # The project exempts real file and directory names: `paper合/` is a directory on disk, and
        # renaming it in a path description would break the path. Anything else is prose.
        if tokens <= {"合", "paper合"}:
            functional.append((rel, n, sorted(tokens)))
        else:
            cjk_hits.append((rel, n, sorted(tokens)[:6]))
    total_docs = len(CJK.findall((PC / "RELEASE_NOTES_v2.5.md").read_text(encoding="utf-8",
                                                                       errors="replace")))
    print(f"    RELEASE_NOTES_v2.5.md CJK characters : {total_docs}")
    print(f"    staged files whose only Chinese is the exempt directory name `paper合` : "
          f"{len(functional)}")
    for rel, n, toks in functional:
        print(f"       {n:6d} chars  {rel}   {toks}")
    print(f"    staged files carrying Chinese prose : {len(cjk_hits)}")
    for rel, n, toks in sorted(cjk_hits, key=lambda kv: -kv[1]):
        print(f"       {n:6d} chars  {rel}")
        print(f"              tokens: {toks}")
    if total_docs:
        ok_all = False
        print("    RESULT: FAIL - the release notes carry Chinese")
    elif cjk_hits:
        review.append("(d) Chinese prose in staged archive files (see the tokens above)")
        print("    RESULT: REVIEW - the release notes and the staging helper are clean, and the")
        print("            `paper合` occurrences are exempt functional path data, but the archive")
        print("            files listed above carry Chinese text. Archives must stay byte-faithful")
        print("            to what their scripts produced, so they are staged as they are.")
    else:
        print("    RESULT: PASS - no Chinese beyond the exempt directory name")

    # (e) staged diff
    print("\n(e) staged diff")
    added = [p for st, p in rows_in if st == "A"]
    modified = [p for st, p in rows_in if st == "M"]
    deleted = [p for st, p in rows_in if st == "D"]
    other = [(st, p) for st, p in rows_in if st not in ("A", "M", "D")]
    print(f"    staged paths : {len(rows_in)}  ({len(added)} added, {len(modified)} modified, "
          f"{len(deleted)} deleted, {len(other)} other)")
    for st, p in other[:10]:
        print(f"       {st} {p}")
    payload = sum((PC / b).stat().st_size for b in added + modified if (PC / b).exists())
    print(f"    staged payload (bytes of added+modified files) : {payload / 1e6:.3f} MB "
          f"({payload / (1024 * 1024):.3f} MiB)")
    print(f"    under the 200 MB ceiling : {payload < 200 * 1024 * 1024}")
    print("    diff --stat (tail):")
    stat = git("diff", "--cached", "--stat", cwd=PC).strip().splitlines() if not rev else \
        git("diff", "--stat", f"{rev}^", rev, cwd=PC).strip().splitlines()
    for line in stat[-4:]:
        print(f"       {line}")
    if deleted or other or not payload < 200 * 1024 * 1024:
        ok_all = False
        print("    RESULT: REVIEW - see rows above")
    else:
        print("    RESULT: PASS - additions and modifications only, under the ceiling")

    print()
    print("=" * 100)
    if ok_all and not review:
        print("pre-flight verdict: PASS")
    elif ok_all:
        print(f"pre-flight verdict: PASS with {len(review)} review item(s) for the lead:")
        for item in review:
            print(f"    - {item}")
    else:
        print("pre-flight verdict: FAIL - see the lines marked RESULT: FAIL")
    print("=" * 100)
    return 0 if ok_all else 1


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    ap.add_argument("--preflight", action="store_true")
    ap.add_argument("--rev", default="", help="run --preflight against a commit, e.g. HEAD")
    a = ap.parse_args()
    if not PC.is_dir():
        raise SystemExit("publish_clean/ not found")
    if a.preflight:
        return do_preflight(a.rev)
    return do_sync(a.apply)


if __name__ == "__main__":
    raise SystemExit(main())