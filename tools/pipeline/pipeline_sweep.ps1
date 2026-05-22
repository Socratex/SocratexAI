param(
	[string]$Config = "",
	[string]$Source = "",
	[string[]]$Project = @(),
	[switch]$Execute,
	[switch]$Update,
	[switch]$Smoke,
	[switch]$Finalize,
	[switch]$All,
	[switch]$StopOnFailure,
	[switch]$Json,
	[switch]$Help
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

. (Join-Path $PSScriptRoot "resolve_tool_runtime.ps1")
$python = Resolve-SocratexPython -SearchRoot $PSScriptRoot

$script = Join-Path $PSScriptRoot "pipeline_sweep.py"
$arguments = @($script)
if (-not [string]::IsNullOrWhiteSpace($Config)) { $arguments += @("--config", $Config) }
if (-not [string]::IsNullOrWhiteSpace($Source)) { $arguments += @("--source", $Source) }
foreach ($projectSpec in $Project) {
	foreach ($splitProjectSpec in @($projectSpec -split "," | Where-Object { -not [string]::IsNullOrWhiteSpace($_) })) {
		$arguments += @("--project", $splitProjectSpec.Trim())
	}
}
if ($Help) { $arguments += "--help" }
if ($Execute) { $arguments += "--execute" }
if ($Update) { $arguments += "--update" }
if ($Smoke) { $arguments += "--smoke" }
if ($Finalize) { $arguments += "--finalize" }
if ($All) { $arguments += "--all" }
if ($StopOnFailure) { $arguments += "--stop-on-failure" }
if ($Json) { $arguments += "--json" }

& $python @arguments
if ($LASTEXITCODE -ne 0) {
	throw "pipeline_sweep failed with exit code $LASTEXITCODE"
}
