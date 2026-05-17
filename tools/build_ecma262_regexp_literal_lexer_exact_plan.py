#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
from collections import Counter
from pathlib import Path

from ecma262_tooling import (
    bool_text,
    copy_requirement_metadata,
    read_tsv,
    require_columns,
    require_coverage_area,
    safe_id,
    select_exact_case_requirement_rows,
    validate_expected_fields,
    validate_unique_ids,
)


DETAIL_NAME = "ecma262-regexp-literal-lexer-exact-plan.tsv"
SUMMARY_NAME = "ecma262-regexp-literal-lexer-exact-plan.summary"
TARGET_TEST_ARTIFACT = "test/test_ecma262_literal_lexer_exact_plan.ml"


EXACT_CASES = {
    "ecma262-12.9.5.2-0001": {
        "family": "flagtext_sdo_returns_source_text",
        "literal": "/alpha/gim",
        "pattern_text": "alpha",
        "flag_text": "gim",
        "obligation": "FlagText is a syntax-directed operation that returns source text",
    },
    "ecma262-12.9.5.2-0002": {
        "family": "regular_expression_literal_flags_tail",
        "literal": "/a\\/b/dy",
        "pattern_text": "a\\/b",
        "flag_text": "dy",
        "obligation": "RegularExpressionLiteral recognizes RegularExpressionFlags after the closing slash delimiter",
    },
    "ecma262-12.9.5.2-0003": {
        "family": "flagtext_algorithm_returns_recognized_flags",
        "literal": "/[a/]/su",
        "pattern_text": "[a/]",
        "flag_text": "su",
        "obligation": "FlagText returns the source text recognized as RegularExpressionFlags",
    },
}


def validate_requirement_row(row: dict[str, str]) -> None:
    requirement_id = row["requirement_id"]
    expected = {
        "clause_id": "12.9.5.2",
        "clause_title": "Static Semantics: FlagText",
        "semantic_family": "flags",
        "product_surface": "literal_lexer",
    }
    validate_expected_fields(row, expected, context="literal lexer exact row")
    require_coverage_area(row, "regexp_flags", context="literal lexer exact row")


def plan_row(row: dict[str, str]) -> dict[str, str]:
    validate_requirement_row(row)
    requirement_id = row["requirement_id"]
    case = EXACT_CASES[requirement_id]
    exact_case_id = f"literal-lexer-exact:{requirement_id}:{safe_id(case['family'])}"
    return {
        "plan_id": f"literal-lexer-exact-plan:{requirement_id}",
        **copy_requirement_metadata(row, include_local_id=False),
        "mapping_family": "literal_lexer_exact",
        "executable_layer": "literal_lexer",
        "exact_case_family": case["family"],
        "exact_case_id": exact_case_id,
        "literal_source": case["literal"],
        "expected_pattern_text": case["pattern_text"],
        "expected_flag_text": case["flag_text"],
        "expected_behavior": "literal_parse_ok",
        "coverage_credit": "none_literal_lexer_exact_planned",
        "plan_state": "planned_not_executable",
        "target_test_artifact": TARGET_TEST_ARTIFACT,
        "exact_case_obligation": case["obligation"],
        "next_action": "materialize_literal_lexer_exact_case",
        "plan_reason": (
            "literal lexer exact case is planned from the ECMA-262 FlagText "
            "requirement row; no ledger credit is assigned until the "
            "executable gate and exactness audit consume it"
        ),
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--cache", default="cache")
    parser.add_argument(
        "--requirements",
        default="cache/ecma262-regexp-requirement-mapping.tsv",
    )
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    cache = Path(args.cache)
    requirements = Path(args.requirements)
    detail = cache / DETAIL_NAME
    summary = cache / SUMMARY_NAME

    if not requirements.is_file():
        raise SystemExit(
            f"missing ECMA-262 requirement mapping at {requirements}; "
            "run tools/build_ecma262_regexp_requirement_mapping.py first"
        )

    requirement_fields, requirement_rows = read_tsv(requirements)
    require_columns(
        requirements,
        requirement_fields,
        {
            "requirement_id",
            "clause_id",
            "clause_title",
            "source_file",
            "section_anchor",
            "requirement_kind",
            "requirement_text",
            "coverage_areas",
            "semantic_family",
            "product_surface",
        },
    )
    source_rows = select_exact_case_requirement_rows(requirement_rows, EXACT_CASES)
    rows = [plan_row(row) for row in source_rows]
    validate_unique_ids(rows)

    state_counts = Counter(row["plan_state"] for row in rows)
    credit_counts = Counter(row["coverage_credit"] for row in rows)
    expected_counts = Counter(row["expected_behavior"] for row in rows)
    layer_counts = Counter(row["executable_layer"] for row in rows)
    family_counts = Counter(row["exact_case_family"] for row in rows)
    target_counts = Counter(row["target_test_artifact"] for row in rows)

    coverage_credit_rows = sum(
        count for credit, count in credit_counts.items() if not credit.startswith("none")
    )

    summary_lines = [
        "ecma262_snapshot\t2026\n",
        f"input_requirements\t{requirements}\n",
        f"input_requirement_rows\t{len(requirement_rows)}\n",
        f"source_requirement_rows\t{len(source_rows)}\n",
        f"literal_lexer_exact_plan_rows\t{len(rows)}\n",
        f"planned_executable_rows\t{state_counts.get('planned_not_executable', 0)}\n",
        f"coverage_credit_rows\t{coverage_credit_rows}\n",
        f"planned_detail_output\t{detail}\n",
        f"planned_summary_output\t{summary}\n",
        f"dry_run\t{bool_text(args.dry_run)}\n",
    ]
    for name, count in sorted(state_counts.items()):
        summary_lines.append(f"plan_state_{name}\t{count}\n")
    for name, count in sorted(credit_counts.items()):
        summary_lines.append(f"coverage_credit_{name}\t{count}\n")
    for name, count in sorted(expected_counts.items()):
        summary_lines.append(f"expected_behavior_{name}\t{count}\n")
    for name, count in sorted(layer_counts.items()):
        summary_lines.append(f"executable_layer_{name}\t{count}\n")
    for name, count in sorted(family_counts.items()):
        summary_lines.append(f"exact_case_family_{name}\t{count}\n")
    for name, count in sorted(target_counts.items()):
        summary_lines.append(f"target_test_artifact_{name}\t{count}\n")

    if args.dry_run:
        print("".join(summary_lines), end="")
        return

    cache.mkdir(parents=True, exist_ok=True)
    fieldnames = [
        "plan_id",
        "requirement_id",
        "clause_id",
        "clause_title",
        "source_file",
        "section_anchor",
        "requirement_kind",
        "requirement_text",
        "mapping_family",
        "executable_layer",
        "exact_case_family",
        "exact_case_id",
        "literal_source",
        "expected_pattern_text",
        "expected_flag_text",
        "expected_behavior",
        "coverage_credit",
        "plan_state",
        "target_test_artifact",
        "exact_case_obligation",
        "next_action",
        "plan_reason",
    ]
    with detail.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, delimiter="\t", fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)
    with summary.open("w", encoding="utf-8") as f:
        f.write("".join(summary_lines))
    print(summary.read_text(encoding="utf-8"), end="")


if __name__ == "__main__":
    main()
