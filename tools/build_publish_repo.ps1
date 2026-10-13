# Build a brand-new git repository with "code and results only" in a separate directory (without touching the existing repo or worktree)
#
# Why build separately: `git rm -r --cached .` silently fails inside the local sandbox (sh.exe errors),
# so editing the index in the original publish worktree is unreliable. A separate directory = a fresh .git, with no dependence on any existing index state.
#
# Artifact: D:\Realdesktop\Wan\Important\New\publish_clean\
#
# Usage:
#   powershell -NoProfile -ExecutionPolicy Bypass -File tools\build_publish_repo.ps1 [-SkipPush]

[CmdletBinding()]
param(
    [switch]$SkipPush,
    [string]$Target = 'D:\Realdesktop\Wan\Important\New\publish_clean',
    [string]$Remote = 'ssh-origin',
    [string]$RepoUrl = 'ssh://git@github.com/OWNER/gap-susceptibility.git'
)

$ErrorActionPreference = 'Stop'
$repoRoot = (Resolve-Path (Join-Path $PSScriptRoot '..')).Path

Write-Host "=== 1) preparing the target directory $Target ===" -ForegroundColor Cyan
if (Test-Path $Target) {
    Write-Host "  directory already exists, emptying it (affects only this newly built directory)" -ForegroundColor Yellow
    Remove-Item $Target -Recurse -Force
}
New-Item -ItemType Directory -Path $Target -Force | Out-Null

Write-Host "`n=== 2) copying the whitelisted content (robocopy /E) ===" -ForegroundColor Cyan
$jobs = @(
    @{ src = 'tools';        xd = '';  xf = '' },
    @{ src = 'src';          xd = '';  xf = '' },
    @{ src = 'exp';          xd = '';  xf = '' },
    @{ src = 'experiments';  xd = '';  xf = '' },
    @{ src = 'docs';         xd = '_superseded;backups'; xf = '' },
    @{ src = 'outputs';      xd = 'logs;strict_freeze;__pycache__'; xf = '*.pt;*.pth;*.ckpt;*.bin;*.safetensors;*.onnx;*.zip;*.parquet' }
)
foreach ($j in $jobs) {
    $s = Join-Path $repoRoot $j.src
    $d = Join-Path $Target $j.src
    if (-not (Test-Path $s)) { Write-Host "  - $($j.src) (does not exist, skipping)" -ForegroundColor DarkGray; continue }
    $args = @($s, $d, '/E', '/NFL', '/NDL', '/NJH', '/NJS', '/NP', '/R:1', '/W:1')
    if ($j.xd) { $args += '/XD'; $args += ($j.xd -split ';' | ForEach-Object { Join-Path $s $_ }) }
    if ($j.xf) { $args += '/XF'; $args += ($j.xf -split ';') }
    & robocopy @args | Out-Null
    $n = (Get-ChildItem $d -Recurse -File -Force -ErrorAction SilentlyContinue | Measure-Object).Count
    Write-Host ("  + {0,-12} {1,6} files" -f $j.src, $n)
}
foreach ($f in 'README.md', 'requirements.txt', 'AGENTS.md', '.gitignore') {
    $s = Join-Path $repoRoot $f
    if (Test-Path $s) { Copy-Item $s (Join-Path $Target $f) -Force; Write-Host "  + $f" }
}

Write-Host "`n=== 3) validation: manuscript-type files and oversized files must both be 0 ===" -ForegroundColor Cyan
$all = Get-ChildItem $Target -Recurse -File -Force
Write-Host ("  total files: {0} / {1} MB" -f $all.Count, [math]::Round(($all | Measure-Object Length -Sum).Sum / 1MB, 1))
$bad = $all | Where-Object {
    $_.Name -match '^(cover_letter|declaration|title_page|highlights|abstract)[^/]*\.(tex|pdf|docx)$' -or
    $_.Name -match '^main[^/]*\.(tex|pdf)$' -or $_.Name -match 'main_zh\.' -or $_.Name -match 'revision_additions'
}
if ($bad) { Write-Host "  ❌ manuscript-type files:" -ForegroundColor Red; $bad | Select-Object -First 20 | ForEach-Object { Write-Host "     $($_.FullName)" -ForegroundColor Red }; exit 1 }
Write-Host "  ✅ 0 manuscript-type files" -ForegroundColor Green
$big = $all | Where-Object { $_.Length -ge 100MB }
if ($big) { Write-Host "  ❌ ≥100 MB:" -ForegroundColor Red; $big | ForEach-Object { Write-Host ("     {0,8} MB  {1}" -f [math]::Round($_.Length/1MB,1), $_.FullName) -ForegroundColor Red }; exit 1 }
Write-Host "  ✅ no files ≥100 MB" -ForegroundColor Green

Write-Host "`n=== 4) git init + single commit ===" -ForegroundColor Cyan
# Note: git writes "LF will be replaced by CRLF" to stderr, and PS 5.1 with
# $ErrorActionPreference='Stop' treats that as a terminating error -- so we relax it here.
$ErrorActionPreference = 'Continue'
git -C $Target init -q -b main
git -C $Target add -A
$staged = git -C $Target diff --cached --name-only
Write-Host ("  staged: {0} files" -f ($staged | Measure-Object).Count)
git -C $Target -c user.name="Hongrui Wan" -c user.email="contact@example.com" `
    commit -q -m "Code and results only: analysis/audit scripts, result JSONs and method docs (no manuscripts)"
git -C $Target log -1 --pretty=format:"  %h %ad %s" --date=format:"%Y-%m-%d %H:%M"; Write-Host ""
$size = [math]::Round((Get-ChildItem (Join-Path $Target '.git') -Recurse -File -Force | Measure-Object Length -Sum).Sum / 1MB, 1)
Write-Host ("  .git size: {0} MB" -f $size)

Write-Host "`n=== 5) configuring the remote ===" -ForegroundColor Cyan
git -C $Target remote add $Remote $RepoUrl
git -C $Target remote -v

if ($SkipPush) {
    Write-Host "`n=== push skipped (-SkipPush) ===" -ForegroundColor Yellow
    Write-Host "  push command:"
    Write-Host "    git -C `"$Target`" push --force $Remote main" -ForegroundColor White
    exit 0
}

Write-Host "`n=== 6) force push (overwrites the remote main history) ===" -ForegroundColor Cyan
git -C $Target push --force $Remote main
Write-Host "`n=== 7) verification ===" -ForegroundColor Cyan
git -C $Target ls-remote --heads $Remote
Write-Host "Done. The remote main now contains only code and results." -ForegroundColor Green
