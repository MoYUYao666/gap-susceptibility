# -*- coding: utf-8 -*-
r"""落账：PowerShell 往返毁非 ASCII 的教训 + 核实修复（2026-10-12）。

## 事件

上游成员为改报告里一个重复的小节编号，用了
`(Get-Content -Raw) -replace ... | Set-Content -Encoding utf8` ——
**PowerShell 以 GBK 读、以 UTF-8 写** → `tools/_p293e_report.py` 里**所有非 ASCII 字符双重编码**。
它用 `_p293n/o/p/q` 修复，并报告"影响范围为零"。

## 我的独立核实（`tools/_p394_encoding_damage.py`）

**收紧判据后**（只检双重编码特征 / `U+FFFD` / 私用区；**不检"mid-token `?`"**，
那个判据在上一版造成 43+ 个误报）：

| 文件 | 字符 | CJK | U+FFFD/私用区 | 双重编码 | 判定 |
|---|---|---|---|---|---|
| `docs/PR_MORE_MODELS.md` | 25,333 | 0 | 0 | 0 | ✅ |
| `tools/_p293e_report.py` | 46,652 | 0 | 0 | 0 | ✅ |
| `_p293n/o/p_repair*` | — | 0 | 0 | 0 | ✅ |

**全扫：442 个最近改动的文件干净；唯一"可疑"是我自己的检测脚本**（其正则定义自我匹配，假阳性）。

→ **上游"影响范围为零"的声明成立**（核实方式：字节级解码 + 特征扫描，非采信）。

## 建议加入流程规则（**比现有那条更普适**）

现有规则：*"不要用 PowerShell 拼含 `$` 的字符串"*。
**不足以覆盖这个坑** —— 危险的是**任何 `Get-Content -Raw | Set-Content` 往返**：
即使只改 ASCII 内容，它也会毁掉文件里**所有非 ASCII 字符**（按 GBK 读、按 UTF-8 写）。

**新规则**：
> **文件改写一律走 Python** `io.open(path, encoding='utf-8')` 读 + 写；
> **禁止** `Get-Content -Raw | Set-Content` 这类 PowerShell 读写往返，
> 无论被改内容是否含非 ASCII。

**并且**：改完必须**跑一次编码损伤扫描**（`tools/_p394_encoding_damage.py`），
判据为**双重编码特征 / `U+FFFD` / 私用区**，
**不要用"可疑问号"这类宽判据**（会造成大量误报，掩盖真问题）。
"""


def main() -> int:
    import sys
    if "--apply" not in sys.argv:
        print("  （预演）")
        return 0
    import io
    from pathlib import Path
    REPO = Path(__file__).resolve().parents[1]
    hp = REPO / "HANDOFF.md"
    t = io.open(hp, encoding="utf-8").read()
    if "PowerShell 往返毁非 ASCII" in t:
        print("  已记录")
        return 0
    ent = ("> **🧯 2026-10-12（续）—— 教训：`Get-Content -Raw | Set-Content` 往返会毁掉文件里"
           "**全部非 ASCII 字符**（按 GBK 读、UTF-8 写）；已核实修复且影响为零**\n>\n")
    for line in ENT.splitlines():
        ent += "> " + line + "\n" if line.strip() else ">\n"
    i = t.find("# 项目交接文档")
    j = t.find("\n", i)
    io.open(hp, "w", encoding="utf-8", newline="").write(t[:j + 1] + "\n" + ent + t[j + 1:])
    t2 = io.open(hp, encoding="utf-8").read()
    for k in ("PowerShell 往返毁非 ASCII", "25,333", "_p394_encoding_damage", "442"):
        print(f"  {'✅' if k in t2 else '🔴'} {k}")
    print(f"  HANDOFF 行数 = {len(t2.splitlines())}")
    return 0


ENT = r"""**事件**：上游成员为改报告里一个重复的小节编号，用了
`(Get-Content -Raw) -replace ... | Set-Content -Encoding utf8` ——
**PowerShell 以 GBK 读、以 UTF-8 写** → `tools/_p293e_report.py` 里**所有非 ASCII 字符双重编码**。
它用 `_p293n/o/p/q` 修复，并报告"影响范围为零"。

**我的独立核实**（`tools/_p394_encoding_damage.py`；**收紧判据**后 —— 只检双重编码特征 /
`U+FFFD` / 私用区，**不检"mid-token `?`"**，那个宽判据在上一版造成 **43+ 个误报**）

| 文件 | 字符 | CJK | U+FFFD/私用区 | 双重编码 | 判定 |
|---|---|---|---|---|---|
| `docs/PR_MORE_MODELS.md` | 25,333 | 0 | 0 | 0 | ✅ |
| `tools/_p293e_report.py` | 46,652 | 0 | 0 | 0 | ✅ |
| `_p293n/o/p_repair*` | — | 0 | 0 | 0 | ✅ |

**全扫：442 个最近改动的文件干净**；唯一"可疑"是**我自己的检测脚本**（其正则定义自我匹配，假阳性）。
→ **上游"影响范围为零"的声明成立**（核实方式：字节级解码 + 特征扫描，**非采信**）。

**建议加入流程规则（比现有那条更普适）**

现有规则 *"不要用 PowerShell 拼含 `$` 的字符串"* **不足以覆盖这个坑** ——
危险的是**任何 `Get-Content -Raw | Set-Content` 往返**：即使只改 ASCII 内容，
它也会毁掉文件里**所有非 ASCII 字符**。

> **新规则**：文件改写**一律走 Python** `io.open(path, encoding='utf-8')` 读 + 写；
> **禁止** `Get-Content -Raw | Set-Content` 这类 PowerShell 读写往返，**无论被改内容是否含非 ASCII**。
>
> **并且**：改完必须跑一次**编码损伤扫描**（`tools/_p394_encoding_damage.py`），
> 判据为**双重编码特征 / `U+FFFD` / 私用区**；
> **不要用"可疑问号"这类宽判据**（大量误报会掩盖真问题）。"""


if __name__ == "__main__":
    raise SystemExit(main())
