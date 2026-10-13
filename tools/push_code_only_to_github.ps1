# Wipe and re-upload the GitHub repository (keeping only code and results)
#
# Background (operator instruction 2026-09-24):
#   * "wipe github and re-upload" (operator's wording, 2026-09-24)
#   * boundary (AGENTS.md): only code and results, no papers
#   * current state: publish/main tracks 1807 files, including many manuscripts and 11.96 GB of weight checkpoints
#
# Usage:
#   powershell -NoProfile -ExecutionPolicy Bypass -File tools\push_code_only_to_github.ps1
#       default is **read-only preview**: does not touch any worktree, does not commit, does not push.
#   powershell -NoProfile -ExecutionPolicy Bypass -File tools\push_code_only_to_github.ps1 -Execute
#       actually run: create publish/code-only in the publish worktree → clear the index → add from the whitelist → commit → force push.
#
# Three limitations you must know:
#   A. The local .git history is still kept (a good thing, do not lose it). The remote history is replaced by a single snapshot commit.
#   B. GitHub may still keep the old unreachable objects for a while (only server-side GC really removes them). To make them
#      "disappear completely", the only reliable way is to **delete the repository on GitHub and create an empty one**, then rerun this script (it does not depend on the old history).
#   C. On this machine git cannot reach the network inside the sandbox (`ls-remote` fails with an sh.exe signal pipe denial), so **the push must be performed by the operator**.

[CmdletBinding()]
param(
    [switch]$Execute,
    [string]$Remote = 'ssh-origin',
    [string]$Worktree = '.worktrees/publish-main',
    [string]$Branch = 'publish/code-only'
)

$ErrorActionPreference = 'Stop'
$repoRoot = (Resolve-Path (Join-Path $PSScriptRoot '..')).Path
$wt = Join-Path $repoRoot $Worktree
if (-not (Test-Path $wt)) { throw "publish worktree not found: $wt" }

$whitelist = @('tools', 'src', 'exp', 'experiments', 'outputs', 'docs',
               'README.md', 'requirements.txt', 'AGENTS.md', '.gitignore')
$heavyExt = '\.(pt|pth|ckpt|bin|safetensors|onnx)$'

Write-Host "=== 1) Read-only inventory (based on the current HEAD, nothing changed) ===" -ForegroundColor Cyan
$base = git -C $wt rev-parse --abbrev-ref HEAD
if ($base -ne 'publish/main') { Write-Host "  ⚠ current branch is $base (recommended to switch back to publish/main first)" -ForegroundColor Yellow }
$commit = git -C $wt rev-parse --short HEAD
Write-Host "  Worktree: $wt"
Write-Host "  Base:     $base @ $commit"

$tracked = git -C $wt ls-tree -r --name-only HEAD
Write-Host ("  Currently tracked: {0} files" -f ($tracked | Measure-Object).Count)

# To be included: under a whitelist prefix and not a weight file
$keep = $tracked | Where-Object {
    $p = $_
    ($whitelist | Where-Object { $p -eq $_ -or $p -like "$_/*" }) -and ($p -notmatch $heavyExt)
}
# To be removed: everything else (including all manuscripts) + weight files under the whitelist
$keepSet = @{}
$keep | ForEach-Object { $keepSet[$_] = $true }
$drop = $tracked | Where-Object { -not $keepSet.ContainsKey($_) }
$dropHeavy = $drop | Where-Object { $_ -match $heavyExt }
$dropPaper = $drop | Where-Object { $_ -notmatch $heavyExt }

Write-Host "`n=== 2) Plan ===" -ForegroundColor Cyan
Write-Host ("  Keep (code+results): {0} files" -f ($keep | Measure-Object).Count) -ForegroundColor Green
Write-Host ("  Remove (weights)   : {0} files (GitHub's per-file limit is 100 MB)" -f ($dropHeavy | Measure-Object).Count) -ForegroundColor Yellow
Write-Host ("  Remove (papers/etc): {0} files" -f ($dropPaper | Measure-Object).Count) -ForegroundColor Yellow

Write-Host "`n  Directory distribution of what is kept:"
$keep | ForEach-Object { ($_ -split '/')[0] } | Group-Object | Sort-Object Count -Descending |
    Select-Object -First 12 | ForEach-Object { Write-Host ("    {0,6}  {1}" -f $_.Count, $_.Name) }

Write-Host "`n  Directory distribution of removed manuscript files (should cover all paper*):"
$dropPaper | ForEach-Object { ($_ -split '/')[0] } | Group-Object | Sort-Object Count -Descending |
    Select-Object -First 12 | ForEach-Object { Write-Host ("    {0,6}  {1}" -f $_.Count, $_.Name) -ForegroundColor DarkYellow }

Write-Host "`n=== 3) Safety checks (dry run) ===" -ForegroundColor Cyan
$banned = $keep | Where-Object {
    $_ -match '(^|/)(cover_letter[^/]*\.(tex|pdf|docx))$' -or
    $_ -match '(^|/)(declaration[^/]*\.(tex|pdf|docx))$' -or
    $_ -match '(^|/)(title_page[^/]*\.(tex|pdf|docx))$' -or
    $_ -match '(^|/)(highlights[^/]*\.(tex|pdf))$' -or
    $_ -match '(^|/)(abstract[^/]*\.(tex|pdf))$' -or
    $_ -match '(^|/)main[^/]*\.(tex|pdf)$' -or
    $_ -match 'main_zh\.' -or
    $_ -match 'revision_additions'
}
if ($banned) {
    Write-Host "  ❌ manuscript-type files hit the keep list, the script logic is wrong:" -ForegroundColor Red
    $banned | Select-Object -First 20 | ForEach-Object { Write-Host "     $_" -ForegroundColor Red }
    exit 1
}
Write-Host "  ✅ 0 manuscript-type files in the keep list" -ForegroundColor Green

$bigKeep = @()
foreach ($f in $keep) {
    $full = Join-Path $wt $f
    if (Test-Path $full) {
        $mb = (Get-Item $full).Length / 1MB
        if ($mb -ge 100) { $bigKeep += [pscustomobject]@{ MB = [math]::Round($mb, 1); File = $f } }
    }
}
if ($bigKeep) {
    Write-Host "  ❌ the keep list contains files ≥100 MB (GitHub will reject them):" -ForegroundColor Red
    $bigKeep | ForEach-Object { Write-Host ("     {0,8} MB  {1}" -f $_.MB, $_.File) -ForegroundColor Red }
    exit 1
}
Write-Host "  ✅ no file ≥100 MB in the keep list" -ForegroundColor Green

if (-not $Execute) {
    Write-Host "`n=== Read-only preview finished: worktree untouched, nothing committed, nothing pushed ===" -ForegroundColor Yellow
    Write-Host "  Once confirmed, run (this force-pushes and overwrites the remote main history):"
    Write-Host "    powershell -NoProfile -ExecutionPolicy Bypass -File tools\push_code_only_to_github.ps1 -Execute" -ForegroundColor White
    exit 0
}

Write-Host "`n=== 4) Execute: create branch + clear index + add from whitelist ===" -ForegroundColor Cyan
git -C $wt checkout -B $Branch | Out-Null
git -C $wt reset --hard | Out-Null
git -C $wt rm -r --cached . --quiet
foreach ($p in $whitelist) {
    if (Test-Path (Join-Path $wt $p)) { git -C $wt add -- $p; Write-Host "  + $p" }
}
$heavyStaged = git -C $wt diff --cached --name-only | Where-Object { $_ -match $heavyExt }
if ($heavyStaged) {
    $heavyStaged | ForEach-Object { git -C $wt rm --cached --quiet -- $_ }
    Write-Host ("  removed {0} weight files" -f $heavyStaged.Count)
}

Write-Host "`n=== 5) Validate once more before executing (based on staged content) ===" -ForegroundColor Cyan
$staged = git -C $wt diff --cached --name-only
$bad = $staged | Where-Object {
    $_ -match '(cover_letter|declaration|title_page|highlights|abstract)[^/]*\.(tex|pdf|docx)$' -or
    $_ -match '(^|/)main[^/]*\.(tex|pdf)$' -or $_ -match 'main_zh\.' -or $_ -match 'revision_additions'
}
if ($bad) { Write-Host "  ❌ manuscript-type files still in the index, aborting:" -ForegroundColor Red; $bad | ForEach-Object { Write-Host "     $_" -ForegroundColor Red }; exit 1 }
Write-Host ("  ✅ {0} files staged, 0 manuscript-type" -f ($staged | Measure-Object).Count) -ForegroundColor Green

Write-Host "`n=== 6) Commit and force push ===" -ForegroundColor Cyan
git -C $wt -c user.name="Hongrui Wan" -c user.email="contact@example.com" `
    commit --quiet -m "Chore: publish code and results only (manuscripts, cover letters and checkpoints removed from tracking)"
git -C $wt log -1 --pretty=format:"  %h %ad %s" --date=format:"%Y-%m-%d %H:%M"; Write-Host ""
git -C $wt push --force $Remote "${Branch}:main"

Write-Host "`n=== 7) Verify ===" -ForegroundColor Cyan
git -C $wt ls-remote --heads $Remote
Write-Host "`nDone. The remote $Remote main now contains only code and results." -ForegroundColor Green
Write-Host "Reminder: when GitHub GCs the old remote objects is up to GitHub; to erase them completely, delete and recreate the repo and rerun this script." -ForegroundColor Yellow
