# -*- coding: utf-8 -*-
"""Mark the Huang citation as resolved in the log and HANDOFF."""
import io
import os

ROOT = r"D:\Realdesktop\Wan\Important\New"

LOG = os.path.join(ROOT, "docs", "P1_REMEDIATION_LOG.md")
OLD_LOG = '- **Huang et al. ICCV 2025 引用仍缺**'
NEW_LOG = ('- **Huang et al. ICCV 2025 引用已补**（操作者 2026-09-20 提供确切 bibtex）：新增条目 '
           '`huang2025mindgap`（Huang, Cao, Lu, Meng, Yang, Liu；ICCV 2025, pp. 3777--3786），'
           '插在 `hu2021lora` 之后保持字母序；引用两处——`related_work.tex` §2.1'
           '（"the gap has become an object of intervention rather than only of analysis"）与 '
           '`introduction.tex` 的定位句（他们作用于 gap，本文刻画 gap 对"在哪一侧/多大规模/什么秩"'
           '的响应）。重建后参考文献 [11]、0 undefined、43 页。**此项关闭。**\n'
           '<!-- 原记录：~~Huang et al. ICCV 2025 引用仍缺~~')
s = io.open(LOG, encoding="utf-8").read()
if OLD_LOG in s:
    s = s.replace(OLD_LOG, NEW_LOG, 1)
    if "此项关闭。" in s and "~~Huang" not in s:
        pass
    io.open(LOG, "w", encoding="utf-8", newline="").write(s)
    print("log updated")
else:
    print("log bullet not found (already updated?)")

H = os.path.join(ROOT, "HANDOFF.md")
OLD_H = '② 补引 **Huang et al. ICCV 2025 "Mind the Gap"**（威胁 "first systematic study"，需 VPN 关闭后取作者列表，`web_fetch` 现被劫持 DNS 挡住）；'
NEW_H = '② ✅ **Huang et al. ICCV 2025 已补引**（`huang2025mindgap`，pp. 3777--3786；§2.1 与 intro 定位句各一处，参考文献 [11]）；'
h = io.open(H, encoding="utf-8").read()
if OLD_H in h:
    io.open(H, "w", encoding="utf-8", newline="").write(h.replace(OLD_H, NEW_H, 1))
    print("handoff updated")
else:
    print("handoff item not found (already updated?)")
