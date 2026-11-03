"""A1 素材包补丁 v2：用锚点切片替换（对源码换行鲁棒），完成剩余 3 处。"""
import sys

P = 'paper_a1/revision_additions.tex'
src = open(P, encoding='utf-8', newline='').read()


def splice(tag, start_anchor, end_anchor, new_text):
    """把 [start_anchor, end_anchor 结尾] 之间的整段替换为 new_text。"""
    global src
    i = src.find(start_anchor)
    j = src.find(end_anchor, i) if i >= 0 else -1
    if i < 0 or j < 0:
        print(f'  FAIL {tag}: anchor 未找到 (start={i}, end={j})')
        return False
    j += len(end_anchor)
    old = src[i:j]
    src = src[:i] + new_text + src[j:]
    print(f'  OK   {tag}: 替换 {len(old)} 字节 → {len(new_text)} 字节')
    return True


ok = []

# ---------- F1e：早停表的叙述段 ----------
ok.append(splice(
    'F1e 早停叙述',
    'erodes monotonically over epochs 1--3',
    'classification-oriented fine-tuning.',
    'erodes slowly over epochs 1--5 ($0.833\\to 0.823$, a $1.2\\%$ loss) and then\r\n'
    '\\emph{drops sharply at the final epoch} ($0.823\\to 0.711$, $13.6\\%$), while\r\n'
    'zero-shot top-1 is inert throughout ($58.05$--$58.61\\%$, a range of $0.56$\r\n'
    'points) and the validation loss moves in the \\emph{opposite} direction at the\r\n'
    'endpoint ($2.472\\to 2.364$): the model fits the fine-tuning distribution better\r\n'
    'exactly when order preservation falls. The endpoint is therefore the informative\r\n'
    'one --- $\\tau$ registers a change that neither top-1 nor the validation loss\r\n'
    'reports as a loss of zero-shot quality --- and it is the same run whose\r\n'
    '$\\lambda_{\\mathrm{reg}}=0$ endpoint ($58.1\\%$, $\\tau = 0.711$) appears in the\r\n'
    'dose--response block above, so the two blocks describe one trajectory. Direction\r\n'
    'consistent with the retrain trajectory of Section~\\ref{sec:traj}, where the\r\n'
    'erosion was larger.'))

# ---------- F2：块 7 ----------
ok.append(splice(
    'F2 块7 数字',
    'The retrain checkpoints of',
    'is the earliest erosion signal, top-1 is inert.',
    'The retrain checkpoints of Section~\\ref{sec:traj} archive the LoRA adapter\r\n'
    'weights only. Two re-evaluations bound the protocol dependence. (a) Strictly\r\n'
    'LoRA-only re-training --- the dose--response script selects trainable\r\n'
    'parameters by name (the \\texttt{lora\\_} prefix), so it cannot update\r\n'
    'embeddings or LayerNorms and is a strict test --- gives $\\tau = 0.833$ at\r\n'
    'epoch 1, $0.823$ at epoch 3 and $0.711$ at epoch 10, with top-1\r\n'
    '$58.58 \\to 58.05\\%$ (Table~\\ref{tab:earlystop};\r\n'
    '\\texttt{a1\\_class\\_aligned/lr0.0/seed42}). (b) Evaluating the archived\r\n'
    'submitted checkpoints (LoRA-component reconstruction, 5000-image sample)\r\n'
    'gives $\\tau = 0.767 \\to 0.748$ and top-1 $58.86 \\to 58.90\\%$\r\n'
    '(\\texttt{a1\\_tau\\_trajectory.json}). The two protocols place the $\\tau$\r\n'
    'level at $0.71$--$0.83$ and $0.75$--$0.77$ respectively, but agree on the\r\n'
    'conclusion: $\\tau$ is the earliest erosion signal, top-1 is inert.'))

# ---------- F3：DINOv2 措辞 ----------
ok.append(splice(
    'F3 DINOv2 措辞',
    'under the same surgery grid,',
    'even where CG shrinks to $0.001$.',
    'under the same surgery grid and in \\emph{both} variants (gap-direction and\r\n'
    'orthogonal, magnitude-matched), $\\tau \\ge 0.930$ at every $\\lambda$\r\n'
    'including $\\lambda = 4$ ($0.930$--$0.995$ for the gap direction,\r\n'
    '$0.950$--$0.997$ for the orthogonal one) and nearest-prototype top-1 stays\r\n'
    'inside $48.18$--$48.26\\%$, even where CG shrinks to $0.001$.'))

if all(ok):
    open(P, 'w', encoding='utf-8', newline='').write(src)
    print(f'\n全部完成；文件 {len(src)} 字节')
else:
    print('\n有未完成项，未写盘')
sys.exit(0 if all(ok) else 1)
