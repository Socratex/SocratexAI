param(
	[Parameter(Mandatory = $true)]
	[string]$Path,
	[Parameter(Mandatory = $true)]
	[string]$Key,
	[string]$Title = "",
	[string]$Content = "",
	[string]$ContentFile = "",
	[string]$ItemFile = "",
	[ValidateSet("start", "end")]
	[string]$Position = "end",
	[string]$Before = "",
	[string]$After = "",
	[switch]$AllowEmpty,
	[switch]$Replace,
	[switch]$NoPostEdit
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

if ([System.IO.Path]::GetExtension($Path).ToLowerInvariant() -eq ".json") {
	$jsonItemInsert = Join-Path $PSScriptRoot "json_item_insert.ps1"
	$jsonItemSet = Join-Path $PSScriptRoot "json_item_set.ps1"
	$jsonPosition = $Position
	$jsonReference = ""
	if ($Replace) {
		# Position is irrelevant for replacement; keep the existing key location.
	} elseif ($Before -ne "") {
		$jsonPosition = "before"
		$jsonReference = $Before
	} elseif ($After -ne "") {
		$jsonPosition = "after"
		$jsonReference = $After
	}

	if ($ItemFile -ne "") {
		if ($Replace) {
			& $jsonItemSet -Path $Path -Key $Key -ValueJsonFile $ItemFile
		} elseif ($jsonReference -ne "") {
			& $jsonItemInsert -Path $Path -Key $Key -Position $jsonPosition -Reference $jsonReference -ValueJsonFile $ItemFile
		} else {
			& $jsonItemInsert -Path $Path -Key $Key -Position $jsonPosition -ValueJsonFile $ItemFile
		}
		if ($LASTEXITCODE -ne 0) {
			throw "JSON item edit failed with exit code $LASTEXITCODE"
		}
		return
	}

	$contentValue = $Content
	if ($ContentFile -ne "") {
		$contentValue = [System.IO.File]::ReadAllText(
			(Resolve-Path -LiteralPath $ContentFile).Path,
			[System.Text.UTF8Encoding]::new($false, $true)
		)
	}
	if ($Title -eq "" -and $contentValue -eq "" -and -not $AllowEmpty) {
		throw "JSON item insert requires -Title, -Content, -ContentFile, -ItemFile, or -AllowEmpty."
	}

	$itemPayload = [ordered]@{}
	if ($Title -ne "") {
		$itemPayload["title"] = $Title
	}
	if ($contentValue -ne "" -or $AllowEmpty) {
		$itemPayload["content"] = $contentValue
	}

	$tempJsonFile = [System.IO.Path]::GetTempFileName()
	try {
		[System.IO.File]::WriteAllText(
			$tempJsonFile,
			($itemPayload | ConvertTo-Json -Depth 20),
			[System.Text.UTF8Encoding]::new($false)
		)
		if ($Replace) {
			& $jsonItemSet -Path $Path -Key $Key -ValueJsonFile $tempJsonFile
		} elseif ($jsonReference -ne "") {
			& $jsonItemInsert -Path $Path -Key $Key -Position $jsonPosition -Reference $jsonReference -ValueJsonFile $tempJsonFile
		} else {
			& $jsonItemInsert -Path $Path -Key $Key -Position $jsonPosition -ValueJsonFile $tempJsonFile
		}
		if ($LASTEXITCODE -ne 0) {
			throw "JSON item edit failed with exit code $LASTEXITCODE"
		}
	} finally {
		if (Test-Path -LiteralPath $tempJsonFile) {
			Remove-Item -LiteralPath $tempJsonFile -Force
		}
	}
	return
}

. (Join-Path $PSScriptRoot "..\pipeline\resolve_tool_runtime.ps1")
$python = Resolve-SocratexPython -SearchRoot $PSScriptRoot

$script = Join-Path $PSScriptRoot "document_item_edit_engine.py"
$arguments = @($script, "insert", $Path, $Key, "--position", $Position)
if ($Title -ne "") { $arguments += @("--title", $Title) }
if ($Content -ne "") { $arguments += @("--content", $Content) }
if ($ContentFile -ne "") { $arguments += @("--content-file", $ContentFile) }
if ($ItemFile -ne "") { $arguments += @("--item-file", $ItemFile) }
if ($Before -ne "") { $arguments += @("--before", $Before) }
if ($After -ne "") { $arguments += @("--after", $After) }
if ($AllowEmpty) { $arguments += "--allow-empty" }
if ($Replace) { $arguments += "--replace" }

& $python @arguments
if ($LASTEXITCODE -ne 0) {
	throw "insert_document_item failed with exit code $LASTEXITCODE"
}

if (-not $NoPostEdit) {
	& powershell -NoProfile -ExecutionPolicy Bypass -File (Join-Path $PSScriptRoot "run_document_post_edit_checks.ps1") -Paths $Path
	if ($LASTEXITCODE -ne 0) {
		throw "insert_document_item post-edit pipeline failed with exit code $LASTEXITCODE"
	}
}
