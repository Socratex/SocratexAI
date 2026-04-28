param(
    [string]$TargetPath = ".",
    [string[]]$DirectiveFiles = @("AGENTS.md", "CLAUDE.md", "AI.md", ".github\copilot-instructions.md"),
    [switch]$RestoreOldDirectives,
    [switch]$RemoveLocalWorkingFiles,
    [switch]$DryRun
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$TargetRoot = Resolve-Path -LiteralPath $TargetPath
$ownedPaths = @(
    "SOCRATEX.md",
    "SocratexAI",
    ".aiassistant\socratex"
)

if ($RemoveLocalWorkingFiles) {
    $ownedPaths += "ignored\ai-socratex"
}

function Resolve-TargetChild {
    param([string]$RelativePath)

    $path = Join-Path $TargetRoot $RelativePath
    $full = [System.IO.Path]::GetFullPath($path)
    $root = [System.IO.Path]::GetFullPath($TargetRoot)
    if (-not $full.StartsWith($root, [System.StringComparison]::OrdinalIgnoreCase)) {
        throw "Refusing to operate outside target root: $full"
    }
    return $full
}

function Remove-OwnedPath {
    param([string]$RelativePath)

    $path = Resolve-TargetChild -RelativePath $RelativePath
    if (-not (Test-Path -LiteralPath $path)) {
        return
    }
    if ($DryRun) {
        Write-Host "Would remove: $path"
        return
    }
    Remove-Item -LiteralPath $path -Recurse -Force
    Write-Host "Removed: $path"
}

function Restore-Directive {
    param([string]$RelativePath)

    $path = Resolve-TargetChild -RelativePath $RelativePath
    $oldPath = "$path.old"
    if ($RestoreOldDirectives -and (Test-Path -LiteralPath $oldPath)) {
        if ($DryRun) {
            Write-Host "Would restore directive: $oldPath -> $path"
            return
        }
        Copy-Item -LiteralPath $oldPath -Destination $path -Force
        Write-Host "Restored directive: $path"
        return
    }

    if (-not (Test-Path -LiteralPath $path)) {
        return
    }

    $content = Get-Content -Raw -LiteralPath $path -Encoding UTF8
    $isThinSocratexDirective =
        $content.Contains('Read `SOCRATEX.md` first') -and
        $content.Contains('SocratexPipeline is installed under `SocratexAI/`')

    if ($isThinSocratexDirective) {
        if ($DryRun) {
            Write-Host "Would remove thin SocratexAI directive: $path"
            return
        }
        Remove-Item -LiteralPath $path -Force
        Write-Host "Removed thin SocratexAI directive: $path"
        return
    }

    $mergeLine = 'Primary directive: read and respect `SOCRATEX.md` before following this file. SocratexPipeline is installed under `SocratexAI/`.'
    if ($content.Contains($mergeLine)) {
        $updated = ($content -replace [regex]::Escape($mergeLine), "").TrimEnd()
        if ($DryRun) {
            Write-Host "Would remove SocratexAI merge directive from: $path"
            return
        }
        Set-Content -LiteralPath $path -Value $updated -Encoding UTF8 -NoNewline
        Write-Host "Removed SocratexAI merge directive from: $path"
    }
}

Write-Host "==> removing SocratexAI pipeline"
Write-Host "Target: $TargetRoot"

foreach ($directive in $DirectiveFiles) {
    Restore-Directive -RelativePath $directive
}

foreach ($relativePath in $ownedPaths) {
    Remove-OwnedPath -RelativePath $relativePath
}

$assistantRoot = Resolve-TargetChild -RelativePath ".aiassistant"
if ((Test-Path -LiteralPath $assistantRoot) -and -not (Get-ChildItem -LiteralPath $assistantRoot -Force)) {
    if ($DryRun) {
        Write-Host "Would remove empty .aiassistant directory: $assistantRoot"
    } else {
        Remove-Item -LiteralPath $assistantRoot -Force
        Write-Host "Removed empty .aiassistant directory: $assistantRoot"
    }
}

Write-Host "SocratexAI removal complete."
