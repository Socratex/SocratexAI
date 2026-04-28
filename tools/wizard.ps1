param(
    [switch]$DryRun
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

function Ask-Default {
    param(
        [string]$Prompt,
        [string]$Default
    )

    $answer = Read-Host "$Prompt [$Default]"
    if ([string]::IsNullOrWhiteSpace($answer)) {
        return $Default
    }

    return $answer
}

Write-Host "SocratexPipeline first-run wizard"
Write-Host "Answer in your preferred language after choosing the project language."
Write-Host ""

$language = Ask-Default -Prompt "1. Project conversation/status language" -Default "English"
$projectName = Ask-Default -Prompt "2. Project name" -Default "Initialized SocratexPipeline Project"
$kind = Ask-Default -Prompt "3. Project kind: code, generic, personal, creative, mixed" -Default "code"
$packs = Ask-Default -Prompt "4. Active packs, comma-separated" -Default $(if ($kind -eq "code") { "code" } else { "generic" })
$aiMode = Ask-Default -Prompt "5. AI mode: Lite, Standard, Enterprise" -Default "Standard"
$firstTarget = Ask-Default -Prompt "6. First concrete target" -Default "Define the first execution pass"
$optimizeFor = Ask-Default -Prompt "7. Optimize for" -Default "correctness"
$avoid = Ask-Default -Prompt "8. What should the agent avoid" -Default "unbounded scope"
$artifacts = Ask-Default -Prompt "9. Required artifacts after initialization" -Default "default pack artifacts"
$useGit = Ask-Default -Prompt "10. Use Git" -Default "yes"
$external = Ask-Default -Prompt "11. External tools, folders, accounts, or references" -Default "none"
$success = Ask-Default -Prompt "12. Successful first session means" -Default "project initialized and first pass ready"
$aiMayCommit = "no"
$aiMayPush = "no"
$branchWorkflow = "unknown"
$externalChangesPossible = "unknown"
$forceDddAdiv = "yes"
$importPipelinePackage = "no"
$packageManagerDetection = "yes"
$directiveMode = "merge"

if ($kind -eq "code" -or $packs -match "code") {
    Write-Host ""
    Write-Host "Programming context questions:"
    try {
        $stackJson = & (Join-Path $PSScriptRoot "detect_project_stack.ps1") -TargetPath "."
        Write-Host "Detected stack:"
        Write-Host $stackJson
    } catch {
        Write-Host "Stack detection failed: $($_.Exception.Message)"
    }
    $aiMayCommit = Ask-Default -Prompt "13. Should AI commit changes" -Default "no"
    $aiMayPush = Ask-Default -Prompt "14. Should AI push changes" -Default "no"
    $branchWorkflow = Ask-Default -Prompt "15. Do you work on branches" -Default "yes"
    $externalChangesPossible = Ask-Default -Prompt "16. Can external changes happen while AI works" -Default "yes"
    $forceDddAdiv = Ask-Default -Prompt "17. Force DDD-ADIV" -Default "yes"
    $importPipelinePackage = Ask-Default -Prompt "18. Import pipeline package/dependency if ecosystem supports it" -Default "no"
    $packageManagerDetection = Ask-Default -Prompt "19. Detect package managers/frameworks, including Composer" -Default "yes"
    $directiveMode = Ask-Default -Prompt "20. Directive mode: snapshot, merge, replace" -Default "merge"
}

Write-Host ""
Write-Host "Summary:"
Write-Host "Language: $language"
Write-Host "Project: $projectName"
Write-Host "Packs: $packs"
Write-Host "AI mode: $aiMode"
Write-Host "Optimize for: $optimizeFor"
Write-Host "Avoid: $avoid"
Write-Host "Artifacts: $artifacts"
Write-Host "External: $external"
Write-Host ""

$confirm = Ask-Default -Prompt "Proceed with initialization? yes/no" -Default "yes"
if ($confirm -ne "yes") {
    Write-Host "Initialization cancelled."
    exit 0
}

$initScript = Join-Path $PSScriptRoot "Initialize-SocratexPipeline.ps1"
& $initScript `
    -ProjectName $projectName `
    -Language $language `
    -AiMode $aiMode `
    -FirstTarget $firstTarget `
    -FirstSessionSuccess $success `
    -UseGit $useGit `
    -AiMayCommit $aiMayCommit `
    -AiMayPush $aiMayPush `
    -BranchWorkflow $branchWorkflow `
    -ExternalChangesPossible $externalChangesPossible `
    -ForceDddAdiv $forceDddAdiv `
    -ImportPipelinePackage $importPipelinePackage `
    -PackageManagerDetection $packageManagerDetection `
    -DirectiveMode $directiveMode `
    -KeepPacks $packs `
    -CreateFiles `
    -CompileAgent `
    -RunAudit `
    -DryRun:$DryRun
