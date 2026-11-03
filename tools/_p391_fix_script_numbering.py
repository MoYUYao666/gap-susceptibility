# -*- coding: utf-8 -*-
r"""消解脚本编号重号：把**我的** 11 个文件重编号到 380+（2026-10-12）。

## 问题（审计成员指出）

隔离并行开发导致 `_p360`–`_p370` 段与队友的编号块相撞 → **11 个编号各有两个不同脚本**
→ 违反项目铁律"每个数字必须能**指名唯一**的产出脚本"。

| 编号 | 我的 | 队友的（保留） |
|---|---|---|
| `_p360` | `eval_paths` | `gallery_noise` |
| `_p361` | `record_gallery_noise` | `protocol_facts` |
| `_p362` | `verify_bioclip_initcg` | `clip_api_check` |
| `_p363` | `gallery_noise_cg` | `logit_scale_provenance` |
| `_p364` | `record_gallery_verdict` | `pristine_clip_provenance` |
| `_p365` | `fix_caption_and_limitation` | `lora_update_norms` |
| `_p366` | `verify_logit_scale` | `gallery_noise_fix` |
| `_p367` | `logit_scale_in_archive` | `r1_discrepancies` |
| `_p368` | `record_logit_scale` | `checkpoint_epochs` |
| `_p369` | `update_noise_numbers` | `reproduce_clip_arm_r1` |
| `_p370` | `record_a1_submitted` | `vision_only_checkpoint_identity` |

**处置**：把我的 11 个改名到 **`_p380`–`_p390`**，并**同步改脚本内与产出 JSON 里的 `script` 字段**
（否则 JSON 会指向一个已不存在的脚本名 → 同样是溯源断裂）。

    python tools\_p390_fix_script_numbering.py [--apply]
"""
from __future__ import annotations

import argparse
import io
import json
import os
import re
import shutil
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
TOOLS = REPO / "tools"

# 我的文件 → 新编号
RENAME = {
    "_p360_eval_paths.py": "_p380_eval_paths.py",
    "_p361_record_gallery_noise.py": "_p381_record_gallery_noise.py",
    "_p362_verify_bioclip_initcg.py": "_p382_verify_bioclip_initcg.py",
    "_p363_gallery_noise_cg.py": "_p383_gallery_noise_cg.py",
    "_p364_record_gallery_verdict.py": "_p384_record_gallery_verdict.py",
    "_p365_fix_caption_and_limitation.py": "_p385_fix_caption_and_limitation.py",
    "_p366_verify_logit_scale.py": "_p386_verify_logit_scale.py",
    "_p367_logit_scale_in_archive.py": "_p387_logit_scale_in_archive.py",
    "_p368_record_logit_scale.py": "_p388_record_logit_scale.py",
    "_p369_update_noise_numbers.py": "_p389_update_noise_numbers.py",
    "_p370_record_a1_submitted.py": "_p390_record_a1_submitted.py",
}

# 产出 JSON 里出现的旧脚本名 → 新名（用于同步 JSON 的 script 字段与溯源说明）
STR_MAP = {old.replace(".py", ""): new.replace(".py", "")
           for old, new in RENAME.items()}
STR_MAP.update({old: new for old, new in RENAME.items()})


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    a = ap.parse_args()

    print("=" * 96)
    print("① 重命名 tools/ 下我的 11 个脚本")
    print("=" * 96)
    done = []
    for old, new in RENAME.items():
        op, np_ = TOOLS / old, TOOLS / new
        if not op.exists():
            print(f"  ⚠️ 缺 {old}")
            continue
        if np_.exists():
            print(f"  ⚠️ 目标已存在 {new}，跳过")
            continue
        if a.apply:
            os.rename(op, np_)
        done.append((old, new))
        print(f"  {'✅' if a.apply else '  '} {old:<44} → {new}")

    if not a.apply:
        print("\n  （预演）")
        return 0

    print()
    print("=" * 96)
    print("② 同步脚本内与产出 JSON 里的旧脚本名")
    print("=" * 96)
    n_py = n_json = 0
    # 脚本内部自指
    for old, new in RENAME.items():
        p = TOOLS / new
        if not p.exists():
            continue
        t = io.open(p, encoding="utf-8", errors="replace").read()
        t2 = t
        for o, nn in STR_MAP.items():
            t2 = t2.replace(o, nn)
        if t2 != t:
            io.open(p, "w", encoding="utf-8", newline="").write(t2)
            n_py += 1
    # 产出 JSON
    for f in (REPO / "outputs").rglob("*.json"):
        try:
            t = io.open(f, encoding="utf-8", errors="replace").read()
        except Exception:
            continue
        t2 = t
        for o, nn in STR_MAP.items():
            t2 = t2.replace(o, nn)
        if t2 != t:
            io.open(f, "w", encoding="utf-8", newline="").write(t2)
            n_json += 1
    print(f"  脚本内改 {n_py} 个 ｜ JSON 改 {n_json} 个")

    print()
    print("=" * 96)
    print("③ 复核重号是否已消解")
    print("=" * 96)
    from collections import defaultdict
    g = defaultdict(list)
    for f in sorted(TOOLS.glob("_p*.py")):
        m = re.match(r"(_p\d+)", f.name)
        if m:
            g[m.group(1)].append(f.name)
    conf = {k: v for k, v in g.items() if len(v) > 1}
    for k in sorted(conf, key=lambda x: int(x[2:])):
        print(f"  ⚠️ {k}: {sorted(conf[k])}")
    print(f"  → 剩余重号编号 {len(conf)} 个（队友的 `_p293*` 系列属同一实验的派生脚本，一并保留）")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
