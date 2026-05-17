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
    rows_by_requirement_id,
    safe_id,
    validate_expected_fields,
    validate_unique_ids,
)


DETAIL_NAME = "ecma262-regexp-match-engine-start-anchor-exact-plan.tsv"
SUMMARY_NAME = "ecma262-regexp-match-engine-start-anchor-exact-plan.summary"
TARGET_TEST_ARTIFACT = "test/test_ecma262_match_engine_start_anchor_exact_plan.ml"
SOURCE_FAILURE_FAMILY = "matcher_runtime_start_anchor"


EXACT_CASES = [
    {
        "requirement_id": "ecma262-22.2.2.4-0003",
        "family": "start_anchor_grammar_routes_to_assertion_matcher",
        "pattern": "^",
        "flags": "",
        "input": "abc",
        "expected_search_result": "true",
        "expected_exec_result": "true",
        "expected_start_index": "0",
        "expected_end_index": "0",
        "expected_match_text": "",
        "expected_behavior": "start_anchor_zero_width_match_at_input_start",
        "obligation": (
            "Assertion :: ^ is a zero-width assertion and can return c(x) "
            "without consuming input at the beginning of the input"
        ),
    },
    {
        "requirement_id": "ecma262-22.2.2.4-0009",
        "family": "start_anchor_accepts_input_start",
        "pattern": "^a",
        "flags": "",
        "input": "abc",
        "expected_search_result": "true",
        "expected_exec_result": "true",
        "expected_start_index": "0",
        "expected_end_index": "1",
        "expected_match_text": "a",
        "expected_behavior": "start_anchor_condition_input_start_success",
        "obligation": (
            "If e = 0, the ^ assertion succeeds and invokes the continuation "
            "with the same match state"
        ),
    },
    {
        "requirement_id": "ecma262-22.2.2.4-0011",
        "family": "start_anchor_rejects_later_search_index",
        "pattern": "^a",
        "flags": "",
        "input": "ba",
        "expected_search_result": "false",
        "expected_exec_result": "false",
        "expected_start_index": "",
        "expected_end_index": "",
        "expected_match_text": "",
        "expected_behavior": "start_anchor_condition_failure_blocks_search_loop",
        "obligation": (
            "When e is not 0 and multiline does not permit the position, the "
            "^ assertion returns failure; the public search loop must not turn "
            "a later input index into an unanchored match"
        ),
    },
    {
        "requirement_id": "ecma262-22.2.2.4-0009",
        "family": "start_anchor_multiline_accepts_after_lf",
        "pattern": "^a",
        "flags": "m",
        "input": "x\\na",
        "expected_search_result": "true",
        "expected_exec_result": "true",
        "expected_start_index": "2",
        "expected_end_index": "3",
        "expected_match_text": "a",
        "expected_behavior": "start_anchor_multiline_line_terminator_success",
        "obligation": (
            "If rer.[[Multiline]] is true and Input[e - 1] is a line "
            "terminator, the ^ assertion succeeds at that position"
        ),
    },
    {
        "requirement_id": "ecma262-22.2.2.4-0009",
        "family": "start_anchor_multiline_accepts_after_cr",
        "pattern": "^a",
        "flags": "m",
        "input": "x\\ra",
        "expected_search_result": "true",
        "expected_exec_result": "true",
        "expected_start_index": "2",
        "expected_end_index": "3",
        "expected_match_text": "a",
        "expected_behavior": "start_anchor_multiline_line_terminator_success",
        "obligation": (
            "The current runtime line-terminator policy treats CR and LF as "
            "line terminators for matcher assertions"
        ),
    },
    {
        "requirement_id": "ecma262-22.2.2.4-0011",
        "family": "start_anchor_without_multiline_rejects_after_lf",
        "pattern": "^a",
        "flags": "",
        "input": "x\\na",
        "expected_search_result": "false",
        "expected_exec_result": "false",
        "expected_start_index": "",
        "expected_end_index": "",
        "expected_match_text": "",
        "expected_behavior": "start_anchor_condition_failure_without_multiline",
        "obligation": (
            "Without rer.[[Multiline]], a line terminator before e does not "
            "make ^ succeed"
        ),
    },
]


def validate_requirement_row(row: dict[str, str]) -> None:
    expected = {
        "clause_id": "22.2.2.4",
        "semantic_family": "assertions",
        "product_surface": "match_engine",
        "route_status": "needs_requirement_to_test_case_mapping",
    }
    validate_expected_fields(row, expected, context="start-anchor row")
    require_coverage_area(
        row,
        "regexp_exec_and_captures",
        context="start-anchor row",
    )


def classify_source_failure(row: dict[str, str]) -> str:
    pattern = row["patterns"]
    description = row["case_description"]
    parts = ["start_anchor"]
    if "$" in pattern:
        parts.append("end_anchor")
    if any(token in pattern for token in ["*", "+", "?", "{"]):
        parts.append("quantifier")
    if (
        "\\p" in pattern
        or "🐲" in pattern
        or "Unicode" in description
        or "UTF-16" in description
        or "non-ASCII" in description
    ):
        parts.append("unicode")
    return "+".join(parts)


def source_failure_rows(rows: list[dict[str, str]]) -> list[dict[str, str]]:
    return [row for row in rows if row["failure_family"] == SOURCE_FAILURE_FAMILY]


def plan_row(
    case: dict[str, str],
    requirement: dict[str, str],
    source_failure_count: int,
) -> dict[str, str]:
    validate_requirement_row(requirement)
    requirement_id = case["requirement_id"]
    exact_case_id = (
        f"match-engine-start-anchor-exact:{requirement_id}:{safe_id(case['family'])}"
    )
    if source_failure_count > 0:
        plan_reason = (
            "JSON Schema failure inventory currently exposes start-anchor as "
            "a matcher blocker; exact ECMA-262 assertion cases must go green "
            "before any corpus-driven implementation credit"
        )
    else:
        plan_reason = (
            "JSON Schema failure inventory no longer exposes start-anchor as "
            "a current blocker; the exact ECMA-262 assertion cases remain in "
            "the coverage system as regression evidence"
        )
    return {
        "plan_id": f"match-engine-start-anchor-exact-plan:{requirement_id}:{safe_id(case['family'])}",
        **copy_requirement_metadata(requirement, include_local_id=False),
        "mapping_family": "match_engine_assertions",
        "executable_layer": "match_engine",
        "exact_case_family": case["family"],
        "exact_case_id": exact_case_id,
        "pattern": case["pattern"],
        "flags": case["flags"],
        "input_text": case["input"],
        "expected_search_result": case["expected_search_result"],
        "expected_exec_result": case["expected_exec_result"],
        "expected_start_index": case["expected_start_index"],
        "expected_end_index": case["expected_end_index"],
        "expected_match_text": case["expected_match_text"],
        "expected_behavior": case["expected_behavior"],
        "source_failure_family": SOURCE_FAILURE_FAMILY,
        "source_failure_count": str(source_failure_count),
        "coverage_credit": "none_match_engine_start_anchor_exact_planned",
        "plan_state": "planned_not_executable",
        "target_test_artifact": TARGET_TEST_ARTIFACT,
        "exact_case_obligation": case["obligation"],
        "observability_status": "search_and_exec_observable",
        "observability_reason": (
            "public Ecma_regex.search observes boolean success and public "
            "Ecma_regex.exec observes start, end, and matched text for "
            "zero-width assertion behavior"
        ),
        "next_action": "materialize_match_engine_start_anchor_exact_case",
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
        {
            "failure_family",
            "schema_keyword",
            "schema_shape",
            "case_description",
            "patterns",
        },
    )

    requirement_by_id = rows_by_requirement_id(requirement_rows)
    source_rows = source_failure_rows(inventory_rows)

    rows = []
    for case in EXACT_CASES:
        requirement_id = case["requirement_id"]
        requirement = requirement_by_id.get(requirement_id)
        if requirement is None:
            raise SystemExit(f"missing requirement row for {requirement_id}")
        rows.append(plan_row(case, requirement, len(source_rows)))
    validate_unique_ids(rows)

    state_counts = Counter(row["plan_state"] for row in rows)
    credit_counts = Counter(row["coverage_credit"] for row in rows)
    behavior_counts = Counter(row["expected_behavior"] for row in rows)
    search_counts = Counter(row["expected_search_result"] for row in rows)
    exec_counts = Counter(row["expected_exec_result"] for row in rows)
    layer_counts = Counter(row["executable_layer"] for row in rows)
    mapping_counts = Counter(row["mapping_family"] for row in rows)
    target_counts = Counter(row["target_test_artifact"] for row in rows)
    observability_counts = Counter(row["observability_status"] for row in rows)
    source_keyword_counts = Counter(row["schema_keyword"] for row in source_rows)
    source_shape_counts = Counter(row["schema_shape"] for row in source_rows)
    source_subfamily_counts = Counter(classify_source_failure(row) for row in source_rows)

    coverage_credit_rows = sum(
        count for credit, count in credit_counts.items() if not credit.startswith("none")
    )
    planned_executable_rows = state_counts.get("planned_not_executable", 0)

    summary_lines = [
        "ecma262_snapshot\t2026\n",
        f"input_requirements\t{requirements}\n",
        f"input_json_schema_inventory\t{inventory}\n",
        f"input_requirement_rows\t{len(requirement_rows)}\n",
        f"input_json_schema_inventory_rows\t{len(inventory_rows)}\n",
        f"source_failure_family\t{SOURCE_FAILURE_FAMILY}\n",
        f"source_failure_rows\t{len(source_rows)}\n",
        f"match_engine_start_anchor_exact_plan_rows\t{len(rows)}\n",
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
    for name, count in sorted(layer_counts.items()):
        summary_lines.append(f"executable_layer_{name}\t{count}\n")
    for name, count in sorted(mapping_counts.items()):
        summary_lines.append(f"mapping_family_{name}\t{count}\n")
    for name, count in sorted(target_counts.items()):
        summary_lines.append(f"target_test_artifact_{name}\t{count}\n")
    for name, count in sorted(observability_counts.items()):
        summary_lines.append(f"observability_status_{name}\t{count}\n")
    for name, count in sorted(source_keyword_counts.items()):
        summary_lines.append(f"source_schema_keyword_{name}\t{count}\n")
    for name, count in sorted(source_shape_counts.items()):
        summary_lines.append(f"source_schema_shape_{name}\t{count}\n")
    for name, count in sorted(source_subfamily_counts.items()):
        summary_lines.append(f"source_subfamily_{name}\t{count}\n")

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
