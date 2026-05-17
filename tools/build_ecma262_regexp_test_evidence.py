#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import hashlib
from collections import Counter
from pathlib import Path

from ecma262_tooling import bool_text, read_tsv, validate_unique_ids


DETAIL_NAME = "ecma262-regexp-test-evidence.tsv"
SUMMARY_NAME = "ecma262-regexp-test-evidence.summary"


def short_hash(*parts: str) -> str:
    digest = hashlib.sha256("\0".join(parts).encode("utf-8")).hexdigest()
    return digest[:12]


def negative_case_id(row: dict[str, str]) -> str:
    return "test262-negative:{source}:{line}:{digest}".format(
        source=row["source_path"],
        line=row["line"],
        digest=short_hash(
            row["source_path"],
            row["line"],
            row["source_kind"],
            row["pattern"],
            row["flags"],
            row["raw"],
        ),
    )


def selected_positive_evidence(row: dict[str, str]) -> dict[str, str]:
    case_id = row["selected_case_id"]
    return {
        "evidence_id": f"evidence:{row['requirement_id']}:{case_id}",
        "evidence_scope": "ecma262_requirement",
        "evidence_kind": "selected_compile_positive_case",
        "requirement_id": row["requirement_id"],
        "requirement_link_state": "linked_to_requirement_candidate",
        "coverage_credit": "none_candidate_not_exact",
        "executable_layer": row["executable_layer"],
        "test_artifact": row["primary_test_artifact"],
        "corpus_artifact": "cache/test262-regexp-core-compile-cases.tsv",
        "case_id": case_id,
        "case_source": row["selected_case_source"],
        "source_kind": "literal",
        "pattern": row["selected_pattern"],
        "flags": row["selected_flags"],
        "raw": row["selected_raw"],
        "expected_behavior": "compile_ok",
        "evidence_exactness": "candidate_not_coverage",
        "evidence_state": "executable_candidate",
        "evidence_reason": (
            "selected compile-positive test262 case is executable and green, "
            "but it is still candidate evidence until exact requirement proof is made"
        ),
    }


def open_negative_or_local_evidence(row: dict[str, str]) -> dict[str, str]:
    return {
        "evidence_id": f"evidence:{row['requirement_id']}:open-negative-or-local",
        "evidence_scope": "ecma262_requirement",
        "evidence_kind": "open_negative_or_local_exact_mapping",
        "requirement_id": row["requirement_id"],
        "requirement_link_state": "linked_requirement_without_case",
        "coverage_credit": "none_no_executable_case",
        "executable_layer": row["executable_layer"],
        "test_artifact": row["primary_test_artifact"],
        "corpus_artifact": "",
        "case_id": "",
        "case_source": "",
        "source_kind": "",
        "pattern": "",
        "flags": "",
        "raw": "",
        "expected_behavior": "compile_error_or_local_exact_needed",
        "evidence_exactness": "no_executable_case_selected",
        "evidence_state": "open_mapping_missing_case",
        "evidence_reason": (
            "requirement is negative/local-exact oriented; no concrete "
            "requirement-level executable case is selected yet"
        ),
    }


def negative_syntax_evidence(row: dict[str, str]) -> dict[str, str]:
    case_id = negative_case_id(row)
    return {
        "evidence_id": f"evidence:{case_id}",
        "evidence_scope": "test262_negative_syntax_corpus",
        "evidence_kind": "unmapped_negative_syntax_case",
        "requirement_id": "",
        "requirement_link_state": "unmapped_to_requirement",
        "coverage_credit": "none_unmapped_corpus",
        "executable_layer": "compile",
        "test_artifact": "test/test_test262_negative_syntax.ml",
        "corpus_artifact": "cache/test262-regexp-negative-syntax-cases.tsv",
        "case_id": case_id,
        "case_source": f"{row['source_path']}:{row['line']}",
        "source_kind": row["source_kind"],
        "pattern": row["pattern"],
        "flags": row["flags"],
        "raw": row["raw"],
        "expected_behavior": row["expected_behavior"],
        "evidence_exactness": "corpus_case_not_requirement_mapped",
        "evidence_state": "executable_unmapped_corpus_case",
        "evidence_reason": (
            "extracted negative test262 syntax case is executable and green, "
            "but it has not been mapped to a concrete ECMA-262 requirement row"
        ),
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--cache", default="cache")
    parser.add_argument(
        "--selection",
        default="cache/ecma262-regexp-compile-parser-test-selection.tsv",
    )
    parser.add_argument(
        "--negative-syntax",
        default="cache/test262-regexp-negative-syntax-cases.tsv",
    )
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    cache = Path(args.cache)
    selection = Path(args.selection)
    negative_syntax = Path(args.negative_syntax)
    detail = cache / DETAIL_NAME
    summary = cache / SUMMARY_NAME

    if not selection.is_file():
        raise SystemExit(
            f"missing compile/parser selection at {selection}; "
            "run tools/map_ecma262_compile_parser_candidates.py first"
        )
    if not negative_syntax.is_file():
        raise SystemExit(
            f"missing negative syntax cases at {negative_syntax}; "
            "run tools/extract_test262_regexp_negative_syntax.py first"
        )

    selection_fields, selection_rows = read_tsv(selection)
    negative_fields, negative_rows = read_tsv(negative_syntax)

    required_selection = {
        "requirement_id",
        "selection_state",
        "selected_case_id",
        "selected_case_source",
        "selected_pattern",
        "selected_flags",
        "selected_raw",
        "selected_expected_behavior",
        "executable_layer",
        "primary_test_artifact",
    }
    missing_selection = required_selection.difference(selection_fields)
    if missing_selection:
        raise SystemExit(
            "missing required selection columns: "
            + ", ".join(sorted(missing_selection))
        )

    required_negative = {
        "source_path",
        "line",
        "source_kind",
        "pattern",
        "flags",
        "raw",
        "expected_behavior",
    }
    missing_negative = required_negative.difference(negative_fields)
    if missing_negative:
        raise SystemExit(
            "missing required negative-syntax columns: "
            + ", ".join(sorted(missing_negative))
        )

    rows: list[dict[str, str]] = []
    for row in selection_rows:
        state = row["selection_state"]
        if state == "selected_compile_positive_case":
            rows.append(selected_positive_evidence(row))
        elif state == "needs_negative_or_local_exact_case":
            rows.append(open_negative_or_local_evidence(row))
        else:
            raise SystemExit(
                f"unsupported selection_state {state!r} for {row['requirement_id']}"
            )

    rows.extend(negative_syntax_evidence(row) for row in negative_rows)
    validate_unique_ids(rows, fields=("evidence_id",))

    scope_counts = Counter(row["evidence_scope"] for row in rows)
    kind_counts = Counter(row["evidence_kind"] for row in rows)
    state_counts = Counter(row["evidence_state"] for row in rows)
    credit_counts = Counter(row["coverage_credit"] for row in rows)
    expected_counts = Counter(row["expected_behavior"] for row in rows)
    exactness_counts = Counter(row["evidence_exactness"] for row in rows)
    link_counts = Counter(row["requirement_link_state"] for row in rows)
    artifact_counts = Counter(row["test_artifact"] for row in rows)

    executable_rows = sum(1 for row in rows if row["case_id"])
    requirement_linked_rows = sum(1 for row in rows if row["requirement_id"])
    unmapped_corpus_rows = link_counts.get("unmapped_to_requirement", 0)
    coverage_credit_rows = sum(
        count for credit, count in credit_counts.items() if not credit.startswith("none")
    )

    summary_lines = [
        "ecma262_snapshot\t2026\n",
        f"input_selection\t{selection}\n",
        f"input_negative_syntax\t{negative_syntax}\n",
        f"selection_rows\t{len(selection_rows)}\n",
        f"negative_syntax_rows\t{len(negative_rows)}\n",
        f"evidence_rows\t{len(rows)}\n",
        f"executable_evidence_rows\t{executable_rows}\n",
        f"requirement_linked_rows\t{requirement_linked_rows}\n",
        f"unmapped_corpus_rows\t{unmapped_corpus_rows}\n",
        f"coverage_credit_rows\t{coverage_credit_rows}\n",
        f"planned_detail_output\t{detail}\n",
        f"planned_summary_output\t{summary}\n",
        f"dry_run\t{bool_text(args.dry_run)}\n",
    ]
    for name, count in sorted(scope_counts.items()):
        summary_lines.append(f"evidence_scope_{name}\t{count}\n")
    for name, count in sorted(kind_counts.items()):
        summary_lines.append(f"evidence_kind_{name}\t{count}\n")
    for name, count in sorted(state_counts.items()):
        summary_lines.append(f"evidence_state_{name}\t{count}\n")
    for name, count in sorted(credit_counts.items()):
        summary_lines.append(f"coverage_credit_{name}\t{count}\n")
    for name, count in sorted(expected_counts.items()):
        summary_lines.append(f"expected_behavior_{name}\t{count}\n")
    for name, count in sorted(exactness_counts.items()):
        summary_lines.append(f"evidence_exactness_{name}\t{count}\n")
    for name, count in sorted(link_counts.items()):
        summary_lines.append(f"requirement_link_state_{name}\t{count}\n")
    for name, count in sorted(artifact_counts.items()):
        summary_lines.append(f"test_artifact_{name}\t{count}\n")

    if args.dry_run:
        print("".join(summary_lines), end="")
        return

    cache.mkdir(parents=True, exist_ok=True)
    fieldnames = [
        "evidence_id",
        "evidence_scope",
        "evidence_kind",
        "requirement_id",
        "requirement_link_state",
        "coverage_credit",
        "executable_layer",
        "test_artifact",
        "corpus_artifact",
        "case_id",
        "case_source",
        "source_kind",
        "pattern",
        "flags",
        "raw",
        "expected_behavior",
        "evidence_exactness",
        "evidence_state",
        "evidence_reason",
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
