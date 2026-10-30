"""把块 12 的 5 处措辞收窄落到投稿正文 main.tex（空白容忍匹配，跨行也能命中）。"""
import io
import re

P = 'paper_a1/main.tex'
s = io.open(P, encoding='utf-8').read()

PAIRS = [
    # 1) 摘要：把"universal health indicator"降为"diagnostic / 常被隐含读作质量代理"
    (
        "The modality gap---the separation between image and text embedding clusters---is widely treated as a universal health indicator of cross-modal alignment: narrowing it is an explicit objective in method design, and gap-based quantities predict retrieval degradation.",
        "The modality gap is widely used as a \\emph{diagnostic} quantity for cross-modal alignment and retrieval, and is often read \\emph{implicitly} as a proxy for representation quality: narrowing it is an explicit objective in method design, and gap-based quantities predict retrieval degradation. We show that this implicit quality-proxy reading does not extend to zero-shot classification.",
    ),
    # 2) 引言：de facto health indicator -> 诊断量/隐含质量代理 + 明确我们质疑的是"无条件"读法
    (
        "Because the gap is measurable and interpretable, it has become a de facto health indicator: methods explicitly optimize gap reduction, gap change predicts retrieval degradation, and gap-aware early stopping has been proposed as a training-time signal.",
        "Because the gap is measurable and interpretable, it is widely used as a diagnostic of alignment and retrieval and is often read implicitly as a quality proxy: methods explicitly optimize gap reduction, gap change predicts retrieval degradation, and gap-aware early stopping has been proposed as a training-time signal. What we dispute is the \\emph{unconditional} form of that reading, not its usefulness for alignment and retrieval.",
    ),
    # 3) 摘要（推荐句）：收窄到实际测过的模型族与基准
    (
        "and recommend $\\tau$ as the monitoring signal for classification-oriented fine-tuning, reserving the gap for retrieval-oriented tasks.",
        "and, for the model families and benchmarks tested here (CLIP ViT-B/32, OpenCLIP laion2B and SigLIP base-patch16-224, ImageNet-1K zero-shot classification, adaptation by LoRA or full fine-tuning on Flickr30k), identify $\\tau$ as the more informative monitoring signal for classification-oriented fine-tuning, reserving the gap for retrieval-oriented tasks. We do not claim this for other encoder families, other benchmarks, or adaptation mechanisms outside those measured here.",
    ),
    # 4) 讨论：the right signal -> the more informative of the two signals（限定"我们测的设置"）
    (
        "for classification-oriented adaptation, order preservation $\\tau$ is the right signal",
        "for classification-oriented adaptation in the settings we test, order preservation $\\tau$ is the more informative of the two signals",
    ),
    # 5) 结论：收窄 + 加"族校准"边界（R²/ Spearman 为已有 JSON 数字）
    (
        "We recommend $\\tau$ as the monitoring signal for classification-oriented fine-tuning and reserve the gap for retrieval.",
        "In the settings tested here we find $\\tau$ to be the more informative monitoring signal for classification-oriented fine-tuning, and reserve the gap for retrieval. Because the cross-family mapping is family-calibrated ($R^2$ $0.371$/$0.378$ with pooled Spearman $0.927$), we recommend $\\tau$ as an \\emph{ordering} proxy rather than as a calibrated accuracy predictor.",
    ),
]

ok = 0
for i, (old, new) in enumerate(PAIRS, 1):
    pat = re.compile(r'\s+'.join(re.escape(t) for t in old.split()), flags=re.S)
    hits = pat.findall(s)
    if len(hits) == 1:
        s = pat.sub(lambda m: new, s, count=1)
        print('  [%d] 命中并替换 ✓' % i)
        ok += 1
    else:
        print('  [%d] 命中 %d 次 → 未替换（需人工确认）' % (i, len(hits)))

if ok:
    io.open(P, 'w', encoding='utf-8').write(s)
    print('已写回 %s（成功 %d/5）' % (P, ok))
