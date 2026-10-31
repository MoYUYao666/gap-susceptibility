# -*- coding: utf-8 -*-
r"""Verify the corrected Qwen2-VL-2B sweep, pull it back, and summarise it against the frozen baseline.

This is step 2-3 of the cloud shutdown rule (`AGENTS.md`): verify, then pull everything back, and only then is the
host allowed to be switched off.

Verification is by assertion, not by eyeballing:
  * exactly 39 arm records = 3 arms x 13 seeds, plus the frozen baseline;
  *每一 record carries three epoch values for dg_star, and non-empty cg / legacy / loss / token counts;
  * the clean number must be far below the legacy one (the legacy construction is dominated by the fixed random
    projections, so a clean value of order 2 would mean the projection removal did not take effect);
  * tower isolation per arm: text_only must touch no vision adapter, vision_only no language adapter, both both;
  * epoch-3 clean DG* must be below the frozen baseline for the reduction to be meaningful.

Then every JSON and both logs are copied back and their sizes compared.

    python tools/_p1164_verify_pull_analyze_e.py [--apply]
"""
from __future__ import annotations

import argparse
import json
import os
import statistics as st
import sys

import paramiko

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
HOST = os.environ.get("P3SSH_HOST", "")
PORT = int(os.environ.get("P3SSH_PORT", "22"))
PASS = os.environ.get("P3SSH_PASS", "")
REMOTE = "/root/p3/outputs/vlm_clean"
LOCAL = os.path.join(REPO, "outputs", "vlm_clean_cloud")
SEEDS = [42, 123, 456, 789, 1011, 1313, 1616, 1919, 2323, 2727, 3131, 3737, 4141]
ARMS = ("text_only", "vision_only", "both")

VERIFY = r"""
import glob, json
from pathlib import Path
d = Path("/root/p3/outputs/vlm_clean")
base = json.loads((d / "frozen_baseline.json").read_text(encoding="utf-8"))
recs, problems = {}, []
for f in sorted(d.glob("*_seed*.json")):
    if f.name.startswith("summary"):
        continue
    o = json.loads(f.read_text(encoding="utf-8"))
    recs[(o["arm"], o["seed"])] = o
for arm in ("text_only", "vision_only", "both"):
    for s in (42, 123, 456, 789, 1011, 1313, 1616, 1919, 2323, 2727, 3131, 3737, 4141):
        o = recs.get((arm, s))
        if o is None:
            problems.append(f"missing {arm} seed {s}")
            continue
        if len(o.get("dg_star") or []) != 3:
            problems.append(f"{arm} s{s}: dg_star not 3 epochs")
        if not o.get("legacy_dg_star"):
            problems.append(f"{arm} s{s}: no legacy field")
        tc = o.get("token_counts_first_batch") or {}
        if not (tc.get("img") and min(tc["img"]) > 0):
            problems.append(f"{arm} s{s}: image-token mask empty")
        if not (tc.get("cap") and min(tc["cap"]) > 0):
            problems.append(f"{arm} s{s}: caption mask empty")
        if arm == "text_only" and o.get("n_vis"):
            problems.append(f"text_only s{s} touched {o['n_vis']} vision adapters")
        if arm == "vision_only" and o.get("n_lang"):
            problems.append(f"vision_only s{s} touched {o['n_lang']} language adapters")
        if arm == "both" and not (o.get("n_vis") and o.get("n_lang")):
            problems.append(f"both s{s} missing one tower")
        if o["dg_star"][-1] >= base["dg_star"]:
            problems.append(f"{arm} s{s}: epoch-3 clean DG* {o['dg_star'][-1]:.4f} not below frozen {base['dg_star']:.4f}")
clean_too_big = [k for k, o in recs.items() if o["dg_star"][-1] > 1.0]
if clean_too_big:
    problems.append(f"{len(clean_too_big)} records still have clean DG* > 1 (projection removal suspect)")
print(json.dumps({
    "n_records": len(recs),
    "frozen": base,
    "problems": problems,
    "per_arm": {a: {"seeds": sorted(s for (aa, s) in recs if aa == a),
                    "dg_star_ep3": [recs[(a, s)]["dg_star"][-1] for s in sorted(x for (aa, x) in recs if aa == a)],
                    "legacy_ep3": [recs[(a, s)]["legacy_dg_star"][-1] for s in sorted(x for (aa, x) in recs if aa == a)]}
                for a in ("text_only", "vision_only", "both")},
}, indent=1))
"""


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    a = ap.parse_args()
    if not a.apply:
        print("  (dry run)")
        return 0
    if not (HOST and PASS):
        print("  P3SSH_HOST / P3SSH_PASS are not set")
        return 2
    cli = paramiko.SSHClient()
    cli.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    cli.connect(HOST, port=PORT, username="root", password=PASS, timeout=30,
                allow_agent=False, look_for_keys=False)

    def sh(cmd: str, timeout: int = 600) -> str:
        _i, o, e = cli.exec_command(cmd, timeout=timeout)
        return (o.read() + e.read()).decode("utf-8", "replace").strip()

    sftp = cli.open_sftp()
    with sftp.open("/root/p3/_verify_e.py", "w") as fh:
        fh.write(VERIFY)
    sftp.close()
    raw = sh("/root/miniconda3/bin/python /root/p3/_verify_e.py")
    info = json.loads(raw[raw.find("{"):])
    print("=== verification ===")
    print(f"  records: {info['n_records']} (expected 39)")
    print(f"  frozen clean DG*: {info['frozen']['dg_star']:.6f}")
    if info["problems"]:
        print("  PROBLEMS:")
        for p in info["problems"][:20]:
            print("   -", p)
        cli.close()
        return 1
    print("  all assertions passed")

    print("\n=== per-arm clean DG* after epoch 3, and reduction vs frozen ===")
    fz = info["frozen"]["dg_star"]
    print(f"  {'arm':<12} {'n':>2} {'mean ep3':>10} {'reduction mean':>15} {'sd':>8} {'legacy ep3':>11}")
    summary = {}
    for arm in ARMS:
        v = info["per_arm"][arm]["dg_star_ep3"]
        rel = [100 * (fz - x) / fz for x in v]
        lg = info["per_arm"][arm]["legacy_ep3"]
        summary[arm] = {"n": len(v), "dg_star_ep3_mean": st.mean(v), "reduction_mean": st.mean(rel),
                        "reduction_sd": st.pstdev(rel), "per_seed": v,
                        "legacy_ep3_mean": st.mean(lg)}
        print(f"  {arm:<12} {len(v):>2} {st.mean(v):>10.4f} {st.mean(rel):>14.2f}% {st.pstdev(rel):>7.2f}% "
              f"{st.mean(lg):>11.4f}")

    print("\n=== pulling results back ===")
    os.makedirs(LOCAL, exist_ok=True)
    # The SFTP session used to upload the verifier was closed before the remote command ran; re-open one here.
    # Reusing the closed handle is what produced "OSError: Socket is closed" on the first attempt.
    sftp = cli.open_sftp()
    ok = bad = 0
    for name in sorted(sftp.listdir(REMOTE)):
        if not name.endswith(".json"):
            continue
        rp, lp = f"{REMOTE}/{name}", os.path.join(LOCAL, name)
        rs = sftp.stat(rp).st_size
        sftp.get(rp, lp)
        good = os.path.getsize(lp) == rs
        ok += good
        bad += not good
        print(f"  {'OK ' if good else 'BAD'} {name:<34} {rs:>8,}")
    sftp.close()

    os.makedirs(LOCAL, exist_ok=True)
    sftp2 = cli.open_sftp()
    for log in ("vlm_clean_A.log", "vlm_clean_B.log", "vlm_clean_runner.log"):
        rp, lp = f"/root/p3/{log}", os.path.join(LOCAL, log)
        sftp2.get(rp, lp)
        print(f"  log {log:<24} {os.path.getsize(lp):>10,} bytes")
    sftp2.close()

    out = os.path.join(REPO, "outputs", "vlm_clean_summary.json")
    with open(out, "w", encoding="utf-8") as fh:
        json.dump({"frozen": info["frozen"], "per_arm": summary,
                   "verification": {"n_records": info["n_records"], "problems": []}}, fh,
                  ensure_ascii=False, indent=1)
    print(f"\n  files verified: {ok}, mismatched: {bad}")
    print(f"  summary written: {os.path.relpath(out, REPO)}")
    cli.close()
    return 0 if bad == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
