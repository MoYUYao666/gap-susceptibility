# -*- coding: utf-8 -*-
r"""跑 SigLIP 的 rank-4 跨骨干 rank sweep（text_only 与 both 各 5 seeds）。

## 协议

5000 样本 / 10 epochs / batch 64 / **严格冻结** / alpha = rank×2（r4 → α8）。
产物：`outputs/siglip_strict/seed<SEED>/<tag>/results.json`（**每 seed 独立目录**）

## ⚠ 历史缺陷（已修）

先前版本**没传 `--outputs_dir`** → 结果落到默认 `./outputs/siglip`，**5 个 seed 写同一文件、互相覆盖**，
只剩最后一个 seed 的数据（违反「数据来源必须明确」）。且 runner 的判据查 `outputs/siglip_strict/*`，
与落盘位置不符 → 被误判为「静默失败」。

    python tools\_run_siglip_r4.py            # 预演
    python tools\_run_siglip_r4.py --apply    # 执行
"""
from __future__ import annotations

import glob
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
PY = r"D:\Anaconda\envs\pytorch\python.exe"
SEEDS = ["42", "123", "456", "789", "1024"]
TAGS = ["s7_siglip_lora_r4_text_only", "s7_siglip_lora_r4_both"]
COMMON = ["--strict-freeze", "--max_samples", "5000", "--epochs", "10",
          "--batch_size", "64", "--skip_full_ft", "--data_dir", "."]


def dest(tag: str, seed: str) -> Path:
    return REPO / "outputs" / "siglip_strict" / ("seed" + seed) / tag / "results.json"


def main() -> int:
    apply = "--apply" in sys.argv
    todo = [(t, s) for t in TAGS for s in SEEDS if not dest(t, s).exists()]
    print("SigLIP r4：目标 %d 个 run，待跑 %d" % (len(TAGS) * len(SEEDS), len(todo)))
    for t, s in todo:
        print("  %-30s seed=%-5s → %s" % (t, s, dest(t, s).parent.relative_to(REPO)))
    if not apply:
        print("\n（预演，加 --apply 执行）")
        return 0

    MAX_CONSEC = 2          # 连续失败这么多次就停（GPU 故障时不硬撞）
    consec = 0
    for t, s in todo:
        outdir = "outputs/siglip_strict/seed%s" % s
        cmd = [PY, "experiments/siglip_experiments.py", *COMMON,
               "--only", t, "--seed", s, "--outputs_dir", outdir]
        r = subprocess.run(cmd, cwd=REPO, capture_output=True, text=True,
                           encoding="utf-8", errors="replace")
        keep = [l for l in (r.stdout or "").splitlines()
                if any(k in l for k in ("严格冻结", "time=", "✅", "❌", "done"))]
        for l in keep[-3:]:
            print("  " + l.strip()[:140], flush=True)
        if r.returncode != 0:
            print("  ⚠ %s seed=%s 退出码 %d" % (t, s, r.returncode), flush=True)
            for l in (r.stderr or "").strip().splitlines()[-3:]:
                print("    stderr: " + l[:130], flush=True)
        # 落盘位置校验：必须在期望路径
        ok = dest(t, s).exists()
        if not ok:
            print("  ❌ 结果未落在期望路径：%s" % dest(t, s).relative_to(REPO), flush=True)
        consec = 0 if ok else consec + 1
        if consec >= MAX_CONSEC:
            print("\n  🛑 连续 %d 次失败 —— GPU 可能处于故障态，**停止本批**。" % consec, flush=True)
            print("     请检查：nvidia-smi（报错/掉卡？）｜ 是否有其他训练在并发占用？", flush=True)
            print("     恢复后用同一命令续跑（幂等）：python tools/_run_siglip_r4.py --apply", flush=True)
            break

    done = len(glob.glob(str(REPO / "outputs/siglip_strict/*/s7_siglip_lora_r4_*/results.json")))
    print("\n完成 %d/%d" % (done, len(TAGS) * len(SEEDS)))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
