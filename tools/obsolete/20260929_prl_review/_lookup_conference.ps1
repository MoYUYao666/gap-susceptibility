# -*- coding: utf-8 -*-
<#
.SYNOPSIS
    在会议论文集官方索引页中按题名定位论文，给出**正式发表版**的 URL 与题名。

.DESCRIPTION
    为什么需要：`web_fetch` 不可用、arXiv API 限流、DBLP 反爬；而 NeurIPS proceedings 的
    年度索引页（HTML）稳定可抓，且是"该文是否被正式接收"的权威证据——
    用于避免把 arXiv 预印本写成正式发表版（核验器会对此告警）。

    用法：
        $f = [scriptblock]::Create((Get-Content -Raw tools/_lookup_conference.ps1))
        & $f -Venue neurips -Year 2022 -Pattern 'AdaptFormer|Scaling . Shifting'
        & $f -Venue iclr    -Year 2024 -Pattern 'LLaMA-Adapter'
        & $f -Venue icml    -Year 2024 -Pattern 'DoRA'

    支持的 venue：neurips / iclr / icml。只读网络，不写仓库。
#>
param(
    [Parameter(Mandatory = $true)][ValidateSet('neurips', 'iclr', 'icml')][string]$Venue,
    [Parameter(Mandatory = $true)][int]$Year,
    [Parameter(Mandatory = $true)][string]$Pattern
)

$ProgressPreference = 'SilentlyContinue'
$UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) citation-verify/1.0"

$url = switch ($Venue) {
    'neurips' { "https://proceedings.neurips.cc/paper_files/paper/$Year" }
    'iclr' { "https://iclr.cc/virtual/$Year/papers.html" }
    'icml' { "https://icml.cc/virtual/$Year/papers.html" }
}

Write-Output "=== $Venue $Year  (index: $url)"
try {
    $r = Invoke-WebRequest -Uri $url -UseBasicParsing -UserAgent $UA -TimeoutSec 90
}
catch {
    Write-Output "  ERROR: $($_.Exception.Message)"
    return
}

$hits = 0
foreach ($m in [regex]::Matches($r.Content, '(?is)<a[^>]*href="([^"]+)"[^>]*>(.*?)</a>')) {
    $href = $m.Groups[1].Value
    $text = ($m.Groups[2].Value -replace '<[^>]+>', '' -replace '\s+', ' ').Trim()
    if ($text.Length -lt 8) { continue }
    if ($text -notmatch $Pattern) { continue }
    Write-Output "  TITLE: $text"
    Write-Output "  HREF : $href"
    $hits++
}
if ($hits -eq 0) { Write-Output "  (no match for /$Pattern/)" }
Write-Output "  hits=$hits"
