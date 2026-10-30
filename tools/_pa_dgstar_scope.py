# -*- coding: utf-8 -*-
r"""按 ③+①改写：不补 COCO 的 ODE 表 + 把 `DG*` 的**适用边界**写清楚（2026-10-08）。

## 操作者决定：③ + ①

- **③**：不为 COCO 硬凑一张与 Flickr30k 不同量的 ODE 表 → **删掉 supplement 的 `tab:coco_ode` 与 D 节**；
- **①**：把边界条件写进 limitation —— `DG*` 在"**冻结骨干 + 低检索性能**"配置下**不移动**，
  ODE 拟合无意义。**"框架何时适用"本身是有价值的发现。**

## 实测依据（`tools/_p39_verify_dgstar_failure.py`）

| 数据集（严格冻结） | `dg*`/`cg` 跨度比 | `dg*` R² | `cg` R² |
|---|---|---|---|
| COCO（新跑） | **0.030–0.055** | **0.124 / 0.679** | 0.927 / 0.931 |
| Flickr30k（归档） | **1.215–1.568** | 0.956 / 0.957 | 0.874 / 0.902 |

**物理解释**：COCO 严格冻结后 R@1 仅 0.12（Flickr30k 为 0.62–0.70）——
模型只让**质心**靠近，**未真正拉近配对**。**质心靠近 ≠ 配对对齐。**

## 改动

| 文件 | 改什么 |
|---|---|
| `supplement.tex` | 删 `tab:coco_ode` 表 + D 节正文；改为一段说明"为什么该表被撤回" |
| `discussion.tex` | 在第四/五条 limitation 之间**插入新的一条**（DG\* 的适用条件） |

    python tools\_pa_dgstar_scope.py [--apply]
"""
from __future__ import annotations

import ast
import io
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
SUP = REPO / "paper合" / "sections" / "supplement.tex"
DIS = REPO / "paper合" / "sections" / "discussion.tex"

# ── ① supplement：把 D 节（含表）整段替换为说明
SUP_HEAD = r"\section*{D. Cross-Dataset ODE Validation}"
SUP_NEW = r"""\section*{D. Cross-Dataset ODE Validation}

An earlier version of this supplement reported ODE coefficients for MS-COCO in a table. That table has
been withdrawn. Its coefficients were fitted to ^*$ trajectories from runs in which the backbone
remained trainable, and the strict-freezing runs that this paper's controls use do not reproduce the
quantity it measured.

The reason is measurable and is reported here rather than left implicit. Under strict freezing the
^*$ trajectory on MS-COCO moves by $0.003$--$0.006$ over ten epochs, whereas the centroid gap
moves by $0.108$--$0.111$ on the same runs; the ratio of the two spans is $0.030$--$0.055$. On
Flickr30k the same ratio is $1.2$--$1.6$. Fitting the exponential form to the MS-COCO trajectory gives
$R^2 = 0.12$ and $0.68$ on the two seeds available, against $0.93$ for the centroid gap on those same
runs. The retrieval accuracy explains why: strict freezing on MS-COCO reaches $R@1 = 0.12$ where
Flickr30k reaches $0.62$--$0.70$, so the model has moved the two modality centroids toward one another
without bringing matched pairs together. A centroid gap can narrow while paired embeddings stay apart,
and ^*$ measures the latter. Where ^*$ does not move, the ODE is fitted to noise.

MS-COCO is therefore retained in this paper for what the strict-freezing runs do support --- the
comparison of adaptation sites by centroid gap, which is reported in the main text and in
Section~\ref{sec:validation} --- and not for ODE coefficients."""

# ── ② discussion：插入新 limitation（放在 Fourth 之前）
DIS_ANCHOR = r"Fourth, the fit accuracies reported in Section~\ref{sec:validation}"
DIS_NEW = (r"Fourth, the ODE's state variable does not move in every configuration the framework is asked "
           r"to describe. On MS-COCO under strict freezing the ^*$ trajectory changes by "
           r"$0.003$--$0.006$ over ten epochs while the centroid gap changes by $0.108$--$0.111$, and the "
           r"exponential fit returns $R^2$ between $0.12$ and $0.68$ against $0.93$ for the centroid gap on "
           r"the same runs; the corresponding ratio of spans on Flickr30k is $1.2$--$1.6$. The retrieval "
           r"accuracies indicate why: strict freezing reaches $R@1 = 0.12$ on MS-COCO against "
           r"$0.62$--$0.70$ on Flickr30k, so the centroids of the two modalities approach one another "
           r"without matched pairs being brought together, and ^*$ measures the latter. The framework "
           r"therefore describes alignment dynamics where adaptation actually moves the embeddings, and its "
           r"coefficients should not be reported for configurations in which it does not; we report no ODE "
           r"coefficients for MS-COCO for this reason. Fifth, the fit accuracies reported in "
           r"Section~\ref{sec:validation}")


def main() -> int:
    apply = "--apply" in sys.argv
    ok = 0

    # ① supplement
    t = io.open(SUP, encoding="utf-8").read()
    if "That table has been withdrawn" in t:
        print("  · supplement 已改，跳过")
        ok += 1
    else:
        i = t.find(SUP_HEAD)
        assert i > 0, "未找到 D 节"
        j = t.find(r"\section*", i + len(SUP_HEAD))
        assert j > i, "未找到 D 节结尾"
        old = t[i:j]
        t = t[:i] + SUP_NEW + "\n\n" + t[j:]
        if apply:
            ast.parse("pass")
            io.open(SUP, "w", encoding="utf-8", newline="").write(t)
        print("  ✅ supplement：D 节已替换（表撤回 + 说明原因）")
        ok += 1

    # ② discussion
    t2 = io.open(DIS, encoding="utf-8").read()
    if "does not move in every configuration" in t2:
        print("  · discussion 已改，跳过")
        ok += 1
    else:
        if t2.count(DIS_ANCHOR) != 1:
            print(f"  ❌ discussion 锚点未唯一命中（{t2.count(DIS_ANCHOR)}）")
        else:
            t2 = t2.replace(DIS_ANCHOR, DIS_NEW, 1)
            if apply:
                io.open(DIS, "w", encoding="utf-8", newline="").write(t2)
            print("  ✅ discussion：已插入 DG* 适用边界的 limitation")
            ok += 1

    if ok < 2:
        return 1
    if apply:
        s = io.open(SUP, encoding="utf-8").read()
        d = io.open(DIS, encoding="utf-8").read()
        assert "That table has been withdrawn" in s
        assert "tab:coco_ode" not in s, "旧表仍在 supplement"
        assert "does not move in every configuration" in d
        assert "\^*$" in s and "\^*$" in d
        print("  ✅ 断言通过：旧表已删、limitation 已写")
    else:
        print("  （预演）")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
