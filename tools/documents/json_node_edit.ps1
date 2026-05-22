param(
	[ValidateSet("read", "insert", "set", "move", "delete", "insert-line", "set-line", "move-line")]
	[string]$Operation = "",
	[string]$Path = "",
	[string]$Node = "",
	[string]$TargetPath = "",
	[string]$TargetNode = "",
	[ValidateSet("start", "end", "before", "after")]
	[string]$Position = "end",
	[string]$ReferenceNode = "",
	[int]$Line = 0,
	[int]$ReferenceLine = 0,
	[string]$ReferenceText = "",
	[string[]]$Text = @(),
	[string]$ValueJson = "",
	[string]$ValueJsonFile = "",
	[switch]$ValueJsonStdin,
	[switch]$Replace,
	[switch]$Help,
	[Parameter(ValueFromPipeline = $true)]
	[string[]]$PipelineJson = @()
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

function Show-Usage {
	@"
Usage:
  json_node_edit.ps1 -Operation read -Path <file> -Node <node>
  json_node_edit.ps1 -Operation insert -Path <file> -Node <node> [-Position start|end|before|after] [-ReferenceNode <node>] (-ValueJson|-ValueJsonFile|-ValueJsonStdin|-Text)
  json_node_edit.ps1 -Operation set -Path <file> -Node <node> (-ValueJson|-ValueJsonFile|-ValueJsonStdin|-Text)
  json_node_edit.ps1 -Operation move -Path <file> -Node <node> [-TargetPath <file>] [-TargetNode <node>] [-Position start|end|before|after] [-ReferenceNode <node>]
  json_node_edit.ps1 -Operation delete -Path <file> -Node <node>
  json_node_edit.ps1 -Operation insert-line -Path <file> -Node <list-node> -Text <line>... [-Position ...] [-ReferenceLine N|-ReferenceText text]
  json_node_edit.ps1 -Operation set-line -Path <file> -Node <list-node> -Line N -Text <line>
  json_node_edit.ps1 -Operation move-line -Path <file> -Node <list-node> -Line N [-Position ...] [-ReferenceLine N|-ReferenceText text]

Node paths are dot-separated JSON paths, or slash-separated when a segment contains dots, for example:
  content.pass_7_dense_world_traversal_performance_foundation
  content.pass_7_dense_world_traversal_performance_foundation.steps
  content/json_node_edit.ps1

Use this wrapper when the agent knows the full JSON node path. Prefer it for structural edits that do not change content:
move, delete, reorder, insert before/after, and list-line ordering.
"@
}

if ($Help) {
	Show-Usage
	exit 0
}

if ([string]::IsNullOrWhiteSpace($Operation)) { throw "-Operation is required. Use -Help for examples." }
if ([string]::IsNullOrWhiteSpace($Path)) { throw "-Path is required. Use -Help for examples." }
if ([string]::IsNullOrWhiteSpace($Node)) { throw "-Node is required. Use -Help for examples." }

. (Join-Path $PSScriptRoot "..\pipeline\resolve_tool_runtime.ps1")
$python = Resolve-SocratexPython -SearchRoot $PSScriptRoot

$script = Join-Path $PSScriptRoot "json_list_doc.py"
$commandByOperation = @{
	"read" = "read-node"
	"insert" = "insert-node"
	"set" = "set-node"
	"move" = "move-node"
	"delete" = "delete-node"
	"insert-line" = "insert-node-line"
	"set-line" = "set-node-line"
	"move-line" = "move-node-line"
}

[object[]]$arguments = @($script, $commandByOperation[$Operation], $Path, $Node)

if ($Operation -in @("insert", "move", "insert-line", "move-line")) {
	$arguments += @("--position", $Position)
	if ($ReferenceNode -ne "") { $arguments += @("--reference-node", $ReferenceNode) }
}
if ($Operation -eq "move") {
	if ($TargetPath -ne "") { $arguments += @("--target-path", $TargetPath) }
	if ($TargetNode -ne "") { $arguments += @("--target-node", $TargetNode) }
	if ($Replace) { $arguments += "--replace" }
}
if ($Operation -in @("set-line", "move-line")) {
	if ($Line -le 0) { throw "-Line must be greater than 0 for $Operation." }
	$arguments += @("--line", [string]$Line)
}
if ($Operation -in @("insert-line", "move-line")) {
	if ($ReferenceLine -gt 0) { $arguments += @("--reference-line", [string]$ReferenceLine) }
	if ($ReferenceText -ne "") { $arguments += @("--reference-text", $ReferenceText) }
}

$valueOperations = @("insert", "set")
if ($Operation -in $valueOperations) {
	$valueSourceCount = 0
	if ($Text.Count -gt 0) { $valueSourceCount++ }
	if ($ValueJson -ne "") { $valueSourceCount++ }
	if ($ValueJsonFile -ne "") { $valueSourceCount++ }
	if ($ValueJsonStdin) { $valueSourceCount++ }
	if ($valueSourceCount -ne 1) {
		throw "Use exactly one of -Text, -ValueJson, -ValueJsonFile, or -ValueJsonStdin for $Operation."
	}
	foreach ($textValue in $Text) { $arguments += @("--text", $textValue) }
	if ($ValueJson -ne "") { $arguments += @("--value-json", $ValueJson) }
	if ($ValueJsonFile -ne "") {
		$arguments += @("--value-json-file", (Resolve-Path -LiteralPath $ValueJsonFile).Path)
	}
}
if ($Operation -in @("insert-line", "set-line")) {
	if ($Text.Count -eq 0) { throw "-Text is required for $Operation." }
	if ($Operation -eq "set-line" -and $Text.Count -ne 1) { throw "-Text must contain exactly one line for set-line." }
	foreach ($textValue in $Text) { $arguments += @("--text", $textValue) }
}

$temporaryJsonFile = ""
if ($Operation -in $valueOperations -and $ValueJsonStdin) {
	if ($PipelineJson.Count -gt 0) {
		$temporaryJsonFile = [System.IO.Path]::GetTempFileName()
		[System.IO.File]::WriteAllText(
			$temporaryJsonFile,
			($PipelineJson -join [Environment]::NewLine),
			[System.Text.UTF8Encoding]::new($false)
		)
		$arguments += @("--value-json-file", $temporaryJsonFile)
	} else {
		$arguments += "--value-json-stdin"
	}
}

try {
	& $python @arguments
	if ($LASTEXITCODE -ne 0) {
		throw "json_node_edit failed with exit code $LASTEXITCODE"
	}
} finally {
	if ($temporaryJsonFile -ne "" -and (Test-Path -LiteralPath $temporaryJsonFile)) {
		Remove-Item -LiteralPath $temporaryJsonFile -Force
	}
}
