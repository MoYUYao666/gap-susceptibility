# 修改后核心逻辑自洽修复（3 处）
edits = [
    # 1. abstract：删 "full FT marginal α≈0"
    ('main_springer.tex',
     r"LoRA's protective bound ($\alpha<0$ for all ranks, in contrast to full fine-tuning's marginal $\alpha\approx 0$); and Effective Rank Saturation",
     r"LoRA's protective bound ($\alpha<0$ for all ranks and, in the matched-setting ODE fits, for full fine-tuning as well); and Effective Rank Saturation"),
    # 2. intro：删 "contrasted with full fine-tuning's marginal α≈0"
    ('sections/introduction.tex',
     r"LoRA's protective effect is captured by $\alpha < 0$ for all ranks contrasted with full fine-tuning's marginal $\alpha \approx 0$. The restoring coefficient",
     r"LoRA's protective effect is captured by $\alpha < 0$ for all ranks (and for full fine-tuning in the matched-setting fits). The restoring coefficient"),
    # 3. theory：Full FT 段重写为诚实版（DG* 动力学与 CG 度量区分）
    ('sections/theory.tex',
     r'\textbf{Full fine-tuning\'s catastrophic effect.} Section~\ref{sec:empirical} found that full fine-tuning explodes the gap (CG $+24\%$, zero-shot $-53.3\%$). In the ODE framework, full fine-tuning operates with a comparable restoring force ($\beta_{\text{full}} \approx 0.159$) but substantially altered gradient geometry. The perturbation force $\alpha$ involves contributions from \emph{all} parameters, including those most sensitive to alignment disruption. In contrast, PEFT constrains updates to low-rank subspaces, which is shown in Section~\ref{sec:validation} to yield consistently negative $\alpha$.',
     r'\textbf{Full fine-tuning\'s catastrophic effect.} Section~\ref{sec:empirical} found that full fine-tuning explodes the gap (CG $+24\%$, zero-shot $-53.3\%$). In the ODE framework, the fitted $DG^*$ dynamics of full fine-tuning are comparable to PEFT under matched settings ($\alpha_{\text{full}}=-0.040$, $\beta_{\text{full}}=0.159$), indicating that the first-order $DG^*$ dynamics do not by themselves distinguish full fine-tuning from PEFT. The catastrophic effect is instead captured by the empirical CG metric, which measures a different aspect of the distributional geometry; reconciling the two metrics is left to future work.'),
]
for f, old, new in edits:
    src = open(f, encoding='utf-8').read()
    if old in src:
        src = src.replace(old, new)
        open(f, 'w', encoding='utf-8').write(src)
        print('OK:', f)
    else:
        print('MISS:', f, '|', old[:70])
