"""Independent pre-submission re-check of the A23 -> JOE package. v2.

v1 had two bugs that produced false alarms:
  * it searched `doc` (with newlines) but indexed contexts into `flat` (without),
    so every context printed as empty;
  * IEEEtran sets section headings in small caps, and pdftotext inserts spaces
    inside small-caps runs ("P ROBE TABLE"), so exact-name matching failed.
v2 searches a whitespace-stripped, uppercased copy for headings, and keeps
offsets consistent by doing all searching and slicing on the same string.
"""
import re
import subprocess

BASE = r"D:\Realdesktop\Wan\Important\New\paper_a2"
PDF = BASE + r"\main_ieee.pdf"
LETTER = BASE + r"\cover_letter.pdf"


def text(path, layout=True):
    cmd = ["pdftotext"] + (["-layout"] if layout else []) + [path, "-"]
    r = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8",
                       errors="replace")
    return r.stdout


doc = text(PDF)
letter = text(LETTER)
flat = re.sub(r"\s+", " ", doc)                 # for quoting context
nospace = re.sub(r"\s+", "", doc).upper()       # for robust heading search

print("=" * 78)
print("A. 章节/声明（对 small-caps 与换行容错）")
print("=" * 78)
sections = [
    ("Introduction", "INTRODUCTION"),
    ("Background and related work", "BACKGROUNDANDRELATEDWORK"),
    ("Materials and methods", "MATERIALSANDMETHODS"),
    ("Results", "RESULTS"),
    ("Engineering implications", "ENGINEERINGIMPLICATIONS"),
    ("Discussion", "DISCUSSION"),
    ("Conclusions", "CONCLUSIONS"),
    ("Appendix", "APPENDIX"),
    ("Data availability", "DATAAVAILABILITY"),
    ("Funding", "FUNDING"),
    ("Declaration of competing interests", "DECLARATIONOFCOMPETINGINTERESTS"),
    ("CRediT", "CREDIT"),
    ("Generative AI declaration", "GENERATIVEAI"),
    ("Acknowledgements", "ACKNOWLEDGEMENTS"),
]
for label, key in sections:
    n = nospace.count(key)
    print(f"  {label:<36} {'OK x%d' % n if n else '*** MISSING ***'}")

print()
print("=" * 78)
print("B. venue 专属残留（正文 + 参考文献）")
print("=" * 78)
for pat, label in [
    (r"Ocean Engineering", "'Ocean Engineering'"),
    (r"this journal", "'this journal'"),
    (r"Elsevier", "'Elsevier'"),
    (r"[Hh]ighlights", "'highlights'"),
    (r"graphical abstract", "'graphical abstract'"),
    (r"Pattern Recognition Letters", "'Pattern Recognition Letters'"),
]:
    hits = list(re.finditer(pat, flat))
    print(f"  {label:<30} {len(hits)} 次")
    for m in hits[:6]:
        a, b = max(0, m.start() - 80), min(len(flat), m.end() + 60)
        print(f"      ...{flat[a:b]}...")

print()
print("=" * 78)
print("C. 封面信的声明 vs 稿件实际内容")
print("=" * 78)
claims = [
    ("理论附录 self-contained", r"self-contained"),
    ("五个感知域", r"ImageNet-1K"),
    ("DTD", r"\bDTD\b"),
    ("Food101", r"Food101"),
    ("FathomNet 船载子集", r"FathomNet"),
    ("四个声学仪器", r"NKSID"),
    ("ARIS-3000 水槽", r"ARIS"),
    ("riku-1825", r"riku"),
    ("UATD", r"UATD"),
]
for label, pat in claims:
    n = len(re.findall(pat, flat, re.I))
    print(f"  {label:<28} {'OK x%d' % n if n else '*** NOT FOUND ***'}")

print()
print("=" * 78)
print("D. 参考文献：DOI / 稳定 URL 计数（对换行容错）")
print("=" * 78)
doi_refs = re.findall(r"doi:\s*10\.\S+", flat)
print(f"  含 'doi: 10.x' 的条目: {len(doi_refs)}")
for d in doi_refs:
    print(f"      {d[:78]}")
online = re.findall(r"\[Online\]", flat) + re.findall(r"https?://", flat)
print(f"  '[Online]' + 裸 URL 合计: {len(online)}")

print()
print("=" * 78)
print("E. 引用编号 1-29 是否都出现在正文/文献表中")
print("=" * 78)
nums = sorted({int(x) for x in re.findall(r"\[(\d{1,2})\]", flat) if 1 <= int(x) <= 29})
missing = [i for i in range(1, 30) if i not in nums]
print(f"  出现: {nums}")
print(f"  未出现: {missing if missing else '无'}")
