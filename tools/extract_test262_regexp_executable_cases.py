#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
from collections import Counter
from pathlib import Path

from ecma262_tooling import (
    bool_text,
    read_tsv,
    require_columns,
    safe_id,
    validate_unique_ids,
)


DETAIL_NAME = "test262-regexp-executable-cases.tsv"
SUMMARY_NAME = "test262-regexp-executable-cases.summary"
TARGET_TEST_ARTIFACT = "test/test_test262_regexp_executable_cases.ml"

EXPECTED_CASE_ROWS = 25


CASE_BY_ID = {
    "12.9.5-0001": {
        "source_path": "test/language/literals/regexp/S7.8.5_A1.1_T1.js",
        "source_snippet": "/a/",
        "literal_source": "/a/",
        "expected_pattern_text": "a",
        "expected_flag_text": "",
        "expected_parser_result": "literal_parse_ok",
        "expected_compile_result": "compile_ok",
        "expected_behavior": "literal_body_and_flags_reparsed",
    },
    "12.9.5-0002": {
        "source_path": "test/language/literals/regexp/early-err-bad-flag.js",
        "source_snippet": "/./G",
        "literal_source": "/./G",
        "expected_pattern_text": "",
        "expected_flag_text": "",
        "expected_parser_result": "literal_parse_error",
        "expected_compile_result": "not_applicable",
        "expected_behavior": "literal_rejects_extended_flags",
    },
    "12.9.5-0003": {
        "source_path": "test/language/literals/regexp/S7.8.5_A3.1_T1.js",
        "source_snippet": "/(?:)/g",
        "literal_source": "/(?:)/g",
        "expected_pattern_text": "(?:)",
        "expected_flag_text": "g",
        "expected_parser_result": "literal_parse_ok",
        "expected_compile_result": "compile_ok",
        "expected_behavior": "regular_expression_literal_body_flags_observed",
    },
    "12.9.5-0004": {
        "source_path": "test/language/literals/regexp/S7.8.5_A2.1_T1.js",
        "source_snippet": "/aa/",
        "literal_source": "/aa/",
        "expected_pattern_text": "aa",
        "expected_flag_text": "",
        "expected_parser_result": "literal_parse_ok",
        "expected_compile_result": "compile_ok",
        "expected_behavior": "regular_expression_body_first_char_chars_observed",
    },
    "12.9.5-0005": {
        "source_path": "test/language/literals/regexp/S7.8.5_A1.1_T1.js",
        "source_snippet": "/a/",
        "literal_source": "/a/",
        "expected_pattern_text": "a",
        "expected_flag_text": "",
        "expected_parser_result": "literal_parse_ok",
        "expected_compile_result": "compile_ok",
        "expected_behavior": "regular_expression_chars_empty_observed",
    },
    "12.9.5-0006": {
        "source_path": "test/language/literals/regexp/S7.8.5_A2.1_T1.js",
        "source_snippet": "/1a/",
        "literal_source": "/1a/",
        "expected_pattern_text": "1a",
        "expected_flag_text": "",
        "expected_parser_result": "literal_parse_ok",
        "expected_compile_result": "compile_ok",
        "expected_behavior": "regular_expression_chars_recursive_observed",
    },
    "12.9.5-0007": {
        "source_path": "test/language/literals/regexp/S7.8.5_A1.1_T1.js",
        "source_snippet": "/1/",
        "literal_source": "/1/",
        "expected_pattern_text": "1",
        "expected_flag_text": "",
        "expected_parser_result": "literal_parse_ok",
        "expected_compile_result": "compile_ok",
        "expected_behavior": "regular_expression_first_char_nonterminator_observed",
    },
    "12.9.5-0008": {
        "source_path": "test/language/literals/regexp/S7.8.5_A1.4_T1.js",
        "source_snippet": "/\\;/",
        "literal_source": "/\\;/",
        "expected_pattern_text": "\\;",
        "expected_flag_text": "",
        "expected_parser_result": "literal_parse_ok",
        "expected_compile_result": "compile_ok",
        "expected_behavior": "regular_expression_first_char_backslash_sequence_observed",
    },
    "12.9.5-0009": {
        "source_path": "test/built-ins/RegExp/regexp-class-chars.js",
        "source_snippet": "/[/]/",
        "literal_source": "/[/]/",
        "expected_pattern_text": "[/]",
        "expected_flag_text": "",
        "expected_parser_result": "literal_parse_ok",
        "expected_compile_result": "compile_ok",
        "expected_behavior": "regular_expression_first_char_class_observed",
    },
    "12.9.5-0010": {
        "source_path": "test/language/literals/regexp/S7.8.5_A2.1_T1.js",
        "source_snippet": "/1a/",
        "literal_source": "/1a/",
        "expected_pattern_text": "1a",
        "expected_flag_text": "",
        "expected_parser_result": "literal_parse_ok",
        "expected_compile_result": "compile_ok",
        "expected_behavior": "regular_expression_char_nonterminator_observed",
    },
    "12.9.5-0011": {
        "source_path": "test/language/literals/regexp/S7.8.5_A2.4_T1.js",
        "source_snippet": "/,\\;/",
        "literal_source": "/,\\;/",
        "expected_pattern_text": ",\\;",
        "expected_flag_text": "",
        "expected_parser_result": "literal_parse_ok",
        "expected_compile_result": "compile_ok",
        "expected_behavior": "regular_expression_char_backslash_sequence_observed",
    },
    "12.9.5-0012": {
        "source_path": "test/built-ins/RegExp/S15.10.2.13_A1_T12.js",
        "source_snippet": "/a[b]c/",
        "literal_source": "/a[b]c/",
        "expected_pattern_text": "a[b]c",
        "expected_flag_text": "",
        "expected_parser_result": "literal_parse_ok",
        "expected_compile_result": "compile_ok",
        "expected_behavior": "regular_expression_char_class_observed",
    },
    "12.9.5-0013": {
        "source_path": "test/language/literals/regexp/S7.8.5_A1.4_T1.js",
        "source_snippet": "/\\;/",
        "literal_source": "/\\;/",
        "expected_pattern_text": "\\;",
        "expected_flag_text": "",
        "expected_parser_result": "literal_parse_ok",
        "expected_compile_result": "compile_ok",
        "expected_behavior": "regular_expression_backslash_sequence_nonterminator_observed",
    },
    "12.9.5-0014": {
        "source_path": "test/language/literals/regexp/S7.8.5_A1.5_T2.js",
        "source_snippet": r"\\\u000A",
        "literal_source": "/\\<LF>/",
        "literal_source_encoding": "escaped_line_feed",
        "expected_pattern_text": "",
        "expected_flag_text": "",
        "expected_parser_result": "literal_parse_error",
        "expected_compile_result": "not_applicable",
        "expected_behavior": "regular_expression_nonterminator_rejects_line_terminator",
    },
    "12.9.5-0015": {
        "source_path": "test/built-ins/RegExp/regexp-class-chars.js",
        "source_snippet": "/[/]/",
        "literal_source": "/[/]/",
        "expected_pattern_text": "[/]",
        "expected_flag_text": "",
        "expected_parser_result": "literal_parse_ok",
        "expected_compile_result": "compile_ok",
        "expected_behavior": "regular_expression_class_brackets_observed",
    },
    "12.9.5-0016": {
        "source_path": "test/built-ins/RegExp/S15.10.2.13_A1_T2.js",
        "source_snippet": "/a[]/",
        "literal_source": "/a[]/",
        "expected_pattern_text": "a[]",
        "expected_flag_text": "",
        "expected_parser_result": "literal_parse_ok",
        "expected_compile_result": "compile_ok",
        "expected_behavior": "regular_expression_class_chars_empty_observed",
    },
    "12.9.5-0017": {
        "source_path": "test/built-ins/RegExp/regexp-class-chars.js",
        "source_snippet": "/[//]/",
        "literal_source": "/[//]/",
        "expected_pattern_text": "[//]",
        "expected_flag_text": "",
        "expected_parser_result": "literal_parse_ok",
        "expected_compile_result": "compile_ok",
        "expected_behavior": "regular_expression_class_chars_recursive_observed",
    },
    "12.9.5-0018": {
        "source_path": "test/built-ins/RegExp/regexp-class-chars.js",
        "source_snippet": "/[/]/",
        "literal_source": "/[/]/",
        "expected_pattern_text": "[/]",
        "expected_flag_text": "",
        "expected_parser_result": "literal_parse_ok",
        "expected_compile_result": "compile_ok",
        "expected_behavior": "regular_expression_class_char_nonterminator_observed",
    },
    "12.9.5-0019": {
        "source_path": "test/annexB/language/literals/regexp/class-escape.js",
        "source_snippet": "/[\\c0]/",
        "literal_source": "/[\\c0]/",
        "expected_pattern_text": "[\\c0]",
        "expected_flag_text": "",
        "expected_parser_result": "literal_parse_ok",
        "expected_compile_result": "compile_ok",
        "expected_behavior": "regular_expression_class_char_backslash_sequence_observed",
    },
    "12.9.5-0020": {
        "source_path": "test/language/literals/regexp/S7.8.5_A1.1_T1.js",
        "source_snippet": "/a/",
        "literal_source": "/a/",
        "expected_pattern_text": "a",
        "expected_flag_text": "",
        "expected_parser_result": "literal_parse_ok",
        "expected_compile_result": "compile_ok",
        "expected_behavior": "regular_expression_flags_empty_observed",
    },
    "12.9.5-0021": {
        "source_path": "test/language/literals/regexp/S7.8.5_A3.1_T4.js",
        "source_snippet": "/(?:)/gi",
        "literal_source": "/(?:)/gi",
        "expected_pattern_text": "(?:)",
        "expected_flag_text": "gi",
        "expected_parser_result": "literal_parse_ok",
        "expected_compile_result": "compile_ok",
        "expected_behavior": "regular_expression_flags_recursive_identifier_part_observed",
    },
    "12.9.5.1-0001": {
        "source_path": "test/language/literals/regexp/S7.8.5_A1.1_T1.js",
        "source_snippet": "/a/",
        "literal_source": "/a/",
        "expected_pattern_text": "a",
        "expected_flag_text": "",
        "expected_parser_result": "literal_parse_ok",
        "expected_compile_result": "compile_ok",
        "expected_behavior": "body_text_operation_source_text_observed",
    },
    "12.9.5.1-0002": {
        "source_path": "test/language/literals/regexp/S7.8.5_A3.1_T1.js",
        "source_snippet": "/(?:)/g",
        "literal_source": "/(?:)/g",
        "expected_pattern_text": "(?:)",
        "expected_flag_text": "g",
        "expected_parser_result": "literal_parse_ok",
        "expected_compile_result": "compile_ok",
        "expected_behavior": "body_text_production_literal_body_flags_observed",
    },
    "12.9.5.1-0003": {
        "source_path": "test/language/literals/regexp/S7.8.5_A1.1_T1.js",
        "source_snippet": "/\\u0041/",
        "literal_source": "/\\u0041/",
        "expected_pattern_text": "\\u0041",
        "expected_flag_text": "",
        "expected_parser_result": "literal_parse_ok",
        "expected_compile_result": "compile_ok",
        "expected_behavior": "body_text_returns_regular_expression_body_source_text",
    },
    "13.2.7-0001": {
        "source_path": "test/language/literals/regexp/S7.8.5_A1.1_T1.js",
        "source_snippet": "/a/",
        "literal_source": "/a/",
        "expected_pattern_text": "a",
        "expected_flag_text": "",
        "expected_parser_result": "literal_parse_ok",
        "expected_compile_result": "compile_ok",
        "expected_behavior": "regular_expression_literal_primary_expression_delegates_to_12_9_5",
    },
}


def requirement_key(row: dict[str, str]) -> str:
    return f"{row['clause_id']}-{row['requirement_id'].rsplit('-', 1)[1]}"


def line_number_for_snippet(path: Path, snippet: str) -> int:
    text = path.read_text(encoding="utf-8", errors="replace")
    index = text.find(snippet)
    if index < 0:
        raise SystemExit(f"snippet {snippet!r} is missing from {path}")
    return text.count("\n", 0, index) + 1


def selected_mapping_rows(rows: list[dict[str, str]]) -> list[dict[str, str]]:
    selected = [
        row
        for row in rows
        if row["route_status"] == "needs_test262_executable_extractor"
        and row["coverage_areas"] == "regexp_literal_lexical_grammar"
        and row["product_surface"] in {"compile", "literal_lexer"}
    ]
    selected.sort(key=lambda row: (row["clause_id"], row["requirement_id"]))
    if len(selected) != EXPECTED_CASE_ROWS:
        raise SystemExit(
            f"expected {EXPECTED_CASE_ROWS} test262 executable rows, "
            f"selected {len(selected)}"
        )
    missing_cases = [
        row["requirement_id"] for row in selected if requirement_key(row) not in CASE_BY_ID
    ]
    if missing_cases:
        raise SystemExit(
            "missing test262 executable case definitions for "
            + ", ".join(missing_cases)
        )
    extra_cases = sorted(
        set(CASE_BY_ID).difference(requirement_key(row) for row in selected)
    )
    if extra_cases:
        raise SystemExit(
            "case definitions do not correspond to selected requirements: "
            + ", ".join(extra_cases)
        )
    return selected


def executable_case_row(
    row: dict[str, str],
    test262_root: Path,
) -> dict[str, str]:
    requirement_id = row["requirement_id"]
    case = CASE_BY_ID[requirement_key(row)]
    source_path = case["source_path"]
    snippet = case["source_snippet"]
    source_line = line_number_for_snippet(test262_root / source_path, snippet)
    expected_behavior = case["expected_behavior"]
    literal_source_encoding = case.get("literal_source_encoding", "plain")
    return {
        "case_id": f"test262-regexp-executable:{requirement_id}:{safe_id(expected_behavior)}",
        "requirement_id": requirement_id,
        "clause_id": row["clause_id"],
        "clause_title": row["clause_title"],
        "source_file": row["source_file"],
        "section_anchor": row["section_anchor"],
        "requirement_kind": row["requirement_kind"],
        "requirement_local_id": row["requirement_local_id"],
        "requirement_text": row["requirement_text"],
        "semantic_family": row["semantic_family"],
        "product_surface": row["product_surface"],
        "mapping_family": "test262_literal_lexer",
        "executable_layer": "literal_lexer",
        "source_path": source_path,
        "source_line": str(source_line),
        "source_snippet": snippet,
        "literal_source": case["literal_source"],
        "literal_source_encoding": literal_source_encoding,
        "expected_parser_result": case["expected_parser_result"],
        "expected_pattern_text": case["expected_pattern_text"],
        "expected_flag_text": case["expected_flag_text"],
        "expected_compile_result": case["expected_compile_result"],
        "expected_behavior": expected_behavior,
        "coverage_credit": "none_test262_literal_lexer_executable_planned",
        "case_state": "planned_not_executable",
        "target_test_artifact": TARGET_TEST_ARTIFACT,
        "exact_case_obligation": row["requirement_text"],
        "next_action": "materialize_test262_literal_lexer_exact_case",
        "extractor_reason": (
            "test262 file contains an executable source snippet for the "
            "ECMA-262 RegExp literal lexical requirement; the focused gate "
            "parses that literal through the public literal lexer"
        ),
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--test262", default="external/test262")
    parser.add_argument("--cache", default="cache")
    parser.add_argument(
        "--requirement-mapping",
        default="cache/ecma262-regexp-requirement-mapping.tsv",
    )
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    test262_root = Path(args.test262)
    cache = Path(args.cache)
    requirement_mapping = Path(args.requirement_mapping)
    detail = cache / DETAIL_NAME
    summary = cache / SUMMARY_NAME

    if not test262_root.is_dir():
        raise SystemExit(f"missing test262 checkout at {test262_root}")
    if not requirement_mapping.is_file():
        raise SystemExit(
            f"missing ECMA-262 requirement mapping at {requirement_mapping}; "
            "run tools/build_ecma262_regexp_requirement_mapping.py first"
        )

    mapping_fields, mapping_rows = read_tsv(requirement_mapping)
    require_columns(
        requirement_mapping,
        mapping_fields,
        {
            "requirement_id",
            "clause_id",
            "clause_title",
            "source_file",
            "section_anchor",
            "requirement_kind",
            "requirement_local_id",
            "requirement_text",
            "coverage_areas",
            "semantic_family",
            "product_surface",
            "route_status",
        },
    )
    source_rows = selected_mapping_rows(mapping_rows)
    rows = [executable_case_row(row, test262_root) for row in source_rows]
    validate_unique_ids(rows, fields=("case_id", "requirement_id"))

    parser_result_counts = Counter(row["expected_parser_result"] for row in rows)
    compile_result_counts = Counter(row["expected_compile_result"] for row in rows)
    credit_counts = Counter(row["coverage_credit"] for row in rows)
    state_counts = Counter(row["case_state"] for row in rows)
    behavior_counts = Counter(row["expected_behavior"] for row in rows)
    family_counts = Counter(row["semantic_family"] for row in rows)
    surface_counts = Counter(row["product_surface"] for row in rows)
    source_counts = Counter(row["source_path"] for row in rows)
    encoding_counts = Counter(row["literal_source_encoding"] for row in rows)

    credit_rows = sum(
        count for credit, count in credit_counts.items() if not credit.startswith("none")
    )

    summary_lines = [
        "ecma262_snapshot\t2026\n",
        f"input_requirement_mapping\t{requirement_mapping}\n",
        f"input_test262\t{test262_root}\n",
        f"executable_case_rows\t{len(rows)}\n",
        f"coverage_credit_rows\t{credit_rows}\n",
        f"target_test_artifact\t{TARGET_TEST_ARTIFACT}\n",
        f"planned_detail_output\t{detail}\n",
        f"planned_summary_output\t{summary}\n",
        f"dry_run\t{bool_text(args.dry_run)}\n",
    ]
    for name, count in sorted(parser_result_counts.items()):
        summary_lines.append(f"parser_result_{name}\t{count}\n")
    for name, count in sorted(compile_result_counts.items()):
        summary_lines.append(f"compile_result_{name}\t{count}\n")
    for name, count in sorted(credit_counts.items()):
        summary_lines.append(f"coverage_credit_{name}\t{count}\n")
    for name, count in sorted(state_counts.items()):
        summary_lines.append(f"case_state_{name}\t{count}\n")
    for name, count in sorted(behavior_counts.items()):
        summary_lines.append(f"expected_behavior_{name}\t{count}\n")
    for name, count in sorted(family_counts.items()):
        summary_lines.append(f"semantic_family_{name}\t{count}\n")
    for name, count in sorted(surface_counts.items()):
        summary_lines.append(f"product_surface_{name}\t{count}\n")
    for name, count in sorted(encoding_counts.items()):
        summary_lines.append(f"literal_source_encoding_{name}\t{count}\n")
    for name, count in sorted(source_counts.items()):
        summary_lines.append(f"source_path_{name}\t{count}\n")

    if args.dry_run:
        print("".join(summary_lines), end="")
        return

    cache.mkdir(parents=True, exist_ok=True)
    fieldnames = [
        "case_id",
        "requirement_id",
        "clause_id",
        "clause_title",
        "source_file",
        "section_anchor",
        "requirement_kind",
        "requirement_local_id",
        "requirement_text",
        "semantic_family",
        "product_surface",
        "mapping_family",
        "executable_layer",
        "source_path",
        "source_line",
        "source_snippet",
        "literal_source",
        "literal_source_encoding",
        "expected_parser_result",
        "expected_pattern_text",
        "expected_flag_text",
        "expected_compile_result",
        "expected_behavior",
        "coverage_credit",
        "case_state",
        "target_test_artifact",
        "exact_case_obligation",
        "next_action",
        "extractor_reason",
    ]
    with detail.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, delimiter="\t", fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)
    summary.write_text("".join(summary_lines), encoding="utf-8")


if __name__ == "__main__":
    main()
