param(
	[Parameter(Mandatory = $true)]
	[string]$Path,
	[Parameter(ValueFromPipeline = $true)]
	[AllowEmptyString()]
	[string[]]$Value = @(),
	[switch]$NoNewline,
	[ValidateSet("Preserve", "LF", "CRLF")]
	[string]$LineEnding = "LF"
)

begin {
	Set-StrictMode -Version Latest
	$ErrorActionPreference = "Stop"
	. (Join-Path $PSScriptRoot "..\pipeline\resolve_tool_runtime.ps1")
	$python = Resolve-SocratexPython -SearchRoot $PSScriptRoot
	$script = Join-Path $PSScriptRoot "write_utf8_file.py"
	$lines = [System.Collections.Generic.List[string]]::new()
}

process {
	foreach ($entry in $Value) {
		$lines.Add($entry)
	}
}

end {
	$arguments = @(
		$script,
		"--path",
		$Path,
		"--line-ending",
		$LineEnding
	)
	if ($NoNewline) {
		$arguments += "--no-newline"
	}
	if ($lines.Count -eq 0) {
		$arguments += @("--value", "")
	} else {
		foreach ($line in $lines) {
			$arguments += @("--value", $line)
		}
	}

	& $python -B @arguments
	if ($LASTEXITCODE -ne 0) {
		throw "write_utf8_file failed with exit code $LASTEXITCODE"
	}
}
