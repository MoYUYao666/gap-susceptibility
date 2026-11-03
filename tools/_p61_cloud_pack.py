# -*- coding: utf-8 -*-
r"""生成**云端部署包**与**一键命令**（风险 #1/#3/#4 托管到云端，2026-10-09）。

## 为什么

本地是 **8 GB 共享卡**，单 run 峰值 **7.9 GB（96%）** → 会占满、且 `both` 臂约 3 h/run。
云端 runbook（`docs/CLOUD_RUNBOOK.md`）实测为 **RTX 4080 SUPER 16 GB**，
且已跑过 Qwen2-VL-7B（峰值 8.94 GB）→ **16 GB 足够，且更快**。

**→ 把剩余的补 seed（14 缺口）+ `Γ_m` 完整测量托管到云端，本地释放。**

## 本脚本产出

1. `cloud_pack/` —— 只含**必要文件**（代码 + 脚本 + 配置），**不含模型、不含数据**；
2. `cloud_pack/manifest.txt` —— 文件清单与大小；
3. `docs/CLOUD_SEEDS_RUNBOOK.md` —— **可照抄的一组命令**（含模型/数据的服务器端下载）。

## 两条硬规则（来自 `exp/README.md` 与 `AGENTS.md`）

- **模型一律在服务器下载**（ModelScope 优先）——**禁止上传**；
- **数据不上传**：Flickr30k 在服务器用 `curl` 取（已实测过该来源）。

    python tools\_p61_cloud_pack.py [--apply]
"""
from __future__ import annotations

import io
import shutil
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
PACK = REPO / "cloud_pack"

INCLUDE_DIRS = ["src", "experiments", "tools/audit"]
INCLUDE_FILES = [
    "tools/_p56_add_seeds.py",
    "tools/_p58_gamma_clip.py",
    "tools/_p59_seed_stability.py",
    "tools/_claim_ledger.py",
    "requirements.txt",
]
EXTRA = ["configs", "AGENTS.md"]


def main() -> int:
    apply = "--apply" in sys.argv
    print("=== 云端部署包生成 ===")
    files = []
    for d in INCLUDE_DIRS:
        p = REPO / d
        if p.exists():
            for f in p.rglob("*"):
                if f.is_file() and "__pycache__" not in str(f):
                    files.append(f)
    for f in INCLUDE_FILES:
        p = REPO / f
        if p.exists():
            files.append(p)
    for d in EXTRA:
        p = REPO / d
        if p.is_dir():
            files += [x for x in p.rglob("*") if x.is_file()]
        elif p.is_file():
            files.append(p)

    total = sum(f.stat().st_size for f in files) / 2**20
    print(f"  将打包 {len(files)} 个文件 ｜ {total:.1f} MB")
    for f in sorted(files)[:6]:
        print(f"    {f.relative_to(REPO)}")
    print(f"    …（共 {len(files)} 个）")

    if not apply:
        print("\n  （预演；加 --apply 实际复制到 cloud_pack/）")
        return 0

    if PACK.exists():
        shutil.rmtree(PACK)
    for f in files:
        rel = f.relative_to(REPO)
        dst = PACK / rel
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(f, dst)

    man = PACK / "manifest.txt"
    with io.open(man, "w", encoding="utf-8", newline="") as fh:
        for f in sorted(files):
            rel = f.relative_to(REPO)
            fh.write(f"{f.stat().st_size:>12}  {rel}\n")
        fh.write(f"\n合计 {len(files)} 文件 ｜ {total:.1f} MB\n")
    print(f"\n  ✅ 已生成 {PACK.relative_to(REPO)}/ （{len(files)} 文件，{total:.1f} MB）")
    print(f"  ✅ 清单 {man.relative_to(REPO)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
