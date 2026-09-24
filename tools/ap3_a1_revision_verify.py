"""最终复验：素材包改正/补充是否全部到位（用 raw string，避免转义坑）。"""
import sys

t = open('paper_a1/revision_additions.tex', encoding='utf-8', newline='').read()
checks = {
    'F1 表题已更新为 strictly LoRA-only': r'strictly LoRA-only fine-tuning' in t,
    'F1 epoch10 τ = 0.711': r'\textbf{0.711}' in t,
    'F1 epoch10 top-1 = 58.05': r'58.61 & 58.05' in t,
    'F1 epoch10 val = 2.364': r'2.472 & 2.364' in t,
    'F1 旧的"平台化"叙述已删': r'erodes monotonically over epochs' not in t,
    'F1 新的"两阶段"叙述': r'drops sharply at the final epoch' in t,
    'F2 块7 严格 LoRA 数字': r'0.833$ at' in t and r'$58.58 \to 58.05\%$' in t,
    'F2 块7 重建轨迹数字': r'0.767 \to 0.748' in t and r'58.86 \to 58.90\%' in t,
    'F2 旧的 0.76/0.73/0.71 已删': r'0.76$ at epoch 1' not in t,
    'F3 τ ≥ 0.930': r'\ge 0.930' in t,
    'F3 orth 变体区间': r'0.950$--$0.997' in t,
    'F3 旧的 above 0.93 已删': r'above $0.93$' not in t,
    'S2 Qwen 负 λ 行': r'0.434 & 0.574 & 0.730' in t,
    'S2 对称性叙述': r'symmetrically' in t,
    'S2 multicolumn 宽度已改 7': r'\multicolumn{7}{c}' in t,
    'S3 折大小披露': r'n_{\mathrm{test}} = 20' in t,
    'S4 高斯界边界': r'Gaussian surrogate' in t,
    '无重复的 tabular 结束': t.count(r'\end{tabular}') == t.count(r'\begin{tabular}'),
    '花括号平衡': t.count('{') == t.count('}'),
}
bad = [k for k, v in checks.items() if not v]
for k, v in checks.items():
    print(f'  {"OK  " if v else "FAIL"} {k}')
print(f'\n{len(checks) - len(bad)}/{len(checks)} 通过')
sys.exit(1 if bad else 0)
