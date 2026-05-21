[CmdletBinding(PositionalBinding = $false)]
param(
	[Parameter(Mandatory = $true)]
	[string]$TaskId,
	[Parameter(Mandatory = $true)]
	[string]$GroupId,
	[Parameter(Mandatory = $true)]
	[string]$SubtaskId,
	[string]$ProjectRoot = ".",
	[ValidateSet("planned", "active", "done", "blocked")]
	[string]$Status = "done",
	[string]$GroupGoal = "",
	[string]$SubtaskGoal = "",
	[string]$HandoffSummary = "",
	[string[]]$InspectedFiles = @(),
	[string[]]$ChangedFiles = @(),
	[string[]]$Verification = @(),
	[string[]]$Risks = @(),
	[string[]]$NextFiles = @(),
	[string[]]$NextCommands = @(),
	[string]$NextSubtaskId = "",
	[string]$NextSubtaskGoal = "",
	[string]$HandoffPath = "",
	[string]$PromptPath = "",
	[switch]$NoPrompt,
	[switch]$PrintJson
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$repoRoot = Resolve-Path -LiteralPath $ProjectRoot
if ([string]::IsNullOrWhiteSpace($HandoffPath)) {
	$HandoffPath = Join-Path $repoRoot.Path "docs-tech/cache/grouped_task_handoff.json"
} elseif (-not [System.IO.Path]::IsPathRooted($HandoffPath)) {
	$HandoffPath = Join-Path $repoRoot.Path $HandoffPath
}
if ([string]::IsNullOrWhiteSpace($PromptPath)) {
	$PromptPath = Join-Path $repoRoot.Path "docs-tech/cache/next_subtask_prompt.md"
} elseif (-not [System.IO.Path]::IsPathRooted($PromptPath)) {
	$PromptPath = Join-Path $repoRoot.Path $PromptPath
}

function Convert-ToArray {
	param([string[]]$Values)
	$items = [System.Collections.Generic.List[string]]::new()
	foreach ($value in $Values) {
		if ([string]::IsNullOrWhiteSpace([string]$value)) {
			continue
		}
		foreach ($part in ([string]$value -split "[,;`n]")) {
			$trimmed = $part.Trim()
			if ($trimmed.Length -gt 0) {
				$items.Add($trimmed) | Out-Null
			}
		}
	}
	return @($items)
}

function New-EmptyState {
	return [ordered]@{
		schema = "socratex-grouped-task-handoff/v1"
		metadata = [ordered]@{
			task_id = $TaskId
			current_group_id = $GroupId
			current_subtask_id = $SubtaskId
			updated_at_utc = [System.DateTime]::UtcNow.ToString("o")
			model = "User approves groups; subtasks inside an approved group can run automatically through file handoff."
		}
		groups = [ordered]@{}
	}
}

if (Test-Path -LiteralPath $HandoffPath -PathType Leaf) {
	try {
		$state = Get-Content -LiteralPath $HandoffPath -Raw | ConvertFrom-Json -AsHashtable
	} catch {
		throw "Existing handoff file is not valid JSON: $HandoffPath"
	}
} else {
	$state = New-EmptyState
}

if (-not $state.Contains("schema")) {
	$state["schema"] = "socratex-grouped-task-handoff/v1"
}
if (-not $state.Contains("metadata") -or $null -eq $state["metadata"]) {
	$state["metadata"] = [ordered]@{}
}
if (-not $state.Contains("groups") -or $null -eq $state["groups"]) {
	$state["groups"] = [ordered]@{}
}

$state["metadata"]["task_id"] = $TaskId
$state["metadata"]["current_group_id"] = $GroupId
$state["metadata"]["current_subtask_id"] = $SubtaskId
$state["metadata"]["updated_at_utc"] = [System.DateTime]::UtcNow.ToString("o")

if (-not $state["groups"].Contains($GroupId)) {
	$state["groups"][$GroupId] = [ordered]@{
		goal = $GroupGoal
		status = "active"
		subtasks = [ordered]@{}
		handoff_for_next = [ordered]@{}
	}
}

$group = $state["groups"][$GroupId]
if (-not [string]::IsNullOrWhiteSpace($GroupGoal)) {
	$group["goal"] = $GroupGoal
}
if (-not $group.Contains("subtasks") -or $null -eq $group["subtasks"]) {
	$group["subtasks"] = [ordered]@{}
}
if (-not $group.Contains("handoff_for_next") -or $null -eq $group["handoff_for_next"]) {
	$group["handoff_for_next"] = [ordered]@{}
}

$record = [ordered]@{
	id = $SubtaskId
	status = $Status
	goal = $SubtaskGoal
	completed_at_utc = [System.DateTime]::UtcNow.ToString("o")
	summary = $HandoffSummary
	inspected_files = @(Convert-ToArray -Values $InspectedFiles)
	changed_files = @(Convert-ToArray -Values $ChangedFiles)
	verification = @(Convert-ToArray -Values $Verification)
	risks = @(Convert-ToArray -Values $Risks)
	next = [ordered]@{
		subtask_id = $NextSubtaskId
		goal = $NextSubtaskGoal
		files = @(Convert-ToArray -Values $NextFiles)
		commands = @(Convert-ToArray -Values $NextCommands)
	}
}
$group["subtasks"][$SubtaskId] = $record
$group["handoff_for_next"] = $record["next"]
if ($Status -eq "blocked") {
	$group["status"] = "blocked"
} elseif (-not [string]::IsNullOrWhiteSpace($NextSubtaskId)) {
	$group["status"] = "active"
} elseif ($Status -eq "done") {
	$group["status"] = "done"
}

New-Item -ItemType Directory -Force -Path (Split-Path -Parent $HandoffPath) | Out-Null
$json = $state | ConvertTo-Json -Depth 20
[System.IO.File]::WriteAllText($HandoffPath, $json + [Environment]::NewLine, [System.Text.UTF8Encoding]::new($false))

if (-not $NoPrompt) {
	$promptLines = [System.Collections.Generic.List[string]]::new()
	$promptLines.Add("# Next Grouped Subtask Prompt") | Out-Null
	$promptLines.Add("") | Out-Null
	$promptLines.Add("Task: $TaskId") | Out-Null
	$promptLines.Add("Group: $GroupId") | Out-Null
	$promptLines.Add("Previous subtask: $SubtaskId") | Out-Null
	if (-not [string]::IsNullOrWhiteSpace($NextSubtaskId)) {
		$promptLines.Add("Next subtask: $NextSubtaskId") | Out-Null
	}
	if (-not [string]::IsNullOrWhiteSpace($NextSubtaskGoal)) {
		$promptLines.Add("") | Out-Null
		$promptLines.Add("Next goal: $NextSubtaskGoal") | Out-Null
	}
	$promptLines.Add("") | Out-Null
	$promptLines.Add("Read the project startup context by tier, then read:") | Out-Null
	$promptLines.Add("- $([System.IO.Path]::GetRelativePath($repoRoot.Path, $HandoffPath).Replace('\', '/'))") | Out-Null
	$promptLines.Add("") | Out-Null
	$promptLines.Add("Previous handoff summary:") | Out-Null
	$promptLines.Add($HandoffSummary) | Out-Null
	$promptLines.Add("") | Out-Null
	$promptLines.Add("Risks to preserve:") | Out-Null
	foreach ($risk in (Convert-ToArray -Values $Risks)) {
		$promptLines.Add("- $risk") | Out-Null
	}
	$promptLines.Add("") | Out-Null
	$promptLines.Add("Suggested files:") | Out-Null
	foreach ($file in (Convert-ToArray -Values $NextFiles)) {
		$promptLines.Add("- $file") | Out-Null
	}
	$promptLines.Add("") | Out-Null
	$promptLines.Add("Suggested commands:") | Out-Null
	foreach ($command in (Convert-ToArray -Values $NextCommands)) {
		$promptLines.Add("- $command") | Out-Null
	}
	New-Item -ItemType Directory -Force -Path (Split-Path -Parent $PromptPath) | Out-Null
	[System.IO.File]::WriteAllText($PromptPath, (($promptLines -join [Environment]::NewLine) + [Environment]::NewLine), [System.Text.UTF8Encoding]::new($false))
}

if ($PrintJson) {
	$state | ConvertTo-Json -Depth 20
} else {
	Write-Host "OK: grouped task handoff updated"
	Write-Host ("handoff: {0}" -f [System.IO.Path]::GetRelativePath($repoRoot.Path, $HandoffPath).Replace("\", "/"))
	if (-not $NoPrompt) {
		Write-Host ("next_prompt: {0}" -f [System.IO.Path]::GetRelativePath($repoRoot.Path, $PromptPath).Replace("\", "/"))
	}
}
