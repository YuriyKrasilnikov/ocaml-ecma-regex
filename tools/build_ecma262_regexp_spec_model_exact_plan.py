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
    validate_unique_ids,
)


DETAIL_NAME = "ecma262-regexp-spec-model-exact-plan.tsv"
SUMMARY_NAME = "ecma262-regexp-spec-model-exact-plan.summary"
TARGET_TEST_ARTIFACT = "test/test_ecma262_spec_model_exact_plan.ml"

EXPECTED_SPEC_MODEL_ROWS = 4
LEXICAL_GOAL_SYMBOLS = (
    "InputElementDiv,InputElementTemplateTail,InputElementRegExp,"
    "InputElementRegExpOrTemplateTail,InputElementHashbangOrRegExp"
)

CASE_BY_ID = {
    "5.1.2-0001": {
        "spec_model_subfamily": "lexical_grammar_source_model",
        "spec_model_route": "source_character_goal_symbols",
        "exact_case_family": "lexical_grammar_source_character_goal_model",
        "model_scenario": "lexical_grammar_source_model",
        "source_text": "a",
        "expected_behavior": "lexical_grammar_source_character_goal_model_observed",
        "expected_model_field": "lexical_grammar_source_character_goal_model_observed",
    },
    "5.1.2-0002": {
        "spec_model_subfamily": "syntactic_token_stream_policy",
        "spec_model_route": "token_stream_boundary_policy",
        "exact_case_family": "syntactic_token_stream_boundary_model",
        "model_scenario": "syntactic_token_stream_policy",
        "source_text": "a",
        "expected_behavior": "syntactic_token_stream_boundary_policy_observed",
        "expected_model_field": "syntactic_token_stream_boundary_policy_observed",
    },
    "5.1.2-0003": {
        "spec_model_subfamily": "regexp_grammar_pattern_model",
        "spec_model_route": "source_character_pattern_goal",
        "exact_case_family": "regexp_grammar_pattern_source_model",
        "model_scenario": "regexp_grammar_pattern_model",
        "source_text": "a",
        "expected_behavior": "regexp_grammar_pattern_source_model_observed",
        "expected_model_field": "regexp_grammar_pattern_source_model_observed",
    },
    "5.1.2-0004": {
        "spec_model_subfamily": "grammar_notation_boundary_model",
        "spec_model_route": "lexical_regexp_shared_productions",
        "exact_case_family": "lexical_regexp_grammar_notation_boundary_model",
        "model_scenario": "grammar_notation_boundary_model",
        "source_text": "a",
        "expected_behavior": "lexical_regexp_grammar_notation_boundary_observed",
        "expected_model_field": "lexical_regexp_grammar_notation_boundary_observed",
    },
}


def requirement_key(row: dict[str, str]) -> str:
    return f"{row['clause_id']}-{row['requirement_id'].rsplit('-', 1)[1]}"


def selected_mapping_rows(rows: list[dict[str, str]]) -> list[dict[str, str]]:
    selected = [
        row
        for row in rows
        if row["clause_id"] == "5.1.2"
        and row["implementation_layer"] == "spec_model"
        and row["product_surface"] == "spec_model"
        and row["semantic_family"] == "grammar_model"
    ]
    selected.sort(key=lambda row: (row["clause_id"], row["requirement_id"]))
    if len(selected) != EXPECTED_SPEC_MODEL_ROWS:
        raise SystemExit(
            f"expected {EXPECTED_SPEC_MODEL_ROWS} spec-model rows, "
            f"selected {len(selected)}"
        )
    missing_cases = [
        row["requirement_id"] for row in selected if requirement_key(row) not in CASE_BY_ID
    ]
    if missing_cases:
        raise SystemExit(
            "missing spec-model exact case definitions for "
            + ", ".join(missing_cases)
        )
    return selected


def plan_row(row: dict[str, str]) -> dict[str, str]:
    requirement_id = row["requirement_id"]
    case = CASE_BY_ID[requirement_key(row)]
    source_text = case["source_text"]
    exact_case_id = (
        f"spec-model-exact:{requirement_id}:"
        f"{safe_id(case['expected_behavior'])}"
    )
    return {
        "plan_id": f"spec-model-exact-plan:{requirement_id}",
        **copy_requirement_metadata(row, include_local_id=True),
        "mapping_family": "spec_model_local_exact",
        "executable_layer": "spec_model",
        "spec_model_subfamily": case["spec_model_subfamily"],
        "spec_model_route": case["spec_model_route"],
        "exact_case_family": case["exact_case_family"],
        "exact_case_id": exact_case_id,
        "model_scenario": case["model_scenario"],
        "source_text": source_text,
        "expected_source_code_point_count": str(len(source_text)),
        "expected_utf16_code_unit_length": str(len(source_text)),
        "expected_lexical_goal_symbols": LEXICAL_GOAL_SYMBOLS,
        "expected_regexp_goal_symbol": "Pattern",
        "expected_regexp_clause": "22.2.1",
        "expected_behavior": case["expected_behavior"],
        "expected_model_field": case["expected_model_field"],
        "coverage_credit": "none_spec_model_exact_planned",
        "plan_state": "planned_not_executable",
        "target_test_artifact": TARGET_TEST_ARTIFACT,
        "exact_case_obligation": row["requirement_text"],
        "observability_status": "internal_spec_model_observable",
        "observability_reason": (
            "internal spec-model observer exposes the ECMA-262 lexical grammar, "
            "RegExp grammar, and grammar-notation boundary model without "
            "changing public API"
        ),
        "next_action": "materialize_spec_model_exact_case",
        "plan_reason": (
            "Clause 5.1.2 rows describe source and grammar model boundaries, "
            "so exact credit is valid only after an executable internal "
            "spec-model gate proves the requirement-specific model fact"
        ),
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--cache", default="cache")
    parser.add_argument(
        "--requirement-mapping",
        default="cache/ecma262-regexp-requirement-mapping.tsv",
    )
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    cache = Path(args.cache)
    requirement_mapping = Path(args.requirement_mapping)
    detail = cache / DETAIL_NAME
    summary = cache / SUMMARY_NAME

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
            "implementation_layer",
            "product_surface",
            "semantic_family",
        },
    )
    source_rows = selected_mapping_rows(mapping_rows)
    rows = [plan_row(row) for row in source_rows]
    validate_unique_ids(rows)

    state_counts = Counter(row["plan_state"] for row in rows)
    credit_counts = Counter(row["coverage_credit"] for row in rows)
    subfamily_counts = Counter(row["spec_model_subfamily"] for row in rows)
    route_counts = Counter(row["spec_model_route"] for row in rows)
    behavior_counts = Counter(row["expected_behavior"] for row in rows)
    field_counts = Counter(row["expected_model_field"] for row in rows)
    family_counts = Counter(row["exact_case_family"] for row in rows)
    scenario_counts = Counter(row["model_scenario"] for row in rows)
    observability_counts = Counter(row["observability_status"] for row in rows)
    target_counts = Counter(row["target_test_artifact"] for row in rows)

    planned_executable_rows = state_counts.get("planned_not_executable", 0)
    coverage_credit_rows = sum(
        count for credit, count in credit_counts.items() if not credit.startswith("none")
    )

    summary_lines = [
        "ecma262_snapshot\t2026\n",
        f"input_requirement_mapping\t{requirement_mapping}\n",
        f"input_requirement_mapping_rows\t{len(mapping_rows)}\n",
        f"source_requirement_rows\t{len(source_rows)}\n",
        f"spec_model_exact_plan_rows\t{len(rows)}\n",
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
        summary_lines.append(f"spec_model_subfamily_{name}\t{count}\n")
    for name, count in sorted(route_counts.items()):
        summary_lines.append(f"spec_model_route_{name}\t{count}\n")
    for name, count in sorted(family_counts.items()):
        summary_lines.append(f"exact_case_family_{name}\t{count}\n")
    for name, count in sorted(scenario_counts.items()):
        summary_lines.append(f"model_scenario_{name}\t{count}\n")
    for name, count in sorted(behavior_counts.items()):
        summary_lines.append(f"expected_behavior_{name}\t{count}\n")
    for name, count in sorted(field_counts.items()):
        summary_lines.append(f"expected_model_field_{name}\t{count}\n")
    for name, count in sorted(observability_counts.items()):
        summary_lines.append(f"observability_status_{name}\t{count}\n")
    for name, count in sorted(target_counts.items()):
        summary_lines.append(f"target_test_artifact_{name}\t{count}\n")

    if not args.dry_run:
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
            "spec_model_subfamily",
            "spec_model_route",
            "exact_case_family",
            "exact_case_id",
            "model_scenario",
            "source_text",
            "expected_source_code_point_count",
            "expected_utf16_code_unit_length",
            "expected_lexical_goal_symbols",
            "expected_regexp_goal_symbol",
            "expected_regexp_clause",
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

    print("".join(summary_lines), end="")


if __name__ == "__main__":
    main()
