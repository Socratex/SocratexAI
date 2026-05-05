param(
    [string]$TargetPath = "."
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$Root = Resolve-Path -LiteralPath $TargetPath
$signals = New-Object System.Collections.Generic.List[object]

function Add-Signal {
    param(
        [string]$Ecosystem,
        [string]$File,
        [string]$Meaning
    )

    if (Test-Path -LiteralPath (Join-Path $Root $File)) {
        $signals.Add([ordered]@{
            ecosystem = $Ecosystem
            file = $File
            meaning = $Meaning
        }) | Out-Null
    }
}

Add-Signal -Ecosystem "php" -File "composer.json" -Meaning "Composer project"
Add-Signal -Ecosystem "php" -File "composer.lock" -Meaning "Composer lockfile"
Add-Signal -Ecosystem "php" -File "artisan" -Meaning "Laravel project"
Add-Signal -Ecosystem "php" -File "symfony.lock" -Meaning "Symfony project"
Add-Signal -Ecosystem "node" -File "package.json" -Meaning "Node package"
Add-Signal -Ecosystem "node" -File "pnpm-lock.json" -Meaning "pnpm project"
Add-Signal -Ecosystem "node" -File "yarn.lock" -Meaning "Yarn project"
Add-Signal -Ecosystem "python" -File "pyproject.toml" -Meaning "Python project"
Add-Signal -Ecosystem "python" -File "requirements.txt" -Meaning "Python requirements"
Add-Signal -Ecosystem "python" -File "uv.lock" -Meaning "uv project"
Add-Signal -Ecosystem "go" -File "go.mod" -Meaning "Go module"
Add-Signal -Ecosystem "rust" -File "Cargo.toml" -Meaning "Rust crate"
Add-Signal -Ecosystem "java" -File "pom.xml" -Meaning "Maven project"
Add-Signal -Ecosystem "java" -File "build.gradle" -Meaning "Gradle project"
Add-Signal -Ecosystem "java" -File "build.gradle.kts" -Meaning "Gradle Kotlin project"

Get-ChildItem -LiteralPath $Root -Filter "*.sln" -File -ErrorAction SilentlyContinue | ForEach-Object {
    $signals.Add([ordered]@{
        ecosystem = ".net"
        file = $_.Name
        meaning = ".NET solution"
    }) | Out-Null
}

Get-ChildItem -LiteralPath $Root -Filter "*.csproj" -File -Recurse -ErrorAction SilentlyContinue | Select-Object -First 3 | ForEach-Object {
    $signals.Add([ordered]@{
        ecosystem = ".net"
        file = $_.FullName.Substring($Root.Path.Length).TrimStart([System.IO.Path]::DirectorySeparatorChar, [System.IO.Path]::AltDirectorySeparatorChar)
        meaning = ".NET project"
    }) | Out-Null
}

$composerDetected = (@($signals | Where-Object { $_.file -eq "composer.json" }).Count -gt 0)
$signalArray = @($signals.ToArray())

$result = [ordered]@{
    target_path = $Root.Path
    signals = $signalArray
    composer_detected = $composerDetected
}

$result | ConvertTo-Json -Depth 5
