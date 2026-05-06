param(
    [Parameter(Mandatory = $true)]
    [string]$Operation,
    [string]$ParametersJson = "",
    [string]$ParametersJsonFile = "",
    [ValidateSet("json", "text")]
    [string]$OutputMode = "json",
    [string]$ErrorLogPath = "",
    [switch]$NoErrorLog
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$repoRoot = Resolve-Path -LiteralPath (Join-Path $PSScriptRoot "..\..")
$scriptsCatalogPath = Join-Path $repoRoot "SCRIPTS.json"
$errorLogger = Join-Path $PSScriptRoot "tool_error_log.ps1"

function ConvertTo-Hashtable {
    param([object]$Value)

    if ($null -eq $Value) {
        return $null
    }
    if ($Value -is [System.Management.Automation.PSCustomObject]) {
        $table = [ordered]@{}
        foreach ($property in $Value.PSObject.Properties) {
            $table[$property.Name] = ConvertTo-Hashtable -Value $property.Value
        }
        return $table
    }
    if ($Value -is [System.Collections.IEnumerable] -and $Value -isnot [string]) {
        $list = @()
        foreach ($item in $Value) {
            $list += ConvertTo-Hashtable -Value $item
        }
        return $list
    }
    return $Value
}

function ConvertFrom-HandlerJson {
    param(
        [string]$InlineJson,
        [string]$JsonFile
    )

    if ($InlineJson -ne "" -and $JsonFile -ne "") {
        throw "Use only one of -ParametersJson or -ParametersJsonFile."
    }
    if ($JsonFile -ne "") {
        $raw = [System.IO.File]::ReadAllText((Resolve-Path -LiteralPath $JsonFile).Path, [System.Text.UTF8Encoding]::new($false, $true))
    } elseif ($InlineJson -ne "") {
        $raw = $InlineJson
    } else {
        $raw = "{}"
    }
    try {
        return ConvertTo-Hashtable -Value ($raw | ConvertFrom-Json)
    } catch {
        throw "Parameters JSON is invalid: $($_.Exception.Message)"
    }
}

function Normalize-Name {
    param([string]$Value)
    return ($Value.Trim().TrimStart("-") -replace "[^A-Za-z0-9]+", "_").Trim("_").ToLowerInvariant()
}

function Get-ParameterValue {
    param(
        [System.Collections.IDictionary]$Parameters,
        [string]$Name
    )

    $normalized = Normalize-Name -Value $Name
    foreach ($key in $Parameters.Keys) {
        if ((Normalize-Name -Value $key) -eq $normalized) {
            return $Parameters[$key]
        }
    }
    return $null
}

function Set-ParameterValue {
    param(
        [System.Collections.IDictionary]$Parameters,
        [string]$Name,
        [object]$Value
    )

    $normalized = Normalize-Name -Value $Name
    foreach ($key in @($Parameters.Keys)) {
        if ((Normalize-Name -Value $key) -eq $normalized) {
            $Parameters[$key] = $Value
            return
        }
    }
    $Parameters[$Name] = $Value
}

function Test-ValueProvided {
    param([object]$Value)

    if ($null -eq $Value) {
        return $false
    }
    if ($Value -is [string] -and [string]::IsNullOrWhiteSpace($Value)) {
        return $false
    }
    if ($Value -is [System.Collections.ICollection] -and $Value.Count -eq 0) {
        return $false
    }
    return $true
}

function Get-ScriptCatalogEntry {
    param(
        [object]$Catalog,
        [string]$ScriptName
    )

    if ($Catalog.content.PSObject.Properties.Name -contains $ScriptName) {
        return $Catalog.content.PSObject.Properties[$ScriptName].Value
    }
    return $null
}

function ConvertTo-ArgumentList {
    param(
        [System.Collections.IDictionary]$Parameters,
        [string[]]$OrderedNames
    )

    $arguments = @()
    $used = @{}
    foreach ($name in $OrderedNames) {
        $value = Get-ParameterValue -Parameters $Parameters -Name $name
        if (-not (Test-ValueProvided -Value $value)) {
            continue
        }
        $parameterName = "-" + $name.TrimStart("-")
        $used[(Normalize-Name -Value $name)] = $true
        if ($value -is [bool]) {
            if ($value) {
                $arguments += $parameterName
            }
            continue
        }
        $arguments += $parameterName
        if ($value -is [System.Collections.IEnumerable] -and $value -isnot [string]) {
            foreach ($item in $value) {
                $arguments += [string]$item
            }
        } else {
            $arguments += [string]$value
        }
    }

    foreach ($key in $Parameters.Keys) {
        $normalized = Normalize-Name -Value $key
        if ($used.ContainsKey($normalized)) {
            continue
        }
        $value = $Parameters[$key]
        if (-not (Test-ValueProvided -Value $value)) {
            continue
        }
        $parameterName = "-" + $key.TrimStart("-")
        if ($value -is [bool]) {
            if ($value) {
                $arguments += $parameterName
            }
            continue
        }
        $arguments += $parameterName
        if ($value -is [System.Collections.IEnumerable] -and $value -isnot [string]) {
            foreach ($item in $value) {
                $arguments += [string]$item
            }
        } else {
            $arguments += [string]$value
        }
    }
    return $arguments
}

function Write-Envelope {
    param([hashtable]$Envelope)

    if ($OutputMode -eq "json") {
        $Envelope | ConvertTo-Json -Depth 16
        return
    }
    if ($Envelope.ok) {
        "OK: $($Envelope.operation) -> $($Envelope.target_script)"
        if ($Envelope.output.Count -gt 0) {
            $Envelope.output
        }
        return
    }
    "ERROR: $($Envelope.operation)"
    if ($Envelope.error.message -ne "") {
        $Envelope.error.message
    }
    if ($Envelope.logged_error_key -ne "") {
        "logged_error_key: $($Envelope.logged_error_key)"
    }
}

function Invoke-InputErrorLog {
    param(
        [string]$Title,
        [string]$Message,
        [string]$OperationName,
        [string]$ScriptName,
        [System.Collections.IDictionary]$Parameters
    )

    if ($NoErrorLog) {
        return ""
    }
    $details = [ordered]@{
        operation = $OperationName
        target_script = $ScriptName
        parameters = $Parameters
    }
    $detailsJsonFile = [System.IO.Path]::GetTempFileName()
    [System.IO.File]::WriteAllText(
        $detailsJsonFile,
        ([pscustomobject]$details | ConvertTo-Json -Depth 12),
        [System.Text.UTF8Encoding]::new($false)
    )
    $loggerArguments = @(
        "-Title", $Title,
        "-Status", "open",
        "-Tool", "tools/pipeline/tool_handler.ps1",
        "-Failure", $Message,
        "-ObservedError", $Message,
        "-SuspectedContractGap", "tool_handler input validation or alias normalization rejected this invocation before target execution.",
        "-FixTarget", $ScriptName,
        "-DetailsJsonFile", $detailsJsonFile,
        "-Json"
    )
    if ($ErrorLogPath -ne "") {
        $loggerArguments += @("-Path", $ErrorLogPath)
    }
    try {
        $logOutput = & powershell -NoProfile -ExecutionPolicy Bypass -File $errorLogger @loggerArguments
        $logJson = ($logOutput -join "`n") | ConvertFrom-Json
        return [string]$logJson.key
    } catch {
        return ""
    } finally {
        if (Test-Path -LiteralPath $detailsJsonFile) {
            Remove-Item -LiteralPath $detailsJsonFile -Force
        }
    }
}

$operationKey = Normalize-Name -Value $Operation
$operationMap = @{
    "read_compiled_context" = @{ script = "read_compiled_context.ps1"; path = "tools\pipeline\read_compiled_context.ps1" }
    "compiled_context" = @{ script = "read_compiled_context.ps1"; path = "tools\pipeline\read_compiled_context.ps1" }
    "context_read" = @{ script = "read_compiled_context.ps1"; path = "tools\pipeline\read_compiled_context.ps1" }
    "doc_keys" = @{ script = "list_document_keys.ps1"; path = "tools\documents\list_document_keys.ps1" }
    "document_keys" = @{ script = "list_document_keys.ps1"; path = "tools\documents\list_document_keys.ps1" }
    "doc_read" = @{ script = "read_document_item.ps1"; path = "tools\documents\read_document_item.ps1" }
    "document_read" = @{ script = "read_document_item.ps1"; path = "tools\documents\read_document_item.ps1" }
    "doc_item_insert" = @{ script = "insert_document_item.ps1"; path = "tools\documents\insert_document_item.ps1" }
    "document_item_insert" = @{ script = "insert_document_item.ps1"; path = "tools\documents\insert_document_item.ps1" }
    "json_item_insert" = @{ script = "json_item_insert.ps1"; path = "tools\documents\json_item_insert.ps1" }
    "json_item_set" = @{ script = "json_item_set.ps1"; path = "tools\documents\json_item_set.ps1" }
    "tool_error_log" = @{ script = "tool_error_log.ps1"; path = "tools\pipeline\tool_error_log.ps1" }
}

$parameters = [ordered]@{}
$envelope = [ordered]@{
    ok = $false
    operation = $Operation
    normalized_operation = $operationKey
    target_script = ""
    target_path = ""
    normalized_parameters = @{}
    command = @()
    exit_code = $null
    output = @()
    error = [ordered]@{
        type = ""
        message = ""
    }
    logged_error_key = ""
}

try {
    $parameters = ConvertFrom-HandlerJson -InlineJson $ParametersJson -JsonFile $ParametersJsonFile
    if (-not $operationMap.ContainsKey($operationKey)) {
        $message = "Unknown tool operation '$Operation'."
        $loggedKey = Invoke-InputErrorLog -Title "Tool Handler Unknown Operation" -Message $message -OperationName $Operation -ScriptName "" -Parameters $parameters
        $envelope.error.type = "unknown_operation"
        $envelope.error.message = $message
        $envelope.logged_error_key = $loggedKey
        Write-Envelope -Envelope $envelope
        exit 2
    }

    $target = $operationMap[$operationKey]
    $scriptName = $target.script
    $scriptPath = Join-Path $repoRoot $target.path
    $envelope.target_script = $scriptName
    $envelope.target_path = $scriptPath

    if ($scriptName -eq "read_compiled_context.ps1") {
        $document = Get-ParameterValue -Parameters $parameters -Name "Document"
        if (Test-ValueProvided -Value $document) {
            $documentAliases = @{
                "scripts" = "SCRIPTS.json"
                "script" = "SCRIPTS.json"
                "commands" = "COMMANDS.json"
                "command" = "COMMANDS.json"
                "flows" = "FLOWS.json"
                "flow" = "FLOWS.json"
                "docs" = "DOCS.json"
                "workflow" = "workflow"
                "rules" = "rules"
                "entrypoint" = "entrypoint"
                "bootstrap" = "bootstrap"
                "engineering" = "engineering"
            }
            $documentKey = ([string]$document).Trim().ToLowerInvariant()
            if ($documentAliases.ContainsKey($documentKey)) {
                Set-ParameterValue -Parameters $parameters -Name "Document" -Value $documentAliases[$documentKey]
            }
        }
    }

    $catalog = Get-Content -LiteralPath $scriptsCatalogPath -Raw | ConvertFrom-Json
    $scriptEntry = Get-ScriptCatalogEntry -Catalog $catalog -ScriptName $scriptName
    $required = @()
    $optional = @()
    if ($null -ne $scriptEntry -and $scriptEntry.PSObject.Properties.Name -contains "input") {
        if ($scriptEntry.input.PSObject.Properties.Name -contains "required") { $required = @($scriptEntry.input.required) }
        if ($scriptEntry.input.PSObject.Properties.Name -contains "optional") { $optional = @($scriptEntry.input.optional) }
    }

    if ($required.Count -gt 0 -or $optional.Count -gt 0) {
        $allowed = @{}
        foreach ($name in ($required + $optional)) {
            $allowed[(Normalize-Name -Value $name)] = $true
        }
        foreach ($name in $required) {
            $value = Get-ParameterValue -Parameters $parameters -Name $name
            if (-not (Test-ValueProvided -Value $value)) {
                $message = "Missing required parameter '$name' for $scriptName."
                $loggedKey = Invoke-InputErrorLog -Title "Tool Handler Missing Required Parameter" -Message $message -OperationName $Operation -ScriptName $scriptName -Parameters $parameters
                $envelope.normalized_parameters = $parameters
                $envelope.error.type = "input_validation"
                $envelope.error.message = $message
                $envelope.logged_error_key = $loggedKey
                Write-Envelope -Envelope $envelope
                exit 2
            }
        }
        foreach ($key in $parameters.Keys) {
            $normalized = Normalize-Name -Value $key
            if (-not $allowed.ContainsKey($normalized)) {
                $message = "Unknown parameter '$key' for $scriptName."
                $loggedKey = Invoke-InputErrorLog -Title "Tool Handler Unknown Parameter" -Message $message -OperationName $Operation -ScriptName $scriptName -Parameters $parameters
                $envelope.normalized_parameters = $parameters
                $envelope.error.type = "input_validation"
                $envelope.error.message = $message
                $envelope.logged_error_key = $loggedKey
                Write-Envelope -Envelope $envelope
                exit 2
            }
        }
    }

    $orderedNames = @($required + $optional)
    $arguments = ConvertTo-ArgumentList -Parameters $parameters -OrderedNames $orderedNames
    $envelope.normalized_parameters = $parameters
    $envelope.command = @("powershell", "-NoProfile", "-ExecutionPolicy", "Bypass", "-File", $scriptPath) + $arguments

    $rawOutput = & powershell -NoProfile -ExecutionPolicy Bypass -File $scriptPath @arguments 2>&1
    $exitCode = $LASTEXITCODE
    if ($null -eq $exitCode) {
        $exitCode = 0
    }
    $envelope.exit_code = $exitCode
    $envelope.output = @($rawOutput | ForEach-Object { [string]$_ })
    if ($exitCode -ne 0) {
        $envelope.error.type = "target_execution"
        $envelope.error.message = "Target script exited with code $exitCode."
        Write-Envelope -Envelope $envelope
        exit $exitCode
    }
    $envelope.ok = $true
    Write-Envelope -Envelope $envelope
} catch {
    $message = $_.Exception.Message
    $loggedKey = Invoke-InputErrorLog -Title "Tool Handler Invocation Error" -Message $message -OperationName $Operation -ScriptName $envelope.target_script -Parameters $parameters
    $envelope.error.type = "handler_exception"
    $envelope.error.message = $message
    $envelope.logged_error_key = $loggedKey
    Write-Envelope -Envelope $envelope
    exit 1
}
