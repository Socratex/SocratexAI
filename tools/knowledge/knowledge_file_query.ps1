param(
	[string[]]$Tags = @(),
	[ValidateSet("all", "any")]
	[string]$Match = "all",
	[string]$Type = "",
	[switch]$LoadAtStart,
	[string]$SourcePath = "",
	[string]$DocumentPath = "",
	[string]$Name = "",
	[ValidateSet("markdown", "json")]
	[string]$Format = "markdown"
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$script = Join-Path $PSScriptRoot "knowledge_file_select.ps1"
& powershell -NoProfile -ExecutionPolicy Bypass -File $script -Tags $Tags -Match $Match -Type $Type -LoadAtStart:$LoadAtStart -SourcePath $SourcePath -DocumentPath $DocumentPath -Name $Name -Format $Format
if ($LASTEXITCODE -ne 0) {
	exit $LASTEXITCODE
}
