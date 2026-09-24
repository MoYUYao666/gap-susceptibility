"""修复 07_discussion.tex 里残留的 Python 源码片段（会印进 PDF 的内容缺陷）。

缺陷：limitations 段落里混入了三行 Python 原始字符串源码
      r'gradient-path gating ... '
      r'image-token path ... '
      r'not, and that the crossing ...'
它们在 LaTeX 里被当作正文排版，PDF 中可见为 "’ r’gradient-path ..."（编译审计查不出内容级缺陷）。
修法：去掉 r'...' 包装与行尾的 ' 残片，按原意拼回正文；其余文字不动。
"""
import re
import sys

P = 'paper_ap3/sections/07_discussion.tex'
OLD = ("isolated: '\r\n"
       "       r'gradient-path gating (Section~\\ref{sec:gradmask}, Table~\\ref{tab:gradmask}) shows that blocking the '\r\n"
       "       r'image-token path removes $79\\%$ of the $r{=}6$ damage while blocking the language-token path does '\r\n"
       "       r'not, and that the crossing itself still requires")
NEW = ("isolated: gradient-path gating (Section~\\ref{sec:gradmask}, Table~\\ref{tab:gradmask}) shows that blocking "
       "the image-token path removes $79\\%$ of the $r{=}6$ damage while blocking the language-token path does not, "
       "and that the crossing itself still requires")

src = open(P, encoding='utf-8', newline='').read()
if OLD not in src:
    print('FATAL: 锚点未找到（可能已修过或文件变了）')
    sys.exit(1)
src = src.replace(OLD, NEW, 1)
open(P, 'w', encoding='utf-8', newline='').write(src)

# 验证：不应再有以 r' 开头的整行
leftover = [i + 1 for i, ln in enumerate(src.split('\r\n')) if ln.lstrip().startswith("r'")]
print(f'修复完成；残留的 r\'-开头行：{leftover if leftover else "无"}')
print(f'检查 "gradient-path gating" 出现次数：{len(re.findall("gradient-path gating", src))}')
