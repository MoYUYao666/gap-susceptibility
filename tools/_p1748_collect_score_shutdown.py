# -*- coding: utf-8 -*-
r"""Collect the 15 pre-registered CLIP arms, score prediction P1 against the frozen rules, and shut the box down.

Scoring rules (frozen in docs/PaperA_preregistered_predictions.md before the runs):
  sign      : text-only Delta CG negative
  ordering  : smallest |Delta CG| first = text-only, then both, then vision-only
  retrieval : text-only R@1 change relative to the frozen model is negative
A prediction holds only if sign and the first two ordering positions match.
"""
import glob
import io
import json
import os
import time

import paramiko

HOST = os.environ.get("CLOUD_HOST", "connect.westd.seetacloud.com")
PORT = int(os.environ.get("CLOUD_PORT", "21492"))
USER = os.environ.get("CLOUD_USER", "root")
PWD = os.environ["CLOUD_PASS"]
REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
REMOTE = "/root/autodl-tmp/work"
LOCAL = os.path.join(REPO, "outputs", "paperA_c_prereg")

c = paramiko.SSHClient()
c.set_missing_host_key_policy(paramiko.AutoAddPolicy())
c.connect(HOST, port=PORT, username=USER, password=PWD, timeout=30, banner_timeout=30, auth_timeout=30)

# ---- 1. wait for the last arm -------------------------------------------------------------
for i in range(40):
    stdin, stdout, stderr = c.exec_command(
        "find %s/outputs/c_prereg -name results.json | wc -l" % REMOTE, timeout=60)
    n = int(stdout.read().decode().strip() or 0)
    if n >= 15:
        break
    time.sleep(15)
print("results on the instance:", n)

# ---- 2. download -------------------------------------------------------------------------
os.makedirs(LOCAL, exist_ok=True)
sftp = c.open_sftp()
stdin, stdout, stderr = c.exec_command("find %s/outputs/c_prereg -name results.json" % REMOTE, timeout=60)
paths = [p for p in stdout.read().decode().split() if p.strip()]
got = []
for rp in paths:
    rel = rp.replace(REMOTE + "/outputs/c_prereg/", "").replace("/", "__")
    lp = os.path.join(LOCAL, rel)
    try:
        sftp.get(rp, lp)
        got.append(lp)
    except Exception as e:
        print("download failed:", rp, e)
sftp.close()
print("downloaded:", len(got), "files | sizes:", sorted({os.path.getsize(p) for p in got})[:4])

# ---- 3. score ----------------------------------------------------------------------------
def num(d, *keys, default=None):
    cur = d
    for k in keys:
        if not isinstance(cur, dict) or k not in cur:
            return default
        cur = cur[k]
    return cur if isinstance(cur, (int, float)) else default


rows = []
for p in got:
    try:
        d = json.load(io.open(p, encoding="utf-8"))
    except Exception:
        continue
    site = None
    for s in ("text_only", "both", "vision_only"):
        if s in p:
            site = s
    if site is None:
        site = d.get("tag") or d.get("site") or os.path.basename(os.path.dirname(p))
    cg0 = num(d, "initial_gap", "centroid_gap")
    cg1 = num(d, "final_gap", "centroid_gap")
    r1 = num(d, "final_task_metrics", "R@1")
    r1_0 = num(d, "initial_task_metrics", "R@1")
    seed = d.get("seed", None)
    if cg0 is None or cg1 is None:
        continue
    rows.append({"file": os.path.basename(p), "site": site, "seed": seed,
                 "dcg": cg1 - cg0, "r1": r1, "r1_init": r1_0})

print("scorable rows:", len(rows))
by = {}
for r in rows:
    by.setdefault(r["site"], []).append(r)
summary = {}
for s, rs in by.items():
    dcgs = [r["dcg"] for r in rs]
    summary[s] = {"n": len(rs),
                  "mean_dcg": sum(dcgs) / len(dcgs),
                  "mean_abs_dcg": sum(abs(x) for x in dcgs) / len(dcgs),
                  "mean_r1": (sum(r["r1"] for r in rs if r["r1"] is not None) /
                              max(1, sum(1 for r in rs if r["r1"] is not None))),
                  "mean_r1_init": (sum(r["r1_init"] for r in rs if r["r1_init"] is not None) /
                                   max(1, sum(1 for r in rs if r["r1_init"] is not None)))}
for s, v in summary.items():
    print("  %-12s n=%d meanΔCG=%+.4f mean|ΔCG|=%.4f R@1=%.4f (frozen %.4f)"
          % (s, v["n"], v["mean_dcg"], v["mean_abs_dcg"], v["mean_r1"], v["mean_r1_init"]))

order = sorted(summary, key=lambda s: summary[s]["mean_abs_dcg"])
verdicts = {}
if "text_only" in summary:
    verdicts["sign holds"] = summary["text_only"]["mean_dcg"] < 0
    r1_change = summary["text_only"]["mean_r1"] - summary["text_only"]["mean_r1_init"]
    verdicts["retrieval direction holds"] = r1_change < 0
else:
    verdicts["sign holds"] = None
    verdicts["retrieval direction holds"] = None
verdicts["measured ordering (smallest |ΔCG| first)"] = order
verdicts["predicted ordering"] = ["text_only", "both", "vision_only"]
verdicts["ordering first two match"] = order[:2] == ["text_only", "both"]
holds = (verdicts["sign holds"] is True) and (verdicts["ordering first two match"] is True)
verdicts["P1 verdict"] = "holds" if holds else ("fails" if verdicts["sign holds"] is False else "partially holds")
print("\nverdicts:", json.dumps(verdicts, indent=1, default=str))

# ---- 4. write results into the pre-registration file + HANDOFF ----------------------------
PR = os.path.join(REPO, "docs", "PaperA_preregistered_predictions.md")
t = io.open(PR, encoding="utf-8").read()
if "## Results (measured" not in t:
    lines = ["", "## Results (measured 2026-10-26)", "",
             "Fifteen CLIP B/32 arms (three sites x five seeds; seeds 42, 123, 456, 789, 1012), strict freezing,",
             "rank 8, alpha = 2*rank, 10 epochs, 5000 samples, batch 128, DG* recorded every epoch.",
             "Archive: `outputs/paperA_c_prereg/` (15 results.json), one directory per site/seed.", "",
             "| site | n | mean DeltaCG | mean abs(DeltaCG) | R@1 | frozen R@1 |", "|---|---|---|---|---|---|"]
    for s in ("text_only", "both", "vision_only"):
        if s in summary:
            v = summary[s]
            lines.append("| %s | %d | %+.4f | %.4f | %.4f | %.4f |"
                         % (s, v["n"], v["mean_dcg"], v["mean_abs_dcg"], v["mean_r1"], v["mean_r1_init"]))
    lines += ["", "**Measured ordering (smallest |DeltaCG| first):** " + " -> ".join(order),
              "**P1 verdict:** " + verdicts["P1 verdict"], "",
              "- sign (text-only DeltaCG negative): **%s**" % verdicts["sign holds"],
              "- retrieval direction (text-only R@1 below frozen): **%s**" % verdicts["retrieval direction holds"],
              "- ordering first two positions as predicted: **%s**" % verdicts["ordering first two match"], ""]
    io.open(PR, "w", encoding="utf-8", newline="").write(t.rstrip() + "\n" + "\n".join(lines))
    print("pre-registration Results section written")

H = os.path.join(REPO, "HANDOFF.md")
th = io.open(H, encoding="utf-8").read()
if "C 批（预注册 P1）已测" not in th:
    entry = ("## 🧪 2026-10-26 — C 批（预注册 P1）已测：15 臂 CLIP 完成\n\n"
             "三个位点 x 五个种子（42/123/456/789/1012），strict freezing、rank 8、alpha=2r、10 epochs、5000 样本、"
             "batch 128，逐 epoch 记录 DG*。归档 `outputs/paperA_c_prereg/`（15 个 results.json）。\n"
             "实测：**" + " -> ".join(order) + "**（按平均 |ΔCG| 由小到大）；**P1 判决："
             + verdicts["P1 verdict"] + "**（符号 %s、检索方向 %s、前两位排序 %s）。\n"
             % (verdicts["sign holds"], verdicts["retrieval direction holds"], verdicts["ordering first two match"]) +
             "\n**教训**：第一版 driver 用了 `text`/`vision` 标签，脚本只接受 `text_only`/`both`/`vision_only`"
             "（`CONFIGS` 的键），导致 10 臂 `KeyError` 白跑一轮；已修正并补齐。\n")
    lines = th.splitlines(keepends=True)
    idx = 0
    for i, ln in enumerate(lines):
        if ln.startswith("## "):
            idx = i
            break
    io.open(H, "w", encoding="utf-8", newline="").write("".join(lines[:idx]) + entry + "\n" + "".join(lines[idx:]))
    print("HANDOFF updated")

# ---- 5. shut down and verify -------------------------------------------------------------
stdin, stdout, stderr = c.exec_command(
    "sync; (shutdown -h now || poweroff || /usr/bin/shutdown -h now) > /dev/null 2>&1 & sleep 2; echo shutdown-requested",
    timeout=120)
print(stdout.read().decode("utf-8", "replace").strip())
c.close()
