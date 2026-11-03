# Run the full LLaVA adaptation-site experiment after the full-COCO scale-up finishes.
# Waiting is by PID: a memory threshold passes while a model is still loading, which is how an earlier
# chain started two GPU jobs at once.
$ErrorActionPreference = 'Continue'
Set-Location 'D:\Realdesktop\Wan\Important\New'
$log = 'outputs\analysis\_p845_chain.log'
function Write-Log($m) { "$(Get-Date -Format 'HH:mm:ss') $m" | Out-File -FilePath $log -Encoding utf8 -Append }
$py = 'D:\Anaconda\envs\pytorch\python.exe'
$env:PYTHONIOENCODING = 'utf-8'; $env:PYTHONUTF8 = '1'
$env:HF_HUB_OFFLINE = '1'; $env:TRANSFORMERS_OFFLINE = '1'
$env:HF_HUB_DISABLE_PROGRESS_BARS = '1'; $env:PYTORCH_ALLOC_CONF = 'expandable_segments:True'
Write-Log "chain started; waiting for the full-COCO run (PID 32100)"
while (Get-Process -Id 32100 -EA SilentlyContinue) { Start-Sleep -Seconds 60 }
Write-Log "full COCO ended; waiting 60 s for the GPU"
Start-Sleep -Seconds 60
Write-Log "starting the full LLaVA adaptation-site experiment"
& $py -u -X utf8 tools\_p820_llava_sites.py --samples 400 --eval-pairs 300 --epochs 3 --batch 2 `
    --max-len 2048 --seeds 3 --lr 1e-4 --rank 8 `
    --arms frozen,text_only,vision_only,both --apply *>> outputs\analysis\_p838_llava.out
Write-Log "LLaVA exit $LASTEXITCODE; chain done"
