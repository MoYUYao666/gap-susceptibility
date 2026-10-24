#!/usr/bin/env python
# -*- coding: utf-8 -*-
r"""Gate for the cloud round: check every expected artifact, then print the retrieval list.

Run this on the instance BEFORE shutting it down, and again on the laptop AFTER copying the artifacts back.
It exits non-zero while anything is missing or malformed, and the instance must not be stopped in that state
(repository rule: verify -> retrieve -> shut down, in that order).

    python cloud_next/verify_cloud_artifacts.py                 # report only
    python cloud_next/verify_cloud_artifacts.py --apply         # also write outputs/analysis/cloud_round_check.json
    python cloud_next/verify_cloud_artifacts.py --phase phase1  # restrict to one phase
"""
from __future__ import annotations

import argparse
import glob
import io
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SPEC = os.path.join(ROOT, "cloud_next", "expected_outputs.json")


def load_json(rel: str):
    p = os.path.join(ROOT, rel)
    if not os.path.exists(p):
        return None, "missing"
    try:
        return json.load(io.open(p, encoding="utf-8")), p
    except Exception as exc:
        return None, "unreadable: %s" % exc


def count_records(obj, key):
    if isinstance(obj, dict):
        v = obj.get(key)
        if isinstance(v, list):
            return len(v)
        if isinstance(v, dict):
            return len(v)
    return None


def check_artifact(spec: dict) -> tuple[bool, str]:
    if "glob" in spec:
        hits = sorted(glob.glob(os.path.join(ROOT, spec["glob"])))
        need = int(spec.get("min_count", 1))
        if len(hits) < need:
            return False, "%d file(s) matched %s, need >= %d" % (len(hits), spec["glob"], need)
        for h in hits:
            try:
                obj = json.load(io.open(h, encoding="utf-8"))
            except Exception as exc:
                return False, "%s unreadable: %s" % (os.path.basename(h), exc)
            for k in spec.get("required_keys", []):
                if not isinstance(obj, dict) or k not in obj:
                    return False, "%s lacks key %r" % (os.path.basename(h), k)
        return True, "%d file(s) ok (%s)" % (len(hits), spec["glob"])

    obj, info = load_json(spec["path"])
    if obj is None:
        return False, "%s: %s" % (spec["path"], info)
    for k in spec.get("required_keys", []):
        if not isinstance(obj, dict) or k not in obj:
            return False, "%s lacks key %r" % (spec["path"], k)
    if "min_epochs" in spec:
        got = len(obj.get("dg_star") or []) if isinstance(obj, dict) else 0
        if got < int(spec["min_epochs"]):
            return False, "%s has %d epoch records, need >= %d" % (spec["path"], got, spec["min_epochs"])
    if "min_records" in spec:
        n = count_records(obj, spec.get("record_key", "questions"))
        if n is None or n < int(spec["min_records"]):
            return False, "%s has %s record(s), need >= %d" % (spec["path"], n, spec["min_records"])
    if spec.get("path", "").startswith("outputs/analysis/decoder_attribution_"):
        d = obj.get("delta_DG_percent")
        if d is None or not isinstance(d, (int, float)):
            return False, "%s: delta_DG_percent is not numeric" % spec["path"]
    return True, "ok"


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--phase", default=None, help="restrict to one phase key (phase1..phase4)")
    ap.add_argument("--apply", action="store_true")
    a = ap.parse_args()

    spec = json.load(io.open(SPEC, encoding="utf-8"))
    report = {"checked": [], "failures": [], "phases": {}}
    for phase, blk in spec["phases"].items():
        if a.phase and phase != a.phase:
            continue
        ok_all = True
        print("== %s :: %s" % (phase, blk["title"]))
        rows = []
        for item in blk["artifacts"]:
            ok, msg = check_artifact(item)
            name = item.get("path") or item.get("glob")
            if not ok and item.get("optional"):
                ok, msg = True, "OPTIONAL, not run: %s" % item.get("optional_reason", "no reason recorded")
            rows.append({"artifact": name, "ok": bool(ok), "detail": msg})
            report["checked"].append({"phase": phase, "artifact": name, "ok": bool(ok), "detail": msg})
            if not ok:
                ok_all = False
                report["failures"].append({"phase": phase, "artifact": name, "detail": msg})
            print("   [%s] %-72s %s" % ("OK " if ok else "MISS", str(name)[:72], "" if ok else msg))
        for cc in blk.get("cross_checks", []):
            print("   (manual) %s" % cc)
        report["phases"][phase] = {"ok": ok_all, "rows": rows}
        print("   -> %s" % ("PASS" if ok_all else "FAIL"))

    print("\n== retrieval list ==")
    for g in spec["retrieval"]["globs"]:
        hits = sorted(glob.glob(os.path.join(ROOT, g)))
        print("   %-58s %d file(s)" % (g, len(hits)))

    report["ok"] = not report["failures"]
    if a.apply:
        out = os.path.join(ROOT, "outputs", "analysis", "cloud_round_check.json")
        os.makedirs(os.path.dirname(out), exist_ok=True)
        io.open(out, "w", encoding="utf-8", newline="").write(json.dumps(report, ensure_ascii=False, indent=1))
        print("\nwrote %s" % out)
    print("\nGATE: %s (%d failure(s))" % ("PASS - retrieval may proceed" if report["ok"] else "FAIL - do NOT stop the instance",
                                          len(report["failures"])))
    return 0 if report["ok"] else 1


if __name__ == "__main__":
    sys.exit(main())