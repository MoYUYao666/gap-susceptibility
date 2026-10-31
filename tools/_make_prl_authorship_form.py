# -*- coding: utf-8 -*-
r"""生成 PRL 的 Authorship Confirmation 表（可指定**任意日期**与稿号）。

## 做法

以 A1 已通过技术检查的单页版为底稿（`paper_a1/_archive_prl/Authorship Confirmation submit.pdf`，
若不存在则回退到本工具此前生成过的任一版本），**只替换"日期"那个内容流**，表格版式一字不动。

机制（已诊断）：每个填写值都是**独立的十六进制文本流**，用 `/helv 11 Tf` + `Tm` 定位。
日期流可通过 `Tm` 的 x 坐标（≈340.43）识别，**不依赖具体日期文本**——因此可反复重生成。

## 用法

    python tools/_make_prl_authorship_form.py --date "September 28, 2026" --slug "rev-02402"
    python tools/_make_prl_authorship_form.py --date "September 26, 2026" --slug "p3-02378"
    python tools/_make_prl_authorship_form.py --check paper_review_prl/Authorship*.pdf

产物命名含**稿号与日期**，避免同目录下张冠李戴（2026-09-29 曾因此误判归属）。
"""
from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

from pypdf import PdfReader, PdfWriter

REPO = Path(__file__).resolve().parents[1]
A1_SRC = REPO / "paper_a1" / "_archive_prl" / "Authorship Confirmation submit.pdf"
FALLBACKS = [A1_SRC,
             REPO / "paper_review_prl" / "Authorship Confirmation (P3, 2026-09-26).pdf",
             REPO / "paper3" / "paper_ieee" / "PRL_submission" / "Authorship Confirmation (P3, 2026-09-26).pdf"]
DATE_X = 340.43          # 日期流的 Tm x 坐标（pt），用于识别
PAGE_RIGHT = 42.52 + 468.04

# Helvetica AFM 宽度（1/1000 em）
W = {" ": 278, ",": 278, "-": 333, ".": 278, "0": 556, "1": 556, "2": 556, "3": 556, "4": 556,
     "5": 556, "6": 556, "7": 556, "8": 556, "9": 556, "A": 667, "B": 667, "C": 722, "D": 722,
     "E": 667, "F": 611, "G": 778, "H": 722, "I": 278, "J": 500, "K": 667, "L": 556, "M": 833,
     "N": 722, "O": 778, "P": 667, "Q": 778, "R": 722, "S": 667, "T": 611, "U": 722, "V": 667,
     "W": 944, "X": 667, "Y": 667, "Z": 611,
     "a": 556, "b": 556, "c": 500, "d": 556, "e": 556, "f": 278, "g": 556, "h": 556, "i": 222,
     "j": 222, "k": 500, "l": 222, "m": 833, "n": 556, "o": 556, "p": 556, "q": 556, "r": 333,
     "s": 500, "t": 278, "u": 556, "v": 500, "w": 722, "x": 500, "y": 500, "z": 500}


def text_width(s: str, size: float) -> float:
    return sum(W.get(c, 556) for c in s) * size / 1000.0


def pick_source() -> Path:
    for p in FALLBACKS:
        if p.exists():
            return p
    raise SystemExit("❌ 找不到任何底稿")


def find_date_stream(page):
    """按 Tm 的 x 坐标识别日期流（不依赖具体日期文本）。"""
    for i, ref in enumerate(page["/Contents"]):
        obj = ref.get_object()
        data = obj.get_data()
        for m in re.finditer(rb"1 0 0 1 ([\d.]+) [\d.]+ Tm", data):
            if abs(float(m.group(1)) - DATE_X) < 0.5 and b"/helv" in data:
                hexes = re.findall(rb"<([0-9A-Fa-f]+)>", data)
                if hexes:
                    return i, obj, bytes(hexes[0])
    raise SystemExit("❌ 未找到日期内容流")


def check(path: Path, expect_date: str) -> int:
    r = PdfReader(str(path))
    t = r.pages[0].extract_text()
    ok = [len(r.pages) == 1, expect_date in t, t.count("Hongrui Wan") >= 2, t.count("None") >= 2]
    print(f"  校验 {path.name}")
    print(f"    单页 {len(r.pages) == 1} ｜ 含日期 {expect_date!r} {expect_date in t} ｜ "
          f"姓名×2 {t.count('Hongrui Wan') >= 2} ｜ None×2 {t.count('None') >= 2}")
    return 0 if all(ok) else 1


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--date", default="September 26, 2026")
    ap.add_argument("--slug", default="p3-02378", help="输出文件名后缀，如 p3-02378 / rev-02402")
    ap.add_argument("--outdir", default=None)
    ap.add_argument("--check", nargs="*", help="只校验给定 PDF")
    args = ap.parse_args()

    if args.check:
        rc = 0
        for f in args.check:
            for p in sorted(Path().glob(f)) if "*" in f else [Path(f)]:
                rc |= check(p, args.date)
        return rc

    src = pick_source()
    reader = PdfReader(str(src))
    page = reader.pages[0]
    idx, obj, old_hex = find_date_stream(page)
    old_txt = bytes.fromhex(old_hex.decode())
    new_hex = args.date.encode().hex().encode()
    if old_hex == new_hex:
        print(f"  底稿已是目标日期 {args.date!r}（流 #{idx}），无需替换")

    width = text_width(args.date, 11)
    end = DATE_X + width
    print(f"  底稿: {src.relative_to(REPO)}")
    print(f"  日期流 #{idx}: {old_txt.decode()} → {args.date}")
    print(f"  新日期宽度 {width:.1f} pt，终点 x={end:.1f}（版心右边界 {PAGE_RIGHT:.1f}）")
    if end > PAGE_RIGHT - 4:
        raise SystemExit("❌ 新日期将溢出，需缩小字号")

    data = obj.get_data().replace(old_hex, new_hex)
    obj.set_data(data)

    outdir = Path(args.outdir).resolve() if args.outdir else REPO / "paper_review_prl"
    outdir.mkdir(parents=True, exist_ok=True)
    out = outdir / f"Authorship Confirmation ({args.slug}).pdf"
    w = PdfWriter()
    w.add_page(page)
    with out.open("wb") as fh:
        w.write(fh)
    shown = out.relative_to(REPO) if str(out).startswith(str(REPO)) else out
    print(f"  写出 {shown}（{out.stat().st_size} B）\n")
    return check(out, args.date)


if __name__ == "__main__":
    raise SystemExit(main())
