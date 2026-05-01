param(
	[string]$EvalDir = "evals"
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$repoRoot = Resolve-Path -LiteralPath (Join-Path $PSScriptRoot "..")
$evalRoot = Join-Path $repoRoot $EvalDir
$errors = [System.Collections.Generic.List[string]]::new()

function Add-CheckError {
	param([string]$Message)
	$errors.Add($Message) | Out-Null
}

function Test-RequiredFile {
	param([string]$RelativePath)

	$path = Join-Path $repoRoot $RelativePath
	if (-not (Test-Path -LiteralPath $path -PathType Leaf)) {
		Add-CheckError "Missing eval file: $RelativePath"
		return ""
	}
	return Get-Content -Raw -LiteralPath $path -Encoding UTF8
}

if (-not (Test-Path -LiteralPath $evalRoot -PathType Container)) {
	throw "Missing eval directory: $EvalDir"
}

$scenarioIds = @(
	"priority_conflict",
	"low_friction_adoption",
	"on_demand_team",
	"finish_boundary",
	"document_ownership",
	"compiled_instruction_layer",
	"three_tier_fit",
	"code_engineering_context_preload",
	"knowledge_freshness_and_fallback",
	"knowledge_entry_lifecycle",
	"pipeline_update_artifact_sync"
)

$requiredFiles = @(
	"$EvalDir/README.md",
	"$EvalDir/personas.yaml",
	"$EvalDir/expected-behaviors.yaml",
	"$EvalDir/scoring.md",
	"$EvalDir/results/baseline.yaml",
	"$EvalDir/results/with-pipeline.yaml"
)

foreach ($scenarioId in $scenarioIds) {
	$requiredFiles += "$EvalDir/prompts/$scenarioId.md"
}

$fileText = @{}
foreach ($file in $requiredFiles) {
	$fileText[$file] = Test-RequiredFile -RelativePath $file
}

$expected = $fileText["$EvalDir/expected-behaviors.yaml"]
foreach ($scenarioId in $scenarioIds) {
	if ($expected -notmatch [regex]::Escape("id: $scenarioId")) {
		Add-CheckError "expected-behaviors.yaml missing scenario id: $scenarioId"
	}
	if ($expected -notmatch [regex]::Escape("prompt_file: `"$EvalDir/prompts/$scenarioId.md`"")) {
		Add-CheckError "expected-behaviors.yaml missing prompt_file for: $scenarioId"
	}
	foreach ($resultFile in @("$EvalDir/results/baseline.yaml", "$EvalDir/results/with-pipeline.yaml")) {
		$resultText = $fileText[$resultFile]
		if ($resultText -notmatch [regex]::Escape("scenario: $scenarioId")) {
			Add-CheckError "$resultFile missing result entry for: $scenarioId"
		}
	}
}

$personas = $fileText["$EvalDir/personas.yaml"]
foreach ($personaId in @("power_user_socratex", "builder_user_kuba", "basic_user_emcia")) {
	if ($personas -notmatch [regex]::Escape("id: $personaId")) {
		Add-CheckError "personas.yaml missing persona id: $personaId"
	}
}

$readme = $fileText["$EvalDir/README.md"]
foreach ($needle in @("manual first", "baseline", "with-pipeline", "low-friction maturity path")) {
	if ($readme -notmatch [regex]::Escape($needle)) {
		Add-CheckError "README.md missing required phrase: $needle"
	}
}

if ($errors.Count -gt 0) {
	Write-Host "ERROR: eval framework check failed."
	foreach ($item in $errors) {
		Write-Host " - $item"
	}
	exit 1
}

Write-Host "OK: eval framework files are present and internally linked."
