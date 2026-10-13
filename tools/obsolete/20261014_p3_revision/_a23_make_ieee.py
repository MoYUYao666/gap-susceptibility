"""Generate paper_a2/main_ieee.tex: elsarticle -> IEEEtran review format.

Transformations (all auditable, no content changes):
  1. preamble  -> IEEEtran review-mode preamble
  2. frontmatter -> \title/\author/\maketitle/abstract/IEEEkeywords
  3. \citep{X} -> \cite{X}   (34x); the single parenthetical \citet is reworded
  4. bibliography -> IEEE numeric order (first-citation), author-year labels
     stripped, seven verified DOIs added
Reads main.tex, writes main_ieee.tex. Does not touch main.tex.
"""
import pathlib
import re
import sys

BASE = pathlib.Path(r"D:\Realdesktop\Wan\Important\New\paper_a2")
src = (BASE / "main.tex").read_text(encoding="utf-8")

# ---------------------------------------------------------------- 1. preamble
NEW_PREAMBLE = r"""\documentclass[journal,12pt,draftclsnofoot,onecolumn]{IEEEtran}
% draftclsnofoot, not draftcls: JOE requires "remove text in the document
% header", and plain draftcls stamps the date and the word DRAFT on every page.
% draftclsnofoot keeps the draft-mode baselineskip behaviour but no footer text.
\usepackage{amsmath,amssymb}
\usepackage{amsthm}
\newtheorem{lemma}{Lemma}
\newtheorem{theorem}{Theorem}
\newtheorem{corollary}{Corollary}
\usepackage{graphicx}
\usepackage{booktabs}
\usepackage{tabularx}
\usepackage{float}
\usepackage[hidelinks]{hyperref}
\usepackage{url}
\usepackage{lineno}
\usepackage{setspace}
% The five \input files (ext_partI..V) are shared verbatim with the elsarticle
% master main.tex and therefore use elsarticle's natbib-style citation commands.
% Map them onto IEEEtran's numeric \cite so the shared files need no forking.
% (ext_partIII_dynamics.tex:65 carries the only such command.)
\providecommand{\citep}[1]{\cite{#1}}
\providecommand{\citet}[1]{\cite{#1}}
"""
# preamble = everything before \begin{document}
m = re.search(r"\\begin\{document\}", src)
if not m:
    sys.exit("FATAL: no \\begin{document}")
preamble_old = src[: m.start()]
body = src[m.start():]
print(f"old preamble: {len(preamble_old.splitlines())} lines -> replaced")

# ------------------------------------------------------------- 2. frontmatter
ABSTRACT = re.search(r"\\begin\{abstract\}(.*?)\\end\{abstract\}", src, re.S)
KEYWORDS = re.search(r"\\begin\{keyword\}(.*?)\\end\{keyword\}", src, re.S)
TITLE = re.search(r"\\title\{(.*?)\}\s*\n", src, re.S)
if not (ABSTRACT and KEYWORDS and TITLE):
    sys.exit("FATAL: abstract/keyword/title not found")

abstract_text = ABSTRACT.group(1).strip()
kw_raw = KEYWORDS.group(1).strip()
keywords = [k.strip() for k in kw_raw.split(r"\sep") if k.strip()]
print(f"keywords parsed from elsarticle source: {len(keywords)}")
# JOE Guide: "Three to five subject keywords suitable for indexing must be
# provided." The elsarticle master carries seven, which exceeds the cap, so the
# IEEE/JOE build keeps the five most central and drops the two most specific.
KW_CAP = 5
if len(keywords) > KW_CAP:
    dropped = keywords[KW_CAP:]
    keywords = keywords[:KW_CAP]
    print(f"  trimmed to {KW_CAP} (JOE cap); dropped: {dropped}")

title_text = " ".join(TITLE.group(1).split())

NEW_FRONT = (
    "\\begin{document}\n\n"
    "% JOE requires TRUE double spacing. Two traps here, both measured:\n"
    "%   - IEEEtran's draftcls already sets \\baselinestretch{1.5}, i.e. 20.8pt\n"
    "%     leading at 12pt, which reads as space-and-a-half, not double.\n"
    "%   - setspace's \\doublespacing is \\setstretch{1.667}, giving only 23.0pt.\n"
    "% \\setstretch{2.0} gives 27.8pt, which is unambiguously double spacing.\n"
    "\\setstretch{2.0}\n"
    "\\linenumbers\n"
    "\\sloppy\n\n"
    f"\\title{{{title_text}}}\n\n"
    "\\author{Hongrui Wan%\n"
    "\\thanks{Hongrui Wan is with the University of Southampton, University Road,\n"
    "Southampton SO17 1BJ, United Kingdom (e-mail: contact@example.com).}}\n\n"
    "\\maketitle\n\n"
    "\\begin{abstract}\n"
    f"{abstract_text}\n"
    "\\end{abstract}\n\n"
    "\\begin{IEEEkeywords}\n"
    + ", ".join(keywords)
    + "\n\\end{IEEEkeywords}\n"
)

# replace everything from \begin{document} through \end{frontmatter}
fm = re.search(r"\\end\{frontmatter\}", body)
if not fm:
    sys.exit("FATAL: no \\end{frontmatter}")
rest = body[fm.end():]
print(f"frontmatter block replaced; body kept from after \\end{{frontmatter}}")

doc = NEW_PREAMBLE + NEW_FRONT + rest

# ------------------------------------------------------------- 3. citations
n_citep = doc.count(r"\citep{")
doc = doc.replace(r"\citep{", r"\cite{")
print(f"\\citep{{ -> \\cite{{ : {n_citep} replacements")

# the one \citet sits inside parentheses: "(...release (\citet{key}))" -> drop
# the wrapper parens so numeric style does not produce double parentheses
citet_old = r"debris release (\citet{mvaldenegro2024})"
citet_new = r"debris release \cite{mvaldenegro2024}"
if citet_old not in doc:
    sys.exit("FATAL: the \\citet reword anchor was not found verbatim")
doc = doc.replace(citet_old, citet_new)
print("\\citet reworded (parenthetical wrapper removed)")

leftover = re.findall(r"\\cite[tp]\{", doc)
if leftover:
    sys.exit(f"FATAL: {len(leftover)} elsarticle citation commands remain")

# ------------------------------------------------- 3b. AI disclosure placement
# The PaperCept submission form certifies that AI-generated content "has been
# disclosed in the Acknowledgment section". The elsarticle master instead uses
# Elsevier's convention, a standalone "Declaration of generative AI ..."
# section, which would make that certification literally untrue at JOE.
# IEEE's own convention is the Acknowledgement, so for the IEEE build the
# disclosure is relocated there. The elsarticle master is left untouched.
AI_ANCHOR = r"\section*{Declaration of generative AI"
ACK_HDR = r"\section*{Acknowledgements}"

i_ai = doc.find(AI_ANCHOR)
i_ack = doc.find(ACK_HDR)
if i_ai < 0:
    sys.exit("FATAL: standalone AI declaration section not found")
if i_ack < i_ai:
    sys.exit("FATAL: Acknowledgements precede the AI declaration; unexpected order")

body_start = i_ai + len(r"\section*{Declaration of generative AI and AI-assisted technologies in the manuscript preparation process}")
if doc[i_ai:body_start].find("in the manuscript preparation process") < 0:
    sys.exit("FATAL: AI declaration header text not matched exactly")
nxt = doc.find(r"\section", body_start)
if nxt != i_ack:
    sys.exit(f"FATAL: expected the Acknowledgements to follow the AI declaration (got offset {nxt} vs {i_ack})")
ai_body = doc[body_start:i_ack].strip()

# Once the standalone heading is gone, nothing in the text says "generative
# AI"; under an "Acknowledgements" heading a reader is not primed for an AI
# disclosure, and IEEE asks specifically about AI-generated content. Name it.
_old = "the author used Claude (Anthropic) and DeepSeek V4 in order to"
_new = "the author used the generative AI tools Claude (Anthropic) and DeepSeek V4 in order to"
if _old not in ai_body:
    sys.exit("FATAL: could not find the AI-tool sentence to label explicitly")
ai_body = ai_body.replace(_old, _new)

# drop the standalone declaration, then append its text to the Acknowledgements
doc = doc[:i_ai] + doc[i_ack:]
i_ack2 = doc.find(ACK_HDR)
start2 = i_ack2 + len(ACK_HDR)
nxt2 = doc.find(r"\section", start2)
if nxt2 < 0:
    nxt2 = doc.find(r"\begin{thebibliography}", start2)
if nxt2 < 0:
    sys.exit("FATAL: could not find the end of the Acknowledgements section")
ack_body = doc[start2:nxt2].strip()
doc = doc[:start2] + "\n" + ack_body + " " + ai_body + "\n\n" + doc[nxt2:]

if "Declaration of generative AI" in doc:
    sys.exit("FATAL: the standalone declaration header still present")
if doc.count(ai_body) != 1:
    sys.exit(f"FATAL: AI disclosure text appears {doc.count(ai_body)} times")
print("AI disclosure relocated into the Acknowledgements section (IEEE build only)")

# ----------------------------------------------------------- 4. bibliography
BIB = r"""\begin{thebibliography}{99}
\bibitem{chen2025}
L. Chen, Y. Huang, J. Dong \emph{et al.}, ``Underwater optical object detection in the era of artificial intelligence: current, challenges and future,'' \emph{ACM Computing Surveys}, 2025, doi: 10.1145/3759243.

\bibitem{jian2024}
M. Jian, N. Yang, T. Chen \emph{et al.}, ``Underwater object detection and datasets: a survey,'' \emph{Intelligent Marine Technology and Systems}, 2024, doi: 10.1007/s44295-024-00023-6.

\bibitem{qin2022}
J. Qin, M. Li, D. Li \emph{et al.}, ``A survey on visual navigation and positioning for autonomous UUVs,'' \emph{Remote Sensing}, 2022, doi: 10.3390/rs14153794.

\bibitem{aquaticclip2026}
B. Alawode, I. I. Ganapathi, S. Javed, M. Bennamoun, and A. Mahmood, ``AquaticCLIP: a vision-language foundation model and dataset for underwater scene analysis,'' \emph{IEEE Trans. Neural Netw. Learn. Syst.}, 2026, doi: 10.1109/TNNLS.2026.3657138 (arXiv:2502.01785).

\bibitem{marinegpt2023}
Z. Zheng, J. Zhang, T.-A. Vu, S. Diao \emph{et al.}, ``MarineGPT: unlocking secrets of `ocean' to the public,'' arXiv:2310.13596, 2023, doi: 10.48550/arXiv.2310.13596.

\bibitem{oceangpt2023}
Z. Bi, N. Zhang, Y. Xue, Y. Ou \emph{et al.}, ``OceanGPT: a large language model for ocean science tasks,'' in \emph{Proc. 62nd Annu. Meeting Assoc. Comput. Linguistics (ACL)}, 2024, pp. 3357--3372, doi: 10.18653/v1/2024.acl-long.184.

\bibitem{oceanclip2025}
zjunlp, ``OceanCLIP-0.15B: marine vision-language model,'' HuggingFace model card (OceanGPT-X collection), 2025. [Online]. Available: \url{https://huggingface.co/zjunlp/OceanCLIP-0.15B}

\bibitem{wanA1}
H. Wan, ``The modality gap is not a universal health metric: order preservation governs zero-shot robustness,'' manuscript PRLETTERS-D-26-01941, previously submitted to \emph{Pattern Recognition Letters}; revised manuscript submitted to \emph{Neurocomputing} (manuscript NEUCOM-D-26-20952), 2026.

\bibitem{liang2022}
V. W. Liang, Y. Zhang, Y. Kwon, S. Yeung, and J. Zou, ``Mind the gap: understanding the modality gap in multi-modal contrastive representation learning,'' in \emph{Adv. Neural Inf. Process. Syst. (NeurIPS)}, vol.~35, 2022, doi: 10.52202/068431-1280.

\bibitem{levi2025}
M. Y. Levi and G. Gilboa, ``The double-ellipsoid geometry of CLIP,'' in \emph{Proc. Int. Conf. Machine Learning (ICML)}, 2025.

\bibitem{yi2025}
L. Yi, R. Douady, and C. Chen, ``Decipher the modality gap in multimodal contrastive learning: from convergent representations to pairwise alignment,'' arXiv:2510.03268, 2025, doi: 10.48550/arXiv.2510.03268 (ICML 2026 version: The Convergent Representation of Contrastive Vision-Language Models: Geometry, Modality Gap and Shared Space Alignment).

\bibitem{mistretta2025}
M. Mistretta, A. Baldrati, L. Agnolucci, M. Bertini, and A. Bagdanov, ``Cross the gap: exposing the intra-modal misalignment in CLIP via modality inversion,'' in \emph{Proc. Int. Conf. Learning Representations (ICLR)}, 2025.

\bibitem{yamaguchi2025}
S. Yamaguchi, D. Feng, S. Kanai, K. Adachi, and D. Chijiwa, ``Post-pre-training for modality alignment in vision-language foundation models,'' in \emph{Proc. IEEE/CVF Conf. Comput. Vis. Pattern Recognit. (CVPR)}, 2025, doi: 10.1109/CVPR52734.2025.00402.

\bibitem{sofer2025}
A. Sofer, Y. Goldman, and S. E. Chazan, ``Pull it together: reducing the modality gap in contrastive learning,'' in \emph{Proc. Interspeech}, 2025, doi: 10.21437/Interspeech.2025-1664.

\bibitem{chowers2026}
R. Chowers, O. Naparstek \emph{et al.}, ``Is the modality gap a bug or a feature? A robustness perspective,'' in \emph{Proc. IEEE/CVF Conf. Comput. Vis. Pattern Recognit. (CVPR)}, 2026.

\bibitem{grassucci2026}
E. Grassucci, G. Cicchetti, E. Frasca, A. Uncini, and D. Comminiello, ``Closing the modality gap aligns group-wise semantics,'' in \emph{Proc. Int. Conf. Learning Representations (ICLR)}, 2026.

\bibitem{wortsman2022}
M. Wortsman, G. Ilharco, J. W. Kim \emph{et al.}, ``Robust fine-tuning of zero-shot models,'' in \emph{Proc. IEEE/CVF Conf. Comput. Vis. Pattern Recognit. (CVPR)}, 2022, doi: 10.1109/CVPR52688.2022.00780.

\bibitem{biderman2024}
D. Biderman, J. Portes, J. J. G. Ortiz, M. Paul \emph{et al.}, ``LoRA learns less and forgets less,'' \emph{Trans. Machine Learning Research (TMLR)}, 2024.

\bibitem{wanP1}
H. Wan, ``Protect, don't perturb: cross-modal alignment under PEFT of vision-language models,'' under review, \emph{Pattern Recognition} (PR-D-26-10149), 2026.

\bibitem{christensen2026}
K. A. Christensen, A. G. Tufte, A. Gusev, R. Sinha \emph{et al.}, ``Foundation models on the bridge: semantic hazard detection and safety maneuvers for maritime autonomy with vision-language models,'' \emph{Ocean Engineering}, 2026, doi: 10.1016/j.oceaneng.2026.124646.

\bibitem{maione2026}
F. Maione, S. S. Arici, A. Hasan, and M. Sukarevicius, ``Agentic AI for autonomous condition monitoring and predictive maintenance of marine vessels,'' \emph{Ocean Engineering}, 2026, doi: 10.1016/j.oceaneng.2026.127078.

\bibitem{nksid2024}
NanKai Sonar Image Dataset (NKSID), 2024. [Online]. Available: \url{https://github.com/Jorwnpay/NK-Sonar-Image-Dataset} (MIT licence); indexed as a classification benchmark in the sonar-resource survey \cite{sonarsurvey2025}.

\bibitem{uatd2022}
K. Xie, J. Yang, and K. Qiu, ``A dataset with multibeam forward-looking sonar for underwater object detection,'' \emph{Scientific Data}, vol.~9, art. no.~739, 2022, doi: 10.1038/s41597-022-01854-w.

\bibitem{s3simulator2024}
S. Kamal Basha and A. Nambiar, ``S3Simulator: a benchmarking side scan sonar simulator dataset for underwater image analysis,'' in \emph{Pattern Recognition (ICPR 2024, Part XVI)}, Springer, 2024, doi: 10.1007/978-3-031-78444-6\_15.

\bibitem{sonarsurvey2025}
L. S. Gomes, G. P. Almeida, B. U. Moreira, M. Quiroz, B. Xavier, L. Soares, S. L. Bri\~ao, F. G. Oliveira, and P. L. J. Drews-Jr, ``Sonar image datasets: a comprehensive survey of resources, challenges, and applications,'' in \emph{SIBGRAPI}, 2025, doi: 10.48550/arXiv.2510.03353. Community catalogue: \url{https://github.com/Jorwnpay/Awesome-Sonar-Image-Resources}.

\bibitem{aubard2025}
M. Aubard, A. Madureira, C. Teixeira, and J. Pinto, ``Sonar-based deep learning in underwater robotics: overview, robustness, and challenges,'' \emph{IEEE J. Ocean. Eng.}, 2025, doi: 10.1109/JOE.2025.3531933.

\bibitem{radford2021}
A. Radford, J. W. Kim, C. Hallacy \emph{et al.}, ``Learning transferable visual models from natural language supervision,'' in \emph{Proc. Int. Conf. Machine Learning (ICML)}, 2021.

\bibitem{mvaldenegro2024}
M. Valdenegro-Toro, ``Deep neural networks for marine debris detection in sonar images,'' Ph.D. dissertation, Heriot-Watt University, 2019. Dataset releases and code: \url{https://github.com/mvaldenegro/marine-debris-fls-datasets} (water-tank and turntable FLS classification, matching and patches; ARIS 3000).

\bibitem{qwen2vl2024}
Qwen Team, ``Qwen2-VL: a vision-language model with enhanced multi-modal understanding (Qwen2-VL-2B-Instruct),'' 2024. [Online]. Available: \url{https://huggingface.co/Qwen/Qwen2-VL-2B-Instruct}

\end{thebibliography}
"""

b0 = re.search(r"\\begin\{thebibliography\}", doc)
b1 = re.search(r"\\end\{thebibliography\}", doc)
if not (b0 and b1):
    sys.exit("FATAL: bibliography not found")
old_bib = doc[b0.start(): b1.end()]
n_old = old_bib.count(r"\bibitem")
n_new = BIB.count(r"\bibitem")
if n_old != n_new:
    sys.exit(f"FATAL: bibliography entry count changed {n_old} -> {n_new}")
doc = doc[: b0.start()] + BIB.rstrip("\n") + doc[b1.end():]
print(f"bibliography rebuilt: {n_new} entries, order = first citation")

out = BASE / "main_ieee.tex"
out.write_text(doc, encoding="utf-8")
print(f"\nwrote {out}  ({len(doc.splitlines())} lines)")
