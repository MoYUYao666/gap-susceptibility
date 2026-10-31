# 把 GitHub 仓库清空重传（只留代码与结果）
#
# 背景（操作者 2026-09-24 指示）：
#   * "github 清空重新上传"
#   * 边界（AGENTS.md）：只放代码与结果，不放论文
#   * 现状：publish/main 跟踪 1807 个文件，含大量稿件与 11.96 GB 权重检查点
#
# 用法：
#   powershell -NoProfile -ExecutionPolicy Bypass -File tools\push_code_only_to_github.ps1
#       默认 **只读预览**：不改动任何工作树、不提交、不推送。
#   powershell -NoProfile -ExecutionPolicy Bypass -File tools\push_code_only_to_github.ps1 -Execute
#       真正执行：在发布工作树里建 publish/code-only → 清零索引 → 按白名单加入 → 提交 → force push。
#
# 三条必须知道的限制：
#   A. 本地 .git 历史仍保留（好东西，别丢）。远端历史被替换成单条快照提交。
#   B. GitHub 可能仍保留旧的不可达对象一段时间（服务端 GC 才真正清除）。要"彻底消失"，
#      唯一可靠办法是**在 GitHub 上删除该仓库并新建空仓库**，再跑本脚本（不依赖旧历史）。
#   C. 本机沙箱内 git 无法联网（`ls-remote` 报 sh.exe signal pipe 拒绝），**推送必须由操作者执行**。

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
if (-not (Test-Path $wt)) { throw "找不到发布工作树: $wt" }

$whitelist = @('tools', 'src', 'exp', 'experiments', 'outputs', 'docs',
               'README.md', 'requirements.txt', 'AGENTS.md', '.gitignore')
$heavyExt = '\.(pt|pth|ckpt|bin|safetensors|onnx)$'

Write-Host "=== 1) 只读盘点（基于当前 HEAD，不改任何东西）===" -ForegroundColor Cyan
$base = git -C $wt rev-parse --abbrev-ref HEAD
if ($base -ne 'publish/main') { Write-Host "  ⚠ 当前分支是 $base（建议先切回 publish/main）" -ForegroundColor Yellow }
$commit = git -C $wt rev-parse --short HEAD
Write-Host "  工作树: $wt"
Write-Host "  基准:   $base @ $commit"

$tracked = git -C $wt ls-tree -r --name-only HEAD
Write-Host ("  当前跟踪: {0} 个文件" -f ($tracked | Measure-Object).Count)

# 将被纳入的：白名单前缀下、且非权重类
$keep = $tracked | Where-Object {
    $p = $_
    ($whitelist | Where-Object { $p -eq $_ -or $p -like "$_/*" }) -and ($p -notmatch $heavyExt)
}
# 将被移出的：其余全部（含全部稿件）+ 白名单下的权重类
$keepSet = @{}
$keep | ForEach-Object { $keepSet[$_] = $true }
$drop = $tracked | Where-Object { -not $keepSet.ContainsKey($_) }
$dropHeavy = $drop | Where-Object { $_ -match $heavyExt }
$dropPaper = $drop | Where-Object { $_ -notmatch $heavyExt }

Write-Host "`n=== 2) 计划 ===" -ForegroundColor Cyan
Write-Host ("  保留(代码+结果): {0} 个文件" -f ($keep | Measure-Object).Count) -ForegroundColor Green
Write-Host ("  移出(权重类)   : {0} 个文件（GitHub 单文件上限 100 MB）" -f ($dropHeavy | Measure-Object).Count) -ForegroundColor Yellow
Write-Host ("  移出(稿件/其它): {0} 个文件" -f ($dropPaper | Measure-Object).Count) -ForegroundColor Yellow

Write-Host "`n  保留内容的目录分布:"
$keep | ForEach-Object { ($_ -split '/')[0] } | Group-Object | Sort-Object Count -Descending |
    Select-Object -First 12 | ForEach-Object { Write-Host ("    {0,6}  {1}" -f $_.Count, $_.Name) }

Write-Host "`n  被移出的稿件类目录分布（应覆盖全部 paper*）:"
$dropPaper | ForEach-Object { ($_ -split '/')[0] } | Group-Object | Sort-Object Count -Descending |
    Select-Object -First 12 | ForEach-Object { Write-Host ("    {0,6}  {1}" -f $_.Count, $_.Name) -ForegroundColor DarkYellow }

Write-Host "`n=== 3) 安全检查（预演）===" -ForegroundColor Cyan
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
    Write-Host "  ❌ 保留清单里命中稿件类文件，脚本逻辑有误：" -ForegroundColor Red
    $banned | Select-Object -First 20 | ForEach-Object { Write-Host "     $_" -ForegroundColor Red }
    exit 1
}
Write-Host "  ✅ 保留清单内稿件类文件 0 个" -ForegroundColor Green

$bigKeep = @()
foreach ($f in $keep) {
    $full = Join-Path $wt $f
    if (Test-Path $full) {
        $mb = (Get-Item $full).Length / 1MB
        if ($mb -ge 100) { $bigKeep += [pscustomobject]@{ MB = [math]::Round($mb, 1); File = $f } }
    }
}
if ($bigKeep) {
    Write-Host "  ❌ 保留清单里有 ≥100 MB 的文件（GitHub 会拒）：" -ForegroundColor Red
    $bigKeep | ForEach-Object { Write-Host ("     {0,8} MB  {1}" -f $_.MB, $_.File) -ForegroundColor Red }
    exit 1
}
Write-Host "  ✅ 保留清单内无 ≥100 MB 文件" -ForegroundColor Green

if (-not $Execute) {
    Write-Host "`n=== 只读预览结束：未改动工作树、未提交、未推送 ===" -ForegroundColor Yellow
    Write-Host "  确认无误后执行（会 force push 覆盖远端 main 历史）："
    Write-Host "    powershell -NoProfile -ExecutionPolicy Bypass -File tools\push_code_only_to_github.ps1 -Execute" -ForegroundColor White
    exit 0
}

Write-Host "`n=== 4) 执行：建分支 + 清零索引 + 按白名单加入 ===" -ForegroundColor Cyan
git -C $wt checkout -B $Branch | Out-Null
git -C $wt reset --hard | Out-Null
git -C $wt rm -r --cached . --quiet
foreach ($p in $whitelist) {
    if (Test-Path (Join-Path $wt $p)) { git -C $wt add -- $p; Write-Host "  + $p" }
}
$heavyStaged = git -C $wt diff --cached --name-only | Where-Object { $_ -match $heavyExt }
if ($heavyStaged) {
    $heavyStaged | ForEach-Object { git -C $wt rm --cached --quiet -- $_ }
    Write-Host ("  已移出权重类文件 {0} 个" -f $heavyStaged.Count)
}

Write-Host "`n=== 5) 执行前再校验一次（基于已暂存内容）===" -ForegroundColor Cyan
$staged = git -C $wt diff --cached --name-only
$bad = $staged | Where-Object {
    $_ -match '(cover_letter|declaration|title_page|highlights|abstract)[^/]*\.(tex|pdf|docx)$' -or
    $_ -match '(^|/)main[^/]*\.(tex|pdf)$' -or $_ -match 'main_zh\.' -or $_ -match 'revision_additions'
}
if ($bad) { Write-Host "  ❌ 暂存区仍有稿件类文件，中止：" -ForegroundColor Red; $bad | ForEach-Object { Write-Host "     $_" -ForegroundColor Red }; exit 1 }
Write-Host ("  ✅ 暂存 {0} 个文件，稿件类 0 个" -f ($staged | Measure-Object).Count) -ForegroundColor Green

Write-Host "`n=== 6) 提交并 force push ===" -ForegroundColor Cyan
git -C $wt -c user.name="Hongrui Wan" -c user.email="2024282101@hrbeu.edu.cn" `
    commit --quiet -m "Chore: publish code and results only (manuscripts, cover letters and checkpoints removed from tracking)"
git -C $wt log -1 --pretty=format:"  %h %ad %s" --date=format:"%Y-%m-%d %H:%M"; Write-Host ""
git -C $wt push --force $Remote "${Branch}:main"

Write-Host "`n=== 7) 复核 ===" -ForegroundColor Cyan
git -C $wt ls-remote --heads $Remote
Write-Host "`n完成。远端 $Remote 的 main 现在只有代码与结果。" -ForegroundColor Green
Write-Host "提醒：远端旧对象何时被 GC 清除由 GitHub 决定；要彻底清除请删库重建后重跑本脚本。" -ForegroundColor Yellow
