#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
from collections import Counter
from pathlib import Path

from ecma262_tooling import bool_text, read_tsv, split_csv_set, validate_unique_ids


DETAIL_NAME = "ecma262-regexp-selector-gap-worklist.tsv"
SUMMARY_NAME = "ecma262-regexp-selector-gap-worklist.summary"


GENERIC_SELECTORS = {
    "accepted_literal",
}


def line_number(row: dict[str, str]) -> int:
    try:
        return int(row["line"])
    except ValueError:
        return 0


def score_exact_case(selectors: set[str], case: dict[str, str]) -> tuple[int, int, str, int, str]:
    features = split_csv_set(case["feature_tags"])
    specific_selectors = selectors.difference(GENERIC_SELECTORS)
    extra_features = len(features.difference(selectors))
    return (
        extra_features,
        -len(specific_selectors.intersection(features)),
        case["source_path"],
        line_number(case),
        case["case_id"],
    )


def exact_candidates(selectors: set[str], feature_rows: list[dict[str, str]]) -> list[dict[str, str]]:
    return [
        case
        for case in feature_rows
        if selectors.issubset(split_csv_set(case["feature_tags"]))
    ]


def source_of(case: dict[str, str]) -> str:
    return f"{case['source_path']}:{case['line']}"


def worklist_row(
    audit_row: dict[str, str],
    feature_rows: list[dict[str, str]],
) -> dict[str, str]:
    selectors = split_csv_set(audit_row["selector_tags"])
    missing_selectors = split_csv_set(audit_row["selected_missing_selector_tags"])
    candidates = exact_candidates(selectors, feature_rows)
    selected = sorted(candidates, key=lambda case: score_exact_case(selectors, case))

    if selected:
        best = selected[0]
        state = "selector_complete_compile_case_available"
        next_action = "promote_selector_complete_case_into_selection"
        reason = "an existing compile-positive corpus case contains every selector required by the requirement row"
        best_case_id = best["case_id"]
        best_case_source = source_of(best)
        best_pattern = best["pattern"]
        best_flags = best["flags"]
        best_feature_tags = best["feature_tags"]
    else:
        state = "local_exact_test_required"
        next_action = "add_local_exact_compile_or_parser_test"
        reason = "no current compile-positive corpus case contains every selector required by the requirement row"
        best_case_id = ""
        best_case_source = ""
        best_pattern = ""
        best_flags = ""
        best_feature_tags = ""

    return {
        "worklist_id": f"selector-gap:{audit_row['requirement_id']}",
        "requirement_id": audit_row["requirement_id"],
        "mapping_family": audit_row["mapping_family"],
        "executable_layer": audit_row["executable_layer"],
        "current_case_id": audit_row["case_id"],
        "current_case_source": audit_row["case_source"],
        "selector_tags": ",".join(sorted(selectors)),
        "missing_selector_tags": ",".join(sorted(missing_selectors)),
        "current_feature_tags": audit_row["selected_feature_tags"],
        "exact_candidate_count": str(len(candidates)),
        "best_case_id": best_case_id,
        "best_case_source": best_case_source,
        "best_pattern": best_pattern,
        "best_flags": best_flags,
        "best_feature_tags": best_feature_tags,
        "selector_gap_state": state,
        "next_action": next_action,
        "worklist_reason": reason,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--cache", default="cache")
    parser.add_argument(
        "--exactness-audit",
        default="cache/ecma262-regexp-exactness-audit.tsv",
    )
    parser.add_argument(
        "--compile-case-features",
        default="cache/ecma262-regexp-compile-case-features.tsv",
    )
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    cache = Path(args.cache)
    exactness_audit = Path(args.exactness_audit)
    compile_case_features = Path(args.compile_case_features)
    detail = cache / DETAIL_NAME
    summary = cache / SUMMARY_NAME

    if not exactness_audit.is_file():
        raise SystemExit(
            f"missing exactness audit at {exactness_audit}; "
            "run tools/build_ecma262_regexp_exactness_audit.py first"
        )
    if not compile_case_features.is_file():
        raise SystemExit(
            f"missing compile case features at {compile_case_features}; "
            "run tools/map_ecma262_compile_parser_candidates.py first"
        )

    audit_fields, audit_rows = read_tsv(exactness_audit)
    feature_fields, feature_rows = read_tsv(compile_case_features)

    required_audit = {
        "requirement_id",
        "mapping_family",
        "executable_layer",
        "case_id",
        "case_source",
        "selector_tags",
        "selected_feature_tags",
        "selected_missing_selector_tags",
        "exactness_audit_state",
    }
    missing_audit = required_audit.difference(audit_fields)
    if missing_audit:
        raise SystemExit(
            "missing required exactness-audit columns: "
            + ", ".join(sorted(missing_audit))
        )

    required_features = {
        "case_id",
        "source_path",
        "line",
        "pattern",
        "flags",
        "feature_tags",
    }
    missing_features = required_features.difference(feature_fields)
    if missing_features:
        raise SystemExit(
            "missing required compile-case feature columns: "
            + ", ".join(sorted(missing_features))
        )

    gap_rows = [
        row
        for row in audit_rows
        if row["exactness_audit_state"] == "open_missing_selector_coverage"
    ]
    rows = [worklist_row(row, feature_rows) for row in gap_rows]
    validate_unique_ids(rows, fields=("worklist_id",))

    state_counts = Counter(row["selector_gap_state"] for row in rows)
    action_counts = Counter(row["next_action"] for row in rows)
    family_counts = Counter(row["mapping_family"] for row in rows)
    layer_counts = Counter(row["executable_layer"] for row in rows)
    missing_selector_counts: Counter[str] = Counter()
    for row in rows:
        missing_selector_counts.update(split_csv_set(row["missing_selector_tags"]))

    exact_available_rows = state_counts.get("selector_complete_compile_case_available", 0)
    local_required_rows = state_counts.get("local_exact_test_required", 0)

    summary_lines = [
        "ecma262_snapshot\t2026\n",
        f"input_exactness_audit\t{exactness_audit}\n",
        f"input_compile_case_features\t{compile_case_features}\n",
        f"exactness_audit_rows\t{len(audit_rows)}\n",
        f"compile_case_feature_rows\t{len(feature_rows)}\n",
        f"selector_gap_rows\t{len(rows)}\n",
        f"selector_complete_case_available_rows\t{exact_available_rows}\n",
        f"local_exact_test_required_rows\t{local_required_rows}\n",
        f"planned_detail_output\t{detail}\n",
        f"planned_summary_output\t{summary}\n",
        f"dry_run\t{bool_text(args.dry_run)}\n",
    ]
    for name, count in sorted(state_counts.items()):
        summary_lines.append(f"selector_gap_state_{name}\t{count}\n")
    for name, count in sorted(action_counts.items()):
        summary_lines.append(f"next_action_{name}\t{count}\n")
    for name, count in sorted(family_counts.items()):
        summary_lines.append(f"mapping_family_{name}\t{count}\n")
    for name, count in sorted(layer_counts.items()):
        summary_lines.append(f"executable_layer_{name}\t{count}\n")
    for name, count in sorted(missing_selector_counts.items()):
        summary_lines.append(f"missing_selector_{name}\t{count}\n")

    if args.dry_run:
        print("".join(summary_lines), end="")
        return

    cache.mkdir(parents=True, exist_ok=True)
    fieldnames = [
        "worklist_id",
        "requirement_id",
        "mapping_family",
        "executable_layer",
        "current_case_id",
        "current_case_source",
        "selector_tags",
        "missing_selector_tags",
        "current_feature_tags",
        "exact_candidate_count",
        "best_case_id",
        "best_case_source",
        "best_pattern",
        "best_flags",
        "best_feature_tags",
        "selector_gap_state",
        "next_action",
        "worklist_reason",
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
