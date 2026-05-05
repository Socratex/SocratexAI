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

function Read-JsonText {
	param(
		[string]$Text,
		[string]$Label
	)

	try {
		return $Text | ConvertFrom-Json
	} catch {
		Add-CheckError "$Label is not valid JSON: $($_.Exception.Message)"
		return $null
	}
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
	"pipeline_update_artifact_sync",
	"context_tagged_knowledge_prelude",
	"task_type_router",
	"unknown_task_routing"
)

$requiredFiles = @(
	"$EvalDir/README.md",
	"$EvalDir/personas.json",
	"$EvalDir/expected-behaviors.json",
	"$EvalDir/scoring.md",
	"$EvalDir/results/baseline.json",
	"$EvalDir/results/with-pipeline.json"
)

foreach ($scenarioId in $scenarioIds) {
	$requiredFiles += "$EvalDir/prompts/$scenarioId.md"
}

$fileText = @{}
foreach ($file in $requiredFiles) {
	$fileText[$file] = Test-RequiredFile -RelativePath $file
}

$expected = Read-JsonText -Text $fileText["$EvalDir/expected-behaviors.json"] -Label "expected-behaviors.json"
$expectedScenarios = @{}
if ($null -ne $expected -and $null -ne $expected.scenarios) {
	foreach ($scenario in @($expected.scenarios)) {
		if ($null -ne $scenario.id) {
			$expectedScenarios[[string]$scenario.id] = $scenario
		}
	}
}
$resultSets = @{}
foreach ($resultFile in @("$EvalDir/results/baseline.json", "$EvalDir/results/with-pipeline.json")) {
	$resultPayload = Read-JsonText -Text $fileText[$resultFile] -Label $resultFile
	$resultIds = @{}
	if ($null -ne $resultPayload -and $null -ne $resultPayload.results) {
		foreach ($result in @($resultPayload.results)) {
			if ($null -ne $result.scenario) {
				$resultIds[[string]$result.scenario] = $true
			}
		}
	}
	$resultSets[$resultFile] = $resultIds
}
foreach ($scenarioId in $scenarioIds) {
	if (-not $expectedScenarios.ContainsKey($scenarioId)) {
		Add-CheckError "expected-behaviors.json missing scenario id: $scenarioId"
	} elseif ([string]$expectedScenarios[$scenarioId].prompt_file -ne "$EvalDir/prompts/$scenarioId.md") {
		Add-CheckError "expected-behaviors.json missing prompt_file for: $scenarioId"
	}
	foreach ($resultFile in @("$EvalDir/results/baseline.json", "$EvalDir/results/with-pipeline.json")) {
		if (-not $resultSets[$resultFile].ContainsKey($scenarioId)) {
			Add-CheckError "$resultFile missing result entry for: $scenarioId"
		}
	}
}

$personas = Read-JsonText -Text $fileText["$EvalDir/personas.json"] -Label "personas.json"
$personaIds = @{}
if ($null -ne $personas -and $null -ne $personas.personas) {
	foreach ($persona in @($personas.personas)) {
		if ($null -ne $persona.id) {
			$personaIds[[string]$persona.id] = $true
		}
	}
}
foreach ($personaId in @("power_user_socratex", "builder_user_kuba", "basic_user_emcia")) {
	if (-not $personaIds.ContainsKey($personaId)) {
		Add-CheckError "personas.json missing persona id: $personaId"
	}
}

$readme = $fileText["$EvalDir/README.md"]
foreach ($needle in @("manual first", "baseline", "with-pipeline", "low-friction maturity path", "missed_context", "do not add new synthetic scenarios")) {
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
