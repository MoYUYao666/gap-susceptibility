# -*- coding: utf-8 -*-
"""Build the two journal submission folders under SUBMISSION/.

Each folder holds exactly the files that go to the journal, plus a README that says
which upload slot each one belongs in and which files in the paper directory were
deliberately left out.  The paper directories remain the single source of truth:
this script copies *from* them, so re-run it after any edit rather than editing here.

SUBMISSION/ is generated and is listed in .gitignore; it is still covered by the
local backup."""
import hashlib
import io
import os
import shutil
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, 'SUBMISSION')

A1 = {
    'dest': 'A1_Neurocomputing',
    'src': 'paper_a1',
    'title': 'A1 -> Neurocomputing (Elsevier)',
    'manuscript': 'The Modality Gap Is Not a Universal Health Metric: Order Preservation Governs Zero-Shot Robustness',
    'renames': {'cover_letter.pdf': 'Cover letter.pdf'},
    'files': [
        ('LaTeX source (manuscript)', ['main.tex', 'related_work.tex', 'related_work_bibitems.tex']),
        ('Manuscript PDF', ['main.pdf']),
        ('Cover letter', ['cover_letter.tex', 'cover_letter.pdf']),
        ('Highlights', ['highlights.tex', 'highlights.pdf']),
        ('Declaration of Interest', ['declaration.tex', 'declaration.pdf', 'declaration_of_interest.docx']),
        ('Figures (vector PDF, referenced by main.tex)', [
            'figures/fig1_lambda.pdf', 'figures/fig2_tau_top1.pdf',
            'figures/fig3_trajectory.pdf', 'figures/fig4_spectrum.pdf']),
        ('Abstract (standalone page, for systems that ask for it separately)', ['abstract.tex', 'abstract.pdf']),
    ],
    'excluded': [
        ('main_zh.tex / main_zh.pdf', 'Chinese reference translation; not submitted to an English-language journal'),
        ('revision_additions.tex', 'internal audit record of the eight-block revision package; it is not \\input by main.tex and is not part of the manuscript'),
        ('figures/graphical_abstract.png', 'Neurocomputing requires no graphical abstract; the file is portrait and would need transposing only if reused for a journal that does'),
        ('_archive_prl/', 'superseded Pattern Recognition Letters-era submission files, kept for provenance'),
        ('*.aux / *.log / *.out / *.spl', 'LaTeX build artifacts'),
    ],
    'system_items': [
        'Data availability statement: state that the code and data are available at github.com/OWNER/gap-susceptibility (public repository), matching the closing sentence of the manuscript.',
        'Declaration of Interest: complete the online Elsevier declarations tool and upload its Word output; the .docx here is an author-side draft so the wording is settled in advance.',
        'CRediT: the manuscript has a single author, and the guide frames CRediT around co-author contributions, so no CRediT block is included.',
        'Generative-AI declaration: already carried in the manuscript, in a new section before the reference list, as the guide requires.',
    ],
}

A23 = {
    'dest': 'A23_OceanEngineering',
    'src': 'paper_a2',
    'title': 'A23 -> Ocean Engineering (Elsevier)',
    'manuscript': 'Alignment health across perception modalities: a gap-surgery diagnostic for marine vision and acoustic sonar models',
    'renames': {'cover_letter.pdf': 'Cover letter.pdf'},
    'files': [
        ('LaTeX source (manuscript + extension parts)', [
            'main.tex', 'ext_partI_theory.tex', 'ext_partII_domains.tex',
            'ext_partIII_dynamics.tex', 'ext_partIV_degradation.tex', 'ext_partV_mechanisms.tex']),
        ('Figures (referenced by main.tex)', [
            'figures/fig1_lambda.png', 'figures/fig2_sigma.png', 'figures/fig3_taupred.png',
            'figures/fig4_peft.png', 'figures/fig5_degradation.png',
            'figures/fig6_sonar_lambda.png', 'figures/fig7_sonar_sigma.png']),
        ('Manuscript PDF', ['main.pdf']),
        ('Cover letter', ['cover_letter.tex', 'cover_letter.pdf']),
        ('Highlights', ['highlights.tex', 'highlights.pdf', 'highlights.docx']),
        ('Declaration of Interest', ['declaration_of_interest.docx']),
        ('Abstract (standalone page, for systems that ask for it separately)', ['abstract.tex', 'abstract.pdf']),
    ],
    'excluded': [
        ('main_zh.tex / main_zh.pdf, zh_ext_part*.tex', 'Chinese mirror of the manuscript and its extension parts; not submitted'),
        ('*.aux / *.log / *.out', 'LaTeX build artifacts'),
    ],
    'system_items': [
        'Data availability statement: required at submission (guide :901); the manuscript carries a Data availability section.',
        'Declaration of Interest: complete the online Elsevier declarations tool and upload its Word output; the .docx here is an author-side draft.',
        'CRediT authorship contribution statement: present in the manuscript.',
        'Generative-AI declaration: present in the manuscript, before the reference list, as the guide requires.',
        'Length: the manuscript is 65 double-spaced pages against the guide\'s "preferably not more than 40" (:189). The wording is soft and nothing was cut.',
    ],
}

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
        'Version history: the original submission is dated 24 July 2026 and reported 24%%, 53.3%%/1.7%%/+0.079, CIFAR-100, 116 experiments and r=-0.827/-0.807; a round of corrections followed on 14 August. The revision cover letter reconciles the original submission against this revision row by row.',
        'Strict-freeze control: only the text-only arm is complete (5 seeds, 196,608 trainable parameters, 0 of 199 vision_model.* tensors changed, CG delta -0.0465 +/- 0.0027). The joint arm costs about 52 minutes per seed because it forces a full vision-side backward pass; run tools/_p1_add_joint_rows.py after it and the table updates itself.',
        'Change-score correlations differ from the 2026-08-14 letter (-0.042/+0.012 there, +0.134/+0.190 recomputed on the reproducible archive). The letter says so.',
        'Generative-AI declaration and Funding statement: both present in the manuscript before the reference list.',
        'Data availability: the manuscript states that the archive will be made public on publication and is available to the reviewers on request.',
        'Length: 43 pages double-spaced including figures and appendices; no page limit was applied.',
    ],
}



def sha256(path):
    h = hashlib.sha256()
    with open(path, 'rb') as f:
        for chunk in iter(lambda: f.read(1 << 20), b''):
            h.update(chunk)
    return h.hexdigest()


def build(spec):
    src_dir = os.path.join(ROOT, spec['src'])
    dest_dir = os.path.join(OUT, spec['dest'])
    if os.path.isdir(dest_dir):
        shutil.rmtree(dest_dir)
    os.makedirs(dest_dir)

    copied, total_bytes = [], 0
    lines = []
    for slot, names in spec['files']:
        lines.append('## %s' % slot)
        lines.append('')
        for rel in names:
            s = os.path.join(src_dir, rel.replace('/', os.sep))
            if not os.path.isfile(s):
                print('ABORT: missing source file %s' % s)
                sys.exit(1)
            d = os.path.join(dest_dir, rel.replace('/', os.sep))
            os.makedirs(os.path.dirname(d), exist_ok=True)
            shutil.copy2(s, d)
            final_rel = spec.get('renames', {}).get(rel, rel)
            if final_rel != rel:
                os.replace(d, os.path.join(dest_dir, final_rel.replace("/", os.sep)))
            copied.append(final_rel)
            total_bytes += os.path.getsize(s)
            lines.append('| `%s` | %d B | `%s` |' % (final_rel, os.path.getsize(s), sha256(s)[:16]))
        lines.append('')

    readme = []
    readme.append('# %s' % spec['title'])
    readme.append('')
    readme.append('**Manuscript:** %s' % spec['manuscript'])
    readme.append('')
    readme.append('This folder is **generated** by `tools/build_submission_packages.py` from `%s/`.' % spec['src'])
    readme.append('Edit the manuscript in `%s/`, then re-run the script -- do not edit files here, they will be overwritten.' % spec['src'])
    readme.append('')
    readme.append('## Files in this folder (%d files, %.1f MB)' % (len(copied), total_bytes / 1e6))
    readme.append('')
    readme.append('| File | Size | SHA256 (first 16) |')
    readme.append('|---|---|---|')
    readme.extend(lines)
    readme.append('## Deliberately NOT included')
    readme.append('')
    for name, why in spec['excluded']:
        readme.append('- **%s** -- %s' % (name, why))
    readme.append('')
    readme.append('## Submission-system items (not files)')
    readme.append('')
    for item in spec['system_items']:
        readme.append('- %s' % item)
    readme.append('')
    with io.open(os.path.join(dest_dir, 'README.md'), 'w', encoding='utf-8', newline='\n') as f:
        f.write('\n'.join(readme))
    return copied, total_bytes


for spec in (A1, A23, P1):
    copied, nb = build(spec)
    print('%-24s %2d files  %7.2f MB  -> SUBMISSION/%s/' % (spec['manuscript'][:22], len(copied), nb / 1e6, spec['dest']))
print('')
print('SUBMISSION/ rebuilt.')
