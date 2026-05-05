#!/usr/bin/env python3
import argparse
import json
import platform
import shutil
import subprocess
import sys
from typing import Optional


def command_version(command: str, args: list) -> Optional[str]:
    path = shutil.which(command)
    if path is None:
        return None
    try:
        completed = subprocess.run(
            [command, *args],
            check=False,
            capture_output=True,
            text=True,
            timeout=5,
        )
    except Exception:
        return "available"
    if completed.returncode != 0:
        return None
    output = (completed.stdout or completed.stderr).strip().splitlines()
    return output[0] if output else "available"


def pwsh_install_hint() -> str:
    system = platform.system().lower()
    if system == "linux":
        return "sudo snap install powershell --classic"
    if system == "darwin":
        return "brew install --cask powershell"
    if system == "windows":
        return "winget install --id Microsoft.PowerShell --source winget"
    return "PowerShell install is not known for this platform."


def pwsh_supported() -> bool:
    return platform.system().lower() in {"linux", "darwin", "windows"}


def pwsh_fallback_recommendation() -> str:
    if pwsh_supported():
        return "Install PowerShell 7 before using SocratexAI tools when possible."
    return "Use a no-tools/lite mode, run SocratexAI from a supported host, or port required scripts to the target shell before relying on automation."


def main() -> int:
    parser = argparse.ArgumentParser(description="Report SocratexAI tooling runtime availability.")
    parser.add_argument("--root-key", default="runtime", help="JSON root key to emit.")
    args = parser.parse_args()

    python_version = f"Python {platform.python_version()} ({sys.executable})"
    pwsh_version = command_version("pwsh", ["--version"])
    status = {
        "python3": {
            "ok": python_version is not None,
            "version": python_version,
            "install_hint": None if python_version else "Install Python 3 for your platform.",
        },
        "pwsh": {
            "ok": pwsh_version is not None,
            "version": pwsh_version,
            "install_hint": None if pwsh_version else pwsh_install_hint(),
            "install_supported": pwsh_supported(),
            "fallback_recommendation": None if pwsh_version else pwsh_fallback_recommendation(),
        },
    }
    print(json.dumps({args.root_key: status}, ensure_ascii=False, indent=4))
    missing_required = not status["python3"]["ok"]
    return 1 if missing_required else 0


if __name__ == "__main__":
    raise SystemExit(main())
