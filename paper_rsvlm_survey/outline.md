# Outline: vision-language models for remote sensing

Working title: **Vision-language models for remote sensing: a survey of pretraining, adaptation and evaluation**

The survey's thesis, stated up front so every section has a job: *remote sensing is not just another image domain; the
overhead geometry, multi-sensor heterogeneity and geographic leakage between splits change what a vision-language model
learns and how it must be evaluated.* Sections 3-6 each supply evidence for one part of that sentence.

## 1. Introduction
- why RS-VLMs matter (archives grew, labels are scarce, text is cheap);
- what is different from natural-image VLMs: overhead viewpoint, scale, season/time, sensor mix (optical, SAR, multispectral);
- contributions and the taxonomy used in the rest of the paper.

## 2. Foundations
- contrastive image-text pretraining (CLIP, SigLIP, OpenCLIP) and what transfers;
- RS-specific pretraining (SSL, masked reconstruction, geo-aware encoders);
- multimodal large language models and instruction tuning;
- the gap between natural-image and RS feature spaces (cite the mechanism evidence, not just the observation).

## 3. Datasets and benchmarks (a table, with access route and size for each)
- classification and scene understanding; image-text retrieval; captioning; visual question answering; grounding and
  referring; language-guided segmentation; change detection with language;
- licence/access notes and known quality problems (templated captions, machine-generated text, class imbalance).

## 4. Pretraining recipes for RS vision-language models
- synthetic caption generation from metadata and segmentation maps;
- single-sensor vs multi-sensor pretraining; SAR-optical alignment;
- scale and resolution handling; temporal pairing.

## 5. Adaptation strategies
- full fine-tuning, linear probing, adapters, LoRA and where to place it (vision tower, text tower, both);
- prompt and instruction tuning; zero-shot transfer;
- compute/accuracy trade-offs, with an explicit table of reported numbers and their budgets.

## 6. Evaluation and its pitfalls
- metrics used per task; what they do and do not measure;
- geographic leakage and same-region splits; near-duplicate tiles; caption templating inflating scores;
- reporting practice: seeds, confidence intervals, compute disclosure.

## 7. Open problems
- cross-sensor and cross-resolution generalisation; physics-informed conditioning; uncertainty;
- data governance and licensing; reproducible benchmarks with geographic separation;
- evaluation as a first-class contribution.

## 8. Conclusion

## Reference integrity appendix
- corpus size, query themes, verification rate, date of verification, and the exact commands that regenerate it.
