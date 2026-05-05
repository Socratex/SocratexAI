import argparse
import json
import sys
from pathlib import Path
from typing import Any


DEFAULT_DOCUMENTS = [
    "DOCS.json",
    "WORKFLOW.json",
    "COMMANDS.json",
    "FLOWS.json",
    "SCRIPTS.json",
]


def read_json(path: Path) -> dict[str, Any]:
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError(f"{path} must contain a JSON object.")
    return data


def document_index(document: dict[str, Any]) -> list[str]:
    index = document.get("index")
    if isinstance(index, list):
        return [str(item) for item in index]
    content = document.get("content")
    if isinstance(content, dict):
        return [str(key) for key in content.keys()]
    return []


def build_index(repo_root: Path, documents: list[str]) -> dict[str, Any]:
    content: dict[str, list[str]] = {}
    seen: set[str] = set()
    ordered_documents: list[str] = []
    for raw_document in documents:
        relative = raw_document.replace("\\", "/").strip()
        if not relative or relative in seen:
            continue
        seen.add(relative)
        ordered_documents.append(relative)
        content[relative] = document_index(read_json(repo_root / relative))

    return {
        "index": ordered_documents,
        "content": content,
        "metadata": {
            "document": {
                "title": "Pipeline Bootstrap Index",
                "type": "pipeline_bootstrap_index",
                "language": "en",
            },
            "contract": [
                "Load this bootstrap index at the start of every source-pipeline prompt before selecting a command, flow, script, workflow row, or document route.",
                "Use WORKFLOW.json and FLOWS.json for every source-pipeline prompt: WORKFLOW defines classification and guardrails; FLOWS defines ordered execution steps.",
                "Use COMMANDS.json when a prompt matches a command keyword, SCRIPTS.json when choosing tools, and DOCS.json when document ownership or routing matters.",
                "If a needed command, flow, script, workflow rule, or document route is missing, report the missing contract before executing the prompt.",
            ],
            "generated_by": "tools/pipeline_bootstrap_index.ps1",
        },
    }


def normalized_json(value: dict[str, Any]) -> str:
    return json.dumps(value, ensure_ascii=False, indent=4) + "\n"


def main() -> int:
    parser = argparse.ArgumentParser(description="Generate the minimal SocratexPipeline bootstrap index.")
    parser.add_argument("--repo-root", default=".", help="Repository root.")
    parser.add_argument("--output", default="docs-tech/PIPELINE-BOOTSTRAP.json", help="Output JSON path.")
    parser.add_argument("--documents", nargs="*", default=DEFAULT_DOCUMENTS, help="Source documents to index.")
    parser.add_argument("--check", action="store_true", help="Fail if output is stale instead of writing it.")
    args = parser.parse_args()

    repo_root = Path(args.repo_root).resolve()
    output_path = repo_root / args.output
    expected = normalized_json(build_index(repo_root, args.documents))

    if args.check:
        if not output_path.exists():
            print(f"Pipeline bootstrap index is missing: {args.output}", file=sys.stderr)
            return 1
        current = output_path.read_text(encoding="utf-8")
        if current != expected:
            print(f"Pipeline bootstrap index is stale: {args.output}", file=sys.stderr)
            return 1
        print(f"OK: pipeline bootstrap index is current: {args.output}")
        return 0

    output_path.parent.mkdir(parents=True, exist_ok=True)
    if output_path.exists() and output_path.read_text(encoding="utf-8") == expected:
        print(f"OK: pipeline bootstrap index is current: {args.output}")
        return 0
    output_path.write_text(expected, encoding="utf-8", newline="\n")
    print(f"Updated pipeline bootstrap index: {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
