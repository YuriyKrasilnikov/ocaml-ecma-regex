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


DETAIL_NAME = "ecma262-regexp-match-state-exact-plan.tsv"
SUMMARY_NAME = "ecma262-regexp-match-state-exact-plan.summary"
TARGET_TEST_ARTIFACT = "test/test_ecma262_match_state_exact_plan.ml"


EXACT_CASES = {
    "ecma262-22.2.2.3.3-0002": {
        "family": "match_two_alternatives_closure",
        "pattern": "a|b",
        "flags": "",
        "input": "a",
        "expected_observation": "match_two_alternatives_closure",
        "obligation": (
            "MatchTwoAlternatives returns a Matcher closure that receives "
            "the current MatchState and MatcherContinuation and closes over "
            "the alternative matchers"
        ),
    },
    "ecma262-22.2.2.3.3-0003": {
        "family": "match_two_alternatives_match_state_assert",
        "pattern": "a|b",
        "flags": "",
        "input": "a",
        "expected_observation": "match_state_parameter",
        "obligation": (
            "The x parameter passed to the MatchTwoAlternatives matcher is "
            "represented as a MatchState in the executable matcher model"
        ),
    },
    "ecma262-22.2.2.3.3-0004": {
        "family": "match_two_alternatives_continuation_assert",
        "pattern": "a|b",
        "flags": "",
        "input": "a",
        "expected_observation": "matcher_continuation_parameter",
        "obligation": (
            "The c parameter passed to the MatchTwoAlternatives matcher is "
            "represented as a MatcherContinuation in the executable matcher model"
        ),
    },
}


def validate_requirement_row(row: dict[str, str]) -> None:
    expected = {
        "product_surface": "match_engine",
        "semantic_family": "alternation",
        "route_status": "needs_requirement_to_test_case_mapping",
    }
    validate_expected_fields(row, expected, context="match-state exact row")
    require_coverage_area(
        row,
        "regexp_exec_and_captures",
        context="match-state exact row",
    )


def plan_row(row: dict[str, str]) -> dict[str, str]:
    validate_requirement_row(row)
    requirement_id = row["requirement_id"]
    case = EXACT_CASES[requirement_id]
    exact_case_id = f"match-state-exact:{requirement_id}:{safe_id(case['family'])}"
    return {
        "plan_id": f"match-state-exact-plan:{requirement_id}",
        **copy_requirement_metadata(row, include_local_id=False),
        "mapping_family": f"match_engine_{row['semantic_family']}",
        "executable_layer": "match_engine",
        "exact_case_family": case["family"],
        "exact_case_id": exact_case_id,
        "pattern": case["pattern"],
        "flags": case["flags"],
        "input_text": case["input"],
        "expected_observation": case["expected_observation"],
        "expected_observed": "true",
        "expected_behavior": "match_state_model_observable",
        "coverage_credit": "none_match_state_exact_planned",
        "plan_state": "planned_not_executable",
        "target_test_artifact": TARGET_TEST_ARTIFACT,
        "exact_case_obligation": case["obligation"],
        "observability_status": "match_state_model_observable",
        "observability_reason": (
            "Ecma_regex_core exposes a test-only matcher model observation "
            "without adding public Ecma_regex API surface"
        ),
        "next_action": "materialize_match_state_exact_case",
        "plan_reason": (
            "match-state exact case is planned from an ECMA-262 runtime "
            "requirement row; no ledger credit is assigned until the "
            "executable matcher-model gate and exactness audit consume it"
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
    source_rows = select_exact_case_requirement_rows(
        requirement_rows,
        EXACT_CASES,
        "match-state exact case definitions absent from requirement mapping",
    )
    rows = [plan_row(row) for row in source_rows]
    validate_unique_ids(rows)

    state_counts = Counter(row["plan_state"] for row in rows)
    credit_counts = Counter(row["coverage_credit"] for row in rows)
    behavior_counts = Counter(row["expected_behavior"] for row in rows)
    observation_counts = Counter(row["expected_observation"] for row in rows)
    layer_counts = Counter(row["executable_layer"] for row in rows)
    mapping_counts = Counter(row["mapping_family"] for row in rows)
    target_counts = Counter(row["target_test_artifact"] for row in rows)
    observability_counts = Counter(row["observability_status"] for row in rows)

    coverage_credit_rows = sum(
        count for credit, count in credit_counts.items() if not credit.startswith("none")
    )
    planned_executable_rows = state_counts.get("planned_not_executable", 0)

    summary_lines = [
        "ecma262_snapshot\t2026\n",
        f"input_requirements\t{requirements}\n",
        f"input_requirement_rows\t{len(requirement_rows)}\n",
        f"source_requirement_rows\t{len(source_rows)}\n",
        f"match_state_exact_plan_rows\t{len(rows)}\n",
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
    for name, count in sorted(observation_counts.items()):
        summary_lines.append(f"expected_observation_{name}\t{count}\n")
    for name, count in sorted(layer_counts.items()):
        summary_lines.append(f"executable_layer_{name}\t{count}\n")
    for name, count in sorted(mapping_counts.items()):
        summary_lines.append(f"mapping_family_{name}\t{count}\n")
    for name, count in sorted(target_counts.items()):
        summary_lines.append(f"target_test_artifact_{name}\t{count}\n")
    for name, count in sorted(observability_counts.items()):
        summary_lines.append(f"observability_status_{name}\t{count}\n")

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
    with detail.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, delimiter="\t", fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)
    with summary.open("w", encoding="utf-8") as f:
        f.write("".join(summary_lines))

    print("".join(summary_lines), end="")


if __name__ == "__main__":
    main()
