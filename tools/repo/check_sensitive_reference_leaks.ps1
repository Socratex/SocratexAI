param(
    [string]$Root,
    [int]$MaxFindings = 200
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

if ([string]::IsNullOrWhiteSpace($Root)) {
    $Root = Join-Path $PSScriptRoot "..\.."
}
$repoRoot = Resolve-Path -LiteralPath $Root
$allowedIdentityFiles = @("LICENSE", "LICENCE")
$violations = [System.Collections.Generic.List[object]]::new()

function ConvertTo-RepoRelativePath {
    param([string]$Path)

    $relative = [System.IO.Path]::GetRelativePath($repoRoot, $Path)
    return ($relative -replace "\\", "/")
}

function Test-SkippedPath {
    param([string]$RelativePath)

    return $RelativePath -eq ".git" -or $RelativePath.StartsWith(".git/", [System.StringComparison]::Ordinal)
}

function New-Rule {
    param(
        [string]$Id,
        [string]$Pattern,
        [string[]]$AllowedBasenames = @()
    )

    return [pscustomobject]@{
        Id = $Id
        Regex = [regex]::new($Pattern, [System.Text.RegularExpressions.RegexOptions]::IgnoreCase -bor [System.Text.RegularExpressions.RegexOptions]::CultureInvariant)
        AllowedBasenames = $AllowedBasenames
    }
}

function Get-LineNumber {
    param(
        [string]$Text,
        [int]$Index
    )

    if ($Index -le 0) {
        return 1
    }
    $prefix = $Text.Substring(0, $Index)
    return (($prefix.ToCharArray() | Where-Object { $_ -eq "`n" }).Count + 1)
}

function Read-FileText {
    param([string]$Path)

    $bytes = [System.IO.File]::ReadAllBytes($Path)
    return [System.Text.Encoding]::UTF8.GetString($bytes)
}

$rules = @(
    (New-Rule -Id "private-project-a" -Pattern ("Rift" + "bound[\s_-]*" + "Van" + "guard")),
    (New-Rule -Id "private-project-b" -Pattern ("Om" + "ega")),
    (New-Rule -Id "private-project-b-legacy-path" -Pattern ("v3[\s_-]*" + "om" + "ega")),
    (New-Rule -Id "external-private-domain" -Pattern ("plan[.]com(?![A-Za-z0-9_])")),
    (New-Rule -Id "private-identity" -Pattern ("micha[l" + [char]0x0142 + "]|jasi[n" + [char]0x0144 + "]ski") -AllowedBasenames $allowedIdentityFiles)
)

Write-Host "==> sensitive reference leak smoke test"
Write-Host "Root: $repoRoot"

$files = @(Get-ChildItem -LiteralPath $repoRoot -Recurse -Force -File | ForEach-Object {
    $relative = ConvertTo-RepoRelativePath -Path $_.FullName
    if (-not (Test-SkippedPath -RelativePath $relative)) {
        $_
    }
})

foreach ($file in $files) {
    $relativePath = ConvertTo-RepoRelativePath -Path $file.FullName
    $basename = [System.IO.Path]::GetFileName($file.FullName)
    $text = Read-FileText -Path $file.FullName

    foreach ($rule in $rules) {
        if ($rule.AllowedBasenames.Count -gt 0 -and $rule.AllowedBasenames -contains $basename) {
            continue
        }

        foreach ($match in $rule.Regex.Matches($text)) {
            $violations.Add([pscustomobject]@{
                Path = $relativePath
                Line = Get-LineNumber -Text $text -Index $match.Index
                Rule = $rule.Id
                Match = $match.Value
            }) | Out-Null

            if ($violations.Count -ge $MaxFindings) {
                break
            }
        }
        if ($violations.Count -ge $MaxFindings) {
            break
        }
    }
    if ($violations.Count -ge $MaxFindings) {
        break
    }
}

if ($violations.Count -gt 0) {
    Write-Host ""
    Write-Host "FAIL: found $($violations.Count) sensitive reference leak(s)."
    foreach ($violation in $violations) {
        Write-Host ("{0}:{1}: {2}: {3}" -f $violation.Path, $violation.Line, $violation.Rule, $violation.Match)
    }
    if ($violations.Count -ge $MaxFindings) {
        Write-Host "Output stopped at MaxFindings=$MaxFindings."
    }
    exit 1
}

Write-Host "OK: no sensitive reference leaks found."
