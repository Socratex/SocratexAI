param(
	[string]$ProjectRoot = ".",
	[switch]$Quiet
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$resolvedRoot = (Resolve-Path -LiteralPath $ProjectRoot).Path
$configPath = Join-Path $resolvedRoot ".aiassistant/socratex/PIPELINE-CONFIG.json"

if (-not (Test-Path -LiteralPath $configPath -PathType Leaf)) {
	Write-Error "Project PIPELINE-CONFIG.json not found at: $configPath"
	exit 1
}

$config = Get-Content -Raw -LiteralPath $configPath | ConvertFrom-Json

$reads = @()
if ($config.PSObject.Properties.Name -contains "code_design_required_reads") {
	$reads = @($config.code_design_required_reads)
}

if ($reads.Count -eq 0) {
	if (-not $Quiet) {
		Write-Host "==> project_design_context: no code_design_required_reads declared"
		Write-Host "Project: $resolvedRoot"
		Write-Host "Workspace base rules from knowledge_code_context.ps1 still apply."
	}
	# Write minimal gate so check_task.ps1 sees an explicit no-op
	$gatePath = Join-Path $resolvedRoot "ignored/project_design_context_gate.json"
	$gateDir = Split-Path -Parent $gatePath
	if (-not (Test-Path -LiteralPath $gateDir)) {
		New-Item -ItemType Directory -Path $gateDir | Out-Null
	}
	$emptyGate = [ordered]@{
		schema = 1
		tool = "project_design_context"
		loaded_at = (Get-Date).ToUniversalTime().ToString("o")
		project_root = $resolvedRoot
		repo_head = (git -C $resolvedRoot rev-parse HEAD 2>$null)
		declared_reads = @()
		loaded = @()
		note = "Project declares no code_design_required_reads; workspace base rules apply."
	}
	$utf8NoBom = New-Object System.Text.UTF8Encoding($false)
	[System.IO.File]::WriteAllText($gatePath, ($emptyGate | ConvertTo-Json -Depth 8), $utf8NoBom)
	exit 0
}

if (-not $Quiet) {
	Write-Host "==> project_design_context: loading $($reads.Count) project-specific design files"
	Write-Host "Project: $resolvedRoot"
	Write-Host ""
}

$loaded = @()
$missing = @()
foreach ($rel in $reads) {
	$abs = Join-Path $resolvedRoot $rel
	if (-not (Test-Path -LiteralPath $abs -PathType Leaf)) {
		Write-Warning "Missing required read: $rel"
		$missing += $rel
		continue
	}
	if (-not $Quiet) {
		Write-Host "===== $rel ====="
		Write-Host ""
		Get-Content -LiteralPath $abs -Raw | Write-Output
		Write-Host ""
	}
	$item = Get-Item -LiteralPath $abs
	$loaded += [ordered]@{
		path = $rel
		size_bytes = $item.Length
		modified = $item.LastWriteTimeUtc.ToString("o")
	}
}

# Write gate file
$gatePath = Join-Path $resolvedRoot "ignored/project_design_context_gate.json"
$gateDir = Split-Path -Parent $gatePath
if (-not (Test-Path -LiteralPath $gateDir)) {
	New-Item -ItemType Directory -Path $gateDir | Out-Null
}

$repoHead = $null
try { $repoHead = (git -C $resolvedRoot rev-parse HEAD 2>$null) } catch { }

$gate = [ordered]@{
	schema = 1
	tool = "project_design_context"
	loaded_at = (Get-Date).ToUniversalTime().ToString("o")
	project_root = $resolvedRoot
	repo_head = $repoHead
	declared_reads = @($reads)
	loaded = $loaded
	missing = $missing
	full_set_loaded = ($missing.Count -eq 0)
}
$json = $gate | ConvertTo-Json -Depth 8
$utf8NoBom = New-Object System.Text.UTF8Encoding($false)
[System.IO.File]::WriteAllText($gatePath, $json, $utf8NoBom)

if (-not $Quiet) {
	Write-Host ""
	Write-Host "Gate file written: $gatePath"
	if ($missing.Count -gt 0) {
		Write-Host ""
		Write-Warning "$($missing.Count) declared read(s) missing — gate marked full_set_loaded=false."
		exit 2
	}
}
