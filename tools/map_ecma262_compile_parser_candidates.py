#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import hashlib
import re
from collections import Counter
from pathlib import Path

from ecma262_tooling import bool_text, read_tsv, split_csv_set


DETAIL_NAME = "ecma262-regexp-compile-parser-candidate-map.tsv"
FEATURES_NAME = "ecma262-regexp-compile-case-features.tsv"
SUMMARY_NAME = "ecma262-regexp-compile-parser-candidate-map.summary"
SELECTION_DETAIL_NAME = "ecma262-regexp-compile-parser-test-selection.tsv"
SELECTION_SUMMARY_NAME = "ecma262-regexp-compile-parser-test-selection.summary"

GENERIC_SELECTORS = {
    "accepted_literal",
}


def contains_unescaped(pattern: str, needle: str) -> bool:
    escaped = False
    for char in pattern:
        if escaped:
            escaped = False
            continue
        if char == "\\":
            escaped = True
            continue
        if char == needle:
            return True
    return False


def named_capture_names(pattern: str) -> list[str]:
    return re.findall(r"\(\?<([A-Za-z_$][A-Za-z0-9_$]*)>", pattern)


def feature_tags(row: dict[str, str]) -> list[str]:
    pattern = row["pattern"]
    flags = row["flags"]
    tags = {"accepted_literal", "compile_positive"}

    if flags:
        tags.add("flagged")
        for flag in flags:
            tags.add(f"flag_{flag}")
    else:
        tags.add("no_flags")

    if "i" in flags:
        tags.add("ignore_case")
    if "u" in flags:
        tags.add("unicode_mode")
    if "v" in flags:
        tags.add("unicode_sets_mode")
    if "g" in flags:
        tags.add("global")
    if "y" in flags:
        tags.add("sticky")
    if "m" in flags:
        tags.add("multiline")
    if "s" in flags:
        tags.add("dot_all")
    if "d" in flags:
        tags.add("has_indices")

    names = named_capture_names(pattern)
    if names:
        tags.add("capturing_group")
        tags.add("named_capture")
    if len(names) != len(set(names)):
        tags.add("duplicate_named_capture")
    if re.search(r"\((?!\?[<:=!])", pattern):
        tags.add("capturing_group")
    if "(?:" in pattern:
        tags.add("noncapturing_group")
    if "\\k<" in pattern:
        tags.add("backreference")
        tags.add("named_backreference")
    if re.search(r"\\[1-9]", pattern):
        tags.add("backreference")
        tags.add("numeric_backreference")
    if contains_unescaped(pattern, "|"):
        tags.add("alternation")
    if re.search(r"(?<!\\)([*+?]|\{[0-9,]+\})", pattern):
        tags.add("quantifier")
    if "[" in pattern:
        tags.add("character_class")
    if re.search(r"\[[^\]\n]*-[^\]\n]*\]", pattern):
        tags.add("class_range")
    if contains_unescaped(pattern, "."):
        tags.add("dot")
    if "\\" in pattern:
        tags.add("escape")
    if "\\u" in pattern:
        tags.add("unicode_escape")
    if "\\x" in pattern:
        tags.add("hex_escape")
    if "\\c" in pattern:
        tags.add("control_escape")
    if "\\p{" in pattern or "\\P{" in pattern:
        tags.add("unicode_property")
    if re.search(r"\\[dDsSwW]", pattern):
        tags.add("character_class_escape")
    if "(?=" in pattern or "(?!" in pattern:
        tags.add("lookahead")
        tags.add("assertion")
    if "(?<=" in pattern or "(?<!" in pattern:
        tags.add("lookbehind")
        tags.add("assertion")
    if contains_unescaped(pattern, "^") or contains_unescaped(pattern, "$"):
        tags.add("anchor_assertion")
        tags.add("assertion")
    if "\\b" in pattern or "\\B" in pattern:
        tags.add("word_boundary")
        tags.add("assertion")
    if re.search(r"\(\?[ims-]", pattern):
        tags.add("modifiers")
    if "&&" in pattern or "--" in pattern:
        tags.add("unicode_sets")
    if "annexB" in row["source_path"] or "annex-b" in row["source_path"].lower():
        tags.add("annex_b")

    return sorted(tags)


def case_id(row: dict[str, str]) -> str:
    digest = hashlib.sha1(
        "\t".join(
            [
                row["source_path"],
                row["line"],
                row["pattern"],
                row["flags"],
                row["raw"],
            ]
        ).encode("utf-8")
    ).hexdigest()[:12]
    return f"test262-compile:{row['source_path']}:{row['line']}:{digest}"


def selectors_for(row: dict[str, str]) -> set[str]:
    semantic = row["semantic_family"]
    text = f"{row['requirement_text']} {row['requirement_local_id']}".lower()
    routes = {part for part in row["coverage_routes"].split(",") if part}
    selectors: set[str] = set()

    if "test262_positive_compile" in routes:
        selectors.add("accepted_literal")
    if "test262_flags" in routes or semantic == "flags" or "flag" in text:
        selectors.add("flagged")
    if semantic in {"captures", "creation"} or "capture" in text:
        selectors.update({"capturing_group", "named_capture"})
    if "groupname" in text or "group specifier" in text:
        selectors.add("named_capture")
    if semantic == "unicode_sets" or "unicode sets" in text:
        selectors.update({"unicode_sets", "unicode_sets_mode", "unicode_property"})
    if semantic in {"escapes", "escapes_grammar"} or "escape" in text:
        selectors.update({"escape", "unicode_escape", "hex_escape", "control_escape"})
    if "unicode" in semantic or "unicode" in text:
        selectors.update({"unicode_mode", "unicode_escape", "unicode_property"})
    if "class" in semantic or "class" in text:
        selectors.add("character_class")
    if "range" in text:
        selectors.add("class_range")
    if "backreference" in text:
        selectors.update({"backreference", "named_backreference"})
    if "alternative" in text or "disjunction" in text or semantic == "pattern_grammar":
        selectors.add("alternation")
    if "quantifier" in text:
        selectors.add("quantifier")
    if "assertion" in text:
        selectors.add("assertion")
    if "atom" in text:
        selectors.update({"dot", "character_class", "capturing_group", "escape"})
    if semantic == "modifiers" or "modifier" in text:
        selectors.add("modifiers")
    if semantic == "syntax_early_errors":
        selectors.add("negative_syntax_needed")
    if semantic == "regexp_literal_expression":
        selectors.add("accepted_literal")

    return selectors


def candidate_state(
    row: dict[str, str],
    selectors: set[str],
    matches: list[dict[str, str]],
) -> tuple[str, str]:
    routes = {part for part in row["coverage_routes"].split(",") if part}
    if "negative_syntax_needed" in selectors and "test262_positive_compile" not in routes:
        return (
            "needs_negative_or_local_exact_case",
            "requirement is negative-syntax oriented; accepted compile cases are not enough",
        )
    if matches:
        return (
            "candidate_compile_cases_found",
            "compile-positive corpus has candidate cases; exact requirement-to-test selection is still open",
        )
    if "test262_positive_compile" in routes:
        return (
            "no_compile_candidate_found",
            "requirement expects positive compile evidence but no current compile case matched the selectors",
        )
    return (
        "needs_local_exact_case",
        "requirement has no suitable compile-positive corpus route and needs local exact case selection",
    )


def line_number(row: dict[str, str]) -> int:
    try:
        return int(row["line"])
    except ValueError:
        return 0


def selection_tags(row: dict[str, str]) -> set[str]:
    selectors = split_csv_set(row["candidate_selector_tags"])
    selectors.discard("negative_syntax_needed")
    if not selectors:
        selectors.add("accepted_literal")
    return selectors


def score_case(
    selectors: set[str],
    case: dict[str, str],
) -> tuple[int, int, int, str, int, str]:
    features = split_csv_set(case["feature_tags"])
    specific_selectors = selectors.difference(GENERIC_SELECTORS)
    matched_specific = len(specific_selectors.intersection(features))
    matched_all = len(selectors.intersection(features))
    extra_features = len(features.difference(selectors))
    return (
        -matched_specific,
        -matched_all,
        extra_features,
        case["source_path"],
        line_number(case),
        case["case_id"],
    )


def select_case(
    row: dict[str, str],
    feature_rows: list[dict[str, str]],
) -> dict[str, str] | None:
    selectors = selection_tags(row)
    matches = [
        case
        for case in feature_rows
        if selectors.intersection(split_csv_set(case["feature_tags"]))
    ]
    if not matches:
        return None
    return sorted(matches, key=lambda case: score_case(selectors, case))[0]


def selection_row(
    row: dict[str, str],
    feature_rows: list[dict[str, str]],
) -> dict[str, str]:
    state = row["compile_candidate_state"]
    if state != "candidate_compile_cases_found":
        return {
            **row,
            "selection_state": state,
            "selected_case_id": "",
            "selected_case_source": "",
            "selected_pattern": "",
            "selected_flags": "",
            "selected_raw": "",
            "selected_feature_tags": "",
            "selected_matched_selector_tags": "",
            "selected_missing_selector_tags": "",
            "selected_expected_behavior": "compile_error_or_local_exact_needed",
            "selection_exactness": "no_positive_exact_selection",
            "selection_reason": "row is negative/local-exact oriented; accepted compile-positive cases must not be treated as exact coverage",
        }

    selected = select_case(row, feature_rows)
    if selected is None:
        return {
            **row,
            "selection_state": "open_no_selected_case",
            "selected_case_id": "",
            "selected_case_source": "",
            "selected_pattern": "",
            "selected_flags": "",
            "selected_raw": "",
            "selected_feature_tags": "",
            "selected_matched_selector_tags": "",
            "selected_missing_selector_tags": "",
            "selected_expected_behavior": "compile_ok_candidate_needed",
            "selection_exactness": "no_positive_exact_selection",
            "selection_reason": "candidate state said compile cases exist, but no case matched selectors during deterministic selection",
        }

    selectors = selection_tags(row)
    features = split_csv_set(selected["feature_tags"])
    matched = sorted(selectors.intersection(features))
    missing_selectors = sorted(selectors.difference(features))
    return {
        **row,
        "selection_state": "selected_compile_positive_case",
        "selected_case_id": selected["case_id"],
        "selected_case_source": f"{selected['source_path']}:{selected['line']}",
        "selected_pattern": selected["pattern"],
        "selected_flags": selected["flags"],
        "selected_raw": selected["raw"],
        "selected_feature_tags": selected["feature_tags"],
        "selected_matched_selector_tags": ",".join(matched),
        "selected_missing_selector_tags": ",".join(missing_selectors),
        "selected_expected_behavior": "compile_ok",
        "selection_exactness": "selected_candidate_not_coverage",
        "selection_reason": "deterministic compile-positive case selected from candidate evidence; ledger coverage remains open until tests are generated and green",
    }


def build_selection_rows(
    candidate_rows: list[dict[str, str]],
    feature_rows: list[dict[str, str]],
) -> list[dict[str, str]]:
    return [selection_row(row, feature_rows) for row in candidate_rows]


def selection_summary_lines(
    candidate_rows: list[dict[str, str]],
    selection_rows: list[dict[str, str]],
    candidate_map: Path,
    compile_case_features: Path,
    detail: Path,
    summary: Path,
    dry_run: bool,
) -> list[str]:
    state_counts = Counter(row["selection_state"] for row in selection_rows)
    exactness_counts = Counter(row["selection_exactness"] for row in selection_rows)
    expected_counts = Counter(row["selected_expected_behavior"] for row in selection_rows)
    layer_counts = Counter(row["executable_layer"] for row in selection_rows)
    family_counts = Counter(row["mapping_family"] for row in selection_rows)
    selected_case_counts = Counter(
        row["selected_case_id"] for row in selection_rows if row["selected_case_id"]
    )
    selected_unique_cases = len(selected_case_counts)
    selected_rows = state_counts.get("selected_compile_positive_case", 0)
    no_positive_rows = len(selection_rows) - selected_rows

    lines = [
        "ecma262_snapshot\t2026\n",
        f"input_candidate_map\t{candidate_map}\n",
        f"input_compile_case_features\t{compile_case_features}\n",
        f"candidate_map_rows\t{len(candidate_rows)}\n",
        f"selection_rows\t{len(selection_rows)}\n",
        f"selected_compile_positive_rows\t{selected_rows}\n",
        f"no_positive_selection_rows\t{no_positive_rows}\n",
        f"selected_unique_compile_cases\t{selected_unique_cases}\n",
        "covered_rows\t0\n",
        f"planned_detail_output\t{detail}\n",
        f"planned_summary_output\t{summary}\n",
        f"dry_run\t{bool_text(dry_run)}\n",
    ]
    for name, count in sorted(state_counts.items()):
        lines.append(f"selection_state_{name}\t{count}\n")
    for name, count in sorted(exactness_counts.items()):
        lines.append(f"selection_exactness_{name}\t{count}\n")
    for name, count in sorted(expected_counts.items()):
        lines.append(f"expected_behavior_{name}\t{count}\n")
    for name, count in sorted(layer_counts.items()):
        lines.append(f"executable_layer_{name}\t{count}\n")
    for name, count in sorted(family_counts.items()):
        lines.append(f"mapping_family_{name}\t{count}\n")
    for case_id, count in selected_case_counts.most_common(20):
        lines.append(f"selected_case_reuse_{case_id}\t{count}\n")
    return lines


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--cache", default="cache")
    parser.add_argument(
        "--worklist",
        default="cache/ecma262-regexp-requirement-test-worklist.tsv",
    )
    parser.add_argument(
        "--compile-cases",
        default="cache/test262-regexp-core-compile-cases.tsv",
    )
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    cache = Path(args.cache)
    worklist_path = Path(args.worklist)
    compile_cases_path = Path(args.compile_cases)
    detail = cache / DETAIL_NAME
    features_detail = cache / FEATURES_NAME
    summary = cache / SUMMARY_NAME
    selection_detail = cache / SELECTION_DETAIL_NAME
    selection_summary = cache / SELECTION_SUMMARY_NAME

    if not worklist_path.is_file():
        raise SystemExit(
            f"missing requirement-test worklist at {worklist_path}; "
            "run tools/map_ecma262_requirements_to_tests.py first"
        )
    if not compile_cases_path.is_file():
        raise SystemExit(
            f"missing compile cases at {compile_cases_path}; "
            "run tools/extract_test262_regexp_core.py first"
        )

    input_fieldnames, worklist_rows = read_tsv(worklist_path)
    _, compile_cases = read_tsv(compile_cases_path)

    compile_parser_rows = [
        row
        for row in worklist_rows
        if row["executable_layer"] in {"compile", "parser"}
    ]

    feature_rows = []
    for row in compile_cases:
        tags = feature_tags(row)
        feature_rows.append(
            {
                **row,
                "case_id": case_id(row),
                "feature_tags": ",".join(tags),
            }
        )

    candidate_rows = []
    for row in compile_parser_rows:
        selectors = selectors_for(row)
        negative_only = selectors == {"negative_syntax_needed"}
        searchable_selectors = {
            selector for selector in selectors if selector != "negative_syntax_needed"
        }
        if not searchable_selectors and not negative_only:
            searchable_selectors = {"accepted_literal"}

        matches = []
        for case in feature_rows:
            case_tags = {part for part in case["feature_tags"].split(",") if part}
            if searchable_selectors.intersection(case_tags):
                matches.append(case)

        state, reason = candidate_state(row, selectors, matches)
        sample = matches[:12]
        candidate_rows.append(
            {
                **row,
                "candidate_selector_tags": ",".join(sorted(selectors)),
                "compile_candidate_state": state,
                "compile_candidate_count": str(len(matches)),
                "compile_candidate_case_ids_sample": "|".join(
                    case["case_id"] for case in sample
                ),
                "compile_candidate_sources_sample": "|".join(
                    f"{case['source_path']}:{case['line']}" for case in sample
                ),
                "compile_candidate_reason": reason,
                    "candidate_exactness": "candidate_only_not_exact",
                }
            )

    selection_rows = build_selection_rows(candidate_rows, feature_rows)

    state_counts = Counter(row["compile_candidate_state"] for row in candidate_rows)
    exactness_counts = Counter(row["candidate_exactness"] for row in candidate_rows)
    layer_counts = Counter(row["executable_layer"] for row in candidate_rows)
    family_counts = Counter(row["mapping_family"] for row in candidate_rows)
    semantic_counts = Counter(row["semantic_family"] for row in candidate_rows)
    selector_counts: Counter[str] = Counter()
    for row in candidate_rows:
        selector_counts.update(
            part for part in row["candidate_selector_tags"].split(",") if part
        )
    feature_counts: Counter[str] = Counter()
    for row in feature_rows:
        feature_counts.update(part for part in row["feature_tags"].split(",") if part)

    rows_with_candidates = sum(
        1 for row in candidate_rows if int(row["compile_candidate_count"]) > 0
    )
    total_candidate_links = sum(
        int(row["compile_candidate_count"]) for row in candidate_rows
    )

    summary_lines = [
        "ecma262_snapshot\t2026\n",
        f"input_worklist\t{worklist_path}\n",
        f"input_compile_cases\t{compile_cases_path}\n",
        f"input_worklist_rows\t{len(worklist_rows)}\n",
        f"compile_parser_worklist_rows\t{len(compile_parser_rows)}\n",
        f"compile_case_rows\t{len(feature_rows)}\n",
        f"candidate_map_rows\t{len(candidate_rows)}\n",
        "exact_mapped_rows\t0\n",
        f"rows_with_compile_candidates\t{rows_with_candidates}\n",
        f"rows_without_compile_candidates\t{len(candidate_rows) - rows_with_candidates}\n",
        f"total_candidate_links\t{total_candidate_links}\n",
        f"planned_detail_output\t{detail}\n",
        f"planned_feature_output\t{features_detail}\n",
        f"planned_summary_output\t{summary}\n",
        f"planned_selection_detail_output\t{selection_detail}\n",
        f"planned_selection_summary_output\t{selection_summary}\n",
        f"selection_rows\t{len(selection_rows)}\n",
        f"dry_run\t{bool_text(args.dry_run)}\n",
    ]
    for name, count in sorted(state_counts.items()):
        summary_lines.append(f"compile_candidate_state_{name}\t{count}\n")
    for name, count in sorted(exactness_counts.items()):
        summary_lines.append(f"candidate_exactness_{name}\t{count}\n")
    for name, count in sorted(layer_counts.items()):
        summary_lines.append(f"executable_layer_{name}\t{count}\n")
    for name, count in sorted(family_counts.items()):
        summary_lines.append(f"mapping_family_{name}\t{count}\n")
    for name, count in sorted(semantic_counts.items()):
        summary_lines.append(f"semantic_family_{name}\t{count}\n")
    for name, count in sorted(selector_counts.items()):
        summary_lines.append(f"selector_{name}\t{count}\n")
    for name, count in sorted(feature_counts.items()):
        summary_lines.append(f"compile_case_feature_{name}\t{count}\n")

    if args.dry_run:
        print("".join(summary_lines), end="")
        print(
            "".join(
                selection_summary_lines(
                    candidate_rows,
                    selection_rows,
                    detail,
                    features_detail,
                    selection_detail,
                    selection_summary,
                    args.dry_run,
                )
            ),
            end="",
        )
        return

    cache.mkdir(parents=True, exist_ok=True)
    feature_fieldnames = [
        "case_id",
        "source_path",
        "line",
        "source_kind",
        "pattern",
        "flags",
        "raw",
        "feature_tags",
    ]
    with features_detail.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, delimiter="\t", fieldnames=feature_fieldnames)
        writer.writeheader()
        writer.writerows(feature_rows)

    candidate_fieldnames = [
        *input_fieldnames,
        "candidate_selector_tags",
        "compile_candidate_state",
        "compile_candidate_count",
        "compile_candidate_case_ids_sample",
        "compile_candidate_sources_sample",
        "compile_candidate_reason",
        "candidate_exactness",
    ]
    with detail.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, delimiter="\t", fieldnames=candidate_fieldnames)
        writer.writeheader()
        writer.writerows(candidate_rows)
    with summary.open("w", encoding="utf-8") as f:
        f.write("".join(summary_lines))
    selection_fieldnames = [
        *candidate_fieldnames,
        "selection_state",
        "selected_case_id",
        "selected_case_source",
        "selected_pattern",
        "selected_flags",
        "selected_raw",
        "selected_feature_tags",
        "selected_matched_selector_tags",
        "selected_missing_selector_tags",
        "selected_expected_behavior",
        "selection_exactness",
        "selection_reason",
    ]
    with selection_detail.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, delimiter="\t", fieldnames=selection_fieldnames)
        writer.writeheader()
        writer.writerows(selection_rows)
    with selection_summary.open("w", encoding="utf-8") as f:
        f.write(
            "".join(
                selection_summary_lines(
                    candidate_rows,
                    selection_rows,
                    detail,
                    features_detail,
                    selection_detail,
                    selection_summary,
                    args.dry_run,
                )
            )
        )
    print(summary.read_text(encoding="utf-8"), end="")
    print(selection_summary.read_text(encoding="utf-8"), end="")


if __name__ == "__main__":
    main()
