# -*- coding: utf-8 -*-
r"""Add the interior-optimum monitoring claims to the A1 ledger and stage the new archives for the public mirror.

    python tools/_p1355_claims_and_mirror.py [--apply]
"""
from __future__ import annotations

import argparse
import ast
import io

LEDGER = "tools/_claim_ledger_a1.py"
MIRROR = "tools/_p1284_prepare_public_mirror.py"

CLAIMS = '''    # ---- interior-optimum monitoring validation
    mon = load("outputs/analysis/a1_monitor_interior.json")
    _runs = mon["runs"]
    _tops = [r["top1"] for rows in _runs.values() for r in rows]
    _mass = [r["mass_0.01"] for rows in _runs.values() for r in rows]
    _cg = [r["CG"] for rows in _runs.values() for r in rows]
    _n = len(_tops)
    _m = lambda x: sum(x) / len(x)
    def _pear(a, b):
        ma, mb = _m(a), _m(b)
        cov = sum((x - ma) * (y - mb) for x, y in zip(a, b))
        sa = (sum((x - ma) ** 2 for x in a)) ** 0.5
        sb = (sum((y - mb) ** 2 for y in b)) ** 0.5
        return cov / (sa * sb)
    claim("interior checkpoints", 32, _n, "...a1_monitor_interior", 0)
    claim("interior r(M,top1)", -0.983, _pear(_mass, _tops), "...a1_monitor_interior", 3)
    claim("interior r(CG,top1)", 0.324, _pear(_cg, _tops), "...a1_monitor_interior", 3)
    _reg = {"min_M": [], "min_CG": [], "last": [], "first": []}
    for rows in _runs.values():
        tops = [r["top1"] for r in rows]
        orc = max(tops)
        i_m = min(range(len(rows)), key=lambda i: rows[i]["mass_0.01"])
        i_c = min(range(len(rows)), key=lambda i: rows[i]["CG"])
        _reg["min_M"].append(orc - tops[i_m])
        _reg["min_CG"].append(orc - tops[i_c])
        _reg["last"].append(orc - tops[-1])
        _reg["first"].append(orc - tops[0])
    claim("min-M mean regret", 0.19, _m(_reg["min_M"]), "...a1_monitor_interior", 2)
    claim("min-M max regret", 0.74, max(_reg["min_M"]), "...a1_monitor_interior", 2)
    claim("min-CG mean regret", 2.19, _m(_reg["min_CG"]), "...a1_monitor_interior", 2)
    claim("last-epoch mean regret (interior)", 0.76, _m(_reg["last"]), "...a1_monitor_interior", 2)
    claim("first-epoch mean regret (interior)", 4.03, _m(_reg["first"]), "...a1_monitor_interior", 2)

'''

NEW_MIRROR = [
    "outputs/analysis/p3_upgrade_analysis.json",
    "outputs/analysis/a23_threshold_transfer.json",
    "outputs/analysis/a23_threshold_transfer_extended.json",
    "outputs/analysis/a23_certificate_control.json",
    "outputs/analysis/a23_certificate_adapted.json",
    "outputs/analysis/a1_monitor_interior.json",
    "tools/_p1343_p3_upgrade_analyses.py",
    "tools/_p1344_a23_certificate_control.py",
    "tools/_p1345_a23_threshold_transfer.py",
    "tools/_p1347_commentary_upgrade.py",
    "tools/_p1349_fix_commentary_gates.py",
    "tools/_p1350_record_neucom_with_editor.py",
    "tools/_p1351_a23_extended_transfer.py",
    "tools/_p1352_a23_certificate_adapted.py",
    "tools/_p1354_monitor_interior.py",
]


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    a = ap.parse_args()
    s = io.open(LEDGER, encoding="utf-8").read()
    if "interior-optimum monitoring validation" not in s:
        anchor = "    # ---- epoch sweep correlation (manuscript abstract/intro/epoch subsection)"
        assert s.count(anchor) == 1
        s = s.replace(anchor, CLAIMS + anchor, 1)
        print("  ledger claims added")
    if a.apply:
        io.open(LEDGER, "w", encoding="utf-8", newline="").write(s)
        ast.parse(io.open(LEDGER, encoding="utf-8").read())
    m = io.open(MIRROR, encoding="utf-8").read()
    missing = [x for x in NEW_MIRROR if x not in m]
    print(f"  mirror additions: {len(missing)}")
    if missing:
        anchor = '    "outputs/analysis/a1_campaign_correct.npz",'
        assert m.count(anchor) == 1
        m = m.replace(anchor, anchor + "\n" + "\n".join('    "%s",' % x for x in missing), 1)
        if a.apply:
            io.open(MIRROR, "w", encoding="utf-8", newline="").write(m)
            print("  mirror list extended")
    if not a.apply:
        print("  (dry run)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
