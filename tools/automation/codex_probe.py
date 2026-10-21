"""Read-only App Server probe. A private server cannot certify desktop idleness."""

from __future__ import annotations

import json
import queue
import shutil
import subprocess
import threading
import time


class AppServerProbe:
    def __init__(self, executable: str = "codex", timeout: float = 20):
        self.executable = shutil.which(executable)
        if not self.executable:
            raise ValueError("Codex CLI executable was not found")
        self.timeout = timeout
        self.process = None
        self.messages = queue.Queue()
        self.sequence = 0

    def __enter__(self):
        flags = subprocess.CREATE_NO_WINDOW if hasattr(subprocess, "CREATE_NO_WINDOW") else 0
        self.process = subprocess.Popen(
            [self.executable, "app-server", "--listen", "stdio://"],
            stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL,
            text=True, encoding="utf-8", bufsize=1, creationflags=flags,
        )
        threading.Thread(target=self._read, daemon=True).start()
        try:
            self.request("initialize", {"clientInfo": {"name": "socratex_auto_probe", "version": "1"}})
            self._send({"method": "initialized"})
            return self
        except BaseException:
            self.__exit__(None, None, None)
            raise

    def __exit__(self, *_):
        if self.process is not None:
            self.process.terminate()
            try:
                self.process.wait(timeout=3)
            except subprocess.TimeoutExpired:
                self.process.kill()
                self.process.wait(timeout=3)
            for stream in (self.process.stdin, self.process.stdout):
                if stream:
                    stream.close()

    def _read(self):
        for line in self.process.stdout:
            try:
                self.messages.put(json.loads(line))
            except ValueError:
                self.messages.put({"probe_error": "App Server emitted invalid JSON"})
        self.messages.put({"probe_error": "App Server closed its output"})

    def _send(self, message: dict):
        self.process.stdin.write(json.dumps(message) + "\n")
        self.process.stdin.flush()

    def request(self, method: str, params: dict) -> dict:
        # No turn/start, resume, shell command or mutation route is exposed by this probe.
        if method not in {"initialize", "thread/read", "account/rateLimits/read"}:
            raise ValueError("Probe only supports read-only methods")
        self.sequence += 1
        self._send({"id": self.sequence, "method": method, "params": params})
        deadline = time.monotonic() + self.timeout
        while True:
            remaining = deadline - time.monotonic()
            if remaining <= 0:
                raise TimeoutError("App Server read timed out")
            try:
                message = self.messages.get(timeout=remaining)
            except queue.Empty as exc:
                raise TimeoutError("App Server read timed out") from exc
            if "probe_error" in message:
                raise RuntimeError(message["probe_error"])
            if message.get("id") != self.sequence:
                continue
            if "error" in message:
                error = message["error"]
                raise RuntimeError(f"App Server {method}: {error.get('code')}: {error.get('message')}")
            return message["result"]

    def observe(self, thread_id: str) -> dict:
        result = self.request("thread/read", {"threadId": thread_id, "includeTurns": False})
        thread = result["thread"]
        if thread.get("id") != thread_id:
            raise ValueError("App Server returned a different thread")
        limits = self.request("account/rateLimits/read", {})
        status = thread.get("status", {})
        return {
            "thread_id": thread_id, "repo": thread["cwd"], "observed_at": time.time(),
            "status": status.get("type", "unknown"), "limits": limits,
            "authoritative": False, "project_activity_complete": False,
            "active_project_threads": [], "source": "private_app_server_read_only",
        }
