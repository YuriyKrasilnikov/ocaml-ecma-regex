#!/usr/bin/env python3
from __future__ import annotations

import argparse
from pathlib import Path

from source_fetching import bool_text, fetch_url, write_with_checksum


DEFAULT_VERSION = "16.0.0"
UCD_FILES = [
    "PropertyAliases.txt",
    "PropertyValueAliases.txt",
    "UnicodeData.txt",
    "CaseFolding.txt",
    "PropList.txt",
    "DerivedCoreProperties.txt",
    "DerivedNormalizationProps.txt",
    "Scripts.txt",
    "ScriptExtensions.txt",
    "emoji/emoji-data.txt",
]


def url_for(version: str, name: str) -> str:
    return f"https://www.unicode.org/Public/{version}/ucd/{name}"


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--version", default=DEFAULT_VERSION)
    parser.add_argument("--dest", default=None)
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    destination = (
        Path(args.dest) if args.dest is not None else Path("external/ucd") / args.version
    )

    print("source_family\tucd")
    print(f"version\t{args.version}")
    print(f"destination\t{destination}")
    print(f"required_files\t{len(UCD_FILES)}")
    print(f"dry_run\t{bool_text(args.dry_run)}")

    planned = []
    for name in UCD_FILES:
        url = url_for(args.version, name)
        target = destination / name
        planned.append((url, target))
        print(f"source\t{url}\t{target}")

    if args.dry_run:
        return

    for url, target in planned:
        data = fetch_url(url)
        digest = write_with_checksum(target, data)
        print(f"fetched\t{url}\t{target}\tsha256={digest}")


if __name__ == "__main__":
    main()
