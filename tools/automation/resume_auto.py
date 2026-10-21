#!/usr/bin/env python3
"""Run one manual AUTO recovery sweep; no scheduler, new chat or model override."""

from __future__ import annotations

import argparse
import json
import os
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from automation.controller import Registry, project_path  # noqa: E402
from automation.desktop_bridge import DesktopBridge, find_endpoint  # noqa: E402
from automation.files import write_projection  # noqa: E402
from automation.recovery import eligibility, record_delivery, reserve_wake, resolve_delivery  # noqa: E402


def sweep(registry: Registry, bridge, *, dry_run: bool = False, repo: str | None = None,
          thread_id: str | None = None) -> list[dict]:
    # Freeze exact run identities, then recheck each under the shared OS lock.
    with registry.transaction() as data:
        entries = [dict(row) for row in data["threads"].values()
                   if (repo is None or row["repo"] == project_path(repo))
                   and (thread_id is None or row["thread_id"] == thread_id)]
    results = []
    for entry in entries:
        reason = eligibility(entry, time.time())
        if reason:
            results.append({"thread_id": entry["thread_id"], "action": "skip", "reason": reason})
            continue
        try:
            observation = bridge.observation(entry)
            reservation = reserve_wake(registry, entry["thread_id"], entry["run_id"], observation, dry_run=dry_run)
            if reservation["action"] != "prepared":
                results.append(reservation)
                continue
            try:
                response = bridge.send(entry["thread_id"])
                # Tool-level success without the expected recipient is ambiguous.
                if response.get("threadId") != entry["thread_id"]:
                    raise ValueError("Desktop did not confirm the exact destination threadId")
            except Exception as exc:
                record_delivery(registry, reservation, "unknown", str(exc))
                results.append({**reservation, "action": "delivery_unknown", "error": str(exc)})
            else:
                record_delivery(registry, reservation, "sent")
                results.append({**reservation, "action": "sent"})
        except (OSError, ValueError, KeyError, RuntimeError, TimeoutError) as exc:
            results.append({"thread_id": entry["thread_id"], "action": "blocked", "error": str(exc)})
    return results


def main(argv: list[str] | None = None) -> int:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--state-dir", type=Path)
    parser.add_argument("--dry-run", action="store_true", help="Observe and report; never reserve or send a prompt")
    parser.add_argument("--repo", help="Optional exact project filter; default scans all registered AUTO grants")
    parser.add_argument("--thread-id", help="Optional exact target filter; never selected by recency")
    parser.add_argument("--endpoint", help="Local desktop pipe/socket; default detects the running Windows app")
    parser.add_argument("--caller-thread-id", help="Control chat identity, or saved setup; not the wake destination")
    parser.add_argument("--configure", action="store_true", help="Save the explicit control chat ID, without sending")
    parser.add_argument("--resolve-delivery", help="Exact pending delivery ID, after manually checking chat history")
    parser.add_argument("--confirmed-consumed-or-not-delivered", action="store_true",
                        help="Operator confirms the pending message was consumed or never delivered")
    parser.add_argument("--timeout", type=float, default=20)
    args = parser.parse_args(argv)
    sweep_started = False
    try:
        if not 0 < args.timeout <= 60:
            raise ValueError("--timeout must be in (0, 60] seconds")
        registry = Registry(args.state_dir)
        if args.resolve_delivery:
            if not args.thread_id or not args.confirmed_consumed_or_not_delivered or args.dry_run or args.configure:
                raise ValueError("Resolution requires --thread-id and --confirmed-consumed-or-not-delivered, without dry-run/configure")
            print(json.dumps(resolve_delivery(registry, args.thread_id, args.resolve_delivery)))
            return 0
        config_path = registry.home / "recovery-client.json"
        config = json.loads(config_path.read_text(encoding="utf-8")) if config_path.exists() else {}
        caller = args.caller_thread_id or os.environ.get("CODEX_THREAD_ID") or config.get("caller_thread_id")
        if args.configure:
            if not caller:
                raise ValueError("Configure from the authorized Codex chat or pass --caller-thread-id")
            config = {"schema_version": 1, "caller_thread_id": caller}
            if args.endpoint:
                config["endpoint"] = args.endpoint
            write_projection(config_path, json.dumps(config, ensure_ascii=False, indent=4) + "\n")
            print(json.dumps({"action": "configured", "path": str(config_path), "dispatch": False}))
            return 0
        endpoint = find_endpoint(args.endpoint or config.get("endpoint"))
        with DesktopBridge(endpoint, caller, args.timeout) as bridge:
            sweep_started = True
            results = sweep(registry, bridge, dry_run=args.dry_run, repo=args.repo, thread_id=args.thread_id)
        report = {"observed_at": time.time(), "dry_run": args.dry_run, "results": results}
        write_projection(registry.home / "last-recovery.json", json.dumps(report, ensure_ascii=False, indent=4) + "\n")
        print(json.dumps(report, ensure_ascii=False, indent=4))
        return 2 if any(row["action"] in {"blocked", "delivery_unknown"} for row in results) else 0
    except (OSError, ValueError, KeyError, RuntimeError, TimeoutError) as exc:
        print(json.dumps({"ok": False, "dispatch_may_have_occurred": sweep_started and not args.dry_run,
                          "error": str(exc)}, ensure_ascii=False), file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
