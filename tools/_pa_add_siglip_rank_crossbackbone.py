# -*- coding: utf-8 -*-
r"""把 SigLIP 的跨骨干 rank 确认写进正文（2026-10-04）。

## 数据（严格冻结，text_only 臂；已核对）

### CLIP ViT-B/32（6 个 rank）

| rank | 1 | 4 | 8 | 16 | 32 | 64 |
|---|---|---|---|---|---|---|
| $\Delta$CG | −0.0091 | −0.0285 | −0.0465 | −0.0598 | −0.0754 | −0.0754 |
| $R@1$ | 0.614 | 0.618 | 0.624 | 0.628 | 0.633 | 0.639 |

**单调递减**（rank 越高降间隙越多），$r{=}32$ 后饱和。

### CLIP ViT-B/32（both 臂）

| rank | 1 | 4 | 8 | 16 | 32 | 64 |
|---|---|---|---|---|---|---|
| $\Delta$CG | −0.0004 | −0.0184 | **−0.0258** | −0.0149 | −0.0032 | **+0.0179** |

**U 形**（最优在 $r{=}8$ 附近，$r{=}64$ 转正）。

### SigLIP ViT-B/16（text_only，r4 vs r8）

配对差 **+0.0166 ± 0.0098**，配对 **t = +3.79**，5/5 同向；
CLIP 同口径为 **+0.0192**，**t = +7.96**。

**→ 两骨干方向一致**（rank 升高都使间隔降得更多）→ **「协议依赖」的结论跨骨干成立**。

## 修正记录

我在中途曾误读这两个数字为"方向相反"（把 CLIP 的"更负"与 SigLIP 的"更小"当成不同方向），
并据此说过"rank 方向依骨干反转"——**配对检验推翻了这个说法**。该错误**未写进稿件**。

    python tools\_pa_add_siglip_rank_crossbackbone.py [--apply]
"""
from __future__ import annotations

import io
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
F = REPO / "paper合" / "sections" / "empirical.tex"

OLD = ("Under strict freezing, where the optimiser sees only the adapter matrices, the text-only arm "
       "improves monotonically with rank instead, reaching $-0.075$ at $r{=}32$ against $-0.029$ at "
       "$r{=}4$. The rule is therefore an artefact of what else was being trained, not a property of rank.")

NEW = ("Under strict freezing, where the optimiser sees only the adapter matrices, the text-only arm "
       "improves monotonically with rank instead, reaching $-0.075$ at $r{=}32$ against $-0.009$ at "
       "$r{=}1$ and $-0.029$ at $r{=}4$, and the both-position arm is non-monotonic, turning positive by "
       "$r{=}64$. The rule is therefore an artefact of what else was being trained, not a property of "
       "rank. This one does carry across backbones: on SigLIP the same ordering appears, with rank~$8$ "
       "reducing the gap relative to rank~$4$ by $+0.017$ over five paired seeds ($t = +3.8$), against "
       "$+0.019$ on CLIP ($t = +8.0$).")


def main() -> int:
    apply = "--apply" in sys.argv
    t = io.open(F, encoding="utf-8").read()
    c = t.count(OLD)
    if c != 1:
        print(f"  ⚠ 未唯一命中（{c} 次）")
        return 1
    print("  ✅ 命中设计模式②的 strict-freezing 句")
    if apply:
        io.open(F, "w", encoding="utf-8", newline="").write(t.replace(OLD, NEW, 1))
        t2 = io.open(F, encoding="utf-8").read()
        for k in ("$-0.009$ at $r{=}1$", "SigLIP the same ordering", "t = +3.8"):
            assert k in t2, f"断言失败：缺 {k}"
        assert "non-monotonic" in t2
        print("  ✅ 已写入跨骨干确认并断言通过")
    else:
        print("  （预演）")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
