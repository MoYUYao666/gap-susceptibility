# Queue for the LLaVA adaptation-site experiment: wait until at least 4.5 GB of the GPU is free,
# then run the isolation check, then a pilot, then the full run if the pilot passes.
$ErrorActionPreference = 'Continue'
Set-Location 'D:\Realdesktop\Wan\Important\New'
$log = 'outputs\analysis\_p820_queue.log'
function Write-Log($m) { "$(Get-Date -Format 'HH:mm:ss') $m" | Out-File -FilePath $log -Encoding utf8 -Append }
Write-Log "queue started"
$py = 'D:\Anaconda\envs\pytorch\python.exe'
$env:PYTHONIOENCODING = 'utf-8'; $env:PYTHONUTF8 = '1'
$env:HF_HUB_OFFLINE = '1'; $env:TRANSFORMERS_OFFLINE = '1'
$env:PYTORCH_ALLOC_CONF = 'expandable_segments:True'

$waited = 0
while ($true) {
    $free = (& nvidia-smi --query-gpu=memory.free --format=csv,noheader,nounits 2>$null | Select-Object -First 1)
    $freeMB = [int]($free -replace '\D','')
    Write-Log "free VRAM ${freeMB} MB"
    if ($freeMB -ge 4600) { break }
    Start-Sleep -Seconds 120
    $waited += 2
    if ($waited -gt 900) { Write-Log "gave up waiting"; exit 1 }
}
Write-Log "enough VRAM free (${freeMB} MB); starting isolation check"
& $py tools\_p820_llava_sites.py --verify-only *>> outputs\analysis\_p820_verify.log
Write-Log "isolation check exit $LASTEXITCODE"

Write-Log "starting pilot"
& $py tools\_p820_llava_sites.py --pilot *>> outputs\analysis\_p820_pilot.log
$pilotExit = $LASTEXITCODE
Write-Log "pilot exit $pilotExit"

if ($pilotExit -eq 0) {
    Write-Log "starting full run"
    & $py tools\_p820_llava_sites.py --samples 400 --eval-pairs 500 --epochs 3 --batch 2 --seeds 3 --lr 1e-4 --rank 8 --apply *>> outputs\analysis\_p820.log
    Write-Log "full run exit $LASTEXITCODE"
} else {
    Write-Log "pilot failed; not running the full experiment"
}
