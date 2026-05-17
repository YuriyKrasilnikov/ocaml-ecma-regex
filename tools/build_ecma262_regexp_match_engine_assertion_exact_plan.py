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
    select_requirement_rows,
    validate_expected_fields,
    validate_unique_ids,
)


DETAIL_NAME = "ecma262-regexp-match-engine-assertion-exact-plan.tsv"
SUMMARY_NAME = "ecma262-regexp-match-engine-assertion-exact-plan.summary"
TARGET_TEST_ARTIFACT = "test/test_ecma262_match_engine_assertion_exact_plan.ml"
SEPARATE_ANCHOR_EXACT_REQUIREMENTS = {
    "ecma262-22.2.2.4-0003",
    "ecma262-22.2.2.4-0009",
    "ecma262-22.2.2.4-0011",
    "ecma262-22.2.2.4-0012",
    "ecma262-22.2.2.4-0019",
    "ecma262-22.2.2.4-0021",
}


CASE_TEMPLATES = {
    "compile_assertion_dispatch": {
        "pattern": "(?=a)a",
        "input": "a",
        "expected_search_result": "true",
        "expected_exec_result": "true",
        "expected_start_index": "0",
        "expected_end_index": "1",
        "expected_match_text": "a",
        "expected_behavior": "compile_assertion_dispatches_to_matcher",
    },
    "start_anchor_generic": {
        "pattern": "^a",
        "input": "a",
        "expected_search_result": "true",
        "expected_exec_result": "true",
        "expected_start_index": "0",
        "expected_end_index": "1",
        "expected_match_text": "a",
        "expected_behavior": "start_anchor_matcher_continuation_observable",
    },
    "end_anchor_generic": {
        "pattern": "a$",
        "input": "a",
        "expected_search_result": "true",
        "expected_exec_result": "true",
        "expected_start_index": "0",
        "expected_end_index": "1",
        "expected_match_text": "a",
        "expected_behavior": "end_anchor_matcher_continuation_observable",
    },
    "word_boundary_success": {
        "pattern": "\\ba",
        "input": "a",
        "expected_search_result": "true",
        "expected_exec_result": "true",
        "expected_start_index": "0",
        "expected_end_index": "1",
        "expected_match_text": "a",
        "expected_behavior": "word_boundary_iswordchar_diff_success",
    },
    "word_boundary_failure": {
        "pattern": "a\\b",
        "input": "ab",
        "expected_search_result": "false",
        "expected_exec_result": "false",
        "expected_start_index": "",
        "expected_end_index": "",
        "expected_match_text": "",
        "expected_behavior": "word_boundary_iswordchar_same_failure",
    },
    "non_word_boundary_success": {
        "pattern": "a\\B",
        "input": "ab",
        "expected_search_result": "true",
        "expected_exec_result": "true",
        "expected_start_index": "0",
        "expected_end_index": "1",
        "expected_match_text": "a",
        "expected_behavior": "non_word_boundary_iswordchar_same_success",
    },
    "non_word_boundary_failure": {
        "pattern": "\\Ba",
        "input": "a",
        "expected_search_result": "false",
        "expected_exec_result": "false",
        "expected_start_index": "",
        "expected_end_index": "",
        "expected_match_text": "",
        "expected_behavior": "non_word_boundary_iswordchar_diff_failure",
    },
    "positive_lookahead_success": {
        "pattern": "(?=a)a",
        "input": "a",
        "expected_search_result": "true",
        "expected_exec_result": "true",
        "expected_start_index": "0",
        "expected_end_index": "1",
        "expected_match_text": "a",
        "expected_behavior": "positive_lookahead_submatcher_success_resets_index",
    },
    "positive_lookahead_failure": {
        "pattern": "(?=b)a",
        "input": "a",
        "expected_search_result": "false",
        "expected_exec_result": "false",
        "expected_start_index": "",
        "expected_end_index": "",
        "expected_match_text": "",
        "expected_behavior": "positive_lookahead_submatcher_failure_blocks_match",
    },
    "positive_lookahead_capture_visible": {
        "pattern": "(?=(a))\\1",
        "input": "a",
        "expected_search_result": "true",
        "expected_exec_result": "true",
        "expected_start_index": "0",
        "expected_end_index": "1",
        "expected_match_text": "a",
        "expected_behavior": "positive_lookahead_captures_feed_outer_continuation",
    },
    "negative_lookahead_success": {
        "pattern": "(?!b)a",
        "input": "a",
        "expected_search_result": "true",
        "expected_exec_result": "true",
        "expected_start_index": "0",
        "expected_end_index": "1",
        "expected_match_text": "a",
        "expected_behavior": "negative_lookahead_submatcher_failure_allows_match",
    },
    "negative_lookahead_failure": {
        "pattern": "(?!a)a",
        "input": "a",
        "expected_search_result": "false",
        "expected_exec_result": "false",
        "expected_start_index": "",
        "expected_end_index": "",
        "expected_match_text": "",
        "expected_behavior": "negative_lookahead_submatcher_success_blocks_match",
    },
    "positive_lookbehind_success": {
        "pattern": "(?<=a)b",
        "input": "ab",
        "expected_search_result": "true",
        "expected_exec_result": "true",
        "expected_start_index": "1",
        "expected_end_index": "2",
        "expected_match_text": "b",
        "expected_behavior": "positive_lookbehind_submatcher_success_resets_index",
    },
    "positive_lookbehind_failure": {
        "pattern": "(?<=b)a",
        "input": "a",
        "expected_search_result": "false",
        "expected_exec_result": "false",
        "expected_start_index": "",
        "expected_end_index": "",
        "expected_match_text": "",
        "expected_behavior": "positive_lookbehind_submatcher_failure_blocks_match",
    },
    "positive_lookbehind_capture_visible": {
        "pattern": "(?<=(a))\\1",
        "input": "aa",
        "expected_search_result": "true",
        "expected_exec_result": "true",
        "expected_start_index": "1",
        "expected_end_index": "2",
        "expected_match_text": "a",
        "expected_behavior": "positive_lookbehind_captures_feed_outer_continuation",
    },
    "negative_lookbehind_success": {
        "pattern": "(?<!b)a",
        "input": "a",
        "expected_search_result": "true",
        "expected_exec_result": "true",
        "expected_start_index": "0",
        "expected_end_index": "1",
        "expected_match_text": "a",
        "expected_behavior": "negative_lookbehind_submatcher_failure_allows_match",
    },
    "negative_lookbehind_failure": {
        "pattern": "(?<!a)b",
        "input": "ab",
        "expected_search_result": "false",
        "expected_exec_result": "false",
        "expected_start_index": "",
        "expected_end_index": "",
        "expected_match_text": "",
        "expected_behavior": "negative_lookbehind_submatcher_success_blocks_match",
    },
}


def include_requirement_row(row: dict[str, str]) -> bool:
    return (
        row["product_surface"] == "match_engine"
        and row["semantic_family"] == "assertions"
        and row["route_status"] == "needs_requirement_to_test_case_mapping"
        and row["requirement_id"] not in SEPARATE_ANCHOR_EXACT_REQUIREMENTS
    )


def selected_requirement_rows(rows: list[dict[str, str]]) -> list[dict[str, str]]:
    return select_requirement_rows(
        rows,
        include_row=include_requirement_row,
        expected_count=89,
        count_message=lambda count: (
            "expected 89 open match-engine assertion worklist rows, got "
            f"{count}"
        ),
    )


def validate_requirement_row(row: dict[str, str]) -> None:
    expected = {
        "clause_id": "22.2.2.4",
        "semantic_family": "assertions",
        "product_surface": "match_engine",
        "route_status": "needs_requirement_to_test_case_mapping",
    }
    validate_expected_fields(row, expected, context="assertion row")
    require_coverage_area(
        row,
        "regexp_exec_and_captures",
        context="assertion row",
    )


def ordinal(row: dict[str, str]) -> int:
    return int(row["requirement_id"].rsplit("-", 1)[1])


def template_name_for_requirement(row: dict[str, str]) -> str:
    n = ordinal(row)
    if n in {1, 2}:
        return "compile_assertion_dispatch"
    if n in {4, 5, 6, 7, 8, 10}:
        return "start_anchor_generic"
    if n in {13, 14, 15, 16, 17, 18, 20}:
        return "end_anchor_generic"
    if 22 <= n <= 30:
        return "word_boundary_success"
    if n == 31:
        return "word_boundary_failure"
    if 32 <= n <= 40:
        return "non_word_boundary_success"
    if n == 41:
        return "non_word_boundary_failure"
    if 42 <= n <= 57:
        if n == 51:
            return "positive_lookahead_failure"
        if 53 <= n <= 57:
            return "positive_lookahead_capture_visible"
        return "positive_lookahead_success"
    if 58 <= n <= 68:
        if n == 67:
            return "negative_lookahead_failure"
        return "negative_lookahead_success"
    if 69 <= n <= 84:
        if n == 78:
            return "positive_lookbehind_failure"
        if 80 <= n <= 84:
            return "positive_lookbehind_capture_visible"
        return "positive_lookbehind_success"
    if 85 <= n <= 95:
        if n == 94:
            return "negative_lookbehind_failure"
        return "negative_lookbehind_success"
    raise SystemExit(f"unexpected assertion requirement ordinal {n}")


def plan_row(requirement: dict[str, str]) -> dict[str, str]:
    validate_requirement_row(requirement)
    requirement_id = requirement["requirement_id"]
    template_name = template_name_for_requirement(requirement)
    case = CASE_TEMPLATES[template_name]
    exact_case_id = (
        f"match-engine-assertion-exact:{requirement_id}:{safe_id(template_name)}"
    )
    return {
        "plan_id": f"match-engine-assertion-exact-plan:{requirement_id}",
        **copy_requirement_metadata(requirement, include_local_id=False),
        "mapping_family": "match_engine_assertions",
        "executable_layer": "match_engine",
        "exact_case_family": template_name,
        "exact_case_id": exact_case_id,
        "pattern": case["pattern"],
        "flags": "",
        "input_text": case["input"],
        "expected_search_result": case["expected_search_result"],
        "expected_exec_result": case["expected_exec_result"],
        "expected_start_index": case["expected_start_index"],
        "expected_end_index": case["expected_end_index"],
        "expected_match_text": case["expected_match_text"],
        "expected_behavior": case["expected_behavior"],
        "coverage_credit": "none_match_engine_assertion_exact_planned",
        "plan_state": "planned_not_executable",
        "target_test_artifact": TARGET_TEST_ARTIFACT,
        "exact_case_obligation": (
            "Assertion exact case selected from ECMA-262 "
            f"{requirement['clause_title']} requirement {requirement_id}"
        ),
        "observability_status": "search_and_exec_observable",
        "observability_reason": (
            "public Ecma_regex.search observes boolean assertion success and "
            "public Ecma_regex.exec observes zero-width assertion interaction "
            "with continuation, captures, and consumed suffix"
        ),
        "next_action": "materialize_match_engine_assertion_exact_case",
        "plan_reason": (
            "ECMA-262 CompileAssertion row is open in the exact requirement "
            "worklist and needs executable search/exec evidence"
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
            "route_status",
        },
    )

    rows = [plan_row(row) for row in selected_requirement_rows(requirement_rows)]
    validate_unique_ids(rows)

    state_counts = Counter(row["plan_state"] for row in rows)
    credit_counts = Counter(row["coverage_credit"] for row in rows)
    behavior_counts = Counter(row["expected_behavior"] for row in rows)
    search_counts = Counter(row["expected_search_result"] for row in rows)
    exec_counts = Counter(row["expected_exec_result"] for row in rows)
    family_counts = Counter(row["exact_case_family"] for row in rows)

    coverage_credit_rows = sum(
        count for credit, count in credit_counts.items() if not credit.startswith("none")
    )
    planned_executable_rows = state_counts.get("planned_not_executable", 0)

    summary_lines = [
        "ecma262_snapshot\t2026\n",
        f"input_requirements\t{requirements}\n",
        f"input_requirement_rows\t{len(requirement_rows)}\n",
        f"separate_anchor_exact_requirement_rows\t{len(SEPARATE_ANCHOR_EXACT_REQUIREMENTS)}\n",
        f"match_engine_assertion_exact_plan_rows\t{len(rows)}\n",
        f"planned_executable_rows\t{planned_executable_rows}\n",
        f"coverage_credit_rows\t{coverage_credit_rows}\n",
        f"planned_detail_output\t{detail}\n",
        f"planned_summary_output\t{summary}\n",
        f"dry_run\t{bool_text(args.dry_run)}\n",
    ]
    for name, count in sorted(state_counts.items()):
        summary_lines.append(f"plan_state_{name}\t{count}\n")
    for name, count in sorted(credit_counts.items()):
        summary_lines.append(f"coverage_credit_{name}\t{count}\n")
    for name, count in sorted(behavior_counts.items()):
        summary_lines.append(f"expected_behavior_{name}\t{count}\n")
    for name, count in sorted(search_counts.items()):
        summary_lines.append(f"expected_search_result_{name}\t{count}\n")
    for name, count in sorted(exec_counts.items()):
        summary_lines.append(f"expected_exec_result_{name}\t{count}\n")
    for name, count in sorted(family_counts.items()):
        summary_lines.append(f"exact_case_family_{name}\t{count}\n")

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
        "pattern",
        "flags",
        "input_text",
        "expected_search_result",
        "expected_exec_result",
        "expected_start_index",
        "expected_end_index",
        "expected_match_text",
        "expected_behavior",
        "coverage_credit",
        "plan_state",
        "target_test_artifact",
        "exact_case_obligation",
        "observability_status",
        "observability_reason",
        "next_action",
        "plan_reason",
    ]
    with detail.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames, delimiter="\t", lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)
    summary.write_text("".join(summary_lines), encoding="utf-8")


if __name__ == "__main__":
    main()
