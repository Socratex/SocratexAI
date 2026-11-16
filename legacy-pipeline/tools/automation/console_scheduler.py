"""Start one visible console scheduler per AUTO registry; CMD owns the timer."""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import time
import uuid
from contextlib import contextmanager
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from automation.controller import default_home
from automation.files import write_projection


@contextmanager
def scheduler_lock(path: Path):
    """Process-owned OS lock: closing the console also releases ownership."""
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a+b") as handle:
        handle.seek(0, os.SEEK_END)
        if handle.tell() == 0:
            handle.write(b"\0")
            handle.flush()
        handle.seek(0)
        acquired = False
        try:
            try:
                if os.name == "nt":
                    import msvcrt
                    msvcrt.locking(handle.fileno(), msvcrt.LK_NBLCK, 1)
                else:
                    import fcntl
                    fcntl.flock(handle.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
                acquired = True
            except OSError:
                pass
            yield acquired
        finally:
            if acquired:
                handle.seek(0)
                if os.name == "nt":
                    msvcrt.locking(handle.fileno(), msvcrt.LK_UNLCK, 1)
                else:
                    fcntl.flock(handle.fileno(), fcntl.LOCK_UN)


def console_command(launcher: Path) -> str:
    # CMD's outer quotes preserve a batch path containing spaces and Unicode.
    return f'"{os.environ.get("COMSPEC", "cmd.exe")}" /d /s /c ""{launcher}" --loop"'


def serve(home: Path, launcher: Path, request: str | None = None) -> int:
    def acknowledge(action: str) -> None:
        if request:
            write_projection(home / "scheduler-ready.json", json.dumps({"request": request, "action": action}))

    with scheduler_lock(home / "console-scheduler.lock") as acquired:
        if not acquired:
            acknowledge("already_running")
            print("AUTO scheduler juz dziala; pozostawiam istniejace okno.")
            return 0
        environment = dict(os.environ, SOCRATEX_AUTO_HOME=str(home.resolve()))
        # The child shares this console. Closing it terminates both processes;
        # no detached timer can survive after the lock owner exits.
        with subprocess.Popen(console_command(launcher), env=environment, cwd=launcher.parent) as child:
            acknowledge("started")
            return child.wait()


def ensure_scheduler(home: Path, launcher: Path) -> dict:
    if os.name != "nt":
        return {"action": "unsupported", "reason": "Visible CMD scheduler requires Windows"}
    launcher = launcher.resolve(strict=True)
    home = home.resolve()
    with scheduler_lock(home / "console-launch.lock") as launching:
        if not launching:
            raise RuntimeError("Scheduler startup is already in progress; repeat START AUTO")
        with scheduler_lock(home / "console-scheduler.lock") as available:
            if not available:
                return {"action": "already_running"}
        request = uuid.uuid4().hex
        command = [sys.executable, "-B", str(Path(__file__).resolve()), "--state-dir", str(home),
                   "--launcher", str(launcher), "--request", request]
        child = subprocess.Popen(command, cwd=launcher.parent, creationflags=subprocess.CREATE_NEW_CONSOLE,
                                 env=dict(os.environ, SOCRATEX_AUTO_HOME=str(home)))
        # Bounded startup handshake only; the persistent timer remains in CMD.
        deadline = time.monotonic() + 5
        while time.monotonic() < deadline:
            ready = home / "scheduler-ready.json"
            if ready.exists():
                result = json.loads(ready.read_text(encoding="utf-8"))
                if result.get("request") == request:
                    return {"action": result["action"]}
            if child.poll() is not None:
                raise RuntimeError("Scheduler exited before confirming startup; AUTO grant is preserved")
            time.sleep(0.05)
        raise TimeoutError("Scheduler startup unconfirmed; AUTO grant is preserved. Check the CMD window")


def start_for_grant(entry: dict, home: Path, launcher: Path) -> dict:
    if entry["mode"] != "native" or entry.get("wake_transport") != "manual":
        return {"action": "not_applicable"}
    return ensure_scheduler(home, launcher)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--state-dir", type=Path)
    parser.add_argument("--launcher", type=Path, required=True)
    parser.add_argument("--request")
    args = parser.parse_args()
    return serve(args.state_dir or default_home(), args.launcher.resolve(strict=True), args.request)


if __name__ == "__main__":
    raise SystemExit(main())
