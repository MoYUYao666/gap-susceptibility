# -*- coding: utf-8 -*-
r"""**决定性对比 3**：云端 `results.json` 的**全部字段** vs 本地归档（2026-10-09）。

## 已逐项排除

| 假设 | 证据 |
|---|---|
| 模型权重不同 | ❌ `image_embeds_hash` 完全一致 |
| 预处理不同 | ❌ `cos_ii`/`dist_it`/`cg` 一致到 7 位 |
| 脚本不同 | ❌ sha256 一致 |
| **数据不同** | ❌ **前 1000 图 md5 一致**、CSV md5 一致 |
| `n_trainable` 不同 | ❌ 一致 |

**剩：gap 的计算/存储路径不同。** 本脚本对齐两边 **`results.json` 全字段**。

    python tools\_p69_field_diff.py [--apply]
"""
from __future__ import annotations

import io
import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "tools"))


def main() -> int:
    apply = "--apply" in sys.argv

    from _cloud_ssh import client, run

    c = client()
    try:
        # 拉云端的 results.json 内容
        out, _ = run(c, "cat /root/autodl-tmp/work/outputs/strict_freeze_b32_r4/both/"
                        "seed123/results.json", timeout=120)
        cloud = None
        try:
            s = out[out.find("{"):out.rfind("}") + 1]
            cloud = json.loads(s)
        except Exception as e:
            print("  云端 JSON 解析失败:", str(e)[:120])

        # 也拉 initial/final gap 的完整结构
        out2, _ = run(c, "cat /root/autodl-tmp/work/outputs/strict_freeze_b32_r4/"
                         "both/seed123/results.json | python3 -c "
                         "\"import json,sys;d=json.load(sys.stdin);"
                         "print(json.dumps({'initial':d['initial_gap'],"
                         "'final':d['final_gap']},indent=1))\"", timeout=120)
    finally:
        c.close()

    local = json.loads(io.open(
        REPO / "outputs/strict_freeze_b32_r4/both/seed123/results.json",
        encoding="utf-8").read())

    if cloud:
        print("=== 字段对齐（本地 seed123 vs 云端 seed123，both）===")
        keys = sorted(set(local) | set(cloud))
        print(f"  {'字段':<34}{'本地':>26}{'云端':>26}")
        for k in keys:
            lv, cv = local.get(k), cloud.get(k)
            ls = json.dumps(lv, ensure_ascii=False)[:24] if lv is not None else "—"
            cs = json.dumps(cv, ensure_ascii=False)[:24] if cv is not None else "—"
            mark = "" if ls == cs else "  ⚠️"
            print(f"  {k:<34}{ls:>26}{cs:>26}{mark}")

        print("\n=== gap 结构逐键对比 ===")
        for phase in ("initial_gap", "final_gap"):
            lg, cg = local.get(phase, {}), cloud.get(phase, {})
            print(f"  --- {phase}")
            for k in sorted(set(lg) | set(cg)):
                lv, cv = lg.get(k), cg.get(k)
                if isinstance(lv, (int, float)) and isinstance(cv, (int, float)):
                    diff = abs(lv - cv)
                    ratio = (cv / lv) if lv else float("nan")
                    print(f"      {k:<26} 本地={lv:>12.6f} 云端={cv:>12.6f} "
                          f"比值={ratio:>7.4f}{'  ⚠️' if diff > 1e-6 else ''}")
                else:
                    print(f"      {k:<26} 本地={lv} 云端={cv}")

    if apply and cloud:
        out_p = REPO / "outputs" / "analysis" / "field_diff.json"
        out_p.parent.mkdir(parents=True, exist_ok=True)
        io.open(out_p, "w", encoding="utf-8", newline="").write(json.dumps({
            "local": local, "cloud": cloud,
            "note": "same seed123/both/batch128/epochs10/max5000, identical model+data+script",
        }, ensure_ascii=False, indent=1))
        print(f"\n  ✅ 已写 {out_p.relative_to(REPO)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
