import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any

import yaml

import docs_slim


if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")


URL_RE = re.compile(r"https?://[^\s\]\)>,\"']+", re.IGNORECASE)


def load_yaml(path: Path) -> Any:
    with path.open("r", encoding="utf-8") as handle:
        return yaml.safe_load(handle) or {}


def write_yaml(path: Path, value: Any) -> None:
    rendered = yaml.dump(value, Dumper=docs_slim.SlimYamlDumper, allow_unicode=True, sort_keys=False, width=1000)
    path.write_text(rendered, encoding="utf-8")


def normalize_document(document: Any) -> dict[str, Any]:
    if not isinstance(document, dict):
        raise ValueError("YAML document must be a mapping.")
    if "items" not in document:
        document["items"] = {}
    if not isinstance(document["items"], dict):
        raise ValueError("Document items must be a mapping.")
    return docs_slim.slim_document(document)


def normalize_text(value: str) -> str:
    return re.sub(r"\s+", " ", value.strip()).lower()


def extract_urls(value: str) -> list[str]:
    return [url.rstrip(".,;:") for url in URL_RE.findall(value)]


def item_content(item: Any, key: str) -> str:
    if not isinstance(item, dict):
        raise ValueError(f"Item must be a mapping: {key}")
    content = item.get("content", item.get("body", ""))
    if content is None:
        return ""
    if not isinstance(content, str):
        raise ValueError(f"Item content/body must be a string: {key}")
    return content


def item_title(item: Any, key: str) -> str:
    if not isinstance(item, dict):
        raise ValueError(f"Item must be a mapping: {key}")
    title = item.get("title", key)
    return str(title or key)


def set_item_content(item: dict[str, Any], value: str) -> None:
    if "content" in item or "body" not in item:
        item["content"] = value
    else:
        item["body"] = value


def item_search_text(key: str, item: Any) -> str:
    return " ".join([key, item_title(item, key), item_content(item, key)])


def excerpt_for_term(text: str, terms: list[str]) -> str:
    compact = " ".join(text.split())
    if not compact:
        return ""
    compact_lower = compact.casefold()
    for term in terms:
        term_lower = term.casefold()
        index = compact_lower.find(term_lower)
        if index >= 0:
            start = max(index - 80, 0)
            end = min(index + len(term) + 140, len(compact))
            prefix = "..." if start > 0 else ""
            suffix = "..." if end < len(compact) else ""
            return f"{prefix}{compact[start:end]}{suffix}"
    return compact[:220] + ("..." if len(compact) > 220 else "")


def candidate_matches(document: dict[str, Any], terms: list[str], limit: int) -> list[dict[str, Any]]:
    clean_terms = [term.strip() for term in terms if term.strip()]
    if not clean_terms:
        raise ValueError("At least one term is required.")

    results: list[dict[str, Any]] = []
    for key, item in document["items"].items():
        item_key = str(key)
        text = item_search_text(item_key, item)
        text_lower = text.casefold()
        title = item_title(item, item_key)
        title_lower = title.casefold()
        key_lower = item_key.casefold()
        matched_terms = [term for term in clean_terms if term.casefold() in text_lower]
        if not matched_terms:
            continue
        score = len(matched_terms)
        score += sum(4 for term in matched_terms if term.casefold() in title_lower)
        score += sum(3 for term in matched_terms if term.casefold() in key_lower)
        results.append(
            {
                "score": score,
                "key": item_key,
                "title": title,
                "matched_terms": matched_terms,
                "excerpt": excerpt_for_term(text, matched_terms),
            }
        )
    results.sort(key=lambda item: (-int(item["score"]), item["title"], item["key"]))
    return results[:limit]


def print_candidates(candidates: list[dict[str, Any]], output_json: bool) -> None:
    if output_json:
        print(json.dumps(candidates, ensure_ascii=False, indent=2))
        return
    if not candidates:
        print("OK: no candidate duplicates")
        return
    print(f"CANDIDATES: {len(candidates)} title(s)")
    for candidate in candidates:
        terms = ", ".join(candidate["matched_terms"])
        print(f"- {candidate['title']} [{candidate['key']}]")
        print(f"  terms: {terms}")
        print(f"  excerpt: {candidate['excerpt']}")


def select_items_by_titles(document: dict[str, Any], titles: list[str]) -> list[dict[str, str]]:
    wanted = [normalize_text(title) for title in titles if title.strip()]
    if not wanted:
        raise ValueError("At least one title is required.")

    selected: list[dict[str, str]] = []
    for requested, normalized in zip(titles, wanted):
        matches = []
        for key, item in document["items"].items():
            item_key = str(key)
            if normalize_text(item_key) == normalized or normalize_text(item_title(item, item_key)) == normalized:
                matches.append(
                    {
                        "requested": requested,
                        "key": item_key,
                        "title": item_title(item, item_key),
                        "content": item_content(item, item_key),
                    }
                )
        selected.extend(matches)
    return selected


def iter_scope_text(document: dict[str, Any], key: str, scope: str) -> list[tuple[str, str]]:
    items = document["items"]
    if scope == "item":
        if key not in items:
            raise ValueError(f"Item does not exist: {key}")
        return [(key, item_content(items[key], key))]
    result: list[tuple[str, str]] = []
    for item_key, item in items.items():
        result.append((str(item_key), item_content(item, str(item_key))))
    return result


def find_duplicates(document: dict[str, Any], key: str, scope: str, text: str, url: str) -> list[dict[str, str]]:
    query_urls = [url] if url else extract_urls(text)
    normalized_query = normalize_text(text)
    duplicates: list[dict[str, str]] = []
    for item_key, content in iter_scope_text(document, key, scope):
        lines = [line.strip() for line in content.splitlines() if line.strip()]
        for line in lines:
            line_urls = extract_urls(line)
            matched_url = next((candidate for candidate in query_urls if candidate in line_urls), "")
            matched_text = bool(normalized_query and normalize_text(line).strip("- ") == normalized_query.strip("- "))
            if matched_url or matched_text:
                duplicates.append({"key": item_key, "match": matched_url or "text", "line": line})
    return duplicates


def format_list_line(text: str) -> str:
    stripped = text.strip()
    if not stripped:
        raise ValueError("List item text cannot be empty.")
    return stripped if stripped.startswith("- ") else f"- {stripped}"


def command_check(args: argparse.Namespace) -> None:
    document = normalize_document(load_yaml(Path(args.path)))
    if args.terms:
        candidates = candidate_matches(document, args.terms, args.limit)
        print_candidates(candidates, args.json)
        if candidates and args.fail_on_duplicate:
            raise SystemExit(2)
        return
    duplicates = find_duplicates(document, args.key, args.scope, args.text, args.url)
    if duplicates:
        print(f"DUPLICATE: {len(duplicates)} match(es)")
        for duplicate in duplicates:
            print(f"- {duplicate['key']}: {duplicate['line']}")
        if args.fail_on_duplicate:
            raise SystemExit(2)
    else:
        print("OK: no duplicates")


def command_read_titles(args: argparse.Namespace) -> None:
    document = normalize_document(load_yaml(Path(args.path)))
    selected = select_items_by_titles(document, args.titles)
    if args.json:
        print(json.dumps(selected, ensure_ascii=False, indent=2))
        return
    if not selected:
        print("OK: no matching titles")
        return
    print(f"ITEMS: {len(selected)}")
    for item in selected:
        print(f"- {item['title']} [{item['key']}]")
        if item["content"]:
            print(item["content"])


def command_insert(args: argparse.Namespace) -> None:
    path = Path(args.path)
    document = normalize_document(load_yaml(path))
    items = document["items"]
    if args.key not in items:
        if not args.create_title:
            raise ValueError(f"Item does not exist: {args.key}")
        items[args.key] = {"title": args.create_title, "content": ""}
        if args.key not in document.get("index", []):
            document["index"] = list(document.get("index", [])) + [args.key]
    duplicates = find_duplicates(document, args.key, args.scope, args.text, args.url)
    if duplicates and not args.allow_duplicate:
        print(f"DUPLICATE: {len(duplicates)} match(es)")
        for duplicate in duplicates:
            print(f"- {duplicate['key']}: {duplicate['line']}")
        raise SystemExit(2)

    item = items[args.key]
    content = item_content(item, args.key)
    line = format_list_line(args.text)
    if content.strip():
        set_item_content(item, content.rstrip() + "\n" + line)
    else:
        set_item_content(item, line)
    document = docs_slim.slim_document(document)
    write_yaml(path, document)
    print(f"OK: inserted list item into {path}#{args.key}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Check and insert list lines in slim YAML document item content.")
    subparsers = parser.add_subparsers(dest="command", required=True)

    check = subparsers.add_parser("check")
    check.add_argument("path")
    check.add_argument("--key", default="")
    check.add_argument("--scope", choices=["item", "document"], default="document")
    check.add_argument("--text", default="")
    check.add_argument("--url", default="")
    check.add_argument("--terms", nargs="*", default=[])
    check.add_argument("--limit", type=int, default=12)
    check.add_argument("--json", action="store_true")
    check.add_argument("--fail-on-duplicate", action="store_true")
    check.set_defaults(func=command_check)

    read_titles = subparsers.add_parser("read-titles")
    read_titles.add_argument("path")
    read_titles.add_argument("--titles", nargs="+", required=True)
    read_titles.add_argument("--json", action="store_true")
    read_titles.set_defaults(func=command_read_titles)

    insert = subparsers.add_parser("insert")
    insert.add_argument("path")
    insert.add_argument("key")
    insert.add_argument("--text", required=True)
    insert.add_argument("--url", default="")
    insert.add_argument("--scope", choices=["item", "document"], default="document")
    insert.add_argument("--allow-duplicate", action="store_true")
    insert.add_argument("--create-title", default="")
    insert.set_defaults(func=command_insert)

    args = parser.parse_args()
    if args.command == "check" and not args.text and not args.url and not args.terms:
        raise ValueError("--text or --url is required.")
    args.func(args)


if __name__ == "__main__":
    main()
