# -*- coding: utf-8 -*-
r"""Record the live in-progress state so a new session can pick the work up from the files, not the chat.

The operator asked whether a copied session id lets a new session read and continue this one. Tested:
`session_search` returns "session history storage is unavailable" on this machine, so conversations are **not**
recoverable. The workspace is the only durable channel, and it must therefore carry enough state on its own.

    python tools/_p1158_record_live_state.py [--apply]
"""
from __future__ import annotations

import argparse
import io
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
HANDOFF = REPO / "HANDOFF.md"
MARK = "进行中状态（新会话从这里接）"

ENT = """> **🕐 2026-10-17 18:55 —— ⏳ 进行中状态（新会话从这里接；会话历史不可读，本文件是唯一载体）**
>
> ### 一、⚠️ 会话接续能力（已实测）
>
> - `session_search` → **`session history storage is unavailable`** ⇒ **新会话无法读取旧对话**，复制 session id 也读不到；
> - ⇒ **接续必须靠工作区文件**：新会话开场读 `HANDOFF.md` 顶部三条（本条 + 18:20 干净口径 + 18:30 关机规则）与
>   `文件地图.md` 顶部「当前总状态」+ 第 52 条，即可接上。
>
> ### 二、正在跑什么
>
> | 项 | 值 |
> |---|---|
> | 任务 | **E 节（Qwen2-VL-2B）干净口径重跑** |
> | 脚本 | 远端 `/root/p3/_p1155.sh` → `tools/_p1150_qwen_clean_sweep.py`（两路并行，每路 7/6 个 seed）|
> | 规模 | 3 臂 × 13 seed = **39 run**，每 run 约 6.2 分钟 |
> | 主机 | `connect.westc.seetacloud.com:16320`（认证走会话内的 `P3SSH_*` 环境变量）|
> | 进度 | 截至 18:55 **16/39**，零失败；预计 **20:20–20:40** 结束 |
> | 产物 | 远端 `/root/p3/outputs/vlm_clean/{arm}_seed{seed}.json` + 日志 `/root/p3/vlm_clean_{A,B}.log` |
>
> ### 三、跑完之后必须做什么（按顺序，**不要跳步**）
>
> 1. **确认跑完**：`ls /root/p3/outputs/vlm_clean/*.json | wc -l` 应为 **39**；`vlm_clean_runner.log` 末尾应为
>    `ALL_STREAMS_DONE`；两份日志里无 `Traceback`/`CUDA` 错误；
> 2. **补 frozen 基线**（脚本尚未含此步，必须手补）：Qwen2-VL-2B 不加载任何适配器、用**同一干净口径**
>    （I=图像 token 池化，T=**caption 位置**池化，无投影）在 400 样本上测一次 DG\*，否则"降幅"只能用第 1 epoch 当基准——
>    那是混入训练进度的错误算法（原 `_p47`/E 表正是这么算的，属已知缺陷，不得沿用）；
> 3. **全项校验**：39 条记录齐全、每臂 13 seed、`token_counts_first_batch` 里 `img` 与 `cap` 均 > 0、
>    分塔隔离 `n_vis/n_lang` 符合臂定义、`clean` 与 `legacy_dg_star` 字段齐全；
> 4. **取回本地**：全部 39 个 JSON + summary + 两份日志拉到 `outputs/vlm_clean_cloud/` 并逐文件校验大小；
> 5. **算三臂均值±sd**（相对 frozen 基线），与 G 节（LLaVA：**vision +121.5% > both +95.7% > text +73.3%**）对照；
> 6. **改写**补充 E、G 两节 + `discussion.tex` ¶32 + 摘要相关句；**两表不宣称量级可比**（E=对比对齐目标、G=生成目标）；
> 7. 过 `_claim_ledger_paperA.py`，重编译 `main_nc.pdf` / `main_springer.pdf`；
> 8. 更新 `HANDOFF.md` / `文件地图.md` / `docs/`（阶段收尾规则）。
>
> ### 四、🔴 最后一步：关机（操作者已授权，规则见 `AGENTS.md`）
>
> **只有上面第 1–4 步全部完成并通过校验后**才执行：
> `sync && ( shutdown -h now || poweroff )`；若容器无权关机，**如实报告"需在控制台停止"，不得假装已关**；
> 关机后用端口探测确认不可达，并在此文件记一条"已关机 + 时间"。
>
> ### 五、其他已就绪但未用的东西
>
> - LLaVA 干净重测结果：`outputs/canonical_caption_metric.json`（已取回，**权威**）；
> - LLaVA 9 个真适配器：`outputs/llava_canonical_cloud/`（已取回，1700 MB）；
> - 远端持久盘上仍有：LLaVA 权重 14 GB、Qwen2-VL-2B 4.42 GB、Flickr30k 120 图 fixture、COCO 2000 图；
> - `tools/_p1150`（修正版 Qwen 扫描）、`_p1153`（Flickr fixture）、`_p1145`（LLaVA 干净重测）均已验证可跑。
>
> **脚本**：`_p1158`（本条）。
>

"""


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    a = ap.parse_args()
    if not a.apply:
        print("  (dry run)")
        return 0
    hp = io.open(HANDOFF, encoding="utf-8").read()
    if MARK in hp:
        print("  live-state entry already present; replace it instead of duplicating")
        return 0
    i = hp.find("# 项目交接文档")
    j = hp.find("\n", i)
    hp = hp[: j + 1] + "\n" + ENT + hp[j + 1:]
    io.open(HANDOFF, "w", encoding="utf-8", newline="").write(hp)
    print("  live-state entry added at the top of HANDOFF.md")

    mp = io.open(REPO / "文件地图.md", encoding="utf-8").read()
    row = ("53. 🕐 **进行中：E 节干净重跑 39 run（2026-10-17 18:55）** —— 新会话接续**只能靠工作区文件**"
           "（实测 `session_search` 报 `session history storage is unavailable`，**旧对话不可读**）。"
           "E 跑完后依次：补 **frozen 基线**（不可用第 1 epoch 当基准）→ 全项校验 → 取回 39 JSON → 算均值±sd → "
           "改写 E/G/`discussion.tex` ¶32 → 过账本 → 重编译 → **关机**。详见 `HANDOFF.md` 顶部 18:55 条目。\n")
    if "进行中：E 节干净重跑" not in mp:
        anchor = "52. 🔁 **干净口径反转"
        idx = mp.find(anchor)
        if idx >= 0:
            end = mp.find("\n", idx)
            mp = mp[: end + 1] + row + mp[end + 1:]
            io.open(REPO / "文件地图.md", "w", encoding="utf-8", newline="").write(mp)
            print("  map item added")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
