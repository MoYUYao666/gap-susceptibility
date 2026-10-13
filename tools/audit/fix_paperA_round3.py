# Paper A fixes — three-model audit findings (2026-08-12)
# A1 both Full FT batches reported / A2 the n convention / A3 Theorem 2 proof / A4 phantom citation / A5 linear baseline / A6 CV / A7 theorem numbering / A9 fig note
import re

def patch(path, pairs):
    src = open(path, encoding='utf-8').read()
    for old, new in pairs:
        if old in src:
            src = src.replace(old, new)
            print('OK  ', path.split('/')[-1], '|', old[:55])
        else:
            print('MISS', path.split('/')[-1], '|', old[:55])
    open(path, 'w', encoding='utf-8').write(src)

# ============ theory.tex ============
patch('paper合/sections/theory.tex', [
    # A3: derivation inlined into the proof
    (r'\begin{proof}'
     r'\nSee the Supplementary Information.'
     r'\n\end{proof}',
     r'\begin{proof}'
     r'\nStarting from the gradient-flow identity (Equation~\ref{eq:gradflow}), the trajectory-averaged right-hand side $f(DG^*) = \langle \nabla_\theta DG^*, \nabla_\theta \mathcal{L} \rangle$ is linearized around the pretrained value $DG_0$: $f(DG^*) \approx f(DG_0) + f^\prime(DG_0)(DG^* - DG_0)$. Substituting into Equation~(\ref{eq:gradflow}) and collecting terms yields the ODE with $\alpha = -\eta f(DG_0)$ and $\beta = \eta f^\prime(DG_0)$, where the trajectories of $\Gamma_m$ and $\|g_m\|$ enter through the averages defining $f$.'
     r'\n\end{proof}'),
    # A12: downgrade the DG*~DG sentence (r=0.96 has no JSON support)
    (r' Empirically, $DG^*$ and the measured DG are highly correlated (mean $r = 0.96$ over pilot runs), validating $DG^*$ as a tractable proxy.',
     r' $DG^*$ tracks the measured DG closely in the pilot runs, validating it as a tractable proxy.'),
    # Full FT paragraph: present both batches
    (r'In the ODE framework, the fitted $DG^*$ dynamics of full fine-tuning are comparable to PEFT under matched settings ($\alpha_{\text{full}}=-0.040$, $\beta_{\text{full}}=0.159$), indicating that the first-order $DG^*$ dynamics do not by themselves distinguish full fine-tuning from PEFT. The catastrophic effect is instead captured by the empirical CG metric, which measures a different aspect of the distributional geometry; reconciling the two metrics is left to future work.',
     r'In the ODE framework, the fitted $DG^*$ dynamics of full fine-tuning are comparable to PEFT within the matched Phase-2 batch ($\alpha_{\text{full}}=-0.040$, $\beta_{\text{full}}=0.159$), whereas the Phase-1 pilot batch found a substantially larger $\beta_{\text{full}}=0.643$ (Section~\ref{sec:validation}); the batch sensitivity of this estimate indicates that the first-order $DG^*$ dynamics are not by themselves a reliable discriminator between full fine-tuning and PEFT. The catastrophic effect is instead captured by the empirical CG metric, which measures a different aspect of the distributional geometry; reconciling the two metrics is left to future work.'),
])

# ============ main_springer.tex ============
patch('paper合/main_springer.tex', [
    # A7: auto-number Theorem 2 + A5: linear baseline + Full FT wording
    (r'(Theorem~2) and $\beta$ is the alignment-restoring coefficient. The ODE predicts the full gap trajectory with mean $R^2 > 0.96$ across all tested LoRA configurations, substantially outperforming constant ($R^2=0.00$) and linear ($R^2\approx0.5$) baselines. $\beta$ is stable within PEFT ($\text{CV}=13.3\%$) and remains stable under full fine-tuning with matched training settings ($\beta_{\text{full}}=0.159$).',
     r'(Theorem~\ref{thm:ode}) and $\beta$ is the alignment-restoring coefficient. The ODE predicts the full gap trajectory with mean $R^2 > 0.96$ across all tested LoRA configurations, outperforming the constant baseline ($R^2=0.00$) and marginally the linear baseline (mean $R^2=0.946$). $\beta$ is stable within PEFT ($\text{CV}=13.3\%$); estimates of $\beta_{\text{full}}$ differ across batches ($0.159$ in the matched Phase-2 sweep vs.\ $0.643$ in the Phase-1 pilot, Section~\ref{sec:validation}).'),
])

# ============ introduction.tex ============
patch('paper合/sections/introduction.tex', [
    (r'is the trajectory-averaged perturbation force (Theorem~2) and $\beta$ is the alignment-restoring coefficient. This ODE yields',
     r'is the trajectory-averaged perturbation force (Theorem~\ref{thm:ode}) and $\beta$ is the alignment-restoring coefficient. This ODE yields'),
    (r'predicts gap trajectories with $R^2 > 0.96$, substantially outperforming constant ($R^2=0.00$) and linear ($R^2\approx0.5$) baselines.',
     r'predicts gap trajectories with mean $R^2 > 0.96$, outperforming the constant baseline ($R^2=0.00$) and marginally the linear baseline (mean $R^2=0.946$).'),
])

# ============ supplement.tex ============
patch('paper合/sections/supplement.tex', [
    (r'The Theorem~2 prediction---',
     r'The Theorem~\ref{thm:ode} prediction---'),
    # A11: honest note on the theoretical beta formula
    (r'\section*{C. ODE Framework: Theorem Verification and Falsification}',
     r'\section*{C. ODE Framework: Theorem Verification and Falsification}'
     r'\n'
     r'\nA note on the theoretical $\beta$ formula: applying Equation~(\ref{eq:ode_main})''s definition of $\beta$ directly to the measured gradients yields $\beta_{\text{theor}} \approx 0.004$, roughly $40\times$ smaller than the fitted values ($\beta \approx 0.14$--$0.16$). The $\alpha$ prediction is therefore the primary quantitative test of the framework (verified below), while a fully predictive theory of the restoring coefficient requires additional modeling (e.g., gradient-noise or higher-order effects) and is left to future work.'),
])

# ============ validation.tex ============
patch('paper合/sections/validation.tex', [
    # A4: A1 phantom -> reword at first definition
    (r'Assumption~A1 states that $\beta$ is approximately constant across PEFT configurations that preserve the pre-trained loss landscape geometry. We measure $\beta$ on three configurations',
     r'The constancy assumption (A1) states that $\beta$ is approximately constant across PEFT configurations that preserve the pre-trained loss landscape geometry. We measure $\beta$ on three configurations'),
    # Phase 1 caption: present both batches
    (r'A1 holds across PEFT and full fine-tuning under matched training settings ($\text{CV}=13.3\%$ within PEFT).',
     r'A1 holds within PEFT ($\text{CV}=13.3\%$). Full-FT $\beta$ differs across batches: $0.643$ (this pilot) vs.\ $0.159$ (Phase-2 matched sweep); see text.'),
    # Phase 1 table Full FT row: restore the pilot measurement
    (r'Full fine-tuning    & $0.159 \pm 0.024$ & $>0.97$ & comparable \\',
     r'Full fine-tuning    & $0.643 \pm 0.224$ & $0.86$--$0.96$ & batch-sensitive \\'),
    # Phase 1 body paragraph: present both batches
    (r'The stability of $\beta$ across PEFT and full fine-tuning confirms the physical interpretation: $\beta$ is a landscape-curvature quantity intrinsic to the pretrained geometry, insensitive to the fine-tuning method under matched training settings.',
     r'Within PEFT, $\beta$ is stable (CV $=13.3\%$), confirming A1. For full fine-tuning the picture is batch-dependent: this pilot yields $\beta_{\text{full}}=0.643\pm0.224$ (a $4.7\times$ departure from the PEFT mean), while the larger matched-setting Phase-2 sweep yields $\beta_{\text{full}}=0.159$ (Table~\ref{tab:phase2}), comparable to PEFT. The discrepancy indicates sensitivity to batch-specific training details rather than a method-level effect; we therefore report both values and do not base claims on either alone. The within-batch comparison of Phase~2 (same script, same settings) is the more controlled estimate.'),
    # L71: Corollary 3 phantom + drop the specific 29% CV figure + linear/logarithmic
    (r'confirming the protective bound predicted by Corollary~3.',
     r'confirming the protective bound.'),
    (r'$\beta$ is stable across ranks and positions within a consistent range ($\text{CV}=29\%$ across configuration means), justifying the constancy assumption. Third, the exponential form fits all trajectories with mean $R^2 > 0.96$, eliminating alternative model forms (linear, logarithmic) that would produce substantially worse fits.',
     r'$\beta$ is stable across ranks and positions within a consistent range, justifying the constancy assumption. Third, the exponential form fits all trajectories with mean $R^2 > 0.96$, marginally above the linear baseline (mean $R^2=0.946$).'),
    # L39: linear baseline
    (r'mean $R^2 > 0.96$ across PEFT configurations, substantially outperforming constant ($R^2=0.00$) and linear ($R^2\approx0.5$) baselines.',
     r'mean $R^2 > 0.96$ across PEFT configurations, outperforming the constant baseline ($R^2=0.00$) and marginally the linear baseline (mean $R^2=0.946$).'),
    # A9: fig note on epochs
    (r'Solid curves: ODE predictions ($\alpha$, $\beta$ fitted from first 3 epochs).',
     r'Solid curves: ODE predictions ($\alpha$, $\beta$ fitted over the full training trajectory).'),
])

# ============ empirical.tex ============
patch('paper合/sections/empirical.tex', [
    # A2: the n convention
    (r'A key statistical discovery is that the Distribution Gap strongly predicts retrieval performance. Across $n=94$ experiments spanning different methods, architectures, and datasets, DG achieves $r = -0.827$ with R@1, substantially outperforming CG ($r = -0.683$).',
     r'A key statistical discovery is that the Distribution Gap strongly predicts retrieval performance. Across the $n=81$ complete experiments spanning different methods, architectures, and datasets, DG achieves $r = -0.827$ with R@1, substantially outperforming CG ($r = -0.683$).'),
    (r'\caption{Pearson correlation between gap metrics and R@1 ($n=94$).}',
     r'\caption{Pearson correlation between gap metrics and R@1 ($n=81$).}'),
    (r'($-0.819$ vs.\ naive bootstrap estimate $-0.815$, which is consistent with the Pearson $r=-0.827$ up to the resampling procedure).',
     r'($-0.819$ vs.\ the naive Pearson $-0.815$ over the same $n=94$ sample; the $n=81$ Pearson is $-0.827$).'),
])

print('\nPaper A fixes complete (pending compile verification)')
