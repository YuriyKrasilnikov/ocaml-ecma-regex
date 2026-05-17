#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import re
import subprocess
from collections import Counter
from pathlib import Path


DETAIL_NAME = "test262-regexp-core-compile-cases.tsv"
SUMMARY_NAME = "test262-regexp-core-compile-cases.summary"

META_RE = re.compile(r"/\*---(?P<body>.*?)---\*/", re.S)
EXPR_PREFIX_CHARS = set("([{:;,=!?&|+-*%^~<>")
EXPR_PREFIX_WORDS = {
    "await",
    "case",
    "delete",
    "do",
    "else",
    "in",
    "instanceof",
    "new",
    "of",
    "return",
    "throw",
    "typeof",
    "void",
    "yield",
}


def git_revision(root: Path) -> str:
    return subprocess.check_output(
        ["git", "-C", str(root), "rev-parse", "HEAD"], text=True
    ).strip()


def code_without_metadata(text: str) -> str:
    def replace(match: re.Match[str]) -> str:
        return "\n" * match.group(0).count("\n")

    return META_RE.sub(replace, text, count=1)


def previous_word(code: str, index: int) -> str:
    end = index
    while end >= 0 and code[end].isspace():
        end -= 1
    start = end
    while start >= 0 and (code[start].isalnum() or code[start] in {"_", "$"}):
        start -= 1
    return code[start + 1 : end + 1]


def regex_allowed_here(code: str, index: int) -> bool:
    j = index - 1
    while j >= 0 and code[j].isspace():
        j -= 1
    if j < 0:
        return True
    if code[j] in EXPR_PREFIX_CHARS:
        return True
    if code[j] == ">" and j > 0 and code[j - 1] == "=":
        return True
    return previous_word(code, index - 1) in EXPR_PREFIX_WORDS


def skip_string(code: str, index: int, quote: str) -> int:
    i = index + 1
    while i < len(code):
        if code[i] == "\\":
            i += 2
        elif code[i] == quote:
            return i + 1
        else:
            i += 1
    return i


def skip_template(code: str, index: int) -> int:
    i = index + 1
    while i < len(code):
        if code[i] == "\\":
            i += 2
        elif code[i] == "`":
            return i + 1
        else:
            i += 1
    return i


def parse_regex_literal(code: str, index: int) -> tuple[int, str, str, str] | None:
    if not regex_allowed_here(code, index):
        return None

    i = index + 1
    in_class = False
    escaped = False
    while i < len(code):
        char = code[i]
        if escaped:
            escaped = False
        elif char == "\\":
            escaped = True
        elif in_class:
            if char == "]":
                in_class = False
        elif char == "[":
            in_class = True
        elif char == "/":
            j = i + 1
            while j < len(code) and code[j].isalpha():
                j += 1
            pattern = code[index + 1 : i]
            flags = code[i + 1 : j]
            raw = code[index:j]
            return j, pattern, flags, raw
        elif char in {"\n", "\r"}:
            return None
        i += 1
    return None


def extract_regex_literals(path: Path, relative: str) -> list[dict[str, str]]:
    text = path.read_text(encoding="utf-8", errors="replace")
    code = code_without_metadata(text)
    rows: list[dict[str, str]] = []
    i = 0
    while i < len(code):
        char = code[i]
        if char in {"'", '"'}:
            i = skip_string(code, i, char)
            continue
        if char == "`":
            i = skip_template(code, i)
            continue
        if char == "/" and i + 1 < len(code) and code[i + 1] == "/":
            newline = code.find("\n", i + 2)
            i = len(code) if newline < 0 else newline + 1
            continue
        if char == "/" and i + 1 < len(code) and code[i + 1] == "*":
            end = code.find("*/", i + 2)
            i = len(code) if end < 0 else end + 2
            continue
        if char == "/":
            parsed = parse_regex_literal(code, i)
            if parsed is not None:
                end, pattern, flags, raw = parsed
                line = code.count("\n", 0, i) + 1
                rows.append(
                    {
                        "source_path": relative,
                        "line": str(line),
                        "source_kind": "literal",
                        "pattern": pattern,
                        "flags": flags,
                        "raw": raw,
                    }
                )
                i = end
                continue
        i += 1
    return rows


def read_promoted_core_paths(audit: Path) -> list[str]:
    with audit.open(encoding="utf-8", newline="") as f:
        rows = csv.DictReader(f, delimiter="\t")
        return [
            row["path"]
            for row in rows
            if row["action"] == "promote_core_corpus"
            and row["candidate_class"] == "core_regexp_semantics"
        ]


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--test262", default="external/test262")
    parser.add_argument("--cache", default="cache")
    parser.add_argument(
        "--audit", default="cache/test262-regexp-candidate-audit.tsv"
    )
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    test262 = Path(args.test262)
    audit = Path(args.audit)
    cache = Path(args.cache)
    detail = cache / DETAIL_NAME
    summary = cache / SUMMARY_NAME

    if not test262.is_dir():
        raise SystemExit(f"missing test262 checkout at {test262}")
    if not audit.is_file():
        raise SystemExit(
            f"missing candidate audit at {audit}; run tools/audit_test262_regexp_candidates.py"
        )

    promoted_paths = read_promoted_core_paths(audit)
    rows: list[dict[str, str]] = []
    files_with_literals: set[str] = set()
    for relative in promoted_paths:
        extracted = extract_regex_literals(test262 / relative, relative)
        if extracted:
            files_with_literals.add(relative)
            rows.extend(extracted)

    seen: set[tuple[str, str, str, str, str]] = set()
    unique_rows: list[dict[str, str]] = []
    for row in rows:
        key = (
            row["source_path"],
            row["line"],
            row["source_kind"],
            row["pattern"],
            row["flags"],
        )
        if key in seen:
            continue
        seen.add(key)
        unique_rows.append(row)

    flag_counts = Counter(row["flags"] for row in unique_rows)
    no_flag_count = flag_counts.get("", 0)
    flagged_count = len(unique_rows) - no_flag_count

    summary_lines = [
        f"revision\t{git_revision(test262)}\n",
        f"input_audit\t{audit}\n",
        f"promote_core_rows\t{len(promoted_paths)}\n",
        f"files_with_regex_literals\t{len(files_with_literals)}\n",
        f"literal_compile_cases\t{len(unique_rows)}\n",
        f"literal_compile_cases_without_flags\t{no_flag_count}\n",
        f"literal_compile_cases_with_flags\t{flagged_count}\n",
        f"planned_detail_output\t{detail}\n",
        f"planned_summary_output\t{summary}\n",
        f"dry_run\t{str(args.dry_run).lower()}\n",
    ]
    for flags, count in sorted(flag_counts.items()):
        name = flags if flags else "<none>"
        summary_lines.append(f"flags_{name}\t{count}\n")

    if args.dry_run:
        print("".join(summary_lines), end="")
        return

    cache.mkdir(parents=True, exist_ok=True)
    fieldnames = ["source_path", "line", "source_kind", "pattern", "flags", "raw"]
    with detail.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, delimiter="\t", fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(unique_rows)

    with summary.open("w", encoding="utf-8") as f:
        f.write("".join(summary_lines))

    print(summary.read_text(encoding="utf-8"), end="")


if __name__ == "__main__":
    main()
