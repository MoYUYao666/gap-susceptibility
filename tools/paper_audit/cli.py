# -*- coding: utf-8 -*-
"""Command line interface for the paper-audit mode (English-only artifact).

    python -m tools.paper_audit list-profiles
    python -m tools.paper_audit list-checks [--dimension A]
    python -m tools.paper_audit freeze --profile p3_prl --write
    python -m tools.paper_audit audit --profile paperA_nc
    python -m tools.paper_audit audit --profile paperA_nc --staged --out docs/audits
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

from .profiles import PROFILES, get_profile
from .registry import CHECKS, DIMENSIONS
from . import checks as engine
from .report import write_report, print_summary
from .model import Severity


ROOT = Path(__file__).resolve().parents[2]


def cmd_list_profiles(args) -> int:
    print("%-18s %-52s %s" % ("profile", "label", "manuscript"))
    for pid in sorted(PROFILES):
        p = PROFILES[pid]
        print("%-18s %-52s %s" % (pid, p["label"], p["manuscript"]))
    return 0


def cmd_list_checks(args) -> int:
    rows = [c for c in CHECKS if not args.dimension or c.dimension == args.dimension]
    if args.json:
        import json
        print(json.dumps([{"id": c.id, "dimension": c.dimension,
                           "severity": c.severity.value, "title": c.title,
                           "method": c.method, "automated": c.automated} for c in rows],
                         indent=2, ensure_ascii=False))
        return 0
    current = None
    for c in rows:
        if c.dimension != current:
            current = c.dimension
            print("\n[%s] %s" % (c.dimension, DIMENSIONS.get(c.dimension, "")))
        print("  %-5s %-3s %-5s %s" % (c.id, c.severity.value,
                                       "auto" if c.automated else "man", c.title))
    print("\n%d checks" % len(rows))
    return 0


def cmd_freeze(args) -> int:
    profile = get_profile(args.profile)
    if not profile.get("freeze_paths"):
        print("profile %s has no frozen artefacts; nothing to do" % args.profile)
        return 0
    if not args.write:
        res = engine.compare_freeze(profile)
        print("freeze check: %s" % res)
        if res.get("status") == "skip":
            return 0
        drift = bool(res.get("added") or res.get("removed") or res.get("changed"))
        return 1 if drift else 0
    path = engine.freeze_profile(profile)
    entries = len(engine.tree_hashes(profile["freeze_paths"]))
    print("freeze manifest written: %s (%d files)" % (path.relative_to(ROOT).as_posix(), entries))
    return 0


def cmd_audit(args) -> int:
    profile = get_profile(args.profile)
    opts = {"staged_result": None, "command_timeout": args.command_timeout}
    if args.staged:
        staged_cmd = profile.get("staged_command")
        if not staged_cmd:
            print("note: profile has no staged_command; --staged ignored")
        else:
            print("running staged compile: %s" % " ".join(staged_cmd))
            rc, out = engine.run_cmd(staged_cmd, timeout=args.command_timeout)
            expect = profile.get("staged_expect", "")
            ok = rc == 0 and (not expect or expect in out)
            tail = "\n".join(out.strip().splitlines()[-5:])
            opts["staged_result"] = {"ok": ok, "message": "rc=%d %s" % (rc, tail)}
    report = engine.run_audit(profile, opts)
    out_dir = Path(args.out) if args.out else ROOT / "docs" / "audits"
    if not out_dir.is_absolute():
        out_dir = ROOT / out_dir
    md, js = write_report(report, out_dir)
    print_summary(report)
    print("markdown: %s" % md)
    print("json:     %s" % js)
    print("reproduce: python -m tools.paper_audit audit --profile %s" % args.profile)

    gate = report.gate_failures()
    fail_on = (args.fail_on or "P1").upper()
    if fail_on == "NONE":
        return 0
    if fail_on == "P0":
        return 1 if [f for f in gate if f.severity == Severity.P0] else 0
    return 1 if gate else 0



def cmd_selftest(args) -> int:
    from .model import Severity
    problems = []
    ids = [c.id for c in CHECKS]
    if len(ids) != len(set(ids)):
        problems.append("duplicate check ids")
    for c in CHECKS:
        if c.dimension not in DIMENSIONS:
            problems.append("bad dimension %s in %s" % (c.dimension, c.id))
        if not isinstance(c.severity, Severity):
            problems.append("bad severity in %s" % c.id)
        if not c.title or not c.method:
            problems.append("empty title/method in %s" % c.id)
    tdir = Path(__file__).resolve().parent / "templates"
    for name in ("AUDIT_REPORT_TEMPLATE.md", "FIX_EVIDENCE_TEMPLATE.md",
                 "SUBMISSION_READINESS_TEMPLATE.md"):
        if not (tdir / name).is_file():
            problems.append("missing template %s" % name)
    frozen_checked = 0
    for pid in sorted(PROFILES):
        prof = PROFILES[pid]
        for key in ("id", "label", "manuscript", "tex", "pdfs", "logs", "limits",
                    "freeze_manifest"):
            if key not in prof:
                problems.append("profile %s missing key %s" % (pid, key))
        if prof.get("freeze_paths"):
            manifest = ROOT / prof["freeze_manifest"]
            if not manifest.is_file():
                problems.append("profile %s has freeze_paths but no baseline manifest" % pid)
            else:
                res = engine.compare_freeze(prof)
                frozen_checked += res.get("n", 0)
                for bucket in ("changed", "removed", "added"):
                    if res.get(bucket):
                        problems.append("profile %s freeze %s: %s" % (pid, bucket, res[bucket][:5]))
    print("registry checks: %d" % len(CHECKS))
    print("profiles: %d" % len(PROFILES))
    print("templates: OK")
    print("frozen files verified: %d" % frozen_checked)
    mech_cases = engine.selftest_mechanical()
    mech_bad = [c for c in mech_cases if not c[4]]
    for cid, case, expect, got, ok, detail in mech_cases:
        print("  mech %-5s %-32s expect=%-6s got=%-6s %s"
              % (cid, case, expect, got, "OK" if ok else "FAIL"))
        if not ok:
            problems.append("mechanical fixture %s/%s: expected %s, got %s (%s)"
                            % (cid, case, expect, got, detail))
    print("mechanical gate fixtures: %d/%d passed"
          % (len(mech_cases) - len(mech_bad), len(mech_cases)))
    if problems:
        print("SELFTEST FAILED")
        for p in problems:
            print("  - %s" % p)
        return 1
    print("SELFTEST PASSED")
    return 0


def cmd_render_template(args) -> int:
    tdir = Path(__file__).resolve().parent / "templates"
    name = {"audit": "AUDIT_REPORT_TEMPLATE.md",
            "fix": "FIX_EVIDENCE_TEMPLATE.md",
            "readiness": "SUBMISSION_READINESS_TEMPLATE.md"}[args.kind]
    path = tdir / name
    if not path.is_file():
        print("template missing: %s" % path)
        return 1
    sys.stdout.write(path.read_text(encoding="utf-8"))
    return 0


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(prog="python -m tools.paper_audit",
                                description="Standardised manuscript audit mode")
    sub = p.add_subparsers(dest="command", required=True)

    sp = sub.add_parser("list-profiles", help="list manuscript profiles")
    sp.set_defaults(func=cmd_list_profiles)

    sc = sub.add_parser("list-checks", help="list the check registry")
    sc.add_argument("--dimension", choices=list("ABCDEFGHIJ"))
    sc.add_argument("--json", action="store_true")
    sc.set_defaults(func=cmd_list_checks)

    sf = sub.add_parser("freeze", help="record or verify the frozen submission artefacts")
    sf.add_argument("--profile", required=True, choices=sorted(PROFILES))
    sf.add_argument("--write", action="store_true", help="write the baseline manifest")
    sf.set_defaults(func=cmd_freeze)

    sa = sub.add_parser("audit", help="run the full audit")
    sa.add_argument("--profile", required=True, choices=sorted(PROFILES))
    sa.add_argument("--out", default=None, help="output directory (default docs/audits)")
    sa.add_argument("--staged", action="store_true", help="run the profile staged compile")
    sa.add_argument("--fail-on", default="P1", choices=["P0", "P1", "NONE"],
                    help="exit non-zero on this severity (default P1)")
    sa.add_argument("--command-timeout", type=int, default=900)
    sa.set_defaults(func=cmd_audit)

    ss = sub.add_parser("selftest", help="validate the registry, profiles, templates and freeze baselines")
    ss.set_defaults(func=cmd_selftest)

    st = sub.add_parser("render-template", help="print a report / fix / readiness template")
    st.add_argument("--kind", required=True, choices=["audit", "fix", "readiness"])
    st.set_defaults(func=cmd_render_template)
    return p


def main(argv=None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        return args.func(args)
    except KeyboardInterrupt:
        return 130
    except Exception as exc:  # a runner defect must be visible, not swallowed
        print("runner error: %s: %s" % (type(exc).__name__, exc), file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
