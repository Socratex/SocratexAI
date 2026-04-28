param(
    [ValidateSet("snapshot", "merge", "replace")]
    [string]$Mode = "merge",

    [string]$TargetPath = ".",

    [string[]]$DirectiveFiles = @("AGENTS.md")
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$TargetRoot = Resolve-Path -LiteralPath $TargetPath
$SocratexFile = Join-Path $TargetRoot "SOCRATEX.md"
$mergeDirective = 'Primary directive: read and respect `SOCRATEX.md` before following this file. SocratexPipeline is installed under `SocratexAI/`.'
$replaceDirective = @"
# Agent Directive

Read ``SOCRATEX.md`` first and treat it as the controlling AI pipeline directive for this project.

SocratexPipeline is installed under ``SocratexAI/``.
"@

function Save-OldFile {
    param([string]$Path)

    if (-not (Test-Path -LiteralPath $Path)) {
        return
    }

    $destination = "$Path.old"
    if (Test-Path -LiteralPath $destination) {
        $timestamp = Get-Date -Format "yyyyMMdd-HHmmss"
        $destination = "$Path.$timestamp.old"
    }
    Copy-Item -LiteralPath $Path -Destination $destination -Force
}

if (-not (Test-Path -LiteralPath $SocratexFile)) {
    throw "Missing root SOCRATEX.md. Install or import SocratexPipeline before updating directives."
}

foreach ($directive in $DirectiveFiles) {
    $target = Join-Path $TargetRoot $directive
    New-Item -ItemType Directory -Force -Path (Split-Path -Parent $target) | Out-Null

    if ($Mode -eq "snapshot") {
        Save-OldFile -Path $target
        continue
    }

    if ($Mode -eq "replace") {
        Save-OldFile -Path $target
        Set-Content -LiteralPath $target -Value $replaceDirective -Encoding UTF8 -NoNewline
        continue
    }

    if (Test-Path -LiteralPath $target) {
        $current = Get-Content -Raw -LiteralPath $target -Encoding UTF8
        if ($current.Contains("SOCRATEX.md")) {
            Write-Host "Skip merge; SOCRATEX.md directive already appears in $directive"
            continue
        }
        $merged = $current.TrimEnd() + [Environment]::NewLine + [Environment]::NewLine + $mergeDirective
        Set-Content -LiteralPath $target -Value $merged -Encoding UTF8 -NoNewline
    } else {
        Set-Content -LiteralPath $target -Value $replaceDirective -Encoding UTF8 -NoNewline
    }
}

Write-Host "Directive update complete. Mode: $Mode"
