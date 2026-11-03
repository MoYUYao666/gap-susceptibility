# 在独立目录里构建"只含代码与结果"的全新 git 仓库（不碰现有仓库与工作树）
#
# 为什么另建：`git rm -r --cached .` 在本机沙箱内静默失效（sh.exe 报错），
# 在原发布工作树里改索引不可靠。另建目录 = 全新 .git，不依赖任何现有索引状态。
#
# 产物：D:\Realdesktop\Wan\Important\New\publish_clean\
#
# 用法：
#   powershell -NoProfile -ExecutionPolicy Bypass -File tools\build_publish_repo.ps1 [-SkipPush]

[CmdletBinding()]
param(
    [switch]$SkipPush,
    [string]$Target = 'D:\Realdesktop\Wan\Important\New\publish_clean',
    [string]$Remote = 'ssh-origin',
    [string]$RepoUrl = 'ssh://git@github.com/MoYUYao666/gap-susceptibility.git'
)

$ErrorActionPreference = 'Stop'
$repoRoot = (Resolve-Path (Join-Path $PSScriptRoot '..')).Path

Write-Host "=== 1) 准备目标目录 $Target ===" -ForegroundColor Cyan
if (Test-Path $Target) {
    Write-Host "  目录已存在，清空它（只影响这个新建目录）" -ForegroundColor Yellow
    Remove-Item $Target -Recurse -Force
}
New-Item -ItemType Directory -Path $Target -Force | Out-Null

Write-Host "`n=== 2) 复制白名单内容（robocopy /E）===" -ForegroundColor Cyan
$jobs = @(
    @{ src = 'tools';        xd = '';  xf = '_docs_*;_*venue*;_*review*;_*prl*;_*status*;_*handover*;_*cover_letter*;_*highlights*;_*submission*;_*compliance*;_*reply*;_*response*;_*reject*;_*ap3*;_*roster*;_*archive_*' },
    @{ src = 'src';          xd = '';  xf = '' },
    @{ src = 'exp';          xd = '';  xf = '' },
    @{ src = 'experiments';  xd = '';  xf = '' },
    # docs excluded from v2.8 at the operator's request (kept in earlier tags)
    # @{ src = 'docs';         xd = '_superseded;backups'; xf = '' },
    @{ src = 'outputs';      xd = 'logs;strict_freeze;__pycache__'; xf = '*.pt;*.pth;*.ckpt;*.bin;*.safetensors;*.onnx;*.zip;*.parquet;*.bak;*.log;*.err;*.txt;*.pyc;*review*;*venue*;*submission*;*response*;*reject*;*decision*;*inventory*;*roster*;*highlights*;*provenance_map_draft*;*lessons_checklist*;*stats_hardened*;*audit_postfix*;*audit_refresh*;*submitted_pdf_audit*;*supp_duplicate_check*;*a1_history*;*pr_to_fixes_map*' },
    @{ src = 'paper_a3';     xd = 'data;models;runs;draft;submission;docs;hf_cache;local_runs'; xf = '*.pt;*.pdf;*.zip;*.docx;*.jsonl;*.png' }
    @{ src = 'paper_rsvlm_survey'; xd = 'draft;submission;isprsj;mdpi_template;figures;__pycache__;grrsm;supplement'; xf = '*.pdf;*.txt;*.zip;*.docx;*.png;*.pyc;*.aux;*.log;*.bbl;*.blg;*.out;*.fls;*.fdb_latexmk;outline.md;self_review_2026-10-28.md;SUBMISSION_CHECKLIST.md;shortlist_2026-10-27.md' }
)
foreach ($j in $jobs) {
    $s = Join-Path $repoRoot $j.src
    $d = Join-Path $Target $j.src
    if (-not (Test-Path $s)) { Write-Host "  - $($j.src)（不存在，跳过）" -ForegroundColor DarkGray; continue }
    $args = @($s, $d, '/E', '/NFL', '/NDL', '/NJH', '/NJS', '/NP', '/R:1', '/W:1')
    if ($j.xd) { $args += '/XD'; $args += ($j.xd -split ';' | ForEach-Object { Join-Path $s $_ }) }
    if ($j.xf) { $args += '/XF'; $args += ($j.xf -split ';') }
    & robocopy @args | Out-Null
    $n = (Get-ChildItem $d -Recurse -File -Force -ErrorAction SilentlyContinue | Measure-Object).Count
    Write-Host ("  + {0,-12} {1,6} 文件" -f $j.src, $n)
}
foreach ($f in 'README.md', 'requirements.txt', 'CITATION.cff', '.gitignore') {
    $s = Join-Path $repoRoot $f
    if (Test-Path $s) { Copy-Item $s (Join-Path $Target $f) -Force; Write-Host "  + $f" }
}

# small derived corpora and manifests (the large corpora are excluded by xf)
$small = @(
    'paper_a3/corpora/rsicd/llmcaption.jsonl',
    'paper_a3/corpora/rsicd/llmcaption2.jsonl',
    'paper_a3/corpora/rsicd/repeated.jsonl',
    'paper_a3/corpora/rsicd/provenance_manifest.json',
    'paper_a3/corpora/nwpu_captions/llmcaption.jsonl',
    'paper_a3/corpora/nwpu_captions/provenance_manifest.json',
    'paper_a3/corpora/rsitmd/provenance_manifest.json',
    'paper_a3/corpora/dior_rsvg/provenance_manifest.json'
)
foreach ($rel in $small) {
    $s = Join-Path $repoRoot $rel
    if (Test-Path $s) {
        $d = Join-Path $Target $rel
        New-Item -ItemType Directory -Force -Path (Split-Path $d -Parent) | Out-Null
        Copy-Item $s $d -Force
        Write-Host "  + $rel" -ForegroundColor DarkGray
    }
}

# drop caches and backup artifacts that are not part of the published result set
Get-ChildItem $Target -Recurse -Directory -Force -ErrorAction SilentlyContinue |
    Where-Object { $_.Name -eq '__pycache__' -or $_.Name -like '_fig_backup*' } |
    ForEach-Object { Remove-Item $_.FullName -Recurse -Force -ErrorAction SilentlyContinue }

Write-Host "`n=== 3) 校验：稿件类文件与超限文件必须为 0 ===" -ForegroundColor Cyan
$all = Get-ChildItem $Target -Recurse -File -Force
Write-Host ("  总文件数: {0} / {1} MB" -f $all.Count, [math]::Round(($all | Measure-Object Length -Sum).Sum / 1MB, 1))
$bad = $all | Where-Object {
    $_.Name -match '^(cover_letter|declaration|title_page|highlights|abstract)[^/]*\.(tex|pdf|docx)$' -or
    $_.Name -match '^main[^/]*\.(tex|pdf)$' -or $_.Name -match 'main_zh\.' -or $_.Name -match 'revision_additions'
}
if ($bad) { Write-Host "  ❌ 稿件类文件:" -ForegroundColor Red; $bad | Select-Object -First 20 | ForEach-Object { Write-Host "     $($_.FullName)" -ForegroundColor Red }; exit 1 }
Write-Host "  ✅ 稿件类文件 0 个" -ForegroundColor Green
$big = $all | Where-Object { $_.Length -ge 100MB }
if ($big) { Write-Host "  ❌ ≥100 MB:" -ForegroundColor Red; $big | ForEach-Object { Write-Host ("     {0,8} MB  {1}" -f [math]::Round($_.Length/1MB,1), $_.FullName) -ForegroundColor Red }; exit 1 }
Write-Host "  ✅ 无 ≥100 MB 文件" -ForegroundColor Green

# internal working material must never be published (incident 2026-11-03)
$internal = $all | Where-Object {
    $rel = ($_.FullName.Substring($Target.Length).TrimStart('\')) -replace '\\', '/'
    $rel -like 'docs/*' -or
    $rel -eq 'AGENTS.md' -or
    $rel -eq 'CLAUDE.md' -or
    $rel -like 'local_runs/*' -or
    (($rel -like '*.pdf' -or $rel -like '*.docx') -and $rel -notlike 'outputs/*')
}
if ($internal) { Write-Host "  ❌ 内部/稿件材料:" -ForegroundColor Red; $internal | Select-Object -First 20 | ForEach-Object { Write-Host ("     " + $_.FullName) -ForegroundColor Red }; exit 1 }
Write-Host "  ✅ 无 docs/AGENTS.md/PDF/DOCX 内部材料" -ForegroundColor Green

Write-Host "`n=== 4) git init + 单条提交 ===" -ForegroundColor Cyan
# 注意：git 会把 "LF will be replaced by CRLF" 写到 stderr，PS 5.1 在
# $ErrorActionPreference='Stop' 下会把它当终止错误 —— 故此处放宽。
$ErrorActionPreference = 'Continue'
git -C $Target init -q -b main
git -C $Target add -A
$staged = git -C $Target diff --cached --name-only
Write-Host ("  暂存: {0} 个文件" -f ($staged | Measure-Object).Count)
git -C $Target -c user.name="Hongrui Wan" -c user.email="2024282101@hrbeu.edu.cn" `
    commit -q -m "Code and results only: analysis/audit scripts, result JSONs and method docs (no manuscripts)"
git -C $Target log -1 --pretty=format:"  %h %ad %s" --date=format:"%Y-%m-%d %H:%M"; Write-Host ""
$size = [math]::Round((Get-ChildItem (Join-Path $Target '.git') -Recurse -File -Force | Measure-Object Length -Sum).Sum / 1MB, 1)
Write-Host ("  .git 体积: {0} MB" -f $size)

Write-Host "`n=== 5) 配置远端 ===" -ForegroundColor Cyan
git -C $Target remote add $Remote $RepoUrl
git -C $Target remote -v

if ($SkipPush) {
    Write-Host "`n=== 已跳过推送（-SkipPush）===" -ForegroundColor Yellow
    Write-Host "  推送命令："
    Write-Host "    git -C `"$Target`" push --force $Remote main" -ForegroundColor White
    exit 0
}

Write-Host "`n=== 6) force push（覆盖远端 main 历史）===" -ForegroundColor Cyan
git -C $Target push --force $Remote main
Write-Host "`n=== 7) 复核 ===" -ForegroundColor Cyan
git -C $Target ls-remote --heads $Remote
Write-Host "完成。远端 main 现在只有代码与结果。" -ForegroundColor Green
