Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

function Get-SocratexOptionalCommandSource {
	param([string]$Name)

	$command = Get-Command $Name -ErrorAction SilentlyContinue
	if ($null -eq $command) {
		return ""
	}
	if ($command.PSObject.Properties.Name -contains "Source") {
		return [string]$command.Source
	}
	if ($command.PSObject.Properties.Name -contains "Path") {
		return [string]$command.Path
	}
	return ""
}

function Test-SocratexExecutable {
	param(
		[string]$Path,
		[string[]]$Arguments = @("--version")
	)

	if ([string]::IsNullOrWhiteSpace($Path)) {
		return $false
	}

	try {
		& $Path @Arguments *> $null
		return $LASTEXITCODE -eq 0
	} catch {
		return $false
	}
}

function Test-SocratexPythonCandidate {
	param([string]$Path)

	if ([string]::IsNullOrWhiteSpace($Path)) {
		return $false
	}

	try {
		$output = @(& $Path -c "import sys; print(sys.version_info[0])" 2>$null)
		if ($LASTEXITCODE -ne 0 -or $output.Count -eq 0) {
			return $false
		}
		return ([string]$output[0]).Trim() -eq "3"
	} catch {
		return $false
	}
}

function Resolve-SocratexRepoRoot {
	param([string]$SearchRoot = $PSScriptRoot)

	$current = Resolve-Path -LiteralPath $SearchRoot
	while ($null -ne $current) {
		$candidate = [string]$current
		if (
			(Test-Path -LiteralPath (Join-Path $candidate "tools") -PathType Container) -or
			(Test-Path -LiteralPath (Join-Path $candidate "Tools") -PathType Container)
		) {
			return $candidate
		}
		$parent = Split-Path -Parent $candidate
		if ([string]::IsNullOrWhiteSpace($parent) -or $parent -eq $candidate) {
			break
		}
		$current = Resolve-Path -LiteralPath $parent
	}

	throw "Could not resolve Socratex repository root from: $SearchRoot"
}

function Test-SocratexWindowsRuntime {
	return [System.Runtime.InteropServices.RuntimeInformation]::IsOSPlatform(
		[System.Runtime.InteropServices.OSPlatform]::Windows
	)
}

function Resolve-SocratexPython {
	param([string]$SearchRoot = $PSScriptRoot)

	$repoRoot = Resolve-SocratexRepoRoot -SearchRoot $SearchRoot
	$bundledPythonCandidates = @(
		(Join-Path $repoRoot "Tools\Python312\python.exe"),
		(Join-Path $repoRoot "tools\Python312\python.exe")
	)
	$candidates = [System.Collections.Generic.List[string]]::new()

	if (-not [string]::IsNullOrWhiteSpace($env:SOCRATEX_PYTHON)) {
		$candidates.Add($env:SOCRATEX_PYTHON)
	}
	if (-not [string]::IsNullOrWhiteSpace($env:RIFTBOUND_PYTHON)) {
		$candidates.Add($env:RIFTBOUND_PYTHON)
	}
	if (Test-SocratexWindowsRuntime) {
		foreach ($bundledPython in $bundledPythonCandidates) {
			if (Test-Path -LiteralPath $bundledPython -PathType Leaf) {
				$candidates.Add($bundledPython)
			}
		}
	}

	foreach ($name in @("python3", "python")) {
		$source = Get-SocratexOptionalCommandSource -Name $name
		if (-not [string]::IsNullOrWhiteSpace($source)) {
			$candidates.Add($source)
		}
	}

	foreach ($candidate in @($candidates | Select-Object -Unique)) {
		if (Test-SocratexPythonCandidate -Path $candidate) {
			return $candidate
		}
	}

	throw "Python 3 is required, but no usable interpreter was found. Set SOCRATEX_PYTHON or install python3."
}

function Resolve-SocratexPowerShell {
	$candidates = [System.Collections.Generic.List[string]]::new()

	if (-not [string]::IsNullOrWhiteSpace($env:SOCRATEX_PWSH)) {
		$candidates.Add($env:SOCRATEX_PWSH)
	}
	foreach ($name in @("pwsh", "powershell", "powershell.exe")) {
		$source = Get-SocratexOptionalCommandSource -Name $name
		if (-not [string]::IsNullOrWhiteSpace($source)) {
			$candidates.Add($source)
		}
	}

	foreach ($candidate in @($candidates | Select-Object -Unique)) {
		if (Test-SocratexExecutable -Path $candidate -Arguments @("-NoLogo", "-NoProfile", "-Command", "`$PSVersionTable.PSVersion.ToString()")) {
			return $candidate
		}
	}

	throw "PowerShell is required, but no usable pwsh/powershell executable was found. Set SOCRATEX_PWSH or install PowerShell 7+."
}

function Resolve-ProjectPython {
	param([string]$SearchRoot = $PSScriptRoot)

	return Resolve-SocratexPython -SearchRoot $SearchRoot
}
