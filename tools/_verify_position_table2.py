# -*- coding: utf-8 -*-
r"""修 `_verify_position_table.py` 的归档路径（2026-10-08 07:45）。

## 修正

| 骨干 | 我之前写的路径 | **实际路径** |
|---|---|---|
| SigLIP B/16 | `outputs/siglip` | **`outputs/siglip_strict`**（`seed{N}/s4_..._text_only` / `s4_..._both` / `s6_..._vision_only`） |
| BioCLIP B/16 | `outputs/strict_freeze_bioclip`（逐 run） | **同目录但只有 `results_partial.json`**（**逐 run `results.json` 数为 0**；值在 `summary` 里，且含 `sd`/`n`，由 `tools/_exp3_bioclip_harvest.py` 从运行日志解析落盘） |

**BioCLIP 是"有汇总无逐 run"**——按可复现原则，**汇总值本身有来源**（`results_partial.json:summary`，
注明了解析脚本），但与 SigLIP/CLIP 的"逐 run 可复算"**强度不同**，须如实标注。

    python tools\_verify_position_table2.py [--apply]
"""
from __future__ import annotations

import glob
import io
import json
import statistics as st
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
OUT = REPO / "outputs" / "analysis" / "position_table_verification.json"

PAPER = {
    "CLIP B/32":     {"patch": 32, "text_only": -0.0465, "both": -0.0258, "vision_only": +0.0106},
    "OpenCLIP B/32": {"patch": 32, "text_only": +0.0694, "both": +0.0881, "vision_only": +0.0925},
    "SigLIP B/16":   {"patch": 16, "text_only": +0.0664, "both": -0.0114, "vision_only": +0.0522},
    "BioCLIP B/16":  {"patch": 16, "text_only": -0.3671, "both": -0.4515, "vision_only": -0.2927},
}

# 逐 run 归档（glob 模板）
RUNS = {
    "CLIP B/32":     "outputs/strict_freeze/{arm}/seed*/results.json",
    "OpenCLIP B/32": "outputs/strict_freeze_openclip/{arm}/seed*/results.json",
    "SigLIP B/16":   "outputs/siglip_strict/seed*/{siglip_dir}/results.json",
}
SIGLIP_DIR = {"text_only": "s4_siglip_lora_text_only", "both": "s4_siglip_lora_both",
              "vision_only": "s6_siglip_lora_vision_only"}
# BioCLIP：汇总归档
BIOCLIP_SUMMARY = "outputs/strict_freeze_bioclip/results_partial.json"


def cg_delta(f: Path):
    try:
        d = json.loads(io.open(f, encoding="utf-8").read())
    except Exception:
        return None
    g = d.get("initial_gap", {}).get("centroid_gap") if isinstance(d.get("initial_gap"), dict) else None
    h = d.get("final_gap", {}).get("centroid_gap") if isinstance(d.get("final_gap"), dict) else None
    return (h - g) if (g is not None and h is not None) else None


def main() -> int:
    apply = "--apply" in sys.argv
    print("=== 复算论文 tab:position_strict ===")
    report, bad = {}, 0

    for name, paper in PAPER.items():
        print(f"\n  ── {name}（patch {paper['patch']}）──")
        rec = {"patch": paper["patch"], "arms": {}, "evidence": "per-run"}
        if name == "BioCLIP B/16":
            p = REPO / BIOCLIP_SUMMARY
            d = json.loads(io.open(p, encoding="utf-8").read())
            rec["evidence"] = "summary-only"
            rec["source"] = BIOCLIP_SUMMARY
            for arm, key in (("text_only", "r4_text_only"), ("both", "r4_both"),
                             ("vision_only", "r4_vision_only")):
                v = d["summary"][key]["mean"]
                ok = abs(v - paper[arm]) <= 0.0005
                bad += not ok
                print(f"     {arm:<12} 论文 {paper[arm]:+.4f} ｜ 归档 {v:+.4f}"
                      f"（n={d['summary'][key]['n']}, sd={d['summary'][key]['sd']}）"
                      f" ｜ {'✅' if ok else '❌'}")
                rec["arms"][arm] = {"paper": paper[arm], "computed": v,
                                    "n": d["summary"][key]["n"], "pass": bool(ok)}
        else:
            for arm in ("text_only", "both", "vision_only"):
                pat = RUNS[name].format(arm=arm, siglip_dir=SIGLIP_DIR.get(arm, ""))
                files = glob.glob(str(REPO / pat))
                vals = [v for v in (cg_delta(Path(f)) for f in files) if v is not None]
                if not vals:
                    print(f"     {arm:<12} ❌ 无归档 run（{pat}）")
                    bad += 1
                    rec["arms"][arm] = {"paper": paper[arm], "n": 0}
                    continue
                m = st.mean(vals)
                ok = abs(m - paper[arm]) <= max(0.0005, abs(paper[arm]) * 0.005)
                bad += not ok
                print(f"     {arm:<12} 论文 {paper[arm]:+.4f} ｜ 归档均值 {m:+.4f}"
                      f"（n={len(vals)}）｜ {'✅' if ok else '❌'}")
                rec["arms"][arm] = {"paper": paper[arm], "computed": round(m, 6),
                                    "n": len(vals), "pass": bool(ok),
                                    "values": [round(v, 5) for v in vals]}
        if all(rec["arms"][a].get("computed") is not None for a in ("text_only", "both", "vision_only")):
            best = min(("text_only", "both", "vision_only"),
                       key=lambda a: rec["arms"][a]["computed"])
            rec["most_protective"] = best
            print(f"     → 最保护臂 = **{best}**")
        report[name] = rec

    print("\n  === 规律检验（论文措辞）===")
    viol = []
    for name, rec in report.items():
        if "most_protective" not in rec:
            continue
        expect = "text_only" if rec["patch"] == 32 else "both"
        got = rec["most_protective"]
        mark = "✅" if got == expect else "❌ 违反"
        if got != expect:
            viol.append(name)
        print(f"     {name:<16} patch={rec['patch']:<3} 预期 {expect:<10} 实测 {got:<10} {mark}")

    print(f"\n  === 结论 ===")
    print(f"     复算失败项: {bad}")
    print(f"     违反规律的骨干: {viol if viol else '无'}")
    if apply:
        OUT.parent.mkdir(parents=True, exist_ok=True)
        io.open(OUT, "w", encoding="utf-8", newline="").write(
            json.dumps({"table": report, "bad": bad, "violations": viol},
                       ensure_ascii=False, indent=1))
        print(f"     ✅ 已写 {OUT.relative_to(REPO)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
