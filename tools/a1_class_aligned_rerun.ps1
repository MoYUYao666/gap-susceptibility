# Rerun the lambda_reg class-alignment dose-response after fixing two bugs:
#   1) the centroid table is now indexed BY CLASS ID (the old code stacked rows in
#      cls_ids order while training indexed c_ema[y] by class id, so every class
#      after the first missing one got the wrong centroid);
#   2) the text set uses only the real 1000 classes (the current shard's ClassLabel
#      carries a trailing placeholder class 'none' -> 1001 texts).
# frozen_refs.pt was also rebuilt from the current shards because the 2026-08-16
# reference does not correspond to the images now on disk (even a zero-LoRA model
# returned tau = -0.087, i.e. pure noise).
# GPU is strictly serial.  NOTE: ASCII-only on purpose - Windows PowerShell 5.1
# decodes BOM-less UTF-8 .ps1 files as ANSI and mangles non-ASCII strings.
$ErrorActionPreference = 'Continue'
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8
$OutputEncoding = [System.Text.Encoding]::UTF8

Set-Location -Path (Join-Path $PSScriptRoot '..')
$py = 'D:\Anaconda\envs\pytorch\python.exe'
$root = (Get-Location).Path
$log = Join-Path $root 'a1_class_aligned_rerun.log'
$tmp = Join-Path $root '_run_tmp.log'

function Say($m) {
    $line = "`n===== [" + (Get-Date -Format 'yyyy-MM-dd HH:mm:ss') + "] $m ====="
    Write-Output $line
    Add-Content -Path $log -Value $line -Encoding UTF8
}

function Invoke-Py($a, $label) {
    & $py @a *> $tmp
    $code = $LASTEXITCODE
    Get-Content $tmp -Encoding UTF8 | Add-Content -Path $log -Encoding UTF8
    $line = "  exit=$code  $label"
    Write-Output $line
    Add-Content -Path $log -Value $line -Encoding UTF8
}

function Train($lam, $seed, $extra) {
    Say "train lambda=$lam seed=$seed $extra"
    $a = @('tools/train_class_aligned.py', '--lambda-reg', $lam, '--seed', $seed, '--epochs', '10')
    if ($extra -ne '') { $a += $extra }
    Invoke-Py $a "train lambda=$lam seed=$seed $extra"
}

function EvalOnly($lam, $seed, $ep) {
    Say "eval-only lambda=$lam seed=$seed ep=$ep"
    $a = @('tools/train_class_aligned.py', '--eval-only', '--epoch', $ep,
           '--lambda-reg', $lam, '--seed', $seed)
    Invoke-Py $a "eval lambda=$lam seed=$seed ep=$ep"
}

Say 'STAGE A: dose-response, seed 42, six lambdas'
foreach ($lam in @('0', '0.05', '0.1', '0.25', '0.5', '1.0')) {
    Train $lam '42' ''
}

Say 'STAGE A2: seeds 123 and 456, four lambdas each'
foreach ($seed in @('123', '456')) {
    foreach ($lam in @('0', '0.1', '0.5', '1.0')) {
        Train $lam $seed ''
    }
}

Say 'STAGE B: early-stopping table, lambda=0 seed=42, epochs 1/2/3/5/10'
foreach ($ep in @('1', '2', '3', '5', '10')) {
    EvalOnly '0' '42' $ep
}

Say 'STAGE C: no-EMA controls, seed 42, lambda=0.5 and 1.0'
foreach ($lam in @('0.5', '1.0')) {
    Train $lam '42' '--no-ema'
}

Say 'SUMMARY of endpoints'
Get-ChildItem 'outputs/a1_class_aligned' -Directory -Filter 'lr*' | ForEach-Object {
    $lamDir = $_
    Get-ChildItem $lamDir.FullName -Directory -Filter 'seed*' | ForEach-Object {
        $f = Join-Path $_.FullName 'results.json'
        if (Test-Path $f) {
            $d = Get-Content $f -Raw -Encoding UTF8 | ConvertFrom-Json
            $t = "  {0,-14} {1,-8} top1_50k={2} val_loss={3} align_loss={4}" -f `
                $lamDir.Name, $_.Name, $d.top1_50k, [math]::Round($d.val_loss, 4), `
                [math]::Round($d.history[-1].align_loss, 4)
            Write-Output $t
            Add-Content -Path $log -Value $t -Encoding UTF8
        }
    }
}
Say 'DONE'
