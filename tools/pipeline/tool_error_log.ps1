param(
    [string]$Path = "",
    [string]$Key = "",
    [string]$Title = "",
    [string]$Status = "open",
    [string]$Tool = "",
    [string]$Failure = "",
    [string]$FailingCommandShape = "",
    [string]$ObservedError = "",
    [string]$SuspectedContractGap = "",
    [string]$FixTarget = "",
    [string]$DetailsJson = "",
    [string]$DetailsJsonFile = "",
    [string]$ObservedAt = "",
    [switch]$Json
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$packageRoot = Resolve-Path -LiteralPath (Join-Path $PSScriptRoot "..\..")
$workspaceRoot = $packageRoot
$packageLeaf = Split-Path -Leaf $packageRoot
if ($packageLeaf -eq "SocratexAI") {
    $parentRoot = Split-Path -Parent $packageRoot
    if (Test-Path -LiteralPath (Join-Path $parentRoot "docs-tech")) {
        $workspaceRoot = Resolve-Path -LiteralPath $parentRoot
    }
}

if ([string]::IsNullOrWhiteSpace($Path)) {
    $Path = Join-Path $workspaceRoot "docs-tech\TOOL-ERRORS.json"
}

function New-Slug {
    param([string]$Value)

    $slug = $Value.Trim().ToLowerInvariant()
    $slug = [regex]::Replace($slug, "[^a-z0-9]+", "_").Trim("_")
    if ([string]::IsNullOrWhiteSpace($slug)) {
        return "tool_error"
    }
    return $slug
}

function New-EmptyToolErrorDocument {
    return [ordered]@{
        index = @()
        content = [ordered]@{}
        metadata = [ordered]@{
            document = [ordered]@{
                title = "Tool Errors"
                type = "tool_error_registry"
                language = "en"
            }
            purpose = "Records repeatable repository tool invocation, input, result, quoting, path, encoding, and contract failures so the owning script or script catalog can be hardened instead of relying on manual memory."
        }
    }
}

function Get-UniqueKey {
    param(
        [string]$RequestedKey,
        [string]$BaseTitle,
        [object]$Document
    )

    if (-not [string]::IsNullOrWhiteSpace($RequestedKey)) {
        $baseKey = New-Slug -Value $RequestedKey
    } elseif (-not [string]::IsNullOrWhiteSpace($BaseTitle)) {
        $baseKey = New-Slug -Value $BaseTitle
    } else {
        $baseKey = "tool_error"
    }

    $existingKeys = @()
    foreach ($property in @($Document.content.PSObject.Properties)) {
        $existingKeys += [string]$property.Name
    }

    $key = $baseKey
    $suffix = 1
    while ($existingKeys -contains $key) {
        $key = "$baseKey`_$suffix"
        $suffix++
    }
    return $key
}

function Ensure-ToolErrorDocument {
    param([string]$TargetPath)

    $parent = Split-Path -Parent $TargetPath
    if (-not (Test-Path -LiteralPath $parent)) {
        New-Item -ItemType Directory -Force -Path $parent | Out-Null
    }

    if (-not (Test-Path -LiteralPath $TargetPath -PathType Leaf)) {
        $empty = New-EmptyToolErrorDocument
        [System.IO.File]::WriteAllText(
            $TargetPath,
            ($empty | ConvertTo-Json -Depth 20),
            [System.Text.UTF8Encoding]::new($false)
        )
    }
}

if ([string]::IsNullOrWhiteSpace($ObservedAt)) {
    $ObservedAt = (Get-Date).ToString("yyyy-MM-dd HH:mm:ss zzz")
}
if ([string]::IsNullOrWhiteSpace($Title)) {
    $Title = "Tool Error"
}
if ($DetailsJson -ne "" -and $DetailsJsonFile -ne "") {
    throw "Use only one of -DetailsJson or -DetailsJsonFile."
}
if ($DetailsJsonFile -ne "") {
    $DetailsJson = [System.IO.File]::ReadAllText((Resolve-Path -LiteralPath $DetailsJsonFile).Path, [System.Text.UTF8Encoding]::new($false, $true))
}

Ensure-ToolErrorDocument -TargetPath $Path
$resolvedPath = (Resolve-Path -LiteralPath $Path).Path
$document = Get-Content -LiteralPath $resolvedPath -Raw | ConvertFrom-Json
$entryKey = Get-UniqueKey -RequestedKey $Key -BaseTitle $Title -Document $document

$entry = [ordered]@{
    title = $Title
    status = $Status
    observed_at = $ObservedAt
}
if ($Tool -ne "") { $entry["tool"] = $Tool }
if ($Failure -ne "") { $entry["failure"] = $Failure }
if ($FailingCommandShape -ne "") { $entry["failing_command_shape"] = $FailingCommandShape }
if ($ObservedError -ne "") { $entry["observed_error"] = $ObservedError }
if ($SuspectedContractGap -ne "") { $entry["suspected_contract_gap"] = $SuspectedContractGap }
if ($FixTarget -ne "") { $entry["fix_target"] = $FixTarget }
if ($DetailsJson -ne "") {
    try {
        $entry["details"] = $DetailsJson | ConvertFrom-Json
    } catch {
        $entry["details"] = $DetailsJson
    }
}

$tempJsonFile = [System.IO.Path]::GetTempFileName()
try {
    [System.IO.File]::WriteAllText(
        $tempJsonFile,
        ($entry | ConvertTo-Json -Depth 20),
        [System.Text.UTF8Encoding]::new($false)
    )
    $jsonItemInsert = Join-Path $packageRoot "tools\documents\json_item_insert.ps1"
    $appendOutput = & powershell -NoProfile -ExecutionPolicy Bypass -File $jsonItemInsert -Path $resolvedPath -Key $entryKey -ValueJsonFile $tempJsonFile 2>&1
    if ($LASTEXITCODE -ne 0) {
        throw "tool_error_log failed to append '$entryKey' with exit code $LASTEXITCODE`: $($appendOutput -join "`n")"
    }
} finally {
    if (Test-Path -LiteralPath $tempJsonFile) {
        Remove-Item -LiteralPath $tempJsonFile -Force
    }
}

$result = [ordered]@{
    ok = $true
    key = $entryKey
    path = $resolvedPath
}
if ($Json) {
    $result | ConvertTo-Json -Depth 6
    return
}

"OK: logged $entryKey"
