"""回归验证: 第三轮(文字/一致性)审计的修复项。"""
import glob
import re

tex = {}
for f in glob.glob('paper_ap3/sections/*.tex') + ['paper_ap3/main.tex']:
    tex[f.replace('\\', '/')] = open(f, encoding='utf-8').read()
allt = '\n'.join(tex.values())
disc = tex.get('paper_ap3/sections/07_discussion.tex', '')
assert disc, 'discussion file not loaded'


def chk(name, cond):
    print(('  OK   ' if cond else '  FAIL ') + name)


print('=== 结构/重复 ===')
l23 = disc.split('\n')[22]
chk('重复片段已删除 (1007 字符)', 'at rank 6' in l23 and l23.count('at rank 6') == 1)
chk('Sixteenth 在 Fifteenth 之后', l23.index('Fifteenth,') < l23.index('Sixteenth,'))
chk('"undetermined. Eighth" 断句已修', 'is undetermined. Eighth' in l23)
chk('"The reported 1-epoch" 大小写已修', '. The reported 1-epoch' in l23)

print('=== 指针 ===')
chk('自指已改指 β 小节', 'Section~\\ref{sec:beta_sel}' in tex['paper_ap3/sections/06_crossarch.tex'])
chk('二项检验指针→§6.2', 'Section~\\ref{sec:phase_trans}' in tex['paper_ap3/sections/06_crossarch.tex'])
chk('NaN 指针→附录 B', 'Appendix~\\ref{app:details}' in tex['paper_ap3/sections/06_crossarch.tex'])
chk('定理 W6 指针→§5', 'Section~\\ref{sec:dynamics}' in tex['paper_ap3/sections/03_theory.tex'])
chk('定理 W4/W5 错误指针已清', 'Section~\\ref{sec:special} CLIP data' not in allt)
chk('"116 catalog released with code" 措辞与结论一致', 'is available together with the analysis code' in allt and 'is released with the code' not in allt)

print('=== 图表题 ===')
chk('tab:position 题注已限定', 'architecture- and dataset-dependent' in allt)
chk('fig:p3ers 方向词已修', 'at a \\emph{higher} rank than the 3-epoch critical rank' in allt)
chk('fig:zeroshot 题注收窄', 'full fine-tuning is excluded from this comparison' in allt)
chk('tab:policy "comparable budget" 全局一致', 'comparable budget' in allt and 'matched budget' not in allt)

print('=== 声明范围 ===')
chk('定理限定 fixed E(摘要)', 'For a fixed alignment energy' in tex['paper_ap3/main.tex'])
chk('定理限定 fixed E(引言)', 'for a fixed alignment energy $E$' in allt)
chk('定理限定 fixed E(结论)', 'for a fixed alignment energy $E$' in tex['paper_ap3/sections/08_conclusion.tex'])
chk('r_c 条件化(引言 C3)', 'protocol-conditional in location' in allt)
chk('r_c 条件化(结论 C3)', 'configuration-conditional, Section~\\ref{sec:crossarch}' in tex['paper_ap3/sections/08_conclusion.tex'])
chk('C2 端到端负结果(引言)', 'measured negative, Section~\\ref{sec:crossarch}' in allt)
chk('SigLIP 例外(讨论)', 'SigLIP the two positions are indistinguishable' in allt or 'on SigLIP the two positions' in allt)
chk('regime 21-23 空白已注明', 'the boundary between $r=20$ and $r=24$ is not resolved' in allt)

print('=== 符号/缩写 ===')
chk('(AX*) 命名已改 R*', '(AX' not in allt)
chk('thm:proj 已加标签并被证明引用', '\\label{thm:proj}' in allt and 'Proof of Theorem~\\ref{thm:proj}' in allt)
chk('附录 F 公式补回 ‖g_m‖', '\\Gamma_m \\|g_m\\|' in allt)
chk('Appendix B 版本号更新', 'bitsandbytes 0.50.2' in allt)
chk('Appendix B vision 适配器披露', 'also\ncovers its self-attention' in allt or 'also covers its self-attention' in allt.replace('\n', ' '))
chk('硬编码 Equation (5) 已清', 'Equation~(5)' not in allt)
chk('β=0.137 已辨析', 'numerically coincident with, but conceptually' in allt)
chk('KKT 展开', 'Karush--Kuhn--Tucker (KKT)' in allt)
chk('BH-FDR 展开', 'Benjamini--Hochberg false-discovery-rate (BH-FDR)' in allt)
chk('QLoRA/NTK/SVD/VLM 已展开', 'QLoRA' in allt and 'neural-tangent-kernel (NTK)' in allt and 'singular-value-decomposition (SVD)' in allt and 'vision-language models (VLMs)' in allt)
