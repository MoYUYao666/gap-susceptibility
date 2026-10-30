# -*- coding: utf-8 -*-
r"""核查：待译的 JSON/TXT 里的中文是否被程序读取（翻译是否会破坏一致性）（2026-10-14）。

## 风险

`outputs/*.json` 里的中文若是**下游脚本用到的键值或字符串**，翻译会：
- 让 `.json` 与引用它的 `.py` 不一致
- 或改变数据的语义

**⇒ 分类**：① 仅作人类可读的注释/说明 ⇒ **可译**；② 被代码读取 ⇒ **不译**（或同步改代码）。

    python tools\_p594_check_json_cjk_safety.py
"""
from __future__ import annotations

import argparse
import io
import json
import re
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
PC = REPO / "publish_clean"
MAN = REPO / "outputs" / "analysis" / "translate_manifest.json"
CJK = re.compile(r"[\u4e00-\u9fff]")


def walk_strings(obj, path="$"):
    """产出 (json_path, value)。"""
    if isinstance(obj, dict):
        for k, v in obj.items():
            yield (f"{path}.{k}", k)
            yield from walk_strings(v, f"{path}.{k}")
    elif isinstance(obj, list):
        for i, v in enumerate(obj):
            yield from walk_strings(v, f"{path}[{i}]")
    elif isinstance(obj, str):
        yield (path, obj)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    a = ap.parse_args()
    man = json.loads(io.open(MAN, encoding="utf-8").read())
    targets = [i for b in man["batches"] for i in b
               if i["ext"] in (".json", ".txt")]
    print(f"  待查 {len(targets)} 个（json/txt）")
    print()
    verdict = {}
    for it in targets:
        p = PC / it["path"]
        t = io.open(p, encoding="utf-8", errors="replace").read()
        # ① 该文件名是否被任何 .py 引用
        base = p.name
        refs = []
        r = subprocess.run(["git", "grep", "-l", "-F", base], cwd=str(PC), capture_output=True)
        if r.returncode == 0:
            refs = [x for x in r.stdout.decode("utf-8", errors="replace").splitlines() if x.strip()]
        refs = [x for x in refs if x != it["path"]]
        # ② 中文是否出现在 JSON 的**键**上
        key_cjk = 0
        val_cjk = 0
        if it["ext"] == ".json":
            try:
                obj = json.loads(t)
                for jp, s in walk_strings(obj):
                    if isinstance(s, str) and CJK.search(s):
                        # 判断该串是否是 key（路径最后一段不含 [ ）
                        if jp.endswith("." + s):
                            key_cjk += len(CJK.findall(s))
                        else:
                            val_cjk += len(CJK.findall(s))
            except Exception as e:
                print(f"  ⚠️ {it['path']}: JSON 解析失败 {e}")
        print(f"  ── {it['path']}（{it['cjk']} 中文字符）")
        print(f"       被引用：{len(refs)} 处 {refs[:3]}")
        if it["ext"] == ".json":
            print(f"       中文在**键**上：{key_cjk} ｜ 在**值**上：{val_cjk}")
        safe = (not refs) or (key_cjk == 0)
        verdict[it["path"]] = {"refs": refs[:5], "key_cjk": key_cjk, "val_cjk": val_cjk,
                               "safe_to_translate": safe}
        print(f"       ⇒ {'✅ 可译' if safe else '🔴 有代码引用且中文在键上 ⇒ 不译或需同步改代码'}")

    print()
    n_safe = sum(1 for v in verdict.values() if v["safe_to_translate"])
    print(f"  **可译 {n_safe} / {len(targets)}；需谨慎 {len(targets) - n_safe}**")
    if a.apply:
        out = REPO / "outputs" / "analysis" / "translate_json_safety.json"
        io.open(out, "w", encoding="utf-8", newline="").write(
            json.dumps(verdict, ensure_ascii=False, indent=1))
        print(f"  ✅ 已写 {out.relative_to(REPO)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
