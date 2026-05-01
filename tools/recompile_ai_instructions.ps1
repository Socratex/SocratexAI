param(
	[string]$OutputDir = "AI-compiled",
	[string[]]$Packs = @("code", "generic", "personal", "creative"),
	[switch]$Check
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$repoRoot = Resolve-Path -LiteralPath (Join-Path $PSScriptRoot "..")
$outputRoot = Join-Path $repoRoot $OutputDir
$knowledgeCompileScript = Join-Path $PSScriptRoot "knowledge_compile.ps1"
$knowledgeCheckScript = Join-Path $PSScriptRoot "knowledge_check.ps1"

function Get-RepoText {
	param([string]$RelativePath)

	$path = Join-Path $repoRoot $RelativePath
	if (-not (Test-Path -LiteralPath $path -PathType Leaf)) {
		return ""
	}
	return Get-Content -Raw -LiteralPath $path -Encoding UTF8
}

function Join-Lines {
	param([object[]]$Lines)

	$list = [System.Collections.Generic.List[string]]::new()
	foreach ($line in $Lines) {
		$list.Add([string]$line) | Out-Null
	}
	return ($list -join [Environment]::NewLine)
}

function Get-Section {
	param(
		[string]$RelativePath,
		[string]$Selector
	)

	$script = Join-Path $PSScriptRoot "doc_read.ps1"
	if (-not (Test-Path -LiteralPath $script -PathType Leaf)) {
		return ""
	}
	try {
		$output = @(powershell -NoProfile -ExecutionPolicy Bypass -File $script -Path (Join-Path $repoRoot $RelativePath) -Selector $Selector)
		if ($LASTEXITCODE -ne 0) {
			return ""
		}
		return Join-Lines -Lines $output
	} catch {
		return ""
	}
}

function Get-ExistingPacks {
	param([string[]]$Candidates)

	$result = [System.Collections.Generic.List[string]]::new()
	foreach ($pack in $Candidates) {
		$name = ([string]$pack).Trim()
		if ($name.Length -eq 0) {
			continue
		}
		if (Test-Path -LiteralPath (Join-Path $repoRoot "project\$name\PACK.yaml") -PathType Leaf) {
			$result.Add($name) | Out-Null
		}
	}
	return @($result)
}

function New-CompiledFile {
	param(
		[string]$RelativePath,
		[string]$Content
	)

	if ($RelativePath -match 'WORKFLOW|ORCHESTRATION|TEAM|README|compile-report' -and $Content.Trim().Length -lt 20) {
		throw "Compiled file content was unexpectedly short for $RelativePath (length=$($Content.Length))."
	}

	return [pscustomobject]@{
		RelativePath = $RelativePath
		FileContent = $Content.TrimEnd() + [Environment]::NewLine
	}
}

function ConvertTo-Hash {
	param([string]$Text)

	$sha = [System.Security.Cryptography.SHA256]::Create()
	try {
		$bytes = [System.Text.Encoding]::UTF8.GetBytes($Text)
		$hashBytes = $sha.ComputeHash($bytes)
		return ([System.BitConverter]::ToString($hashBytes)).Replace("-", "").ToLowerInvariant()
	} finally {
		$sha.Dispose()
	}
}

function Get-RelativeHash {
	param([string]$RelativePath)

	$path = Join-Path $repoRoot $RelativePath
	if (-not (Test-Path -LiteralPath $path -PathType Leaf)) {
		return $null
	}
	return ConvertTo-Hash -Text (Get-Content -Raw -LiteralPath $path -Encoding UTF8)
}

function Get-SourceManifest {
	param([string[]]$PackNames)

	$sources = [ordered]@{}
	foreach ($path in @(
		"AGENTS.md",
		"README.md",
		"PUBLIC-BOOTSTRAP.md",
		"core/AGENT-CONTRACT.yaml",
		"core/MEMORY-MODEL.yaml",
		"core/PROMOTION-RULES.yaml",
		"core/FILE-FORMATS.yaml",
		"core/ROI-BIAS.yaml",
		"core/TASK-WORK.yaml",
		"core/SCRIPT-FALLBACK.yaml",
		"context-docs/ENGINEERING.yaml",
		"docs-tech/KNOWLEDGE-VIEWS.yaml",
		"tools/knowledge_index.py",
		"tools/knowledge_select.ps1",
		"tools/knowledge_compile.ps1",
		"tools/knowledge_check.ps1",
		"templates/ORCHESTRATION.yaml",
		"templates/docs-tech/KNOWLEDGE-VIEWS.yaml",
		"templates/code/context-docs/ENGINEERING.yaml",
		"templates/team/product.yaml",
		"templates/team/technical.yaml",
		"templates/team/performance.yaml",
		"templates/team/experience.yaml",
		"templates/team/pipeline.yaml"
	)) {
		$hash = Get-RelativeHash -RelativePath $path
		if ($hash) {
			$sources[$path] = $hash
		}
	}
	foreach ($pack in $PackNames) {
		foreach ($path in @(
			"project/$pack/PACK.yaml",
			"project/$pack/WORKFLOW.yaml"
		)) {
			$hash = Get-RelativeHash -RelativePath $path
			if ($hash) {
				$sources[$path] = $hash
			}
		}
	}
	return $sources
}

function New-CompiledFiles {
	Set-StrictMode -Off
	$packNames = @(Get-ExistingPacks -Candidates $Packs)
	$sourceManifest = Get-SourceManifest -PackNames $packNames
	$sourceEntries = @(
		$sourceManifest.GetEnumerator() |
			Sort-Object Name |
			ForEach-Object { "$($_.Name)=$($_.Value)" }
	)
	$sourceHashText = $sourceEntries -join [Environment]::NewLine
	$generatedAt = "source-" + (ConvertTo-Hash -Text $sourceHashText).Substring(0, 12)
	$featureList = Get-RepoText -RelativePath "pipeline_featurelist.json"
	$agentContractPurpose = Get-Section -RelativePath "core/AGENT-CONTRACT.yaml" -Selector "purpose"
	$agentContractPrinciples = Get-Section -RelativePath "core/AGENT-CONTRACT.yaml" -Selector "operating_principles"
	$memoryLayers = Get-Section -RelativePath "core/AGENT-CONTRACT.yaml" -Selector "project_memory_layers"
	$toolFirstYaml = Get-Section -RelativePath "core/AGENT-CONTRACT.yaml" -Selector "tool_first_yaml"
	$codeWorkflowReadOrder = Get-Section -RelativePath "project/code/WORKFLOW.yaml" -Selector "read_order"
	$codeWorkflowGeneral = Get-Section -RelativePath "project/code/WORKFLOW.yaml" -Selector "general_workflow"
	$codeWorkflowVerification = Get-Section -RelativePath "project/code/WORKFLOW.yaml" -Selector "verification_boundary"

	$entry = @"
# Compiled Codex Entrypoint

Generated: $generatedAt

This directory is generated. Do not edit it by hand.
Edit source instructions, then run:

~~~powershell
powershell -NoProfile -ExecutionPolicy Bypass -File tools/recompile_ai_instructions.ps1
~~~

Primary rule: use these compiled files for fast agent orientation, then read source files only when exact details or edits are needed.

Read order for Codex:

1. `AI-compiled/codex/RULES.compiled.md`
2. `AI-compiled/codex/WORKFLOW.compiled.md`
3. `AI-compiled/codex/ORCHESTRATION.compiled.md` only when priority steering matters
4. `AI-compiled/codex/TEAM.compiled.md` only when a role is requested or routed
5. Source files referenced by the compiled layer when implementation requires exact detail

Generated checksum data lives in `AI-compiled/checksum.json`.
"@

	$rules = @"
# Compiled Rules for Codex

Generated: $generatedAt

## Source of Truth

- Source instructions remain authoritative.
- `AI-compiled/` is a generated read-optimized cache.
- Do not edit compiled files manually.
- Recompile after source instruction, workflow, template, or pack changes.

## Core Contract Extracts

$agentContractPurpose

$agentContractPrinciples

$memoryLayers

## Tool Discipline

$toolFirstYaml

## Feature Manifest

~~~json
$featureList
~~~
"@

	$compiledWorkflowContent = @"
# Compiled Workflow for Codex

Generated: $generatedAt

## Code Read Order

$codeWorkflowReadOrder

## General Workflow

$codeWorkflowGeneral

## Verification Boundary

$codeWorkflowVerification

## Recompile Command

Use this command after changing source instructions, templates, core docs, project packs, or compiled-output rules:

~~~powershell
powershell -NoProfile -ExecutionPolicy Bypass -File tools/recompile_ai_instructions.ps1
~~~

Use this command to check for drift:

~~~powershell
powershell -NoProfile -ExecutionPolicy Bypass -File tools/check_compiled_instructions.ps1
~~~
"@

	$orchestration = @"
# Compiled Orchestration Rules

Generated: $generatedAt

`ORCHESTRATION.yaml` is opt-in priority context, not default context.

Read it when:

- planning, priority, roadmap, broad feature triage, or project-risk judgment is needed
- a user request may conflict with a higher-priority active pain point
- work must be routed to active plan, backlog, issue registry, or decision log

Do not read it for narrow local fixes without priority or planning impact.

Installed projects get `ORCHESTRATION.yaml` from `templates/ORCHESTRATION.yaml`.
"@
	if ($compiledWorkflowContent.Trim().Length -lt 100) {
		throw "Compiled workflow content was unexpectedly short."
	}
	if ($orchestration.Trim().Length -lt 100) {
		throw "Compiled orchestration content was unexpectedly short."
	}

	$teamFiles = [System.Collections.Generic.List[string]]::new()
	foreach ($role in @("product", "technical", "performance", "experience", "pipeline")) {
		$text = Get-RepoText -RelativePath "templates/team/$role.yaml"
		if ($text.Trim().Length -gt 0) {
			$teamFiles.Add("## $role") | Out-Null
			$teamFiles.Add("") | Out-Null
			$teamFiles.Add('```yaml') | Out-Null
			$teamFiles.Add($text.TrimEnd()) | Out-Null
			$teamFiles.Add('```') | Out-Null
			$teamFiles.Add("") | Out-Null
		}
	}
	$teamBody = @($teamFiles) -join [Environment]::NewLine
	$team = @"
# Compiled Team Role Lenses

Generated: $generatedAt

Team files are on-demand decision lenses. Load only when the user names a role, asks for team-style review, or `ORCHESTRATION.yaml` routes the task to that role.

$teamBody
"@
	if ($team.Trim().Length -lt 100) {
		throw "Compiled team content was unexpectedly short."
	}

	$index = [ordered]@{
		schema = "socratex-compiled-agent-instructions/v1"
		generated_at = $generatedAt
		role = "generated_agent_cache"
		source_of_truth = "source instruction files outside AI-compiled"
		do_not_edit_manually = $true
		targets = @("codex")
		packs = @($packNames)
		files = @(
			"codex/ENTRYPOINT.md",
			"codex/RULES.compiled.md",
			"codex/WORKFLOW.compiled.md",
			"codex/ORCHESTRATION.compiled.md",
			"codex/TEAM.compiled.md"
		)
		recompile_command = "powershell -NoProfile -ExecutionPolicy Bypass -File tools/recompile_ai_instructions.ps1"
		check_command = "powershell -NoProfile -ExecutionPolicy Bypass -File tools/check_compiled_instructions.ps1"
		sources = $sourceManifest
	}
	$indexJson = $index | ConvertTo-Json -Depth 8

	$compiledReadme = @"
# AI-compiled

Generated read-optimized agent instructions.

Do not edit this directory manually. Edit source instructions and run:

~~~powershell
powershell -NoProfile -ExecutionPolicy Bypass -File tools/recompile_ai_instructions.ps1
~~~

Codex starts at `codex/ENTRYPOINT.md`.
"@
	$compiledIndex = @"
schema: socratex-compiled-agent-index/v1
role: generated_agent_cache
generated_at: $generatedAt
do_not_edit_manually: true
targets:
  - codex
entrypoints:
  codex: codex/ENTRYPOINT.md
recompile_command: powershell -NoProfile -ExecutionPolicy Bypass -File tools/recompile_ai_instructions.ps1
check_command: powershell -NoProfile -ExecutionPolicy Bypass -File tools/check_compiled_instructions.ps1
"@
	$files = @()
	if ($compiledReadme.Trim().Length -lt 20) {
		throw "compiledReadme variable unexpectedly short before file creation."
	}
	$files += New-CompiledFile -RelativePath "README.md" -Content $compiledReadme
	$files += New-CompiledFile -RelativePath "INDEX.yaml" -Content $compiledIndex
	$files += New-CompiledFile -RelativePath "codex/ENTRYPOINT.md" -Content $entry
	$files += New-CompiledFile -RelativePath "codex/RULES.compiled.md" -Content $rules
	$files += New-CompiledFile -RelativePath "codex/WORKFLOW.compiled.md" -Content $compiledWorkflowContent
	$files += New-CompiledFile -RelativePath "codex/ORCHESTRATION.compiled.md" -Content $orchestration
	$files += New-CompiledFile -RelativePath "codex/TEAM.compiled.md" -Content $team

	$checksums = [ordered]@{}
	foreach ($file in $files) {
		$checksums[$file.RelativePath] = ConvertTo-Hash -Text $file.FileContent
	}
	$checksumPayload = [ordered]@{
		schema = "socratex-compiled-agent-checksum/v1"
		generated_at = $generatedAt
		source_hashes = $sourceManifest
		output_hashes = $checksums
	}
	$checksumJson = $checksumPayload | ConvertTo-Json -Depth 8
	$files += New-CompiledFile -RelativePath "compile-report.json" -Content $indexJson
	$files += New-CompiledFile -RelativePath "checksum.json" -Content $checksumJson

	return @($files)
}

$compiledFiles = @(New-CompiledFiles)

if ($Check) {
	$drift = [System.Collections.Generic.List[string]]::new()
	foreach ($file in $compiledFiles) {
		$path = Join-Path $outputRoot $file.RelativePath
		if (-not (Test-Path -LiteralPath $path -PathType Leaf)) {
			$drift.Add("missing: $($file.RelativePath)") | Out-Null
			continue
		}
		$current = Get-Content -Raw -LiteralPath $path -Encoding UTF8
		if ($current -ne $file.FileContent) {
			$drift.Add("stale: $($file.RelativePath)") | Out-Null
		}
	}
	if ($drift.Count -gt 0) {
		Write-Host "ERROR: compiled agent instructions are stale."
		foreach ($item in $drift) {
			Write-Host " - $item"
		}
		Write-Host "Run: powershell -NoProfile -ExecutionPolicy Bypass -File tools/recompile_ai_instructions.ps1"
		exit 1
	}
	if (Test-Path -LiteralPath $knowledgeCheckScript -PathType Leaf) {
		& powershell -NoProfile -ExecutionPolicy Bypass -File $knowledgeCheckScript
		if ($LASTEXITCODE -ne 0) {
			exit $LASTEXITCODE
		}
	}
	Write-Host "OK: compiled agent instructions are current."
	exit 0
}

if (Test-Path -LiteralPath $outputRoot) {
	Remove-Item -LiteralPath $outputRoot -Recurse -Force
}
New-Item -ItemType Directory -Force -Path $outputRoot | Out-Null

foreach ($file in $compiledFiles) {
	$path = Join-Path $outputRoot $file.RelativePath
	New-Item -ItemType Directory -Force -Path (Split-Path -Parent $path) | Out-Null
	[System.IO.File]::WriteAllText($path, $file.FileContent, [System.Text.UTF8Encoding]::new($false))
}

if (Test-Path -LiteralPath $knowledgeCompileScript -PathType Leaf) {
	& powershell -NoProfile -ExecutionPolicy Bypass -File $knowledgeCompileScript
	if ($LASTEXITCODE -ne 0) {
		exit $LASTEXITCODE
	}
}

Write-Host "OK: recompiled AI instructions into $OutputDir"
