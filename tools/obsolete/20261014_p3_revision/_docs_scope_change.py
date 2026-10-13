# -*- coding: utf-8 -*-
r"""落账：按 ③+① 改稿（撤回 COCO ODE 表 + 写入适用边界，2026-10-08 19:00）。

    python tools\_docs_scope_change.py [--apply]
"""
from __future__ import annotations

import io
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]

ENT = """> **✅ 2026-10-08 19:00 —— 按 ③+① 改稿：**撤回 COCO 的 ODE 表**，把 `DG*` 的**适用边界**写进 limitation**
>
> ### 操作者决定：③（不补 COCO 的 ODE 表）+ ①（把边界条件写清楚）
>
> ### 改了两处
>
> | 文件 | 改动 |
> |---|---|
> | **`supplement.tex` D 节** | **删掉 `tab:coco_ode` 与旧正文**，替换为一段说明：**该表已撤回**及其可测原因 |
> | **`discussion.tex` Limitations** | **插入新的第四条**（原第四/五条顺延为五/六），写明 `DG*` **并非在所有配置下都移动** |
> >
> ### 写进论文的实测数字（全部有来源）
>
> | 量 | COCO（严格冻结） | Flickr30k（严格冻结） |
> |---|---|---|
> | `DG*` 跨度（10 epoch） | **0.003–0.006** | — |
> | 同 run 的 CG 跨度 | **0.108–0.111** | — |
> | **两者跨度之比** | **0.030–0.055** | **1.2–1.6** |
> | `DG*` 拟合 R² | **0.12 / 0.68** | 0.956 / 0.957 |
> | 同 run 的 CG R² | **0.93** | 0.874 / 0.902 |
> | R@1 | **0.12** | 0.62–0.70 |
>
> **机制句（写进论文）**：
> *"the model has moved the two modality centroids toward one another without bringing matched pairs
> together. A centroid gap can narrow while paired embeddings stay apart, and $DG^*$ measures the latter.
> Where $DG^*$ does not move, the ODE is fitted to noise."*
>
> **处置句**：*"we report no ODE coefficients for MS-COCO for this reason."*
> —— MS-COCO **仍保留**其能支持的部分（**按质心间隙比较适配位置**，正文与 §validation 已报）。
>
> ### 编译与门禁
>
> | 项 | 结果 |
> |---|---|
> | NC | **52 页** ｜ 0 错误 ｜ 0 未定义引用 ｜ **0 Overfull** |
> | Springer | **38 页** ｜ 0 错误 ｜ 0 未定义引用 ｜ **0 Overfull** |
> | **门禁** `_claim_ledger.py` | **33/33 通过** |
>
> ### 台账同步（**重要，防止日后误读**）
>
> 删表后，`tab:coco_ode` 的 3 条断言（`0.897`/`0.910`/`0.966`）**已无对应正文**（实测：三个值已不在任何 `.tex` 中）。
> **已把台账里那 3 条断言换成说明性注释**，记录数字的去向与撤回原因，**不再断言**。
> **否则过期的台账会让日后复核的人以为那些表还在。**
>
> ### 两处踩坑（已修）
>
> | # | 现象 | 原因 |
> |---|---|---|
> | 1 | 我最初用 `\\dgstar{}` 宏 | **该宏不存在**（实测论文用字面 `$DG^*$`）→ 已改 |
> | 2 | 断言报"未找到 withdrawn" | 我逐行检查，**而该短语跨行** → 实际已写入；改用整文件匹配确认 |
"""


def main() -> int:
    apply = "--apply" in sys.argv
    if not apply:
        print("  （预演）")
        return 0
    hp = REPO / "HANDOFF.md"
    t = io.open(hp, encoding="utf-8").read()
    if "按 ③+① 改稿" in t:
        print("  已记录，跳过")
        return 0
    i = t.find("# 项目交接文档")
    j = t.find("\n", i)
    io.open(hp, "w", encoding="utf-8", newline="").write(t[:j + 1] + "\n" + ENT + t[j + 1:])
    t2 = io.open(hp, encoding="utf-8").read()
    for k in ("按 ③+① 改稿", "该表已撤回", "0.030–0.055", "33/33 通过",
              "过期的台账会让日后复核的人以为那些表还在"):
        assert k in t2, f"断言失败：缺 {k}"
    print(f"  ✅ HANDOFF 已追加（{len(t2.splitlines())} 行）")

    mp = REPO / "文件地图.md"
    m = io.open(mp, encoding="utf-8").read()
    if "0M." not in m:
        add = """
**0M. ✅ COCO ODE 表已撤回 + `DG*` 适用边界已写入（2026-10-08 19:00，操作者选 ③+①）**

- `supplement.tex` D 节：**删 `tab:coco_ode`**，改为说明撤回原因（含实测数字）。
- `discussion.tex` Limitations：**新增第四条**——`DG*` 在冻结骨干 + 低检索性能的配置下不移动，ODE 拟合噪声。
- **关键数字**：COCO 严格冻结下 `DG*`/CG 跨度比 **0.030–0.055**（Flickr30k 为 1.2–1.6）；`DG*` R² 0.12/0.68 vs CG R² 0.93；R@1 0.12 vs 0.62–0.70。
- **编译**：NC **52 页** / Springer **38 页**，0 错误 0 未定义 0 Overfull。
- **门禁**：`tools/_claim_ledger.py` → **33/33**（已移除 3 条随表撤回的断言，改为说明性注释）。
- 脚本：`tools/_pa_dgstar_scope2.py`、`tools/_pa_ledger_drop_coco.py`。

"""
        anchor = "## 七、当前真正待办（按优先级）\n"
        m2 = m.replace(anchor, anchor + add, 1)
        io.open(mp, "w", encoding="utf-8", newline="").write(m2)
        print(f"  ✅ 文件地图.md 已更新（{len(m2.splitlines())} 行）")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
