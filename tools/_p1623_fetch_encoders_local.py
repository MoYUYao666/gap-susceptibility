# -*- coding: utf-8 -*-
r"""Fetch the A23 encoder weights on this laptop through ModelScope and expose them where the transfer script
expects them (`<models-root>/<local dir>`).

The laptop cannot reach hf-mirror (HTTP 403), so ModelScope is the only working source here; the cloud bundle
uses the mirror-first policy instead. Downloads land in the ModelScope cache and are then linked into
`models/<local dir>` with a directory junction (no admin rights needed on Windows).

    python tools/_p1623_fetch_encoders_local.py [--apply]
"""
from __future__ import annotations

import argparse
import importlib.util
import io
import os
import subprocess
import sys

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
os.chdir(REPO)
MODELS_ROOT = os.path.join(REPO, "models")
MS_CACHE = os.path.join(MODELS_ROOT, "ms_cache")


def load_registry():
    spec = importlib.util.spec_from_file_location(
        "a23menc", os.path.join(REPO, "tools", "_p1614_a23_multi_encoder_transfer.py"))
    mod = importlib.util.module_from_spec(spec)
    sys.modules["a23menc"] = mod
    spec.loader.exec_module(mod)
    for name in ("ENCODERS", "REGISTRY", "ENCODER_REGISTRY"):
        reg = getattr(mod, name, None)
        if isinstance(reg, dict):
            print("registry:", name, "->", len(reg), "encoders")
            return reg
    raise SystemExit("no encoder registry found in the script")


def repo_of(entry) -> str | None:
    for key in ("repo_id", "repo", "hf_repo"):
        if isinstance(entry.get(key), str):
            return entry[key]
    for key in ("snapshot", "weights"):
        v = entry.get(key)
        if isinstance(v, dict) and isinstance(v.get("repo_id"), str):
            return v["repo_id"]
    return None


def local_dir_of(entry) -> str | None:
    for key in ("local_dir", "local", "dir"):
        if isinstance(entry.get(key), str):
            return entry[key]
    for key in ("snapshot", "weights"):
        v = entry.get(key)
        if isinstance(v, dict) and isinstance(v.get("local"), str):
            return v["local"]
    return None


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    a = ap.parse_args()
    os.environ.setdefault("MODELSCOPE_CACHE", MS_CACHE)
    reg = load_registry()
    plan = []
    for name, entry in reg.items():
        repo = repo_of(entry)
        ld = local_dir_of(entry)
        if not repo or not ld:
            print("  %-26s no repo/local declared -> skipped" % name)
            continue
        target = os.path.join(MODELS_ROOT, ld)
        present = os.path.isdir(target) and any(
            f.endswith((".bin", ".safetensors", ".pt")) for f in os.listdir(target)) if os.path.isdir(target) else False
        plan.append((name, repo, target, present))
        print("  %-26s %-42s %-34s %s" % (name, repo, ld, "PRESENT" if present else "missing"))
    todo = [p for p in plan if not p[3]]
    print("to fetch: %d" % len(todo))
    if not a.apply:
        print("dry run: pass --apply to download and link")
        return 0

    from modelscope import snapshot_download
    for name, repo, target, _ in todo:
        print("== fetching %s (%s)" % (name, repo), flush=True)
        try:
            snap = snapshot_download(repo)
        except Exception as exc:
            print("   FAILED: %s %s" % (type(exc).__name__, str(exc)[:180]), flush=True)
            continue
        print("   snapshot:", snap, flush=True)
        if os.path.isdir(target) or os.path.exists(target):
            print("   target already exists, leaving it alone:", target)
            continue
        os.makedirs(os.path.dirname(target), exist_ok=True)
        rc = subprocess.run(["cmd", "/c", "mklink", "/J", target, snap],
                            capture_output=True, text=True).returncode
        print("   junction %s -> %s (rc=%d)" % (target, snap, rc))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())