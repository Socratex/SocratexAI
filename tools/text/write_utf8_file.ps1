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
	. (Join-Path $PSScriptRoot "utf8_file_helpers.ps1")
	$lines = [System.Collections.Generic.List[string]]::new()
}

process {
	foreach ($entry in $Value) {
		$lines.Add($entry)
	}
}

end {
	Write-Utf8File -Path $Path -Value $lines -NoNewline:$NoNewline -LineEnding $LineEnding
}
