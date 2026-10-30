# 跨方法对比表格

> 自动生成于 Phase 5 分析

## 计算效率对比

| 方法 | CG Δ (mean) | R@1 (mean) | Params | 实验数 |
|------|:---:|:---:|:---:|:---:|
| adapter | -0.0472 | 0.6228 | 145170177 | 5 |
| full_ft | 0.1994 | 0.527 | 151277313 | 2 |
| lora | -0.0038 | 0.6692 | 135974145 | 56 |

## Pareto 前沿 (Gap-Performance)

| 实验 | 方法 | CG Δ | R@1 |
|------|------|:---:|:---:|
| flickr30k/alpha_64 | adapter | -0.0808 | 0.637 |
| flickr30k/modules_qvko | lora | -0.0666 | 0.641 |
| null_lora_r8/null_lora_r8 | lora | -0.038 | 0.691 |
| flickr30k/null_lora_r8 | lora | -0.038 | 0.691 |
| flickr30k/rq3_img_drop_50 | lora | -0.0327 | 0.699 |
| flickr30k/rq2_both | lora | -0.0324 | 0.7 |
| rq2_both/rq2_both | lora | -0.0324 | 0.7 |
| flickr30k/rq1_rank16 | lora | -0.0199 | 0.702 |
| rq1_rank16/rq1_rank16 | lora | -0.0199 | 0.702 |
| rq1_rank32/seed456 | lora | -0.0034 | 0.72 |

## 综合排名 Top 10

| 排名 | 实验 | 方法 | Score | CG Δ | R@1 |
|:---:|------|------|:---:|:---:|:---:|
| 1 | gap_init_r4/gap_init_r4 | lora | 0.2274 | -0.030626 | 0.694 |
| 2 | flickr30k/gap_init_r4 | lora | 0.2435 | -0.030626 | 0.694 |
| 3 | null_lora_r8/null_lora_r8 | lora | 0.2435 | -0.03801 | 0.691 |
| 4 | flickr30k/rq2_both | lora | 0.2435 | -0.032387 | 0.7 |
| 5 | flickr30k/null_lora_r8 | lora | 0.2597 | -0.03801 | 0.691 |
| 6 | rq2_both/rq2_both | lora | 0.2597 | -0.032387 | 0.7 |
| 7 | flickr30k/rq3_img_drop_50 | lora | 0.271 | -0.032684 | 0.699 |
| 8 | flickr30k/rq3_complete | lora | 0.3258 | -0.036419 | 0.687 |
| 9 | flickr30k/rq1_rank8 | lora | 0.3419 | -0.030391 | 0.687 |
| 10 | flickr30k/rq3_img_drop_10 | lora | 0.3484 | -0.037287 | 0.683 |