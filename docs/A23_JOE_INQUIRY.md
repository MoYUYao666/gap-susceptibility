# A23 → IEEE Journal of Oceanic Engineering：presubmission inquiry（合并修订版）

> 收件人：`joe-editor@ieeeoes.org`　抄送：`journal@ieeeoes.org`
> 主编：Karl von Ellenrieder
> 发送方式：不附全文（信里写"on request"）；若想附，附摘要单页即可
> 状态：**尚未发送**
> 本版 = 操作者原稿的语音与结构 + 修正两处已过期事实 + 并入今日新核实的三项内容

---

**Subject: Presubmission inquiry — scope of a cross-modal alignment-diagnostics study on marine and sonar perception**

Dear Professor von Ellenrieder,

I am writing, as the sole author, to ask whether a manuscript I am preparing is within the scope of the IEEE Journal of Oceanic Engineering, and which of your contribution types would suit it best, before I submit it.

The manuscript, "Alignment health across perception modalities: a gap-surgery diagnostic for marine vision and acoustic sonar models", asks what happens to contrastive vision-language perception models when they are adapted to marine data. Using a controlled perturbation protocol across five perception domains (marine optical, acoustic sonar, ImageNet-1K, DTD, Food101) and four contrastive model families, it reports two practically relevant results: that domain adaptation flattens the class bias field in a domain-specific way (3.6x on marine data; 3.8x on sonar at 650 images against 1.8x at 2,617), and that parameter-efficient fine-tuning preserves marine zero-shot accuracy (-2.8% to -8.1%) where full fine-tuning destroys it (-15% to -62%). It closes with a per-image operator that removes off-axis degradation error and with monitoring guidance for practitioners.

The acoustic claims are replicated across four public instruments: an Oculus M750d forward-looking sonar (NKSID; 2,617 images, 8 classes), an ARIS 3000 acoustic camera (a controlled water-tank debris release), a full-resolution ARIS3k plus sonar7 collection (11 classes), and the Gemini 1200ik multibeam forward-looking sonar dataset (9,200 frames, 10 classes). Negative results are reported as results: a domain-adaptive fine-tuning variant on the last of these collapsed on all three seeds, and the publicly available side-scan sets we examined carry only one to three labels each, so the study is not replicated on a multi-class side-scan set. The full acquisition log, including the datasets we could not obtain, is in the appendix.

I read the Journal's field of interest as covering "all aspects of science, engineering and technology ... pertaining to all bodies of water", and note that articles may represent "contributions of a theoretical or analytical nature" and that "system performance and tradeoff studies" are valid Technical Communications. I also note the Journal's own recent survey, Aubard et al., "Sonar-Based Deep Learning in Underwater Robotics" (2025, DOI 10.1109/JOE.2025.3531933), which identifies data availability and robustness as standing constraints on sonar deep learning; the present manuscript takes one of those constraints, alignment robustness under domain adaptation, and addresses it quantitatively, and cites that survey when documenting the sonar data landscape. May I ask (i) whether this work falls within JOE's scope, (ii) whether you would advise submitting it as a Peer-Reviewed Journal Article or as a Technical Communication, and (iii) any indication of the element you would most want strengthened?

Two points of context, for transparency. The diagnostic method has a companion paper by the same author, "The modality gap is not a universal health metric: order preservation governs zero-shot robustness" (NEUCOM-D-26-20952, submitted to Neurocomputing); the present manuscript reports entirely new marine and sonar experiments and a self-contained theoretical appendix, and does not overlap with it.

I can send the full manuscript or the abstract on request. Thank you for your time and for any guidance you can offer.

Sincerely,
Hongrui Wan
University of Southampton
hw4c24@soton.ac.uk

---

## 备注（不要发出去）

- **只披露 A1（`NEUCOM-D-26-20952`），不披露 P1（`PR-D-26-10149`）**：这是操作者的决定（2026-09-16）。
  - 理由：A1 是**理论姊妹篇**，正文明写 "our companion study \citep{wanA1}"（§1 第 46 行、§2 第 70 行），其精确反转条件与 $\tau$ 预测器直接支撑本文附录，Editors 若发现另一篇相似稿，A1 就是解释；P1 在本文只被引一次（§2 第 75 行，作"文本侧 LoRA 为最优处方"的实证支撑），**与"是否 in scope / 走哪个栏目"无关**。
  - 询问信的功能是 scope 与栏目判定，不是披露表；第一封邮件里摆两篇"under review"的自引，容易招来 salami/重叠问询，收益为负。
  - **不算隐瞒**：P1 在稿件里出现两处——参考文献 `\bibitem[Wan(2026b)]{wanP1}`（条目内标明 "under review, Pattern Recognition（PR-D-26-10149）"），以及 **封面信**（`paper_a2/cover_letter.tex:32`）：「the parameter-efficient fine-tuning results generalize my earlier study under review at *Pattern Recognition* (PR-D-26-10149)」。即：**随稿提交的封面信已把 A1 与 P1 两篇姊妹稿都披露给了编辑**，所以询问信只提 A1 不构成隐瞒。（2026-09-18 核实原文。⚠️ 不要为了"跟本备注一致"去删封面信里那句 P1 披露——封面信是更诚实的一版，留着。）
  - ⚠️ 唯一红线：措辞**不得暗示排他**。本版写的是 "The diagnostic method has a companion paper…"，点名 A1 是**方法**的姊妹篇，未声称"仅此一篇"，因此是真的。**不要**改写成 "the only related manuscript" 之类的排他表述。
- **绝不发送原稿中"acoustic evidence rests on one dataset (NKSID), because it was the only one retrievable"那段**：2026-08-31/09-03 已取得另外三套声学数据，正文与附录今天刚按四台仪器改正（`main.tex:85`、`:811`）。原句既与稿子矛盾，又白白丢掉三台仪器的复现证据。
- ~~不提 Ocean Engineering 桌面拒稿（与 JOE 无关）。若被直接问是否投过别处/被拒过，如实回答：2026-09-16 投 OE，当日以 scope 为由桌面拒稿，无审稿意见。~~
  → **⚠️ 此口径已于 2026-09-24 作废。** JOE Guide for Authors 明文强制："If a manuscript was previously reviewed and rejected by any other publication, authors **must disclose this history at the time of submission**"，且须附先前决定信副本 + 回应。写这条备注时尚未读 Guide。**投稿时必须在封面信主动披露** `OE-D-26-11643` 桌面拒稿并附决定信副本；隐瞒属 Guide 列明的 ethics 问题。已落实于 `paper_a2/cover_letter.tex` 的 "Prior submission history (disclosure)" 段，详见 `docs/A23_JOE_MIGRATION.md` 第四节。事实口径（**已按决定信原文更正**）：2026-09-16 投 OE，**2026-09-18** 以 scope 为由桌面拒稿（**非"当日"**），无审稿意见。
- 若答复"不适合"，按 `docs/A23_VENUE_DECISION.md` 第九节顺序落到 Neurocomputing 或 IEEE Access。
- 换刊确定后仍需改的项见同文件第十节。
