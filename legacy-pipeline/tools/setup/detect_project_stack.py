#!/usr/bin/env python3
"""Detect common project stack signals."""

from __future__ import annotations

import argparse
import json
from pathlib import Path


STATIC_SIGNALS = [
    ("php", "composer.json", "Composer project"),
    ("php", "composer.lock", "Composer lockfile"),
    ("php", "artisan", "Laravel project"),
    ("php", "symfony.lock", "Symfony project"),
    ("node", "package.json", "Node package"),
    ("node", "pnpm-lock.json", "pnpm project"),
    ("node", "yarn.lock", "Yarn project"),
    ("python", "pyproject.toml", "Python project"),
    ("python", "requirements.txt", "Python requirements"),
    ("python", "uv.lock", "uv project"),
    ("go", "go.mod", "Go module"),
    ("rust", "Cargo.toml", "Rust crate"),
    ("java", "pom.xml", "Maven project"),
    ("java", "build.gradle", "Gradle project"),
    ("java", "build.gradle.kts", "Gradle Kotlin project"),
]


def detect(root: Path) -> dict[str, object]:
    signals: list[dict[str, str]] = []
    for ecosystem, relative, meaning in STATIC_SIGNALS:
        if (root / relative).exists():
            signals.append({"ecosystem": ecosystem, "file": relative, "meaning": meaning})
    for path in sorted(root.glob("*.sln")):
        if path.is_file():
            signals.append({"ecosystem": ".net", "file": path.name, "meaning": ".NET solution"})
    for path in sorted(root.rglob("*.csproj"))[:3]:
        if path.is_file():
            signals.append({"ecosystem": ".net", "file": path.relative_to(root).as_posix(), "meaning": ".NET project"})
    return {
        "target_path": str(root),
        "signals": signals,
        "composer_detected": any(signal["file"] == "composer.json" for signal in signals),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--target-path", "-TargetPath", default=".")
    args = parser.parse_args()
    print(json.dumps(detect(Path(args.target_path).resolve()), ensure_ascii=False, indent=4))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
