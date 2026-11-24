---
type: guide
title: Obsidian (optional)
description: How to open the SocratexAI notes in Obsidian as a viewer and graph; optional, off by default.
updated: 2026-11-24
---

# Obsidian (optional)

## What it is
- Obsidian is a desktop app that opens a folder of Markdown files (a "vault") and shows them as notes with links and a graph view.
- It is closed-source freeware. SocratexAI works the same without it.

## Why
- The notes in `local/` are plain Markdown with YAML frontmatter, the same files the agents read.
- Obsidian adds a viewer and a link graph on top of them. No copy, no export, no sync.

## Setup
1. Install Obsidian from obsidian.md.
2. Choose "Open folder as vault" and select `SocratexAI/local/`, not the repo root. `local/` is git-ignored, so the `.obsidian/` settings folder stays private and is never tracked.
3. Turn on the Graph view (core plugin, in Settings -> Core plugins if it is off).
4. Optional: `sox ext enable obsidian` (adds one startup line; the app itself costs 0 tokens).

## Link convention
- Link notes with `[[note-name]]` wiki links.
- Keep the YAML frontmatter (`type`, `title`, `description`, `updated`) as it is.
- Agents must not edit `.obsidian/`.

## Known limits
- The notes have few `[[links]]` today, so the graph starts sparse and fills in as links are added.
- Obsidian skills (ledger item 114) are a separate decision, not part of this. Decide after the graph pilot.
