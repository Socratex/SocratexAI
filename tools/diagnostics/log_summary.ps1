param(
    [Parameter(Mandatory = $true)]
    [string]$Description,

    [string]$LogsPath = "logs",
    [int]$TailLines = 160,
    [string]$OutputPath = "DIAGNOSTICS-SUMMARY.json"
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$Root = Resolve-Path -LiteralPath (Join-Path $PSScriptRoot "..\..")
. (Join-Path $Root "tools\text\utf8_file_helpers.ps1")
$ResolvedLogsPath = Join-Path $Root $LogsPath
$SummaryPath = Join-Path $Root $OutputPath

function Get-TailText {
    param(
        [string]$Path,
        [int]$LineCount
    )

    $lines = @(Get-Content -LiteralPath $Path -Tail $LineCount -ErrorAction Stop)
    return [string]::Join([Environment]::NewLine, $lines)
}

if (-not (Test-Path -LiteralPath $ResolvedLogsPath)) {
    New-Item -ItemType Directory -Force -Path $ResolvedLogsPath | Out-Null
    New-Item -ItemType File -Force -Path (Join-Path $ResolvedLogsPath ".gitkeep") | Out-Null
}

$files = @(
    Get-ChildItem -LiteralPath $ResolvedLogsPath -File -Recurse -ErrorAction SilentlyContinue |
        Where-Object { $_.Name -ne ".gitkeep" } |
        Sort-Object LastWriteTime -Descending
)

$evidence = New-Object System.Collections.Generic.List[object]

if ($files.Count -eq 0) {
    $evidence.Add([ordered]@{
        path = $null
        modified = $null
        preview = "No diagnostic files found under $LogsPath."
    }) | Out-Null
} else {
    foreach ($file in ($files | Select-Object -First 5)) {
        $relativePath = $file.FullName.Substring($Root.Path.Length)
        $relativePath = $relativePath.TrimStart([System.IO.Path]::DirectorySeparatorChar, [System.IO.Path]::AltDirectorySeparatorChar)

        $preview = "Binary or unsupported text preview; inspect manually if relevant."
        if ($file.Extension -match '^\.(log|txt|json|xml|csv|md)$') {
            $preview = Get-TailText -Path $file.FullName -LineCount $TailLines
        }

        $evidence.Add([ordered]@{
            path = $relativePath
            modified = $file.LastWriteTime.ToString("s")
            preview = $preview
        }) | Out-Null
    }
}

$summary = [ordered]@{
    summary = "Diagnostics summary"
    description = $Description
    logs_path = $LogsPath
    evidence = @($evidence)
    observed_facts = @()
    current_hypothesis = "TBD"
    smallest_source_owned_fix_or_diagnostic_step = "TBD"
    verification = "TBD"
}

Write-Utf8File -Path $SummaryPath -Value ($summary | ConvertTo-Json -Depth 6) -NoNewline
Write-Host "Wrote diagnostics summary: $OutputPath"
