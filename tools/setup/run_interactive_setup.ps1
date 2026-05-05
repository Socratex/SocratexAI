param(
    [switch]$DryRun
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$repoRoot = Resolve-Path -LiteralPath (Join-Path $PSScriptRoot "..\..")

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
$communicationProfile = Ask-Default -Prompt "7. Communication profile: standard, epistemic_skeptic" -Default "standard"
$optimizeFor = Ask-Default -Prompt "8. Optimize for" -Default "correctness"
$avoid = Ask-Default -Prompt "9. What should the agent avoid" -Default "unbounded scope"
$artifacts = Ask-Default -Prompt "10. Required artifacts after initialization" -Default "default pack artifacts"
$useChangelog = Ask-Default -Prompt "11. Use CHANGELOG for shipped history? yes/no" -Default "yes"
$useGit = Ask-Default -Prompt "12. Use Git" -Default "yes"
$external = Ask-Default -Prompt "13. External tools, folders, accounts, or references" -Default "none"
$success = Ask-Default -Prompt "14. Successful first session means" -Default "project initialized and first pass ready"
$aiMayCommit = "no"
$aiMayPush = "no"
$branchMode = "linear"
$externalChangesPossible = "unknown"
$forceDddAdiv = "yes"
$importPipelinePackage = "no"
$packageManagerDetection = "yes"
$directiveMode = "merge"
$projectLifecycle = "TBD"
$testCoverage = "TBD"
$framework = "TBD"
$frameworkKind = "TBD"
$linter = "TBD"
$ci = "TBD"
$docs = "TBD"
$teamSize = "TBD"
$velocity = "TBD"
$highestPain = "TBD"
$stackTags = @()

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
    $aiMayCommit = Ask-Default -Prompt "15. Should AI commit changes" -Default "no"
    $aiMayPush = Ask-Default -Prompt "16. Should AI push changes" -Default "no"
    $projectLifecycle = Ask-Default -Prompt "17. Lifecycle: greenfield, early, mature, legacy, sunset" -Default "early"
    $testCoverage = Ask-Default -Prompt "18. Test coverage: none, smoke-only, partial, comprehensive, tdd" -Default "partial"
    $framework = Ask-Default -Prompt "19. Framework name or none" -Default "TBD"
    $frameworkKind = Ask-Default -Prompt "20. Framework kind: standard, custom in-house, mixed, none" -Default "standard"
    $linter = Ask-Default -Prompt "21. Linter/typecheck: enforced, optional, none" -Default "optional"
    $ci = Ask-Default -Prompt "22. CI/CD: full, partial, none" -Default "partial"
    $docs = Ask-Default -Prompt "23. Documentation: current, partial, stale, none" -Default "partial"
    $teamSize = Ask-Default -Prompt "24. Team size: solo, small, medium, large" -Default "solo"
    $velocity = Ask-Default -Prompt "25. Velocity: experimental, iterating, shipping, maintenance" -Default "iterating"
    $highestPain = Ask-Default -Prompt "26. Highest current pain" -Default "TBD"
    $stackText = Ask-Default -Prompt "27. Stack tags, comma-separated" -Default "TBD"
    $stackTags = $stackText -split "," | ForEach-Object { $_.Trim() } | Where-Object { $_ -and $_ -ne "TBD" }
    $branchMode = Ask-Default -Prompt "28. Branch mode: branch_scoped, linear" -Default "branch_scoped"
    $externalChangesPossible = Ask-Default -Prompt "29. Can external changes happen while AI works" -Default "yes"
    $forceDddAdiv = Ask-Default -Prompt "30. Force DDD-ADIV" -Default "yes"
    $importPipelinePackage = Ask-Default -Prompt "31. Import pipeline package/dependency if ecosystem supports it" -Default "no"
    $packageManagerDetection = Ask-Default -Prompt "32. Detect package managers/frameworks, including Composer" -Default "yes"
    $directiveMode = Ask-Default -Prompt "33. Directive mode: snapshot, merge, replace" -Default "merge"
}

Write-Host ""
Write-Host "Summary:"
Write-Host "Language: $language"
Write-Host "Project: $projectName"
Write-Host "Packs: $packs"
Write-Host "AI mode: $aiMode"
Write-Host "Communication profile: $communicationProfile"
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

$initScript = Join-Path $repoRoot "tools\pipeline\Initialize-SocratexPipeline.ps1"
& $initScript `
    -ProjectName $projectName `
    -Language $language `
    -AiMode $aiMode `
    -CommunicationProfile $communicationProfile `
    -FirstTarget $firstTarget `
    -FirstSessionSuccess $success `
    -UseChangelog $useChangelog `
    -UseGit $useGit `
    -AiMayCommit $aiMayCommit `
    -AiMayPush $aiMayPush `
    -BranchMode $branchMode `
    -ExternalChangesPossible $externalChangesPossible `
    -ForceDddAdiv $forceDddAdiv `
    -ImportPipelinePackage $importPipelinePackage `
    -PackageManagerDetection $packageManagerDetection `
    -ProjectLifecycle $projectLifecycle `
    -TestCoverage $testCoverage `
    -Framework $framework `
    -FrameworkKind $frameworkKind `
    -Linter $linter `
    -Ci $ci `
    -Docs $docs `
    -TeamSize $teamSize `
    -Velocity $velocity `
    -HighestPain $highestPain `
    -StackTags $stackTags `
    -DirectiveMode $directiveMode `
    -KeepPacks $packs `
    -CreateFiles `
    -CompileAgent `
    -RunAudit `
    -DryRun:$DryRun
