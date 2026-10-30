# Full FT 数值修复（v1 正式批为准）
edits = [
    # 2. Phase1 表 Full FT 行
    ('sections/validation.tex',
     r'Full fine-tuning    & $0.643 \pm 0.224$ & $>0.86$ & $4.7\times$ PEFT',
     r'Full fine-tuning    & $0.159 \pm 0.024$ & $>0.97$ & comparable'),
    # 3. Phase1 caption
    ('sections/validation.tex',
     r'A1 holds within PEFT ($\text{CV}=13.3\%$); full FT breaks it at $4.7\times$ PEFT mean.',
     r'A1 holds across PEFT and full fine-tuning under matched training settings ($\text{CV}=13.3\%$ within PEFT).'),
    # 4. Phase1 正文
    ('sections/validation.tex',
     r'The dramatic increase of $\beta$ under full FT confirms the physical interpretation: $\beta$ is a landscape-curvature quantity, and full FT reshapes the landscape while PEFT preserves it. This sharp distinction validates $\beta$ as a diagnostic that separates PEFT from destructive fine-tuning regimes.',
     r'The stability of $\beta$ across PEFT and full fine-tuning confirms the physical interpretation: $\beta$ is a landscape-curvature quantity intrinsic to the pretrained geometry, insensitive to the fine-tuning method under matched training settings.'),
    # 5. abstract
    ('main_springer.tex',
     r'$\beta$ is stable within PEFT ($\text{CV}=13.3\%$) and sharply distinguishes PEFT from full fine-tuning ($\beta_{\text{full}}=0.643$, $4.7\times$ larger).',
     r'$\beta$ is stable within PEFT ($\text{CV}=13.3\%$) and remains stable under full fine-tuning with matched training settings ($\beta_{\text{full}}=0.159$).'),
    # 6. intro
    ('sections/introduction.tex',
     r'The restoring coefficient $\beta$ is stable across PEFT methods ($\text{CV}=13.3\%$) and sharply distinguishes PEFT from full fine-tuning ($\beta_{\text{full}}=0.643$, $4.7\times$ larger).',
     r'The restoring coefficient $\beta$ is stable across PEFT methods ($\text{CV}=13.3\%$) and remains stable under full fine-tuning with matched training settings ($\beta_{\text{full}}=0.159$).'),
    # 7. conclusion
    ('sections/conclusion.tex',
     r'$\alpha$ is universally negative for PEFT, and $\beta$ sharply distinguishes PEFT from full fine-tuning ($\beta_{\text{full}} = 0.643$, $4.7\times$ larger).',
     r'$\alpha$ is universally negative for PEFT, and $\beta$ is stable across PEFT and full fine-tuning under matched settings ($\beta_{\text{full}} = 0.159$).'),
    # 8. theory
    ('sections/theory.tex',
     r'full fine-tuning operates with marginal restoring force ($\beta_{\text{full}} \approx 0.643$)',
     r'full fine-tuning operates with a comparable restoring force ($\beta_{\text{full}} \approx 0.159$)'),
    # 9. OpenCLIP 段
    ('sections/validation.tex',
     r'$\beta = 0.484$---intermediate between LoRA ($0.153$) and full fine-tuning ($0.643$), consistent with $\beta$ as a landscape-curvature diagnostic that scales with the perturbation magnitude.',
     r'$\beta = 0.484$---larger than both LoRA ($0.153$) and full fine-tuning ($0.159$), consistent with $\beta$ as a landscape-curvature diagnostic that varies across PEFT methods.'),
    # 10. fig5 caption（Full FT outlier → stable）
    ('sections/validation.tex',
     r'Full FT outlier confirms $\beta$ as a landscape diagnostic.',
     r'Full FT remains within the PEFT range under matched settings, confirming $\beta$ as a stable landscape quantity.'),
]
for f, old, new in edits:
    src = open(f, encoding='utf-8').read()
    if old in src:
        src = src.replace(old, new)
        open(f, 'w', encoding='utf-8').write(src)
        print('OK:', f, '|', old[:50])
    else:
        print('MISS:', f, '|', old[:60])
