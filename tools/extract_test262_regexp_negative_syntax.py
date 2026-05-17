#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import re
from collections import Counter
from pathlib import Path

from ecma262_tooling import read_tsv_rows


DETAIL_NAME = "test262-regexp-negative-syntax-cases.tsv"
SUMMARY_NAME = "test262-regexp-negative-syntax-cases.summary"

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


def code_without_metadata(text: str) -> str:
    def replace(match: re.Match[str]) -> str:
        return "\n" * match.group(0).count("\n")

    return META_RE.sub(replace, text, count=1)


def frontmatter(text: str) -> str:
    match = META_RE.search(text)
    return "" if match is None else match.group("body")


def has_parse_negative_metadata(text: str) -> bool:
    meta = frontmatter(text)
    return (
        "negative:" in meta
        and "phase: parse" in meta
        and "SyntaxError" in meta
    )


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


def skip_non_code(code: str, index: int) -> int | None:
    char = code[index]
    if char in {"'", '"'}:
        return skip_string(code, index, char)
    if char == "`":
        return skip_template(code, index)
    if char == "/" and index + 1 < len(code) and code[index + 1] == "/":
        newline = code.find("\n", index + 2)
        return len(code) if newline < 0 else newline + 1
    if char == "/" and index + 1 < len(code) and code[index + 1] == "*":
        end = code.find("*/", index + 2)
        return len(code) if end < 0 else end + 2
    return None


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


def find_matching(code: str, open_index: int, open_char: str, close_char: str) -> int:
    depth = 0
    i = open_index
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
        if char == open_char:
            depth += 1
        elif char == close_char:
            depth -= 1
            if depth == 0:
                return i
        i += 1
    return -1


def find_call_open(code: str, name: str, start: int = 0) -> int:
    index = start
    while index < len(code):
        skipped = skip_non_code(code, index)
        if skipped is not None:
            index = skipped
            continue
        if code.startswith(name, index):
            cursor = index + len(name)
            while cursor < len(code) and code[cursor].isspace():
                cursor += 1
            if cursor < len(code) and code[cursor] == "(":
                return cursor
        index += 1
    return -1


def decode_js_string(raw_body: str) -> str:
    result: list[str] = []
    i = 0
    while i < len(raw_body):
        char = raw_body[i]
        if char != "\\":
            result.append(char)
            i += 1
            continue
        if i + 1 >= len(raw_body):
            result.append("\\")
            i += 1
            continue
        escaped = raw_body[i + 1]
        if escaped in {"\\", "'", '"', "/"}:
            result.append(escaped)
            i += 2
        elif escaped == "b":
            result.append("\b")
            i += 2
        elif escaped == "f":
            result.append("\f")
            i += 2
        elif escaped == "n":
            result.append("\n")
            i += 2
        elif escaped == "r":
            result.append("\r")
            i += 2
        elif escaped == "t":
            result.append("\t")
            i += 2
        elif escaped == "v":
            result.append("\v")
            i += 2
        elif escaped == "x" and i + 3 < len(raw_body):
            digits = raw_body[i + 2 : i + 4]
            try:
                result.append(chr(int(digits, 16)))
                i += 4
            except ValueError:
                result.append("x")
                i += 2
        elif escaped == "u" and i + 5 < len(raw_body):
            digits = raw_body[i + 2 : i + 6]
            try:
                result.append(chr(int(digits, 16)))
                i += 6
            except ValueError:
                result.append("u")
                i += 2
        elif escaped in {"\n", "\r"}:
            i += 2
            if escaped == "\r" and i < len(raw_body) and raw_body[i] == "\n":
                i += 1
        else:
            result.append(escaped)
            i += 2
    return "".join(result)


def parse_string_argument(code: str, index: int) -> tuple[int, str, str] | None:
    while index < len(code) and code[index].isspace():
        index += 1
    if index >= len(code) or code[index] not in {"'", '"'}:
        return None
    quote = code[index]
    i = index + 1
    while i < len(code):
        if code[i] == "\\":
            i += 2
        elif code[i] == quote:
            raw = code[index : i + 1]
            return i + 1, raw, decode_js_string(code[index + 1 : i])
        else:
            i += 1
    return None


def parse_string_args(code: str, open_index: int) -> tuple[str, str, str] | None:
    first = parse_string_argument(code, open_index + 1)
    if first is None:
        return None
    index, raw_pattern, pattern = first
    while index < len(code) and code[index].isspace():
        index += 1
    flags = ""
    raw_flags = ""
    if index < len(code) and code[index] == ",":
        second = parse_string_argument(code, index + 1)
        if second is not None:
            _, raw_flags, flags = second
        else:
            return None
    elif index < len(code) and code[index] == ")":
        pass
    else:
        return None
    return pattern, flags, raw_pattern if not raw_flags else f"{raw_pattern}, {raw_flags}"


def compact_source(source: str) -> str:
    return " ".join(source.split())


def find_top_level_comma(code: str, index: int) -> int:
    depth = 0
    i = index
    while i < len(code):
        skipped = skip_non_code(code, i)
        if skipped is not None:
            i = skipped
            continue
        char = code[i]
        if char in {"(", "[", "{"}:
            depth += 1
        elif char in {")", "]", "}"}:
            if depth == 0:
                return -1
            depth -= 1
        elif char == "," and depth == 0:
            return i
        i += 1
    return -1


def parse_non_string_pattern_string_flags(
    code: str, open_index: int
) -> tuple[str, str, str] | None:
    if parse_string_argument(code, open_index + 1) is not None:
        return None
    comma = find_top_level_comma(code, open_index + 1)
    if comma < 0:
        return None
    second = parse_string_argument(code, comma + 1)
    if second is None:
        return None
    _, raw_flags, flags = second
    if flags == "":
        return None
    raw_pattern = compact_source(code[open_index + 1 : comma])
    return "", flags, f"{raw_pattern}, {raw_flags}"


def is_first_arg_to_regexp_call_with_string_flags(code: str, name_index: int) -> bool:
    cursor = name_index - 1
    while cursor >= 0 and code[cursor].isspace():
        cursor -= 1
    if cursor < 0 or code[cursor] != "(":
        return False
    callee_end = cursor - 1
    while callee_end >= 0 and code[callee_end].isspace():
        callee_end -= 1
    callee_start = callee_end - len("RegExp") + 1
    if callee_start < 0 or code[callee_start : callee_end + 1] != "RegExp":
        return False
    comma = find_top_level_comma(code, cursor + 1)
    return comma >= 0 and parse_string_argument(code, comma + 1) is not None


def line_number(code: str, index: int) -> int:
    return code.count("\n", 0, index) + 1


def extract_regex_literals(code: str, relative: str) -> list[dict[str, str]]:
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
                rows.append(
                    {
                        "source_path": relative,
                        "line": str(line_number(code, i)),
                        "source_kind": "literal_parse_negative",
                        "pattern": pattern,
                        "flags": flags,
                        "raw": raw,
                        "extractor": "metadata_parse_negative_literal",
                        "expected_behavior": "compile_error",
                    }
                )
                i = end
                continue
        i += 1
    return rows


def extract_calls_from_region(
    code: str, relative: str, start: int, end: int, extractor: str
) -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    region = code[start:end]
    for call_name, source_kind in [
        ("new RegExp", "regexp_constructor_string"),
        ("RegExp", "regexp_function_string"),
        (".compile", "regexp_compile_method_string"),
    ]:
        search = 0
        while True:
            open_index = find_call_open(region, call_name, search)
            if open_index < 0:
                break
            parsed = parse_string_args(region, open_index)
            if parsed is None and call_name in {"new RegExp", "RegExp"}:
                parsed = parse_non_string_pattern_string_flags(region, open_index)
            if parsed is not None:
                name_index = region.rfind(call_name, 0, open_index)
                if call_name == "new RegExp" and is_first_arg_to_regexp_call_with_string_flags(
                    region, name_index
                ):
                    search = open_index + 1
                    continue
                if call_name == "RegExp":
                    prefix = region[max(0, name_index - 8) : name_index]
                    if prefix.rstrip().endswith("new"):
                        search = open_index + 1
                        continue
                pattern, flags, raw = parsed
                absolute = start + open_index
                rows.append(
                    {
                        "source_path": relative,
                        "line": str(line_number(code, absolute)),
                        "source_kind": source_kind,
                        "pattern": pattern,
                        "flags": flags,
                        "raw": raw,
                        "extractor": extractor,
                        "expected_behavior": "compile_error",
                    }
                )
            search = open_index + 1
    return rows


def extract_assert_throws(code: str, relative: str) -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    search = 0
    while True:
        marker = code.find("assert.throws", search)
        if marker < 0:
            break
        open_index = code.find("(", marker)
        if open_index < 0:
            break
        close_index = find_matching(code, open_index, "(", ")")
        if close_index < 0:
            break
        snippet = code[marker:close_index]
        if "SyntaxError" in snippet:
            rows.extend(
                extract_calls_from_region(
                    code, relative, marker, close_index, "assert_throws_syntax_error"
                )
            )
        search = close_index + 1
    return rows


def extract_legacy_try_throw(code: str, relative: str) -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    search = 0
    while True:
        marker = code.find("new Test262Error", search)
        if marker < 0:
            break
        line_start = code.rfind("\n", 0, marker) + 1
        semicolon = code.find(";", marker)
        line_end = len(code) if semicolon < 0 else semicolon
        rows.extend(
            extract_calls_from_region(
                code, relative, line_start, line_end, "legacy_try_test262error"
            )
        )
        search = line_end + 1
    return rows


def negative_source_paths(matrix: Path) -> list[str]:
    return [
        row["path"]
        for row in read_tsv_rows(matrix)
        if row["coverage_status"] == "needs_negative_syntax_extraction"
    ]


def unique_rows(rows: list[dict[str, str]]) -> list[dict[str, str]]:
    seen: set[tuple[str, str, str, str, str, str]] = set()
    unique: list[dict[str, str]] = []
    for row in rows:
        key = (
            row["source_path"],
            row["line"],
            row["source_kind"],
            row["pattern"],
            row["flags"],
            row["extractor"],
        )
        if key in seen:
            continue
        seen.add(key)
        unique.append(row)
    return unique


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--test262", default="external/test262")
    parser.add_argument("--cache", default="cache")
    parser.add_argument(
        "--coverage-matrix", default="cache/test262-regexp-coverage-matrix.tsv"
    )
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    test262 = Path(args.test262)
    cache = Path(args.cache)
    coverage_matrix = Path(args.coverage_matrix)
    detail = cache / DETAIL_NAME
    summary = cache / SUMMARY_NAME

    if not test262.is_dir():
        raise SystemExit(f"missing test262 checkout at {test262}")
    if not coverage_matrix.is_file():
        raise SystemExit(
            f"missing coverage matrix at {coverage_matrix}; run tools/build_test262_regexp_coverage_matrix.py"
        )

    source_paths = negative_source_paths(coverage_matrix)
    rows: list[dict[str, str]] = []
    sources_with_cases: set[str] = set()
    for relative in source_paths:
        path = test262 / relative
        text = path.read_text(encoding="utf-8", errors="replace")
        code = code_without_metadata(text)
        extracted = []
        if has_parse_negative_metadata(text):
            extracted.extend(extract_regex_literals(code, relative))
        extracted.extend(extract_assert_throws(code, relative))
        extracted.extend(extract_legacy_try_throw(code, relative))
        if extracted:
            sources_with_cases.add(relative)
            rows.extend(extracted)

    rows = unique_rows(rows)
    extractor_counts = Counter(row["extractor"] for row in rows)
    source_kind_counts = Counter(row["source_kind"] for row in rows)
    flag_counts = Counter(row["flags"] if row["flags"] else "<none>" for row in rows)

    summary_lines = [
        f"input_coverage_matrix\t{coverage_matrix}\n",
        f"negative_source_rows\t{len(source_paths)}\n",
        f"sources_with_negative_cases\t{len(sources_with_cases)}\n",
        f"sources_without_negative_cases\t{len(source_paths) - len(sources_with_cases)}\n",
        f"negative_compile_cases\t{len(rows)}\n",
        f"planned_detail_output\t{detail}\n",
        f"planned_summary_output\t{summary}\n",
        f"dry_run\t{str(args.dry_run).lower()}\n",
    ]
    for name, count in sorted(extractor_counts.items()):
        summary_lines.append(f"extractor_{name}\t{count}\n")
    for name, count in sorted(source_kind_counts.items()):
        summary_lines.append(f"source_kind_{name}\t{count}\n")
    for name, count in sorted(flag_counts.items()):
        summary_lines.append(f"flags_{name}\t{count}\n")

    if args.dry_run:
        print("".join(summary_lines), end="")
        return

    cache.mkdir(parents=True, exist_ok=True)
    fieldnames = [
        "source_path",
        "line",
        "source_kind",
        "pattern",
        "flags",
        "raw",
        "extractor",
        "expected_behavior",
    ]
    with detail.open(
        "w", encoding="utf-8", errors="backslashreplace", newline=""
    ) as f:
        writer = csv.DictWriter(f, delimiter="\t", fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)

    with summary.open("w", encoding="utf-8", errors="backslashreplace") as f:
        f.write("".join(summary_lines))

    print(summary.read_text(encoding="utf-8"), end="")


if __name__ == "__main__":
    main()
