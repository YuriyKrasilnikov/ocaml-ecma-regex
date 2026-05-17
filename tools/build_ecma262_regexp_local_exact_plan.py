#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
from collections import Counter
from pathlib import Path

from ecma262_tooling import bool_text, read_tsv, safe_id, split_csv_set, validate_unique_ids


DETAIL_NAME = "ecma262-regexp-local-exact-plan.tsv"
SUMMARY_NAME = "ecma262-regexp-local-exact-plan.summary"


def existing_data_rows(path: Path) -> int:
    if not path.is_file():
        return 0
    with path.open(encoding="utf-8", newline="") as f:
        reader = csv.DictReader(f, delimiter="\t")
        return sum(1 for _ in reader)


def first_matching(tags: set[str], candidates: list[str]) -> str:
    for candidate in candidates:
        if candidate in tags:
            return candidate
    return "accepted_literal"


def local_case_family(row: dict[str, str]) -> str:
    mapping_family = row["mapping_family"]
    tags = split_csv_set(row["selector_tags"])
    missing = split_csv_set(row["missing_selector_tags"])
    combined = tags.union(missing)

    if mapping_family.startswith("compile_"):
        return mapping_family
    if "unicode_sets_mode" in combined or "unicode_sets" in combined:
        return "parser_unicode_sets_local_exact"
    if "unicode_property" in combined:
        return "parser_unicode_property_local_exact"
    if "modifiers" in combined:
        return "parser_modifiers_local_exact"
    if "control_escape" in combined or "hex_escape" in combined:
        return "parser_character_escape_local_exact"
    if "unicode_escape" in combined:
        return "parser_unicode_escape_local_exact"
    if "named_capture" in combined or "capturing_group" in combined:
        return "parser_capture_local_exact"
    if "character_class" in combined:
        return "parser_character_class_local_exact"
    if "alternation" in combined:
        return "parser_alternation_local_exact"
    if "dot" in combined:
        return "parser_dot_local_exact"
    return mapping_family


def planned_flags(tags: set[str]) -> str:
    if "unicode_sets_mode" in tags or "unicode_sets" in tags:
        return "v"
    if "unicode_mode" in tags or "unicode_property" in tags:
        return "u"
    return ""


def planned_core_atom(tags: set[str]) -> str:
    if "unicode_sets_mode" in tags or "unicode_sets" in tags:
        return "[\\p{Script=Latin}&&\\p{Letter}]"
    if "unicode_property" in tags:
        return "\\p{Script=Latin}"
    if "unicode_escape" in tags:
        return "\\u{41}"
    if "hex_escape" in tags:
        return "\\x41"
    if "control_escape" in tags:
        return "\\cA"
    if "character_class" in tags:
        return "[A-Z]"
    if "dot" in tags:
        return "."
    if "escape" in tags:
        return "\\n"
    return "a"


def planned_pattern(row: dict[str, str]) -> str:
    tags = split_csv_set(row["selector_tags"])
    atom = planned_core_atom(tags)

    if "named_capture" in tags:
        atom = f"(?<name>{atom})"
    elif "capturing_group" in tags:
        atom = f"({atom})"

    if "modifiers" in tags:
        atom = f"(?i:{atom})"

    if "alternation" in tags:
        return f"(?:{atom}|b)"
    return atom


def spec_reason(row: dict[str, str], requirement: dict[str, str] | None) -> str:
    if requirement is None:
        return "selector-gap row has no matching requirement matrix row"
    text = requirement["requirement_text"]
    compact = " ".join(text.split())
    if len(compact) > 180:
        compact = compact[:177] + "..."
    return compact


def implementation_pressure(row: dict[str, str]) -> str:
    tags = split_csv_set(row["missing_selector_tags"])
    primary = first_matching(
        tags,
        [
            "unicode_sets_mode",
            "unicode_sets",
            "unicode_property",
            "modifiers",
            "control_escape",
            "hex_escape",
            "unicode_escape",
            "named_capture",
            "capturing_group",
            "character_class",
            "alternation",
            "dot",
            "escape",
        ],
    )
    return f"add local exact compile/parser case for missing selector {primary}"


def plan_row(
    row: dict[str, str],
    requirement_rows: dict[str, dict[str, str]],
) -> dict[str, str]:
    requirement = requirement_rows.get(row["requirement_id"])
    tags = split_csv_set(row["selector_tags"])
    family = local_case_family(row)
    case_id = f"local-exact:{row['requirement_id']}:{safe_id(family)}"
    expected_behavior = "compile_ok"

    return {
        "plan_id": f"local-exact-plan:{row['requirement_id']}",
        "requirement_id": row["requirement_id"],
        "clause_id": "" if requirement is None else requirement["clause_id"],
        "clause_title": "" if requirement is None else requirement["clause_title"],
        "source_file": "" if requirement is None else requirement["source_file"],
        "section_anchor": "" if requirement is None else requirement["section_anchor"],
        "requirement_kind": "" if requirement is None else requirement["requirement_kind"],
        "mapping_family": row["mapping_family"],
        "executable_layer": row["executable_layer"],
        "selector_tags": ",".join(sorted(tags)),
        "missing_selector_tags": row["missing_selector_tags"],
        "local_case_family": family,
        "local_case_id": case_id,
        "planned_pattern": planned_pattern(row),
        "planned_flags": planned_flags(tags),
        "expected_behavior": expected_behavior,
        "coverage_credit": "none_local_exact_planned",
        "plan_state": "planned_not_executable",
        "target_test_artifact": "test/test_ecma262_local_exact_compile_parser.ml",
        "spec_reason": spec_reason(row, requirement),
        "implementation_pressure": implementation_pressure(row),
        "next_action": "materialize_local_exact_case",
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--cache", default="cache")
    parser.add_argument(
        "--selector-gap-worklist",
        default="cache/ecma262-regexp-selector-gap-worklist.tsv",
    )
    parser.add_argument(
        "--requirement-matrix",
        default="cache/ecma262-regexp-requirement-matrix.tsv",
    )
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--allow-empty-output-overwrite", action="store_true")
    args = parser.parse_args()

    cache = Path(args.cache)
    selector_gap_worklist = Path(args.selector_gap_worklist)
    requirement_matrix = Path(args.requirement_matrix)
    detail = cache / DETAIL_NAME
    summary = cache / SUMMARY_NAME

    if not selector_gap_worklist.is_file():
        raise SystemExit(
            f"missing selector-gap worklist at {selector_gap_worklist}; "
            "run tools/build_ecma262_regexp_selector_gap_worklist.py first"
        )
    if not requirement_matrix.is_file():
        raise SystemExit(
            f"missing requirement matrix at {requirement_matrix}; "
            "run tools/build_ecma262_regexp_requirement_matrix.py first"
        )

    selector_fields, selector_rows = read_tsv(selector_gap_worklist)
    requirement_fields, requirement_rows_list = read_tsv(requirement_matrix)

    required_selector = {
        "requirement_id",
        "mapping_family",
        "executable_layer",
        "selector_tags",
        "missing_selector_tags",
        "selector_gap_state",
    }
    missing_selector = required_selector.difference(selector_fields)
    if missing_selector:
        raise SystemExit(
            "missing required selector-gap columns: "
            + ", ".join(sorted(missing_selector))
        )

    required_requirement = {
        "requirement_id",
        "clause_id",
        "clause_title",
        "source_file",
        "section_anchor",
        "requirement_kind",
        "requirement_text",
    }
    missing_requirement = required_requirement.difference(requirement_fields)
    if missing_requirement:
        raise SystemExit(
            "missing required requirement-worklist columns: "
            + ", ".join(sorted(missing_requirement))
        )

    requirement_rows = {
        row["requirement_id"]: row
        for row in requirement_rows_list
    }

    local_required_rows = [
        row
        for row in selector_rows
        if row["selector_gap_state"] == "local_exact_test_required"
    ]
    rows = [plan_row(row, requirement_rows) for row in local_required_rows]
    validate_unique_ids(rows, fields=("plan_id",))

    family_counts = Counter(row["local_case_family"] for row in rows)
    mapping_counts = Counter(row["mapping_family"] for row in rows)
    layer_counts = Counter(row["executable_layer"] for row in rows)
    flag_counts = Counter(row["planned_flags"] if row["planned_flags"] else "<none>" for row in rows)
    state_counts = Counter(row["plan_state"] for row in rows)
    credit_counts = Counter(row["coverage_credit"] for row in rows)
    missing_selector_counts: Counter[str] = Counter()
    source_missing_rows = 0
    for row in rows:
        missing_selector_counts.update(split_csv_set(row["missing_selector_tags"]))
        if not row["source_file"] or not Path(row["source_file"]).is_file():
            source_missing_rows += 1

    summary_lines = [
        "ecma262_snapshot\t2026\n",
        f"input_selector_gap_worklist\t{selector_gap_worklist}\n",
        f"input_requirement_matrix\t{requirement_matrix}\n",
        f"selector_gap_rows\t{len(selector_rows)}\n",
        f"local_exact_plan_rows\t{len(rows)}\n",
        f"source_missing_rows\t{source_missing_rows}\n",
        f"coverage_credit_rows\t0\n",
        f"planned_detail_output\t{detail}\n",
        f"planned_summary_output\t{summary}\n",
        f"dry_run\t{bool_text(args.dry_run)}\n",
    ]
    for name, count in sorted(family_counts.items()):
        summary_lines.append(f"local_case_family_{name}\t{count}\n")
    for name, count in sorted(mapping_counts.items()):
        summary_lines.append(f"mapping_family_{name}\t{count}\n")
    for name, count in sorted(layer_counts.items()):
        summary_lines.append(f"executable_layer_{name}\t{count}\n")
    for name, count in sorted(flag_counts.items()):
        summary_lines.append(f"planned_flags_{name}\t{count}\n")
    for name, count in sorted(state_counts.items()):
        summary_lines.append(f"plan_state_{name}\t{count}\n")
    for name, count in sorted(credit_counts.items()):
        summary_lines.append(f"coverage_credit_{name}\t{count}\n")
    for name, count in sorted(missing_selector_counts.items()):
        summary_lines.append(f"missing_selector_{name}\t{count}\n")

    if args.dry_run:
        print("".join(summary_lines), end="")
        return

    existing_rows = existing_data_rows(detail)
    if not rows and existing_rows > 0 and not args.allow_empty_output_overwrite:
        raise SystemExit(
            f"refusing to overwrite non-empty local exact plan {detail} "
            f"({existing_rows} rows) with an empty output from current "
            "selector-gap worklist; pass --allow-empty-output-overwrite only "
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
        "mapping_family",
        "executable_layer",
        "selector_tags",
        "missing_selector_tags",
        "local_case_family",
        "local_case_id",
        "planned_pattern",
        "planned_flags",
        "expected_behavior",
        "coverage_credit",
        "plan_state",
        "target_test_artifact",
        "spec_reason",
        "implementation_pressure",
        "next_action",
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
