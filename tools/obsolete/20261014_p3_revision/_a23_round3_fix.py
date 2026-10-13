# -*- coding: utf-8 -*-
"""
A23 round-3 fixes (2026-09-16), EN + ZH mirrors kept in sync.

1. main.tex:85  - remove the stale "in our network environment only NKSID was
   retrievable" caveat; the final acquisition outcome is that four acoustic
   instruments were obtained.
2. main.tex:811 - the appendix is chronological; the closing sentence of the
   FIRST pass must be framed historically, not as the paper's final state.
3. Add the IEEE JOE 2025 survey (Aubard et al.) as a citation supporting the
   sonar data-availability claim, in section 2 and in the data appendix.

Every replacement asserts an exact occurrence count, so a silent no-op or a
double replacement fails loudly.
"""
import io
import sys

ROOT = r"D:\Realdesktop\Wan\Important\New\paper_a2"
EN = ROOT + r"\main.tex"
ZH = ROOT + r"\main_zh.tex"

FAILS = []


def patch(path, pairs, tag):
    with io.open(path, "r", encoding="utf-8") as fh:
        src = fh.read()
    for i, (old, new) in enumerate(pairs, 1):
        n = src.count(old)
        if n != 1:
            FAILS.append("%s #%d: expected 1 occurrence, found %d :: %s"
                         % (tag, i, n, old[:70]))
            continue
        src = src.replace(old, new)
        print("  ok   %s #%d" % (tag, i))
    with io.open(path, "w", encoding="utf-8", newline="") as fh:
        fh.write(src)
    return src


# ----------------------------------------------------------------- main.tex
en_pairs = [
    # (1) section 2 data-availability caveat -> final outcome
    (
        "(We note as a data-availability caveat that several sonar datasets are "
        "distributed only through GitHub repositories, cloud drives or figshare; in "
        "our network environment only NKSID was retrievable, and we document the "
        "failed attempts transparently in the appendix.)",
        "(We note as a data-availability caveat that several sonar datasets are "
        "distributed only through GitHub repositories, cloud drives or figshare, and "
        "that bulk transfer from our environment failed repeatedly in 2026-08; the "
        "reachable channels were eventually acquired through retries, a VPN and "
        "API/CDN routes, and the full attempt log---including the sets that remain "
        "unobtainable---is documented transparently in Appendix~\\ref{app:data}.)",
    ),
    # (2) appendix, first pass: historical framing
    (
        "We therefore report single-dataset acoustic evidence with an internal "
        "robustness check (balanced 650 vs full 2{,}617 protocols) and mark "
        "cross-dataset replication as an explicit future item.",
        "At the time of this first pass we therefore reported single-dataset acoustic "
        "evidence with an internal robustness check (balanced 650 vs full 2{,}617 "
        "protocols) and marked cross-dataset replication as an explicit future item; "
        "the retries documented below supersede that state.",
    ),
    # (3a) JOE 2025 survey, section 2
    (
        "and a recent survey mapping the full dataset landscape across side-scan, "
        "FLS, synthetic-aperture, multibeam and DIDSON modalities "
        "\\citep{sonarsurvey2025}.",
        "and recent surveys mapping the dataset landscape across side-scan, FLS, "
        "synthetic-aperture, multibeam and DIDSON modalities \\citep{sonarsurvey2025} "
        "and reviewing deep-learning robustness and open challenges for sonar in "
        "underwater robotics \\citep{aubard2025}.",
    ),
    # (3b) JOE 2025 survey, data appendix
    (
        "To replicate the acoustic results on a second instrument or dataset, we "
        "attempted (all in 2026-08):",
        "To replicate the acoustic results on a second instrument or dataset---recent "
        "overviews of sonar deep learning likewise identify data availability as a "
        "standing constraint \\citep{aubard2025}---we attempted (all in 2026-08):",
    ),
    # (5) bibliography entry (alphabetical: Aubard < Alawode? no -> Alawode then Aubard)
    (
        "\\bibitem[Bi et al.(2024)]{oceangpt2023}",
        "\\bibitem[Aubard et al.(2025)]{aubard2025}\n"
        "Aubard, M., Madureira, A., Teixeira, C., Pinto, J., 2025. Sonar-based deep "
        "learning in underwater robotics: overview, robustness, and challenges. IEEE "
        "Journal of Oceanic Engineering. https://doi.org/10.1109/JOE.2025.3531933.\n"
        "\\bibitem[Bi et al.(2024)]{oceangpt2023}",
    ),
]

# --------------------------------------------------------------- main_zh.tex
zh_pairs = [
    (
        "（数据可得性警示：多个声呐数据集仅经 GitHub 仓库、云盘或 figshare 分发；"
        "在我们的网络环境下仅 NKSID 可获取，失败尝试已在附录公开记录。）",
        "（数据可得性警示：多个声呐数据集仅经 GitHub 仓库、云盘或 figshare 分发，"
        "且 2026-08 期间从我们的环境批量传输屡次失败；可达通道最终通过重试、VPN 与 "
        "API/CDN 途径完成获取，完整尝试记录——包括至今仍无法获得的数据集——"
        "已在附录~\\ref{app:data} 公开。）",
    ),
    (
        "因此我们报告单数据集声呐证据，配内部稳健性检验（平衡 650 对全量 2{,}617 口径），"
        "并把跨数据集复现列为显式未来事项。",
        "此时我们因此报告单数据集声呐证据，配内部稳健性检验（平衡 650 对全量 2{,}617 "
        "口径），并把跨数据集复现列为显式未来事项；下文记录的重试已更新该状态。",
    ),
    (
        "以及横跨侧扫、FLS、合成孔径、多波束与 DIDSON 全谱系的数据集综述 "
        "\\cite{sonarsurvey2025}。",
        "以及横跨侧扫、FLS、合成孔径、多波束与 DIDSON 全谱系的数据集综述 "
        "\\cite{sonarsurvey2025}、与综述声呐深度学习稳健性及开放挑战的近期工作 "
        "\\cite{aubard2025}。",
    ),
    (
        "为在第二台仪器或数据集上复现声学结果，我们尝试了（2026-08）：",
        "为在第二台仪器或数据集上复现声学结果——声呐深度学习的近期综述同样把"
        "数据可得性列为长期约束 \\cite{aubard2025}——我们尝试了（2026-08）：",
    ),
    (
        "\\bibitem[Bi et al.(2024)]{oceangpt2023}",
        "\\bibitem[Aubard et al.(2025)]{aubard2025} M.~Aubard, A.~Madureira, "
        "C.~Teixeira, J.~Pinto, Sonar-based deep learning in underwater robotics: "
        "overview, robustness, and challenges, IEEE Journal of Oceanic Engineering, "
        "2025, \\href{https://doi.org/10.1109/JOE.2025.3531933}"
        "{doi:10.1109/JOE.2025.3531933}。\n"
        "\\bibitem[Bi et al.(2024)]{oceangpt2023}",
    ),
]

print("[EN] main.tex")
en = patch(EN, en_pairs, "EN")
print("[ZH] main_zh.tex")
zh = patch(ZH, zh_pairs, "ZH")

# ------------------------------------------------------------------ verify
checks = [
    ("EN stale caveat gone", "only NKSID was retrievable" not in en),
    ("ZH stale caveat gone", "仅 NKSID 可获取" not in zh),
    ("EN historical framing", "At the time of this first pass" in en),
    ("ZH historical framing", "此时我们因此报告单数据集" in zh),
    ("EN aubard cited x2", en.count("\\citep{aubard2025}") == 2),
    ("ZH aubard cited x2", zh.count("\\cite{aubard2025}") == 2),
    ("EN bibitem present", en.count("\\bibitem[Aubard et al.(2025)]{aubard2025}") == 1),
    ("ZH bibitem present", zh.count("\\bibitem[Aubard et al.(2025)]{aubard2025}") == 1),
    ("EN no dup label", en.count("{aubard2025}") == 3),
    ("ZH no dup label", zh.count("{aubard2025}") == 3),
    ("EN app:data ref intact", "\\label{app:data}" in en),
    ("ZH app:data ref intact", "\\label{app:data}" in zh),
]
print("\n[verify]")
for name, ok in checks:
    print("  %-24s %s" % (name, "PASS" if ok else "FAIL"))
    if not ok:
        FAILS.append(name)

if FAILS:
    print("\nFAILURES (%d):" % len(FAILS))
    for f in FAILS:
        print("  - " + f)
    sys.exit(1)
print("\nALL CHECKS PASSED")
