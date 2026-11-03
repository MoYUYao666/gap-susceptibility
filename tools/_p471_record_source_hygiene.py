# -*- coding: utf-8 -*-
r"""落账：来源卫生自查（派生聚合指纹 + 逐 run 自带超参）+ 守卫双向验证规则（2026-10-13）。

    python tools\_p471_record_source_hygiene.py [--apply]
"""
from __future__ import annotations

import argparse
import io
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]

ENT = """> **🔐 2026-10-13 08:20 —— 来源卫生自查：**派生聚合加 sha256 指纹 + 逐 run 自带超参**；并新增"守卫必须双向验证"规则**
>
> ### 一、我转达的规则在 `p3-downstream` 处**确实成立**，两处真实风险（它自己查出）
>
> | 风险 | 实况 | 处置 |
> |---|---|---|
> | **顶层 `protocol` 每次调用被重写** | `_p461`/`_p464` 的训练超参**只写顶层** ⇒ 续跑若改超参，**旧 run 被静默误标** | 逐 run **自带超参**（回填 79+43+4 条）+ `train_spec` + **共有核心键不一致则硬失败** |
> | **`_p472` rows 覆盖式合并** | 按 `max_pixels` 合并 ⇒ **换设备重跑会静默替换旧行**（CPU↔GPU bf16 $E_0$ 差 **0.09%**：21771.7 vs 21751.8） | 逐行加 **`device`** + **设备一致性守卫** |
>
> ### 二、✅ 我独立核实（`tools/_p469`、`_p470`）
>
> **逐 run 自带超参**：
> - `p3d_clip_ranksweep.json`（79 run）：`batch/device/epochs/lr/n_train` ✅
> - `p3d_qwen_ranksweep.json`（43 run）：`+dtype/lora_targets/max_pixels/min_pixels` ✅
> - `p3d_qwen_ranksweep_mp50176.json`（4 run）：同上 ✅
> - `p3d_e0_vs_token_budget_*.json` **三个文件逐行都带 `device`** ✅
>
> **`source_fingerprint` 的 sha256 逐位一致**：
>
> | summary | 指向源文件 | 记录 | 实际 | 条数 |
> |---|---|---|---|---|
> | `p3d_summary.json` | `p3d_clip_ranksweep.json` | `0cf8e8729c276f90f709f49fddfdd323…` | **同** ✅ | 79 / 79 ✅ |
> | `p3d_qwen_summary.json` | `p3d_qwen_ranksweep.json` | `4022cc68b8417277f274cc54062e9484…` | **同** ✅ | 43 / 43 ✅ |
>
> **`device={cpu:1, cuda:42}` 是设计如此**：唯一 cpu run 是 **`condition=real, rank=0`（冻结基线，无 `delta_E`）**，
> 42 个 cuda 是训练 run。**⇒ 设备守卫的例外有明确依据。**
>
> ### 三、⚠️ 我的第 21 个错（检查写法）
>
> 我第一版检查把 `source_fingerprint` 当成"文件名 → 元数据"的**映射**去遍历，
> 但它是**扁平结构** `{"file":…, "sha256":…, "n_runs":…}` ⇒ 我把 `file`/`sha256`/`n_runs`
> **当成了文件名** ⇒ **假报"源文件不在"**。已由 `tools/_p470` 修正并逐位核对通过。
> **⇒ 又是"判据/检查串写错"（本阶段同类错误已多次）。**
>
> ### 四、⭐ 新增流程规则：**守卫必须双向验证**
>
> 成员自查发现：它的**守卫第一版写成"整体比较 `train_spec`"** ⇒ 实测会
> **把"参数完全相同、只是 spec 键集不同"的合法续跑也拒掉**（**假阳性**）。
> 改成**只比对共有核心键**后，**两个方向都实测**：
> - 不同预算指向同一归档 → `exit 1` + 明确列出差异键
> - **8 个共有核心键全同** → 打印 `来源校验通过（比对 8 个共有超参键）`、`exit 0`，正常续跑
>
> > **规则：防"静默误标"的守卫很容易做成"把正常操作也堵死"，
> > 必须双向验证（该拒的拒、该放的放），否则守卫本身会成为新的事故源。**
>
> **依据**：本条与"随机对照污染""归档键名漂移""聚合产物当来源"同源 —— **都是"机制的边界没有被检验"**。
> **已要求转达 `p3-allocation`**（它同样在写归档）。
>
> ### 五、成员报备的一处"弄巧成拙"（诚实，我认可）
>
> 它为测守卫用 `--max-pixels 99999` 跑了一次 —— 但**该参数会把输出重定向到新归档**，
> 守卫因此**正确地无从比较**（新文件里没有可比对的旧 spec），于是**意外启动了一次 CPU 上的真实训练**
> （吃 ~4600 s CPU，**已 kill，未产生任何归档**）。
> **它的定性正确**："**不是守卫失效，是我测试设计错了**"（换预算 = 换归档，守卫本就无从比较）。
> **⇒ 已改用"同预算指同一归档"重测，两个方向都拿到确认。**
>
> ### 六、`p3-downstream` 的其余交付我确认
>
> - **归属口径**已逐项写进 §3.3.2（谁测的/什么预算/哪批样本/哪个口径/归档字段），
>   并加红字：**论文只跑 blank、无 real 对照 ⇒ 不得写成"论文的 gap 是 3.09×"**，附 "we measured…" 建议措辞
> - **重复归档**由 `_p473` **逐行比对确认被完全覆盖后**才删除（**不是凭文件名删**）；
>   n=2 曲线补全为 4 点，**消掉了报告里唯一一个未归档数字**
> - **576 档不补 seed**（$E_0$ 前向确定性 ⇒ 单次即精确值）✅
>
> ### 七、状态
>
> - **P1 ✅ 完成**｜**P3(AdaLoRA) ✅ 跑完**（不可比）｜**P2 🔄**（≈09:50）→ **AdaLoRA lr ≈18 min**
> - **门禁**：`_p466` **91/91**｜`_p471` 编码 **14/14**
> - **P3 稿件**：**14 页** / 0 错 / 0 未定义；**累计修 23 处**
> - **转达**：`只增不改` 与 `守卫双向验证` 两条规则已发给另两个成员
"""


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    a = ap.parse_args()
    if not a.apply:
        print("  （预演）")
        return 0
    hp = REPO / "HANDOFF.md"
    t = io.open(hp, encoding="utf-8").read()
    if "来源卫生自查" in t:
        print("  已记录")
        return 0
    i = t.find("# 项目交接文档")
    j = t.find("\n", i)
    io.open(hp, "w", encoding="utf-8", newline="").write(t[:j + 1] + "\n" + ENT + t[j + 1:])
    t2 = io.open(hp, encoding="utf-8").read()
    for k in ("来源卫生自查", "0cf8e872", "4022cc68", "守卫必须双向验证", "cpu:1, cuda:42"):
        print(f"  {'✅' if k in t2 else '🔴'} {k}")
    print(f"  HANDOFF 行数 = {len(t2.splitlines())}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
