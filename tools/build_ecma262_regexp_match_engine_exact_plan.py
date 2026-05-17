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


DETAIL_NAME = "ecma262-regexp-match-engine-exact-plan.tsv"
SUMMARY_NAME = "ecma262-regexp-match-engine-exact-plan.summary"
TARGET_TEST_ARTIFACT = "test/test_ecma262_match_engine_exact_plan.ml"


EXACT_CASES = {
    "ecma262-22.2.2.7-0003": {
        "family": "atom_pattern_character_grammar",
        "pattern": "a",
        "flags": "",
        "input": "xxa",
        "expected": True,
        "obligation": "Atom :: PatternCharacter contributes a matcher for the source character",
    },
    "ecma262-22.2.2.7-0004": {
        "family": "atom_pattern_character_value",
        "pattern": "a",
        "flags": "",
        "input": "a",
        "expected": True,
        "obligation": "CompileAtom reads the character matched by PatternCharacter",
    },
    "ecma262-22.2.2.7-0005": {
        "family": "atom_pattern_character_singleton_charset",
        "pattern": "a",
        "flags": "",
        "input": "b",
        "expected": False,
        "obligation": "CompileAtom builds a one-element CharSet for PatternCharacter",
    },
    "ecma262-22.2.2.7-0006": {
        "family": "atom_pattern_character_charset_matcher",
        "pattern": "a",
        "flags": "",
        "input": "za",
        "expected": True,
        "obligation": "CompileAtom returns CharacterSetMatcher for PatternCharacter",
    },
    "ecma262-22.2.2.3.4-0006": {
        "family": "match_sequence_forward_continuation",
        "pattern": "ab",
        "flags": "",
        "input": "ab",
        "expected": True,
        "obligation": "Forward MatchSequence creates a continuation from the first matcher to the second matcher",
    },
    "ecma262-22.2.2.3.4-0008": {
        "family": "match_sequence_forward_second_matcher",
        "pattern": "ab",
        "flags": "",
        "input": "ab",
        "expected": True,
        "obligation": "Forward MatchSequence invokes the second matcher after the first matcher advances the state",
    },
    "ecma262-22.2.2.3.4-0009": {
        "family": "match_sequence_forward_first_then_second",
        "pattern": "ab",
        "flags": "",
        "input": "xab",
        "expected": True,
        "obligation": "Forward MatchSequence starts with the first matcher and reaches the second through the continuation",
    },
    "ecma262-22.2.2.3.3-0001": {
        "family": "match_two_alternatives_matcher",
        "pattern": "a|b",
        "flags": "",
        "input": "b",
        "expected": True,
        "obligation": "MatchTwoAlternatives returns a matcher that can match through the alternation",
    },
    "ecma262-22.2.2.3.3-0002": {
        "family": "match_two_alternatives_closure",
        "deferred": "requires_match_state_model",
        "obligation": "The generated Matcher closes over m1, m2, x, and c; boolean search cannot inspect matcher parameters",
    },
    "ecma262-22.2.2.3.3-0003": {
        "family": "match_two_alternatives_match_state_assert",
        "deferred": "requires_match_state_model",
        "obligation": "The x MatchState assertion needs an explicit MatchState model or observer",
    },
    "ecma262-22.2.2.3.3-0004": {
        "family": "match_two_alternatives_continuation_assert",
        "deferred": "requires_match_state_model",
        "obligation": "The c MatcherContinuation assertion needs an explicit continuation model or observer",
    },
    "ecma262-22.2.2.3.3-0005": {
        "family": "match_two_alternatives_first_matcher",
        "pattern": "a|b",
        "flags": "",
        "input": "a",
        "expected": True,
        "obligation": "The first alternative is invoked and can produce a successful match",
    },
    "ecma262-22.2.2.3.3-0006": {
        "family": "match_two_alternatives_return_first_result",
        "deferred": "requires_exec_result_observer",
        "obligation": "Returning r, not merely succeeding, needs an exec result observer for left-priority result identity",
    },
    "ecma262-22.2.2.3.3-0007": {
        "family": "match_two_alternatives_second_matcher",
        "pattern": "a|b",
        "flags": "",
        "input": "b",
        "expected": True,
        "obligation": "The second alternative is invoked when the first alternative fails",
    },
}


def validate_requirement_row(row: dict[str, str]) -> None:
    requirement_id = row["requirement_id"]
    expected = {
        "product_surface": "match_engine",
        "route_status": "needs_requirement_to_test_case_mapping",
    }
    validate_expected_fields(row, expected, context="match-engine exact row")
    if row["semantic_family"] not in {"atoms", "concatenation", "alternation"}:
        raise SystemExit(
            f"match-engine exact row {requirement_id} has "
            f"semantic_family={row['semantic_family']!r}; expected atoms, "
            "concatenation, or alternation"
        )
    require_coverage_area(
        row,
        "regexp_exec_and_captures",
        context="match-engine exact row",
    )


def plan_row(row: dict[str, str]) -> dict[str, str]:
    validate_requirement_row(row)
    requirement_id = row["requirement_id"]
    case = EXACT_CASES[requirement_id]
    deferred = case.get("deferred")
    if deferred is None:
        exact_case_id = f"match-engine-exact:{requirement_id}:{safe_id(case['family'])}"
        expected_search_result = bool_text(case["expected"])
        expected_behavior = "search_true" if case["expected"] else "search_false"
        pattern = case["pattern"]
        flags = case["flags"]
        input_text = case["input"]
        coverage_credit = "none_match_engine_exact_planned"
        plan_state = "planned_not_executable"
        target_test_artifact = TARGET_TEST_ARTIFACT
        next_action = "materialize_match_engine_exact_case"
        observability_status = "search_bool_observable"
        observability_reason = (
            "public Ecma_regex.search has enough observable behavior for this "
            "requirement row"
        )
    else:
        exact_case_id = f"match-engine-deferred:{requirement_id}:{safe_id(case['family'])}"
        expected_search_result = "not_observable"
        expected_behavior = deferred
        pattern = ""
        flags = ""
        input_text = ""
        coverage_credit = "none_match_engine_exact_deferred"
        plan_state = f"deferred_{deferred}"
        target_test_artifact = ""
        next_action = f"design_{deferred}_before_credit"
        observability_status = deferred
        observability_reason = case["obligation"]
    return {
        "plan_id": f"match-engine-exact-plan:{requirement_id}",
        **copy_requirement_metadata(row, include_local_id=False),
        "mapping_family": f"match_engine_{row['semantic_family']}",
        "executable_layer": "match_engine",
        "exact_case_family": case["family"],
        "exact_case_id": exact_case_id,
        "pattern": pattern,
        "flags": flags,
        "input_text": input_text,
        "expected_search_result": expected_search_result,
        "expected_behavior": expected_behavior,
        "coverage_credit": coverage_credit,
        "plan_state": plan_state,
        "target_test_artifact": target_test_artifact,
        "exact_case_obligation": case["obligation"],
        "observability_status": observability_status,
        "observability_reason": observability_reason,
        "next_action": next_action,
        "plan_reason": (
            "match-engine exact case is planned from an ECMA-262 runtime "
            "requirement row; no ledger credit is assigned until the "
            "executable gate and exactness audit consume it; deferred rows "
            "remain uncredited until a stronger observer exists"
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
    source_rows = select_exact_case_requirement_rows(requirement_rows, EXACT_CASES)
    rows = [plan_row(row) for row in source_rows]
    validate_unique_ids(rows)

    state_counts = Counter(row["plan_state"] for row in rows)
    credit_counts = Counter(row["coverage_credit"] for row in rows)
    expected_counts = Counter(row["expected_behavior"] for row in rows)
    expected_search_counts = Counter(row["expected_search_result"] for row in rows)
    layer_counts = Counter(row["executable_layer"] for row in rows)
    family_counts = Counter(row["exact_case_family"] for row in rows)
    mapping_counts = Counter(row["mapping_family"] for row in rows)
    target_counts = Counter(row["target_test_artifact"] for row in rows)
    observability_counts = Counter(row["observability_status"] for row in rows)

    coverage_credit_rows = sum(
        count for credit, count in credit_counts.items() if not credit.startswith("none")
    )
    planned_executable_rows = state_counts.get("planned_not_executable", 0)
    deferred_rows = len(rows) - planned_executable_rows

    summary_lines = [
        "ecma262_snapshot\t2026\n",
        f"input_requirements\t{requirements}\n",
        f"input_requirement_rows\t{len(requirement_rows)}\n",
        f"source_requirement_rows\t{len(source_rows)}\n",
        f"match_engine_exact_plan_rows\t{len(rows)}\n",
        f"planned_executable_rows\t{planned_executable_rows}\n",
        f"deferred_rows\t{deferred_rows}\n",
        f"coverage_credit_rows\t{coverage_credit_rows}\n",
        f"planned_detail_output\t{detail}\n",
        f"planned_summary_output\t{summary}\n",
        f"dry_run\t{bool_text(args.dry_run)}\n",
    ]
    for name, count in sorted(state_counts.items()):
        summary_lines.append(f"plan_state_{name}\t{count}\n")
    for name, count in sorted(credit_counts.items()):
        summary_lines.append(f"coverage_credit_{name}\t{count}\n")
    for name, count in sorted(expected_counts.items()):
        summary_lines.append(f"expected_behavior_{name}\t{count}\n")
    for name, count in sorted(expected_search_counts.items()):
        summary_lines.append(f"expected_search_result_{name}\t{count}\n")
    for name, count in sorted(layer_counts.items()):
        summary_lines.append(f"executable_layer_{name}\t{count}\n")
    for name, count in sorted(mapping_counts.items()):
        summary_lines.append(f"mapping_family_{name}\t{count}\n")
    for name, count in sorted(family_counts.items()):
        summary_lines.append(f"exact_case_family_{name}\t{count}\n")
    for name, count in sorted(target_counts.items()):
        if name:
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
        "expected_search_result",
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
    print(summary.read_text(encoding="utf-8"), end="")


if __name__ == "__main__":
    main()
