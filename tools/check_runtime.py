#!/usr/bin/env python3
import importlib.util
import argparse
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
        return "Install PowerShell from Microsoft Store or GitHub releases."
    return "Install PowerShell for your platform."


def emit_yaml(data: dict, root_key: str) -> None:
    def scalar(value):
        if isinstance(value, bool):
            return "true" if value else "false"
        if value is None:
            return "null"
        text = str(value).replace("\\", "\\\\").replace('"', '\\"')
        return f'"{text}"'

    print(f"{root_key}:")
    for name, details in data.items():
        print(f"  {name}:")
        for key, value in details.items():
            print(f"    {key}: {scalar(value)}")


def main() -> int:
    parser = argparse.ArgumentParser(description="Report SocratexAI tooling runtime availability.")
    parser.add_argument("--root-key", default="runtime", help="YAML root key to emit.")
    args = parser.parse_args()

    python_version = f"Python {platform.python_version()} ({sys.executable})"
    pwsh_version = command_version("pwsh", ["--version"])
    pyyaml_ok = importlib.util.find_spec("yaml") is not None

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
        },
        "pyyaml": {
            "ok": pyyaml_ok,
            "version": "available" if pyyaml_ok else None,
            "install_hint": None if pyyaml_ok else "python -m pip install --user pyyaml",
        },
    }
    emit_yaml(status, args.root_key)
    missing_required = not status["python3"]["ok"]
    return 1 if missing_required else 0


if __name__ == "__main__":
    raise SystemExit(main())
