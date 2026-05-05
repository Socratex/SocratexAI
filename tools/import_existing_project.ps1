param(
    [Parameter(Mandatory = $true)]
    [string]$TargetPath,

    [string[]]$Packs = @("code"),

    [ValidateSet("Lite", "Standard", "Enterprise")]
    [string]$AiMode = "Standard",

    [string]$Language = "English",

    [ValidateSet("branch_scoped", "linear")]
    [string]$BranchMode = "linear",

    [switch]$CreateProjectFiles,
    [switch]$DryRun
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$SourceRoot = Resolve-Path -LiteralPath (Join-Path $PSScriptRoot "..")
$TargetRoot = Resolve-Path -LiteralPath $TargetPath
$InstallRoot = Join-Path $TargetRoot "SocratexAI"

$normalizedPacks = @()
foreach ($pack in $Packs) {
    $normalizedPacks += ($pack -split "," | ForEach-Object { $_.Trim() } | Where-Object { $_ })
}
$Packs = $normalizedPacks

function Copy-ItemSafe {
    param(
        [string]$Source,
        [string]$Destination
    )

    if ($DryRun) {
        Write-Host "Would copy: $Source -> $Destination"
        return
    }

    if (Test-Path -LiteralPath $Destination) {
        Write-Host "Skip existing: $Destination"
        return
    }

    $parent = Split-Path -Parent $Destination
    New-Item -ItemType Directory -Force -Path $parent | Out-Null
    Copy-Item -LiteralPath $Source -Destination $Destination -Recurse
}

function Ensure-TargetGitignore {
    $gitignorePath = Join-Path $TargetRoot ".gitignore"
    $comment = "# AI working files in user's prompt language - local-only, not for review"
    $ignoredLine = "/ignored"

    if ($DryRun) {
        Write-Host "Would ensure .gitignore contains: $ignoredLine"
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

function Get-CurrentBranchName {
    Push-Location -LiteralPath $TargetRoot
    try {
        $branch = git branch --show-current 2>$null
        if ($LASTEXITCODE -eq 0 -and $branch) {
            return ($branch.Trim() -replace '[\\/:*?"<>|]', '-')
        }
    } finally {
        Pop-Location
    }
    return "unknown-branch"
}

function Initialize-TargetAssistantLayout {
    $assistantRoot = Join-Path $TargetRoot ".aiassistant\socratex"
    if ($DryRun) {
        Write-Host "Would create branch-scoped committed directives under: $assistantRoot"
        return
    }

    New-Item -ItemType Directory -Force -Path $assistantRoot | Out-Null
    Copy-Item -LiteralPath (Join-Path $SourceRoot "AGENTS.md") -Destination (Join-Path $assistantRoot "AGENTS.md") -Force
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
    Set-Content -LiteralPath (Join-Path $TargetRoot ".aiassistant\PROJECT.md") -Value @"
# Project Rules

## Summary

Project-specific code generation rules belong here when they are durable and review-facing.

"@ -NoNewline
}

Write-Host "==> importing SocratexPipeline into existing project"
Write-Host "Target: $TargetRoot"
Write-Host "Install root: $InstallRoot"

foreach ($path in @("AI-compiled", "core", "adapters", "docs-tech", "templates", "tools")) {
    Copy-ItemSafe -Source (Join-Path $SourceRoot $path) -Destination (Join-Path $InstallRoot $path)
}

Copy-ItemSafe -Source (Join-Path $SourceRoot "pipeline_featurelist.json") -Destination (Join-Path $InstallRoot "pipeline_featurelist.json")

if (-not $DryRun) {
    New-Item -ItemType Directory -Force -Path (Join-Path $InstallRoot "project") | Out-Null
}
foreach ($pack in $Packs) {
    $sourcePack = Join-Path $SourceRoot "project\$pack"
    if (-not (Test-Path -LiteralPath $sourcePack)) {
        throw "Unknown pack: $pack"
    }

    Copy-ItemSafe -Source $sourcePack -Destination (Join-Path $InstallRoot "project\$pack")
}

Copy-ItemSafe -Source (Join-Path $SourceRoot "AGENTS.md") -Destination (Join-Path $InstallRoot "AGENTS.md")
Copy-ItemSafe -Source (Join-Path $SourceRoot "RECOMMENDATION.md") -Destination (Join-Path $InstallRoot "RECOMMENDATION.md")
Copy-ItemSafe -Source (Join-Path $SourceRoot "PUBLIC-BOOTSTRAP.md") -Destination (Join-Path $InstallRoot "PUBLIC-BOOTSTRAP.md")
Copy-ItemSafe -Source (Join-Path $SourceRoot "templates\SOCRATEX.md") -Destination (Join-Path $TargetRoot "SOCRATEX.md")

if ($CreateProjectFiles) {
    $hasCodePack = $Packs -contains "code"
    $templateMap = if ($hasCodePack) {
        @{
            "code/DOCS.json" = "DOCS.json"
            "code/STATE.json" = "STATE.json"
            "code/_PLAN.json" = "_PLAN.json"
            "code/TODO.json" = "TODO.json"
            "code/DECISIONS.json" = "DECISIONS.json"
            "code/CHANGELOG.json" = "CHANGELOG.json"
            "code/BUGS.json" = "BUGS.json"
            "code/BUGS-SOLVED.json" = "BUGS-SOLVED.json"
            "_PROMPTS.md" = "_PROMPTS.md"
            "code/_PROMPT-QUEUE.json" = "_PROMPT-QUEUE.json"
            "_INSTRUCTIONS.md" = "_INSTRUCTIONS.md"
            "code/_INSTRUCTION-QUEUE.json" = "_INSTRUCTION-QUEUE.json"
            "code/PIPELINE-CONFIG.json" = "PIPELINE-CONFIG.json"
            "WORKFLOW.json" = "WORKFLOW.json"
            "docs-tech/KNOWLEDGE-VIEWS.json" = "docs-tech\KNOWLEDGE-VIEWS.json"
            "team/product.json" = "team\product.json"
            "team/technical.json" = "team\technical.json"
            "team/performance.json" = "team\performance.json"
            "team/experience.json" = "team\experience.json"
            "team/pipeline.json" = "team\pipeline.json"
            "code/context-docs/ENGINEERING.json" = "context-docs\ENGINEERING.json"
            "code/context-docs/TECHNICAL.json" = "context-docs\TECHNICAL.json"
            "code/context-docs/FROZEN_LAYERS.json" = "context-docs\FROZEN_LAYERS.json"
            "logs-.gitkeep" = "logs\.gitkeep"
        }
    } else {
        @{
            "DOCS.json" = "DOCS.json"
            "STATE.md" = "STATE.md"
            "_PLAN.md" = "_PLAN.md"
            "BACKLOG.md" = "BACKLOG.md"
            "DECISIONS.md" = "DECISIONS.md"
            "ISSUES.md" = "ISSUES.md"
            "JOURNAL.md" = "JOURNAL.md"
            "REVIEW.md" = "REVIEW.md"
            "PIPELINE-CONFIG.json" = "PIPELINE-CONFIG.json"
            "WORKFLOW.json" = "WORKFLOW.json"
            "docs-tech/KNOWLEDGE-VIEWS.json" = "docs-tech\KNOWLEDGE-VIEWS.json"
            "team/product.json" = "team\product.json"
            "team/technical.json" = "team\technical.json"
            "team/performance.json" = "team\performance.json"
            "team/experience.json" = "team\experience.json"
            "team/pipeline.json" = "team\pipeline.json"
        }
    }

    foreach ($entry in $templateMap.GetEnumerator()) {
        Copy-ItemSafe -Source (Join-Path $SourceRoot "templates\$($entry.Key)") -Destination (Join-Path $InstallRoot $entry.Value)
    }

    if ($hasCodePack -and $BranchMode -eq "branch_scoped") {
        Copy-ItemSafe -Source (Join-Path $SourceRoot "templates\code\branch\BRANCH-TODO.md") -Destination (Join-Path $TargetRoot "ignored\ai-socratex\TODO.md")
        $branch = Get-CurrentBranchName
        Copy-ItemSafe -Source (Join-Path $SourceRoot "templates\code\branch\BRANCH-STATE.md") -Destination (Join-Path $TargetRoot "ignored\ai-socratex\$branch-STATE.md")
        Copy-ItemSafe -Source (Join-Path $SourceRoot "templates\code\branch\BRANCH-PLAN.md") -Destination (Join-Path $TargetRoot "ignored\ai-socratex\$branch-PLAN.md")
        Ensure-TargetGitignore
        Initialize-TargetAssistantLayout
    }
}

if (-not $DryRun) {
    $syncFeatureListScript = Join-Path $InstallRoot "tools\sync_pipeline_featurelist.ps1"
    if (Test-Path -LiteralPath $syncFeatureListScript) {
        & powershell -NoProfile -ExecutionPolicy Bypass -File $syncFeatureListScript -TargetPath $TargetRoot
    }
    $knowledgeCompileScript = Join-Path $InstallRoot "tools\knowledge_compile.ps1"
    if (Test-Path -LiteralPath $knowledgeCompileScript) {
        & powershell -NoProfile -ExecutionPolicy Bypass -File $knowledgeCompileScript
        if ($LASTEXITCODE -ne 0) {
            throw "knowledge_compile failed with exit code $LASTEXITCODE"
        }
    }
    $hasCodePack = $Packs -contains "code"
    $configPath = if ($hasCodePack) {
        Join-Path $InstallRoot "PIPELINE-CONFIG.json"
    } else {
        Join-Path $InstallRoot "PIPELINE-CONFIG.json"
    }
    $shouldWriteConfig = -not (Test-Path -LiteralPath $configPath)
    if (-not $shouldWriteConfig) {
        $existingConfig = Get-Content -Raw -LiteralPath $configPath
        try {
            $existingConfigJson = $existingConfig | ConvertFrom-Json
            $shouldWriteConfig = [string]$existingConfigJson.language -eq "TBD"
        } catch {
            $shouldWriteConfig = $true
        }
    }
    if ($shouldWriteConfig) {
        $config = [ordered]@{
            summary = "Imported SocratexPipeline configuration."
            language = $Language
            active_project_packs = @($Packs)
            ai_operating_mode = $AiMode
            communication = [ordered]@{ profile = "standard" }
            branch_workflow = $BranchMode
            pipeline = [ordered]@{
                version = "0.2.0-alpha"
                update_source = "TBD"
                public_bootstrap_url = "TBD"
                update_command = "powershell -NoProfile -ExecutionPolicy Bypass -File SocratexAI/tools/update_pipeline_from_link.ps1 -Source `"<source>`" -Packs $($Packs[0]) -ReinitializeNew"
                remove_command = "powershell -NoProfile -ExecutionPolicy Bypass -File SocratexAI/tools/remove_pipeline.ps1 -TargetPath ."
                reinitialize_command = "powershell -NoProfile -ExecutionPolicy Bypass -File SocratexAI/tools/reinitialize_pipeline.ps1 -TargetPath ."
            }
        }
        if ($hasCodePack) {
            $config["changelog"] = [ordered]@{ enabled = "yes" }
            $config["workflow"] = [ordered]@{
                branch_mode = $BranchMode
                branch_files_dir = "ignored/ai-socratex"
                branch_state_file = "ignored/ai-socratex/<branch>-STATE.md"
                branch_plan_file = "ignored/ai-socratex/<branch>-PLAN.md"
                branch_files_language = "prompt-language"
            }
            $config["project_profile"] = [ordered]@{
                lifecycle = "TBD"
                test_coverage = "TBD"
                framework = "TBD"
                framework_kind = "TBD"
                linter = "TBD"
                ci = "TBD"
                docs = "TBD"
                team_size = "TBD"
                velocity = "TBD"
                highest_pain = "TBD"
                stack = @()
            }
            $config["runtime_status"] = [ordered]@{
                python3 = [ordered]@{ ok = "TBD"; version = "TBD"; install_hint = "TBD" }
                pwsh = [ordered]@{ ok = "TBD"; version = "TBD"; install_hint = "TBD"; install_supported = "TBD"; fallback_recommendation = "TBD" }
            }
        }
        [System.IO.File]::WriteAllText($configPath, (($config | ConvertTo-Json -Depth 8) + [Environment]::NewLine), [System.Text.UTF8Encoding]::new($false))
    }
}

Write-Host "Import complete. SocratexAI is now active for this project; future sessions should start from SOCRATEX.md."
Write-Host "Review SOCRATEX.md and run SocratexAI/tools/audit_docs.ps1 when ready."
