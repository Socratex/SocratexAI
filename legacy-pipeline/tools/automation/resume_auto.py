#!/usr/bin/env python3
"""Run one manual AUTO recovery sweep; no scheduler, new chat or model override."""

from __future__ import annotations

import argparse
import json
import os
import sys
import time
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from automation.controller import Registry, current_run, limit_availability, limit_reset_at, project_path, remember_limit  # noqa: E402
from automation.desktop_bridge import DesktopBridge, find_endpoint  # noqa: E402
from automation.files import write_projection  # noqa: E402
from automation.recovery import eligibility, record_delivery, reserve_wake, resolve_delivery  # noqa: E402


def sweep(registry: Registry, bridge, *, dry_run: bool = False, repo: str | None = None,
          thread_id: str | None = None, account_limits: dict | None = None, observations: dict | None = None) -> list[dict]:
    # Freeze exact run identities, then recheck each under the shared OS lock.
    with registry.transaction() as data:
        entries = [dict(row) for row in data["threads"].values()
                   if (repo is None or row["repo"] == project_path(repo))
                   and (thread_id is None or row["thread_id"] == thread_id)]
    results = []
    available, retry_at = limit_availability(account_limits, time.time()) if account_limits is not None else (True, 0)
    for entry in entries:
        reason = eligibility(entry, time.time())
        if reason:
            results.append({"thread_id": entry["thread_id"], "action": "skip", "reason": reason})
            continue
        if not available:
            if not dry_run:
                with registry.transaction() as data:
                    remember_limit(current_run(data, entry["thread_id"], entry["run_id"]), account_limits, time.time(), retry_at)
            results.append({"thread_id": entry["thread_id"], "action": "skip", "reason": "account_limit",
                            "next_check_at": retry_at, "limit_reset_at": limit_reset_at(account_limits)})
            continue
        try:
            observation = (observations or {}).get(entry["thread_id"]) or bridge.observation(entry)
            reservation = reserve_wake(registry, entry["thread_id"], entry["run_id"], observation, dry_run=dry_run)
            if reservation["action"] != "prepared":
                results.append(reservation)
                continue
            try:
                response = bridge.send(entry["thread_id"], reservation["prompt"])
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


def human_report(report: dict) -> str:
    reasons = {"inactive": "AUTO nieaktywne lub zakonczone", "terminal_or_needs_input": "STOP lub potrzebna decyzja",
               "account_limit": "limit konta - nie wysylam promptu", "backoff": "oczekiwanie do kolejnej dozwolonej proby",
               "delivery_pending": "poprzednia wysylka oczekuje na potwierdzenie", "thread_not_idle": "czat pracuje lub nie jest gotowy",
               "project_busy": "inny czat projektu pracuje", "project_reserved": "projekt ma rezerwacje",
               "batch_finished_or_invalid": "partia zakonczona lub niepoprawny stan"}
    timestamp = datetime.fromtimestamp(report["observed_at"]).astimezone().strftime("%Y-%m-%d %H:%M:%S")
    lines = [f"[{timestamp}] Kontrola AUTO" + (" (podglad)" if report["dry_run"] else "")]
    actions = {"sent": "wyslano CONTINUE-AUTO", "would_send": "podglad: mozna wznowic",
               "blocked": "kontrola zablokowana", "delivery_unknown": "niepotwierdzona wysylka - bez ponawiania"}
    for row in report["results"]:
        detail = reasons.get(row.get("reason"), row.get("error") or actions.get(row["action"], row["action"]))
        lines.append(f"  {row['thread_id']}: {detail}")
    if not report["results"]:
        lines.append("  Brak pasujacych AUTO.")
    return "\n".join(lines)


def check_registered(registry: Registry, *, caller: str | None, endpoint: str | None,
                     timeout: float, dry_run: bool, repo: str | None, thread_id: str | None) -> list[dict]:
    with registry.transaction() as data:
        entries = [dict(row) for row in data["threads"].values()
                   if (repo is None or row["repo"] == project_path(repo))
                   and (thread_id is None or row["thread_id"] == thread_id)]
    results = []
    for entry in entries:
        if (entry.get("shutdown_policy") or {}).get("armed"):
            from automation.shutdown import advance, system_shutdown
            with DesktopBridge(find_endpoint(endpoint), caller or entry["thread_id"], timeout) as bridge:
                observation = bridge.observation(entry)
                power = advance(registry, entry["thread_id"], entry["run_id"], observation,
                                executor=system_shutdown, dry_run=dry_run)
                if power["action"] != "continue":
                    results.append(power)
                    continue
                results.extend(sweep(registry, bridge, dry_run=dry_run, repo=repo, thread_id=entry["thread_id"],
                                     account_limits=observation["limits"], observations={entry["thread_id"]: observation}))
            continue
        reason = eligibility(entry, time.time())
        if reason:
            waiting = entry.get("limit_wait") or {}
            if reason == "backoff" and (waiting.get("active") or entry["state"] == "waiting_limit"):
                results.append({"thread_id": entry["thread_id"], "action": "skip", "reason": "account_limit",
                                "limit_reset_at": waiting.get("reset_at"), "next_check_at": entry["next_check_at"]})
            else:
                results.append({"thread_id": entry["thread_id"], "action": "skip", "reason": reason})
            continue
        # A standalone CMD has no caller environment. Use this exact registered
        # grant as tool context; the destination is still checked independently.
        with DesktopBridge(find_endpoint(endpoint), caller or entry["thread_id"], timeout) as bridge:
            limits = bridge.call("get_usage_limits", {})
            results.extend(sweep(registry, bridge, dry_run=dry_run, repo=repo,
                                 thread_id=entry["thread_id"], account_limits=limits))
    return results


def main(argv: list[str] | None = None) -> int:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--state-dir", type=Path)
    parser.add_argument("--dry-run", action="store_true", help="Observe and report; never reserve or send a prompt")
    parser.add_argument("--human", action="store_true", help="Readable console output instead of JSON")
    parser.add_argument("--watchdog", action="store_true", help="Print only status changes; exit10 while account limited; still one sweep")
    parser.add_argument("--repo", help="Optional exact project filter; default scans all registered AUTO grants")
    parser.add_argument("--thread-id", help="Optional exact target filter; never selected by recency")
    parser.add_argument("--endpoint", help="Local desktop pipe/socket; default detects the running Windows app")
    parser.add_argument("--caller-thread-id", help="Optional control chat override; defaults to each exact registered AUTO chat")
    parser.add_argument("--configure", action="store_true", help="Save the explicit control chat ID, without sending")
    parser.add_argument("--resolve-delivery", help="Exact pending delivery ID, after manually checking chat history")
    parser.add_argument("--confirmed-consumed-or-not-delivered", action="store_true",
                        help="Operator confirms the pending message was consumed or never delivered")
    parser.add_argument("--timeout", type=float, default=20)
    args = parser.parse_args(argv)
    sweep_started = False
    registry = Registry(args.state_dir)
    try:
        if not 0 < args.timeout <= 60:
            raise ValueError("--timeout must be in (0, 60] seconds")
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
        sweep_started = True
        results = check_registered(registry, caller=caller, endpoint=args.endpoint or config.get("endpoint"),
                                   timeout=args.timeout, dry_run=args.dry_run, repo=args.repo, thread_id=args.thread_id)
        report = {"observed_at": time.time(), "dry_run": args.dry_run, "results": results}
        write_projection(registry.home / "last-recovery.json", json.dumps(report, ensure_ascii=False, indent=4) + "\n")
        if args.watchdog:
            from automation.watchdog_status import print_changes
            print_changes(registry.home, report)
        else:
            print(human_report(report) if args.human else json.dumps(report, ensure_ascii=False, indent=4))
        if any(row["action"] == "shutdown_pending" for row in results):
            return 30
        if any(row["action"] in {"blocked", "delivery_unknown", "shutdown_failed"} for row in results):
            return 2
        return 10 if args.watchdog and any(row.get("reason") == "account_limit" for row in results) else 0
    except (OSError, ValueError, KeyError, RuntimeError, TimeoutError) as exc:
        error = {"ok": False, "dispatch_may_have_occurred": sweep_started and not args.dry_run, "error": str(exc)}
        if args.watchdog:
            from automation.watchdog_status import print_changes
            try:
                print_changes(registry.home, {"observed_at": time.time(), "results": [
                    {"thread_id": "scheduler", "action": "blocked", "error": str(exc)}]})
            except (OSError, ValueError) as logging_error:
                print(json.dumps({**error, "status_log_error": str(logging_error)}), file=sys.stderr)
        else:
            print(json.dumps(error, ensure_ascii=False), file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
