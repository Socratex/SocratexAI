param(
    [string[]]$Command,
    [switch]$Skip
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$Root = Resolve-Path -LiteralPath (Join-Path $PSScriptRoot "..\..")

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
        powershell -NoProfile -ExecutionPolicy Bypass -Command $commandLine
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
            powershell -NoProfile -ExecutionPolicy Bypass -Command $candidate.Command
            exit $LASTEXITCODE
        }
    }

    Write-Host "WARNING: no quality gate detected. Pass -Command '<command>' to run one explicitly."
    exit 0
} finally {
    Pop-Location
}
