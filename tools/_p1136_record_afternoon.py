# -*- coding: utf-8 -*-
r"""Record the 2026-10-17 afternoon state: adapter deletion, Qwen prep, retrain checkpoint verified.

    python tools/_p1136_record_afternoon.py [--apply]
"""
from __future__ import annotations

import argparse
import io
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
HANDOFF = REPO / "HANDOFF.md"
MAP = REPO / "文件地图.md"
MARK = "空适配器已删、Qwen 重测准备"

ENT = """> **🧹 2026-10-17 11:05 —— 空适配器已删；Qwen 重测准备就绪；重训 checkpoint **已验证含 448 个真实张量**；新 shell 经验**
>
> ### 一、✅ 空适配器已删除（操作者指示"删"）
>
> | 位置 | 删除 | 验证 |
> |---|---|---|
> | 本地 `outputs/llava_bf16_sites_cloud/` | **811 MB**（7 个 `.pt`）| 删前逐个 `torch.load` 确认 `model tensors: 0` |
> | 云端 `/root/p3/adapters/` | **773 MB**（7 个）| 同样逐个确认 |
>
> **12 条记录未动**（Paper A 补充 F 节的来源）。脚本 `tools/_p1131_delete_empty_adapters.py`（带"非空则保留"的保护）。
>
> ### 二、✅ 重训 checkpoint 实测**非空**（最大风险已排除）
>
> ```
> text_only_s42_ckpt.pt | tensors: 448 | 240 MB
> sample: base_model.model.model.language_model.layers.0.self_attn.q_proj.lora_A.default.weight
> ```
>
> 与冒烟测试**完全一致**（同为 448 张量 / 240 MB）⇒ `_p1115` 的按名过滤修复在真实运行中生效。
>
> ### 三、🔄 Qwen 重测准备（不占 GPU，与重训并行）
>
> **重新审视昨天的结论**：昨天判"32 GB 装不下 Qwen-7B"，但当时测量走 **`output_hidden_states=True`**，
> 而今天在 LLaVA 上发现该开关**实际分配 29.81 GiB**（远超其应占量）⇒ **Qwen 那次 OOM 很可能主要是这个开关**，
> 而非模型本身太大。既然已换成 `lm_head` hook，**值得重测**。
>
> | 项 | 状态 |
> |---|---|
> | Qwen2.5-VL-7B 权重 | 下载中（镜像多连接，**5 分片 16.6 GB**，约 5–13 MB/s）|
> | **新 Qwen 运行器** | ✅ `tools/_p1135_qwen_sites.py`（**从今天修好的 `_p820` 重新生成**，743 行）|
> | 生成器 7 项断言 | Qwen 类 / chat template / `image_token_id`(151655) / 分塔 `model.visual.*` / **`lm_head` hook** / **真权重保存** / **规范度量** |
> | LLaVA 脚本未被污染 | ✅ 生成前后字节一致（断言） |
>
> ⚠️ 与昨天的 Qwen 运行器相比，**修掉了两个已知缺陷**：度量含图像 token（自比自）、保存空权重。
>
> ### 四、💻 PowerShell shell 变更经验（2026-10-17 立）
>
> DSH 工具 shell 现为 **PowerShell 7.6.7 + UTF-8**（`[Console]::OutputEncoding = utf-8`）。
> **注意**：编码变好**不代表引号问题消失**——双引号字面量里 `` ` `` 仍是转义符、`$` 仍是变量前缀，实测：
>
> ```
> 双引号:  python -c "s='a`b'"        -> 反引号被吞
> 单引号:  python -c 's="a`b"; b="$HOME"'  -> 反引号与 $ 原样保留 ✅
> ```
>
> ⇒ **规矩：内联命令（python -c / 远端命令）一律用 PowerShell 单引号包裹**，含双引号、`$`、反引号、正则时尤其必要；
> 中文输出已正常，无需再设 `PYTHONIOENCODING`。这一条可省掉今天反复踩的坑。
>
> ### 五、⏭️ 顺序
>
> 1. Qwen 权重下完（约 11:40）；
> 2. **等重训腾出 GPU（约 17:00）** → Qwen 冒烟（5 步：能否装下 + 规范度量）；
> 3. 重训完成 → 全项校验 + 取回 12 条记录 + 7 个**真**适配器；
> 4. 规范值过账本，再决定 Paper A 补充 F 节是否改写。
>
> **工具**：`_p1131`（删空适配器）｜`_p1132`/`_p1133`（Qwen 下载）｜`_p1134`/`_p1135`（新 Qwen 运行器）｜`_p1136`（本条）。
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
    if MARK not in hp:
        i = hp.find("# 项目交接文档")
        j = hp.find("\n", i)
        hp = hp[: j + 1] + "\n" + ENT + hp[j + 1:]
        io.open(HANDOFF, "w", encoding="utf-8", newline="").write(hp)
        print("  handoff entry added")
    mp = io.open(REPO / "文件地图.md", encoding="utf-8").read()
    row = ("48. 🧹 **空适配器已删、Qwen 重测就绪（2026-10-17 11:05）** —— 删空 `.pt`：**本地 811 MB + 云端 773 MB**"
           "（删前逐个验证 `model tensors: 0`；12 条记录未动）。**重训 checkpoint 实测非空**：`448 tensors / 240 MB`，"
           "样例 `...q_proj.lora_A.default.weight` ⇒ `_p1115` 修复在真实运行中生效。**Qwen 重测**：昨天\"32 GB 装不下\""
           "的结论**可能不成立**——当时走 `output_hidden_states=True`，而该开关今天实测分配 **29.81 GiB**；"
           "已从修好的 `_p820` **重新生成** `_p1135_qwen_sites.py`（7 项断言全过，LLaVA 脚本未被污染），权重下载中（16.6 GB）。"
           "**💻 shell 经验**：PowerShell **7.6.7 + UTF-8**，但双引号里 `` ` `` 与 `$` 仍会被解释 ⇒ **内联命令一律用单引号包裹**。"
           "详见 `HANDOFF.md` 顶部 11:05 条目。\n")
    anchor = "47. 🚀 **重训 12 run 已启动"
    idx = mp.find(anchor)
    if idx >= 0:
        end = mp.find("\n", idx)
        mp = mp[: end + 1] + row + mp[end + 1:]
        io.open(REPO / "文件地图.md", "w", encoding="utf-8", newline="").write(mp)
        print("  map item added")

    # also capture the shell rule where it will be seen in future sessions
    for name in ("AGENTS.md", "CLAUDE.md"):
        f = REPO / name
        if not f.exists():
            continue
        t = io.open(f, encoding="utf-8").read()
        if "内联命令一律用单引号" in t:
            print(f"  {name}: shell rule already present")
            continue
        rule = ("\n## 💻 内联命令的引号规则（2026-10-17 立，工具 shell = PowerShell 7.6.7 + UTF-8）\n\n"
                "**编码已是 UTF-8，但双引号字面量里 `` ` `` 仍是转义符、`$` 仍是变量前缀** ⇒\n"
                "**内联命令（`python -c`、远端命令）一律用 PowerShell 单引号包裹**：\n\n"
                "```powershell\n"
                "python -c 'import re; print(len(re.findall(r\"\\d+\", s)))'   # 单引号：反引号/美元/双引号都原样\n"
                "```\n\n"
                "含正则、`$`、反引号、嵌套双引号时尤其必要；中文输出已正常。\n")
        io.open(f, "w", encoding="utf-8", newline="").write(t.rstrip("\n") + "\n" + rule)
        print(f"  {name}: shell quoting rule added")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
