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
    select_expected_source_rows,
    suffix_number,
    validate_expected_fields,
    validate_unique_ids,
)


DETAIL_NAME = "ecma262-regexp-match-engine-unicode-sets-string-exact-plan.tsv"
SUMMARY_NAME = "ecma262-regexp-match-engine-unicode-sets-string-exact-plan.summary"
TARGET_TEST_ARTIFACT = (
    "test/test_ecma262_match_engine_unicode_sets_string_exact_plan.ml"
)

OBSERVATIONS_BY_SUFFIX = {
    16: "unicode_sets_character_class_invert_false_assert",
    17: "unicode_sets_matcher_list_initialized",
    18: "unicode_sets_multi_char_elements_descending_iteration",
    19: "unicode_sets_last_code_point_charset",
    20: "unicode_sets_last_code_point_matcher",
    21: "unicode_sets_prefix_code_point_iteration",
    22: "unicode_sets_prefix_code_point_charset",
    23: "unicode_sets_prefix_code_point_matcher",
    24: "unicode_sets_match_sequence_built",
    25: "unicode_sets_multi_matcher_appended",
    26: "unicode_sets_singles_charset_built",
    27: "unicode_sets_singles_matcher_appended",
    28: "unicode_sets_empty_sequence_checked",
    29: "unicode_sets_empty_matcher_appended",
    30: "unicode_sets_last_matcher_selected",
    31: "unicode_sets_match_two_alternatives_fold",
    32: "unicode_sets_final_matcher_return",
}


def validate_source_row(row: dict[str, str]) -> None:
    requirement_id = row["requirement_id"]
    expected = {
        "mapping_family": "match_engine_atoms",
        "executable_layer": "match_engine",
        "atom_subfamily": "character_class_unicode_sets_string_elements",
        "atom_semantic_route": "unicode_sets_string_element_matcher_model",
        "expected_behavior": "requires_unicode_sets_string_element_model",
        "coverage_credit": "none_match_engine_atoms_exact_deferred",
        "plan_state": "deferred_requires_unicode_sets_string_element_model",
        "observability_status": "requires_unicode_sets_string_element_model",
    }
    validate_expected_fields(
        row,
        expected,
        context="UnicodeSets string exact source row",
    )
    number = suffix_number(requirement_id)
    if number not in OBSERVATIONS_BY_SUFFIX:
        raise SystemExit(
            f"UnicodeSets string exact source row {requirement_id} has "
            "unsupported suffix"
        )
    if not Path(row["source_file"]).is_file():
        raise SystemExit(
            f"UnicodeSets string exact source row {requirement_id} source is "
            f"missing: {row['source_file']}"
        )


def selected_source_rows(rows: list[dict[str, str]]) -> list[dict[str, str]]:
    expected_ids = {
        f"ecma262-22.2.2.7-{number:04d}" for number in OBSERVATIONS_BY_SUFFIX
    }
    return select_expected_source_rows(
        rows,
        include_row=lambda row: row["atom_subfamily"]
        == "character_class_unicode_sets_string_elements",
        expected_ids=expected_ids,
        validate_row=validate_source_row,
        duplicate_message=lambda requirement_id: (
            f"duplicate UnicodeSets string source row for {requirement_id}"
        ),
        missing_prefix="UnicodeSets string exact source rows missing from atom plan: ",
        extra_prefix=(
            "UnicodeSets string exact source rows outside expected CompileAtom range: "
        ),
    )


def plan_row(row: dict[str, str]) -> dict[str, str]:
    requirement_id = row["requirement_id"]
    observation = OBSERVATIONS_BY_SUFFIX[suffix_number(requirement_id)]
    exact_case_id = (
        f"match-engine-unicode-sets-string-exact:{requirement_id}:"
        f"{safe_id(observation)}"
    )
    return {
        "plan_id": f"match-engine-unicode-sets-string-exact-plan:{requirement_id}",
        "source_atom_plan_id": row["plan_id"],
        **copy_requirement_metadata(row, include_local_id=True),
        "mapping_family": "match_engine_atoms",
        "executable_layer": "match_engine",
        "unicode_sets_subfamily": "character_class_unicode_sets_string_elements",
        "unicode_sets_semantic_route": "unicode_sets_string_element_matcher_model",
        "exact_case_family": observation,
        "exact_case_id": exact_case_id,
        "pattern": r"[\q{ab|a|}]",
        "flags": "v",
        "input_text": "ab",
        "expected_exec_text": "ab",
        "expected_observation": observation,
        "expected_observed": "true",
        "expected_behavior": "unicode_sets_string_element_model_observable",
        "coverage_credit": "none_match_engine_unicode_sets_string_exact_planned",
        "plan_state": "planned_not_executable",
        "target_test_artifact": TARGET_TEST_ARTIFACT,
        "exact_case_obligation": row["requirement_text"],
        "observability_status": "unicode_sets_string_element_model_observable",
        "observability_reason": (
            "Ecma_regex_core exposes a test-only UnicodeSets string-element "
            "matcher-model observation without adding public Ecma_regex API surface"
        ),
        "next_action": "materialize_match_engine_unicode_sets_string_exact_case",
        "plan_reason": (
            "UnicodeSets string exact case upgrades previously deferred "
            "CompileAtom CharacterClass rows into executable internal "
            "matcher-model evidence; ledger credit is assigned only after the "
            "exactness audit consumes this plan"
        ),
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--cache", default="cache")
    parser.add_argument(
        "--atoms-plan",
        default="cache/ecma262-regexp-match-engine-atoms-exact-plan.tsv",
    )
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    cache = Path(args.cache)
    atoms_plan = Path(args.atoms_plan)
    detail = cache / DETAIL_NAME
    summary = cache / SUMMARY_NAME

    if not atoms_plan.is_file():
        raise SystemExit(
            f"missing match-engine atoms exact plan at {atoms_plan}; "
            "run tools/build_ecma262_regexp_match_engine_atoms_exact_plan.py first"
        )

    atoms_fields, atoms_rows = read_tsv(atoms_plan)
    require_columns(
        atoms_plan,
        atoms_fields,
        {
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
            "atom_subfamily",
            "atom_semantic_route",
            "expected_behavior",
            "coverage_credit",
            "plan_state",
            "observability_status",
        },
    )
    rows = [plan_row(row) for row in selected_source_rows(atoms_rows)]
    validate_unique_ids(rows)

    fieldnames = [
        "plan_id",
        "source_atom_plan_id",
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
        "unicode_sets_subfamily",
        "unicode_sets_semantic_route",
        "exact_case_family",
        "exact_case_id",
        "pattern",
        "flags",
        "input_text",
        "expected_exec_text",
        "expected_observation",
        "expected_observed",
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

    state_counts = Counter(row["plan_state"] for row in rows)
    observation_counts = Counter(row["expected_observation"] for row in rows)
    route_counts = Counter(row["unicode_sets_semantic_route"] for row in rows)
    summary_lines = [
        "ecma262_snapshot\t2026\n",
        f"input_atoms_plan\t{atoms_plan}\n",
        f"match_engine_unicode_sets_string_exact_plan_rows\t{len(rows)}\n",
        f"planned_executable_rows\t{state_counts.get('planned_not_executable', 0)}\n",
        "unicode_sets_route_unicode_sets_string_element_matcher_model\t"
        f"{route_counts.get('unicode_sets_string_element_matcher_model', 0)}\n",
        f"target_test_artifact\t{TARGET_TEST_ARTIFACT}\n",
        f"planned_detail_output\t{detail}\n",
        f"planned_summary_output\t{summary}\n",
        f"dry_run\t{bool_text(args.dry_run)}\n",
    ]
    for name, count in sorted(state_counts.items()):
        summary_lines.append(f"plan_state_{name}\t{count}\n")
    for name, count in sorted(observation_counts.items()):
        summary_lines.append(f"expected_observation_{name}\t{count}\n")

    if args.dry_run:
        print("".join(summary_lines), end="")
        return

    cache.mkdir(parents=True, exist_ok=True)
    with detail.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames, delimiter="\t")
        writer.writeheader()
        writer.writerows(rows)
    summary.write_text("".join(summary_lines), encoding="utf-8")
    print(summary.read_text(encoding="utf-8"), end="")


if __name__ == "__main__":
    main()
