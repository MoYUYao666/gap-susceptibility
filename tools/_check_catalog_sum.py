# -*- coding: utf-8 -*-
r"""核算目录表：**各类求和 vs 表中 Total**（2026-10-05）。

## 已发现的矛盾

| 项 | 值 |
|---|---|
| 原表 13 类（改动前，`git show 16bb0f5`） | 30,7,8,7,3,16,20,4,5,4,2,3,8 |
| 原表 **Total** | **117** |
| 新增第 XIV 类（严格冻结） | 95 |
| 现表 14 类求和 | 见下 |
| 现表 **Total** | **374** |

**先算准数字，再判断哪个是对的。**

    python tools\_check_catalog_sum.py
"""
from __future__ import annotations

import io
import re
import subprocess
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
SUP = REPO / "paper合" / "sections" / "supplement.tex"

CATS = ["LoRA Core (Flickr30k)", "Adapter (Flickr30k)", "COCO Cross-Dataset",
        "BLIP-1 Cross-Architecture", "ViT-L Cross-Model", "Route C/D/E Enhanced Strategies",
        "5-Seed Statistical Validation", "ImageNet Zero-Shot", "ViT-B Layered Fine-Tuning",
        "ViT-L Layered Fine-Tuning", "Adapter Layered Fine-Tuning", "Mechanism Probes",
        "Zero-Shot Generalization and SigLIP", "Strict-Freezing Controls"]


def parse(text: str) -> tuple[list[tuple[str, int]], int | None]:
    """返回 ([(类别, 数)], Total 或 None)。按 '&' 切，右侧取第一个数字（先剥 LaTeX 命令）。"""
    i, j = text.find("begin{longtable}"), text.find("end{longtable}")
    tbl = text[i:j]
    out: list[tuple[str, int]] = []
    total = None
    for line in tbl.splitlines():
        s = line.strip()
        if s.count("&") != 1 or not s.endswith("\\\\"):
            continue
        left, right = s.rsplit("&", 1)
        # 剥掉 \textbf{...} / \textit{...} 等命令，保留参数
        clean_r = re.sub(r"\\[a-zA-Z]+\*?(?:\[[^\]]*\])?\{([^{}]*)\}", r"\1", right)
        clean_r = re.sub(r"[{}$\\]", "", clean_r).strip()
        clean_l = re.sub(r"\\[a-zA-Z]+\*?(?:\[[^\]]*\])?\{([^{}]*)\}", r"\1", left)
        clean_l = re.sub(r"[{}$\\]", "", clean_l).strip()
        m = re.match(r"^(\d[\d,]*)$", clean_r)
        if not m:
            continue
        val = int(m.group(1).replace(",", ""))
        if clean_l.lower().startswith("total"):
            total = val
        else:
            out.append((clean_l, val))
    return out, total


def main() -> int:
    cur = io.open(SUP, encoding="utf-8").read()
    cats, total = parse(cur)

    print("=== 现表（14 类 + Total）===")
    s = 0
    for name, v in cats:
        s += v
        print(f"  {name[:46]:<48} {v}")
    print(f"  {'各类求和':<48} {s}")
    print(f"  {'表中 Total':<48} {total}")
    print(f"  → {'✅ 一致' if s == total else '❌ 不一致'}")

    print("\n=== 改动前（git 16bb0f5）===")
    r = subprocess.run(["git", "show", "16bb0f5:paper合/sections/supplement.tex"],
                       capture_output=True, cwd=REPO)
    old = r.stdout.decode("utf-8", "ignore")
    cats_o, total_o = parse(old)
    so = 0
    for name, v in cats_o:
        so += v
        print(f"  {name[:46]:<48} {v}")
    print(f"  {'各类求和':<48} {so}")
    print(f"  {'表中 Total':<48} {total_o}")
    print(f"  → {'✅ 一致' if so == total_o else '❌ 不一致'}")

    print("\n=== 判定（数字均动态读取，不硬编码）===")
    print(f"  改动前：求和 {so} ｜ Total {total_o}")
    print(f"  改动后：求和 {s} ｜ Total {total} ｜ {'✅ 自洽' if s == total else '❌ 不自洽'}")

    # ── 动态统计严格冻结 run 数（不再硬编码）
    import glob as _glob
    sf_groups = [
        "outputs/strict_freeze/*/seed*/results.json",
        "outputs/strict_freeze_rank/r*/*/seed*/results.json",
        "outputs/strict_freeze_openclip/*/seed*/results.json",
        "outputs/strict_freeze_openclip_rank/r4/*/seed*/results.json",
        "outputs/siglip_strict/*/s4_siglip_lora_*/results.json",
        "outputs/siglip_strict/*/s6_siglip_lora_vision_only/results.json",
        "outputs/siglip_strict/*/s7_siglip_lora_r4_*/results.json",
    ]
    n_sf_files = sum(len(_glob.glob(str(REPO / g))) for g in sf_groups)
    # BioCLIP 的结果在部分结果文件里（run_log 解析而来）
    bio = REPO / "outputs" / "strict_freeze_bioclip" / "results_partial.json"
    n_bio = 0
    if bio.exists():
        import json as _json
        n_bio = len(_json.loads(bio.read_text(encoding="utf-8")).get("records") or [])
    n_sf = n_sf_files + n_bio

    # ── 动态读 ODE 拟合数（论文自己声明）
    va = io.open(REPO / "paper合" / "sections" / "validation.tex", encoding="utf-8").read()
    m_ode = re.search(r"(?:fit the ODE on|across)\s+(\d+)\s+experiments", va)
    n_ode = int(m_ode.group(1)) if m_ode else None

    # ── 动态读全文合计（摘要）
    ab = io.open(REPO / "paper合" / "main_nc.tex", encoding="utf-8").read()
    m_tot = re.search(r"(?:spans|across)\s+(\d+)\s*\n?\s*experiments", ab)
    n_tot = int(m_tot.group(1)) if m_tot else None

    print(f"\n  实测严格冻结 run : {n_sf}（各骨干 {n_sf_files} + BioCLIP {n_bio}）")
    print(f"  论文声明 ODE 拟合 : {n_ode}")
    print(f"  附录目录求和      : {s}")
    print(f"  摘要声明全文合计  : {n_tot}")
    if None not in (n_ode, n_tot):
        expect = s + n_ode
        ok = expect == n_tot
        print(f"  目录 + ODE = {s} + {n_ode} = {expect} ｜ 摘要称 {n_tot}"
              f"  → {'✅ 一致' if ok else '❌ 不一致'}")
        if ok and n_sf != s - 117:
            print(f"  ⚠ 严格冻结实测 {n_sf} 与目录表隐含的 {s - 117} 不符——目录表 XIV 类需核对")
        elif ok:
            print(f"  ✅ 严格冻结实测 {n_sf} = 目录表隐含值（{s} − 117）")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
