# -*- coding: utf-8 -*-
<#
.SYNOPSIS
    抓取 arXiv abs 页面的权威元数据（标题/作者/日期/comments/journal-ref），并可保存整页正文。

.DESCRIPTION
    为什么存在：本机 `web_fetch` 工具不可用（provider 未注册），arXiv API 被限流（ti: 前缀必 406）。
    abs 页面（HTML）稳定可用且自带 citation_* 元标签，是核验文献元数据与取原文数据的唯一可靠通道。

    用法：
        pwsh -File tools/_fetch_arxiv_meta.ps1 -Ids 2106.09685,2310.03744
        pwsh -File tools/_fetch_arxiv_meta.ps1 -Ids 2310.03744 -SaveHtml docs/_cache

    输出：每条一行 TSV（ID / TITLE / AUTHORS / DATE / COMMENTS / JOURNAL-REF），便于复制进核验脚本。
    只读取网络、不修改仓库（除非显式给 -SaveHtml）。
#>
param(
    [Parameter(Mandatory = $true)][string[]]$Ids,
    [string]$SaveHtml = ""
)

$ProgressPreference = 'SilentlyContinue'
$UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) citation-verify/1.0"

function Get-Meta([string]$html, [string]$name) {
    $m = [regex]::Match($html, '<meta name="' + $name + '" content="(.*?)"')
    if ($m.Success) { return $m.Groups[1].Value } else { return "" }
}

function Clean([string]$s) {
    if (-not $s) { return "" }
    $s = $s -replace '<[^>]+>', ' '
    $s = $s -replace '&amp;', '&' -replace '&lt;', '<' -replace '&gt;', '>' -replace '&quot;', '"' -replace '&#39;', "'"
    return ($s -replace '\s+', ' ').Trim()
}

foreach ($raw in $Ids) {
    $id = $raw.Trim()
    $url = "https://arxiv.org/abs/$id"
    try {
        $r = Invoke-WebRequest -Uri $url -UseBasicParsing -UserAgent $UA -TimeoutSec 45
    }
    catch {
        Write-Output "$id`tERROR`t$($_.Exception.Message)"
        continue
    }
    $h = $r.Content
    if ($h -notmatch 'citation_title') {
        Write-Output "$id`tNO_METATAGS`tlen=$($h.Length)"
        continue
    }
    $title = Clean (Get-Meta $h 'citation_title')
    $authors = (([regex]::Matches($h, '<meta name="citation_author" content="(.*?)"') |
                 ForEach-Object { $_.Groups[1].Value }) -join ' ; ')
    $date = Clean (Get-Meta $h 'citation_date')
    $journal = Clean (Get-Meta $h 'citation_journal_title')
    $doi = Clean (Get-Meta $h 'citation_doi')
    # comments 块（含"Accepted at ..."这类关键信息）
    $cm = ""
    $cmMatch = [regex]::Match($h, '(?s)<td class="tablecell comments[^"]*">(.*?)</td>')
    if ($cmMatch.Success) { $cm = Clean $cmMatch.Groups[1].Value }
    $abs = ""
    $absMatch = [regex]::Match($h, '(?s)<blockquote class="abstract[^"]*">(.*?)</blockquote>')
    if ($absMatch.Success) { $abs = Clean $absMatch.Groups[1].Value }

    Write-Output "$id`tTITLE`t$title"
    Write-Output "$id`tAUTHORS`t$authors"
    Write-Output "$id`tDATE`t$date"
    Write-Output "$id`tCOMMENTS`t$cm"
    Write-Output "$id`tJOURNALREF`t$journal"
    Write-Output "$id`tDOI`t$doi"
    Write-Output "$id`tABSTRACT`t$abs"
    Write-Output "---"

    if ($SaveHtml) {
        if (-not (Test-Path $SaveHtml)) { New-Item -ItemType Directory -Path $SaveHtml -Force | Out-Null }
        $safe = $id -replace '[\\/:*?"<>|]', '_'
        Set-Content -Path (Join-Path $SaveHtml "$safe.abs.html") -Value $h -Encoding UTF8
    }
    Start-Sleep -Milliseconds 800
}
