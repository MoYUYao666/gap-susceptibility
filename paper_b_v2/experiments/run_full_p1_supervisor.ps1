$ErrorActionPreference = 'Continue'
$root = 'D:\Realdesktop\Wan\Important\New'
$py = 'D:\Anaconda\envs\pytorch\python.exe'
$log = Join-Path $root 'outputs\paper_b\p1_supervisor.log'
function Log($msg) { $line = "$(Get-Date -Format o) $msg"; $line | Tee-Object -FilePath $log -Append }
function Launch($script, $args, $name) {
    $out = Join-Path $root "outputs\paper_b\$name.log"
    $err = Join-Path $root "outputs\paper_b\$name.err.log"
    $p = Start-Process -FilePath $py -ArgumentList (@($script) + $args) -WorkingDirectory $root `
        -RedirectStandardOutput $out -RedirectStandardError $err -WindowStyle Hidden -PassThru
    Log "START $name pid=$($p.Id)"
    return $p
}
Log 'supervisor start'
& $py (Join-Path $root 'paper_b_v2\experiments\clean_partial.py') 2>&1 | Tee-Object -FilePath $log -Append

# Phase 1: full CLIP P1 blocks, five workers.
$workers = @()
$workers += Launch 'paper_b/run_matrix.py' @('--backbones','clip-b32','--datasets','dtd,inat,nksid','--ranks','6','--seeds','45,46,47,48','--towers','both,text,vision','--outdir','outputs/paper_b/runs_b32_r6_full') 'p1_r6'
$workers += Launch 'paper_b/run_matrix.py' @('--backbones','clip-b32','--datasets','dtd,inat,nksid','--ranks','12','--seeds','45,46,47,48','--towers','both,text,vision','--outdir','outputs/paper_b/runs_b32_r12_full') 'p1_r12'
$workers += Launch 'paper_b/run_matrix.py' @('--backbones','clip-b32','--datasets','dtd,inat,nksid','--ranks','24','--seeds','45,46,47,48','--towers','both,text,vision','--outdir','outputs/paper_b/runs_b32_r24_full') 'p1_r24'
$workers += Launch 'paper_b/run_matrix.py' @('--backbones','clip-b32','--datasets','dtd,inat,nksid','--ranks','48','--seeds','45,46,47,48','--towers','both,text,vision','--outdir','outputs/paper_b/runs_b32_r48_full') 'p1_r48'
$workers += Launch 'paper_b/run_matrix.py' @('--backbones','clip-b32','--datasets','dtd,inat,nksid','--ranks','16','--seeds','49,50,51,52','--towers','both,text,vision','--outdir','outputs/paper_b/runs_b32_split2_full') 'p1_split2'
Log 'phase1 launched; waiting'
$workers | Wait-Process
Log 'phase1 done'
& $py (Join-Path $root 'paper_b_v2\analysis\p1_full.py') 2>&1 | Tee-Object -FilePath $log -Append

# Phase 2: full SigLIP rank-8, two dataset groups.
$sig = @()
$sig += Launch 'paper_b_v2/experiments/run_matrix_siglip.py' @('--backbones','siglip-b16','--datasets','dtd','--ranks','8','--seeds','45,46,47,48','--towers','both,text,vision','--outdir','outputs/paper_b/runs_siglip_r8_dtd') 'siglip_dtd'
$sig += Launch 'paper_b_v2/experiments/run_matrix_siglip.py' @('--backbones','siglip-b16','--datasets','inat,nksid','--ranks','8','--seeds','45,46,47,48','--towers','both,text,vision','--outdir','outputs/paper_b/runs_siglip_r8_other') 'siglip_other'
Log 'phase2 launched; waiting'
$sig | Wait-Process
Log 'phase2 done'
& $py (Join-Path $root 'paper_b_v2\analysis\p1_siglip_full.py') 2>&1 | Tee-Object -FilePath $log -Append
Log 'supervisor complete'
