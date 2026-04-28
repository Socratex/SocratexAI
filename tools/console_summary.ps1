param(
	[string]$ConsoleLogPath = "",
	[string]$OutputPath = ""
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$repoRoot = Resolve-Path -LiteralPath (Join-Path $PSScriptRoot "..")
if ([string]::IsNullOrWhiteSpace($ConsoleLogPath)) {
	$ConsoleLogPath = Join-Path $repoRoot "CONSOLE-LOG"
}
if ([string]::IsNullOrWhiteSpace($OutputPath)) {
	$OutputPath = Join-Path $repoRoot "CONSOLE-LOG-SUMMARY"
}

$lines = [System.Collections.Generic.List[string]]::new()
$lines.Add("# Console Log Summary")
$lines.Add("Generated: $(Get-Date -Format "yyyy-MM-dd HH:mm:ss zzz")")
$lines.Add("Source: $ConsoleLogPath")

if (-not (Test-Path -LiteralPath $ConsoleLogPath)) {
	$lines.Add("")
	$lines.Add("CONSOLE-LOG is missing.")
	Set-Content -LiteralPath $OutputPath -Value $lines -Encoding UTF8
	Write-Host "Console summary written to: $OutputPath"
	return
}

$content = @(Get-Content -LiteralPath $ConsoleLogPath)
$errorMatches = @($content | Where-Object { $_ -match "ERROR|SCRIPT ERROR" })
$warningMatches = @($content | Where-Object { $_ -match "WARNING" })

$lines.Add("")
$lines.Add("Errors: $($errorMatches.Count)")
$lines.Add("Warnings: $($warningMatches.Count)")

$startupLines = @($content | Where-Object { $_ -match "Godot Engine|Vulkan " } | Select-Object -Last 6)
$lines.Add("")
$lines.Add("## Latest Startup Lines")
if ($startupLines.Count -eq 0) {
	$lines.Add("(none)")
} else {
	foreach ($line in $startupLines) {
		$lines.Add([string]$line)
	}
}

$lines.Add("")
$lines.Add("## Unique Error/Warning Lines")
$uniqueProblemLines = @($content |
	Where-Object { $_ -match "ERROR|SCRIPT ERROR|WARNING" } |
	Sort-Object -Unique |
	Select-Object -First 40)
if ($uniqueProblemLines.Count -eq 0) {
	$lines.Add("(none)")
} else {
	foreach ($line in $uniqueProblemLines) {
		$lines.Add([string]$line)
	}
}

$lastBacktraceIndex = -1
for ($index = $content.Count - 1; $index -ge 0; $index--) {
	if ([string]$content[$index] -match "GDScript backtrace") {
		$lastBacktraceIndex = $index
		break
	}
}

$lines.Add("")
$lines.Add("## Latest GDScript Backtrace")
if ($lastBacktraceIndex -lt 0) {
	$lines.Add("(none)")
} else {
	$endIndex = [Math]::Min($content.Count - 1, $lastBacktraceIndex + 24)
	for ($index = $lastBacktraceIndex; $index -le $endIndex; $index++) {
		$lines.Add([string]$content[$index])
	}
}

Set-Content -LiteralPath $OutputPath -Value $lines -Encoding UTF8
Write-Host "Console summary written to: $OutputPath"
