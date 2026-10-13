# -*- coding: utf-8 -*-
<#
.SYNOPSIS
    Crossref 检索：给定题名打印候选条目的 标题/年份/DOI/刊名/首作者（用于核验文献是否真实存在）。

.DESCRIPTION
    为什么存在：本机 web_fetch 不可用，arXiv API 限流，DBLP 反爬。Crossref 是唯一稳定的多源通道。
    只做检索与打印，不写仓库。

    用法：
        $f = [scriptblock]::Create((Get-Content -Raw tools/_crossref_search.ps1))
        & $f -Titles "LLaMA-Adapter","DoRA: Weight-Decomposed Low-Rank Adaptation" -Rows 5
#>
param(
    [Parameter(Mandatory = $true)][string[]]$Titles,
    [int]$Rows = 5
)

$ProgressPreference = 'SilentlyContinue'
$UA = "citation-verify/1.0 (mailto:hw4c24@soton.ac.uk)"

foreach ($t in $Titles) {
    $q = [uri]::EscapeDataString($t)
    $url = "https://api.crossref.org/works?query.bibliographic=$q&rows=$Rows"
    Write-Output "=== QUERY: $t"
    try {
        $r = Invoke-RestMethod -Uri $url -UserAgent $UA -TimeoutSec 45
    }
    catch {
        Write-Output "   ERROR: $($_.Exception.Message)"
        continue
    }
    foreach ($it in $r.message.items) {
        $title = ""
        if ($it.title) { $title = $it.title[0] }
        $year = ""
        foreach ($k in @('published-print', 'published-online', 'issued', 'created')) {
            if ($it.$k -and $it.$k.'date-parts' -and $it.$k.'date-parts'[0][0]) {
                $year = $it.$k.'date-parts'[0][0]; break
            }
        }
        $cont = ""
        if ($it.'container-title') { $cont = $it.'container-title'[0] }
        $auth = ""
        if ($it.author -and $it.author.Count -gt 0) {
            $a0 = $it.author[0]
            if ($a0.family) { $auth = $a0.family } elseif ($a0.name) { $auth = $a0.name }
        }
        Write-Output ("   {0} | {1} | {2} | {3} | {4}" -f $year, $it.DOI, $cont, $auth, $title)
    }
    Start-Sleep -Milliseconds 600
}
