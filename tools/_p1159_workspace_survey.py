# -*- coding: utf-8 -*-
r"""Survey the workspace and classify what could be cleaned, without deleting anything.

Precedent: the 2026-10-16 cleanup ran as guarded scripts (`tools/_p1047_cleanup.py`,
`tools/_p1048_cleanup_caches.py`) with their decisions logged in `docs/cleanup_*.md`, and the operator asked to be
told which items would be removed before they were removed. This survey keeps that order: measure, classify, ask.

Categories, in ascending order of risk:

  SAFE        caches and stray build artefacts, regenerable, untracked by git
  LIKELY      local scratch copies that the archive already covers (e.g. a cloud pull also present in another dir)
  ASK         large archives/snapshots or duplicate outputs where value depends on the operator's intent
  KEEP        everything tracked, everything cited by the claim ledger, everything from `outputs/`

    python tools/_p1159_workspace_survey.py
"""
from __future__ import annotations

import json
import os
import subprocess
from collections import defaultdict
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
MB = 1024 * 1024


def du(path: Path) -> int:
    total = 0
    for root, dirs, files in os.walk(path):
        dirs[:] = [d for d in dirs if d != ".git"]
        for f in files:
            try:
                total += os.path.getsize(os.path.join(root, f))
            except OSError:
                pass
    return total


def main() -> None:
    print("=== top-level sizes ===")
    rows = []
    for p in sorted(REPO.iterdir()):
        if p.name == ".git":
            continue
        size = du(p) if p.is_dir() else p.stat().st_size
        rows.append((size, p.name, "dir" if p.is_dir() else "file"))
    for size, name, kind in sorted(rows, reverse=True)[:22]:
        print(f"  {size/MB:>10.1f} MB  {kind:<4} {name}")
    total = sum(r[0] for r in rows)
    print(f"  {total/MB:>10.1f} MB  TOTAL (excluding .git)")

    print("\n=== caches / build artefacts (SAFE candidates) ===")
    pats = ["__pycache__", ".pytest_cache", ".mypy_cache", ".ipynb_checkpoints", ".ruff_cache"]
    found = defaultdict(int)
    for root, dirs, files in os.walk(REPO):
        if ".git" in dirs:
            dirs.remove(".git")
        for d in list(dirs):
            if d in pats:
                found[d] += du(Path(root) / d)
                dirs.remove(d)
    if not found:
        print("  none")
    for k, v in sorted(found.items(), key=lambda kv: -kv[1]):
        print(f"  {v/MB:>10.1f} MB  {k}")

    print("\n=== files over 100 MB ===")
    big = []
    for root, dirs, files in os.walk(REPO):
        if ".git" in dirs:
            dirs.remove(".git")
        for f in files:
            fp = Path(root) / f
            try:
                s = fp.stat().st_size
            except OSError:
                continue
            if s > 100 * MB:
                big.append((s, fp.relative_to(REPO)))
    for s, rel in sorted(big, reverse=True)[:30]:
        print(f"  {s/MB:>10.1f} MB  {rel}")

    print("\n=== stray logs / backups in the repo root ===")
    strays = [p for p in REPO.iterdir()
              if p.is_file() and (p.suffix in (".log", ".tmp", ".bak") or p.name.endswith("~"))]
    for p in sorted(strays)[:25]:
        print(f"  {p.stat().st_size/MB:>10.3f} MB  {p.name}")
    if not strays:
        print("  none")

    print("\n=== git view: tracked vs untracked size ===")
    try:
        out = subprocess.run(["git", "-C", str(REPO), "status", "--porcelain"],
                             capture_output=True, text=True, timeout=180)
        lines = [l for l in out.stdout.splitlines() if l.strip()]
        print(f"  changed/untracked entries: {len(lines)}")
        for l in lines[:15]:
            print("   ", l[:120])
    except Exception as exc:
        print("  git status unavailable:", exc)

    print("\n=== disk ===")
    for d in ("C:\\", "D:\\"):
        try:
            st = os.statvfs(d) if hasattr(os, "statvfs") else None
            if st:
                free = st.f_bavail * st.f_frsize / (1024 ** 3)
                print(f"  {d} free {free:.1f} GB")
        except Exception:
            pass
    try:
        out = subprocess.run(["powershell", "-NoProfile", "-Command",
                              "Get-PSDrive C,D | Select-Object Name,@{n='FreeGB';e={[math]::Round($_.Free/1GB,1)}} | ConvertTo-Json"],
                             capture_output=True, text=True, timeout=120)
        print("  ", out.stdout.strip()[:300])
    except Exception as exc:
        print("  drive probe failed:", exc)

    print("\nNOTE: nothing has been deleted. Classification and sizes are reported for the operator to choose.")


if __name__ == "__main__":
    main()
