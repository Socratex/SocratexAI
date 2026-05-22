param(
    [string[]]$Command,
    [string]$Root = "",
    [switch]$Skip
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$packageRoot = Resolve-Path -LiteralPath (Join-Path $PSScriptRoot "..\..")
$Root = if ([string]::IsNullOrWhiteSpace($Root)) {
    $packageRoot
} else {
    Resolve-Path -LiteralPath $Root
}
$contractRunner = Join-Path $PSScriptRoot "run_quality_gate_contract.ps1"
$qualityGateContract = Join-Path $Root "QUALITY-GATE.json"

if ($Skip) {
    Write-Host "SKIP: quality gate skipped by request."
    exit 0
}

Push-Location -LiteralPath $Root
try {
    Write-Host "==> quality gate"

    if ($Command -and $Command.Count -gt 0) {
        $commandLine = [string]::Join(" ", $Command)
        Write-Host "Running configured command: $commandLine"
        pwsh -NoLogo -NoProfile -Command $commandLine
        exit $LASTEXITCODE
    }

    if ((Test-Path -LiteralPath $qualityGateContract) -and (Test-Path -LiteralPath $contractRunner)) {
        pwsh -NoLogo -NoProfile -File $contractRunner -Path $qualityGateContract -Root $Root
        exit $LASTEXITCODE
    }

    $candidates = @(
        @{ File = "package.json"; Command = "npm test" },
        @{ File = "pyproject.toml"; Command = "python -m pytest" },
        @{ File = "Cargo.toml"; Command = "cargo test" },
        @{ File = "go.mod"; Command = "go test ./..." },
        @{ File = "pom.xml"; Command = "mvn test" },
        @{ File = "build.gradle"; Command = "gradle test" },
        @{ File = "build.gradle.kts"; Command = "gradle test" }
    )

    foreach ($candidate in $candidates) {
        if (Test-Path -LiteralPath $candidate.File) {
            Write-Host "Detected $($candidate.File); running $($candidate.Command)"
            pwsh -NoLogo -NoProfile -Command $candidate.Command
            exit $LASTEXITCODE
        }
    }

    Write-Host "WARNING: no quality gate detected. Pass -Command '<command>' to run one explicitly."
    exit 0
} finally {
    Pop-Location
}
