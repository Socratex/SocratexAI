from __future__ import annotations

import argparse
import json
from pathlib import Path

import document_list_item_edit_engine as engine


def main() -> int:
    parser = argparse.ArgumentParser(description="Review duplicate candidates and selected items for a structured document.")
    parser.add_argument("path", nargs="?")
    parser.add_argument("--path", "-Path", dest="path_option", default="")
    parser.add_argument("--key", "-Key", default="")
    parser.add_argument("--scope", "-Scope", choices=["item", "document"], default="document")
    parser.add_argument("--text", "-Text", default="")
    parser.add_argument("--url", "-Url", default="")
    parser.add_argument("--terms", "-Terms", nargs="*", default=[])
    parser.add_argument("--limit", "-Limit", type=int, default=12)
    parser.add_argument("--json", "-Json", action="store_true")
    parser.add_argument("--fail-on-duplicate", "-FailOnDuplicate", action="store_true")
    args = parser.parse_args()

    path = args.path_option or args.path
    if not path:
        raise SystemExit("--path or positional path is required.")

    document = engine.normalize_document(engine.load_document(Path(path)))  # type: ignore[name-defined]
    if args.terms:
        candidates = engine.candidate_matches(document, args.terms, args.limit)
    else:
        candidates = engine.find_duplicates(document, args.key, args.scope, args.text, args.url)

    items = []
    if args.terms and candidates:
        titles = sorted({str(candidate["title"]) for candidate in candidates})
        items = engine.select_items_by_titles(document, titles)

    if args.json:
        print(json.dumps({"candidates": candidates, "items": items}, ensure_ascii=False, indent=2))
    else:
        if args.terms:
            engine.print_candidates(candidates, False)
            if items:
                print()
                print(f"ITEMS: {len(items)}")
                for item in items:
                    print(f"- {item['title']} [{item['key']}]")
                    if item["content"]:
                        print(item["content"])
        elif candidates:
            print(f"DUPLICATE: {len(candidates)} match(es)")
            for candidate in candidates:
                print(f"- {candidate['key']}: {candidate['line']}")
        else:
            print("OK: no candidate duplicates")

    if args.fail_on_duplicate and candidates:
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
