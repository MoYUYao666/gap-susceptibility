# -*- coding: utf-8 -*-
r"""最终全面核验（2026-10-12）—— 所有工作面收官后的单一门禁。

跑齐所有既有门禁 + 报告/稿件完整性，输出一张总表。

    python tools\_p406_final_gate.py [--apply]
"""
from __future__ import annotations

import argparse
import glob
import io
import json
import os
import re
import subprocess
import sys
import time
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
OUT = REPO / "outputs" / "analysis" / "final_gate.json"


def run(cmd, cwd=None):
    r = subprocess.run(cmd, cwd=cwd or REPO, capture_output=True,
                       encoding="utf-8", errors="replace")
    return r.returncode, (r.stdout or "") + (r.stderr or "")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    a = ap.parse_args()
    res = {}
    print("=" * 104)
    print("最终门禁")
    print("=" * 104)

    # 1) PR 审计
    rc, out = run([sys.executable, "tools/_p290_final_pr_audit.py"])
    m = re.search(r"(\d+)/(\d+) 通过", out)
    res["pr_audit"] = m.group(0) if m else f"rc={rc}"
    print(f"  1. PR 意见核验（_p290）: {res['pr_audit']}")

    # 2) 编译
    for name in ("main_nc", "main_springer"):
        lg = REPO / "paper合" / f"{name}.log"
        pdf = REPO / "paper合" / f"{name}.pdf"
        if not pdf.exists():
            print(f"  2. {name}: 🔴 无 PDF")
            continue
        o = subprocess.run(["pdfinfo", str(pdf)], capture_output=True,
                           encoding="utf-8", errors="replace").stdout or ""
        pg = re.search(r"Pages:\s+(\d+)", o)
        t = io.open(lg, encoding="utf-8", errors="replace").read() if lg.exists() else ""
        err = len(re.findall(r"^!", t, re.M))
        und = len(re.findall(r"(Citation|Reference) .* undefined", t))
        ovf = len(re.findall(r"Overfull .hbox", t))
        res[name] = {"pages": pg.group(1) if pg else None, "errors": err,
                     "undefined": und, "overfull": ovf}
        flag = "✅" if (err == 0 and und == 0 and ovf == 0) else "🔴"
        print(f"  2. {name}: {flag} {res[name]['pages']} 页 ｜ 错 {err} ｜ 未定义 {und} ｜ Overfull {ovf}")

    # 3) 投稿包一致性
    rc, out = run([sys.executable, "tools/_p190_finish_submission.py", "--apply"])
    same = out.count("✅")
    res["submission_sync"] = "✅" if "已同步" in out else "🔴"
    print(f"  3. 投稿包同步（_p190）: {res['submission_sync']}")

    # 4) 编码损伤
    rc, out = run([sys.executable, "tools/_p394_encoding_damage.py", "--apply"])
    m = re.search(r"干净 (\d+) 个、可疑 (\d+) 个", out)
    res["encoding"] = m.group(0) if m else "?"
    print(f"  4. 编码损伤扫描（_p394）: {res['encoding']}")

    # 5) 全体成员交付件存在性
    print("  5. 交付件：")
    deliverables = [
        "docs/PR_STATS_FIX.md", "docs/PR_CAUSAL_FIX.md", "docs/PR_FAIRNESS_FIX.md",
        "docs/PR_FAIRNESS_FIX2.md", "docs/PR_FAIRNESS_FIX3.md", "docs/PR_WRITING_FIX.md",
        "docs/PR_MORE_MODELS.md", "docs/DINOV2_AUDIT.md",
        "outputs/analysis/pr_stats_hardened.json",
        "outputs/analysis/pr_relative_perturbation.json",
        "outputs/analysis/pr_fullft_lr_sweep_full.json",
        "outputs/analysis/pr_peft_lr_sweep.json",
        "outputs/analysis/pr_adapter_init_check.json",
        "outputs/analysis/dinov2_hetero/fitted/both/seed42/results.json",
        "outputs/analysis/dinov2_hetero/random/text_only/seed42/results.json",
        "outputs/analysis/gallery_noise_cg.json",
        "SUBMISSION/README.md", "SUBMISSION/A1_NeuralNetworks/README.md",
        "SUBMISSION/_old/README.md", "HANDOFF.md", "文件地图.md",
    ]
    miss = []
    for d in deliverables:
        ok = (REPO / d).exists()
        if not ok:
            miss.append(d)
    res["missing_deliverables"] = miss
    print(f"     {len(deliverables) - len(miss)}/{len(deliverables)} 存在"
          + (f" ｜ 🔴 缺 {miss}" if miss else " ✅"))

    # 6) 关键禁语检查（稿件内不得出现）
    print("  6. 稿件禁语检查：")
    banned = {
        "4--37 倍": ["4--37", "4-37", "four to thirty-seven"],
        "universally negative": ["universally negative"],
        "'saturation above 3e-5'": ["saturation above $3\\times10^{-5}$"],
        "isotropic Gaussian noise": ["isotropic Gaussian noise"],
        "guaranteed alignment": ["guaranteed alignment"],
        "zero-overhead": ["zero-overhead"],
        "\\logit 未定义宏": ["\\logit "],
    }
    # 0.986 只在**我们自己的正文**（main*.tex 摘要）里算违规；
    # related_work.tex 里的 0.986 是 \cite{liu2026tpc} 的**他人数值**（正确引用）。
    banned_own = {"无来源的 0.986（仅限 main*.tex）": ["0.986"]}
    files = sorted(glob.glob(str(REPO / "paper合" / "sections" / "*.tex"))) + \
        sorted(glob.glob(str(REPO / "paper合" / "main*.tex")))
    files_own = sorted(glob.glob(str(REPO / "paper合" / "main*.tex")))
    bad = {}
    for label, pats in list(banned.items()) + list(banned_own.items()):
        scan = files_own if label.startswith("无来源的 0.986") else files
        for f in scan:
            t = io.open(f, encoding="utf-8", errors="replace").read()
            for p in pats:
                if p in t:
                    i = t.find(p)
                    ctx = t[max(0, i - 200):i + 100]
                    if "withdrawn" not in ctx and "earlier version" not in ctx:
                        bad.setdefault(label, []).append(Path(f).name)
    for label in list(banned) + list(banned_own):
        print(f"     {'🔴' if label in bad else '✅'} {label}"
              + (f"  → {bad[label]}" if label in bad else ""))
    res["banned_found"] = bad

    # 7) 成员状态
    print("  7. 成员与 GPU：")
    procs = []
    try:
        o = subprocess.run(["powershell", "-NoProfile", "-Command",
                            "Get-CimInstance Win32_Process -Filter \"Name='python.exe'\" | "
                            "ForEach-Object { $_.CommandLine }"],
                           capture_output=True, encoding="utf-8", errors="replace").stdout or ""
        procs = [l for l in o.splitlines() if "tools" in l]
    except Exception:
        pass
    res["running_python"] = len(procs)
    print(f"     运行中的 tools/*.py 进程：{len(procs)}（0 = GPU 已释放）")

    if a.apply:
        OUT.parent.mkdir(parents=True, exist_ok=True)
        res["timestamp"] = time.strftime("%Y-%m-%d %H:%M:%S")
        io.open(OUT, "w", encoding="utf-8", newline="").write(
            json.dumps(res, ensure_ascii=False, indent=1))
        print(f"\n  ✅ 已写 {OUT.relative_to(REPO)}")
    ok = (not miss) and (not bad) and res["encoding"].startswith("干净")
    return 0 if ok else 2


if __name__ == "__main__":
    raise SystemExit(main())
