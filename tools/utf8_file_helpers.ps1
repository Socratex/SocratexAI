Set-StrictMode -Version Latest

$script:Utf8NoBomEncoding = [System.Text.UTF8Encoding]::new($false)
$script:Utf8StrictEncoding = [System.Text.UTF8Encoding]::new($false, $true)

function ConvertTo-ConfiguredLineEnding {
	param(
		[Parameter(Mandatory = $true)]
		[AllowEmptyString()]
		[string]$Text,
		[ValidateSet("Preserve", "LF", "CRLF")]
		[string]$LineEnding = "LF"
	)

	if ($LineEnding -eq "Preserve") {
		return $Text
	}

	$normalized = $Text -replace "`r`n", "`n"
	$normalized = $normalized -replace "`r", "`n"
	if ($LineEnding -eq "CRLF") {
		return ($normalized -replace "`n", "`r`n")
	}
	return $normalized
}

function ConvertTo-Utf8FileText {
	param(
		[Parameter(Mandatory = $true)]
		[AllowEmptyString()]
		[object]$Value,
		[switch]$NoNewline,
		[ValidateSet("Preserve", "LF", "CRLF")]
		[string]$LineEnding = "LF"
	)

	$text = ""
	if ($Value -is [string]) {
		$text = [string]$Value
	} elseif ($Value -is [System.Collections.IEnumerable]) {
		$parts = [System.Collections.Generic.List[string]]::new()
		foreach ($entry in $Value) {
			$parts.Add([string]$entry)
		}
		$text = $parts -join "`n"
	} else {
		$text = [string]$Value
	}

	$text = ConvertTo-ConfiguredLineEnding -Text $text -LineEnding $LineEnding
	if (-not $NoNewline -and -not $text.EndsWith("`n")) {
		if ($LineEnding -eq "CRLF") {
			$text += "`r`n"
		} else {
			$text += "`n"
		}
	}
	return $text
}

function Read-Utf8File {
	param(
		[Parameter(Mandatory = $true)]
		[string]$Path
	)

	return [System.IO.File]::ReadAllText($Path, $script:Utf8StrictEncoding)
}

function Write-Utf8File {
	param(
		[Parameter(Mandatory = $true)]
		[string]$Path,
		[Parameter(Mandatory = $true)]
		[AllowEmptyString()]
		[object]$Value,
		[switch]$NoNewline,
		[ValidateSet("Preserve", "LF", "CRLF")]
		[string]$LineEnding = "LF"
	)

	$resolvedPath = $Path
	if (-not [System.IO.Path]::IsPathRooted($resolvedPath)) {
		$resolvedPath = Join-Path (Get-Location) $resolvedPath
	}
	$parent = Split-Path -Parent $resolvedPath
	if (-not [string]::IsNullOrWhiteSpace($parent) -and -not (Test-Path -LiteralPath $parent)) {
		New-Item -ItemType Directory -Force -Path $parent | Out-Null
	}

	$text = ConvertTo-Utf8FileText -Value $Value -NoNewline:$NoNewline -LineEnding $LineEnding
	[System.IO.File]::WriteAllText($resolvedPath, $text, $script:Utf8NoBomEncoding)
}
