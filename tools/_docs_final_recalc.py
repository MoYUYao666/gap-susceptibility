# -*- coding: utf-8 -*-
r"""落账：批次统一 + 5 seed + VLM 13 seed 全部写进论文（2026-10-11）。

    python tools\_docs_final_recalc.py [--apply]
"""
from __future__ import annotations

import io
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]

ENT = """> **✅ 2026-10-11 晚 —— 实验全部收尾：批次统一 batch 128 + 5 seed + VLM 13 seed 已写进论文，门禁 80/80**
>
> ### 一、总核对：**批次污染已彻底清除**
>
> | 组 | run | 批次 |
> |---|---|---|
> | `strict_freeze_b32_r4` | 15 | ✅ 全 128（5 seed × 3 臂） |
> | `strict_freeze_b16/r4` | 15 | ✅ 全 128 |
> | `strict_freeze_oclip/r4` | 15 | ✅ 全 128 |
> | `coco_sweep_text_only` | 24 | ✅ 全 128 |
> | `coco_sweep`（both 等） | 31 | ✅ 全 128 |
>
> **100 个 run，全部 batch 128。**
>
> ### 二、重算后的核心数字
>
> **① `tab:position_strict`（n=5，batch 128）—— 三骨干一致**
>
> | 骨干 | `text_only` | `both` | `vision_only` | 最保护 |
> |---|---|---|---|---|
> | CLIP B/32 (WIT) | **$-0.0304\\pm0.0039$** | $-0.0204\\pm0.0028$ | $+0.0166\\pm0.0055$ | `text_only` |
> | CLIP B/16 (WIT) | **$-0.0166\\pm0.0018$** | $+0.0124\\pm0.0024$ | $+0.0376\\pm0.0051$ | `text_only` |
> | OpenCLIP (LAION) | **$+0.0802\\pm0.0006$** | $+0.0864\\pm0.0042$ | $+0.0996\\pm0.0026$ | `text_only` |
>
> **② 🔴 批次污染正是 OpenCLIP"效应量弱"的原因**
>
> | 比较 | 混批次（旧） | **统一后（新）** |
> |---|---|---|
> | `text_only` vs `both` | $0.52$ sd | **$1.48$ sd** |
> | `both` vs `vision_only` | $0.55$ sd | **$2.71$ sd** |
>
> 旧 seed 42 是 128、123/456 是 64 → 把真实差异抹平了。**表注已从"排序 not resolved"
> 改为"$1.5$/$2.7$ pooled sd，排序成立"**。
>
> **③ 数据集翻转（r4 同秩同批次）—— 确实相反**
>
> | 数据集 | `text_only` | `both` | 最保护 |
> |---|---|---|---|
> | Flickr30k | **$-0.0304\\pm0.0039$** | $-0.0204\\pm0.0028$ | `text_only` |
> | MS-COCO | $-0.0414\\pm0.0015$ | **$-0.0886\\pm0.0026$** | `both` |
>
> COCO `text_only` 全秩（batch 128 重跑后）：r2 $-0.0247$｜r8 $-0.0690$｜r32 $-0.1153$｜r64 $-0.1359$
>
> **④ `tab:vlm`（13 seed）**
>
> | 臂 | $DG^*$ 相对变化 | 范围 | CG 跨度 |
> |---|---|---|---|
> | `text_only` | $+66.5\\pm8.3\\%$ | 47.8--78.8 | $0.168\\pm0.094$ |
> | `both` | $+87.9\\pm5.3\\%$ | 73.1--95.1 | $0.291\\pm0.108$ |
> | `vision_only` | $+18.0\\pm8.8\\%$ | **8.5--35.7** | $0.392\\pm0.087$ |
>
> **`vision_only` 最大值 $35.7\\%$ < 另两臂最小值（$47.8$ / $73.1$）→ 分布不重叠，13 seed 全支持"最弱"。**
> 而 `text_only` 的均值随 seed 漂移（9 seed $+82.0$ → 13 seed $+66.5$），**说明单一 seed 数不可靠**。
>
> ### 三、论文改动
>
> | 文件 | 改动 |
> |---|---|
> | `empirical.tex` | `tab:position_strict` 3 行 + 表注（5 seed / batch 128 / OpenCLIP $1.5$/$2.7$ sd） |
> | `validation.tex` | 翻转段全部数字改为 5 seed / batch 128 |
> | `supplement.tex` | `tab:vlm` → **13 seed**；判读段重写（含"9 seed 的 $+82\\%$ 是波动"） |
> | `discussion.tex` | Second limitation 同步 13-seed 数字 |
>
> **旧数字残留扫描（`tools/_p178`）：0 命中** ✅
>
> ### 四、编译与门禁
>
> | 稿 | 页数 | 错误 | 未定义 | Overfull |
> |---|---|---|---|---|
> | Springer | **40** | 0 | 0 | 0 |
> | **NC** | **56** | 0 | 0 | 0 |
>
> **门禁：80/80 通过（退出码 0）**——修掉 22 条因重算失效的断言
> （含 `NEW_ROWS` 表、VLM 汇总、COCO 全秩）。
>
> ### 五、本阶段踩过的坑（都已修 + 留档）
>
> | # | 坑 | 修法 |
> |---|---|---|
> | 1 | `_p169` 队列传基础路径 → COCO 被校验拒绝（16 失败）+ r8 写入错位目录（4 个） | `_p172`：outdir 含 rank；错位结果改名 `.MISPLACED_*` 留证 |
> | 2 | **`_p173` 静默跳过**（旧 batch-64 文件在即跳过，rc=0）→ 11 个没真跑 | `_p174`：加 `stash_old()` 把旧文件改名 |
> | 3 | `_p175` rank 解析漏了 `strict_freeze_b32_r4`（rank 在组名里） | `_p176`：回退到组名解析 |
> | 4 | 正则写 `\\\\pm` 而文件是 `\pm` → 不匹配 | `_p179` dump 真实字节 → `re.escape()` |
>
> **"静默跳过"这个坑踩了两次**（`_p169` 与 `_p173`）——**教训**：
> `strict_freeze_control.py` 的设计是"存在即跳过"，**rc=0 无法区分"跑成功"与"什么都没做"**；
> **凡要"重跑覆盖"，必须先 stash 旧文件**，并以**文件 mtime + 元数据**判真伪。
>
> ### 六、待办（只剩投稿类，无实验）
>
> | # | 项 | 谁 |
> |---|---|---|
> | 1 | **`paper合` 定目标刊并投出**（ESWA/KBS/CVIU） | 待操作者 |
> | 2 | **A1 转投确认**（`Neural Networks`，截止 `Nov 08`） | 待操作者 |
> | 3 | `imod`/`hu2022lora` 两条文献作者（现 `Anon.`） | 待操作者 |
"""


def main() -> int:
    apply = "--apply" in sys.argv
    if not apply:
        print("  （预演）")
        return 0
    hp = REPO / "HANDOFF.md"
    t = io.open(hp, encoding="utf-8").read()
    if "实验全部收尾" in t:
        print("  已记录，跳过")
        return 0
    i = t.find("# 项目交接文档")
    j = t.find("\n", i)
    io.open(hp, "w", encoding="utf-8", newline="").write(t[:j + 1] + "\n" + ENT + t[j + 1:])
    t2 = io.open(hp, encoding="utf-8").read()
    for k in ("实验全部收尾", "100 个 run", "1.48", "2.71", "80/80",
              "静默跳过", "13 seed", "批次污染正是 OpenCLIP"):
        assert k in t2, f"断言失败：缺 {k}"
    print(f"  ✅ HANDOFF 已追加（{len(t2.splitlines())} 行）")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
