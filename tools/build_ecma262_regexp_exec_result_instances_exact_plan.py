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


DETAIL_NAME = "ecma262-regexp-exec-result-instances-exact-plan.tsv"
SUMMARY_NAME = "ecma262-regexp-exec-result-instances-exact-plan.summary"
TARGET_TEST_ARTIFACT = "test/test_ecma262_exec_result_instances_exact_plan.ml"

EXPECTED_INSTANCE_ROWS = 3
EXPECTED_INTERNAL_SLOTS = (
    "[[OriginalSource]],[[OriginalFlags]],[[RegExpRecord]],[[RegExpMatcher]]"
)

BASE_CASE = {
    "pattern": "a",
    "flags": "g",
    "input_text": "ba",
    "expected_original_source": "a",
    "expected_original_flags": "g",
    "expected_internal_slots": EXPECTED_INTERNAL_SLOTS,
    "expected_last_index_initial_value": "0",
    "expected_last_index_writable": "true",
    "expected_last_index_enumerable": "false",
    "expected_last_index_configurable": "false",
}

CASE_BY_ID = {
    "22.2.8-0001": {
        **BASE_CASE,
        "result_subfamily": "regexp_instance_internal_slots",
        "result_semantic_route": "instance_slots_model",
        "exact_case_family": "regexp_instance_internal_slots_model",
        "expected_behavior": "regexp_instance_internal_slots_observed",
        "expected_model_field": "regexp_instance_internal_slots_observed",
    },
    "22.2.8-0002": {
        **BASE_CASE,
        "result_subfamily": "regexp_instance_property_inventory",
        "result_semantic_route": "last_index_property_model",
        "exact_case_family": "regexp_instance_property_model",
        "expected_behavior": "regexp_instance_last_index_property_observed",
        "expected_model_field": "regexp_instance_last_index_property_observed",
    },
    "22.2.8.1-0001": {
        **BASE_CASE,
        "result_subfamily": "last_index_property",
        "result_semantic_route": "last_index_property_attributes_model",
        "exact_case_family": "last_index_property_attributes_model",
        "expected_behavior": "last_index_integral_start_property_attributes_observed",
        "expected_model_field": "last_index_integral_start_property_attributes_observed",
    },
}


def requirement_key(row: dict[str, str]) -> str:
    return f"{row['clause_id']}-{row['requirement_id'].rsplit('-', 1)[1]}"


def selected_worklist_rows(rows: list[dict[str, str]]) -> list[dict[str, str]]:
    selected = select_worklist_rows(
        rows,
        include_row=lambda row: row["mapping_family"] == "exec_result_instances"
        and row["executable_layer"] == "exec_result"
        and row["ledger_state"] == "open_requirement_to_test_mapping_missing",
        sort_key=lambda row: (row["clause_id"], row["requirement_id"]),
        expected_count=EXPECTED_INSTANCE_ROWS,
        count_message=lambda selected_count: (
            f"expected {EXPECTED_INSTANCE_ROWS} exec-result instance rows, "
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
            "missing exec-result instance exact case definitions for "
            + ", ".join(missing_cases)
        )
    return selected


def plan_row(row: dict[str, str]) -> dict[str, str]:
    requirement_id = row["requirement_id"]
    case = CASE_BY_ID[requirement_key(row)]
    exact_case_id = (
        f"exec-result-instances-exact:{requirement_id}:"
        f"{safe_id(case['expected_behavior'])}"
    )
    return {
        "plan_id": f"exec-result-instances-exact-plan:{requirement_id}",
        **copy_requirement_metadata(row, include_local_id=True),
        "mapping_family": "exec_result_instances",
        "executable_layer": "exec_result",
        "result_subfamily": case["result_subfamily"],
        "result_semantic_route": case["result_semantic_route"],
        "exact_case_family": case["exact_case_family"],
        "exact_case_id": exact_case_id,
        "pattern": case["pattern"],
        "flags": case["flags"],
        "input_text": case["input_text"],
        "expected_original_source": case["expected_original_source"],
        "expected_original_flags": case["expected_original_flags"],
        "expected_internal_slots": case["expected_internal_slots"],
        "expected_last_index_initial_value": case["expected_last_index_initial_value"],
        "expected_last_index_writable": case["expected_last_index_writable"],
        "expected_last_index_enumerable": case["expected_last_index_enumerable"],
        "expected_last_index_configurable": case["expected_last_index_configurable"],
        "expected_behavior": case["expected_behavior"],
        "expected_model_field": case["expected_model_field"],
        "coverage_credit": "none_exec_result_instances_exact_planned",
        "plan_state": "planned_not_executable",
        "target_test_artifact": TARGET_TEST_ARTIFACT,
        "exact_case_obligation": row["requirement_text"],
        "observability_status": "internal_exec_result_instance_model_observable",
        "observability_reason": (
            "internal exec-result instance observer exposes OriginalSource, "
            "OriginalFlags, RegExpRecord, RegExpMatcher, and lastIndex property "
            "attributes from the compiled opaque value without changing public API"
        ),
        "next_action": "materialize_exec_result_instances_exact_case",
        "plan_reason": (
            "RegExp instance rows are exact only after the executable internal "
            "instance model gate proves the requirement-specific slots and "
            "lastIndex property policy"
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
        f"exec_result_instances_exact_plan_rows\t{len(rows)}\n",
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
        "expected_original_source",
        "expected_original_flags",
        "expected_internal_slots",
        "expected_last_index_initial_value",
        "expected_last_index_writable",
        "expected_last_index_enumerable",
        "expected_last_index_configurable",
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
