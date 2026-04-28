param(
	[string]$IndexPath = "docs-tech/CODE_LINE_INDEX.json",
	[string]$LargeFilesPath = "docs-tech/LARGE_FILES.yaml",
	[int]$LargeFileThreshold = 300,
	[string[]]$Paths = @(),
	[switch]$ChangedOnly,
	[switch]$Check
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$repoRoot = Resolve-Path -LiteralPath (Join-Path $PSScriptRoot "..")
$utf8NoBom = [System.Text.UTF8Encoding]::new($false)
$codeExtensions = @(
	".gd",
	".ps1",
	".py",
	".bat",
	".cmd",
	".sh",
	".cs",
	".js",
	".ts"
)

function ConvertTo-RepoPath {
	param([string]$Path)

	$fullPath = [System.IO.Path]::GetFullPath((Join-Path $repoRoot $Path))
	$root = [System.IO.Path]::GetFullPath($repoRoot)
	if (-not $root.EndsWith([System.IO.Path]::DirectorySeparatorChar)) {
		$root = "$root$([System.IO.Path]::DirectorySeparatorChar)"
	}
	if (-not $fullPath.StartsWith($root, [System.StringComparison]::OrdinalIgnoreCase)) {
		throw "Path is outside repo: $Path"
	}
	return $fullPath.Substring($root.Length).Replace("\", "/")
}

function Test-CodePath {
	param([string]$Path)

	$extension = [System.IO.Path]::GetExtension($Path).ToLowerInvariant()
	if (-not $codeExtensions.Contains($extension)) {
		return $false
	}

	$normalized = $Path.Replace("\", "/")
	return -not (
		$normalized.StartsWith("Tools/Python") -or
		$normalized.StartsWith("Tools/python-installer") -or
		$normalized.StartsWith("Tools/tmp/") -or
		$normalized.StartsWith(".venv/") -or
		$normalized.StartsWith("build/")
	)
}

function Get-TrackedCodePaths {
	$tracked = @(git -C $repoRoot ls-files)
	if ($LASTEXITCODE -ne 0) {
		throw "git ls-files failed."
	}
	$untracked = @(git -C $repoRoot ls-files --others --exclude-standard)
	if ($LASTEXITCODE -ne 0) {
		throw "git ls-files --others failed."
	}
	return @($tracked + $untracked | Where-Object { Test-CodePath -Path $_ } | Sort-Object -Unique)
}

function Get-ChangedCodePaths {
	$changed = @(git -C $repoRoot diff --name-only)
	if ($LASTEXITCODE -ne 0) {
		throw "git diff failed."
	}
	$changed += @(git -C $repoRoot diff --cached --name-only)
	if ($LASTEXITCODE -ne 0) {
		throw "git diff --cached failed."
	}
	$changed += @(git -C $repoRoot ls-files --others --exclude-standard)
	if ($LASTEXITCODE -ne 0) {
		throw "git ls-files --others failed."
	}
	return @($changed | Where-Object { Test-CodePath -Path $_ } | Sort-Object -Unique)
}

function Get-ExplicitCodePaths {
	$expanded = New-Object System.Collections.Generic.List[string]
	foreach ($path in $Paths) {
		foreach ($candidate in ($path -split ",")) {
			$trimmed = $candidate.Trim()
			if ($trimmed.Length -eq 0) {
				continue
			}
			$repoPath = ConvertTo-RepoPath -Path $trimmed
			if (Test-CodePath -Path $repoPath) {
				$expanded.Add($repoPath) | Out-Null
			}
		}
	}
	return @($expanded | Sort-Object -Unique)
}

function Get-CodeLineCount {
	param([string]$RepoPath)

	$path = Join-Path $repoRoot $RepoPath
	if (-not (Test-Path -LiteralPath $path -PathType Leaf)) {
		return $null
	}

	$count = 0
	$stream = [System.IO.FileStream]::new(
		$path,
		[System.IO.FileMode]::Open,
		[System.IO.FileAccess]::Read,
		[System.IO.FileShare]::ReadWrite
	)
	try {
		$reader = [System.IO.StreamReader]::new($stream, [System.Text.Encoding]::UTF8, $true)
		try {
			while (-not $reader.EndOfStream) {
				$line = $reader.ReadLine()
				if (-not [string]::IsNullOrWhiteSpace($line)) {
					$count += 1
				}
			}
		} finally {
			$reader.Dispose()
		}
	} finally {
		$stream.Dispose()
	}
	return $count
}

function Read-Index {
	param([string]$Path)

	$fullPath = Join-Path $repoRoot $Path
	if (-not (Test-Path -LiteralPath $fullPath -PathType Leaf)) {
		return [ordered]@{
			generatedAt = $null
			threshold = $LargeFileThreshold
			files = @()
		}
	}

	return Get-Content -Raw -LiteralPath $fullPath -Encoding UTF8 | ConvertFrom-Json
}

function ConvertTo-IndexObject {
	param([object]$Index)

	$records = @{}
	if ($null -ne $Index.files) {
		foreach ($record in $Index.files) {
			$records[[string]$record.path] = [ordered]@{
				path = [string]$record.path
				lines = [int]$record.lines
				extension = [string]$record.extension
				large = [bool]$record.large
			}
		}
	}

	return $records
}

function Build-IndexPayload {
	param(
		[hashtable]$Records,
		[string]$GeneratedAt = $null
	)

	$files = @(
		$Records.Values |
			ForEach-Object { [pscustomobject]$_ } |
			Sort-Object @{ Expression = "lines"; Descending = $true }, @{ Expression = "path"; Descending = $false }
	)

	$timestamp = $GeneratedAt
	if ([string]::IsNullOrWhiteSpace($timestamp)) {
		$timestamp = (Get-Date).ToString("yyyy-MM-ddTHH:mm:sszzz")
	}

	return [ordered]@{
		generatedAt = $timestamp
		threshold = $LargeFileThreshold
		files = $files
	}
}

function Get-LargeFileNote {
	param([string]$Path)

	$notes = @{
		"Game/scripts/world/domain/world_traversal_grammar_contract.gd" = "Traversal grammar source for generated routes, branch shapes, affordance rules, and terrain-readable structure data. It is large because it currently keeps the route vocabulary and generation constraints together as one explicit contract."
		"Game/scripts/world/infrastructure/world_generator.gd" = "World generator coordinator for deterministic route, chunk, biome, and payload construction. It is large because several generation stages still need a single traceable orchestration path while worldgen contracts are evolving."
		"Game/scripts/runtime/application/game_root_controller.gd" = "Runtime orchestration hub that wires debug capture, camera/runtime coordination, save/report helpers, and high-level gameplay services. It is large because it still owns several cross-cutting runtime integration points that should only be split when a stable boundary is obvious."
		"Game/scripts/player/domain/player_movement_runtime.gd" = "Player movement-state runtime for acceleration, jumping, slopes, contact, and feel-critical movement values. It is large because movement feel is still being tuned and the state transitions need to remain mechanically traceable."
		"Game/scripts/ui/view/main_menu_controller.gd" = "Main menu and character/setup UI controller. It is large because one scene controller still owns several menu modes and input/view transitions."
		"Game/scripts/player/application/player_controller.gd" = "Player movement, combat hooks, input application, and runtime state coordination. It is large because player feel is still under active iteration and premature splitting could obscure the control flow."
		"Game/scripts/enemies/application/enemy_director.gd" = "Enemy spawning, activation, lifecycle, and runtime coordination layer. It is large because enemy orchestration still crosses spawn data, pooling, runtime state, and progression-facing behavior."
		"Game/scripts/world/domain/world_generation_pipeline.gd" = "World generation orchestration pipeline. It is large because it coordinates route data, biome data, chunk payloads, and deterministic generation contracts."
		"Game/scripts/world/application/world_runtime_application.gd" = "Application-facing world runtime coordinator. It is large because it bridges generated world data, active chunk lifecycle, debug hooks, and presentation/runtime services."
		"Game/scripts/world/infrastructure/world_procedural_structure_pass.gd" = "Procedural structure generation pass for data-backed world dressing and silhouettes. It is large because structure placement still shares deterministic context, biome rules, and payload output in one pass."
		"Game/scripts/world/application/world_controller.gd" = "World scene controller that applies generated data to active runtime nodes. It is large because it coordinates chunk presentation, lifecycle, and world-facing runtime state."
		"Game/scripts/ui/view/gameplay_hud_controller.gd" = "Gameplay HUD controller for player-facing status, overlays, and runtime UI state. It is large because HUD presentation still aggregates several gameplay domains into one screen controller."
		"Game/scripts/world/domain/world_biome_field_contract.gd" = "Biome field contract for deterministic biome sampling and region-level biome data. It is large because it holds the explicit data shape used by generation, diagnostics, and chunk-level consumers."
		"Game/scripts/world/view/fragments/platform_fragment.gd" = "Platform fragment view/runtime script for generated platform presentation and collision behavior. It is large because fragment setup, material/state application, and editor/runtime behavior are still colocated."
		"Game/test-scripts/terrain_profile_probe.gd" = "Terrain profile diagnostic probe for biome terrain shape, slope, and affordance validation. It is large because it collects broad diagnostic summaries rather than serving as runtime gameplay code."
		"Game/scripts/world/domain/world_biome_region_planner_contract.gd" = "Biome region planner contract for macro-region spans, shape scale, centers, and neighbor relationships. It is large because it documents and computes deterministic biome-region planning data in one place."
		"Game/scripts/world/domain/world_map_runtime.gd" = "Runtime map/discovery state for world map data and explored chunk information. It is large because map state currently combines discovery bookkeeping, persistence-facing payloads, and query helpers."
		"Game/scripts/runtime/application/modes/rift_mode_controller.gd" = "Rift gameplay mode controller for mode lifecycle and runtime coordination. It is large because it owns mode-specific setup, transitions, and gameplay-facing services."
		"Game/scripts/runtime/domain/game_session.gd" = "Session progression and run-state domain model. It is large because progression, pickups, upgrades, and run summary state are still represented in one explicit session contract."
	}

	if ($notes.ContainsKey($Path)) {
		return $notes[$Path]
	}

	$extension = [System.IO.Path]::GetExtension($Path)
	switch ($extension) {
		".gd" { return "Godot gameplay/runtime script above the size threshold. Keep it documented here until the ownership boundary is clear enough to split without hiding flow." }
		".ps1" { return "Repository automation script above the size threshold. Keep it documented here because it encodes workflow behavior used by Codex or local tooling." }
		".py" { return "Repository helper script above the size threshold. Keep it documented here because it performs non-trivial tooling logic." }
		default { return "Code file above the size threshold. Keep it documented here until it can be reduced or split cleanly." }
	}
}

function Get-Emoji {
	param([int]$CodePoint)

	return [char]::ConvertFromUtf32($CodePoint)
}

function Add-YamlLiteralBlock {
	param(
		[System.Collections.Generic.List[string]]$Lines,
		[string]$Key,
		[string[]]$Content,
		[int]$Indent = 4
	)

	$prefix = " " * $Indent
	$Lines.Add("${prefix}${Key}: |") | Out-Null
	foreach ($line in $Content) {
		if ([string]::IsNullOrEmpty($line)) {
			$Lines.Add("") | Out-Null
		} else {
			$Lines.Add("$prefix  $line") | Out-Null
		}
	}
}

function Build-LargeFilesDocument {
	param([object[]]$LargeRecords)

	$rulerEmoji = Get-Emoji -CodePoint 0x1F4CF
	$pinEmoji = Get-Emoji -CodePoint 0x1F4CC
	$chartEmoji = Get-Emoji -CodePoint 0x1F4CA
	$toolEmoji = Get-Emoji -CodePoint 0x1F6E0

	$tableLines = New-Object System.Collections.Generic.List[string]
	$tableLines.Add("$chartEmoji Current files above $LargeFileThreshold non-empty code lines.") | Out-Null
	$tableLines.Add("") | Out-Null
	$tableLines.Add("| Lines | File | Why It Is Large |") | Out-Null
	$tableLines.Add("| ---: | --- | --- |") | Out-Null

	if ($LargeRecords.Count -eq 0) {
		$tableLines.Add("| 0 | _(none)_ | No tracked code files exceed the threshold. |") | Out-Null
	} else {
		foreach ($record in $LargeRecords) {
			$path = [string]$record.path
			$linesCount = [int]$record.lines
			$note = Get-LargeFileNote -Path $path
			$tableLines.Add("| $linesCount | ``$path`` | $note |") | Out-Null
		}
	}

	$lines = New-Object System.Collections.Generic.List[string]
	$lines.Add("index:") | Out-Null
	$lines.Add("- quick_index") | Out-Null
	$lines.Add("- summary") | Out-Null
	$lines.Add("- large_file_index") | Out-Null
	$lines.Add("- maintenance") | Out-Null
	$lines.Add("items:") | Out-Null
	$lines.Add("  quick_index:") | Out-Null
	$lines.Add("    title: Quick Index") | Out-Null
	Add-YamlLiteralBlock -Lines $lines -Key "content" -Indent 4 -Content @(
		"- $pinEmoji Summary",
		"- $chartEmoji Large File Index",
		"- $toolEmoji Maintenance"
	)
	$lines.Add("  summary:") | Out-Null
	$lines.Add("    title: $pinEmoji Summary") | Out-Null
	Add-YamlLiteralBlock -Lines $lines -Key "content" -Indent 4 -Content @(
		"$pinEmoji Generated index of code files above the large-file threshold.",
		"",
		"$pinEmoji This document is generated from ``docs-tech/CODE_LINE_INDEX.json`` by ``Tools/update_code_line_index.ps1``. It tracks code files above $LargeFileThreshold non-empty lines so large files have an explicit reason to stay large or a visible reason to split later."
	)
	$lines.Add("  large_file_index:") | Out-Null
	$lines.Add("    title: $chartEmoji Large File Index") | Out-Null
	Add-YamlLiteralBlock -Lines $lines -Key "content" -Indent 4 -Content @($tableLines)
	$lines.Add("  maintenance:") | Out-Null
	$lines.Add("    title: $toolEmoji Maintenance") | Out-Null
	Add-YamlLiteralBlock -Lines $lines -Key "content" -Indent 4 -Content @(
		"$toolEmoji Update this document through the line-index script instead of editing the table manually.",
		"",
		"$toolEmoji Use ``Tools/update_code_line_index.ps1`` for a full refresh. Use ``Tools/update_code_line_index.ps1 -ChangedOnly`` when only changed files need to update their index records from the current git diff."
	)
	$lines.Add("meta:") | Out-Null
	$lines.Add("  document:") | Out-Null
	$lines.Add("    title: $rulerEmoji Large Files") | Out-Null
	$lines.Add("    type: technical") | Out-Null
	$lines.Add("    language: en") | Out-Null
	$lines.Add("  routing:") | Out-Null
	$lines.Add("    purpose: Generated YAML index of code files above the large-file threshold.") | Out-Null
	$lines.Add("    read_when:") | Out-Null
	$lines.Add("    - When checking large source-owned files or deciding whether a file should be split.") | Out-Null
	$lines.Add("    - When code line index tooling is in scope.") | Out-Null
	$lines.Add("    do_not_read_when:") | Out-Null
	$lines.Add("    - When the current task is unrelated to repository size, ownership, or tooling.") | Out-Null

	return ($lines -join "`n") + "`n"
}

Push-Location -LiteralPath $repoRoot
try {
	if ($Paths.Count -gt 0) {
		$targetPaths = @(Get-ExplicitCodePaths)
	} elseif ($ChangedOnly) {
		$targetPaths = @(Get-ChangedCodePaths)
	} else {
		$targetPaths = @(Get-TrackedCodePaths)
	}

	$existingIndex = Read-Index -Path $IndexPath
	$records = ConvertTo-IndexObject -Index $existingIndex

	if (-not $ChangedOnly -and $Paths.Count -eq 0) {
		$records.Clear()
	}

	foreach ($path in $targetPaths) {
		$lineCount = Get-CodeLineCount -RepoPath $path
		if ($null -eq $lineCount) {
			$records.Remove($path)
			continue
		}

		$records[$path] = [ordered]@{
			path = $path
			lines = $lineCount
			extension = [System.IO.Path]::GetExtension($path)
			large = ($lineCount -gt $LargeFileThreshold)
		}
	}

	if ($ChangedOnly -and $Paths.Count -eq 0) {
		foreach ($path in @($records.Keys)) {
			$fullPath = Join-Path $repoRoot $path
			if (-not (Test-Path -LiteralPath $fullPath -PathType Leaf)) {
				$records.Remove($path)
			}
		}
	}

	$existingGeneratedAt = $null
	if ($null -ne $existingIndex.generatedAt) {
		$existingGeneratedAt = [string]$existingIndex.generatedAt
	}

	$payload = Build-IndexPayload -Records $records -GeneratedAt $existingGeneratedAt
	$indexJson = ($payload | ConvertTo-Json -Depth 5) + "`n"
	$largeRecords = @($payload.files | Where-Object { $_.large } | Sort-Object @{ Expression = "lines"; Descending = $true }, @{ Expression = "path"; Descending = $false })
	$largeDocument = Build-LargeFilesDocument -LargeRecords $largeRecords

	$indexFullPath = Join-Path $repoRoot $IndexPath
	$largeFullPath = Join-Path $repoRoot $LargeFilesPath
	$currentIndex = if (Test-Path -LiteralPath $indexFullPath -PathType Leaf) { Get-Content -Raw -LiteralPath $indexFullPath -Encoding UTF8 } else { "" }
	$currentLarge = if (Test-Path -LiteralPath $largeFullPath -PathType Leaf) { Get-Content -Raw -LiteralPath $largeFullPath -Encoding UTF8 } else { "" }

	$needsWrite = ($currentIndex -ne $indexJson) -or ($currentLarge -ne $largeDocument)
	if ($Check) {
		if ($needsWrite) {
			throw "code line index is stale; run Tools/update_code_line_index.ps1."
		}
		Write-Host "OK: code line index is current."
		return
	}

	$indexDirectory = Split-Path -Parent $indexFullPath
	$largeDirectory = Split-Path -Parent $largeFullPath
	[System.IO.Directory]::CreateDirectory($indexDirectory) | Out-Null
	[System.IO.Directory]::CreateDirectory($largeDirectory) | Out-Null
	if ($currentIndex -ne $indexJson) {
		$payload = Build-IndexPayload -Records $records
		$indexJson = ($payload | ConvertTo-Json -Depth 5) + "`n"
	}
	[System.IO.File]::WriteAllText($indexFullPath, $indexJson, $utf8NoBom)
	[System.IO.File]::WriteAllText($largeFullPath, $largeDocument, $utf8NoBom)

	Write-Host "OK: indexed $($payload.files.Count) code file(s); $($largeRecords.Count) above $LargeFileThreshold lines."
} finally {
	Pop-Location
}
