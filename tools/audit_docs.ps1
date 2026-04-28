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
    $contract = Get-RepoText -RelativePath "core/AGENT-CONTRACT.md"
    $fileFormats = Get-RepoText -RelativePath "core/FILE-FORMATS.md"
    $promotionRules = Get-RepoText -RelativePath "core/PROMOTION-RULES.md"
    $contextCompaction = Get-RepoText -RelativePath "core/CONTEXT-COMPACTION.md"
    $instructionCapture = Get-RepoText -RelativePath "core/INSTRUCTION-CAPTURE.md"
    $codePackActive = Test-Path -LiteralPath (Join-Path $repoRoot "project/code/PACK.md")
    $codePack = if ($codePackActive) { Get-RepoText -RelativePath "project/code/PACK.md" } else { "" }
    $codeWorkflow = if ($codePackActive) { Get-RepoText -RelativePath "project/code/WORKFLOW.md" } else { "" }
    $codeCommands = if ($codePackActive) { Get-RepoText -RelativePath "project/code/COMMANDS.md" } else { "" }
    $codeRegistries = if ($codePackActive) { Get-RepoText -RelativePath "project/code/REGISTRIES.md" } else { "" }
    $dddAdiv = if ($codePackActive) { Get-RepoText -RelativePath "project/code/DDD-ADIV.md" } else { "" }
    $gitRules = if ($codePackActive) { Get-RepoText -RelativePath "project/code/GIT.md" } else { "" }
    $frozenLayers = if ($codePackActive) { Get-RepoText -RelativePath "project/code/FROZEN-LAYERS.md" } else { "" }
    $codeInstructionCapture = if ($codePackActive) { Get-RepoText -RelativePath "project/code/INSTRUCTION-CAPTURE.md" } else { "" }
    $codeDiagnostics = if ($codePackActive) { Get-RepoText -RelativePath "project/code/DIAGNOSTICS.md" } else { "" }

    Test-ContainsText -Text $agents -Needle "core/AGENT-CONTRACT.md" -Label "AGENTS.md"
    Test-ContainsText -Text $agents -Needle "core/PROMOTION-RULES.md" -Label "AGENTS.md"
    Test-ContainsText -Text (Get-RepoText -RelativePath "PUBLIC-BOOTSTRAP.md") -Needle "Programming Questions" -Label "PUBLIC-BOOTSTRAP.md"
    Test-ContainsText -Text (Get-RepoText -RelativePath "PUBLIC-BOOTSTRAP.md") -Needle "Update, Upgrade, Migrate" -Label "PUBLIC-BOOTSTRAP.md"
    Test-ContainsText -Text (Get-RepoText -RelativePath "PUBLIC-BOOTSTRAP.md") -Needle "Directive Merge Modes" -Label "PUBLIC-BOOTSTRAP.md"
    Test-ContainsText -Text (Get-RepoText -RelativePath "templates/SOCRATEX.md") -Needle "SocratexAI/" -Label "templates/SOCRATEX.md"
    Test-ContainsText -Text (Get-RepoText -RelativePath "VERSION") -Needle "0.1.0-alpha" -Label "VERSION"
    Test-ContainsText -Text (Get-RepoText -RelativePath "LICENSE") -Needle "MIT License" -Label "LICENSE"
    Test-ContainsText -Text (Get-RepoText -RelativePath "QUALITY-GATE.yaml") -Needle "audit_docs" -Label "QUALITY-GATE.yaml"
    Test-ContainsText -Text (Get-RepoText -RelativePath "docs/CI-SELF-CHECK.md") -Needle "Provider Guidance" -Label "docs/CI-SELF-CHECK.md"

    Test-ContainsText -Text $contract -Needle "Emoji Rule" -Label "core/AGENT-CONTRACT.md"
    Test-ContainsText -Text $contract -Needle "## <emoji> Brief" -Label "core/AGENT-CONTRACT.md"
    Test-ContainsText -Text $contract -Needle "## <emoji> State" -Label "core/AGENT-CONTRACT.md"
    Test-ContainsText -Text $contract -Needle "## <emoji> Problem" -Label "core/AGENT-CONTRACT.md"
    Test-ContainsText -Text $contract -Needle "## <emoji> Suggestion" -Label "core/AGENT-CONTRACT.md"
    Test-ContainsText -Text $contract -Needle "## <emoji> Summary" -Label "core/AGENT-CONTRACT.md"
    Test-ContainsText -Text $contract -Needle "configured pipeline language" -Label "core/AGENT-CONTRACT.md"
    Test-ContainsText -Text $contract -Needle "Primary Known-Solutions Directive" -Label "core/AGENT-CONTRACT.md"
    Test-ContainsText -Text $contract -Needle "Build-vs-borrow discipline" -Label "core/AGENT-CONTRACT.md"
    Test-ContainsText -Text $contract -Needle "Future-fit check" -Label "core/AGENT-CONTRACT.md"
    Test-ContainsText -Text $contract -Needle "DDD-ADIV" -Label "core/AGENT-CONTRACT.md"
    Test-ContainsText -Text $contract -Needle "core/PROMOTION-RULES.md" -Label "core/AGENT-CONTRACT.md"
    Test-ContainsText -Text $contract -Needle "core/FILE-FORMATS.md" -Label "core/AGENT-CONTRACT.md"
    Test-ContainsText -Text $fileFormats -Needle "Code Projects" -Label "core/FILE-FORMATS.md"
    Test-ContainsText -Text $fileFormats -Needle "YAML and JSON" -Label "core/FILE-FORMATS.md"
    Test-ContainsText -Text $contextCompaction -Needle "When to Recommend a Hard Reset" -Label "core/CONTEXT-COMPACTION.md"
    Test-ContainsText -Text $instructionCapture -Needle "Defragmentation" -Label "core/INSTRUCTION-CAPTURE.md"
    Test-ContainsText -Text $instructionCapture -Needle "Cleaning Rules" -Label "core/INSTRUCTION-CAPTURE.md"

    Test-ContainsText -Text $promotionRules -Needle "BACKLOG to PLAN" -Label "core/PROMOTION-RULES.md"
    Test-ContainsText -Text $promotionRules -Needle "PLAN to STATE" -Label "core/PROMOTION-RULES.md"
    Test-ContainsText -Text $promotionRules -Needle "PLAN or BACKLOG to DECISIONS" -Label "core/PROMOTION-RULES.md"
    Test-ContainsText -Text $promotionRules -Needle "context-docs/" -Label "core/PROMOTION-RULES.md"

    if ($codePackActive) {
        Test-ContainsText -Text $agents -Needle "project/code/COMMANDS.md" -Label "AGENTS.md"
        Test-ContainsText -Text $agents -Needle "project/code/WORKFLOW.md" -Label "AGENTS.md"
        Test-ContainsText -Text $agents -Needle "core/FILE-FORMATS.md" -Label "AGENTS.md"

        Test-ContainsText -Text $codePack -Needle "Required Reads for Code Projects" -Label "project/code/PACK.md"
        Test-ContainsText -Text $codePack -Needle "Organize code top-down" -Label "project/code/PACK.md"
        Test-ContainsText -Text $codePack -Needle "Known-Solution Bias" -Label "project/code/PACK.md"
        Test-ContainsText -Text $codePack -Needle "Script-First Automation Directive" -Label "project/code/PACK.md"
        Test-ContainsText -Text $codePack -Needle "Task Gating" -Label "project/code/PACK.md"
        Test-ContainsText -Text $codePack -Needle "Reporting" -Label "project/code/PACK.md"
        Test-ContainsText -Text $codePack -Needle "Use existing project scripts and pipeline tools whenever practical" -Label "project/code/PACK.md"
        Test-ContainsText -Text $codePack -Needle "Architecture archetypes check" -Label "project/code/PACK.md"
        Test-ContainsText -Text $codePack -Needle "DDD alignment" -Label "project/code/PACK.md"
        Test-ContainsText -Text $codePack -Needle "Future-fit check" -Label "project/code/PACK.md"

        Test-ContainsText -Text $codeWorkflow -Needle "Command Classifier" -Label "project/code/WORKFLOW.md"
        Test-ContainsText -Text $codeWorkflow -Needle "Script-First Execution" -Label "project/code/WORKFLOW.md"
        Test-ContainsText -Text $codeWorkflow -Needle "Context Cost Control" -Label "project/code/WORKFLOW.md"

        foreach ($command in @("CONTINUE", "PLAN", "BUG", "REVIEW", "AUDIT", "FINISH", "COMMIT", "LOG", "DIAGNOSTICS", "PROMPT", "INSTRUCTIONS")) {
            Test-ContainsText -Text $codeCommands -Needle "## $command" -Label "project/code/COMMANDS.md"
        }

        Test-ContainsText -Text $codeRegistries -Needle "Bug Registry" -Label "project/code/REGISTRIES.md"
        Test-ContainsText -Text $codeRegistries -Needle "Solved Bug Registry" -Label "project/code/REGISTRIES.md"
        Test-ContainsText -Text $codeRegistries -Needle "Changelog Registry" -Label "project/code/REGISTRIES.md"

        Test-ContainsText -Text $dddAdiv -Needle "Domain-Driven" -Label "project/code/DDD-ADIV.md"
        Test-ContainsText -Text $dddAdiv -Needle "Architecture-Decisive" -Label "project/code/DDD-ADIV.md"
        Test-ContainsText -Text $dddAdiv -Needle "Invariant-Visible" -Label "project/code/DDD-ADIV.md"
        Test-ContainsText -Text $dddAdiv -Needle "Known-Solutions Alignment" -Label "project/code/DDD-ADIV.md"
        Test-ContainsText -Text $dddAdiv -Needle "future fit" -Label "project/code/DDD-ADIV.md"

        Test-ContainsText -Text $gitRules -Needle "Worktree Rules" -Label "project/code/GIT.md"
        Test-ContainsText -Text $frozenLayers -Needle "Default Contract" -Label "project/code/FROZEN-LAYERS.md"
        Test-ContainsText -Text $codeInstructionCapture -Needle "Code Sorting Rules" -Label "project/code/INSTRUCTION-CAPTURE.md"
        Test-ContainsText -Text $codeInstructionCapture -Needle "_PROMPTS.md" -Label "project/code/INSTRUCTION-CAPTURE.md"
        Test-ContainsText -Text $codeDiagnostics -Needle "Required Project Setup" -Label "project/code/DIAGNOSTICS.md"
        Test-ContainsText -Text $codeDiagnostics -Needle "tools/log_summary.ps1" -Label "project/code/DIAGNOSTICS.md"
        Test-ContainsText -Text $codeDiagnostics -Needle "DIAGNOSTICS-SUMMARY.json" -Label "project/code/DIAGNOSTICS.md"
        Test-ContainsText -Text $codeDiagnostics -Needle "Human-Readable Reporting" -Label "project/code/DIAGNOSTICS.md"

        foreach ($doc in @("docs/GETTING-STARTED.md", "docs/CODE-PROJECTS.md", "docs/MODES.md", "docs/IMPORT-EXISTING-PROJECT.md", "docs/PUBLIC-USAGE.md")) {
            if (-not (Test-Path -LiteralPath (Join-Path $repoRoot $doc))) {
                Add-Error "Missing user documentation: $doc"
            }
        }

        foreach ($tool in @("detect_project_stack.ps1", "set_directives.ps1", "update_pipeline_from_link.ps1", "upgrade_from_riftbound.ps1", "migrate_ai_pipeline.ps1")) {
            if (-not (Test-Path -LiteralPath (Join-Path $repoRoot "tools/$tool"))) {
                Add-Error "Missing public pipeline tool: tools/$tool"
            }
        }
        foreach ($template in @("templates/_PROMPTS.md", "templates/code/_PROMPT-QUEUE.yaml")) {
            if (-not (Test-Path -LiteralPath (Join-Path $repoRoot $template))) {
                Add-Error "Missing prompt workflow template: $template"
            }
        }
        Test-ContainsText -Text (Get-RepoText -RelativePath "tools/set_directives.ps1") -Needle ".old" -Label "tools/set_directives.ps1"
        Test-ContainsText -Text (Get-RepoText -RelativePath "tools/set_directives.ps1") -Needle "SOCRATEX.md" -Label "tools/set_directives.ps1"
    }

    if ($Initialized) {
        $requiredInitializedFiles = if ($codePackActive) {
            @("STATE.yaml", "_PLAN.yaml", "DECISIONS.yaml", "PIPELINE-CONFIG.yaml")
        } else {
            @("STATE.md", "_PLAN.md", "DECISIONS.md", "PIPELINE-CONFIG.md")
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
    Test-FileSoftLimit -RelativePath "core/AGENT-CONTRACT.md" -SoftLimit 220 -Purpose "the shared contract should stay readable through thin adapters"

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
