from __future__ import annotations

import argparse

import document_schema_migration_engine
from document_wrapper_helpers import repo_root, run_module_main


def main() -> int:
    parser = argparse.ArgumentParser(description="Migrate structured JSON documents to canonical shape.")
    parser.add_argument("paths", nargs="*", default=["**/*.json"])
    parser.add_argument("--repo-root", default="")
    parser.add_argument("--check", "-Check", action="store_true")
    parser.add_argument("--no-post-edit", "-NoPostEdit", action="store_true", help="Accepted for legacy CLI parity; no post-edit hook is run by this entrypoint.")
    args = parser.parse_args()
    root = args.repo_root or str(repo_root())
    argv = ["--repo-root", root]
    if args.check:
        argv.append("--check")
    argv.extend(args.paths)
    return run_module_main(document_schema_migration_engine, argv)


if __name__ == "__main__":
    raise SystemExit(main())

