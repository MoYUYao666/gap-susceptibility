# -*- coding: utf-8 -*-
r"""修 `Γ_m` 测量的余弦算法（2026-10-08）。

## 实测故障

```
both 臂 → RuntimeError: The size of tensor a (5262528) must match
          the size of tensor b (14494912)
```

**原因**：我把各侧梯度 `cat` 成**一个扁平向量**后算余弦——但
**视觉侧与语言侧的张量个数不同**（258 vs 392）→ 两个扁平向量长度不同 →
`cosine_similarity` 无法广播 → 报错。

**正确做法**：余弦**按张量逐元素求和**，不要求两侧长度相同：

    dot   = Σ_p ⟨g_m,p , g_tot,p⟩      （p 遍历「可训且两侧都有梯度」的参数）
    ‖g_m‖ = sqrt(Σ_p ⟨g_m,p , g_m,p⟩)
    ‖g_tot‖ = sqrt(Σ_p ⟨g_tot,p , g_tot,p⟩)
    cos   = dot / (‖g_m‖·‖g_tot‖)

**且必须按「参数身份」配对**（`zip` 两个有序列表），不能按顺序假设。

    python tools\_p55_fix_gamma_cos.py [--apply]
"""
from __future__ import annotations

import ast
import io
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
F = REPO / "tools" / "_p54_gamma_vlm.py"

OLD = '''        g_vis, g_txt = [], []
        for n, p in m.named_parameters():
            if not (p.requires_grad and p.grad is not None):
                continue
            if ".visual." in n:
                g_vis.append(p.grad.detach().float().flatten())
            elif "language_model" in n:
                g_txt.append(p.grad.detach().float().flatten())
        nv_ = float(torch.cat(g_vis).norm()) if g_vis else 0.0
        nt_ = float(torch.cat(g_txt).norm()) if g_txt else 0.0
        parts = [torch.cat(g_vis) if g_vis else None, torch.cat(g_txt) if g_txt else None]
        g_tot = torch.cat([x for x in parts if x is not None])
        cos_v = float(F.cosine_similarity(torch.cat(g_vis).unsqueeze(0), g_tot.unsqueeze(0))) if g_vis else float("nan")
        cos_t = float(F.cosine_similarity(torch.cat(g_txt).unsqueeze(0), g_tot.unsqueeze(0))) if g_txt else float("nan")'''

NEW = '''        # **按张量逐元素求和算余弦**：两侧张量个数不同（258 vs 392），
        # 不能先 cat 成扁平向量再算（实测会因长度不同报 RuntimeError）。
        grads = []          # [(name, grad_flat)]
        for n, p in m.named_parameters():
            if p.requires_grad and p.grad is not None:
                grads.append((n, p.grad.detach().float().flatten()))
        g_vis = [(n, g) for n, g in grads if ".visual." in n]
        g_txt = [(n, g) for n, g in grads if "language_model" in n]

        def _dot(a, b):
            return float(sum(torch.dot(x, y) for (_, x), (_, y) in zip(a, b)))

        def _selfdot(a):
            return _dot(a, a)

        nv_ = _selfdot(g_vis) ** 0.5 if g_vis else 0.0
        nt_ = _selfdot(g_txt) ** 0.5 if g_txt else 0.0
        tot = _selfdot(grads) ** 0.5
        cos_v = _dot(g_vis, [t for t in grads if ".visual." in t[0]]) / (nv_ * tot) \\
            if g_vis and tot > 0 else float("nan")
        cos_t = _dot(g_txt, [t for t in grads if "language_model" in t[0]]) / (nt_ * tot) \\
            if g_txt and tot > 0 else float("nan")'''

OLD2 = '''               "Gamma_vision": nv_ * cos_v if g_vis else 0.0,
               "Gamma_text": nt_ * cos_t if g_txt else 0.0,'''
NEW2 = '''               "Gamma_vision": (nv_ * cos_v) if g_vis else 0.0,
               "Gamma_text": (nt_ * cos_t) if g_txt else 0.0,
               # 单批的瞬时量；论文的 Γ_m 是轨迹平均——两者不等价，须在文档写明
               "note": "single-batch instantaneous grad; paper Gamma_m is trajectory-averaged",'''


def main() -> int:
    apply = "--apply" in sys.argv
    t = io.open(F, encoding="utf-8").read()
    if "按张量逐元素求和算余弦" in t:
        print("  已修，跳过")
        return 0
    for old, tag in ((OLD, "余弦算法"), (OLD2, "记录字段")):
        if t.count(old) != 1:
            print(f"  ❌ {tag} 未唯一命中（{t.count(old)}）")
            return 1
    t = t.replace(OLD, NEW, 1).replace(OLD2, NEW2, 1)
    ast.parse(t)
    if not apply:
        print("  （预演）")
        return 0
    io.open(F, "w", encoding="utf-8", newline="").write(t)
    t2 = io.open(F, encoding="utf-8").read()
    assert "按张量逐元素求和算余弦" in t2 and "trajectory-averaged" in t2
    print("  ✅ 已修：余弦按张量求和；并注明「单批瞬时 vs 轨迹平均」的区别")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
