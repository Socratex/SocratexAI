param(
	[Parameter(Position = 0, ValueFromRemainingArguments = $true)]
	[string[]]$Text = @(),
	[Parameter()]
	[string]$RepoRoot = "",
	[Parameter()]
	[switch]$NoDefaults,
	[Parameter()]
	[switch]$Json,
	[Parameter()]
	[switch]$AsKnowledgeSelectArgs
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

if ([string]::IsNullOrWhiteSpace($RepoRoot)) {
	$RepoRoot = Resolve-Path -LiteralPath (Join-Path $PSScriptRoot "..")
} else {
	$RepoRoot = Resolve-Path -LiteralPath $RepoRoot
}

function Add-Tag {
	param(
		[System.Collections.Generic.List[string]]$Target,
		[string]$Tag
	)

	$value = $Tag.Trim().ToLowerInvariant()
	if ($value.Length -gt 0 -and -not $Target.Contains($value)) {
		$Target.Add($value) | Out-Null
	}
}

function Get-KnownTags {
	param([string]$Root)

	$manifestPath = Join-Path $Root "AI-compiled\project\knowledge-manifest.json"
	if (-not (Test-Path -LiteralPath $manifestPath -PathType Leaf)) {
		return @()
	}

	try {
		$manifest = Get-Content -Raw -LiteralPath $manifestPath -Encoding UTF8 | ConvertFrom-Json
		return @($manifest.tags | ForEach-Object { [string]$_.tag } | Where-Object { $_ -ne "" })
	} catch {
		return @()
	}
}

$inputText = ($Text -join " ").Trim()
$normalized = $inputText.ToLowerInvariant()
$tags = [System.Collections.Generic.List[string]]::new()

if (-not $NoDefaults) {
	foreach ($tag in @("engineering", "workflow", "docs-workflow")) {
		Add-Tag -Target $tags -Tag $tag
	}
}

$rules = [ordered]@{
	"architecture" = @("architecture", "architect", "architekt", "boundary", "boundaries", "ownership", "contract", "ddd", "adiv", "design", "runtime", "source of truth")
	"coding" = @("code", "coding", "program", "script", "implement", "implementation", "refactor", "review", "bugfix", "function", "class")
	"compiled-context" = @("compiled", "skompil", "ai-compiled", "context layer", "compiled context", "dyrektyw", "directive", "instruction")
	"knowledge" = @("knowledge", "sqlite", "tag", "tags", "notat", "note", "notes", "selector", "context", "kontekst")
	"debugging" = @("bug", "error", "crash", "console", "log", "trace", "diagnostic", "diagnost")
	"performance" = @("performance", "fps", "memory", "profiler", "budget", "hot path")
	"domain_modeling" = @("domain_modeling", "world", "chunk", "biome", "terrain", "route")
	"persistence" = @("save", "load", "persistence", "persistent", "reconstruction", "stable id")
	"verification" = @("test", "check", "verify", "verification", "audit", "quality gate", "gate")
	"gamedev" = @("game", "gameplay", "combat", "movement", "camera", "collision", "traversal")
	"documentation" = @("doc", "docs", "document", "markdown", "json", "changelog", "featurelist")
	"planning" = @("plan", "roadmap", "priority", "todo", "pass", "continue")
}

foreach ($entry in $rules.GetEnumerator()) {
	foreach ($pattern in $entry.Value) {
		if ($normalized.Contains($pattern)) {
			Add-Tag -Target $tags -Tag ([string]$entry.Key)
			break
		}
	}
}

$knownTags = @(Get-KnownTags -Root $RepoRoot)
if ($knownTags.Count -gt 0) {
	$knownSet = [System.Collections.Generic.HashSet[string]]::new([StringComparer]::OrdinalIgnoreCase)
	foreach ($tag in $knownTags) {
		$knownSet.Add($tag) | Out-Null
	}
	$filtered = [System.Collections.Generic.List[string]]::new()
	foreach ($tag in $tags) {
		if ($knownSet.Contains($tag)) {
			Add-Tag -Target $filtered -Tag $tag
		}
	}
	$tags = $filtered
}

if ($AsKnowledgeSelectArgs) {
	if ($tags.Count -eq 0) {
		Write-Output "-Match any"
		exit 0
	}
	Write-Output ("-Tags " + ($tags -join ",") + " -Match any")
	exit 0
}

if ($Json) {
	[ordered]@{
		text = $inputText
		tags = @($tags)
	} | ConvertTo-Json -Depth 4
	exit 0
}

foreach ($tag in $tags) {
	Write-Output $tag
}
