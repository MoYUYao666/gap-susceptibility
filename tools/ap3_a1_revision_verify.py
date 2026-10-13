"""Final re-verification: whether all corrections/additions in the material package are in place (uses raw strings to avoid escaping pitfalls)."""
import sys

t = open('paper_a1/revision_additions.tex', encoding='utf-8', newline='').read()
checks = {
    'F1 caption updated to strictly LoRA-only': r'strictly LoRA-only fine-tuning' in t,
    'F1 epoch10 tau = 0.711': r'\textbf{0.711}' in t,
    'F1 epoch10 top-1 = 58.05': r'58.61 & 58.05' in t,
    'F1 epoch10 val = 2.364': r'2.472 & 2.364' in t,
    'F1 old "plateau" narrative removed': r'erodes monotonically over epochs' not in t,
    'F1 new "two-stage" narrative': r'drops sharply at the final epoch' in t,
    'F2 block 7 strict-LoRA numbers': r'0.833$ at' in t and r'$58.58 \to 58.05\%$' in t,
    'F2 block 7 reconstruction-trajectory numbers': r'0.767 \to 0.748' in t and r'58.86 \to 58.90\%' in t,
    'F2 old 0.76/0.73/0.71 removed': r'0.76$ at epoch 1' not in t,
    'F3 tau >= 0.930': r'\ge 0.930' in t,
    'F3 orth variant interval': r'0.950$--$0.997' in t,
    'F3 old "above 0.93" removed': r'above $0.93$' not in t,
    'S2 Qwen negative-lambda row': r'0.434 & 0.574 & 0.730' in t,
    'S2 symmetry narrative': r'symmetrically' in t,
    'S2 multicolumn width changed to 7': r'\multicolumn{7}{c}' in t,
    'S3 fold-size disclosure': r'n_{\mathrm{test}} = 20' in t,
    'S4 Gaussian-bound edge case': r'Gaussian surrogate' in t,
    'no duplicated tabular end': t.count(r'\end{tabular}') == t.count(r'\begin{tabular}'),
    'brace balance': t.count('{') == t.count('}'),
}
bad = [k for k, v in checks.items() if not v]
for k, v in checks.items():
    print(f'  {"OK  " if v else "FAIL"} {k}')
print(f'\n{len(checks) - len(bad)}/{len(checks)} passed')
sys.exit(1 if bad else 0)
