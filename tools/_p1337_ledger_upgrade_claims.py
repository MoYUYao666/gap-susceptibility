# -*- coding: utf-8 -*-
"""Add the upgrade-round claims to both ledgers (A1 and Paper A).

    python tools/_p1337_ledger_upgrade_claims.py [--apply]
"""
from __future__ import annotations

import argparse
import ast
import io

A1 = "tools/_claim_ledger_a1.py"
PA = "tools/_claim_ledger_paperA.py"

A1_ADD = '''    # ---- upgrade round: template robustness, real retrieval, within-run, cross-domain, stopping scope
    tpl = load("outputs/analysis/a1_margin_templates.json")
    m_sp, cg_sp, r_m, r_cg = [], [], [], []
    for _tag, _v in tpl["models"].items():
        _top = [r["top1"] for r in _v["rows"]]
        _m = [r["mass_0.01"] for r in _v["rows"]]
        _cg = [r["CG"] for r in _v["rows"]]
        _n = len(_top)
        _mean = lambda x: sum(x) / len(x)
        _cov = sum((a - _mean(_top)) * (b - _mean(_m)) for a, b in zip(_top, _m))
        _sx = (sum((a - _mean(_top)) ** 2 for a in _top)) ** 0.5
        _sy = (sum((b - _mean(_m)) ** 2 for b in _m)) ** 0.5
        r_m.append(_cov / (_sx * _sy))
        _cov2 = sum((a - _mean(_top)) * (b - _mean(_cg)) for a, b in zip(_top, _cg))
        _sy2 = (sum((b - _mean(_cg)) ** 2 for b in _cg)) ** 0.5
        r_cg.append(_cov2 / (_sx * _sy2))
        m_sp.append(max(_m) - min(_m))
        cg_sp.append(max(_cg) - min(_cg))
    claim("template M(0.01) spread min", 0.032, min(m_sp), "...a1_margin_templates", 3)
    claim("template M(0.01) spread max", 0.047, max(m_sp), "...a1_margin_templates", 3)
    claim("template CG spread min", 0.025, min(cg_sp), "...a1_margin_templates", 3)
    claim("template CG spread max", 0.094, max(cg_sp), "...a1_margin_templates", 3)
    claim("template r(M,top1) min", -0.91, min(r_m), "...a1_margin_templates", 2)
    claim("template r(M,top1) max", -0.84, max(r_m), "...a1_margin_templates", 2)
    claim("template r(CG,top1) min", -0.16, min(r_cg), "...a1_margin_templates", 2)
    claim("template r(CG,top1) max", 0.20, max(r_cg), "...a1_margin_templates", 2)
    ret = load("outputs/analysis/a1_retrieval_realfinetune.json")
    claim("retrieval real frozen R@1", 18.4, ret["frozen"]["R@1_i2t"], "...a1_retrieval_realfinetune:frozen", 1)
    _rows = [c for ck in ret["runs"].values() for c in ck]
    claim("retrieval real best R@1", 29.4, max(c["R@1_i2t"] for c in _rows), "...a1_retrieval_realfinetune", 1)
    claim("retrieval real min CG", 0.49, min(c["CG"] for c in _rows), "...a1_retrieval_realfinetune", 2)
    claim("retrieval real checkpoints", 18, len(_rows), "...a1_retrieval_realfinetune", 0)
    wr = load("outputs/analysis/a1_showdown_within_run.json")["within_run_pearson"]
    claim("within-run r(M)", -0.99, wr["M(0.01)"]["mean"], "...a1_showdown_within_run", 2)
    claim("within-run r(tau)", 0.99, wr["tau5"]["mean"], "...a1_showdown_within_run", 2)
    claim("within-run r(CG)", -0.43, wr["CG"]["mean"], "...a1_showdown_within_run", 2)
    cr = load("outputs/analysis/a1_campaign_crossdomain.json")
    _crows = [c for ck in cr["runs"].values() for c in ck]
    claim("cross-domain top1 min", 44.4, min(c["top1"] for c in _crows), "...a1_campaign_crossdomain", 1)
    claim("cross-domain top1 max", 54.6, max(c["top1"] for c in _crows), "...a1_campaign_crossdomain", 1)
    cert = load("outputs/analysis/a1_certificate_rule.json")
    claim("stopping rule mean regret", 2.77, cert["recommended"]["mean_regret"], "...a1_certificate_rule", 2)
    claim("last-epoch mean regret", 13.8, cert["baselines"]["last_epoch"]["mean_regret"], "...a1_certificate_rule", 1)
    claim("first-epoch mean regret", 0.0, cert["baselines"]["first_epoch"]["mean_regret"], "...a1_certificate_rule", 2)
    it = load("outputs/analysis/a1_certificate_interior.json")
    _irows = [c for ck in it["runs"].values() for c in ck]
    claim("interior control runs", 4, len(it["runs"]), "...a1_certificate_interior", 0)
    claim("interior control n", 24, len(_irows), "...a1_certificate_interior", 0)

'''

PA_HELPER_OLD = """            cur = j(rel)
            for part in path.split("."):
                cur = cur[part]"""
PA_HELPER_NEW = """            cur = j(rel)
            for part in path.split("."):
                cur = cur[int(part)] if isinstance(cur, list) else cur[part]"""

PA_ADD = '''    # ---- upgrade round: ODE diagnostics and rank/family dynamics
    for _name, _val, _rel, _path, _tol in (
        ("ODE mean R2", 0.858, "outputs/analysis/paperA_ode_diagnostics.json", "R2_overall.mean", 0.001),
        ("ODE median R2", 0.94, "outputs/analysis/paperA_ode_diagnostics.json", "R2_overall.median", 0.005),
        ("ODE share above 0.9", 0.635, "outputs/analysis/paperA_ode_diagnostics.json", "R2_overall.share_above_0.9", 0.002),
        ("ODE share below 0.5", 0.083, "outputs/analysis/paperA_ode_diagnostics.json", "R2_overall.share_below_0.5", 0.002),
        ("LoRA alpha", -0.0245, "outputs/analysis/paperA_lora_vs_fullft.json", "by_family.0.alpha_mean", 0.0005),
        ("adapter alpha", -0.0393, "outputs/analysis/paperA_lora_vs_fullft.json", "by_family.1.alpha_mean", 0.0005),
        ("full-FT alpha", -0.0413, "outputs/analysis/paperA_lora_vs_fullft.json", "by_family.2.alpha_mean", 0.0005),
        ("LoRA R2", 0.9486, "outputs/analysis/paperA_lora_vs_fullft.json", "by_family.0.R2_mean", 0.001),
        ("adapter R2", 0.6694, "outputs/analysis/paperA_lora_vs_fullft.json", "by_family.1.R2_mean", 0.001),
        ("full-FT R2", 0.9217, "outputs/analysis/paperA_lora_vs_fullft.json", "by_family.2.R2_mean", 0.001),
        ("rank trend text-only", -0.464, "outputs/analysis/paperA_rank_position_dynamics.json",
         "trend.text_only.spearman_rank_alpha", 0.002),
        ("rank trend both", -0.179, "outputs/analysis/paperA_rank_position_dynamics.json",
         "trend.both.spearman_rank_alpha", 0.002),
    ):
        claim(_name, _val, _rel, _path, _tol)

'''


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    a = ap.parse_args()
    s = io.open(A1, encoding="utf-8").read()
    if "upgrade round: template robustness" not in s:
        anchor = "    # ---- epoch sweep correlation (manuscript abstract/intro/epoch subsection)"
        assert s.count(anchor) == 1
        s = s.replace(anchor, A1_ADD + anchor, 1)
        print("  A1 ledger extended")
    if not a.apply:
        print("  (dry run)")
        return 0
    io.open(A1, "w", encoding="utf-8", newline="").write(s)
    ast.parse(io.open(A1, encoding="utf-8").read())

    p = io.open(PA, encoding="utf-8").read()
    if PA_HELPER_OLD in p:
        p = p.replace(PA_HELPER_OLD, PA_HELPER_NEW, 1)
        print("  Paper A ledger helper accepts list indices")
    if "upgrade round: ODE diagnostics" not in p:
        anchor = '    print("=" * 118)'
        assert p.count(anchor) == 1, p.count(anchor)
        p = p.replace(anchor, PA_ADD + anchor, 1)
        print("  Paper A ledger extended")
    io.open(PA, "w", encoding="utf-8", newline="").write(p)
    ast.parse(io.open(PA, encoding="utf-8").read())
    print("  written")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
