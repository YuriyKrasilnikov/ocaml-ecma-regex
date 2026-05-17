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
    safe_id,
    select_worklist_rows,
    validate_unique_ids,
)


DETAIL_NAME = "ecma262-regexp-exec-result-exec-exact-plan.tsv"
SUMMARY_NAME = "ecma262-regexp-exec-result-exec-exact-plan.summary"
TARGET_TEST_ARTIFACT = "test/test_ecma262_exec_result_exec_exact_plan.ml"

EXPECTED_EXEC_ROWS = 21

SUCCESS_CASE = {
    "pattern": "b",
    "flags": "",
    "input_text": "abc",
    "expected_exec_result": "true",
    "expected_start_index": "1",
    "expected_end_index": "2",
    "expected_match_text": "b",
    "expected_test_result": "not_applicable",
}

NO_MATCH_TEST_CASE = {
    "pattern": "z",
    "flags": "",
    "input_text": "abc",
    "expected_exec_result": "false",
    "expected_start_index": "",
    "expected_end_index": "",
    "expected_match_text": "",
    "expected_test_result": "false",
}

SUCCESS_TEST_CASE = {
    **SUCCESS_CASE,
    "expected_test_result": "true",
}

CASE_BY_ID = {
    "22.2.6.2-0001": {
        **SUCCESS_CASE,
        "result_subfamily": "regexp_prototype_exec",
        "result_semantic_route": "exec_method_model",
        "exact_case_family": "exec_success_result_model",
        "expected_behavior": "regexp_prototype_exec_result_shape_observable",
        "expected_model_field": "regexp_prototype_exec_result_shape_observed",
    },
    "22.2.6.2-0002": {
        **SUCCESS_CASE,
        "result_subfamily": "regexp_prototype_exec",
        "result_semantic_route": "exec_method_model",
        "exact_case_family": "exec_operation_model",
        "expected_behavior": "regexp_prototype_exec_operation_observable",
        "expected_model_field": "regexp_prototype_exec_operation_observed",
    },
    "22.2.6.2-0003": {
        **SUCCESS_CASE,
        "result_subfamily": "regexp_prototype_exec",
        "result_semantic_route": "exec_method_model",
        "exact_case_family": "exec_receiver_model",
        "expected_behavior": "regexp_prototype_exec_this_value_observable",
        "expected_model_field": "regexp_prototype_exec_this_value_observed",
    },
    "22.2.6.2-0004": {
        **SUCCESS_CASE,
        "result_subfamily": "regexp_prototype_exec",
        "result_semantic_route": "exec_method_model",
        "exact_case_family": "exec_internal_slot_model",
        "expected_behavior": "regexp_prototype_exec_requires_matcher_slot",
        "expected_model_field": "regexp_prototype_exec_internal_slot_observed",
    },
    "22.2.6.2-0005": {
        **SUCCESS_CASE,
        "result_subfamily": "regexp_prototype_exec",
        "result_semantic_route": "exec_method_model",
        "exact_case_family": "exec_string_argument_model",
        "expected_behavior": "regexp_prototype_exec_string_argument_observable",
        "expected_model_field": "regexp_prototype_exec_string_input_observed",
    },
    "22.2.6.2-0006": {
        **SUCCESS_CASE,
        "result_subfamily": "regexp_prototype_exec",
        "result_semantic_route": "exec_method_model",
        "exact_case_family": "exec_builtin_delegation_model",
        "expected_behavior": "regexp_prototype_exec_delegates_to_builtin_exec",
        "expected_model_field": "regexp_prototype_exec_delegates_to_builtin_exec",
    },
    "22.2.6.16-0001": {
        **SUCCESS_TEST_CASE,
        "result_subfamily": "regexp_prototype_test",
        "result_semantic_route": "test_method_model",
        "exact_case_family": "test_operation_model",
        "expected_behavior": "regexp_prototype_test_operation_observable",
        "expected_model_field": "regexp_prototype_test_operation_observed",
    },
    "22.2.6.16-0002": {
        **SUCCESS_TEST_CASE,
        "result_subfamily": "regexp_prototype_test",
        "result_semantic_route": "test_method_model",
        "exact_case_family": "test_receiver_model",
        "expected_behavior": "regexp_prototype_test_this_value_observable",
        "expected_model_field": "regexp_prototype_test_this_value_observed",
    },
    "22.2.6.16-0003": {
        **SUCCESS_TEST_CASE,
        "result_subfamily": "regexp_prototype_test",
        "result_semantic_route": "test_method_model",
        "exact_case_family": "test_typed_receiver_model",
        "expected_behavior": "regexp_prototype_test_receiver_type_enforced",
        "expected_model_field": "regexp_prototype_test_typed_receiver_enforced",
    },
    "22.2.6.16-0004": {
        **SUCCESS_TEST_CASE,
        "result_subfamily": "regexp_prototype_test",
        "result_semantic_route": "test_method_model",
        "exact_case_family": "test_string_argument_model",
        "expected_behavior": "regexp_prototype_test_string_argument_observable",
        "expected_model_field": "regexp_prototype_test_string_input_observed",
    },
    "22.2.6.16-0005": {
        **NO_MATCH_TEST_CASE,
        "result_subfamily": "regexp_prototype_test",
        "result_semantic_route": "test_method_model",
        "exact_case_family": "test_calls_regexp_exec_model",
        "expected_behavior": "regexp_prototype_test_calls_regexp_exec",
        "expected_model_field": "regexp_prototype_test_calls_regexp_exec",
    },
    "22.2.6.16-0006": {
        **NO_MATCH_TEST_CASE,
        "result_subfamily": "regexp_prototype_test",
        "result_semantic_route": "test_method_model",
        "exact_case_family": "test_false_result_model",
        "expected_behavior": "regexp_prototype_test_returns_false_for_null",
        "expected_model_field": "regexp_prototype_test_false_result_observed",
    },
    "22.2.6.16-0007": {
        **SUCCESS_TEST_CASE,
        "result_subfamily": "regexp_prototype_test",
        "result_semantic_route": "test_method_model",
        "exact_case_family": "test_true_result_model",
        "expected_behavior": "regexp_prototype_test_returns_true_for_match",
        "expected_model_field": "regexp_prototype_test_true_result_observed",
    },
    "22.2.7.5-0001": {
        **SUCCESS_CASE,
        "result_subfamily": "match_record",
        "result_semantic_route": "match_record_model",
        "exact_case_family": "match_record_span_model",
        "expected_behavior": "match_record_encapsulates_start_end_indices",
        "expected_model_field": "match_record_observed",
    },
    "22.2.7.5-0002": {
        **SUCCESS_CASE,
        "result_subfamily": "match_record",
        "result_semantic_route": "match_record_model",
        "exact_case_family": "match_record_fields_model",
        "expected_behavior": "match_record_fields_list_observable",
        "expected_model_field": "match_record_fields_observed",
    },
    "22.2.7.5-0003": {
        **SUCCESS_CASE,
        "result_subfamily": "match_record",
        "result_semantic_route": "match_record_model",
        "exact_case_family": "match_record_field_table_model",
        "expected_behavior": "match_record_field_table_observable",
        "expected_model_field": "match_record_field_table_observed",
    },
    "22.2.7.5-0004": {
        **SUCCESS_CASE,
        "result_subfamily": "match_record",
        "result_semantic_route": "match_record_model",
        "exact_case_family": "match_record_start_index_model",
        "expected_behavior": "match_record_start_index_non_negative",
        "expected_model_field": "match_record_start_index_observed",
    },
    "22.2.7.5-0005": {
        **SUCCESS_CASE,
        "result_subfamily": "match_record",
        "result_semantic_route": "match_record_model",
        "exact_case_family": "match_record_end_index_model",
        "expected_behavior": "match_record_end_index_after_start",
        "expected_model_field": "match_record_end_index_observed",
    },
    "22.2.7.6-0001": {
        **SUCCESS_CASE,
        "result_subfamily": "get_match_string",
        "result_semantic_route": "get_match_string_model",
        "exact_case_family": "get_match_string_operation_model",
        "expected_behavior": "get_match_string_operation_observable",
        "expected_model_field": "get_match_string_operation_observed",
    },
    "22.2.7.6-0002": {
        **SUCCESS_CASE,
        "result_subfamily": "get_match_string",
        "result_semantic_route": "get_match_string_model",
        "exact_case_family": "get_match_string_range_model",
        "expected_behavior": "get_match_string_range_assertion",
        "expected_model_field": "get_match_string_range_assertion_observed",
    },
    "22.2.7.6-0003": {
        **SUCCESS_CASE,
        "result_subfamily": "get_match_string",
        "result_semantic_route": "get_match_string_model",
        "exact_case_family": "get_match_string_substring_model",
        "expected_behavior": "get_match_string_returns_substring",
        "expected_model_field": "get_match_string_result_observed",
    },
}


def requirement_key(row: dict[str, str]) -> str:
    return f"{row['clause_id']}-{row['requirement_id'].rsplit('-', 1)[1]}"


def selected_worklist_rows(rows: list[dict[str, str]]) -> list[dict[str, str]]:
    selected = select_worklist_rows(
        rows,
        include_row=lambda row: row["mapping_family"] == "exec_result_exec"
        and row["executable_layer"] == "exec_result"
        and row["ledger_state"] == "open_requirement_to_test_mapping_missing",
        sort_key=lambda row: (row["clause_id"], row["requirement_id"]),
        expected_count=EXPECTED_EXEC_ROWS,
        count_message=lambda selected_count: (
            f"expected {EXPECTED_EXEC_ROWS} exec-result exec rows, "
            f"selected {selected_count}"
        ),
    )
    missing_cases = [
        row["requirement_id"]
        for row in selected
        if requirement_key(row) not in CASE_BY_ID
    ]
    if missing_cases:
        raise SystemExit(
            "missing exec-result exec exact case definitions for "
            + ", ".join(missing_cases)
        )
    return selected


def plan_row(row: dict[str, str]) -> dict[str, str]:
    requirement_id = row["requirement_id"]
    case = CASE_BY_ID[requirement_key(row)]
    exact_case_id = (
        f"exec-result-exec-exact:{requirement_id}:"
        f"{safe_id(case['expected_behavior'])}"
    )
    return {
        "plan_id": f"exec-result-exec-exact-plan:{requirement_id}",
        **copy_requirement_metadata(row, include_local_id=True),
        "mapping_family": "exec_result_exec",
        "executable_layer": "exec_result",
        "result_subfamily": case["result_subfamily"],
        "result_semantic_route": case["result_semantic_route"],
        "exact_case_family": case["exact_case_family"],
        "exact_case_id": exact_case_id,
        "pattern": case["pattern"],
        "flags": case["flags"],
        "input_text": case["input_text"],
        "expected_exec_result": case["expected_exec_result"],
        "expected_start_index": case["expected_start_index"],
        "expected_end_index": case["expected_end_index"],
        "expected_match_text": case["expected_match_text"],
        "expected_test_result": case["expected_test_result"],
        "expected_behavior": case["expected_behavior"],
        "expected_model_field": case["expected_model_field"],
        "coverage_credit": "none_exec_result_exec_exact_planned",
        "plan_state": "planned_not_executable",
        "target_test_artifact": TARGET_TEST_ARTIFACT,
        "exact_case_obligation": row["requirement_text"],
        "observability_status": "internal_exec_result_exec_model_observable",
        "observability_reason": (
            "internal exec-result exec observer exposes the typed RegExp receiver, "
            "string input boundary, RegExpBuiltinExec delegation, test true/false "
            "result routing, Match Record start/end fields, and GetMatchString "
            "substring behavior without changing public API"
        ),
        "next_action": "materialize_exec_result_exec_exact_case",
        "plan_reason": (
            "RegExp.prototype.exec/test, Match Record, and GetMatchString rows "
            "are classified as exact only after the executable internal "
            "exec-result exec model gate proves the requirement-specific behavior"
        ),
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--cache", default="cache")
    parser.add_argument(
        "--worklist",
        default="cache/ecma262-regexp-requirement-test-worklist.tsv",
    )
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    cache = Path(args.cache)
    worklist = Path(args.worklist)
    detail = cache / DETAIL_NAME
    summary = cache / SUMMARY_NAME

    if not worklist.is_file():
        raise SystemExit(
            f"missing ECMA-262 requirement-test worklist at {worklist}; "
            "run tools/map_ecma262_requirements_to_tests.py first"
        )

    worklist_fields, worklist_rows = read_tsv(worklist)
    require_columns(
        worklist,
        worklist_fields,
        {
            "requirement_id",
            "clause_id",
            "clause_title",
            "source_file",
            "section_anchor",
            "requirement_kind",
            "requirement_local_id",
            "requirement_text",
            "mapping_family",
            "executable_layer",
            "ledger_state",
        },
    )
    source_rows = selected_worklist_rows(worklist_rows)
    rows = [plan_row(row) for row in source_rows]
    validate_unique_ids(rows)

    state_counts = Counter(row["plan_state"] for row in rows)
    credit_counts = Counter(row["coverage_credit"] for row in rows)
    subfamily_counts = Counter(row["result_subfamily"] for row in rows)
    route_counts = Counter(row["result_semantic_route"] for row in rows)
    behavior_counts = Counter(row["expected_behavior"] for row in rows)
    field_counts = Counter(row["expected_model_field"] for row in rows)
    exec_counts = Counter(row["expected_exec_result"] for row in rows)
    test_counts = Counter(row["expected_test_result"] for row in rows)
    family_counts = Counter(row["exact_case_family"] for row in rows)
    observability_counts = Counter(row["observability_status"] for row in rows)
    target_counts = Counter(row["target_test_artifact"] for row in rows)

    planned_executable_rows = state_counts.get("planned_not_executable", 0)
    coverage_credit_rows = sum(
        count for credit, count in credit_counts.items() if not credit.startswith("none")
    )

    summary_lines = [
        "ecma262_snapshot\t2026\n",
        f"input_worklist\t{worklist}\n",
        f"input_worklist_rows\t{len(worklist_rows)}\n",
        f"source_requirement_rows\t{len(source_rows)}\n",
        f"exec_result_exec_exact_plan_rows\t{len(rows)}\n",
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
    for name, count in sorted(subfamily_counts.items()):
        summary_lines.append(f"result_subfamily_{name}\t{count}\n")
    for name, count in sorted(route_counts.items()):
        summary_lines.append(f"result_semantic_route_{name}\t{count}\n")
    for name, count in sorted(behavior_counts.items()):
        summary_lines.append(f"expected_behavior_{name}\t{count}\n")
    for name, count in sorted(field_counts.items()):
        summary_lines.append(f"expected_model_field_{name}\t{count}\n")
    for name, count in sorted(exec_counts.items()):
        summary_lines.append(f"expected_exec_result_{name}\t{count}\n")
    for name, count in sorted(test_counts.items()):
        summary_lines.append(f"expected_test_result_{name}\t{count}\n")
    for name, count in sorted(family_counts.items()):
        summary_lines.append(f"exact_case_family_{name}\t{count}\n")
    for name, count in sorted(observability_counts.items()):
        summary_lines.append(f"observability_status_{name}\t{count}\n")
    for name, count in sorted(target_counts.items()):
        if name:
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
        "requirement_local_id",
        "requirement_text",
        "mapping_family",
        "executable_layer",
        "result_subfamily",
        "result_semantic_route",
        "exact_case_family",
        "exact_case_id",
        "pattern",
        "flags",
        "input_text",
        "expected_exec_result",
        "expected_start_index",
        "expected_end_index",
        "expected_match_text",
        "expected_test_result",
        "expected_behavior",
        "expected_model_field",
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
        writer = csv.DictWriter(f, delimiter="\t", fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)
    with summary.open("w", encoding="utf-8") as f:
        f.write("".join(summary_lines))
    print(summary.read_text(encoding="utf-8"), end="")


if __name__ == "__main__":
    main()
