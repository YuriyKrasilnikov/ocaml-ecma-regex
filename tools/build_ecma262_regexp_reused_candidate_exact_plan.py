#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
from collections import Counter
from pathlib import Path

from ecma262_tooling import (
    bool_text,
    read_tsv,
    require_columns,
    safe_id,
    split_csv_set,
    validate_unique_ids,
)


DETAIL_NAME = "ecma262-regexp-reused-candidate-exact-plan.tsv"
SUMMARY_NAME = "ecma262-regexp-reused-candidate-exact-plan.summary"
TARGET_TEST_ARTIFACT = "test/test_ecma262_reused_candidate_exact_compile_parser.ml"


def existing_data_rows(path: Path) -> int:
    if not path.is_file():
        return 0
    with path.open(encoding="utf-8", newline="") as f:
        reader = csv.DictReader(f, delimiter="\t")
        return sum(1 for _ in reader)


def test262_source_exists(case_source: str) -> bool:
    if not case_source:
        return False
    source_path = case_source.split(":", 1)[0]
    return Path("external/test262", source_path).is_file()


def ecma262_source_exists(source_file: str) -> bool:
    return bool(source_file) and Path(source_file).is_file()


def first_matching(tags: set[str], candidates: list[str]) -> str:
    for candidate in candidates:
        if candidate in tags:
            return candidate
    return "accepted_literal"


def text_contains(row: dict[str, str], needle: str) -> bool:
    return needle.lower() in row["requirement_text"].lower()


def planned_flags(row: dict[str, str]) -> str:
    tags = split_csv_set(row["selector_tags"]).union(split_csv_set(row["selected_feature_tags"]))
    if text_contains(row, "contains v") or "unicode_sets" in tags or "unicode_sets_mode" in tags:
        return "v"
    if text_contains(row, "contains u") or "unicode_mode" in tags or "unicode_property" in tags:
        return "u"
    return row["selected_flags"]


def planned_core_atom(row: dict[str, str]) -> str:
    tags = split_csv_set(row["selector_tags"]).union(split_csv_set(row["selected_feature_tags"]))
    text = row["requirement_text"]

    if "ClassSetRange ::" in text or "ClassUnion ::" in text or "class_range" in tags:
        return "[A-Z]"
    if "ClassControlLetter ::" in text:
        return "[\\cA]"
    if "ClassEscape ::" in text or "character_class" in tags:
        return "[A-Z]"
    if "unicode_sets" in tags or "unicode_sets_mode" in tags:
        return "[\\p{Script=Latin}&&\\p{Letter}]"
    if "unicode_property" in tags:
        return "\\p{Script=Latin}"
    if "hex_escape" in tags:
        return "\\x41"
    if "control_escape" in tags:
        return "\\cA"
    if "unicode_escape" in tags:
        return "\\u{41}"
    if "dot" in tags:
        return "."
    if "escape" in tags:
        return "\\n"
    return "a"


def planned_pattern(row: dict[str, str]) -> str:
    text = row["requirement_text"]
    tags = split_csv_set(row["selector_tags"]).union(split_csv_set(row["selected_feature_tags"]))

    if "Assertion :: ^" in text:
        return "^a"
    if "Assertion :: $" in text:
        return "a$"
    if "Assertion :: \\b" in text:
        return "\\b"
    if "Assertion :: \\B" in text:
        return "\\B"
    if "QuantifierPrefix :: *" in text:
        return "a*"
    if "QuantifierPrefix :: +" in text:
        return "a+"
    if "QuantifierPrefix :: ?" in text:
        return "a?"
    if "QuantifierPrefix :: { DecimalDigits" in text and "," in text:
        return "a{1,2}"
    if "QuantifierPrefix :: { DecimalDigits" in text:
        return "a{1}"
    if "InvalidBracedQuantifier ::" in text:
        return "x{2147483648}x"
    if "Alternative :: [empty]" in text:
        return "a|"
    if "Disjunction" in text or "alternation" in tags:
        return "a|b"

    atom = planned_core_atom(row)
    if "named_capture" in tags:
        atom = f"(?<name>{atom})"
    elif "capturing_group" in tags:
        atom = f"({atom})"
    if "modifiers" in tags:
        atom = f"(?i:{atom})"
    return atom


def implementation_pressure(row: dict[str, str]) -> str:
    tags = split_csv_set(row["selector_tags"]).union(split_csv_set(row["selected_feature_tags"]))
    primary = first_matching(
        tags,
        [
            "unicode_sets_mode",
            "unicode_sets",
            "unicode_property",
            "named_capture",
            "capturing_group",
            "character_class",
            "class_range",
            "assertion",
            "quantifier",
            "alternation",
            "control_escape",
            "hex_escape",
            "unicode_escape",
            "dot",
            "escape",
        ],
    )
    return f"materialize reused candidate exact compile/parser case for {primary}"


def validate_worklist_row(row: dict[str, str]) -> None:
    requirement_id = row["requirement_id"]
    expected = {
        "reuse_worklist_state": "reused_candidate_needs_exact_proof",
        "coverage_credit": "none_reused_candidate_worklist",
        "next_action": "split_reused_candidate_or_add_local_exact_test",
    }
    for field, expected_value in expected.items():
        if row[field] != expected_value:
            raise SystemExit(
                f"reused worklist row {requirement_id} has {field}={row[field]!r}; "
                f"expected {expected_value!r}"
            )
    if row["proof_decision"] not in {
        "needs_local_exact_case",
        "manual_spec_review_required",
    }:
        raise SystemExit(
            f"reused worklist row {requirement_id} has unsupported proof_decision "
            f"{row['proof_decision']!r}"
        )
    if row["proof_decision"] == "needs_local_exact_case":
        for field in ["selected_case_id", "selected_case_source", "selected_pattern"]:
            if not row[field]:
                raise SystemExit(f"reused worklist row {requirement_id} has empty {field}")
    if not ecma262_source_exists(row["source_file"]):
        raise SystemExit(
            f"reused worklist row {requirement_id} missing ECMA source: "
            f"{row['source_file']}"
        )
    if not test262_source_exists(row["selected_case_source"]):
        raise SystemExit(
            f"reused worklist row {requirement_id} missing test262 source: "
            f"{row['selected_case_source']}"
        )


def plan_row(row: dict[str, str]) -> dict[str, str]:
    validate_worklist_row(row)
    manual = row["proof_decision"] == "manual_spec_review_required"
    exact_case_id = "" if manual else (
        f"reused-exact:{row['requirement_id']}:{safe_id(row['mapping_family'])}"
    )
    state = "manual_spec_review_required" if manual else "planned_not_executable"
    credit = "none_manual_review_required" if manual else "none_reused_candidate_exact_planned"
    next_action = (
        "manual_spec_review_before_exact_case"
        if manual
        else "materialize_reused_candidate_exact_case"
    )
    target = "" if manual else TARGET_TEST_ARTIFACT
    pattern = "" if manual else planned_pattern(row)
    flags = "" if manual else planned_flags(row)

    return {
        "plan_id": f"reused-candidate-exact-plan:{row['requirement_id']}",
        "requirement_id": row["requirement_id"],
        "clause_id": row["clause_id"],
        "clause_title": row["clause_title"],
        "source_file": row["source_file"],
        "section_anchor": row["section_anchor"],
        "requirement_kind": row["requirement_kind"],
        "semantic_family": row["semantic_family"],
        "mapping_family": row["mapping_family"],
        "executable_layer": row["executable_layer"],
        "selector_tags": ",".join(sorted(split_csv_set(row["selector_tags"]))),
        "selected_feature_tags": ",".join(sorted(split_csv_set(row["selected_feature_tags"]))),
        "selected_case_id": row["selected_case_id"],
        "selected_case_source": row["selected_case_source"],
        "selected_pattern": row["selected_pattern"],
        "selected_flags": row["selected_flags"],
        "case_reuse_count": row["case_reuse_count"],
        "cluster_size": row["cluster_size"],
        "cluster_pressure": row["cluster_pressure"],
        "proof_decision": row["proof_decision"],
        "exact_case_id": exact_case_id,
        "planned_pattern": pattern,
        "planned_flags": flags,
        "expected_behavior": "" if manual else "compile_ok",
        "coverage_credit": credit,
        "plan_state": state,
        "target_test_artifact": target,
        "implementation_pressure": "" if manual else implementation_pressure(row),
        "next_action": next_action,
        "plan_reason": (
            "manual spec review required before exact executable case selection"
            if manual
            else "unique reused-candidate exact case planned; no coverage credit until executable gate and exactness audit consume it"
        ),
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--cache", default="cache")
    parser.add_argument(
        "--reused-candidate-worklist",
        default="cache/ecma262-regexp-reused-candidate-worklist.tsv",
    )
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--allow-empty-output-overwrite", action="store_true")
    args = parser.parse_args()

    cache = Path(args.cache)
    worklist = Path(args.reused_candidate_worklist)
    detail = cache / DETAIL_NAME
    summary = cache / SUMMARY_NAME

    if not worklist.is_file():
        raise SystemExit(
            f"missing reused-candidate worklist at {worklist}; "
            "run tools/build_ecma262_regexp_reused_candidate_worklist.py first"
        )

    worklist_fields, worklist_rows = read_tsv(worklist)
    require_columns(
        worklist,
        worklist_fields,
        {
            "worklist_id",
            "requirement_id",
            "clause_id",
            "clause_title",
            "source_file",
            "section_anchor",
            "requirement_kind",
            "requirement_text",
            "semantic_family",
            "mapping_family",
            "executable_layer",
            "selector_tags",
            "selected_feature_tags",
            "selected_case_id",
            "selected_case_source",
            "selected_pattern",
            "selected_flags",
            "case_reuse_count",
            "cluster_size",
            "cluster_pressure",
            "reuse_worklist_state",
            "proof_decision",
            "coverage_credit",
            "next_action",
        },
    )

    rows = [plan_row(row) for row in worklist_rows]
    validate_unique_ids(rows, allow_empty={"exact_case_id"})

    state_counts = Counter(row["plan_state"] for row in rows)
    decision_counts = Counter(row["proof_decision"] for row in rows)
    credit_counts = Counter(row["coverage_credit"] for row in rows)
    action_counts = Counter(row["next_action"] for row in rows)
    family_counts = Counter(row["mapping_family"] for row in rows)
    layer_counts = Counter(row["executable_layer"] for row in rows)
    pressure_counts = Counter(row["cluster_pressure"] for row in rows)
    flag_counts = Counter(
        row["planned_flags"] if row["planned_flags"] else "<none>"
        for row in rows
        if row["plan_state"] == "planned_not_executable"
    )
    target_counts = Counter(row["target_test_artifact"] for row in rows)
    planned_rows = state_counts.get("planned_not_executable", 0)
    manual_rows = state_counts.get("manual_spec_review_required", 0)
    coverage_credit_rows = sum(
        count for credit, count in credit_counts.items() if not credit.startswith("none")
    )

    summary_lines = [
        "ecma262_snapshot\t2026\n",
        f"input_reused_candidate_worklist\t{worklist}\n",
        f"reused_candidate_worklist_rows\t{len(worklist_rows)}\n",
        f"reused_candidate_exact_plan_rows\t{len(rows)}\n",
        f"planned_executable_rows\t{planned_rows}\n",
        f"manual_review_rows\t{manual_rows}\n",
        f"coverage_credit_rows\t{coverage_credit_rows}\n",
        f"planned_detail_output\t{detail}\n",
        f"planned_summary_output\t{summary}\n",
        f"dry_run\t{bool_text(args.dry_run)}\n",
    ]
    for name, count in sorted(state_counts.items()):
        summary_lines.append(f"plan_state_{name}\t{count}\n")
    for name, count in sorted(decision_counts.items()):
        summary_lines.append(f"proof_decision_{name}\t{count}\n")
    for name, count in sorted(credit_counts.items()):
        summary_lines.append(f"coverage_credit_{name}\t{count}\n")
    for name, count in sorted(action_counts.items()):
        summary_lines.append(f"next_action_{name}\t{count}\n")
    for name, count in sorted(family_counts.items()):
        summary_lines.append(f"mapping_family_{name}\t{count}\n")
    for name, count in sorted(layer_counts.items()):
        summary_lines.append(f"executable_layer_{name}\t{count}\n")
    for name, count in sorted(pressure_counts.items()):
        summary_lines.append(f"cluster_pressure_{name}\t{count}\n")
    for name, count in sorted(flag_counts.items()):
        summary_lines.append(f"planned_flags_{name}\t{count}\n")
    for name, count in sorted(target_counts.items()):
        summary_lines.append(f"target_test_artifact_{name or '<none>'}\t{count}\n")

    if args.dry_run:
        print("".join(summary_lines), end="")
        return

    existing_rows = existing_data_rows(detail)
    if not rows and existing_rows > 0 and not args.allow_empty_output_overwrite:
        raise SystemExit(
            f"refusing to overwrite non-empty reused-candidate exact plan {detail} "
            f"({existing_rows} rows) with an empty output from current "
            "reused-candidate worklist; pass --allow-empty-output-overwrite only "
            "after deliberately retiring this exact-plan evidence"
        )

    cache.mkdir(parents=True, exist_ok=True)
    fieldnames = [
        "plan_id",
        "requirement_id",
        "clause_id",
        "clause_title",
        "source_file",
        "section_anchor",
        "requirement_kind",
        "semantic_family",
        "mapping_family",
        "executable_layer",
        "selector_tags",
        "selected_feature_tags",
        "selected_case_id",
        "selected_case_source",
        "selected_pattern",
        "selected_flags",
        "case_reuse_count",
        "cluster_size",
        "cluster_pressure",
        "proof_decision",
        "exact_case_id",
        "planned_pattern",
        "planned_flags",
        "expected_behavior",
        "coverage_credit",
        "plan_state",
        "target_test_artifact",
        "implementation_pressure",
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
