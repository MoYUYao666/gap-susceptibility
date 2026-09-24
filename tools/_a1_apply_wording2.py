"""补第 2 条：引言句在正文里内嵌了 \\cite{} 命令，故上一次空白容忍匹配失败。"""
import io
import re

P = 'paper_a1/main.tex'
s = io.open(P, encoding='utf-8').read()

old = (r"Because the gap is measurable and interpretable, it has become a de facto "
       r"health indicator: methods explicitly optimize gap reduction \cite{imod}, "
       r"gap change predicts retrieval degradation \cite{wan2026protect}, and "
       r"gap-aware early stopping has been proposed as a training-time signal "
       r"\cite{wan2026protect}.")

new = (r"Because the gap is measurable and interpretable, it is widely used as a "
       r"diagnostic of alignment and retrieval and is often read implicitly as a "
       r"quality proxy: methods explicitly optimize gap reduction \cite{imod}, "
       r"gap change predicts retrieval degradation \cite{wan2026protect}, and "
       r"gap-aware early stopping has been proposed as a training-time signal "
       r"\cite{wan2026protect}. What we dispute is the \emph{unconditional} form "
       r"of that reading, not its usefulness for alignment and retrieval.")

pat = re.compile(r'\s+'.join(re.escape(t) for t in old.split()), flags=re.S)
hits = pat.findall(s)
print('命中 %d 次' % len(hits))
if len(hits) == 1:
    s = pat.sub(lambda m: new, s, count=1)
    io.open(P, 'w', encoding='utf-8').write(s)
    print('已替换第 2 条 ✓')
else:
    print('未替换，需人工确认')
