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
    suffix_number,
    validate_expected_fields,
    validate_unique_ids,
)


DETAIL_NAME = "ecma262-regexp-match-engine-modifier-exact-plan.tsv"
SUMMARY_NAME = "ecma262-regexp-match-engine-modifier-exact-plan.summary"
TARGET_TEST_ARTIFACT = "test/test_ecma262_match_engine_modifier_exact_plan.ml"


CASE_TEMPLATES = {
    56: {
        "family": "modifier_add_form_grammar",
        "pattern": "(?i:a)",
        "flags": "",
        "input": "A",
        "expected": True,
        "start": "0",
        "end": "1",
        "match": "A",
        "behavior": "modifier_add_form_grammar_observable",
    },
    57: {
        "family": "modifier_add_source_text",
        "pattern": "(?s:.)",
        "flags": "",
        "input": "\\n",
        "expected": True,
        "start": "0",
        "end": "1",
        "match": "\\n",
        "behavior": "modifier_add_source_text_observable",
    },
    58: {
        "family": "modifier_remove_empty_string",
        "pattern": "(?m:^a)",
        "flags": "",
        "input": "\\na",
        "expected": True,
        "start": "1",
        "end": "2",
        "match": "a",
        "behavior": "modifier_remove_empty_string_observable",
    },
    59: {
        "family": "modifier_update_add",
        "pattern": "(?i:a)b",
        "flags": "",
        "input": "Ab",
        "expected": True,
        "start": "0",
        "end": "2",
        "match": "Ab",
        "behavior": "modifier_update_add_observable",
    },
    60: {
        "family": "modifier_compile_subpattern_add_scope",
        "pattern": "(?i:a)b",
        "flags": "",
        "input": "AB",
        "expected": False,
        "start": "",
        "end": "",
        "match": "",
        "behavior": "modifier_compile_subpattern_add_scope_observable",
    },
    61: {
        "family": "modifier_add_remove_form_grammar",
        "pattern": "(?m-i:^a)",
        "flags": "i",
        "input": "\\na",
        "expected": True,
        "start": "1",
        "end": "2",
        "match": "a",
        "behavior": "modifier_add_remove_form_grammar_observable",
    },
    62: {
        "family": "modifier_first_add_source_text",
        "pattern": "(?m-i:^a)",
        "flags": "i",
        "input": "\\na",
        "expected": True,
        "start": "1",
        "end": "2",
        "match": "a",
        "behavior": "modifier_first_add_source_text_observable",
    },
    63: {
        "family": "modifier_second_remove_source_text",
        "pattern": "(?m-i:^a)",
        "flags": "i",
        "input": "\\nA",
        "expected": False,
        "start": "",
        "end": "",
        "match": "",
        "behavior": "modifier_second_remove_source_text_observable",
    },
    64: {
        "family": "modifier_update_add_remove",
        "pattern": "(?s-i:a.)",
        "flags": "i",
        "input": "a\\n",
        "expected": True,
        "start": "0",
        "end": "2",
        "match": "a\\n",
        "behavior": "modifier_update_add_remove_observable",
    },
    65: {
        "family": "modifier_compile_subpattern_add_remove_scope",
        "pattern": "(?s-i:a.)",
        "flags": "i",
        "input": "A\\n",
        "expected": False,
        "start": "",
        "end": "",
        "match": "",
        "behavior": "modifier_compile_subpattern_add_remove_scope_observable",
    },
}


def selected_rows(rows: list[dict[str, str]]) -> list[dict[str, str]]:
    selected = [
        row
        for row in rows
        if row["plan_state"] == "deferred_requires_modifier_runtime_model"
        and row["coverage_credit"] == "none_match_engine_atoms_exact_deferred"
        and row["atom_subfamily"] == "modifiers_group_atom"
        and row["atom_semantic_route"] == "scoped_modifier_runtime_model"
        and row["expected_behavior"] == "requires_modifier_runtime_model"
        and row["observability_status"] == "requires_modifier_runtime_model"
    ]
    if len(selected) != 10:
        raise SystemExit(
            "expected 10 deferred match-engine modifier atom rows, got "
            f"{len(selected)}"
        )
    suffixes = {suffix_number(row["requirement_id"]) for row in selected}
    if suffixes != set(CASE_TEMPLATES):
        raise SystemExit(
            "unexpected modifier requirement suffixes: "
            + ", ".join(str(value) for value in sorted(suffixes))
        )
    return sorted(selected, key=lambda row: row["requirement_id"])


def validate_source_row(row: dict[str, str]) -> None:
    requirement_id = row["requirement_id"]
    expected = {
        "clause_id": "22.2.2.7",
        "clause_title": "Runtime Semantics: CompileAtom",
        "mapping_family": "match_engine_atoms",
        "executable_layer": "match_engine",
        "atom_subfamily": "modifiers_group_atom",
        "atom_semantic_route": "scoped_modifier_runtime_model",
    }
    validate_expected_fields(row, expected, context="modifier source row")
    if not row["source_file"] or not Path(row["source_file"]).is_file():
        raise SystemExit(
            f"modifier source row {requirement_id} source is missing: "
            f"{row['source_file']!r}"
        )


def plan_row(source: dict[str, str]) -> dict[str, str]:
    validate_source_row(source)
    requirement_id = source["requirement_id"]
    number = suffix_number(requirement_id)
    case = CASE_TEMPLATES[number]
    exact_case_id = (
        f"match-engine-modifier-exact:{requirement_id}:"
        f"{safe_id(case['family'])}"
    )
    return {
        "plan_id": f"match-engine-modifier-exact-plan:{requirement_id}",
        "source_atom_plan_id": source["plan_id"],
        **copy_requirement_metadata(source, include_local_id=False),
        "mapping_family": "match_engine_atoms",
        "executable_layer": "match_engine",
        "modifier_subfamily": source["atom_subfamily"],
        "modifier_semantic_route": source["atom_semantic_route"],
        "exact_case_family": case["family"],
        "exact_case_id": exact_case_id,
        "pattern": case["pattern"],
        "flags": case["flags"],
        "input_text": case["input"],
        "expected_search_result": bool_text(case["expected"]),
        "expected_exec_result": bool_text(case["expected"]),
        "expected_start_index": case["start"],
        "expected_end_index": case["end"],
        "expected_match_text": case["match"],
        "expected_behavior": case["behavior"],
        "coverage_credit": "none_match_engine_modifier_exact_planned",
        "plan_state": "planned_not_executable",
        "target_test_artifact": TARGET_TEST_ARTIFACT,
        "exact_case_obligation": source["requirement_text"],
        "observability_status": "search_and_exec_observable",
        "observability_reason": (
            "public Ecma_regex.search observes scoped modifier success/failure "
            "and public Ecma_regex.exec observes start, end, and matched text "
            "for ECMA-262 CompileAtom modifier groups"
        ),
        "next_action": "materialize_match_engine_modifier_exact_case",
        "plan_reason": (
            "CompileAtom modifier rows are selected from the atom deferred "
            "runtime-model bucket and must pass this scoped i/m/s gate before "
            "exactness audit or coverage ledger may consume them"
        ),
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--cache", default="cache")
    parser.add_argument(
        "--atoms-exact-plan",
        default="cache/ecma262-regexp-match-engine-atoms-exact-plan.tsv",
    )
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    cache = Path(args.cache)
    atoms_exact_plan = Path(args.atoms_exact_plan)
    detail = cache / DETAIL_NAME
    summary = cache / SUMMARY_NAME

    if not atoms_exact_plan.is_file():
        raise SystemExit(
            f"missing match-engine atoms exact plan at {atoms_exact_plan}; "
            "run tools/build_ecma262_regexp_match_engine_atoms_exact_plan.py first"
        )

    fields, atom_rows = read_tsv(atoms_exact_plan)
    require_columns(
        atoms_exact_plan,
        fields,
        {
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
            "atom_subfamily",
            "atom_semantic_route",
            "expected_behavior",
            "coverage_credit",
            "plan_state",
            "observability_status",
        },
    )

    rows = [plan_row(row) for row in selected_rows(atom_rows)]
    validate_unique_ids(rows)

    state_counts = Counter(row["plan_state"] for row in rows)
    credit_counts = Counter(row["coverage_credit"] for row in rows)
    behavior_counts = Counter(row["expected_behavior"] for row in rows)
    search_counts = Counter(row["expected_search_result"] for row in rows)
    exec_counts = Counter(row["expected_exec_result"] for row in rows)
    family_counts = Counter(row["exact_case_family"] for row in rows)
    route_counts = Counter(row["modifier_semantic_route"] for row in rows)

    coverage_credit_rows = sum(
        count for credit, count in credit_counts.items() if not credit.startswith("none")
    )
    planned_executable_rows = state_counts.get("planned_not_executable", 0)

    summary_lines = [
        "ecma262_snapshot\t2026\n",
        f"input_atoms_exact_plan\t{atoms_exact_plan}\n",
        f"match_engine_modifier_exact_plan_rows\t{len(rows)}\n",
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
    for name, count in sorted(family_counts.items()):
        summary_lines.append(f"exact_case_family_{name}\t{count}\n")
    for name, count in sorted(route_counts.items()):
        summary_lines.append(f"modifier_semantic_route_{name}\t{count}\n")

    if args.dry_run:
        print("".join(summary_lines), end="")
        return

    cache.mkdir(parents=True, exist_ok=True)
    fieldnames = [
        "plan_id",
        "source_atom_plan_id",
        "requirement_id",
        "clause_id",
        "clause_title",
        "source_file",
        "section_anchor",
        "requirement_kind",
        "requirement_text",
        "mapping_family",
        "executable_layer",
        "modifier_subfamily",
        "modifier_semantic_route",
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
