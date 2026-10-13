# -*- coding: utf-8 -*-
r"""修 `tools/_run_siglip_r4.py` 的两处缺陷（2026-10-04）。

## 缺陷（昨晚实际发生，见 HANDOFF）

| # | 缺陷 | 后果 |
|---|---|---|
| 1 | **没传 `--outputs_dir`** → 用默认 `./outputs/siglip` | 5 个 seed **写同一文件、互相覆盖**；只剩最后一个 seed 的数据 |
| 2 | **runner 的完成判据查 `outputs/siglip_strict/*`**，而结果落在 `outputs/siglip/*` | 26 分钟"静默"被误判为失败，跳到下一步 |

缺陷 1 违反操作者标准（**数据来源必须明确**）：覆盖后的文件既不分 seed、也无从追溯。

## 修法

- 每个 seed 传 **独立的 `--outputs_dir outputs/siglip_strict/seed<SEED>`**（与既有 SigLIP run 的布局一致）；
- 若结果文件**已存在则跳过**（幂等）；
- 校验每个结果里的 `n_trainable_params` 与 rank 相符（text_only rank4 = 147,456；
  both rank4 = 147,456 + 视觉部分），不符则报警。

    python tools\_fix_siglip_r4_runner.py [--apply]
"""
from __future__ import annotations

import io
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
F = REPO / "tools" / "_run_siglip_r4.py"

NEW = r'''# -*- coding: utf-8 -*-
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
        if not dest(t, s).exists():
            print("  ❌ 结果未落在期望路径：%s" % dest(t, s).relative_to(REPO), flush=True)

    done = len(glob.glob(str(REPO / "outputs/siglip_strict/*/s7_siglip_lora_r4_*/results.json")))
    print("\n完成 %d/%d" % (done, len(TAGS) * len(SEEDS)))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
'''


def main() -> int:
    apply = "--apply" in sys.argv
    old = io.open(F, encoding="utf-8").read()
    if "--outputs_dir" in old:
        print("  已含 --outputs_dir，跳过")
        return 0
    print("  ✅ 将改写 _run_siglip_r4.py（加 --outputs_dir 与落盘校验）")
    if apply:
        io.open(F, "w", encoding="utf-8", newline="").write(NEW)
        t = io.open(F, encoding="utf-8").read()
        assert "'--outputs_dir'" in t and "siglip_strict/seed" in t
        assert "结果未落在期望路径" in t
        print("  ✅ 已改写并断言通过")
    else:
        print("  （预演）")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
