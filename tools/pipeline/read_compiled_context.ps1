param(
    [Parameter(Mandatory = $true, Position = 0)]
    [string]$Document,
    [string]$CompiledRoot = "",
    [switch]$AllowStale,
    [switch]$Json
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$repoRoot = Resolve-Path -LiteralPath (Join-Path $PSScriptRoot "..\..")
if ([string]::IsNullOrWhiteSpace($CompiledRoot)) {
    $CompiledRoot = Join-Path $repoRoot "AI-compiled"
}
$compiledRootPath = Resolve-Path -LiteralPath $CompiledRoot
$checksumPath = Join-Path $compiledRootPath "checksum.json"

function ConvertTo-NormalizedHashText {
    param([string]$Text)

    if ($Text.Length -gt 0 -and $Text[0] -eq [char]0xFEFF) {
        $Text = $Text.Substring(1)
    }
    $Text = $Text -replace "`r`n", "`n"
    $Text = $Text -replace "`r", "`n"
    $lines = $Text -split "`n", -1
    for ($i = 0; $i -lt $lines.Count; $i++) {
        $lines[$i] = [regex]::Replace($lines[$i], "[ `t]+$", "")
    }
    $normalized = ($lines -join "`n").TrimEnd("`n")
    if ($normalized.Length -gt 0) {
        $normalized = $normalized + "`n"
    }
    return $normalized
}

function Get-NormalizedFileSha256 {
    param([string]$Path)

    $text = [System.IO.File]::ReadAllText($Path, [System.Text.UTF8Encoding]::new($false, $true))
    $normalized = ConvertTo-NormalizedHashText -Text $text
    $sha = [System.Security.Cryptography.SHA256]::Create()
    try {
        $bytes = [System.Text.Encoding]::UTF8.GetBytes($normalized)
        $hash = $sha.ComputeHash($bytes)
        return ([System.BitConverter]::ToString($hash)).Replace("-", "").ToLowerInvariant()
    } finally {
        $sha.Dispose()
    }
}

$requestedKey = $Document.Trim().ToLowerInvariant()
$aliases = @{
    "entrypoint" = "codex/ENTRYPOINT.md"
    "rules" = "codex/RULES.compiled.md"
    "workflow" = "codex/WORKFLOW.compiled.md"
    "contextual_workflow" = "codex/CONTEXTUAL-WORKFLOW.compiled.md"
    "team" = "codex/TEAM.compiled.md"
    "bootstrap" = "docs-tech/PIPELINE-BOOTSTRAP.json"
    "pipeline_bootstrap" = "docs-tech/PIPELINE-BOOTSTRAP.json"
    "docs" = "DOCS.json"
    "scripts" = "SCRIPTS.json"
    "script" = "SCRIPTS.json"
    "commands" = "COMMANDS.json"
    "command" = "COMMANDS.json"
    "flows" = "FLOWS.json"
    "flow" = "FLOWS.json"
    "engineering" = "context-docs/ENGINEERING.json"
    "agent_contract" = "core/AGENT-CONTRACT.json"
}

$relativePath = $Document.Trim()
if ($aliases.ContainsKey($requestedKey)) {
    $relativePath = $aliases[$requestedKey]
}

$candidatePaths = @(
    (Join-Path $compiledRootPath $relativePath),
    (Join-Path $repoRoot $relativePath)
)
$targetPath = $candidatePaths | Where-Object { Test-Path -LiteralPath $_ -PathType Leaf } | Select-Object -First 1
if ($null -eq $targetPath) {
    $known = @(
        "entrypoint", "rules", "workflow", "contextual_workflow", "team",
        "bootstrap", "docs", "scripts", "commands", "flows", "engineering", "agent_contract"
    )
    throw "No compiled/source context document matches '$Document'. Known aliases: $($known -join ', ')."
}

$targetPath = (Resolve-Path -LiteralPath $targetPath).Path
$compiledRelativePath = $null
if ($targetPath.StartsWith($compiledRootPath, [System.StringComparison]::OrdinalIgnoreCase)) {
    $compiledRelativePath = ($targetPath.Substring(([string]$compiledRootPath).Length).TrimStart("\", "/")) -replace "\\", "/"
}

if (-not $AllowStale -and $compiledRelativePath -and (Test-Path -LiteralPath $checksumPath -PathType Leaf)) {
    $checksum = Get-Content -LiteralPath $checksumPath -Raw | ConvertFrom-Json
    if ($checksum.output_hashes.PSObject.Properties.Name -contains $compiledRelativePath) {
        $expectedHash = [string]$checksum.output_hashes.PSObject.Properties[$compiledRelativePath].Value
        $currentHash = Get-NormalizedFileSha256 -Path $targetPath
        if ($currentHash -ne $expectedHash) {
            throw "Compiled context for '$compiledRelativePath' is stale. Run tools/pipeline/rebuild_ai_compiled_context.ps1 before reading compiled context."
        }
    }
}

$content = [System.IO.File]::ReadAllText($targetPath, [System.Text.UTF8Encoding]::new($false, $true))
if ($Json) {
    [ordered]@{
        document = $Document
        path = $targetPath
        compiled_path = $compiledRelativePath
        content = [string]$content
    } | ConvertTo-Json -Depth 6
    return
}

$content
