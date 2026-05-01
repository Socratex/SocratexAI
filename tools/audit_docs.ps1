param(
    [int]$StateSoftLimit = 250,
    [switch]$Initialized,
    [switch]$Strict
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$repoRoot = Resolve-Path -LiteralPath (Join-Path $PSScriptRoot "..")
$errors = New-Object System.Collections.Generic.List[string]
$warnings = New-Object System.Collections.Generic.List[string]

function Add-Error {
    param([string]$Message)
    $errors.Add($Message) | Out-Null
}

function Add-Warning {
    param([string]$Message)
    $warnings.Add($Message) | Out-Null
}

function Get-RepoText {
    param([string]$RelativePath)

    $path = Join-Path $repoRoot $RelativePath
    if (-not (Test-Path -LiteralPath $path)) {
        Add-Error "Missing required file: $RelativePath"
        return ""
    }

    return Get-Content -Raw -LiteralPath $path
}

function Get-OptionalRepoText {
    param([string]$RelativePath)

    $path = Join-Path $repoRoot $RelativePath
    if (-not (Test-Path -LiteralPath $path)) {
        return ""
    }

    return Get-Content -Raw -LiteralPath $path
}

function Test-ContainsText {
    param(
        [string]$Text,
        [string]$Needle,
        [string]$Label
    )

    if (-not $Text.Contains($Needle)) {
        Add-Error "$Label is missing required text: $Needle"
    }
}

function Test-OpeningTocEmoji {
    param([System.IO.FileInfo]$File)

    $lines = @(Get-Content -LiteralPath $File.FullName)
    if ($lines.Count -eq 0) {
        return
    }

    $tocIndex = -1
    for ($i = 0; $i -lt [Math]::Min($lines.Count, 80); $i++) {
        if ($lines[$i] -match '^##\s+(TOC|Table of Contents|Contents|Index)\s*$') {
            $tocIndex = $i
            break
        }

        if ($lines[$i] -match '^##\s+' -and $lines[$i] -notmatch '^##\s+(TOC|Table of Contents|Contents|Index)\s*$') {
            break
        }
    }

    if ($tocIndex -lt 0) {
        return
    }

    for ($i = $tocIndex + 1; $i -lt $lines.Count; $i++) {
        $line = $lines[$i]
        if ($line -match '^##\s+') {
            break
        }

        if ($line -notmatch '^\s*[-*+]\s+') {
            continue
        }

        $itemText = $line -replace '^\s*[-*+]\s+(?:\[[ xX]\]\s+)?', ''
        if ($itemText -notmatch '^[^\x00-\x7F]') {
            $relativePath = $File.FullName
            $repoPrefix = "$repoRoot\"
            if ($relativePath.StartsWith($repoPrefix, [System.StringComparison]::OrdinalIgnoreCase)) {
                $relativePath = $relativePath.Substring($repoPrefix.Length)
            }

            Add-Error "${relativePath}:$($i + 1) opening TOC/index item must start with an emoji."
        }
    }
}

function Test-FileSoftLimit {
    param(
        [string]$RelativePath,
        [int]$SoftLimit,
        [string]$Purpose
    )

    $path = Join-Path $repoRoot $RelativePath
    if (-not (Test-Path -LiteralPath $path)) {
        return
    }

    $lineCount = @(Get-Content -LiteralPath $path).Count
    if ($lineCount -gt $SoftLimit) {
        Add-Warning "$RelativePath has $lineCount lines; soft limit is $SoftLimit. Compact it because $Purpose."
    }
}

Push-Location -LiteralPath $repoRoot
try {
    Write-Host "==> audit docs"

    $agents = Get-RepoText -RelativePath "AGENTS.md"
    $contract = Get-RepoText -RelativePath "core/AGENT-CONTRACT.yaml"
    $fileFormats = Get-RepoText -RelativePath "core/FILE-FORMATS.yaml"
    $promotionRules = Get-RepoText -RelativePath "core/PROMOTION-RULES.yaml"
    $contextCompaction = Get-RepoText -RelativePath "core/CONTEXT-COMPACTION.yaml"
    $memoryModel = Get-RepoText -RelativePath "core/MEMORY-MODEL.yaml"
    $activationCheck = Get-RepoText -RelativePath "core/ACTIVATION-CHECK.yaml"
    $updateProtocol = Get-RepoText -RelativePath "core/UPDATE-PROTOCOL.yaml"
    $removalProtocol = Get-RepoText -RelativePath "core/REMOVAL-PROTOCOL.yaml"
    $projectProfile = Get-RepoText -RelativePath "core/PROJECT-PROFILE.yaml"
    $roiBias = Get-RepoText -RelativePath "core/ROI-BIAS.yaml"
    $scriptFallback = Get-RepoText -RelativePath "core/SCRIPT-FALLBACK.yaml"
    $taskWork = Get-RepoText -RelativePath "core/TASK-WORK.yaml"
    $instructionCapture = Get-RepoText -RelativePath "core/INSTRUCTION-CAPTURE.yaml"
    $codePackActive = Test-Path -LiteralPath (Join-Path $repoRoot "project/code/PACK.yaml")
    $codePack = if ($codePackActive) { Get-RepoText -RelativePath "project/code/PACK.yaml" } else { "" }
    $codeWorkflow = if ($codePackActive) { Get-RepoText -RelativePath "project/code/WORKFLOW.yaml" } else { "" }
    $branchMode = if ($codePackActive) { Get-RepoText -RelativePath "project/code/BRANCH-MODE.yaml" } else { "" }
    $codeCommands = if ($codePackActive) { Get-RepoText -RelativePath "project/code/COMMANDS.yaml" } else { "" }
    $codeRegistries = if ($codePackActive) { Get-RepoText -RelativePath "project/code/REGISTRIES.yaml" } else { "" }
    $dddAdiv = if ($codePackActive) { Get-RepoText -RelativePath "project/code/DDD-ADIV.yaml" } else { "" }
    $gitRules = if ($codePackActive) { Get-RepoText -RelativePath "project/code/GIT.yaml" } else { "" }
    $frozenLayers = if ($codePackActive) { Get-RepoText -RelativePath "project/code/FROZEN-LAYERS.yaml" } else { "" }
    $codeInstructionCapture = if ($codePackActive) { Get-RepoText -RelativePath "project/code/INSTRUCTION-CAPTURE.yaml" } else { "" }
    $codeDiagnostics = if ($codePackActive) { Get-RepoText -RelativePath "project/code/DIAGNOSTICS.yaml" } else { "" }

    Test-ContainsText -Text $agents -Needle "core/AGENT-CONTRACT.yaml" -Label "AGENTS.md"
    Test-ContainsText -Text $agents -Needle "core/MEMORY-MODEL.yaml" -Label "AGENTS.md"
    Test-ContainsText -Text $agents -Needle "core/ACTIVATION-CHECK.yaml" -Label "AGENTS.md"
    Test-ContainsText -Text $agents -Needle "core/UPDATE-PROTOCOL.yaml" -Label "AGENTS.md"
    Test-ContainsText -Text $agents -Needle "core/REMOVAL-PROTOCOL.yaml" -Label "AGENTS.md"
    Test-ContainsText -Text $agents -Needle "core/TASK-WORK.yaml" -Label "AGENTS.md"
    Test-ContainsText -Text $agents -Needle "core/PROMOTION-RULES.yaml" -Label "AGENTS.md"
    $publicBootstrap = Get-RepoText -RelativePath "PUBLIC-BOOTSTRAP.md"
    Test-ContainsText -Text $publicBootstrap -Needle "Project Profile Interview" -Label "PUBLIC-BOOTSTRAP.md"
    Test-ContainsText -Text $publicBootstrap -Needle "Runtime Check" -Label "PUBLIC-BOOTSTRAP.md"
    Test-ContainsText -Text $publicBootstrap -Needle "Post-Setup Activation" -Label "PUBLIC-BOOTSTRAP.md"
    Test-ContainsText -Text $publicBootstrap -Needle "ACTIVATION-CHECK.yaml" -Label "PUBLIC-BOOTSTRAP.md"
    Test-ContainsText -Text $publicBootstrap -Needle "Future sessions should start from SOCRATEX.md" -Label "PUBLIC-BOOTSTRAP.md"
    Test-ContainsText -Text $publicBootstrap -Needle "Programming Questions" -Label "PUBLIC-BOOTSTRAP.md"
    Test-ContainsText -Text $publicBootstrap -Needle "branch_scoped" -Label "PUBLIC-BOOTSTRAP.md"
    Test-ContainsText -Text (Get-RepoText -RelativePath "PUBLIC-BOOTSTRAP.md") -Needle "Update, Upgrade, Migrate" -Label "PUBLIC-BOOTSTRAP.md"
    Test-ContainsText -Text (Get-RepoText -RelativePath "PUBLIC-BOOTSTRAP.md") -Needle "UPDATE-PROTOCOL.yaml" -Label "PUBLIC-BOOTSTRAP.md"
    Test-ContainsText -Text (Get-RepoText -RelativePath "PUBLIC-BOOTSTRAP.md") -Needle "REMOVAL-PROTOCOL.yaml" -Label "PUBLIC-BOOTSTRAP.md"
    Test-ContainsText -Text (Get-RepoText -RelativePath "PUBLIC-BOOTSTRAP.md") -Needle "Directive Merge Modes" -Label "PUBLIC-BOOTSTRAP.md"
    Test-ContainsText -Text (Get-RepoText -RelativePath "templates/SOCRATEX.md") -Needle "SocratexAI/" -Label "templates/SOCRATEX.md"
    Test-ContainsText -Text (Get-RepoText -RelativePath "templates/SOCRATEX.md") -Needle "activation point" -Label "templates/SOCRATEX.md"
    Test-ContainsText -Text (Get-RepoText -RelativePath "templates/SOCRATEX.md") -Needle "ACTIVATION-CHECK.yaml" -Label "templates/SOCRATEX.md"
    Test-ContainsText -Text (Get-RepoText -RelativePath "templates/SOCRATEX.md") -Needle "UPDATE-PROTOCOL.yaml" -Label "templates/SOCRATEX.md"
    Test-ContainsText -Text (Get-RepoText -RelativePath "templates/SOCRATEX.md") -Needle "REMOVAL-PROTOCOL.yaml" -Label "templates/SOCRATEX.md"
    Test-ContainsText -Text (Get-RepoText -RelativePath "VERSION") -Needle "0.2.0-alpha" -Label "VERSION"
    Test-ContainsText -Text (Get-RepoText -RelativePath "CHANGELOG.yaml") -Needle "0.2.0-alpha" -Label "CHANGELOG.yaml"
    Test-ContainsText -Text (Get-RepoText -RelativePath "LICENSE") -Needle "MIT License" -Label "LICENSE"
    Test-ContainsText -Text (Get-RepoText -RelativePath "QUALITY-GATE.yaml") -Needle "audit_docs" -Label "QUALITY-GATE.yaml"
    Test-ContainsText -Text (Get-RepoText -RelativePath ".gitignore") -Needle "/ignored/" -Label ".gitignore"
    Test-ContainsText -Text (Get-RepoText -RelativePath "docs/CI-SELF-CHECK.md") -Needle "Provider Guidance" -Label "docs/CI-SELF-CHECK.md"
    Test-ContainsText -Text (Get-RepoText -RelativePath "README.md") -Needle "AI-compiled" -Label "README.md"
    Test-ContainsText -Text (Get-RepoText -RelativePath "README.md") -Needle "evals/" -Label "README.md"
    Test-ContainsText -Text (Get-RepoText -RelativePath "QUALITY-GATE.yaml") -Needle "eval_framework" -Label "QUALITY-GATE.yaml"
    foreach ($compiledFile in @("AI-compiled/README.md", "AI-compiled/INDEX.yaml", "AI-compiled/codex/ENTRYPOINT.md", "AI-compiled/codex/RULES.compiled.md", "AI-compiled/codex/WORKFLOW.compiled.md", "AI-compiled/codex/ORCHESTRATION.compiled.md", "AI-compiled/codex/TEAM.compiled.md", "AI-compiled/checksum.json", "AI-compiled/compile-report.json")) {
        if (-not (Test-Path -LiteralPath (Join-Path $repoRoot $compiledFile))) {
            Add-Error "Missing compiled AI instruction artifact: $compiledFile"
        }
    }
    foreach ($evalFile in @("evals/README.md", "evals/personas.yaml", "evals/expected-behaviors.yaml", "evals/scoring.md", "evals/results/baseline.yaml", "evals/results/with-pipeline.yaml")) {
        if (-not (Test-Path -LiteralPath (Join-Path $repoRoot $evalFile))) {
            Add-Error "Missing eval framework artifact: $evalFile"
        }
    }
    $evalCheckScript = Join-Path $repoRoot "tools/check_evals.ps1"
    if (Test-Path -LiteralPath $evalCheckScript) {
        & powershell -NoProfile -ExecutionPolicy Bypass -File $evalCheckScript
        if ($LASTEXITCODE -ne 0) {
            Add-Error "Eval framework check failed with exit code $LASTEXITCODE"
        }
    } else {
        Add-Error "Missing eval framework checker: tools/check_evals.ps1"
    }

    Test-ContainsText -Text $contract -Needle "Emoji Rule" -Label "core/AGENT-CONTRACT.yaml"
    Test-ContainsText -Text $contract -Needle "Communication Profiles" -Label "core/AGENT-CONTRACT.yaml"
    Test-ContainsText -Text $contract -Needle "epistemic_skeptic" -Label "core/AGENT-CONTRACT.yaml"
    Test-ContainsText -Text $contract -Needle "Tool-First YAML" -Label "core/AGENT-CONTRACT.yaml"
    Test-ContainsText -Text $contract -Needle "doc_item_migrate.ps1" -Label "core/AGENT-CONTRACT.yaml"
    Test-ContainsText -Text $contract -Needle "doc_item_bulk_insert.ps1" -Label "core/AGENT-CONTRACT.yaml"
    Test-ContainsText -Text $contract -Needle "transaction wrappers" -Label "core/AGENT-CONTRACT.yaml"
    Test-ContainsText -Text $contract -Needle "full-text grep tools" -Label "core/AGENT-CONTRACT.yaml"
    Test-ContainsText -Text $contract -Needle "doc_route.ps1" -Label "core/AGENT-CONTRACT.yaml"
    Test-ContainsText -Text $contract -Needle "## <emoji> Brief" -Label "core/AGENT-CONTRACT.yaml"
    Test-ContainsText -Text $contract -Needle "## <emoji> State" -Label "core/AGENT-CONTRACT.yaml"
    Test-ContainsText -Text $contract -Needle "## <emoji> Problem" -Label "core/AGENT-CONTRACT.yaml"
    Test-ContainsText -Text $contract -Needle "## <emoji> Suggestion" -Label "core/AGENT-CONTRACT.yaml"
    Test-ContainsText -Text $contract -Needle "## <emoji> Summary" -Label "core/AGENT-CONTRACT.yaml"
    Test-ContainsText -Text $contract -Needle "configured pipeline language" -Label "core/AGENT-CONTRACT.yaml"
    Test-ContainsText -Text $contract -Needle "Primary Known-Solutions Directive" -Label "core/AGENT-CONTRACT.yaml"
    Test-ContainsText -Text $contract -Needle "Profile-fit check" -Label "core/AGENT-CONTRACT.yaml"
    Test-ContainsText -Text $contract -Needle "ROI Picks" -Label "core/AGENT-CONTRACT.yaml"
    Test-ContainsText -Text $contract -Needle "SCRIPT-FALLBACK.yaml" -Label "core/AGENT-CONTRACT.yaml"
    Test-ContainsText -Text $contract -Needle "Build-vs-borrow discipline" -Label "core/AGENT-CONTRACT.yaml"
    Test-ContainsText -Text $contract -Needle "Future-fit check" -Label "core/AGENT-CONTRACT.yaml"
    Test-ContainsText -Text $contract -Needle "primary steer-direction" -Label "core/AGENT-CONTRACT.yaml"
    Test-ContainsText -Text $contract -Needle "AAA-grade architectural practices" -Label "core/AGENT-CONTRACT.yaml"
    Test-ContainsText -Text $contract -Needle "For programming bug reports" -Label "core/AGENT-CONTRACT.yaml"
    Test-ContainsText -Text $contract -Needle "DDD-ADIV" -Label "core/AGENT-CONTRACT.yaml"
    Test-ContainsText -Text $contract -Needle "core/PROMOTION-RULES.yaml" -Label "core/AGENT-CONTRACT.yaml"
    Test-ContainsText -Text $contract -Needle "core/FILE-FORMATS.yaml" -Label "core/AGENT-CONTRACT.yaml"
    Test-ContainsText -Text $fileFormats -Needle "Code Projects" -Label "core/FILE-FORMATS.yaml"
    Test-ContainsText -Text $fileFormats -Needle "YAML and JSON" -Label "core/FILE-FORMATS.yaml"
    Test-ContainsText -Text $contextCompaction -Needle "When to Recommend a Hard Reset" -Label "core/CONTEXT-COMPACTION.yaml"
    Test-ContainsText -Text $memoryModel -Needle "Branch-Scoped Active State" -Label "core/MEMORY-MODEL.yaml"
    Test-ContainsText -Text $activationCheck -Needle "Required Checks" -Label "core/ACTIVATION-CHECK.yaml"
    Test-ContainsText -Text $activationCheck -Needle "communication format" -Label "core/ACTIVATION-CHECK.yaml"
    Test-ContainsText -Text $activationCheck -Needle "emoji rule" -Label "core/ACTIVATION-CHECK.yaml"
    Test-ContainsText -Text $updateProtocol -Needle "Source Resolution" -Label "core/UPDATE-PROTOCOL.yaml"
    Test-ContainsText -Text $updateProtocol -Needle "pipeline.update_source" -Label "core/UPDATE-PROTOCOL.yaml"
    Test-ContainsText -Text $updateProtocol -Needle "update_pipeline_from_link.ps1" -Label "core/UPDATE-PROTOCOL.yaml"
    Test-ContainsText -Text $updateProtocol -Needle "reinitialize_pipeline.ps1" -Label "core/UPDATE-PROTOCOL.yaml"
    Test-ContainsText -Text $updateProtocol -Needle "pipeline_featurelist.json" -Label "core/UPDATE-PROTOCOL.yaml"
    Test-ContainsText -Text $updateProtocol -Needle "learn_pipeline_features.ps1" -Label "core/UPDATE-PROTOCOL.yaml"
    Test-ContainsText -Text $updateProtocol -Needle "open_pipeline_learning_issue.ps1" -Label "core/UPDATE-PROTOCOL.yaml"
    Test-ContainsText -Text $removalProtocol -Needle "remove_pipeline.ps1" -Label "core/REMOVAL-PROTOCOL.yaml"
    Test-ContainsText -Text $removalProtocol -Needle "Default Preservation" -Label "core/REMOVAL-PROTOCOL.yaml"
    Test-ContainsText -Text $projectProfile -Needle "Profile-Fit Check" -Label "core/PROJECT-PROFILE.yaml"
    Test-ContainsText -Text $roiBias -Needle "ROI Picks" -Label "core/ROI-BIAS.yaml"
    Test-ContainsText -Text $scriptFallback -Needle "Never claim a script ran when it did not run" -Label "core/SCRIPT-FALLBACK.yaml"
    Test-ContainsText -Text $taskWork -Needle "docs-tech/cache/current_task.yaml" -Label "core/TASK-WORK.yaml"
    Test-ContainsText -Text $taskWork -Needle "doc_item_migrate.ps1" -Label "core/TASK-WORK.yaml"
    Test-ContainsText -Text $instructionCapture -Needle "Defragmentation" -Label "core/INSTRUCTION-CAPTURE.yaml"
    Test-ContainsText -Text $instructionCapture -Needle "Cleaning Rules" -Label "core/INSTRUCTION-CAPTURE.yaml"

    Test-ContainsText -Text $promotionRules -Needle "BACKLOG to PLAN" -Label "core/PROMOTION-RULES.yaml"
    Test-ContainsText -Text $promotionRules -Needle "PLAN to STATE" -Label "core/PROMOTION-RULES.yaml"
    Test-ContainsText -Text $promotionRules -Needle "BRANCH STATE to durable memory" -Label "core/PROMOTION-RULES.yaml"
    Test-ContainsText -Text $promotionRules -Needle "PLAN or BACKLOG to DECISIONS" -Label "core/PROMOTION-RULES.yaml"
    Test-ContainsText -Text $promotionRules -Needle "context-docs/" -Label "core/PROMOTION-RULES.yaml"

    if ($codePackActive) {
        Test-ContainsText -Text $agents -Needle "project/code/COMMANDS.yaml" -Label "AGENTS.md"
        Test-ContainsText -Text $agents -Needle "project/code/WORKFLOW.yaml" -Label "AGENTS.md"
        Test-ContainsText -Text $agents -Needle "core/FILE-FORMATS.yaml" -Label "AGENTS.md"

        Test-ContainsText -Text $codePack -Needle "Required Reads for Code Projects" -Label "project/code/PACK.yaml"
        Test-ContainsText -Text $codePack -Needle "Profile-Aware Defaults" -Label "project/code/PACK.yaml"
        Test-ContainsText -Text $codePack -Needle "Organize code top-down" -Label "project/code/PACK.yaml"
        Test-ContainsText -Text $codePack -Needle "Known-Solution Bias" -Label "project/code/PACK.yaml"
        Test-ContainsText -Text $codePack -Needle "Script-First Automation Directive" -Label "project/code/PACK.yaml"
        Test-ContainsText -Text $codePack -Needle "Task Gating" -Label "project/code/PACK.yaml"
        Test-ContainsText -Text $codePack -Needle "Reporting" -Label "project/code/PACK.yaml"
        Test-ContainsText -Text $codePack -Needle "Use existing project scripts and pipeline tools whenever practical" -Label "project/code/PACK.yaml"
        Test-ContainsText -Text $codePack -Needle "doc_item_migrate.ps1" -Label "project/code/PACK.yaml"
        Test-ContainsText -Text $codePack -Needle "Architecture archetypes check" -Label "project/code/PACK.yaml"
        Test-ContainsText -Text $codePack -Needle "DDD alignment" -Label "project/code/PACK.yaml"
        Test-ContainsText -Text $codePack -Needle "Future-fit check" -Label "project/code/PACK.yaml"

        Test-ContainsText -Text $codeWorkflow -Needle "Command Classifier" -Label "project/code/WORKFLOW.yaml"
        Test-ContainsText -Text $codeWorkflow -Needle "Script-First Execution" -Label "project/code/WORKFLOW.yaml"
        Test-ContainsText -Text $codeWorkflow -Needle "Verification Boundary" -Label "project/code/WORKFLOW.yaml"
        Test-ContainsText -Text $codeWorkflow -Needle "doc_item_bulk_insert.ps1" -Label "project/code/WORKFLOW.yaml"
        Test-ContainsText -Text $codeWorkflow -Needle "transaction wrappers" -Label "project/code/WORKFLOW.yaml"
        Test-ContainsText -Text $codeWorkflow -Needle "Select-String" -Label "project/code/WORKFLOW.yaml"
        Test-ContainsText -Text $codeWorkflow -Needle "doc_search.ps1" -Label "project/code/WORKFLOW.yaml"
        Test-ContainsText -Text $codeWorkflow -Needle "AAA-grade architecture" -Label "project/code/WORKFLOW.yaml"
        Test-ContainsText -Text $codeWorkflow -Needle "For bug reports" -Label "project/code/WORKFLOW.yaml"
        Test-ContainsText -Text $codeWorkflow -Needle "Branch-Scoped Workflow" -Label "project/code/WORKFLOW.yaml"
        Test-ContainsText -Text $codeWorkflow -Needle "ROI Workflow" -Label "project/code/WORKFLOW.yaml"
        Test-ContainsText -Text $codeWorkflow -Needle "Task Work Tracking" -Label "project/code/WORKFLOW.yaml"
        Test-ContainsText -Text $codeWorkflow -Needle "Context Cost Control" -Label "project/code/WORKFLOW.yaml"
        Test-ContainsText -Text $branchMode -Needle "Branch Mode" -Label "project/code/BRANCH-MODE.yaml"
        Test-ContainsText -Text (Get-RepoText -RelativePath "project/generic/PACK.yaml") -Needle "steer-direction checkpoints" -Label "project/generic/PACK.yaml"
        Test-ContainsText -Text (Get-RepoText -RelativePath "project/personal/PACK.yaml") -Needle "steer-direction checkpoints" -Label "project/personal/PACK.yaml"
        Test-ContainsText -Text (Get-RepoText -RelativePath "project/creative/PACK.yaml") -Needle "steer-direction checkpoints" -Label "project/creative/PACK.yaml"

        foreach ($command in @("CONTINUE", "PLAN", "BUG", "REVIEW", "AUDIT", "FINISH", "COMMIT", "LOG", "DIAGNOSTICS", "PROMPT", "INSTRUCTIONS")) {
            Test-ContainsText -Text $codeCommands -Needle "## $command" -Label "project/code/COMMANDS.yaml"
        }

        Test-ContainsText -Text $codeRegistries -Needle "Bug Registry" -Label "project/code/REGISTRIES.yaml"
        Test-ContainsText -Text $codeRegistries -Needle "Solved Bug Registry" -Label "project/code/REGISTRIES.yaml"
        Test-ContainsText -Text $codeRegistries -Needle "Changelog Registry" -Label "project/code/REGISTRIES.yaml"

        Test-ContainsText -Text $dddAdiv -Needle "Domain-Driven" -Label "project/code/DDD-ADIV.yaml"
        Test-ContainsText -Text $dddAdiv -Needle "Architecture-Decisive" -Label "project/code/DDD-ADIV.yaml"
        Test-ContainsText -Text $dddAdiv -Needle "Invariant-Visible" -Label "project/code/DDD-ADIV.yaml"
        Test-ContainsText -Text $dddAdiv -Needle "Known-Solutions Alignment" -Label "project/code/DDD-ADIV.yaml"
        Test-ContainsText -Text $dddAdiv -Needle "future fit" -Label "project/code/DDD-ADIV.yaml"

        Test-ContainsText -Text $gitRules -Needle "Worktree Rules" -Label "project/code/GIT.yaml"
        Test-ContainsText -Text $frozenLayers -Needle "Default Contract" -Label "project/code/FROZEN-LAYERS.yaml"
        Test-ContainsText -Text $codeInstructionCapture -Needle "Code Sorting Rules" -Label "project/code/INSTRUCTION-CAPTURE.yaml"
        Test-ContainsText -Text $codeInstructionCapture -Needle "_PROMPTS.md" -Label "project/code/INSTRUCTION-CAPTURE.yaml"
        Test-ContainsText -Text $codeDiagnostics -Needle "Required Project Setup" -Label "project/code/DIAGNOSTICS.yaml"
        Test-ContainsText -Text $codeDiagnostics -Needle "tools/log_summary.ps1" -Label "project/code/DIAGNOSTICS.yaml"
        Test-ContainsText -Text $codeDiagnostics -Needle "DIAGNOSTICS-SUMMARY.json" -Label "project/code/DIAGNOSTICS.yaml"
        Test-ContainsText -Text $codeDiagnostics -Needle "Human-Readable Reporting" -Label "project/code/DIAGNOSTICS.yaml"

        foreach ($doc in @("docs/GETTING-STARTED.md", "docs/CODE-PROJECTS.md", "docs/MODES.md", "docs/IMPORT-EXISTING-PROJECT.md", "docs/PUBLIC-USAGE.md")) {
            if (-not (Test-Path -LiteralPath (Join-Path $repoRoot $doc))) {
                Add-Error "Missing user documentation: $doc"
            }
        }

        foreach ($tool in @("detect_project_stack.ps1", "set_directives.ps1", "update_pipeline_from_link.ps1", "remove_pipeline.ps1", "reinitialize_pipeline.ps1", "install_powershell.ps1", "upgrade_from_riftbound.ps1", "migrate_ai_pipeline.ps1", "check_runtime.py", "init_branch_memory.ps1", "init_task_work.ps1", "doc_post_edit.ps1", "doc_item_bulk_insert.ps1", "doc_item_migrate.ps1", "doc_item_move.ps1", "doc_item_insert.ps1", "sync_pipeline_featurelist.ps1", "learn_pipeline_features.ps1", "report_pipeline_learning.ps1", "open_pipeline_learning_issue.ps1", "check_pipeline_featurelist_update.ps1", "check_evals.ps1")) {
            if (-not (Test-Path -LiteralPath (Join-Path $repoRoot "tools/$tool"))) {
                Add-Error "Missing public pipeline tool: tools/$tool"
            }
        }
        foreach ($tool in @("recompile_ai_instructions.ps1", "check_compiled_instructions.ps1")) {
            if (-not (Test-Path -LiteralPath (Join-Path $repoRoot "tools/$tool"))) {
                Add-Error "Missing compiled-instructions tool: tools/$tool"
            }
        }
        foreach ($template in @("templates/_PROMPTS.md", "templates/code/_PROMPT-QUEUE.yaml", "templates/code/current_task.yaml", "templates/code/branch/BRANCH-STATE.md", "templates/code/branch/BRANCH-PLAN.md", "templates/code/branch/BRANCH-TODO.md")) {
            if (-not (Test-Path -LiteralPath (Join-Path $repoRoot $template))) {
                Add-Error "Missing prompt workflow template: $template"
            }
        }
        foreach ($template in @("templates/ORCHESTRATION.yaml", "templates/team/product.yaml", "templates/team/technical.yaml", "templates/team/performance.yaml", "templates/team/experience.yaml", "templates/team/pipeline.yaml")) {
            if (-not (Test-Path -LiteralPath (Join-Path $repoRoot $template))) {
                Add-Error "Missing orchestration/team template: $template"
            }
        }
        foreach ($template in @("templates/DOCS.yaml", "templates/STATE.md", "templates/_PLAN.md", "templates/BACKLOG.md", "templates/DECISIONS.md", "templates/ISSUES.md", "templates/JOURNAL.md", "templates/REVIEW.md", "templates/PIPELINE-CONFIG.yaml")) {
            if (-not (Test-Path -LiteralPath (Join-Path $repoRoot $template))) {
                Add-Error "Missing non-code user-facing template: $template"
            }
        }
        if (-not (Test-Path -LiteralPath (Join-Path $repoRoot "templates/code/DOCS.yaml"))) {
            Add-Error "Missing code document role template: templates/code/DOCS.yaml"
        }
        $pipelineConfigTemplate = Get-RepoText -RelativePath "templates/code/PIPELINE-CONFIG.yaml"
        Test-ContainsText -Text $pipelineConfigTemplate -Needle "project_profile:" -Label "templates/code/PIPELINE-CONFIG.yaml"
        Test-ContainsText -Text $pipelineConfigTemplate -Needle "runtime_status:" -Label "templates/code/PIPELINE-CONFIG.yaml"
        Test-ContainsText -Text $pipelineConfigTemplate -Needle "install_supported:" -Label "templates/code/PIPELINE-CONFIG.yaml"
        Test-ContainsText -Text $pipelineConfigTemplate -Needle "fallback_recommendation:" -Label "templates/code/PIPELINE-CONFIG.yaml"
        Test-ContainsText -Text $pipelineConfigTemplate -Needle "branch_mode:" -Label "templates/code/PIPELINE-CONFIG.yaml"
        Test-ContainsText -Text $pipelineConfigTemplate -Needle "update_source:" -Label "templates/code/PIPELINE-CONFIG.yaml"
        Test-ContainsText -Text $pipelineConfigTemplate -Needle "remove_command:" -Label "templates/code/PIPELINE-CONFIG.yaml"
        Test-ContainsText -Text $pipelineConfigTemplate -Needle "reinitialize_command:" -Label "templates/code/PIPELINE-CONFIG.yaml"
        Test-ContainsText -Text $pipelineConfigTemplate -Needle "changelog:" -Label "templates/code/PIPELINE-CONFIG.yaml"
        Test-ContainsText -Text $pipelineConfigTemplate -Needle "communication:" -Label "templates/code/PIPELINE-CONFIG.yaml"
        Test-ContainsText -Text $pipelineConfigTemplate -Needle "profile: standard" -Label "templates/code/PIPELINE-CONFIG.yaml"
        Test-ContainsText -Text (Get-RepoText -RelativePath "tools/set_directives.ps1") -Needle ".old" -Label "tools/set_directives.ps1"
        Test-ContainsText -Text (Get-RepoText -RelativePath "tools/set_directives.ps1") -Needle "SOCRATEX.md" -Label "tools/set_directives.ps1"
        Test-ContainsText -Text (Get-RepoText -RelativePath "tools/Initialize-SocratexPipeline.ps1") -Needle "ORCHESTRATION.yaml" -Label "tools/Initialize-SocratexPipeline.ps1"
        Test-ContainsText -Text (Get-RepoText -RelativePath "tools/Initialize-SocratexPipeline.ps1") -Needle "team\pipeline.yaml" -Label "tools/Initialize-SocratexPipeline.ps1"
        Test-ContainsText -Text (Get-RepoText -RelativePath "tools/import_existing_project.ps1") -Needle "ORCHESTRATION.yaml" -Label "tools/import_existing_project.ps1"
        Test-ContainsText -Text (Get-RepoText -RelativePath "tools/import_existing_project.ps1") -Needle "team/pipeline.yaml" -Label "tools/import_existing_project.ps1"
        Test-ContainsText -Text (Get-RepoText -RelativePath "tools/reinitialize_pipeline.ps1") -Needle "ORCHESTRATION.yaml" -Label "tools/reinitialize_pipeline.ps1"
        Test-ContainsText -Text (Get-RepoText -RelativePath "tools/reinitialize_pipeline.ps1") -Needle "team/pipeline.yaml" -Label "tools/reinitialize_pipeline.ps1"
    }

    if ($Initialized) {
        $requiredInitializedFiles = if ($codePackActive) {
            @("DOCS.yaml", "STATE.yaml", "_PLAN.yaml", "DECISIONS.yaml", "PIPELINE-CONFIG.yaml")
        } else {
            @("DOCS.yaml", "STATE.md", "_PLAN.md", "DECISIONS.md", "PIPELINE-CONFIG.yaml")
        }

        foreach ($requiredFile in $requiredInitializedFiles) {
            if (-not (Test-Path -LiteralPath (Join-Path $repoRoot $requiredFile))) {
                Add-Error "Initialized project is missing required file: $requiredFile"
            }
        }

        if (Test-Path -LiteralPath (Join-Path $repoRoot "initializer/FIRST-RUN.md")) {
            Add-Warning "Initialized audit found initializer/FIRST-RUN.md still present; move initializer to temp/trash after first run."
        }

        if ($codePackActive) {
            foreach ($tool in @("task_snapshot.ps1", "run_quality_gate.ps1", "finish_task.ps1", "commit_task.ps1", "compile_agent_instructions.ps1", "log_summary.ps1", "wizard.ps1", "import_existing_project.ps1")) {
                if (-not (Test-Path -LiteralPath (Join-Path $repoRoot "tools/$tool"))) {
                    Add-Error "Initialized code project is missing tool: tools/$tool"
                }
            }
        }
    }

    $markdownFiles = @(
        Get-ChildItem -LiteralPath $repoRoot -Filter "*.md" -File
        Get-ChildItem -LiteralPath (Join-Path $repoRoot "core") -Filter "*.md" -File -ErrorAction SilentlyContinue
        Get-ChildItem -LiteralPath (Join-Path $repoRoot "project") -Filter "*.md" -File -Recurse -ErrorAction SilentlyContinue
        Get-ChildItem -LiteralPath (Join-Path $repoRoot "adapters") -Filter "*.md" -File -Recurse -ErrorAction SilentlyContinue
        Get-ChildItem -LiteralPath (Join-Path $repoRoot "templates") -Filter "*.md" -File -ErrorAction SilentlyContinue
        Get-ChildItem -LiteralPath (Join-Path $repoRoot "docs") -Filter "*.md" -File -ErrorAction SilentlyContinue
    )

    foreach ($file in $markdownFiles) {
        Test-OpeningTocEmoji -File $file
    }

    Test-FileSoftLimit -RelativePath "STATE.yaml" -SoftLimit $StateSoftLimit -Purpose "active state should stay compact"
    Test-FileSoftLimit -RelativePath "STATE.md" -SoftLimit $StateSoftLimit -Purpose "active state should stay compact"
    Test-FileSoftLimit -RelativePath "core/AGENT-CONTRACT.yaml" -SoftLimit 340 -Purpose "the shared contract should stay readable through thin adapters"

    if ((Test-Path -LiteralPath "_PLAN.yaml") -and -not ((Get-Content -Raw -LiteralPath "_PLAN.yaml") -match 'pass_index')) {
        Add-Warning "_PLAN.yaml does not mention pass_index."
    }

    if ((Test-Path -LiteralPath "_PLAN.md") -and -not ((Get-Content -Raw -LiteralPath "_PLAN.md") -match 'Pass Index')) {
        Add-Warning "_PLAN.md does not mention Pass Index."
    }


    foreach ($warning in $warnings) {
        Write-Host "WARNING: $warning"
    }

    if ($Strict -and $warnings.Count -gt 0) {
        foreach ($warning in $warnings) {
            Add-Error "Strict mode warning promoted to error: $warning"
        }
    }

    if ($errors.Count -gt 0) {
        foreach ($issue in $errors) {
            Write-Host "ERROR: $issue"
        }

        throw "audit docs failed with $($errors.Count) error(s)."
    }

    Write-Host "OK: audit docs passed with $($warnings.Count) warning(s)."
} finally {
    Pop-Location
}
