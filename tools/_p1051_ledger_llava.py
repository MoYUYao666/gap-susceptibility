# -*- coding: utf-8 -*-
r"""Add the LLaVA-7B bfloat16 campaign to Paper A's claim ledger, as a scoped negative result.

Operator decision 2026-10-16: report it as a cross-model **limitation**, not as evidence for or against the
paper's thesis. Before any number can be cited, it must be in the ledger.

Design of the entries, to avoid the self-comparison trap (`claim(name, X, X)` verifies nothing):

* the **manuscript values are literals**, taken from the archive and written out by hand;
* the **computed values are recomputed from the per-record files** independently;
* a **cross-check** then compares the per-record recomputation against the summary file the sweep wrote, so
  two separately produced artefacts must agree before anything is claimed;
* one entry asserts a structural fact (text-only equals frozen, bit for bit) rather than a rounded number.

    python tools/_p1051_ledger_llava.py --apply
"""
from __future__ import annotations

import argparse
import ast
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
LEDGER = REPO / "tools" / "_claim_ledger.py"
DATA = REPO / "outputs" / "llava_bf16_sites_cloud"
MARK = "①h LLaVA"

BLOCK = '''
    # ── ①h LLaVA-1.5-7B bf16（2026-10-16，**负结果/局限**；补充材料 F 节）────────────────────────
    # 批次：1500 训练 / 500 评测（各 1 seed×3），3 epochs，rank 8，**bf16**，strict freezing，4 arms × 3 seeds。
    # 归档：outputs/llava_bf16_sites_cloud/{arm}_s{seed}.json（云端逐字节校验后取回）
    # ⚠️ 口径（必须随数字一起报告）：本批 DG__ 为「均值成对距离 − 两模态内距离」，**非**
    #    src/gap_metrics.py 的方差式 W2 = sqrt(CG^2 + ||sigma_I − sigma_T||^2)；文本侧为 LLM token 嵌入
    #    （未排除图像 token），非独立文本编码器输出。⇒ **不与 Qwen2-VL-2B 的 18.0/66.5/87.9 比较**。
    _ldir = REPO / "outputs" / "llava_bf16_sites_cloud"
    _ll = {}
    for _f in sorted(_ldir.glob("*.json")):
        if _f.name in ("llava_sites.json", "train_progress.json"):
            continue
        _d = json.loads(io.open(_f, encoding="utf-8").read())
        if "arm" in _d:
            _ll[(_d["arm"], _d["seed"])] = _d

    if len(_ll) == 12:
        _agg = json.loads(io.open(_ldir / "llava_sites.json", encoding="utf-8").read())

        def _rel_mean_sd(arm):
            _r = [100 * (v["dg_after"] - v["dg_before"]) / v["dg_before"]
                  for k, v in _ll.items() if k[0] == arm]
            return st.mean(_r), st.pstdev(_r)

        # 字面值来自归档（2026-10-16 实测），下面独立重算并逐条断言
        for _arm, _mean_lit, _sd_lit in (("frozen", 0.2971, 0.0),
                                         ("text_only", 0.2971, 0.0),
                                         ("vision_only", 13.3334, 4.7368),
                                         ("both", 6.0676, 6.5465)):
            _m, _s = _rel_mean_sd(_arm)
            claim(f"LLaVA-7B bf16 {_arm} DG__ 相对变化(%) mean, n=3", _mean_lit, _m,
                  f"llava_bf16_sites_cloud/{_arm}_s*.json: (dg_after-dg_before)/dg_before", tol=0.02)
            claim(f"LLaVA-7B bf16 {_arm} DG__ 相对变化(%) sd, n=3", _sd_lit, _s,
                  f"llava_bf16_sites_cloud/{_arm}_s*.json: 总体标准差", tol=0.02)

        # 交叉校验：汇总文件（sweep 自己写的）与逐条重算必须一致
        _sum_rel = {r["arm"]: r.get("dg_rel_change") for r in _agg["runs"] if r.get("dg_rel_change") is not None}
        _x_ok = 0
        for _k, _v in _ll.items():
            _s = next((r for r in _agg["runs"] if r["arm"] == _k[0] and r["seed"] == _k[1]), None)
            if _s is not None and abs(_s["dg_after"] - _v["dg_after"]) < 1e-9:
                _x_ok += 1
        claim("LLaVA 汇总文件与逐条记录一致的 run 数", 12.0, float(_x_ok),
              "llava_sites.json:runs[] 与各 {arm}_s{seed}.json 的 dg_after 逐位比较", tol=0.0)
        claim("LLaVA 汇总文件登记的精度档", 1.0, 1.0 if _agg.get("precision") == "bf16" else 0.0,
              "llava_sites.json:precision（已由 tools/_p1053 修正为 bf16）", tol=0.0)

        # 结构性事实：text_only 与 frozen 末态逐位相同
        _t = sorted(v["dg_after"] for k, v in _ll.items() if k[0] == "text_only")
        _z = sorted(v["dg_after"] for k, v in _ll.items() if k[0] == "frozen")
        claim("LLaVA text_only 与 frozen 末态 DG__ 逐位相同的 seed 数",
              3.0, 3.0 if _t == _z else 0.0,
              "llava_bf16_sites_cloud: text_only_s*.json vs frozen_s*.json 的 dg_after", tol=0.0)

        # 起点：四臂共用同一结构（同一 frozen 基线）
        _b = {round(v["dg_before"], 6) for v in _ll.values()}
        claim("LLaVA 起始 DG__（四臂共用同一值）", 0.261161, list(_b)[0] if len(_b) == 1 else -1.0,
              "llava_bf16_sites_cloud/*.json:dg_before", tol=0.00001)
        _c = {round(v["cg_before"], 6) for v in _ll.values()}
        claim("LLaVA 起始 CG（四臂共用同一值）", 0.743283, list(_c)[0] if len(_c) == 1 else -1.0,
              "llava_bf16_sites_cloud/*.json:cg_before", tol=0.00001)

        # 可训练参数（分塔隔离的验证，来自汇总文件的 isolation_verified）
        _iso = _agg.get("isolation_verified", {})
        claim("LLaVA text_only 可训练参数", 19988480.0,
              float(_iso.get("text_only", {}).get("n_trainable", -1)), tol=0.5)
        claim("LLaVA vision_only 可训练参数", 3645440.0,
              float(_iso.get("vision_only", {}).get("n_trainable", -1)), tol=0.5)
        claim("LLaVA both 可训练参数", 23633920.0,
              float(_iso.get("both", {}).get("n_trainable", -1)), tol=0.5)

'''


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    a = ap.parse_args()
    src = LEDGER.read_text(encoding="utf-8")
    if MARK in src:
        print("  already in the ledger")
        return 0
    rows = list(DATA.glob("*.json")) if DATA.exists() else []
    print(f"  {len(rows)} files in {DATA.name}")
    if len(rows) < 13:
        print("  the archive looks incomplete; refusing")
        return 2
    if "import statistics as st" not in src:
        src = src.replace("import json", "import json\nimport statistics as st", 1)
        print("  added `import statistics as st`")
    anchor = '\n    print(f"\\n  === 台账汇总 ===")'
    idx = src.rfind(anchor)
    assert idx > 0, "could not find the summary block"
    out = src[:idx] + BLOCK + src[idx:]
    ast.parse(out)
    print("  ledger block prepared and parses")
    if not a.apply:
        print("  (dry run)")
        return 0
    LEDGER.write_text(out, encoding="utf-8", newline="")
    print("  written")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
