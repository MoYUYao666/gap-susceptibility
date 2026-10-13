# -*- coding: utf-8 -*-
r"""落账：补 seed 暂停（操作者要求先停，2026-10-09 06:05）。

    python tools\_docs_seed_pause.py [--apply]
"""
from __future__ import annotations

import io
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]

ENT = """> **⏸️ 2026-10-09 06:05 —— 补 seed 暂停（操作者要求"先停，过会儿再跑"）**
>
> ### 停止点（干净停机）
>
> | 项 | 状态 |
> |---|---|
> | 补 seed 驱动 + 训练 | ✅ 已终止（按**精确命令行匹配**，未用 CPU/启动时间筛） |
> | 遗留 DataLoader worker | ✅ 已清（4 个 `multiprocessing.spawn` 孤儿） |
> | python 进程 | **0** ｜ GPU **464 MiB / 8188**（已释放） |
>
> ### ✅ 已完成的结果全部落盘（**19 个 `results.json`，续跑自动跳过**）
>
> | 骨干 | text_only | both | vision_only |
> |---|---|---|---|
> | **CLIP B/32 r4** | **3/3** ✅ | **3/3** ✅ | **3/3** ✅ |
> | CLIP B/16 r4 | **3/3** ✅ | 2/3 | 2/3 |
> | OpenCLIP r4 | 1/3 | 1/3 | 1/3 |
>
> ### 已得的实质结论（停机不影响）
>
> | 骨干 | text_only | both | vision_only | 判定 |
> |---|---|---|---|---|
> | CLIP B/32 r4（3 seed） | **−0.0288 ± 0.0013** | −0.0188 ± 0.0004 | +0.0127 ± 0.0024 | ✅ 未翻转 |
> | CLIP B/16 r4（3/2 seed） | **−0.0172 ± 0.0021** | +0.0139 ± 0.0016 | +0.0403 ± 0.0024 | ✅ 未翻转 |
>
> **两两 sd 区间全部不重叠**；**B/16 上 text_only 与 both 差 14.8 倍 sd**
> → **同秩对照的反例结论经多 seed 加固**。
>
> ### 续跑方式（幂等）
>
> ```
> python tools\\_p56_add_seeds.py --apply
> ```
> **已存在 `results.json` 的 run 会被 `strict_freeze_control.py` 自带逻辑跳过**
> （脚本本身也按 `OUT_DIR/tag/seedN/results.json` 判重）。
>
> ### 剩余
>
> `CLIP B/16` 的 2 个臂 + `OpenCLIP` 的 9 个 run → **约 6–9 h**；
> 之后自动接 **`Γ_m` 完整测量**（`tools/_p58_gamma_clip.py`，~10 min）→ 定 `Γ_m` 口径（操作者选 A）。
>
> ### 本阶段未完成的风险项（供续跑时对齐）
>
> | # | 风险 | 状态 |
> |---|---|---|
> | #1 | 补 seed | ⏸️ **部分完成**（19/30 run；排序已稳定） |
> | #3 | OpenCLIP 效应量（我先前"仅 2 sd"的参照量选错） | ⏸️ 待 OpenCLIP 补完 seed 后**按逐臂 sd 重算** |
> | #4 | COCO 缺的 `text_only` 3 个秩 | ⏸️ 待办（~5 h） |
> | #2 / #5 | `Γ_m` 在解码器 VLM / 用 `Γ_m` 替代 `α` | ✅ 完成 |
> | #6 | 训练规模小 | 已标注，不补 |
"""


def main() -> int:
    apply = "--apply" in sys.argv
    if not apply:
        print("  （预演）")
        return 0
    hp = REPO / "HANDOFF.md"
    t = io.open(hp, encoding="utf-8").read()
    if "补 seed 暂停" in t:
        print("  已记录，跳过")
        return 0
    i = t.find("# 项目交接文档")
    j = t.find("\n", i)
    io.open(hp, "w", encoding="utf-8", newline="").write(t[:j + 1] + "\n" + ENT + t[j + 1:])
    t2 = io.open(hp, encoding="utf-8").read()
    for k in ("补 seed 暂停", "19 个 `results.json`", "_p56_add_seeds.py --apply",
              "按逐臂 sd 重算"):
        assert k in t2, f"断言失败：缺 {k}"
    print(f"  ✅ HANDOFF 已追加（{len(t2.splitlines())} 行）")

    mp = REPO / "文件地图.md"
    m = io.open(mp, encoding="utf-8").read()
    if "0P." not in m:
        add = """
**0P. ⏸️ 补 seed 暂停（2026-10-09 06:05，操作者要求"过会儿再跑"）**

- **停机干净**：驱动+训练按精确命令行终止；4 个 DataLoader worker 孤儿已清；**python 进程 0、GPU 464 MiB**。
- **19 个 `results.json` 已落盘**（CLIP B/32 r4 三臂 3/3；CLIP B/16 r4 3/2/2；OpenCLIP r4 1/1/1）→ **续跑自动跳过**。
- **续跑命令**：`python tools\\_p56_add_seeds.py --apply`（幂等）。
- **已得结论**：B/32 r4 与 B/16 r4 的**最保护臂均未翻转**；两两 sd 区间**不重叠**；**B/16 上 text_only vs both 差 14.8 倍 sd** → 同秩反例经多 seed 加固。
- **剩余**：CLIP B/16 的 2 臂 + OpenCLIP 9 run（6–9 h）→ 之后接 `Γ_m` 完整测量（`tools/_p58_gamma_clip.py`）。

"""
        anchor = "## 七、当前真正待办（按优先级）\n"
        m2 = m.replace(anchor, anchor + add, 1)
        io.open(mp, "w", encoding="utf-8", newline="").write(m2)
        print(f"  ✅ 文件地图.md 已更新（{len(m2.splitlines())} 行）")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
