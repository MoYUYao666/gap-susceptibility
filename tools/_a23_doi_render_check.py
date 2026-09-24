"""Final render check: strip lineno's margin numbers from the -layout text,
then confirm each full DOI / locator appears verbatim in the PDF.

v1 of this check was too weak: its regex stopped at the first '.' so it only
proved the DOI *prefix* rendered. This version lists the full DOIs explicitly
and compares the complete string.
"""
import re
import subprocess

PDF = r"D:\Realdesktop\Wan\Important\New\paper_a2\main_ieee.pdf"

raw = subprocess.run(["pdftotext", "-layout", PDF, "-"], capture_output=True,
                     text=True, encoding="utf-8", errors="replace").stdout

# lineno writes the line number at the left margin of each typeset line; with
# -layout it lands at the start of the extracted line. Strip it.
lines = []
for ln in raw.splitlines():
    lines.append(re.sub(r"^\s*\d{1,4}\s+", "", ln))
clean = re.sub(r"\s+", "", "\n".join(lines))
print(f"剥离行号后文本长度: {len(clean)} 字符\n")

DOIS = [
    ("chen2025",         "10.1145/3759243"),
    ("jian2024",         "10.1007/s44295-024-00023-6"),
    ("qin2022",          "10.3390/rs14153794"),
    ("aquaticclip2026",  "10.1109/TNNLS.2026.3657138"),
    ("marinegpt2023",    "10.48550/arXiv.2310.13596"),
    ("oceangpt2023",     "10.18653/v1/2024.acl-long.184"),
    ("liang2022",        "10.52202/068431-1280"),
    ("yi2025",           "10.48550/arXiv.2510.03268"),
    ("yamaguchi2025",    "10.1109/CVPR52734.2025.00402"),
    ("sofer2025",        "10.21437/Interspeech.2025-1664"),
    ("wortsman2022",     "10.1109/CVPR52688.2022.00780"),
    ("christensen2026",  "10.1016/j.oceaneng.2026.124646"),
    ("maione2026",       "10.1016/j.oceaneng.2026.127078"),
    ("uatd2022",         "10.1038/s41597-022-01854-w"),
    ("s3simulator2024",  "10.1007/978-3-031-78444-6_15"),
    ("sonarsurvey2025",  "10.48550/arXiv.2510.03353"),
    ("aubard2025",       "10.1109/JOE.2025.3531933"),
]
print("=" * 74)
print("完整 DOI 逐条比对（在 PDF 中逐字出现）")
print("=" * 74)
ok = bad = 0
for key, doi in DOIS:
    hit = doi in clean
    print(f"  {'OK  ' if hit else '!!  '}{key:<18} {doi}")
    ok += hit
    bad += (not hit)
print("=" * 74)
print(f"完整渲染 {ok}/{len(DOIS)}    未渲染 {bad}")

URLS = [
    ("oceanclip2025", "https://huggingface.co/zjunlp/OceanCLIP-0.15B"),
    ("nksid2024",     "https://github.com/Jorwnpay/NK-Sonar-Image-Dataset"),
    ("sonarsurvey25", "https://github.com/Jorwnpay/Awesome-Sonar-Image-Resources"),
    ("mvaldenegro",   "https://github.com/mvaldenegro/marine-debris-fls-datasets"),
    ("qwen2vl2024",   "https://huggingface.co/Qwen/Qwen2-VL-2B-Instruct"),
]
print()
print("稳定 URL 逐条比对")
print("=" * 74)
uok = 0
for key, u in URLS:
    hit = u in clean
    print(f"  {'OK  ' if hit else '!!  '}{key:<18} {u}")
    uok += hit
print(f"渲染 {uok}/{len(URLS)}")
