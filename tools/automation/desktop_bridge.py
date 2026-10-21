"""Small local adapter for the bundled codex-app-tools desktop pipe protocol.

This version-sensitive boundary uses the desktop's own tools, never a private
App Server. Missing tools, changed responses and unavailable hosts fail closed.
"""

from __future__ import annotations

import ctypes
import json
import os
import socket
import struct
import time
import uuid
from pathlib import Path

MAX_FRAME = 8 * 1024 * 1024
ALLOWED_TOOLS = {"list_threads", "read_thread", "get_usage_limits", "send_message_to_thread"}


def find_endpoint(configured: str | None = None) -> str:
    endpoint = configured or os.environ.get("CODEX_APP_TOOLS_PIPE_PATH")
    if endpoint:
        return endpoint
    if os.name == "nt":
        matches = [name for name in os.listdir("\\\\.\\pipe\\") if name.startswith("codex-app-tools-")]
        if len(matches) == 1:
            return "\\\\.\\pipe\\" + matches[0]
    raise ValueError("No unique Codex desktop endpoint. Start Codex or pass --endpoint explicitly.")


class LocalChannel:
    def __init__(self, endpoint: str, timeout: float):
        self.timeout = timeout
        self.pipe = None
        self.socket = None
        if os.name == "nt":
            if not endpoint.startswith("\\\\.\\pipe\\codex-app-tools-"):
                raise ValueError("Only the local Codex app-tools pipe is allowed")
            from ctypes import wintypes
            self.kernel = ctypes.WinDLL("kernel32", use_last_error=True)
            self.kernel.WaitNamedPipeW.argtypes = [wintypes.LPCWSTR, wintypes.DWORD]
            self.kernel.PeekNamedPipe.argtypes = [wintypes.HANDLE, ctypes.c_void_p, wintypes.DWORD,
                                                ctypes.c_void_p, ctypes.POINTER(wintypes.DWORD), ctypes.c_void_p]
            if not self.kernel.WaitNamedPipeW(endpoint, int(timeout * 1000)):
                raise ctypes.WinError(ctypes.get_last_error())
            self.pipe = open(endpoint, "r+b", buffering=0)
        else:
            if not Path(endpoint).is_absolute():
                raise ValueError("Desktop socket must be an absolute local path")
            self.socket = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
            self.socket.settimeout(timeout)
            try:
                self.socket.connect(endpoint)
            except BaseException:
                self.socket.close()
                raise

    def close(self):
        if self.pipe:
            self.pipe.close()
        if self.socket:
            self.socket.close()

    def write(self, data: bytes):
        if self.socket:
            self.socket.sendall(data)
            return
        while data:
            count = self.pipe.write(data)
            if not count:
                raise OSError("Desktop pipe closed while sending")
            data = data[count:]

    def read(self, count: int) -> bytes:
        result = bytearray()
        deadline = time.monotonic() + self.timeout
        while len(result) < count:
            if time.monotonic() >= deadline:
                raise TimeoutError("Codex desktop response timed out")
            size = count - len(result)
            if self.pipe:
                import msvcrt
                from ctypes import wintypes
                available = wintypes.DWORD()
                handle = msvcrt.get_osfhandle(self.pipe.fileno())
                if not self.kernel.PeekNamedPipe(handle, None, 0, None, ctypes.byref(available), None):
                    raise ctypes.WinError(ctypes.get_last_error())
                if not available.value:
                    time.sleep(0.01)
                    continue
                block = self.pipe.read(min(size, available.value))
            else:
                self.socket.settimeout(max(0.001, deadline - time.monotonic()))
                block = self.socket.recv(size)
            if not block:
                raise OSError("Desktop closed the response")
            result.extend(block)
        return bytes(result)


class DesktopBridge:
    def __init__(self, endpoint: str, caller_thread_id: str, timeout: float = 20):
        if not caller_thread_id:
            raise ValueError("An explicit caller chat ID is required; run --configure from Codex first")
        self.endpoint = endpoint
        self.caller = caller_thread_id
        self.timeout = timeout
        self.channel = None
        self.sequence = 0
        self.tools = {}

    def __enter__(self):
        self.channel = LocalChannel(self.endpoint, self.timeout)
        try:
            catalogue = self.request("tools/list", {"threadStartKind": "all"})
            self.tools = {tool["name"]: tool for tool in catalogue["tools"] if tool["name"] in ALLOWED_TOOLS}
            if set(self.tools) != ALLOWED_TOOLS:
                raise ValueError("Desktop tool catalogue is incomplete or incompatible")
            for tool in self.tools.values():
                if tool.get("namespace") != "codex_app" or not isinstance(tool.get("inputSchema"), dict):
                    raise ValueError("Unexpected desktop tool schema")
            return self
        except BaseException:
            self.channel.close()
            raise

    def __exit__(self, *_):
        self.channel.close()

    def request(self, method: str, params: dict) -> dict:
        self.sequence += 1
        message = json.dumps({"jsonrpc": "2.0", "id": self.sequence, "method": method, "params": params}).encode("utf-8")
        if len(message) > MAX_FRAME:
            raise ValueError("Desktop request is too large")
        self.channel.write(struct.pack("<I", len(message)) + message)
        length = struct.unpack("<I", self.channel.read(4))[0]
        if not 0 < length <= MAX_FRAME:
            raise ValueError("Invalid desktop response length")
        response = json.loads(self.channel.read(length))
        if response.get("id") != self.sequence or response.get("jsonrpc") != "2.0":
            raise ValueError("Desktop response identity mismatch")
        if "error" in response:
            raise RuntimeError(str(response["error"]))
        if not isinstance(response.get("result"), dict):
            raise ValueError("Invalid desktop result")
        return response["result"]

    def call(self, tool: str, arguments: dict) -> dict:
        if tool not in ALLOWED_TOOLS:
            raise ValueError("Unsupported recovery tool")
        schema = self.tools[tool]["inputSchema"]
        if set(arguments) - set(schema.get("properties", {})) or set(schema.get("required", [])) - set(arguments):
            raise ValueError("Desktop tool arguments no longer match the installed schema")
        try:
            result = self.request("tools/call", {"namespace": "codex_app", "tool": tool, "arguments": arguments,
                                  "callerSource": "codex", "threadId": self.caller,
                                  "turnId": "auto-recovery", "callId": "auto-recovery-" + str(uuid.uuid4())})
        except (RuntimeError, OSError, TimeoutError) as exc:
            raise RuntimeError(f"Desktop {tool}: {exc}") from exc
        if result.get("success") is not True:
            raise RuntimeError("Desktop tool rejected the request: " + json.dumps(result, ensure_ascii=False))
        parts = result.get("contentItems", [])
        texts = [item["text"] for item in parts if item.get("type") == "inputText"]
        if len(texts) != 1:
            raise ValueError("Expected one desktop JSON result")
        value = json.loads(texts[0])
        if not isinstance(value, dict):
            raise ValueError("Expected a desktop result object")
        return value

    def observation(self, entry: dict) -> dict:
        from .native import snapshot
        from .roster import complete_inventory, read_roster

        recent = self.call("list_threads", {"limit": 50})
        if len(recent.get("threads", [])) >= 50:
            roster = read_roster(entry["repo"])
            seen = {row["id"] for row in recent.get("threads", []) + recent.get("pinnedThreads", [])}
            polls = []
            for row in roster["threads"]:
                if row["id"] in seen:
                    continue
                result = self.call("read_thread", {"threadId": row["id"], "hostId": "local", "turnLimit": 1,
                                                    "includeOutputs": False, "maxOutputCharsPerItem": 0})
                thread = result.get("thread", {})
                from .controller import project_path
                if (thread.get("id") != row["id"] or thread.get("kind") != "codex"
                        or project_path(thread.get("cwd", "")) != entry["repo"]):
                    raise ValueError("Desktop returned a foreign project thread")
                polls.append({"polls": [{"thread": thread}], "observed_at": time.time()})
            # A second list includes chats started while the roster was read.
            fresh = self.call("list_threads", {"limit": 50})
            recent = complete_inventory(entry, roster, polls, fresh, time.time())
        limits = self.call("get_usage_limits", {})
        return snapshot(entry, recent, limits, time.time(), 50)

    def send(self, thread_id: str) -> dict:
        return self.call("send_message_to_thread", {"threadId": thread_id, "hostId": "local", "prompt": "CONTINUE-AUTO"})
