# -*- coding: utf-8 -*-
r"""修匹配：`display` 是 "姓, 名" 格式，且需去重音（`Yüksekgönül`）（2026-10-10）。

## 我上一版的错

我断言 "找不到 'Yi'"，但数据是 `{'family': 'Yi', 'given': 'Lingjie', 'display': 'Yi, Lingjie'}`
—— **`family` 本来就是对的**，是我的匹配逻辑写得过严（没处理 "姓, 名" 这种 display）。

**修法**：
1. 匹配时同时看 `family`、`given`、以及 `display` 的**首段**（逗号前）；
2. **去重音/变音符号**再比（`Yüksekgönül` ↔ `Yuksekgonul`）。

    python tools\_p121_fix_match.py --apply
"""
from __future__ import annotations

import argparse
import io
import json
import sys
import unicodedata
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
FIXED = REPO / "outputs" / "analysis" / "a1_apa_fixed.json"

MANUAL = {
    "yi2025": "Yi", "mistretta2025": "Mistretta", "fang2022data": "Fang",
    "yuksekgonul2023when": "Yuksekgonul", "wang2020alignment": "Wang",
}


def deacc(s: str) -> str:
    return "".join(c for c in unicodedata.normalize("NFKD", s or "")
                   if not unicodedata.combining(c)).lower().strip()


def candidates(x: dict) -> set:
    out = {deacc(x.get("family", "")), deacc(x.get("given", ""))}
    disp = x.get("display", "")
    if "," in disp:
        out.add(deacc(disp.split(",")[0]))
    else:
        parts = disp.split()
        if parts:
            out.add(deacc(parts[0]))
            out.add(deacc(parts[-1]))
    out.discard("")
    return out


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    a = ap.parse_args()

    rows = json.loads(io.open(FIXED, encoding="utf-8").read())
    rmap = {r["key"]: r for r in rows}
    print("=== 应用修正 ===")
    for k, fam in MANUAL.items():
        r = rmap.get(k)
        if not r:
            continue
        au = r.get("authors") or []
        tgt = deacc(fam)
        hit = next((i for i, x in enumerate(au) if tgt in candidates(x)), None)
        if hit is None:
            print(f"  ❌ [{k}] 仍找不到 '{fam}'："
                  f"{[(x.get('family'), x.get('display')) for x in au]}")
            continue
        x = au[hit]
        if deacc(x.get("family", "")) != tgt:
            x["family"], x["given"] = fam, x.get("family", "")
        if hit != 0:
            au.insert(0, au.pop(hit))
        r["name_status"] = "OK_MANUAL"
        r["authors"] = au
        print(f"  ✅ [{k}] 首位 → family='{au[0]['family']}' given='{au[0]['given']}'")

    ok = sum(1 for r in rows if str(r.get("name_status", "")).startswith("OK"))
    print(f"\n=== {ok}/{len(rows)} 条作者已核 ===")
    bad = [r["key"] for r in rows if not str(r.get("name_status", "")).startswith("OK")]
    print(f"  仍未核: {len(bad)} {bad[:8]}")

    if a.apply:
        io.open(FIXED, "w", encoding="utf-8", newline="").write(
            json.dumps(rows, ensure_ascii=False, indent=1))
        print(f"  ✅ 已写 {FIXED.relative_to(REPO)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
