"""Shared pipeline engine: chunk changed files, run registry checkers, merge findings, apply fixes in at most 2 rounds.

Library, no CLI: a pipeline wrapper (for example tools/review/run.py) passes its registry path. All run files
(per-checker results, findings.json, log.jsonl, summary.json) live outside the repository under
<temp dir>/socratex-pipeline/<pipeline>/<run id>/ (base overridable by the work_base argument or the
SOCRATEX_PIPELINE_DIR environment variable) and are removed after the run unless keep=True.
Models and the implementer are pluggable callables (see default_model and default_implementer).
Spec: docs/specs/review-pipeline/SPEC.md
"""

from __future__ import annotations

import json
import os
import re
import shlex
import shutil
import subprocess
import sys
import tempfile
import time
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import common  # noqa: E402
import merge  # noqa: E402

MODEL_TIMEOUT_SECONDS = 300
WORK_DIR_ENV = "SOCRATEX_PIPELINE_DIR"
WORK_DIR_NAME = "socratex-pipeline"
STALE_RUN_DAYS = 7
SUMMARY_DIR_NAME = "summaries"
FINDING_DEFAULTS = {"severity": "minor", "confidence": "medium"}
PROMPT = """You are the "{checker}" micro-checker of a code review. Concern: {concern}
Judge ONLY the code below (lines {start}-{end} of a file). Report concrete problems, not style opinions.
Answer with a JSON array and nothing else. Each item: {{"line_start": int, "line_end": int,
"severity": "blocker|major|minor|nit", "confidence": "high|medium|low", "category": "short-kebab-case",
"message": "one sentence, what is wrong", "patch": "optional suggested replacement or empty"}}.
Use "confidence": "low" when unsure. Empty array when the code is fine.
Hint from the pre-filter: {hint}

```
{code}
```
"""


class ModelError(RuntimeError):
    """The model command failed (not an invalid answer: that is handled separately)."""


def default_model(request: dict) -> str:
    """Real model call: `claude -p --model <alias>` (or REVIEW_MODEL_CMD with {alias}); prompt on stdin."""
    override = os.environ.get("REVIEW_MODEL_CMD")
    argv = shlex.split(override.replace("{alias}", request["alias"])) if override else \
        [shutil.which("claude") or "claude", "-p", "--model", request["alias"]]
    done = subprocess.run(argv, input=request["prompt"], capture_output=True, text=True, encoding="utf-8",
                          errors="replace", timeout=MODEL_TIMEOUT_SECONDS)
    if done.returncode != 0:
        raise ModelError(done.stderr.strip()[-300:] or f"exit {done.returncode}")
    return done.stdout


def default_implementer(request: dict) -> None:
    """Real one-file fix: `claude -p --model <alias> --permission-mode acceptEdits` in the project (or REVIEW_IMPLEMENTER_CMD)."""
    override = os.environ.get("REVIEW_IMPLEMENTER_CMD")
    argv = shlex.split(override.replace("{alias}", request["alias"])) if override else \
        [shutil.which("claude") or "claude", "-p", "--model", request["alias"], "--permission-mode", "acceptEdits"]
    done = subprocess.run(argv, input=request["brief"], capture_output=True, text=True, encoding="utf-8",
                          errors="replace", cwd=request["project_dir"], timeout=MODEL_TIMEOUT_SECONDS * 2)
    if done.returncode != 0:
        raise ModelError(done.stderr.strip()[-300:] or f"exit {done.returncode}")


def make_gate(commands: list[str]):
    """Project gate: every command must exit 0; no commands means the gate passes."""
    def gate(project_dir: Path) -> tuple[bool, str]:
        for command in commands:
            done = subprocess.run(command, shell=True, cwd=project_dir, capture_output=True, text=True,
                                  encoding="utf-8", errors="replace")
            if done.returncode != 0:
                return False, (done.stdout + done.stderr)[-500:]
        return True, ""
    return gate


def now_iso() -> str:
    return datetime.now().isoformat(timespec="milliseconds")


def strip_fence(text: str) -> str:
    match = re.search(r"```(?:json)?\s*(.*?)```", text, re.DOTALL)
    return (match.group(1) if match else text).strip()


def work_root(work_base: Path | str | None = None) -> Path:
    if work_base:
        return Path(work_base)
    return Path(os.environ.get(WORK_DIR_ENV) or Path(tempfile.gettempdir()) / WORK_DIR_NAME)


def prune_stale(pipeline_dir: Path, days: int = STALE_RUN_DAYS) -> None:
    """Remove run folders of this pipeline older than `days` (leftovers of crashed or --keep runs)."""
    if not pipeline_dir.is_dir():
        return
    limit = time.time() - days * 86400
    for child in pipeline_dir.iterdir():
        if child.name == SUMMARY_DIR_NAME:
            for old in child.glob("*.json"):
                if old.stat().st_mtime < limit:
                    old.unlink(missing_ok=True)
        elif child.is_dir() and child.stat().st_mtime < limit:
            shutil.rmtree(child, ignore_errors=True)


class Review:
    def __init__(self, project_dir: Path, run_id: str, registry: dict, *, run_dir: Path | None, model, implementer,
                 gate, tool_available) -> None:
        self.project_dir = project_dir
        self.run_id = run_id
        self.registry = registry
        self.run_dir = run_dir
        self.log = common.RunLog(run_dir / "log.jsonl" if run_dir else None)
        self.model, self.implementer, self.gate, self.tool_available = model, implementer, gate, tool_available
        self.checkers = {c["id"]: c for c in registry["checkers"]}
        self.changes: dict[str, dict] = {}
        self.only_script = False
        self.summary_dir: Path | None = None

    def collect_changes(self, files: list[str]) -> int:
        total = 0
        for name in files:
            path = Path(name)
            try:
                rel = (path if path.is_absolute() else self.project_dir / path).resolve().relative_to(
                    self.project_dir.resolve()).as_posix()
            except ValueError:
                self.log.event("skipped_file", file=name, reason="outside the project directory")
                continue
            reason = common.skip_reason(self.project_dir, rel, self.registry["skip_patterns"])
            if reason:
                self.log.event("skipped_file", file=rel, reason=reason)
                continue
            ranges, lines = common.changed_ranges(self.project_dir, rel)
            if not lines:
                self.log.event("skipped_file", file=rel, reason="no changes")
                continue
            self.changes[rel] = {"ranges": ranges, "lines": lines,
                                 "total": len(common.read_text_lines(self.project_dir / rel))}
            total += lines
        return total

    def chunks_for(self, checker: dict, files: list[str], fresh: bool = False) -> list[dict]:
        chunks: list[dict] = []
        for rel in files:
            info = self.changes[rel]
            if fresh:
                ranges, _ = common.changed_ranges(self.project_dir, rel)
                info = {"ranges": ranges, "total": len(common.read_text_lines(self.project_dir / rel))}
            parts, splits = common.build_chunks(rel, checker["scope"], info["ranges"], info["total"],
                                                checker["max_chunk_lines"])
            if splits and not fresh:
                self.log.event("chunk_split", checker=checker["id"], file=rel, limit=checker["max_chunk_lines"],
                               parts=len(parts))
            chunks += parts
        return chunks

    def new_result(self, checker: dict) -> dict:
        return {"checker": checker["id"], "status": "done", "tier": checker["tier"], "findings": [],
                "cost": {"model_calls": 0, "calls_by_tier": {}, "input_chunks": 0, "input_lines": 0,
                         "skipped_chunks": 0}}

    def skip(self, result: dict, reason: str) -> dict:
        result.update(status="skipped", reason=reason)
        self.log.event("checker_skipped", checker=result["checker"], reason=reason)
        return result

    def run_checker(self, checker: dict, files: list[str], dry_run: bool) -> dict:
        result = self.new_result(checker)
        tool = checker.get("tool", "none")
        if tool in ("serena", "graphify", "rg") and not self.tool_available(tool):
            return self.skip(result, f"tool {tool} unavailable")
        chunks = self.chunks_for(checker, files)
        try:
            rows = common.run_select(checker, chunks, self.project_dir)
        except common.SelectError as err:
            return self.skip(result, str(err))
        mechanical = [r for r in rows if r.get("mechanical") or checker["tier"] == "script"]
        judged = [r for r in rows if r not in mechanical]
        result["plan"] = {"chunks": len(chunks), "candidates": len(rows), "predicted_model_calls": len(judged)}
        self.log.event("select", checker=checker["id"], chunks=len(chunks), candidates=len(rows),
                       mechanical=len(mechanical), judge=len(judged))
        counter = 0
        for row in mechanical:
            counter += 1
            result["findings"].append(self.script_finding(checker, counter, row))
        if not dry_run:
            for row in judged:
                for found in self.judge(checker, row, result["cost"]):
                    counter += 1
                    result["findings"].append(self.model_finding(checker, counter, found, row))
        return result

    def script_finding(self, checker: dict, number: int, row: dict) -> dict:
        mechanical = bool(row.get("mechanical")) and checker["autofix"] == "script"
        fix = ({"type": "script", "command_or_patch": checker["fix_script"]} if mechanical
               else {"type": "none", "command_or_patch": ""})
        return self.finding(checker, number, row, row, kind="mechanical" if mechanical else "judgment",
                            confidence=row.get("confidence", "high"), fix=fix)

    def model_finding(self, checker: dict, number: int, found: dict, row: dict) -> dict:
        patch = found.get("patch") if isinstance(found.get("patch"), str) else ""
        fix = {"type": "patch", "command_or_patch": patch} if patch else {"type": "none", "command_or_patch": ""}
        return self.finding(checker, number, found, row, kind="judgment", confidence=found.get("confidence"), fix=fix)

    def finding(self, checker: dict, number: int, source: dict, row: dict, *, kind: str, confidence, fix: dict) -> dict:
        start = min(max(int(source.get("line_start", row["line_start"])), row["line_start"]), row["line_end"])
        end = min(max(int(source.get("line_end", start)), start), row["line_end"])
        severity = source.get("severity") if source.get("severity") in merge.SEVERITIES else FINDING_DEFAULTS["severity"]
        confidence = confidence if confidence in merge.CONFIDENCES else FINDING_DEFAULTS["confidence"]
        category = str(source.get("category") or row.get("category") or checker["id"])
        message = str(source.get("message") or row.get("message") or "Needs attention.")
        made = {"id": f"{checker['id']}-{number}", "checker": checker["id"], "file": row["file"], "line_start": start,
                "line_end": end, "severity": severity, "kind": kind, "confidence": confidence, "message": message,
                "fix": fix, "status": "open", "category": category}
        if row.get("chunk_split"):
            made["chunk_split"] = True
        return made

    def judge(self, checker: dict, row: dict, cost: dict) -> list[dict]:
        cost["input_chunks"] += 1
        cost["input_lines"] += row["line_end"] - row["line_start"] + 1
        tier = checker["tier"]
        found = self.ask(checker, tier, row, cost)
        if found is None:
            cost["skipped_chunks"] += 1
            return []
        if any(f.get("confidence") == "low" for f in found):
            higher = common.next_tier(tier)
            if higher is None:
                self.log.event("escalation_blocked", checker=checker["id"], tier=tier, reason="confidence_low")
                return found
            self.log.event("escalation", checker=checker["id"], file=row["file"], from_tier=tier, to_tier=higher,
                           reason="confidence_low")
            better = self.ask(checker, higher, row, cost)
            if better is not None:
                return better
        return found

    def ask(self, checker: dict, tier: str, row: dict, cost: dict) -> list[dict] | None:
        lines = common.read_text_lines(self.project_dir / row["file"])[row["line_start"] - 1:row["line_end"]]
        code = "\n".join(f"{n}: {text}" for n, text in enumerate(lines, row["line_start"]))
        request = {"checker": checker["id"], "tier": tier, "alias": common.tier_alias(tier, self.registry["aliases"]),
                   "file": row["file"], "line_start": row["line_start"], "line_end": row["line_end"],
                   "prompt": PROMPT.format(checker=checker["id"], concern=checker["concern"], start=row["line_start"],
                                           end=row["line_end"], hint=row.get("message", ""), code=code)}
        for attempt in (1, 2):
            cost["model_calls"] += 1
            cost["calls_by_tier"][tier] = cost["calls_by_tier"].get(tier, 0) + 1
            try:
                text = self.model({**request, "attempt": attempt})
            except Exception as err:  # noqa: BLE001 - a failing model call must not stop the whole review
                self.log.event("model_error", checker=checker["id"], tier=tier, error=str(err)[:200])
                return None
            parsed = self.parse(text)
            self.log.event("model_call", checker=checker["id"], tier=tier, alias=request["alias"], attempt=attempt,
                           file=row["file"], valid=parsed is not None)
            if parsed is not None:
                return parsed
            self.log.event("model_invalid_json", checker=checker["id"], tier=tier, attempt=attempt)
        self.log.event("chunk_skipped", checker=checker["id"], file=row["file"], reason="invalid model JSON after retry")
        return None

    @staticmethod
    def parse(text: str) -> list[dict] | None:
        try:
            data = json.loads(strip_fence(text))
        except (json.JSONDecodeError, TypeError):
            return None
        if isinstance(data, dict):
            data = data.get("findings")
        if not isinstance(data, list):
            return None
        usable = [d for d in data if isinstance(d, dict) and isinstance(d.get("line_start"), int)
                  and isinstance(d.get("message"), str) and d["message"]]
        return usable if len(usable) == len(data) else None

    def write_result(self, result: dict) -> None:
        if self.run_dir is not None:
            (self.run_dir / f"{result['checker']}.json").write_text(
                json.dumps(result, indent=2, ensure_ascii=False) + "\n", encoding="utf-8", newline="\n")

    def check_phase(self, files: list[str], dry_run: bool) -> list[dict]:
        enabled = [c for c in self.registry["checkers"] if c["enabled"] and (not self.only_script or c["tier"] == "script")]

        def work(checker: dict) -> dict:
            result = self.run_checker(checker, files, dry_run)
            if not dry_run:
                self.write_result(result)
            return result

        with ThreadPoolExecutor(max_workers=4) as pool:
            return list(pool.map(work, enabled))

    def route(self, finding: dict) -> str | None:
        checker = self.checkers[finding["checker"]]
        if finding["status"] != "open" or checker["autofix"] == "none":
            return None
        if checker["autofix"] == "script" and finding["fix"]["type"] == "script":
            return "script"
        if checker["autofix"] == "agent" or checker["autofix_fallback"] == "agent":
            return "agent"
        return None

    def gate_ok(self, rel: str) -> bool:
        ok, output = self.gate(self.project_dir)
        self.log.event("gate", file=rel, ok=ok, output=output[-200:])
        return ok

    def revert(self, rel: str, original: bytes, why: str) -> None:
        (self.project_dir / rel).write_bytes(original)
        self.log.event("revert", file=rel, reason=why)

    def mark(self, findings: list[dict], status: str, note: str | None = None) -> None:
        for finding in findings:
            finding["status"] = status
            if note:
                finding["note"] = note

    def timed(self, rel: str, kind: str, action) -> tuple:
        self.log.event("fix_start", file=rel, kind=kind)
        started = now_iso()
        outcome = action()
        self.log.event("fix_end", file=rel, kind=kind, started=started, ended=now_iso())
        return outcome

    def script_fix(self, rel: str, findings: list[dict]) -> bool:
        touched = False
        for command in sorted({f["fix"]["command_or_patch"] for f in findings}):
            mine = [f for f in findings if f["fix"]["command_or_patch"] == command]
            path = self.project_dir / rel
            original = path.read_bytes()
            try:
                done = self.timed(rel, "script", lambda: common.run_fix_script(
                    command, path, self.project_dir, self.checkers[mine[0]["checker"]]["here"],
                    [(f["line_start"], f["line_end"]) for f in mine]))
            except Exception as err:  # noqa: BLE001
                self.revert(rel, original, f"fix script error: {err}")
                self.mark(mine, "open", "fix script could not run")
                continue
            if done.returncode != 0:
                self.revert(rel, original, "fix script failed")
                self.mark(mine, "open", "fix script failed")
            elif path.read_bytes() == original:
                self.mark(mine, "open", "fix script made no change")
            elif not self.gate_ok(rel):
                self.revert(rel, original, "gate failed")
                self.mark(mine, "reported", "fix broke the gate; reverted")
            else:
                self.mark(mine, "fixed", "fixed by script")
                touched = True
        return touched

    def brief(self, rel: str, findings: list[dict]) -> str:
        rows = "\n".join(f"- lines {f['line_start']}-{f['line_end']} [{f['severity']}] {f['message']}" for f in findings)
        return (f"Fix the review findings below in ONE file: {rel}. Edit only this file, change nothing else, keep "
                f"behaviour identical, follow the project's code style. Line numbers are from detection time and may "
                f"have shifted slightly.\n\nFindings:\n{rows}\n")

    def agent_fix(self, rel: str, findings: list[dict]) -> bool:
        path = self.project_dir / rel
        original = path.read_bytes()
        tier = self.registry["implementer_tier"]
        for attempt in (1, 2):
            request = {"file": rel, "project_dir": common.posix(self.project_dir), "tier": tier,
                       "alias": common.tier_alias(tier, self.registry["aliases"]),
                       "brief": self.brief(rel, findings), "findings": findings}
            try:
                self.timed(rel, "agent", lambda: self.implementer(request))
            except Exception as err:  # noqa: BLE001
                self.revert(rel, original, f"implementer error: {str(err)[:100]}")
                self.mark(findings, "open", "implementer failed")
                return False
            if path.read_bytes() == original:
                self.mark(findings, "open", "implementer made no change")
                return False
            if self.gate_ok(rel):
                for checker_id in sorted({f["checker"] for f in findings}):
                    mine = [f for f in findings if f["checker"] == checker_id]
                    if self.still_flagged(rel, checker_id, {f["category"] for f in mine}):
                        self.mark(mine, "reported", "fix applied, but the checker still flags the file")
                    else:
                        self.mark(mine, "fixed", "fixed by agent")
                return True
            self.revert(rel, original, "gate failed")
            higher = common.next_tier(tier)
            if attempt == 1 and higher:
                self.log.event("escalation", file=rel, from_tier=tier, to_tier=higher, reason="gate_failed")
                tier = higher
                continue
            self.mark(findings, "reported", "fix broke the gate; reverted")
            return False
        return False

    def still_flagged(self, rel: str, checker_id: str, categories: set[str]) -> bool:
        """Re-run the checker's select on the file after an agent fix; a mechanical candidate of the same category means not fixed."""
        checker = self.checkers[checker_id]
        try:
            rows = common.run_select(checker, self.chunks_for(checker, [rel], fresh=True), self.project_dir)
        except common.SelectError:
            return False
        left = [r for r in rows if r.get("mechanical") and r.get("category") in categories]
        self.log.event("recheck", file=rel, checker=checker_id, remaining=len(left))
        return bool(left)

    def recheck(self, touched: set[str], findings: list[dict]) -> None:
        for rel in sorted(touched):
            for checker in self.checkers.values():
                fixed = [f for f in findings if f["file"] == rel and f["checker"] == checker["id"]
                         and f["status"] == "fixed" and f["fix"]["type"] == "script"]
                if not fixed or checker["autofix"] != "script":
                    continue
                chunks = self.chunks_for(checker, [rel], fresh=True)
                try:
                    left = [r for r in common.run_select(checker, chunks, self.project_dir) if r.get("mechanical")]
                except common.SelectError:
                    continue
                self.log.event("recheck", file=rel, checker=checker["id"], remaining=len(left))
                if left:
                    self.mark(fixed, "open", "still detected after fix")

    def fix_phase(self, findings: list[dict]) -> int:
        rounds = 0
        for number in range(1, common.MAX_FIX_ROUNDS + 1):
            todo = [f for f in findings if self.route(f)]
            if not todo:
                break
            rounds = number
            self.log.event("round_start", round=number, findings=len(todo))
            touched: set[str] = set()
            for route, handler in (("script", self.script_fix), ("agent", self.agent_fix)):
                for rel in sorted({f["file"] for f in todo if self.route(f) == route}):
                    mine = [f for f in todo if f["file"] == rel and self.route(f) == route]
                    if mine and handler(rel, mine):
                        touched.add(rel)
            self.recheck(touched, findings)
            self.log.event("round_end", round=number)
        left = [f for f in findings if self.route(f)]
        if left:
            self.log.event("rounds_exhausted", open=len(left), max_rounds=common.MAX_FIX_ROUNDS)
        return rounds


def plan_rows(results: list[dict]) -> list[dict]:
    rows = []
    for result in results:
        plan = result.get("plan", {})
        rows.append({"id": result["checker"], "status": result["status"], "reason": result.get("reason", ""),
                     "tier": result["tier"], "chunks": plan.get("chunks", 0), "candidates": plan.get("candidates", 0),
                     "predicted_model_calls": plan.get("predicted_model_calls", 0)})
    return rows


def cost_table(results: list[dict]) -> dict:
    return {r["checker"]: {"model_calls": r["cost"]["model_calls"], "tier": r["tier"],
                           "input_chunks": r["cost"]["input_chunks"], "input_lines": r["cost"]["input_lines"],
                           "calls_by_tier": r["cost"]["calls_by_tier"], "skipped_chunks": r["cost"]["skipped_chunks"]}
            for r in results}


def summarize(run_id: str, files: list[str], changed: int, doc: dict, results: list[dict], review: Review) -> dict:
    statuses = {}
    for finding in doc["findings"]:
        statuses[finding["status"]] = statuses.get(finding["status"], 0) + 1
    cost = cost_table(results)
    for checker_id, row in cost.items():
        row["escalations"] = sum(1 for e in review.log.events if e["event"] == "escalation" and e.get("checker") == checker_id)
        row["rejected"] = sum(1 for f in doc["findings"] if f["checker"] == checker_id and f["status"] == "rejected")
    tiers = [t for r in results for t in r["cost"]["calls_by_tier"]]
    main_tier = next((t for t in ("high", "standard", "cheap") if t in tiers), "cheap")
    escalated = any(e["event"] == "escalation" for e in review.log.events)
    unresolved = statuses.get("open", 0) + statuses.get("reported", 0)
    fixes = doc["rounds"]
    hint = (f"python tools/routing_log.py --type review --tier {main_tier} --agent reviewer --first-pass "
            f"{'yes' if not unresolved and not fixes else 'no'} --fixes {fixes} "
            f"--escalated {'yes' if escalated else 'no'} --commit HEAD")
    return {"run_id": run_id, "files": files, "changed_lines": changed, "model_calls": sum(
        c["model_calls"] for c in cost.values()), "rounds": doc["rounds"], "findings_by_status": statuses,
        "cost": cost, "escalated": escalated, "escalations": [
            {k: e[k] for k in ("from_tier", "to_tier", "reason") if k in e}
            for e in review.log.events if e["event"] == "escalation"], "routing_log_hint": hint}


def run_pipeline(registry_path, project_dir, files, *, run_id: str | None = None, dry_run: bool = False,
                 min_changed_lines: int | None = None, fix: bool = True, keep: bool = False,
                 work_base: Path | str | None = None, model=None, implementer=None, gate=None, tool_available=None,
                 out=print, err=None) -> dict:
    """Run one pipeline over `files`; returns {exit_code, run_dir, plan?, doc?, summary?}.

    Raises common.RegistryError on a bad registry. The run folder is removed at the end unless keep=True.
    """
    project_dir = Path(project_dir).resolve()
    run_id = run_id or datetime.now().strftime("%Y%m%d-%H%M%S")
    registry = common.load_registry(Path(registry_path), project_dir)
    threshold = registry["min_changed_lines"] if min_changed_lines is None else min_changed_lines
    run_dir = None
    created = False
    if not dry_run:
        pipeline_dir = work_root(work_base) / registry["pipeline"]
        prune_stale(pipeline_dir)
        run_dir = pipeline_dir / run_id
        summary_dir = pipeline_dir / SUMMARY_DIR_NAME
        created = not run_dir.exists()
        run_dir.mkdir(parents=True, exist_ok=True)
    review = Review(project_dir, run_id, registry, run_dir=run_dir, model=model or default_model,
                    implementer=implementer or default_implementer, gate=gate or make_gate(registry["gates"]),
                    tool_available=tool_available or (lambda name: shutil.which(name) is not None))
    if run_dir is not None:
        review.summary_dir = summary_dir
    err = err or (lambda text: print(text, file=sys.stderr))
    try:
        result = execute(review, list(files), run_id, run_dir, dry_run, threshold, fix, out, err)
    finally:
        if run_dir is not None and created and not keep:
            shutil.rmtree(run_dir, ignore_errors=True)
    result["run_dir"] = run_dir if run_dir is not None and run_dir.exists() else None
    return result


def execute(review: Review, files: list[str], run_id: str, run_dir: Path | None, dry_run: bool, threshold: int,
            fix: bool, out, err) -> dict:
    review.log.event("run_start", run_id=run_id, files=len(files), dry_run=dry_run)
    changed = review.collect_changes(files)
    finish = {"exit_code": 0}
    if not review.changes:
        review.log.event("empty_diff", reason="no changed files to review")
        out("No changes to review.")
        return finish
    if changed < threshold:
        review.log.event("trivial_change", changed_lines=changed, min_changed_lines=threshold)
        review.only_script = True
        if not any(c["enabled"] and c["tier"] == "script" for c in review.registry["checkers"]):
            out(f"Trivial change ({changed} lines, threshold {threshold}): review skipped.")
            return finish
        out(f"Trivial change ({changed} lines, threshold {threshold}): only script checkers run.")
    results = review.check_phase(sorted(review.changes), dry_run)
    if dry_run:
        finish["plan"] = plan_rows(results)
        for row in finish["plan"]:
            out(f"{row['id']}: {row['status']} tier={row['tier']} chunks={row['chunks']} candidates={row['candidates']} "
                f"predicted_model_calls={row['predicted_model_calls']} {row['reason']}".rstrip())
        out(f"Predicted model calls: {sum(r['predicted_model_calls'] for r in finish['plan'])} (upper bound, no retries).")
        return finish
    doc = merge.build_document(run_id, results)
    merge.write_document(run_dir, doc)
    if fix:
        doc["rounds"] = review.fix_phase(doc["findings"])
    merge.write_document(run_dir, doc)
    summary = summarize(run_id, sorted(review.changes), changed, doc, results, review)
    review.log.event("cost", checkers=summary["cost"])
    review.log.event("run_end", findings=summary["findings_by_status"], rounds=doc["rounds"])
    text = json.dumps(summary, indent=2, ensure_ascii=False) + "\n"
    (run_dir / "summary.json").write_text(text, encoding="utf-8", newline="\n")
    summary_path = None
    if review.summary_dir is not None:
        review.summary_dir.mkdir(parents=True, exist_ok=True)
        summary_path = review.summary_dir / f"{run_id}.json"
        summary_path.write_text(text, encoding="utf-8", newline="\n")
    err(f"Review {run_id}: {summary['findings_by_status']} model_calls={summary['model_calls']} rounds={doc['rounds']}")
    err("Cost: " + "; ".join(f"{k} calls={v['model_calls']} tier={v['tier']} chunks={v['input_chunks']}"
                              for k, v in summary["cost"].items()))
    err(f"Router log: {summary['routing_log_hint']}" + (f"  (cost summary: {summary_path})" if summary_path else ""))
    finish.update(doc=doc, summary=summary, summary_path=summary_path)
    return finish
