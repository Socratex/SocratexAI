param(
    [string]$ProjectName = "Initialized SocratexPipeline Project",
    [string]$Language = "English",
    [ValidateSet("Lite", "Standard", "Enterprise")]
    [string]$AiMode = "Standard",
    [string]$FirstTarget = "TBD",
    [string]$FirstSessionSuccess = "TBD",
    [ValidateSet("standard", "epistemic_skeptic")]
    [string]$CommunicationProfile = "standard",
    [ValidateSet("yes", "no", "TBD")]
    [string]$UseChangelog = "yes",
    [string]$UseGit = "TBD",
    [string]$AiMayCommit = "TBD",
    [string]$AiMayPush = "TBD",
    [ValidateSet("branch_scoped", "linear", "TBD")]
    [string]$BranchMode = "linear",
    [string]$ExternalChangesPossible = "TBD",
    [string]$ForceDddAdiv = "TBD",
    [string]$ImportPipelinePackage = "TBD",
    [string]$PackageManagerDetection = "TBD",
    [string]$ProjectLifecycle = "TBD",
    [string]$TestCoverage = "TBD",
    [string]$Framework = "TBD",
    [string]$FrameworkKind = "TBD",
    [string]$Linter = "TBD",
    [string]$Ci = "TBD",
    [string]$Docs = "TBD",
    [string]$TeamSize = "TBD",
    [string]$Velocity = "TBD",
    [string]$HighestPain = "TBD",
    [string[]]$StackTags = @(),
    [string]$BranchFilesLanguage = "prompt-language",
    [ValidateSet("snapshot", "merge", "replace")]
    [string]$DirectiveMode = "merge",
    [string[]]$KeepPacks = @("generic"),
    [switch]$CreateFiles,
    [switch]$CompileAgent,
    [switch]$RunAudit,
    [switch]$DryRun
)

$ErrorActionPreference = "Stop"

$Root = Resolve-Path (Join-Path $PSScriptRoot "..")
$InstallRoot = Join-Path $Root "SocratexAI"
$ProjectDir = Join-Path $Root "project"
$TemplateDir = Join-Path $Root "templates"
$TrashDir = Join-Path $Root "temp\trash"
$TrashProjectDir = Join-Path $TrashDir "project"
$InitializerDir = Join-Path $Root "initializer"
$TrashInitializerDir = Join-Path $TrashDir "initializer"

New-Item -ItemType Directory -Force -Path $TrashProjectDir | Out-Null
New-Item -ItemType Directory -Force -Path $TrashDir | Out-Null

$allPacks = Get-ChildItem -Path $ProjectDir -Directory
$normalizedPacks = @()
foreach ($pack in $KeepPacks) {
    $normalizedPacks += ($pack -split "," | ForEach-Object { $_.Trim() } | Where-Object { $_ })
}
$KeepPacks = $normalizedPacks

$keep = @{}
foreach ($pack in $KeepPacks) {
    $keep[$pack.ToLowerInvariant()] = $true
}

$knownPacks = @{}
foreach ($packDir in (Get-ChildItem -Path $ProjectDir -Directory)) {
    $knownPacks[$packDir.Name.ToLowerInvariant()] = $true
}

foreach ($pack in $KeepPacks) {
    if (-not $knownPacks.ContainsKey($pack.ToLowerInvariant())) {
        throw "Unknown project pack: $pack"
    }
}

function Copy-TemplateFile {
    param(
        [string]$TemplateName,
        [string]$DestinationRelativePath
    )

    $source = Join-Path $TemplateDir $TemplateName
    $destination = Join-Path $InstallRoot $DestinationRelativePath
    $destinationParent = Split-Path -Parent $destination

    if ($DryRun) {
        Write-Output "Would copy template: $source -> $destination"
        return
    }

    New-Item -ItemType Directory -Force -Path $destinationParent | Out-Null
    if (-not (Test-Path $destination)) {
        Copy-Item -LiteralPath $source -Destination $destination
    }
}

function Copy-CodeTemplateFile {
    param(
        [string]$TemplateName,
        [string]$DestinationRelativePath
    )

    Copy-TemplateFile -TemplateName (Join-Path "code" $TemplateName) -DestinationRelativePath $DestinationRelativePath
}

function Set-TemplateValue {
    param(
        [string]$RelativePath,
        [hashtable]$Values
    )

    $destination = Join-Path $Root $RelativePath
    if ($DryRun) {
        Write-Output "Would update template values in: $destination"
        return
    }

    if (-not (Test-Path -LiteralPath $destination)) {
        return
    }

    $content = Get-Content -Raw -LiteralPath $destination
    foreach ($key in $Values.Keys) {
        $content = $content.Replace($key, [string]$Values[$key])
    }
    Set-Content -LiteralPath $destination -Value $content -NoNewline
}

function Ensure-BranchGitignore {
    param([string]$TargetRoot)

    $gitignorePath = Join-Path $TargetRoot ".gitignore"
    $comment = "# AI working files in user's prompt language - local-only, not for review"
    $ignoredLine = "/ignored"

    if ($DryRun) {
        Write-Output "Would ensure .gitignore contains branch-scoped AI working files ignore rule."
        return
    }

    if (-not (Test-Path -LiteralPath $gitignorePath)) {
        Set-Content -LiteralPath $gitignorePath -Value "$comment`n$ignoredLine`n" -NoNewline
        return
    }

    $content = Get-Content -Raw -LiteralPath $gitignorePath
    $changed = $false
    if ($content -notmatch '(?m)^# AI working files in user''s prompt language - local-only, not for review$') {
        $content = $content.TrimEnd() + "`n$comment`n"
        $changed = $true
    }
    if ($content -notmatch '(?m)^/ignored/?$') {
        $content = $content.TrimEnd() + "`n$ignoredLine`n"
        $changed = $true
    }
    if ($changed) {
        Set-Content -LiteralPath $gitignorePath -Value $content -NoNewline
    }
}

function Initialize-AssistantLayout {
    $assistantRoot = Join-Path $Root ".aiassistant\socratex"
    if ($DryRun) {
        Write-Output "Would create branch-scoped committed directives under: $assistantRoot"
        return
    }

    New-Item -ItemType Directory -Force -Path $assistantRoot | Out-Null
    Copy-Item -LiteralPath (Join-Path $Root "AGENTS.md") -Destination (Join-Path $assistantRoot "AGENTS.md") -Force
    Set-Content -LiteralPath (Join-Path $assistantRoot "DOCS.md") -Value @"
# SocratexAI Documents

## Summary

Committed SocratexAI project directives live here.

Local branch working memory lives under `ignored/ai-socratex/` when branch-scoped mode is active.

"@ -NoNewline
    $configPath = Join-Path $InstallRoot "PIPELINE-CONFIG.json"
    if (Test-Path -LiteralPath $configPath) {
        Copy-Item -LiteralPath $configPath -Destination (Join-Path $assistantRoot "PIPELINE-CONFIG.json") -Force
    }
    $projectFileName = ($ProjectName -replace '[\\/:*?"<>|]', '-').Trim()
    if (-not $projectFileName) {
        $projectFileName = "PROJECT"
    }
    Set-Content -LiteralPath (Join-Path $Root ".aiassistant\$projectFileName.md") -Value @"
# Project Rules

## Summary

Project-specific code generation rules belong here when they are durable and review-facing.

"@ -NoNewline
}

if ($CreateFiles) {
    if ($DryRun) {
        Write-Output "Would copy root controller: $(Join-Path $TemplateDir 'SOCRATEX.md') -> $(Join-Path $Root 'SOCRATEX.md')"
    } else {
        Copy-Item -LiteralPath (Join-Path $TemplateDir "SOCRATEX.md") -Destination (Join-Path $Root "SOCRATEX.md") -Force
    }

    if ($keep.ContainsKey("code")) {
        Copy-CodeTemplateFile -TemplateName "DOCS.json" -DestinationRelativePath "DOCS.json"
        Copy-CodeTemplateFile -TemplateName "STATE.json" -DestinationRelativePath "STATE.json"
        Copy-CodeTemplateFile -TemplateName "_PLAN.json" -DestinationRelativePath "_PLAN.json"
        Copy-CodeTemplateFile -TemplateName "DECISIONS.json" -DestinationRelativePath "DECISIONS.json"
        Copy-CodeTemplateFile -TemplateName "PIPELINE-CONFIG.json" -DestinationRelativePath "PIPELINE-CONFIG.json"
    } else {
        Copy-TemplateFile -TemplateName "DOCS.json" -DestinationRelativePath "DOCS.json"
        Copy-TemplateFile -TemplateName "STATE.md" -DestinationRelativePath "STATE.md"
        Copy-TemplateFile -TemplateName "_PLAN.md" -DestinationRelativePath "_PLAN.md"
        Copy-TemplateFile -TemplateName "DECISIONS.md" -DestinationRelativePath "DECISIONS.md"
        Copy-TemplateFile -TemplateName "JOURNAL.md" -DestinationRelativePath "JOURNAL.md"
        Copy-TemplateFile -TemplateName "REVIEW.md" -DestinationRelativePath "REVIEW.md"
        Copy-TemplateFile -TemplateName "PIPELINE-CONFIG.json" -DestinationRelativePath "PIPELINE-CONFIG.json"
    }

    Copy-TemplateFile -TemplateName "WORKFLOW.json" -DestinationRelativePath "WORKFLOW.json"
    Copy-TemplateFile -TemplateName "team\product.json" -DestinationRelativePath "team\product.json"
    Copy-TemplateFile -TemplateName "team\technical.json" -DestinationRelativePath "team\technical.json"
    Copy-TemplateFile -TemplateName "team\performance.json" -DestinationRelativePath "team\performance.json"
    Copy-TemplateFile -TemplateName "team\experience.json" -DestinationRelativePath "team\experience.json"
    Copy-TemplateFile -TemplateName "team\pipeline.json" -DestinationRelativePath "team\pipeline.json"
    Copy-TemplateFile -TemplateName "docs-tech\KNOWLEDGE-VIEWS.json" -DestinationRelativePath "docs-tech\KNOWLEDGE-VIEWS.json"

    if ($keep.ContainsKey("code") -and $AiMode -ne "Lite") {
        Copy-TemplateFile -TemplateName "_PROMPTS.md" -DestinationRelativePath "_PROMPTS.md"
        Copy-CodeTemplateFile -TemplateName "_PROMPT-QUEUE.json" -DestinationRelativePath "_PROMPT-QUEUE.json"
        Copy-TemplateFile -TemplateName "_INSTRUCTIONS.md" -DestinationRelativePath "_INSTRUCTIONS.md"
        Copy-CodeTemplateFile -TemplateName "_INSTRUCTION-QUEUE.json" -DestinationRelativePath "_INSTRUCTION-QUEUE.json"
        Copy-CodeTemplateFile -TemplateName "TODO.json" -DestinationRelativePath "TODO.json"
        Copy-CodeTemplateFile -TemplateName "BUGS.json" -DestinationRelativePath "BUGS.json"
        Copy-CodeTemplateFile -TemplateName "BUGS-SOLVED.json" -DestinationRelativePath "BUGS-SOLVED.json"
        if ($UseChangelog -ne "no") {
            Copy-CodeTemplateFile -TemplateName "CHANGELOG.json" -DestinationRelativePath "CHANGELOG.json"
        }
        Copy-CodeTemplateFile -TemplateName "context-docs\ENGINEERING.json" -DestinationRelativePath "context-docs\ENGINEERING.json"
        Copy-CodeTemplateFile -TemplateName "context-docs\TECHNICAL.json" -DestinationRelativePath "context-docs\TECHNICAL.json"
        Copy-CodeTemplateFile -TemplateName "context-docs\FROZEN_LAYERS.json" -DestinationRelativePath "context-docs\FROZEN_LAYERS.json"
        Copy-TemplateFile -TemplateName "logs-.gitkeep" -DestinationRelativePath "logs\.gitkeep"
    } elseif ($keep.ContainsKey("code")) {
        Copy-CodeTemplateFile -TemplateName "TODO.json" -DestinationRelativePath "TODO.json"
        if ($UseChangelog -ne "no") {
            Copy-CodeTemplateFile -TemplateName "CHANGELOG.json" -DestinationRelativePath "CHANGELOG.json"
        }
    }

    if ($keep.ContainsKey("generic") -or $keep.ContainsKey("personal") -or $keep.ContainsKey("creative")) {
        Copy-TemplateFile -TemplateName "BACKLOG.md" -DestinationRelativePath "BACKLOG.md"
        Copy-TemplateFile -TemplateName "ISSUES.md" -DestinationRelativePath "ISSUES.md"
    }

    if (-not $DryRun -and (Test-Path -LiteralPath (Join-Path $InstallRoot "PIPELINE-CONFIG.json"))) {
        $runtimeStatus = [ordered]@{
            python3 = [ordered]@{ ok = "TBD"; version = "TBD"; install_hint = "TBD" }
            pwsh = [ordered]@{ ok = "TBD"; version = "TBD"; install_hint = "TBD"; install_supported = "TBD"; fallback_recommendation = "TBD" }
        }
        $python = Get-Command python -ErrorAction SilentlyContinue
        if ($python) {
            try {
                $runtimeJson = [string]::Join([Environment]::NewLine, (& python (Join-Path $PSScriptRoot "check_runtime.py") --root-key runtime_status))
                $runtimePayload = $runtimeJson | ConvertFrom-Json
                $runtimeStatus = $runtimePayload.runtime_status
            } catch {
                $runtimeStatus["check_error"] = "runtime check failed"
            }
        }
        $config = [ordered]@{
            summary = "Initialized project configuration for SocratexPipeline."
            language = $Language
            active_project_packs = @($KeepPacks)
            ai_operating_mode = $AiMode
            git = $UseGit
            ai_may_commit = $AiMayCommit
            ai_may_push = $AiMayPush
            branch_workflow = $BranchMode
            external_changes_possible = $ExternalChangesPossible
            force_ddd_adiv = $ForceDddAdiv
            import_pipeline_package = $ImportPipelinePackage
            package_manager_detection = $PackageManagerDetection
            directive_mode = $DirectiveMode
            first_target = $FirstTarget
            first_session_success_criteria = $FirstSessionSuccess
            communication = [ordered]@{ profile = $CommunicationProfile }
            changelog = [ordered]@{ enabled = $UseChangelog }
            pipeline = [ordered]@{
                version = "0.2.0-alpha"
                update_source = "TBD"
                public_bootstrap_url = "TBD"
                update_command = 'powershell -NoProfile -ExecutionPolicy Bypass -File SocratexAI/tools/update_pipeline_from_link.ps1 -Source "<source>" -Packs code -ReinitializeNew'
                remove_command = "powershell -NoProfile -ExecutionPolicy Bypass -File SocratexAI/tools/remove_pipeline.ps1 -TargetPath ."
                reinitialize_command = "powershell -NoProfile -ExecutionPolicy Bypass -File SocratexAI/tools/reinitialize_pipeline.ps1 -TargetPath ."
            }
            workflow = [ordered]@{
                branch_mode = $BranchMode
                branch_files_dir = "ignored/ai-socratex"
                branch_state_file = "ignored/ai-socratex/<branch>-STATE.md"
                branch_plan_file = "ignored/ai-socratex/<branch>-PLAN.md"
                branch_files_language = $BranchFilesLanguage
            }
            project_profile = [ordered]@{
                lifecycle = $ProjectLifecycle
                test_coverage = $TestCoverage
                framework = $Framework
                framework_kind = $FrameworkKind
                linter = $Linter
                ci = $Ci
                docs = $Docs
                team_size = $TeamSize
                velocity = $Velocity
                highest_pain = $HighestPain
                stack = @($StackTags)
            }
            runtime_status = $runtimeStatus
        }
        [System.IO.File]::WriteAllText((Join-Path $InstallRoot "PIPELINE-CONFIG.json"), (($config | ConvertTo-Json -Depth 8) + [Environment]::NewLine), [System.Text.UTF8Encoding]::new($false))
    }

    if (-not $DryRun -and (Test-Path -LiteralPath (Join-Path $Root "pipeline_featurelist.json"))) {
        New-Item -ItemType Directory -Force -Path $InstallRoot | Out-Null
        Copy-Item -LiteralPath (Join-Path $Root "pipeline_featurelist.json") -Destination (Join-Path $InstallRoot "pipeline_featurelist.json") -Force
        $syncFeatureListScript = Join-Path $Root "tools\sync_pipeline_featurelist.ps1"
        if (Test-Path -LiteralPath $syncFeatureListScript) {
            & powershell -NoProfile -ExecutionPolicy Bypass -File $syncFeatureListScript -TargetPath $Root
        }
        $knowledgeCompileScript = Join-Path $Root "tools\knowledge_compile.ps1"
        if (Test-Path -LiteralPath $knowledgeCompileScript) {
            & powershell -NoProfile -ExecutionPolicy Bypass -File $knowledgeCompileScript
        }
    }

    if ($keep.ContainsKey("code") -and $BranchMode -eq "branch_scoped") {
        if ($DryRun) {
            Write-Output "Would initialize root ignored/ai-socratex branch memory."
        } else {
            & (Join-Path $PSScriptRoot "init_branch_memory.ps1") -BranchFilesDir "ignored/ai-socratex" -EnsureGitignore
        }
        Initialize-AssistantLayout
    }
}

$readmePath = Join-Path $Root "README.md"
if ($DryRun) {
    Write-Output "Would set project name in README.md to: $ProjectName"
} else {
    $readme = Get-Content -Raw -LiteralPath $readmePath
    $readme = $readme -replace "# SocratexPipeline", "# $ProjectName"
    Set-Content -LiteralPath $readmePath -Value $readme -NoNewline
}

foreach ($packDir in $allPacks) {
    if (-not $keep.ContainsKey($packDir.Name.ToLowerInvariant())) {
        $target = Join-Path $TrashProjectDir $packDir.Name
        if ($DryRun) {
            Write-Output "Would move project pack: $($packDir.FullName) -> $target"
        } else {
            if (Test-Path $target) {
                Remove-Item -LiteralPath $target -Recurse -Force
            }
            Move-Item -LiteralPath $packDir.FullName -Destination $target
        }
    }
}

if (Test-Path $InitializerDir) {
    if ($DryRun) {
        Write-Output "Would move initializer: $InitializerDir -> $TrashInitializerDir"
    } else {
        if (Test-Path $TrashInitializerDir) {
            Remove-Item -LiteralPath $TrashInitializerDir -Recurse -Force
        }
        Move-Item -LiteralPath $InitializerDir -Destination $TrashInitializerDir
    }
}

if ($CompileAgent) {
    if ($DryRun) {
        Write-Output "Would compile AGENTS.md for packs: $([string]::Join(', ', $KeepPacks))"
    } else {
        & (Join-Path $PSScriptRoot "generate_installed_agent_instructions.ps1") -Packs $KeepPacks -OutputPath "AGENTS.md"
    }
}

if ($RunAudit -and $keep.ContainsKey("code")) {
    if ($DryRun) {
        Write-Output "Would run initialized code audit."
    } else {
        & (Join-Path $PSScriptRoot "audit_docs.ps1") -Initialized
    }
}

Write-Output "Initialization cleanup complete."
Write-Output "Recommended next improvements: configure quality gate command, Git convention, CI integration, frozen layer candidates, and domain-specific context capsules."
