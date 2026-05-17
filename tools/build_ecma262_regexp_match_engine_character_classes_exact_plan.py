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


DETAIL_NAME = "ecma262-regexp-match-engine-character-classes-exact-plan.tsv"
SUMMARY_NAME = "ecma262-regexp-match-engine-character-classes-exact-plan.summary"
TARGET_TEST_ARTIFACT = (
    "test/test_ecma262_match_engine_character_classes_exact_plan.ml"
)

RANGE_OBSERVATIONS_BY_SUFFIX = {
    1: "character_range_operation",
    2: "character_range_singleton_assert",
    3: "character_range_start_char_read",
    4: "character_range_end_char_read",
    5: "character_range_start_code",
    6: "character_range_end_code",
    7: "character_range_order_assert",
    8: "character_range_inclusive_return",
}

COMPLEMENT_OBSERVATIONS_BY_SUFFIX = {
    1: "character_complement_operation",
    2: "character_complement_all_characters",
    3: "character_complement_difference_return",
}


def expected_observation(requirement_id: str) -> str:
    if requirement_id.startswith("ecma262-22.2.2.9.1-"):
        suffix = suffix_number(requirement_id)
        if suffix in RANGE_OBSERVATIONS_BY_SUFFIX:
            return RANGE_OBSERVATIONS_BY_SUFFIX[suffix]
    if requirement_id.startswith("ecma262-22.2.2.9.6-"):
        suffix = suffix_number(requirement_id)
        if suffix in COMPLEMENT_OBSERVATIONS_BY_SUFFIX:
            return COMPLEMENT_OBSERVATIONS_BY_SUFFIX[suffix]
    raise SystemExit(
        f"unsupported character-class exact requirement id: {requirement_id}"
    )


def is_range_requirement(requirement_id: str) -> bool:
    return requirement_id.startswith("ecma262-22.2.2.9.1-")


def validate_source_row(row: dict[str, str]) -> None:
    requirement_id = row["requirement_id"]
    expected = {
        "mapping_family": "match_engine_character_classes",
        "executable_layer": "match_engine",
        "product_surface": "match_engine",
        "ledger_state": "open_requirement_to_test_mapping_missing",
        "mapping_state": "open_exact_case_selection",
    }
    validate_expected_fields(
        row,
        expected,
        context="character-class source row",
    )
    expected_observation(requirement_id)
    if not Path(row["source_file"]).is_file():
        raise SystemExit(
            f"character-class source row {requirement_id} source is missing: "
            f"{row['source_file']}"
        )


def expected_ids() -> set[str]:
    ids = {
        f"ecma262-22.2.2.9.1-{number:04d}"
        for number in RANGE_OBSERVATIONS_BY_SUFFIX
    }
    ids.update(
        f"ecma262-22.2.2.9.6-{number:04d}"
        for number in COMPLEMENT_OBSERVATIONS_BY_SUFFIX
    )
    return ids


def selected_source_rows(rows: list[dict[str, str]]) -> list[dict[str, str]]:
    return select_expected_source_rows(
        rows,
        include_row=lambda row: row["mapping_family"]
        == "match_engine_character_classes",
        expected_ids=expected_ids(),
        validate_row=validate_source_row,
        duplicate_message=lambda requirement_id: (
            f"duplicate character-class source row {requirement_id}"
        ),
        missing_prefix="character-class source rows missing from worklist: ",
        extra_prefix="unexpected character-class source rows in worklist: ",
    )


def validate_existing_plan_source_row(row: dict[str, str]) -> None:
    requirement_id = row["requirement_id"]
    expected = {
        "mapping_family": "match_engine_character_classes",
        "executable_layer": "match_engine",
        "target_test_artifact": TARGET_TEST_ARTIFACT,
    }
    validate_expected_fields(
        row,
        expected,
        context="character-class existing plan row",
    )
    expected_observation(requirement_id)
    if not Path(row["source_file"]).is_file():
        raise SystemExit(
            f"character-class existing plan row {requirement_id} source "
            f"is missing: {row['source_file']}"
        )


def selected_existing_plan_source_rows(rows: list[dict[str, str]]) -> list[dict[str, str]]:
    selected: dict[str, dict[str, str]] = {}
    for row in rows:
        if row["mapping_family"] != "match_engine_character_classes":
            continue
        requirement_id = row["requirement_id"]
        if requirement_id in selected:
            raise SystemExit(
                f"duplicate character-class existing plan row {requirement_id}"
            )
        validate_existing_plan_source_row(row)
        selected[requirement_id] = row

    missing = sorted(expected_ids().difference(selected))
    extra = sorted(set(selected).difference(expected_ids()))
    if missing:
        raise SystemExit(
            "character-class existing plan rows missing: "
            + ", ".join(missing[:10])
        )
    if extra:
        raise SystemExit(
            "unexpected character-class existing plan rows: "
            + ", ".join(extra[:10])
        )
    return [selected[requirement_id] for requirement_id in sorted(expected_ids())]


def behavior_case(requirement_id: str) -> dict[str, str]:
    if is_range_requirement(requirement_id):
        return {
            "character_class_subfamily": "character_range",
            "character_class_route": "character_range_runtime_semantics",
            "case_route": "ascii_range_member_success",
            "pattern": "[a-c]",
            "flags": "",
            "input_text": "b",
            "expected_search_result": "true",
            "expected_observed": "true",
            "expected_behavior": "character_range_exact_plan_observable",
            "coverage_credit": "none_match_engine_character_classes_exact_planned",
            "plan_state": "planned_not_executable",
            "observability_status": "character_range_model_observable",
            "next_action": "materialize_match_engine_character_class_exact_case",
        }
    return {
        "character_class_subfamily": "character_complement",
        "character_class_route": "character_complement_allcharacters_policy",
        "case_route": "ascii_complement_member_success",
        "pattern": "[^a]",
        "flags": "",
        "input_text": "b",
        "expected_search_result": "true",
        "expected_observed": "true",
        "expected_behavior": "character_complement_exact_plan_observable",
        "coverage_credit": "none_match_engine_character_classes_exact_planned",
        "plan_state": "planned_not_executable",
        "observability_status": "character_complement_allcharacters_model_observable",
        "next_action": "materialize_match_engine_character_class_exact_case",
    }


def plan_row(row: dict[str, str]) -> dict[str, str]:
    requirement_id = row["requirement_id"]
    observation = expected_observation(requirement_id)
    exact_case_id = (
        f"match-engine-character-classes-exact:{requirement_id}:"
        f"{safe_id(observation)}"
    )
    return {
        "plan_id": f"match-engine-character-classes-exact-plan:{requirement_id}",
        **copy_requirement_metadata(row, include_local_id=True),
        "mapping_family": "match_engine_character_classes",
        "executable_layer": "match_engine",
        **behavior_case(requirement_id),
        "exact_case_family": observation,
        "exact_case_id": exact_case_id,
        "expected_observation": observation,
        "target_test_artifact": TARGET_TEST_ARTIFACT,
        "exact_case_obligation": row["requirement_text"],
        "observability_reason": (
            "CharacterRange rows are checked through a test-only matcher model "
            "observation plus public Ecma_regex.search behavior; "
            "CharacterComplement rows are checked through an explicit "
            "AllCharacters(rer) single-code-unit model plus public "
            "Ecma_regex.search behavior"
        ),
        "plan_reason": (
            "character-class exact cases map ECMA-262 22.2.2.9.1/22.2.2.9.6 "
            "rows to executable range and complement evidence where the "
            "current runtime can prove the normative operation without "
            "over-crediting wider Unicode character-class semantics"
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
            f"missing requirement-test worklist at {worklist}; run "
            "tools/map_ecma262_requirements_to_tests.py first"
        )

    fields, worklist_rows = read_tsv(worklist)
    require_columns(
        worklist,
        fields,
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
            "product_surface",
            "ledger_state",
            "mapping_state",
        },
    )
    worklist_source_ids = {
        row["requirement_id"]
        for row in worklist_rows
        if row["mapping_family"] == "match_engine_character_classes"
    }
    if expected_ids().issubset(worklist_source_ids):
        source_rows = selected_source_rows(worklist_rows)
    elif detail.is_file():
        existing_fields, existing_rows = read_tsv(detail)
        require_columns(
            detail,
            existing_fields,
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
                "target_test_artifact",
            },
        )
        source_rows = selected_existing_plan_source_rows(existing_rows)
    else:
        source_rows = selected_source_rows(worklist_rows)
    rows = [plan_row(row) for row in source_rows]
    validate_unique_ids(rows)

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
        "character_class_subfamily",
        "character_class_route",
        "case_route",
        "exact_case_family",
        "exact_case_id",
        "pattern",
        "flags",
        "input_text",
        "expected_search_result",
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
    credit_counts = Counter(row["coverage_credit"] for row in rows)
    search_counts = Counter(row["expected_search_result"] for row in rows)
    observation_counts = Counter(row["expected_observation"] for row in rows)
    subfamily_counts = Counter(row["character_class_subfamily"] for row in rows)
    route_counts = Counter(row["character_class_route"] for row in rows)
    observability_counts = Counter(row["observability_status"] for row in rows)
    summary_lines = [
        "ecma262_snapshot\t2026\n",
        f"input_worklist\t{worklist}\n",
        f"match_engine_character_classes_exact_plan_rows\t{len(rows)}\n",
        f"planned_executable_rows\t{state_counts.get('planned_not_executable', 0)}\n",
        "deferred_rows\t"
        f"{state_counts.get('deferred_requires_allcharacters_model', 0)}\n",
        f"target_test_artifact\t{TARGET_TEST_ARTIFACT}\n",
        f"planned_detail_output\t{detail}\n",
        f"planned_summary_output\t{summary}\n",
        f"dry_run\t{bool_text(args.dry_run)}\n",
    ]
    for name, count in sorted(state_counts.items()):
        summary_lines.append(f"plan_state_{name}\t{count}\n")
    for name, count in sorted(credit_counts.items()):
        summary_lines.append(f"coverage_credit_{name}\t{count}\n")
    for name, count in sorted(search_counts.items()):
        summary_lines.append(f"expected_search_result_{name}\t{count}\n")
    for name, count in sorted(observation_counts.items()):
        summary_lines.append(f"expected_observation_{name}\t{count}\n")
    for name, count in sorted(subfamily_counts.items()):
        summary_lines.append(f"character_class_subfamily_{name}\t{count}\n")
    for name, count in sorted(route_counts.items()):
        summary_lines.append(f"character_class_route_{name}\t{count}\n")
    for name, count in sorted(observability_counts.items()):
        summary_lines.append(f"observability_status_{name}\t{count}\n")

    if not args.dry_run:
        cache.mkdir(parents=True, exist_ok=True)
        with detail.open("w", encoding="utf-8", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames, delimiter="\t")
            writer.writeheader()
            writer.writerows(rows)
        summary.write_text("".join(summary_lines), encoding="utf-8")

    print("".join(summary_lines), end="")


if __name__ == "__main__":
    main()
