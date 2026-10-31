# A23 — anticipated reviewer objections and prepared evidence (2026-10-19)

> For the JOE revision round. Archives: `outputs/analysis/a23_threshold_transfer.json`, `a23_certificate_control.json`,
> `outputs/ocean_*`, `outputs/sonar_*`.

| # | Likely objection | Prepared answer | Evidence |
|---|---|---|---|
| 1 | "A gap threshold cannot be trusted; it is scale-dependent." | We now measure it: a threshold fitted on one domain reaches balanced accuracy $0.83$ in domain but $0.25$--$0.67$ on the other archived domain-model arms (chance $0.50$), in both directions. The paper states the within-domain scope explicitly. | `a23_threshold_transfer.json`; new paragraph in `ext_partII_domains.tex` |
| 2 | "The surgery is one-sided." | The archive contains both directions: image-side translations at twelve amplitudes and text-side translation at $\lambda=1.0$ for the frozen and fine-tuned sonar models. The asymmetry claim is therefore not an artefact of intervening on one side only. | `sonar_protocol.json` rows; memo |
| 3 | "You criticise the gap but propose nothing." | The paper's contribution is diagnostic (order preservation / task spectrum); a positive certificate (margin mass) was tested on a generic CLIP control and **saturated** at that operating point, because the statistic is the margin CDF evaluated at $2\varepsilon$ and the frozen margin bulk lies below $0.02$ CLIP-score units; the 59.1%-accurate ImageNet-5k reference saturates identically for $\varepsilon\ge0.05$, so this is a property of the resolution, not of accuracy. We report that as a negative control rather than dressing it up. | `a23_certificate_control.json`; memo |
| 4 | "Five domains, but the sonar domain is one dataset." | Stated as a limitation: one acoustic dataset (NKSID, Bohai Bay) and one water-tank control; the domain-independent claim is restricted to what the matrix covers. | `ext_partII_domains.tex` |
| 5 | "The five-domain matrix reuses one evaluation protocol, so it cannot detect protocol dependence." | The within-domain/cross-domain threshold result is exactly that protocol-dependence check, now included. | threshold transfer paragraph |
| 6 | "The gap and accuracy dissociate — why keep the gap at all?" | The paper keeps the gap as a *descriptive* fingerprint and uses order preservation as the decision variable; the task-sensitivity hierarchy is the claim, not gap-as-health. | `ext_partI_theory.tex`, §spectrum |
| 7 | "Nine font-substitution warnings suggest a broken build." | They are IEEEtran small-caps-italic substitutions (`OT1/ptm/m/scit` → `it`), a cosmetic style fallback with no visual defect; recorded as accepted, not fixed. | `main_ieee.log` |
| 8 | "The added threshold numbers are new claims without source." | Every number is in `outputs/analysis/a23_threshold_transfer.json`, computed by `tools/_p1345_a23_threshold_transfer.py` from the archived domain rows. | script + archive |

## A23 upgrade memo (2026-10-19)

- **Threshold transfer**: in-domain BA $0.83$; cross-domain/cross-model BA $0.25$--$0.67$; both fit directions reported. Inserted at the end of the domain-matrix section.
- **Symmetric surgery**: verified from `sonar_protocol.json` (text-side translation present for `clip_frozen` and `sonar_ft`).
- **Certificate control**: generic CLIP ViT-B/32 on fathomnet8 (marine optical) and NKSID (sonar); margin mass saturates ($M\approx1$ at every $\lambda$; correlation undefined); this is the margin CDF at a coarse $\varepsilon$ grid rather than an accuracy effect, since the 59.1%-accurate ImageNet-5k reference saturates identically for $\varepsilon\ge0.05$. The control is in the **main text** of the working manuscript (since 2026-10-19, reworded 2026-10-24), and the adapted-encoder version was run: BioCLIP $r=-0.346$, OceanCLIP $r=-0.564$ at $\varepsilon=0.05$.
- **Housekeeping**: dead labels `cor:nocg`/`cor:orth`/`cor:twofield` now referenced; PDF title metadata set; one related-work citation added (acoustic cross-modal distillation, arXiv:2609.31785).
- **Build**: `main_ieee.pdf` **64 pages**, 0 errors, 0 undefined references/citations, 0 overfull boxes.

## 续：适配模型证书与扩展阈值迁移（2026-10-19 18:50）

- **适配模型证书**（BioCLIP 基座 / OceanCLIP，67 类海洋子集，gap-surgery 同协议）：margin 质量与 top-1 相关仅
  $r=-0.35$（BioCLIP）/ $-0.56$（OceanCLIP，$\varepsilon=0.05$）；阈值跨编码器迁移 BA $0.13$–$0.50$（机会 0.50）。
  ⇒ 标量证书不能替代域内诊断；已写入 `ext_partII_domains.tex` 并归档
  `outputs/analysis/a23_certificate_adapted.json`。
- **扩展阈值迁移**：12 个归档域臂（含 4 个 spectrum 臂）跨域 BA 中位 $0.50$、范围 $0.00$–$0.83$；同域拟合降至
  $0.50$–$0.63$ ⇒ 阈值需要足够幅度点才能拟合，已写入正文并归档 `a23_threshold_transfer_extended.json`。
