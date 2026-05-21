param(
    [string]$ProjectRoot = ".",
    [int]$MaxCandidates = 40
)

$ErrorActionPreference = "Stop"

$resolvedRoot = (Resolve-Path -LiteralPath $ProjectRoot).Path
$gitFiles = @()

try {
    $gitFiles = & git -C $resolvedRoot ls-files 2>$null
} catch {
    $gitFiles = @()
}

if (-not $gitFiles -or $LASTEXITCODE -ne 0) {
    $extensions = @("*.gd", "*.cs", "*.ts", "*.tsx", "*.js", "*.jsx", "*.py", "*.ps1", "*.java", "*.kt", "*.go", "*.rs", "*.php")
    $gitFiles = Get-ChildItem -LiteralPath $resolvedRoot -Recurse -File -Include $extensions |
        Where-Object { $_.FullName -notmatch "[/\\](\.git|AI-compiled|ignored|logs|logs-diagnostics|logs-performance|node_modules|vendor|Tools[/\\]Python312)[/\\]" } |
        ForEach-Object { [System.IO.Path]::GetRelativePath($resolvedRoot, $_.FullName) }
}

$codeExtensions = @(".gd", ".cs", ".ts", ".tsx", ".js", ".jsx", ".py", ".ps1", ".java", ".kt", ".go", ".rs", ".php")
$skipPattern = "[/\\](AI-compiled|ignored|logs|logs-diagnostics|logs-performance|node_modules|vendor|Tools[/\\]Python312)[/\\]|\.uid$|\.import$|\.tres$|\.tscn$"
$importantPathPattern = "(movement|player|world|worldgen|diagnostic|runtime|stream|save|persistence|combat|enemy|camera|ui|audio|registry|repository|service|system|controller|orchestrator|coordinator|pipeline|quality|tool)"

$candidates = foreach ($relativePath in $gitFiles) {
    if ([string]::IsNullOrWhiteSpace($relativePath)) { continue }
    if ($relativePath -match $skipPattern) { continue }
    $extension = [System.IO.Path]::GetExtension($relativePath)
    if ($codeExtensions -notcontains $extension) { continue }

    $fullPath = Join-Path $resolvedRoot $relativePath
    if (-not (Test-Path -LiteralPath $fullPath -PathType Leaf)) { continue }

    $lineCount = 0
    try {
        $lineCount = (Get-Content -LiteralPath $fullPath -ErrorAction Stop | Measure-Object -Line).Lines
    } catch {
        $lineCount = 0
    }

    $score = 0
    if ($relativePath -match $importantPathPattern) { $score += 5 }
    if ($lineCount -ge 250) { $score += 4 }
    elseif ($lineCount -ge 120) { $score += 2 }
    if ($relativePath -match "[/\\](domain|application|infrastructure|systems?|services?|runtime|diagnostics?)[/\\]") { $score += 3 }
    if ($relativePath -match "(_test|test_|spec)") { $score -= 2 }

    if ($score -le 0) { continue }

    [pscustomobject]@{
        path = $relativePath
        lines = $lineCount
        score = $score
        reason = if ($relativePath -match $importantPathPattern) { "named system/runtime/diagnostic path" } else { "large or boundary-like code file" }
    }
}

$sorted = $candidates | Sort-Object -Property @{ Expression = "score"; Descending = $true }, @{ Expression = "lines"; Descending = $true }, "path" | Select-Object -First $MaxCandidates

Write-Output "# AI-native code contract dry run"
Write-Output ""
Write-Output "Project root: $resolvedRoot"
Write-Output "Mode: dry-run only; no files were modified."
Write-Output ""
Write-Output "## Header standard"
Write-Output ""
Write-Output "Place this as a comment-prefixed JSON-like block at the top of major system, boundary, diagnostic, runtime, or repeatedly agent-touched source files:"
Write-Output ""
Write-Output 'AI_CONTRACT:'
Write-Output '  purpose: "What this file exists to own."'
Write-Output '  owns:'
Write-Output '    - "state, behavior, or invariant owned here"'
Write-Output '  must_not:'
Write-Output '    - "side effect, layer, or responsibility that belongs elsewhere"'
Write-Output '  design_goals:'
Write-Output '    - "reader-visible intent, feel, safety, budget, or extension goal"'
Write-Output '  non_goals:'
Write-Output '    - "tempting behavior this file must not grow into"'
Write-Output '  diagnostics:'
Write-Output '    taxonomy: "[DOMAIN][SYSTEM][EVENT]"'
Write-Output '    fields: ["stable_field_name"]'
Write-Output '  layer:'
Write-Output '    name: "DOMAIN_OR_LAYER"'
Write-Output '    cannot_depend_on: ["forbidden dependency"]'
Write-Output '  ai_notes:'
Write-Output '    - "short future-agent warning only when useful"'
Write-Output ""
Write-Output "## Candidate rollout files"
Write-Output ""

if (-not $sorted) {
    Write-Output "No strong candidates found by the lightweight heuristic."
    exit 0
}

foreach ($candidate in $sorted) {
    Write-Output ("- {0} ({1} lines, score {2}) - {3}" -f $candidate.path, $candidate.lines, $candidate.score, $candidate.reason)
}
