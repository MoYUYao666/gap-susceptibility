# Paper A 主张提取（投稿前审核用）

> 生成：`tools/_extract_claims.py` ｜ 句子总数 288


## 量级（10 句）

- **[conclusion.tex]** The framework predicts gap trajectories at mean MATH over the LoRA configurations (range MATH -- MATH ), substantially outperforming baselines, and generalizes across datasets (Flickr30k, MS-COCO).
- **[empirical.tex]** \subsection{The Position Effect Under the Earlier Convention} Under the convention used for the runs in this subsection, in which the backbone remains trainable alongside the adapter, the central regularity is shown in Figure~\ref{fig:overview}: \textbf{text-only fine-tuning overwhelmingly preserves cross-modal alignment}.
- **[empirical.tex]** Larger MATH consistently reduces the gap: MATH achieves CG MATH with R@1 of 0.637, contrary to the common practice of setting MATH .
- **[empirical.tex]** On ViT-L, however, rank-4 fails dramatically (CG MATH ), while text-only with rank-8 remains effective ( MATH ), suggesting that effective rank may scale with model capacity.
- **[empirical.tex]** Across the MATH archived experiments spanning different methods, architectures, and datasets, DG achieves MATH with R@1, substantially outperforming CG ( MATH );
- **[empirical.tex]** DG achieves MATH , substantially stronger than CG ( MATH ).} \label{fig:corr} \end{figure} Controlling for CG via partial correlation, DG retains MATH ( MATH ), confirming that DG captures distributional shape information beyond first-order centroid shift.
- **[introduction.tex]** Yet a fundamental question remains largely unanswered: \emph{how does fine-tuning affect the cross-modal alignment that these models were pre-trained to achieve?} Recent empirical work has revealed a striking regularity: text-only fine-tuning overwhelmingly preserves cross-modal alignment better than joint-modality fine-tuning, a phenomenon this paper confirms across 117 experiments on five architectures (Section~\ref{sec:empirical}).
- **[validation.tex]** First, MATH is consistently negative for all PEFT configurations, confirming the protective bound.
- **[validation.tex]** MATH is consistently negative for all PEFT configurations on both Flickr30k and COCO, confirming that the protective bound generalizes across datasets.
- **[validation.tex]** On CLIP, text-only MATH is consistently more negative than both-position MATH for all ranks, and the strict-freezing control confirms that ordering on the measured gap.

## 比较（20 句）

- **[conclusion.tex]** The framework predicts gap trajectories at mean MATH over the LoRA configurations (range MATH -- MATH ), substantially outperforming baselines, and generalizes across datasets (Flickr30k, MS-COCO).
- **[conclusion.tex]** A second caution cuts across architectures: a smaller gap and better retrieval are not the same objective.
- **[discussion.tex]** larger ranks expand the perturbation subspace without adding gradient capacity.
- **[empirical.tex]** on BLIP-1 it keeps the induced gap far smaller ( MATH against MATH );
- **[empirical.tex]** Text-only gives the smaller gap increase on Flickr30k, BLIP-1 and ViT-L, while MS-COCO reverses that ordering.} \label{tab:position} \begin{tabular}{lccc} \toprule Dataset & Text-only & Both & Vision-only \\ \midrule Flickr30k & MATH & MATH & MATH \\ COCO & MATH & MATH & MATH \\ BLIP-1 & MATH & MATH & --- \\ ViT-L & MATH & MATH (r=4) & --- \\ \bottomrule \end{tabular} \end{table} \begin{table}[ht] \centering \caption{The three adaptation positions under strict freezing, where the optimiser sees only the adapter matrices and the arms therefore differ solely in where those adapters sit.
- **[empirical.tex]** Larger MATH consistently reduces the gap: MATH achieves CG MATH with R@1 of 0.637, contrary to the common practice of setting MATH .
- **[empirical.tex]** Text-only LoRA and Adapter both preserve alignment, but scale with capacity in opposite directions: under the earlier protocol the LoRA benefit peaks in the middle of the rank range and reverses beyond it, whereas larger Adapter bottleneck dimensions reduce the gap more effectively.
- **[empirical.tex]** Across the MATH archived experiments spanning different methods, architectures, and datasets, DG achieves MATH with R@1, substantially outperforming CG ( MATH );
- **[empirical.tex]** DG achieves MATH , substantially stronger than CG ( MATH ).} \label{fig:corr} \end{figure} Controlling for CG via partial correlation, DG retains MATH ( MATH ), confirming that DG captures distributional shape information beyond first-order centroid shift.
- **[empirical.tex]** \textbf{Noise sensitivity (withdrawn).} An earlier single evaluation of isotropic Gaussian noise in the encoder parameters suggested that vision-side noise degrades retrieval MATH more than text-side noise.
- **[introduction.tex]** Yet a fundamental question remains largely unanswered: \emph{how does fine-tuning affect the cross-modal alignment that these models were pre-trained to achieve?} Recent empirical work has revealed a striking regularity: text-only fine-tuning overwhelmingly preserves cross-modal alignment better than joint-modality fine-tuning, a phenomenon this paper confirms across 117 experiments on five architectures (Section~\ref{sec:empirical}).
- **[introduction.tex]** The Distribution Gap (DG)---a measure of distributional mismatch between visual and text embeddings---predicts retrieval performance at MATH over MATH experiments, far outperforming the commonly reported Centroid Gap.
- **[introduction.tex]** For a given allocation of perturbation, the text-only position follows from MATH : removing the dominant visual term leaves only the weaker text contribution.
- **[introduction.tex]** Section~\ref{sec:validation} shows that this default does not carry over to SigLIP unchanged, and that a smaller gap and better retrieval can point in different directions.
- **[related_work.tex]** The present results are consistent with all three and sharpen the practical conclusion: the gap is not an objective that can be minimised on behalf of retrieval, because which adaptation site produces the smaller gap and which produces the better retrieval need not be the same site at all.
- **[supplement.tex]** ODE Framework: Theorem Verification and Falsification} A note on the theoretical MATH formula: applying Equation~(\ref{eq:ode_main})'s definition of MATH directly to the measured gradients yields MATH , roughly MATH smaller than the fitted values ( MATH -- MATH ).
- **[theory.tex]** Section~\ref{sec:empirical} shows what the second term costs: under joint-modality training the vision encoder receives the larger gradient signal ( MATH the text encoder's norm in the reference measurement), whereas under strict freezing a text-only arm registers no vision-side update at all.
- **[validation.tex]** the full-fine-tuning pilot fits at MATH , and we return to it below), outperforming the constant baseline ( MATH ) and marginally the linear baseline (mean MATH ).
- **[validation.tex]** The exponential fit achieves MATH (range 0.90--0.99), with MATH (negative, confirming the protective bound) and MATH ---larger than both LoRA ( MATH ) and full fine-tuning ( MATH ), consistent with MATH as a landscape-curvature diagnostic that varies across PEFT methods.
- **[validation.tex]** Under the CLIP strict-freezing control of Section~\ref{sec:empirical}, the text-only arm reduces the gap by more than the both-position arm ( MATH against MATH ;

## 范围（12 句）

- **[conclusion.tex]** The framework predicts gap trajectories at mean MATH over the LoRA configurations (range MATH -- MATH ), substantially outperforming baselines, and generalizes across datasets (Flickr30k, MS-COCO).
- **[conclusion.tex]** MATH is universally negative for PEFT, and MATH is stable across PEFT and full fine-tuning under matched settings ( MATH ).
- **[conclusion.tex]** A second caution cuts across architectures: a smaller gap and better retrieval are not the same objective.
- **[discussion.tex]** \subsection{Connection to Pattern Recognition} The cross-modal alignment dynamics studied here exemplify a broader class of pattern recognition problems: identifying systematic regularities in how training design choices map to representation outcomes across architectures, datasets, and objectives.
- **[empirical.tex]** text-only and low-rank configurations preserve alignment.} \label{fig:overview} \end{figure} The magnitudes across architectures and adaptation positions are collected in Table~\ref{tab:position}.
- **[empirical.tex]** (3) \textbf{Full fine-tuning should be avoided for retrieval tasks}---it uniformly degrades alignment regardless of data volume.
- **[supplement.tex]** The Theorem~\ref{thm:ode} prediction--- MATH ---agrees with the empirically fitted MATH in sign and order of magnitude across all six pilot configurations (all negative, within 0.03 of each other), although rank ordering is not preserved at this sample size.
- **[theory.tex]** The task gradient concentrates in a low-dimensional subspace regardless of the adapter's capacity.
- **[validation.tex]** MATH is consistently negative for all PEFT configurations on both Flickr30k and COCO, confirming that the protective bound generalizes across datasets.
- **[validation.tex]** MATH is stable across ranks and positions within each dataset and consistent across datasets ( MATH vs.\ MATH ), confirming that the ODE captures intrinsic dynamics rather than dataset-specific artifacts.
- **[validation.tex]** \textbf{The ordering reverses}: text-only \emph{increases} the gap ( MATH ) whereas both-position \emph{reduces} it ( MATH ), a paired difference of MATH ( MATH , consistent in sign across all five seeds).
- **[validation.tex]** First, the text-only advantage is a property of the architecture rather than a universal default, so it should not be transferred to a new encoder without this control.

## 统计（34 句）

- **[conclusion.tex]** \section{Conclusion} This paper has established a complete arc from empirical discovery to theoretical explanation to experimental verification, spanning 278 experiments across five model architectures, three PEFT methods, and two retrieval datasets.
- **[conclusion.tex]** First, we presented a systematic empirical characterization of modality gap evolution under PEFT (117 experiments), establishing that adaptation at the text position preserves cross-modal alignment on the InfoNCE-based encoders studied (a direction we show reverses on SigLIP), that the Distribution Gap predicts retrieval performance ( MATH over MATH experiments;
- **[conclusion.tex]** Third, we validated the ODE across 162 additional experiments (81 per dataset).
- **[conclusion.tex]** On SigLIP the same control reverses the ordering, so the recipe has to be established per architecture rather than assumed.
- **[discussion.tex]** The answer, as Section~\ref{sec:validation} shows, is affirmative for the LoRA configurations: mean MATH (range MATH -- MATH ) across the CLIP runs tested.
- **[discussion.tex]** both are reported in Section~\ref{sec:validation}.
- **[discussion.tex]** \item \textbf{Monitor DG as an alignment health signal.} The ODE establishes DG as the natural state variable for alignment dynamics.
- **[discussion.tex]** While the strong empirical agreement (mean MATH over the LoRA configurations) validates this approximation, stochastic gradient noise may affect the instantaneous dynamics in ways not captured by the deterministic ODE.
- **[discussion.tex]** their close agreement in the pilot runs supports the substitution, but formal bounds on the approximation error are not yet established.
- **[empirical.tex]** These experiments, spanning 117 experiments, establish the regularities that our dynamical theory (Section~\ref{sec:theory}) subsequently explains.
- **[empirical.tex]** Statistical validation uses 5-seed experiments with Welch's MATH -test and ANOVA.
- **[empirical.tex]** Section~\ref{sec:validation} shows that this conclusion does not survive strict freezing on every backbone, and Table~\ref{tab:position_strict} reports the strict-freezing comparison.
- **[empirical.tex]** Five-seed validation confirms robustness: text-only CG MATH , vs.\ full fine-tuning MATH ( MATH ).
- **[empirical.tex]** Five-seed experiments confirm statistical significance: rank-4 achieves CG MATH , while rank-32 achieves MATH ( MATH ).
- **[empirical.tex]** Section~\ref{sec:validation} shows that the LoRA side of that comparison is an artefact of the protocol rather than a property of rank: once the backbone is frozen and only the adapter matrices are trained, the text-only arm improves monotonically with rank.
- **[empirical.tex]** Both methods respond to where the adapters sit and to their dimension, but the direction differs: LoRA favours the text-only setting, whereas for Adapter no consistent text-only advantage is present once every run is scored against a common frozen baseline (Section~\ref{sec:validation}).} \label{fig:crossmethod} \end{figure} \subsection{Distribution Gap Predicts Retrieval Performance} \label{sec:dg_empirical} A key statistical discovery is that the Distribution Gap strongly predicts retrieval performance.
- **[empirical.tex]** DG achieves MATH , substantially stronger than CG ( MATH ).} \label{fig:corr} \end{figure} Controlling for CG via partial correlation, DG retains MATH ( MATH ), confirming that DG captures distributional shape information beyond first-order centroid shift.
- **[introduction.tex]** Yet a fundamental question remains largely unanswered: \emph{how does fine-tuning affect the cross-modal alignment that these models were pre-trained to achieve?} Recent empirical work has revealed a striking regularity: text-only fine-tuning overwhelmingly preserves cross-modal alignment better than joint-modality fine-tuning, a phenomenon this paper confirms across 117 experiments on five architectures (Section~\ref{sec:empirical}).
- **[introduction.tex]** Whether that position is in fact the better one is a separate, empirical matter, and Section~\ref{sec:validation} shows it depends on the architecture.
- **[introduction.tex]** \end{enumerate} Together, these contributions establish a principled framework for understanding and predicting how parameter-efficient fine-tuning reshapes cross-modal representation geometry.
- **[introduction.tex]** Section~\ref{sec:validation} shows that this default does not carry over to SigLIP unchanged, and that a smaller gap and better retrieval can point in different directions.
- **[related_work.tex]** The visual half of the model is the more fragile one, and this now has support from three directions that were established independently of each other: multimodal LLMs prove vulnerable to adversarial perturbations applied on the visual side \cite{schiappa2025robust};
- **[supplement.tex]** 5-Seed Statistical Validation & 20 \\ VIII.
- **[supplement.tex]** this is a layered-configuration comparison, and the aggregate cross-dimension comparison in Section~\ref{sec:validation} does not reproduce a text-only advantage for Adapter.} \label{fig:adapter_layered} \end{figure} \FloatBarrier \section*{C.
- **[supplement.tex]** Cross-Dataset ODE Validation} Table~\ref{tab:coco_ode} reports ODE metrics on MS-COCO (81 recorded runs: 14 configurations MATH 5 seeds, 5 frozen evaluations, and 5 full-FT seeds;
- **[theory.tex]** MATH tracks the measured DG closely in the pilot runs, validating it as a tractable proxy.
- **[validation.tex]** \section{Experimental Validation of the Theory} \label{sec:validation} The ODE framework derived in Section~\ref{sec:theory} makes quantitative predictions that we now test against data.
- **[validation.tex]** First, MATH is consistently negative for all PEFT configurations, confirming the protective bound.
- **[validation.tex]** \begin{table}[ht] \centering \caption{Cross-dataset and cross-method validation of ODE framework.
- **[validation.tex]** MATH is consistently negative for all PEFT configurations on both Flickr30k and COCO, confirming that the protective bound generalizes across datasets.
- **[validation.tex]** MATH is stable across ranks and positions within each dataset and consistent across datasets ( MATH vs.\ MATH ), confirming that the ODE captures intrinsic dynamics rather than dataset-specific artifacts.
- **[validation.tex]** The exponential fit achieves MATH (range 0.90--0.99), with MATH (negative, confirming the protective bound) and MATH ---larger than both LoRA ( MATH ) and full fine-tuning ( MATH ), consistent with MATH as a landscape-curvature diagnostic that varies across PEFT methods.
- **[validation.tex]** On CLIP, text-only MATH is consistently more negative than both-position MATH for all ranks, and the strict-freezing control confirms that ordering on the measured gap.
- **[validation.tex]** \end{enumerate} Together, these constitute a closed theoretical explanation for the empirical phenomena, validated by 278 experiments spanning three PEFT methods (LoRA, Adapter, BitFit) and two datasets.
