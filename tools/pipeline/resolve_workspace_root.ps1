param(
	[string]$StartPath = ".",
	[string]$WorkspaceRoot = "",
	[switch]$Json
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

function Resolve-ExistingPath {
	param([string]$Path)

	if ([string]::IsNullOrWhiteSpace($Path)) {
		return $null
	}
	try {
		return (Resolve-Path -LiteralPath $Path -ErrorAction Stop).Path
	} catch {
		return $null
	}
}

function Read-WorkspaceConfig {
	param([string]$Path)

	try {
		return (Get-Content -Raw -LiteralPath $Path -Encoding UTF8 | ConvertFrom-Json)
	} catch {
		throw "workspace.json is not valid JSON: $Path"
	}
}

function Resolve-WorkspaceRelativePath {
	param(
		[string]$Root,
		[object]$Config,
		[string]$PropertyName,
		[string]$DefaultValue
	)

	$value = $DefaultValue
	if ($null -ne $Config -and $Config.PSObject.Properties.Name.Contains($PropertyName)) {
		$configured = [string]$Config.$PropertyName
		if (-not [string]::IsNullOrWhiteSpace($configured)) {
			$value = $configured
		}
	}

	if ([System.IO.Path]::IsPathRooted($value)) {
		return [System.IO.Path]::GetFullPath($value)
	}
	return [System.IO.Path]::GetFullPath((Join-Path $Root $value))
}

function Test-WorkspaceCandidate {
	param(
		[string]$Root,
		[string]$ConfigPath
	)

	if (-not (Test-Path -LiteralPath $ConfigPath -PathType Leaf)) {
		return $false
	}

	$config = Read-WorkspaceConfig -Path $ConfigPath
	$socratexAiPath = Resolve-WorkspaceRelativePath -Root $Root -Config $config -PropertyName "socratex_ai_dir" -DefaultValue "SocratexAI"
	return (Test-Path -LiteralPath $socratexAiPath -PathType Container)
}

function Find-WorkspaceRoot {
	param([string]$Path)

	$resolvedStart = Resolve-ExistingPath -Path $Path
	if ($null -eq $resolvedStart) {
		$resolvedStart = Resolve-ExistingPath -Path "."
	}
	if ($null -eq $resolvedStart) {
		throw "Cannot resolve workspace search start path: $Path"
	}

	$current = if (Test-Path -LiteralPath $resolvedStart -PathType Leaf) {
		Split-Path -Parent $resolvedStart
	} else {
		$resolvedStart
	}

	while (-not [string]::IsNullOrWhiteSpace($current)) {
		$configPath = Join-Path $current "workspace.json"
		if (Test-WorkspaceCandidate -Root $current -ConfigPath $configPath) {
			return $current
		}

		$parent = Split-Path -Parent $current
		if ([string]::IsNullOrWhiteSpace($parent) -or $parent -eq $current) {
			break
		}
		$current = $parent
	}

	return $null
}

$resolvedRoot = Resolve-ExistingPath -Path $WorkspaceRoot
if ($null -ne $resolvedRoot) {
	$configPath = Join-Path $resolvedRoot "workspace.json"
	if (-not (Test-WorkspaceCandidate -Root $resolvedRoot -ConfigPath $configPath)) {
		throw "Explicit workspace root must contain workspace.json and a SocratexAI directory: $resolvedRoot"
	}
} else {
	$resolvedRoot = Find-WorkspaceRoot -Path $StartPath
}

if ($null -eq $resolvedRoot -and -not [string]::IsNullOrWhiteSpace($env:SOCRATEX_WORKSPACE_ROOT)) {
	$envRoot = Resolve-ExistingPath -Path $env:SOCRATEX_WORKSPACE_ROOT
	if ($null -ne $envRoot) {
		$configPath = Join-Path $envRoot "workspace.json"
		if (Test-WorkspaceCandidate -Root $envRoot -ConfigPath $configPath) {
			$resolvedRoot = $envRoot
		}
	}
}

if ($null -eq $resolvedRoot) {
	$scriptResolved = Resolve-ExistingPath -Path $PSScriptRoot
	if ($null -ne $scriptResolved) {
		$current = $scriptResolved
		while (-not [string]::IsNullOrWhiteSpace($current)) {
			if ((Split-Path -Leaf $current) -eq "SocratexAI") {
				$parent = Split-Path -Parent $current
				if (Test-Path -LiteralPath (Join-Path $parent "SocratexAI") -PathType Container) {
					$resolvedRoot = $parent
				}
				break
			}
			$parent = Split-Path -Parent $current
			if ([string]::IsNullOrWhiteSpace($parent) -or $parent -eq $current) {
				break
			}
			$current = $parent
		}
	}
}

if ($null -eq $resolvedRoot) {
	throw "Could not resolve Socratex workspace root. Put workspace.json next to SocratexAI/ or set SOCRATEX_WORKSPACE_ROOT."
}

$workspaceConfigPath = Join-Path $resolvedRoot "workspace.json"
$workspaceConfig = if (Test-Path -LiteralPath $workspaceConfigPath -PathType Leaf) {
	Read-WorkspaceConfig -Path $workspaceConfigPath
} else {
	[pscustomobject]@{
		schema = "socratex-workspace/v1"
		workspace_name = "inferred"
		socratex_ai_dir = "SocratexAI"
		projects_dir = "."
	}
}

$result = [ordered]@{
	workspace_root = $resolvedRoot
	workspace_config = $workspaceConfigPath
	projects_dir = Resolve-WorkspaceRelativePath -Root $resolvedRoot -Config $workspaceConfig -PropertyName "projects_dir" -DefaultValue "."
	socratex_ai_dir = Resolve-WorkspaceRelativePath -Root $resolvedRoot -Config $workspaceConfig -PropertyName "socratex_ai_dir" -DefaultValue "SocratexAI"
	tools_dir = Resolve-WorkspaceRelativePath -Root $resolvedRoot -Config $workspaceConfig -PropertyName "tools_dir" -DefaultValue "tools"
	archive_dir = Resolve-WorkspaceRelativePath -Root $resolvedRoot -Config $workspaceConfig -PropertyName "archive_dir" -DefaultValue "_archive"
	drive_exports_dir = Resolve-WorkspaceRelativePath -Root $resolvedRoot -Config $workspaceConfig -PropertyName "drive_exports_dir" -DefaultValue "drive-exports"
	google_drive_projects_uri = if ($workspaceConfig.PSObject.Properties.Name.Contains("google_drive_projects_uri")) { [string]$workspaceConfig.google_drive_projects_uri } else { "" }
}

if ($Json) {
	$result | ConvertTo-Json -Depth 6
} else {
	$result.workspace_root
}
