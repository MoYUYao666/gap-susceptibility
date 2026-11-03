# -*- coding: utf-8 -*-
r"""追查：论文归档里有没有「LoRA 静默未注入」的 run（2026-10-12）。

## 触发原因

`task-8` 的成员发现：`strict_freeze_control.py` 的默认
`target_modules=["q_proj","v_proj"]` 在 **DINOv2**（层名是 `query`/`value`/`key`）上
**一个 LoRA 层都注不进去**，静默变成假实验（196,608 参数全来自文本侧）。

**同一个坑可能影响论文自己的 run**：若某个 backbone 的层名与默认值不匹配，
那次实验的"vision arm"其实**什么都没训**。

## 判据（不靠推断，靠归档字段）

一次真正的 LoRA 注入，其可训参数必须 ≈ LoRA 参数量。已知真值：
- LoRA-both（q,v；12+12 层）= **491,520**
- LoRA-text（q_proj,v_proj；12 层）= **196,608**

**任何"LoRA" arm 的可训参数若等于纯文本侧值（196,608 / 147,456 等）或为 0，
即为未注入嫌疑。**

    python tools\_p309_audit_lora_injection.py [--apply]
"""
from __future__ import annotations

import argparse
import glob
import io
import json
import re
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
OUT = REPO / "outputs" / "analysis" / "lora_injection_audit.json"

# 已知的真 LoRA 可训参数量（来自论文 strict-freeze 数字与 task-6 的 peft_proof）
KNOWN = {
    491520: "LoRA-both (q,v; 12 vision + 12 text layers)",
    196608: "LoRA-text-only (q_proj,v_proj; 12 text layers)",
    294912: "LoRA-vision-only (query,value; 12 vision layers)",
}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    a = ap.parse_args()

    print("=" * 100)
    print("① 找出所有记录 n_trainable_params / num_trainable 的归档")
    print("=" * 100)
    recs = []
    pat = re.compile(r'"(?:n_trainable_params|num_trainable_params|trainable_params|'
                     r'n_trainable)"\s*:\s*(\d+)')
    for f in glob.glob(str(REPO / "outputs" / "**" / "*.json"), recursive=True):
        if "lit_pool" in f or "claim_ledger" in f:
            continue
        t = io.open(f, encoding="utf-8", errors="replace").read()
        vals = [int(m.group(1)) for m in pat.finditer(t)]
        if vals:
            recs.append((str(Path(f).relative_to(REPO)), sorted(set(vals))))
    print(f"  共 {len(recs)} 个文件含可训参数量字段")

    print()
    print("=" * 100)
    print("② 按数值归类（找「疑似未注入」）")
    print("=" * 100)
    from collections import Counter
    cnt = Counter()
    for rel, vals in recs:
        for v in vals:
            cnt[v] += 1
    for v, c in sorted(cnt.items()):
        tag = KNOWN.get(v)
        flag = "✅" if tag else ("⚠️ " if v < 500000 else "  ")
        print(f"  {flag} {v:>12,}  ×{c:<4} {tag or ''}")

    print()
    print("=" * 100)
    print("③ 疑似未注入的 run（可训参数 < 200,000 且非已知量）")
    print("=" * 100)
    susp = []
    for rel, vals in recs:
        for v in vals:
            if 0 < v < 200000 and v not in KNOWN:
                susp.append({"file": rel, "n_trainable": v})
    if susp:
        for s in susp[:20]:
            print(f"  ⚠️  {s['file']}  n_trainable={s['n_trainable']:,}")
    else:
        print("  ✅ 未发现")
    print(f"  → 共 {len(susp)} 个疑似")
    if a.apply:
        OUT.parent.mkdir(parents=True, exist_ok=True)
        io.open(OUT, "w", encoding="utf-8", newline="").write(json.dumps(
            {"files_with_trainable_counts": {r: v for r, v in recs},
             "value_histogram": {str(k): v for k, v in sorted(cnt.items())},
             "known_lora_counts": {str(k): v for k, v in KNOWN.items()},
             "suspicious": susp}, ensure_ascii=False, indent=1))
        print(f"\n  ✅ 已写 {OUT.relative_to(REPO)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
