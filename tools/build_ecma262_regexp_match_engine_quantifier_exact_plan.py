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


DETAIL_NAME = "ecma262-regexp-match-engine-quantifier-exact-plan.tsv"
SUMMARY_NAME = "ecma262-regexp-match-engine-quantifier-exact-plan.summary"
TARGET_TEST_ARTIFACT = "test/test_ecma262_match_engine_quantifier_exact_plan.ml"
SOURCE_FAILURE_FAMILY = "matcher_runtime_quantifier"


CASE_TEMPLATES = {
    "repeat_recursive_many": {
        "pattern": "a*",
        "input": "aaa",
        "expected_search_result": "true",
        "expected_exec_result": "true",
        "expected_start_index": "0",
        "expected_end_index": "3",
        "expected_match_text": "aaa",
        "expected_behavior": "repeat_matcher_recursive_many",
    },
    "repeat_zero_max_continuation": {
        "pattern": "a{0}b",
        "input": "b",
        "expected_search_result": "true",
        "expected_exec_result": "true",
        "expected_start_index": "0",
        "expected_end_index": "1",
        "expected_match_text": "b",
        "expected_behavior": "repeat_matcher_zero_max_continuation",
    },
    "repeat_zero_width_guard": {
        "pattern": "()*a",
        "input": "a",
        "expected_search_result": "true",
        "expected_exec_result": "true",
        "expected_start_index": "0",
        "expected_end_index": "1",
        "expected_match_text": "a",
        "expected_behavior": "repeat_matcher_zero_width_progress_guard",
    },
    "repeat_capture_reset": {
        "pattern": "(a)*b",
        "input": "aaab",
        "expected_search_result": "true",
        "expected_exec_result": "true",
        "expected_start_index": "0",
        "expected_end_index": "4",
        "expected_match_text": "aaab",
        "expected_behavior": "repeat_matcher_capture_state_rewritten",
    },
    "repeat_greedy_suffix_backtracking": {
        "pattern": "a*a",
        "input": "aaa",
        "expected_search_result": "true",
        "expected_exec_result": "true",
        "expected_start_index": "0",
        "expected_end_index": "3",
        "expected_match_text": "aaa",
        "expected_behavior": "repeat_matcher_greedy_backtracks_for_suffix",
    },
    "repeat_lazy_suffix_shortest": {
        "pattern": "a*?a",
        "input": "aaa",
        "expected_search_result": "true",
        "expected_exec_result": "true",
        "expected_start_index": "0",
        "expected_end_index": "1",
        "expected_match_text": "a",
        "expected_behavior": "repeat_matcher_lazy_tries_continuation_first",
    },
    "compile_quantifier_greedy": {
        "pattern": "a*a",
        "input": "aaa",
        "expected_search_result": "true",
        "expected_exec_result": "true",
        "expected_start_index": "0",
        "expected_end_index": "3",
        "expected_match_text": "aaa",
        "expected_behavior": "compile_quantifier_greedy_true",
    },
    "compile_quantifier_lazy": {
        "pattern": "a*?a",
        "input": "aaa",
        "expected_search_result": "true",
        "expected_exec_result": "true",
        "expected_start_index": "0",
        "expected_end_index": "1",
        "expected_match_text": "a",
        "expected_behavior": "compile_quantifier_greedy_false",
    },
    "prefix_star_many": {
        "pattern": "^a*$",
        "input": "aaa",
        "expected_search_result": "true",
        "expected_exec_result": "true",
        "expected_start_index": "0",
        "expected_end_index": "3",
        "expected_match_text": "aaa",
        "expected_behavior": "quantifier_prefix_star_min_zero_max_infinity",
    },
    "prefix_plus_many": {
        "pattern": "^a+$",
        "input": "aaa",
        "expected_search_result": "true",
        "expected_exec_result": "true",
        "expected_start_index": "0",
        "expected_end_index": "3",
        "expected_match_text": "aaa",
        "expected_behavior": "quantifier_prefix_plus_min_one_max_infinity",
    },
    "prefix_plus_rejects_zero": {
        "pattern": "^a+$",
        "input": "",
        "expected_search_result": "false",
        "expected_exec_result": "false",
        "expected_start_index": "",
        "expected_end_index": "",
        "expected_match_text": "",
        "expected_behavior": "quantifier_prefix_plus_requires_one",
    },
    "prefix_question_accepts_zero": {
        "pattern": "^ab?c$",
        "input": "ac",
        "expected_search_result": "true",
        "expected_exec_result": "true",
        "expected_start_index": "0",
        "expected_end_index": "2",
        "expected_match_text": "ac",
        "expected_behavior": "quantifier_prefix_question_accepts_zero",
    },
    "prefix_question_rejects_two": {
        "pattern": "^ab?c$",
        "input": "abbc",
        "expected_search_result": "false",
        "expected_exec_result": "false",
        "expected_start_index": "",
        "expected_end_index": "",
        "expected_match_text": "",
        "expected_behavior": "quantifier_prefix_question_max_one",
    },
    "prefix_braced_exact": {
        "pattern": "^a{2}$",
        "input": "aa",
        "expected_search_result": "true",
        "expected_exec_result": "true",
        "expected_start_index": "0",
        "expected_end_index": "2",
        "expected_match_text": "aa",
        "expected_behavior": "quantifier_prefix_braced_exact",
    },
    "prefix_braced_exact_rejects_short": {
        "pattern": "^a{2}$",
        "input": "a",
        "expected_search_result": "false",
        "expected_exec_result": "false",
        "expected_start_index": "",
        "expected_end_index": "",
        "expected_match_text": "",
        "expected_behavior": "quantifier_prefix_braced_exact_requires_count",
    },
    "prefix_braced_open": {
        "pattern": "^a{2,}$",
        "input": "aaa",
        "expected_search_result": "true",
        "expected_exec_result": "true",
        "expected_start_index": "0",
        "expected_end_index": "3",
        "expected_match_text": "aaa",
        "expected_behavior": "quantifier_prefix_braced_open_max_infinity",
    },
    "prefix_braced_range": {
        "pattern": "^a{2,3}$",
        "input": "aaa",
        "expected_search_result": "true",
        "expected_exec_result": "true",
        "expected_start_index": "0",
        "expected_end_index": "3",
        "expected_match_text": "aaa",
        "expected_behavior": "quantifier_prefix_braced_range",
    },
    "prefix_braced_range_rejects_overflow": {
        "pattern": "^a{2,3}$",
        "input": "aaaa",
        "expected_search_result": "false",
        "expected_exec_result": "false",
        "expected_start_index": "",
        "expected_end_index": "",
        "expected_match_text": "",
        "expected_behavior": "quantifier_prefix_braced_range_max_bound",
    },
}


def include_requirement_row(row: dict[str, str]) -> bool:
    return (
        row["product_surface"] == "match_engine"
        and row["semantic_family"] == "quantifiers"
        and row["route_status"] == "needs_requirement_to_test_case_mapping"
    )


def selected_requirement_rows(rows: list[dict[str, str]]) -> list[dict[str, str]]:
    return select_requirement_rows(
        rows,
        include_row=include_requirement_row,
        expected_count=45,
        count_message=lambda count: (
            "expected 45 match-engine quantifier requirement rows, got "
            f"{count}"
        ),
    )


def validate_requirement_row(row: dict[str, str]) -> None:
    expected = {
        "product_surface": "match_engine",
        "semantic_family": "quantifiers",
        "route_status": "needs_requirement_to_test_case_mapping",
    }
    validate_expected_fields(row, expected, context="quantifier row")
    require_coverage_area(
        row,
        "regexp_exec_and_captures",
        context="quantifier row",
    )


def template_name_for_requirement(row: dict[str, str]) -> str:
    requirement_id = row["requirement_id"]
    clause_id = row["clause_id"]
    ordinal = int(requirement_id.rsplit("-", 1)[1])
    if clause_id == "22.2.2.3.1":
        if ordinal == 2:
            return "repeat_zero_max_continuation"
        if ordinal == 5:
            return "repeat_zero_width_guard"
        if 9 <= ordinal <= 13:
            return "repeat_capture_reset"
        if 15 <= ordinal <= 18:
            return "repeat_lazy_suffix_shortest"
        if 19 <= ordinal <= 21:
            return "repeat_greedy_suffix_backtracking"
        return "repeat_recursive_many"
    if clause_id == "22.2.2.5":
        if ordinal <= 4:
            return "compile_quantifier_greedy"
        return "compile_quantifier_lazy"
    if clause_id == "22.2.2.6":
        return {
            1: "prefix_star_many",
            2: "prefix_star_many",
            3: "prefix_star_many",
            4: "prefix_plus_many",
            5: "prefix_plus_rejects_zero",
            6: "prefix_question_accepts_zero",
            7: "prefix_question_rejects_two",
            8: "prefix_braced_exact",
            9: "prefix_braced_exact",
            10: "prefix_braced_exact_rejects_short",
            11: "prefix_braced_open",
            12: "prefix_braced_open",
            13: "prefix_braced_open",
            14: "prefix_braced_range",
            15: "prefix_braced_range",
            16: "prefix_braced_range",
            17: "prefix_braced_range_rejects_overflow",
        }[ordinal]
    raise SystemExit(f"unexpected quantifier clause for {requirement_id}: {clause_id}")


def source_failure_rows(rows: list[dict[str, str]]) -> list[dict[str, str]]:
    return [row for row in rows if row["failure_family"] == SOURCE_FAILURE_FAMILY]


def plan_row(
    requirement: dict[str, str],
    source_failure_count: int,
) -> dict[str, str]:
    validate_requirement_row(requirement)
    requirement_id = requirement["requirement_id"]
    template_name = template_name_for_requirement(requirement)
    case = CASE_TEMPLATES[template_name]
    exact_case_id = (
        f"match-engine-quantifier-exact:{requirement_id}:{safe_id(template_name)}"
    )
    if source_failure_count > 0:
        plan_reason = (
            "JSON Schema failure inventory currently exposes quantifiers as a "
            "matcher blocker; exact ECMA-262 quantifier cases must go green "
            "before any corpus-driven implementation credit"
        )
    else:
        plan_reason = (
            "JSON Schema failure inventory no longer exposes quantifiers as a "
            "current blocker; the exact ECMA-262 quantifier cases remain in "
            "the coverage system as regression evidence"
        )
    return {
        "plan_id": f"match-engine-quantifier-exact-plan:{requirement_id}",
        **copy_requirement_metadata(requirement, include_local_id=False),
        "mapping_family": "match_engine_quantifiers",
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
        "source_failure_family": SOURCE_FAILURE_FAMILY,
        "source_failure_count": str(source_failure_count),
        "coverage_credit": "none_match_engine_quantifier_exact_planned",
        "plan_state": "planned_not_executable",
        "target_test_artifact": TARGET_TEST_ARTIFACT,
        "exact_case_obligation": (
            "Quantifier exact case selected from ECMA-262 "
            f"{requirement['clause_title']} requirement {requirement_id}"
        ),
        "observability_status": "search_and_exec_observable",
        "observability_reason": (
            "public Ecma_regex.search observes boolean success and public "
            "Ecma_regex.exec observes start, end, and matched text for "
            "quantifier repeat, bound, greediness, and continuation behavior"
        ),
        "next_action": "materialize_match_engine_quantifier_exact_case",
        "plan_reason": plan_reason,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--cache", default="cache")
    parser.add_argument(
        "--requirements",
        default="cache/ecma262-regexp-requirement-mapping.tsv",
    )
    parser.add_argument(
        "--json-schema-inventory",
        default="cache/json-schema-corpus-failure-inventory.tsv",
    )
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    cache = Path(args.cache)
    requirements = Path(args.requirements)
    inventory = Path(args.json_schema_inventory)
    detail = cache / DETAIL_NAME
    summary = cache / SUMMARY_NAME

    if not requirements.is_file():
        raise SystemExit(
            f"missing ECMA-262 requirement mapping at {requirements}; "
            "run tools/build_ecma262_regexp_requirement_mapping.py first"
        )
    if not inventory.is_file():
        raise SystemExit(
            f"missing JSON Schema corpus failure inventory at {inventory}; "
            "run tools/build_json_schema_corpus_failure_inventory.py first"
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
    inventory_fields, inventory_rows = read_tsv(inventory)
    require_columns(
        inventory,
        inventory_fields,
        {"failure_family", "schema_keyword", "schema_shape", "case_description", "patterns"},
    )

    source_rows = source_failure_rows(inventory_rows)
    rows = [
        plan_row(row, len(source_rows))
        for row in selected_requirement_rows(requirement_rows)
    ]
    validate_unique_ids(rows)

    state_counts = Counter(row["plan_state"] for row in rows)
    credit_counts = Counter(row["coverage_credit"] for row in rows)
    behavior_counts = Counter(row["expected_behavior"] for row in rows)
    search_counts = Counter(row["expected_search_result"] for row in rows)
    exec_counts = Counter(row["expected_exec_result"] for row in rows)
    clause_counts = Counter(row["clause_id"] for row in rows)
    family_counts = Counter(row["exact_case_family"] for row in rows)
    source_keyword_counts = Counter(row["schema_keyword"] for row in source_rows)
    source_shape_counts = Counter(row["schema_shape"] for row in source_rows)

    coverage_credit_rows = sum(
        count for credit, count in credit_counts.items() if not credit.startswith("none")
    )
    planned_executable_rows = state_counts.get("planned_not_executable", 0)

    summary_lines = [
        "ecma262_snapshot\t2026\n",
        f"input_requirements\t{requirements}\n",
        f"input_json_schema_inventory\t{inventory}\n",
        f"source_failure_family\t{SOURCE_FAILURE_FAMILY}\n",
        f"source_failure_rows\t{len(source_rows)}\n",
        f"match_engine_quantifier_exact_plan_rows\t{len(rows)}\n",
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
    for name, count in sorted(clause_counts.items()):
        summary_lines.append(f"clause_id_{name}\t{count}\n")
    for name, count in sorted(family_counts.items()):
        summary_lines.append(f"exact_case_family_{name}\t{count}\n")
    for name, count in sorted(source_keyword_counts.items()):
        summary_lines.append(f"source_schema_keyword_{name}\t{count}\n")
    for name, count in sorted(source_shape_counts.items()):
        summary_lines.append(f"source_schema_shape_{name}\t{count}\n")

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
        "source_failure_family",
        "source_failure_count",
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
