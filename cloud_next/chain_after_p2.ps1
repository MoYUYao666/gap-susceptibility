# Chain: fetch the remaining A23 encoders, wait for the local torch-2.6 seed runs, aggregate them, then run the
# full 21-unit multi-encoder grid. Everything is logged; each step is skipped if its output already exists.
$ErrorActionPreference = 'Continue'
$root = 'D:\Realdesktop\Wan\Important\New'
Set-Location $root
$env:PYTHONIOENCODING = 'utf-8'
$env:MODELSCOPE_CACHE = Join-Path $root 'models\ms_cache'
$log = Join-Path $root 'outputs\_logs\chain_after_p2.log'
function Say($m) { $line = "[{0}] {1}" -f (Get-Date).ToString('HH:mm:ss'), $m; $line | Tee-Object -FilePath $log -Append }

$py = 'D:\Anaconda\envs\pytorch\python.exe'
$torch26 = 'D:\Anaconda\envs\torch26\python.exe'

# --- 1. fetch the four missing encoder checkpoints through ModelScope (hf-mirror is 403 from this laptop)
$repos = @{
  'siglip-base-patch16-224'  = 'google/siglip-base-patch16-224'
  'clip-vit-large-patch14'   = 'openai/clip-vit-large-patch14'
  'dinov2-base'              = 'facebook/dinov2-base'
  'remoteclip'               = 'AI-ModelScope/RemoteCLIP'
}
foreach ($dir in $repos.Keys) {
  $target = Join-Path $root "models\$dir"
  if (Test-Path $target) { Say "encoder $dir already linked"; continue }
  Say "fetching $($repos[$dir]) -> models/$dir"
  $snap = & $py -c "from modelscope import snapshot_download; print(snapshot_download('$($repos[$dir])'))" 2>&1 | Select-Object -Last 1
  if ($LASTEXITCODE -ne 0 -or -not (Test-Path $snap)) { Say "  FAILED: $snap"; continue }
  & cmd /c mklink /J "$target" "$snap" | Out-Null
  Say "  linked models/$dir -> $snap"
}

# --- 2. wait for the torch-2.6 seed runs to finish
while ($true) {
  $running = Get-CimInstance Win32_Process -Filter "name='python.exe'" |
    Where-Object { $_.CommandLine -match '_p1613_p3_cloud_runner' }
  if (-not $running) { break }
  Say "waiting for the torch-2.6 seed runner ($($running.Count) process)"
  Start-Sleep -Seconds 300
}
Say 'torch-2.6 seed runs finished'

# --- 3. aggregate the environment-stack seeds
Say 'aggregating env-seeds'
& $torch26 tools\_p1613_p3_cloud_runner.py --job env-seeds --aggregate --strict 2>&1 |
  Tee-Object -FilePath $log -Append | Select-Object -Last 6

# --- 4. full multi-encoder grid (7 encoders x 3 corpora)
Say 'running the A23 multi-encoder grid (encode)'
& $py tools\_p1614_a23_multi_encoder_transfer.py --encode --include-adapted 2>&1 |
  Tee-Object -FilePath $log -Append | Select-Object -Last 6
Say 'running the A23 multi-encoder grid (analyze)'
& $py tools\_p1614_a23_multi_encoder_transfer.py --analyze --include-adapted 2>&1 |
  Tee-Object -FilePath $log -Append | Select-Object -Last 8
Say 'CHAIN DONE'