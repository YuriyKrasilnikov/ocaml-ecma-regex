#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import hashlib
import urllib.request
from pathlib import Path
from urllib.parse import urlparse


DEFAULT_CLAUSE_MATRIX = "cache/ecma262-regexp-clause-matrix.tsv"
DEFAULT_OUTPUT = "external/ecma262/2026/multipage"


def read_source_urls(path: Path) -> list[str]:
    with path.open(encoding="utf-8", newline="") as f:
        urls = {row["source_url"] for row in csv.DictReader(f, delimiter="\t")}
    return sorted(urls)


def output_name(url: str) -> str:
    parsed = urlparse(url)
    name = Path(parsed.path).name
    if not name:
        raise ValueError(f"cannot derive output file name from {url}")
    return name


def fetch(url: str) -> bytes:
    request = urllib.request.Request(
        url,
        headers={
            "User-Agent": "ocaml-ecma-regex-spec-fetch/0.0 (+test evidence)",
        },
    )
    with urllib.request.urlopen(request, timeout=30) as response:
        return response.read()


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--clause-matrix", default=DEFAULT_CLAUSE_MATRIX)
    parser.add_argument("--output", default=DEFAULT_OUTPUT)
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    clause_matrix = Path(args.clause_matrix)
    output = Path(args.output)
    if not clause_matrix.is_file():
        raise SystemExit(
            f"missing ECMA-262 clause matrix at {clause_matrix}; "
            "run tools/build_ecma262_regexp_clause_matrix.py first"
        )

    urls = read_source_urls(clause_matrix)
    print(f"source_count\t{len(urls)}")
    print(f"output_dir\t{output}")
    print(f"dry_run\t{str(args.dry_run).lower()}")
    for url in urls:
        target = output / output_name(url)
        print(f"source\t{url}\t{target}")

    if args.dry_run:
        return

    output.mkdir(parents=True, exist_ok=True)
    for url in urls:
        target = output / output_name(url)
        data = fetch(url)
        target.write_bytes(data)
        digest = hashlib.sha256(data).hexdigest()
        target.with_suffix(target.suffix + ".sha256").write_text(
            f"{digest}  {target.name}\n", encoding="utf-8"
        )
        print(f"fetched\t{url}\t{target}\tsha256={digest}")


if __name__ == "__main__":
    main()
