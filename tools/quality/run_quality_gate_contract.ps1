param(
    [string]$Path = "QUALITY-GATE.json",
    [string[]]$CommandNames
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$repoRoot = Resolve-Path -LiteralPath (Join-Path $PSScriptRoot "..\..")
$gatePath = if ([System.IO.Path]::IsPathRooted($Path)) {
    $Path
} else {
    Join-Path $repoRoot $Path
}

if (-not (Test-Path -LiteralPath $gatePath)) {
    throw "Quality gate contract not found: $gatePath"
}

$gate = Get-Content -Raw -LiteralPath $gatePath | ConvertFrom-Json
if ($null -eq $gate.commands) {
    throw "Quality gate contract has no commands object: $gatePath"
}

$commands = @($gate.commands.PSObject.Properties)
if ($CommandNames -and $CommandNames.Count -gt 0) {
    $CommandNames = @($CommandNames | ForEach-Object {
        $_ -split "," | ForEach-Object { $_.Trim() } | Where-Object { -not [string]::IsNullOrWhiteSpace($_) }
    })
    $wanted = [System.Collections.Generic.HashSet[string]]::new([System.StringComparer]::OrdinalIgnoreCase)
    foreach ($name in $CommandNames) {
        [void]$wanted.Add($name)
    }

    $commands = @($commands | Where-Object { $wanted.Contains($_.Name) })
    if ($commands.Count -ne $wanted.Count) {
        $found = [System.Collections.Generic.HashSet[string]]::new([System.StringComparer]::OrdinalIgnoreCase)
        foreach ($command in $commands) {
            [void]$found.Add($command.Name)
        }
        $missing = @($CommandNames | Where-Object { -not $found.Contains($_) })
        throw "Quality gate command(s) not found: $($missing -join ', ')"
    }
}

Push-Location -LiteralPath $repoRoot
try {
    Write-Host "==> quality gate contract"
    foreach ($command in $commands) {
        $entry = $command.Value
        if ([string]::IsNullOrWhiteSpace($entry.command)) {
            throw "Quality gate command has empty command text: $($command.Name)"
        }

        Write-Host ""
        Write-Host "==> $($command.Name)"
        if (-not [string]::IsNullOrWhiteSpace($entry.description)) {
            Write-Host $entry.description
        }

        pwsh -NoLogo -NoProfile -Command $entry.command
        if ($LASTEXITCODE -ne 0) {
            throw "Quality gate command failed with exit code ${LASTEXITCODE}: $($command.Name)"
        }
    }

    Write-Host ""
    Write-Host "OK: quality gate contract passed"
} finally {
    Pop-Location
}
