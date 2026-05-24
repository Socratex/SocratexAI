#!/usr/bin/env python3
"""Shared managed-package constants for SocratexPipeline update tooling."""

DEFAULT_MANAGED_PATHS = [
    ".gitignore",
    "AI-compiled",
    "adapters",
    "context-docs",
    "core",
    "docs",
    "docs-tech",
    "evals",
    "initializer",
    "project",
    "profiles",
    "templates",
    "tools",
    "AGENTS.md",
    "CHANGELOG.json",
    "COMMANDS.json",
    "DOCS.json",
    "FLOWS.json",
    "JSON-FORMAT-CONTRACT.json",
    "LICENSE",
    "NOTICE",
    "PUBLIC-BOOTSTRAP.md",
    "QUALITY-GATE.json",
    "README.md",
    "RECOMMENDATION.md",
    "SCRIPTS.json",
    "VERSION",
    "WORKFLOW.json",
    "pipeline_featurelist.json",
]

DEFAULT_CHILD_GENERATED_PATHS = [
    "AI-compiled/project",
    "docs-tech/cache",
    "ignored/code_context_gate.json",
]

DEFAULT_PROTECTED_PATHS = [
    "PIPELINE-CONFIG.json",
]
