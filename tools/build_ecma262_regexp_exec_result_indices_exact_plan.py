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
    suffix_number,
    validate_unique_ids,
)


DETAIL_NAME = "ecma262-regexp-exec-result-indices-exact-plan.tsv"
SUMMARY_NAME = "ecma262-regexp-exec-result-indices-exact-plan.summary"
TARGET_TEST_ARTIFACT = "test/test_ecma262_exec_result_indices_exact_plan.ml"

BUILTIN_EXEC_INDICES_SUFFIXES = {41, 42, 43, 58, 81, 82, 83}
EXPECTED_INDICES_ROWS = 35

BASIC_INDEX_CASE = {
    "case_family": "full_match_index_pair_model",
    "pattern": "(a)(b)",
    "flags": "d",
    "input_text": "ab",
    "expected_indices_length": "3",
    "expected_group_names_length": "2",
    "expected_has_groups": "false",
    "expected_entry_index": "0",
    "expected_index_pair_defined": "true",
    "expected_index_pair_start": "0",
    "expected_index_pair_end": "2",
    "expected_group_name": "",
    "expected_duplicate_group_name": "false",
}

DEFINED_CAPTURE_INDEX_CASE = {
    **BASIC_INDEX_CASE,
    "case_family": "defined_capture_index_pair_model",
    "expected_entry_index": "1",
    "expected_index_pair_start": "0",
    "expected_index_pair_end": "1",
}

UNDEFINED_CAPTURE_INDEX_CASE = {
    **BASIC_INDEX_CASE,
    "case_family": "undefined_capture_index_pair_model",
    "pattern": "(a)|(b)",
    "input_text": "b",
    "expected_entry_index": "1",
    "expected_index_pair_defined": "false",
    "expected_index_pair_start": "",
    "expected_index_pair_end": "",
}

NAMED_CAPTURE_INDEX_CASE = {
    **DEFINED_CAPTURE_INDEX_CASE,
    "case_family": "named_capture_index_pair_model",
    "pattern": "(?<first>a)(b)",
    "expected_has_groups": "true",
    "expected_group_name": "first",
}

DUPLICATE_NAMED_CAPTURE_INDEX_CASE = {
    **BASIC_INDEX_CASE,
    "case_family": "duplicate_named_capture_index_pair_model",
    "pattern": "(?<dup>a)|(?<dup>b)",
    "input_text": "b",
    "expected_has_groups": "true",
    "expected_entry_index": "2",
    "expected_index_pair_start": "0",
    "expected_index_pair_end": "1",
    "expected_group_name": "dup",
    "expected_duplicate_group_name": "true",
}

CASE_BY_ID = {
    "22.2.7.2-0041": {
        **BASIC_INDEX_CASE,
        "expected_behavior": "exec_result_indices_list_initialized",
        "expected_model_field": "indices_list_initialized",
        "result_subfamily": "builtin_exec_indices",
        "result_semantic_route": "indices_result_model",
    },
    "22.2.7.2-0042": {
        **BASIC_INDEX_CASE,
        "expected_behavior": "exec_result_group_names_list_initialized",
        "expected_model_field": "group_names_list_initialized",
        "result_subfamily": "builtin_exec_indices",
        "result_semantic_route": "indices_result_model",
    },
    "22.2.7.2-0043": {
        **BASIC_INDEX_CASE,
        "expected_behavior": "exec_result_appends_full_match_to_indices",
        "expected_model_field": "full_match_appended_to_indices",
        "result_subfamily": "builtin_exec_indices",
        "result_semantic_route": "indices_result_model",
    },
    "22.2.7.2-0058": {
        **UNDEFINED_CAPTURE_INDEX_CASE,
        "expected_behavior": "exec_result_appends_undefined_capture_to_indices",
        "expected_model_field": "undefined_capture_appended_to_indices",
        "result_subfamily": "builtin_exec_indices",
        "result_semantic_route": "indices_result_model",
    },
    "22.2.7.2-0081": {
        **BASIC_INDEX_CASE,
        "expected_behavior": "exec_result_takes_has_indices_branch",
        "expected_model_field": "has_indices_branch_observed",
        "result_subfamily": "builtin_exec_indices",
        "result_semantic_route": "indices_result_model",
    },
    "22.2.7.2-0082": {
        **BASIC_INDEX_CASE,
        "expected_behavior": "exec_result_builds_indices_array",
        "expected_model_field": "indices_array_built",
        "result_subfamily": "builtin_exec_indices",
        "result_semantic_route": "indices_result_model",
    },
    "22.2.7.2-0083": {
        **BASIC_INDEX_CASE,
        "expected_behavior": "exec_result_writes_indices_property",
        "expected_model_field": "result_indices_property_observed",
        "result_subfamily": "builtin_exec_indices",
        "result_semantic_route": "indices_result_model",
    },
    "22.2.7.7-0001": {
        **BASIC_INDEX_CASE,
        "expected_behavior": "get_match_index_pair_operation_observable",
        "expected_model_field": "get_match_index_pair_observed",
        "result_subfamily": "get_match_index_pair",
        "result_semantic_route": "indices_index_pair_model",
    },
    "22.2.7.7-0002": {
        **BASIC_INDEX_CASE,
        "expected_behavior": "get_match_index_pair_range_assertion",
        "expected_model_field": "index_pair_range_valid",
        "result_subfamily": "get_match_index_pair",
        "result_semantic_route": "indices_index_pair_model",
    },
    "22.2.7.7-0003": {
        **BASIC_INDEX_CASE,
        "expected_behavior": "get_match_index_pair_returns_start_end_pair",
        "expected_model_field": "index_pair_start_end_observed",
        "result_subfamily": "get_match_index_pair",
        "result_semantic_route": "indices_index_pair_model",
    },
    "22.2.7.8-0001": {
        **BASIC_INDEX_CASE,
        "expected_behavior": "make_match_indices_array_operation_observable",
        "expected_model_field": "make_match_indices_array_observed",
        "result_subfamily": "make_match_indices_index_pair_array",
        "result_semantic_route": "indices_array_model",
    },
    "22.2.7.8-0002": {
        **BASIC_INDEX_CASE,
        "expected_behavior": "make_match_indices_reads_indices_length",
        "expected_model_field": "indices_array_length_observed",
        "result_subfamily": "make_match_indices_index_pair_array",
        "result_semantic_route": "indices_array_model",
    },
    "22.2.7.8-0003": {
        **BASIC_INDEX_CASE,
        "expected_behavior": "make_match_indices_length_within_array_limit",
        "expected_model_field": "indices_length_within_array_limit",
        "result_subfamily": "make_match_indices_index_pair_array",
        "result_semantic_route": "indices_array_model",
    },
    "22.2.7.8-0004": {
        **BASIC_INDEX_CASE,
        "expected_behavior": "make_match_indices_group_names_length_matches",
        "expected_model_field": "group_names_length_matches",
        "result_subfamily": "make_match_indices_index_pair_array",
        "result_semantic_route": "indices_array_model",
    },
    "22.2.7.8-0005": {
        **BASIC_INDEX_CASE,
        "expected_behavior": "make_match_indices_group_names_aligned",
        "expected_model_field": "group_names_aligned_with_captures",
        "result_subfamily": "make_match_indices_index_pair_array",
        "result_semantic_route": "indices_array_model",
    },
    "22.2.7.8-0006": {
        **BASIC_INDEX_CASE,
        "expected_behavior": "make_match_indices_creates_array",
        "expected_model_field": "indices_array_created",
        "result_subfamily": "make_match_indices_index_pair_array",
        "result_semantic_route": "indices_array_model",
    },
    "22.2.7.8-0007": {
        **NAMED_CAPTURE_INDEX_CASE,
        "expected_behavior": "make_match_indices_takes_has_groups_branch",
        "expected_model_field": "has_groups_branch_observed",
        "result_subfamily": "make_match_indices_index_pair_array",
        "result_semantic_route": "indices_array_model",
    },
    "22.2.7.8-0008": {
        **NAMED_CAPTURE_INDEX_CASE,
        "expected_behavior": "make_match_indices_creates_groups_object",
        "expected_model_field": "indices_groups_object_created",
        "result_subfamily": "make_match_indices_index_pair_array",
        "result_semantic_route": "indices_array_model",
    },
    "22.2.7.8-0009": {
        **BASIC_INDEX_CASE,
        "expected_behavior": "make_match_indices_takes_no_groups_branch",
        "expected_model_field": "no_groups_branch_observed",
        "result_subfamily": "make_match_indices_index_pair_array",
        "result_semantic_route": "indices_array_model",
    },
    "22.2.7.8-0010": {
        **BASIC_INDEX_CASE,
        "expected_behavior": "make_match_indices_groups_undefined_without_groups",
        "expected_model_field": "indices_groups_undefined_observed",
        "result_subfamily": "make_match_indices_index_pair_array",
        "result_semantic_route": "indices_array_model",
    },
    "22.2.7.8-0011": {
        **NAMED_CAPTURE_INDEX_CASE,
        "expected_behavior": "make_match_indices_writes_groups_property",
        "expected_model_field": "indices_groups_property_observed",
        "result_subfamily": "make_match_indices_index_pair_array",
        "result_semantic_route": "indices_array_model",
    },
    "22.2.7.8-0012": {
        **DEFINED_CAPTURE_INDEX_CASE,
        "expected_behavior": "make_match_indices_iterates_entries",
        "expected_model_field": "indices_iteration_observed",
        "result_subfamily": "make_match_indices_index_pair_array",
        "result_semantic_route": "indices_array_model",
    },
    "22.2.7.8-0013": {
        **DEFINED_CAPTURE_INDEX_CASE,
        "expected_behavior": "make_match_indices_reads_index_entry",
        "expected_model_field": "indices_entry_read",
        "result_subfamily": "make_match_indices_index_pair_array",
        "result_semantic_route": "indices_array_model",
    },
    "22.2.7.8-0014": {
        **DEFINED_CAPTURE_INDEX_CASE,
        "expected_behavior": "make_match_indices_takes_defined_entry_branch",
        "expected_model_field": "defined_index_entry_observed",
        "result_subfamily": "make_match_indices_index_pair_array",
        "result_semantic_route": "indices_array_model",
    },
    "22.2.7.8-0015": {
        **DEFINED_CAPTURE_INDEX_CASE,
        "expected_behavior": "make_match_indices_calls_get_match_index_pair",
        "expected_model_field": "get_match_index_pair_called",
        "result_subfamily": "make_match_indices_index_pair_array",
        "result_semantic_route": "indices_array_model",
    },
    "22.2.7.8-0016": {
        **UNDEFINED_CAPTURE_INDEX_CASE,
        "expected_behavior": "make_match_indices_takes_undefined_entry_branch",
        "expected_model_field": "undefined_index_entry_observed",
        "result_subfamily": "make_match_indices_index_pair_array",
        "result_semantic_route": "indices_array_model",
    },
    "22.2.7.8-0017": {
        **UNDEFINED_CAPTURE_INDEX_CASE,
        "expected_behavior": "make_match_indices_returns_undefined_pair",
        "expected_model_field": "undefined_index_pair_observed",
        "result_subfamily": "make_match_indices_index_pair_array",
        "result_semantic_route": "indices_array_model",
    },
    "22.2.7.8-0018": {
        **DEFINED_CAPTURE_INDEX_CASE,
        "expected_behavior": "make_match_indices_writes_numeric_property",
        "expected_model_field": "indices_numeric_property_observed",
        "result_subfamily": "make_match_indices_index_pair_array",
        "result_semantic_route": "indices_array_model",
    },
    "22.2.7.8-0019": {
        **DEFINED_CAPTURE_INDEX_CASE,
        "expected_behavior": "make_match_indices_takes_capture_entry_branch",
        "expected_model_field": "capture_index_entry_observed",
        "result_subfamily": "make_match_indices_index_pair_array",
        "result_semantic_route": "indices_array_model",
    },
    "22.2.7.8-0020": {
        **NAMED_CAPTURE_INDEX_CASE,
        "expected_behavior": "make_match_indices_reads_group_name",
        "expected_model_field": "group_name_read",
        "result_subfamily": "make_match_indices_index_pair_array",
        "result_semantic_route": "indices_array_model",
    },
    "22.2.7.8-0021": {
        **NAMED_CAPTURE_INDEX_CASE,
        "expected_behavior": "make_match_indices_takes_named_group_branch",
        "expected_model_field": "defined_group_name_observed",
        "result_subfamily": "make_match_indices_index_pair_array",
        "result_semantic_route": "indices_array_model",
    },
    "22.2.7.8-0022": {
        **NAMED_CAPTURE_INDEX_CASE,
        "expected_behavior": "make_match_indices_asserts_groups_object_for_name",
        "expected_model_field": "named_groups_object_asserted",
        "result_subfamily": "make_match_indices_index_pair_array",
        "result_semantic_route": "indices_array_model",
    },
    "22.2.7.8-0023": {
        **DUPLICATE_NAMED_CAPTURE_INDEX_CASE,
        "expected_behavior": "make_match_indices_allows_duplicate_group_property_write",
        "expected_model_field": "duplicate_group_name_observed",
        "result_subfamily": "make_match_indices_index_pair_array",
        "result_semantic_route": "indices_array_model",
    },
    "22.2.7.8-0024": {
        **NAMED_CAPTURE_INDEX_CASE,
        "expected_behavior": "make_match_indices_writes_named_group_property",
        "expected_model_field": "named_group_property_observed",
        "result_subfamily": "make_match_indices_index_pair_array",
        "result_semantic_route": "indices_array_model",
    },
    "22.2.7.8-0025": {
        **BASIC_INDEX_CASE,
        "expected_behavior": "make_match_indices_returns_array",
        "expected_model_field": "indices_array_returned",
        "result_subfamily": "make_match_indices_index_pair_array",
        "result_semantic_route": "indices_array_model",
    },
}


def requirement_key(row: dict[str, str]) -> str:
    return f"{row['clause_id']}-{row['requirement_id'].rsplit('-', 1)[1]}"


def selected_worklist_rows(rows: list[dict[str, str]]) -> list[dict[str, str]]:
    selected = select_worklist_rows(
        rows,
        include_row=lambda row: row["ledger_state"]
        == "open_requirement_to_test_mapping_missing"
        and row["executable_layer"] == "exec_result"
        and (
            row["mapping_family"] == "exec_result_indices"
            or (
                row["mapping_family"] == "exec_result_matching"
                and row["clause_id"] == "22.2.7.2"
                and suffix_number(row["requirement_id"])
                in BUILTIN_EXEC_INDICES_SUFFIXES
            )
        ),
        sort_key=lambda row: (row["clause_id"], suffix_number(row["requirement_id"])),
        expected_count=EXPECTED_INDICES_ROWS,
        count_message=lambda selected_count: (
            f"expected {EXPECTED_INDICES_ROWS} exec-result indices rows, "
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
            "missing exec-result indices exact case definitions for "
            + ", ".join(missing_cases)
        )
    return selected


def plan_row(row: dict[str, str]) -> dict[str, str]:
    requirement_id = row["requirement_id"]
    case = CASE_BY_ID[requirement_key(row)]
    exact_case_id = (
        f"exec-result-indices-exact:{requirement_id}:"
        f"{safe_id(case['expected_behavior'])}"
    )
    return {
        "plan_id": f"exec-result-indices-exact-plan:{requirement_id}",
        **copy_requirement_metadata(row, include_local_id=True),
        "mapping_family": row["mapping_family"],
        "executable_layer": "exec_result",
        "result_subfamily": case["result_subfamily"],
        "result_semantic_route": case["result_semantic_route"],
        "exact_case_family": case["case_family"],
        "exact_case_id": exact_case_id,
        "pattern": case["pattern"],
        "flags": case["flags"],
        "input_text": case["input_text"],
        "expected_exec_result": "true",
        "expected_indices_length": case["expected_indices_length"],
        "expected_group_names_length": case["expected_group_names_length"],
        "expected_has_groups": case["expected_has_groups"],
        "expected_entry_index": case["expected_entry_index"],
        "expected_index_pair_defined": case["expected_index_pair_defined"],
        "expected_index_pair_start": case["expected_index_pair_start"],
        "expected_index_pair_end": case["expected_index_pair_end"],
        "expected_group_name": case["expected_group_name"],
        "expected_duplicate_group_name": case["expected_duplicate_group_name"],
        "expected_behavior": case["expected_behavior"],
        "expected_model_field": case["expected_model_field"],
        "coverage_credit": "none_exec_result_indices_exact_planned",
        "plan_state": "planned_not_executable",
        "target_test_artifact": TARGET_TEST_ARTIFACT,
        "exact_case_obligation": row["requirement_text"],
        "observability_status": "internal_exec_result_indices_model_observable",
        "observability_reason": (
            "internal exec-result indices observer exposes the hasIndices "
            "branch, indices/groupNames lists, index pairs, undefined captures, "
            "groups object routing, named-group entries, duplicate-name writes, "
            "and result indices property construction without changing public API"
        ),
        "next_action": "materialize_exec_result_indices_exact_case",
        "plan_reason": (
            "RegExpBuiltinExec and MakeMatchIndicesIndexPairArray indices rows "
            "are classified as exact only after the executable internal indices "
            "model gate proves the requirement-specific result construction behavior"
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
    behavior_counts = Counter(row["expected_behavior"] for row in rows)
    field_counts = Counter(row["expected_model_field"] for row in rows)
    family_counts = Counter(row["exact_case_family"] for row in rows)
    subfamily_counts = Counter(row["result_subfamily"] for row in rows)
    route_counts = Counter(row["result_semantic_route"] for row in rows)
    mapping_counts = Counter(row["mapping_family"] for row in rows)
    has_groups_counts = Counter(row["expected_has_groups"] for row in rows)
    pair_defined_counts = Counter(row["expected_index_pair_defined"] for row in rows)
    duplicate_counts = Counter(row["expected_duplicate_group_name"] for row in rows)
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
        f"exec_result_indices_exact_plan_rows\t{len(rows)}\n",
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
    for name, count in sorted(mapping_counts.items()):
        summary_lines.append(f"mapping_family_{name}\t{count}\n")
    for name, count in sorted(subfamily_counts.items()):
        summary_lines.append(f"result_subfamily_{name}\t{count}\n")
    for name, count in sorted(route_counts.items()):
        summary_lines.append(f"result_semantic_route_{name}\t{count}\n")
    for name, count in sorted(behavior_counts.items()):
        summary_lines.append(f"expected_behavior_{name}\t{count}\n")
    for name, count in sorted(field_counts.items()):
        summary_lines.append(f"expected_model_field_{name}\t{count}\n")
    for name, count in sorted(family_counts.items()):
        summary_lines.append(f"exact_case_family_{name}\t{count}\n")
    for name, count in sorted(has_groups_counts.items()):
        summary_lines.append(f"expected_has_groups_{name}\t{count}\n")
    for name, count in sorted(pair_defined_counts.items()):
        summary_lines.append(f"expected_index_pair_defined_{name}\t{count}\n")
    for name, count in sorted(duplicate_counts.items()):
        summary_lines.append(f"expected_duplicate_group_name_{name}\t{count}\n")
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
        "expected_indices_length",
        "expected_group_names_length",
        "expected_has_groups",
        "expected_entry_index",
        "expected_index_pair_defined",
        "expected_index_pair_start",
        "expected_index_pair_end",
        "expected_group_name",
        "expected_duplicate_group_name",
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
