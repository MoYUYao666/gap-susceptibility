# -*- coding: utf-8 -*-
"""
Add a P1 spec to tools/build_submission_packages.py so the Pattern Recognition package is
generated from paper/ like the A1 and A23 ones, and let the generator own its README.
"""
import io
import os
import sys

P = os.path.join(r"D:\Realdesktop\Wan\Important\New", "tools", "build_submission_packages.py")
src = io.open(P, encoding="utf-8").read()

SPEC = '''
SECTIONS = ['sections/%s.tex' % s for s in (
    'introduction', 'related_work', 'methodology', 'experiments',
    'strict_control', 'visual_fragility', 'discussion', 'conclusion', 'supplementary')]

FIGURES = ['figures/%s.png' % f for f in (
    'fig1', 'fig2', 'fig3', 'fig4', 'fig5', 'fig6', 'fig7',
    'fig8_weight_svd', 'fig9_noise_sensitivity', 'fig10_layered_ft', 'fig11_gsnr',
    'fig12_zeroshot_more', 'fig13_vitl_layered', 'fig14_adapter_layered')]

P1 = {
    'dest': 'P1_PatternRecognition',
    'src': 'paper',
    'title': 'P1 -> Pattern Recognition (Elsevier), revision upload (PR-D-26-10149)',
    'manuscript': "Protect, Don't Perturb: Cross-Modal Alignment under PEFT of Vision-Language Models",
    'renames': {'main_nn.tex': 'main.tex'},
    'files': [
        ('LaTeX source (manuscript + section files)', ['main_nn.tex', 'references.bib'] + SECTIONS),
        ('Figures (referenced by main.tex and the supplementary)', FIGURES),
        ('Manuscript PDF (43 pages)', ['main_nn.pdf']),
        ('Revision cover letter', ['cover_letter_revision.tex', 'cover_letter_revision.pdf']),
        ('Highlights', ['highlights.tex', 'highlights.pdf']),
        ('Declaration of competing interests', ['declaration.tex', 'declaration.pdf']),
        ('Title page', ['title_page.tex']),
    ],
    'excluded': [
        ('main_zh.*', 'no Chinese mirror for this manuscript'),
        ('_p1pdf.txt / main_nn.aux / main_nn.log / main_nn.bbl / main_nn.out', 'build artifacts and the extracted-text dump used for verification'),
        ('cover_letter.tex / cover_letter.pdf / cover_letter_zeroshot_correction.*', 'the two 2026-08-14 correction letters already held by the journal; kept for provenance only'),
        ('_superseded_2026/', 'pre-remediation artefacts (an abstract that contradicted the manuscript, a title page naming a different journal and institution, superseded declarations)'),
        ('figures/*.svg, figures/*.pdf', 'vector twins of the PNGs actually referenced by the manuscript'),
    ],
    'system_items': [
        'Version on file: the manuscript in Editorial Manager is still the 24 July 2026 snapshot, which reports 24%%, 53.3%%/1.7%%/+0.079, CIFAR-100, 116 experiments and r=-0.827/-0.807. The revision cover letter reconciles that version against this one row by row.',
        'Strict-freeze control: only the text-only arm is complete (5 seeds, 196,608 trainable parameters, 0 of 199 vision_model.* tensors changed, CG delta -0.0465 +/- 0.0027). The joint arm costs about 52 minutes per seed because it forces a full vision-side backward pass; run tools/_p1_add_joint_rows.py after it and the table updates itself.',
        'Change-score correlations differ from the 2026-08-14 letter (-0.042/+0.012 there, +0.134/+0.190 recomputed on the reproducible archive). The letter says so.',
        'Generative-AI declaration and Funding statement: both present in the manuscript before the reference list.',
        'Data availability: the manuscript states that the archive will be made public on publication and is available to the reviewers on request.',
        'Length: 43 pages double-spaced including figures and appendices; no page limit was applied.',
    ],
}

'''

if "P1 = {" in src:
    print("P1 spec already present")
else:
    anchor = "\n\ndef sha256(path):"
    if anchor not in src:
        print("FAIL: anchor not found")
        sys.exit(1)
    src = src.replace(anchor, SPEC + anchor, 1)
    src = src.replace("for spec in (A1, A23):", "for spec in (A1, A23, P1):", 1)
    io.open(P, "w", encoding="utf-8", newline="").write(src)
    print("P1 spec added; loop updated")

assert "for spec in (A1, A23, P1):" in io.open(P, encoding="utf-8").read()
print("OK")
