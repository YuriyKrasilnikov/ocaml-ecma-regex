#!/usr/bin/env python3
from __future__ import annotations

import argparse
import re
from collections import Counter
from dataclasses import dataclass
from pathlib import Path

from ecma262_tooling import bool_text, safe_id, write_tsv


DETAIL_NAME = "raw-utf16-generated-cases.tsv"
SUMMARY_NAME = "raw-utf16-generated-cases.summary"

FIELDNAMES = [
    "case_id",
    "api_route",
    "generator_family",
    "flag_family",
    "input_family",
    "pattern_family",
    "assertion_family",
    "pattern",
    "flags",
    "input_units",
    "initial_last_index",
    "expected_match",
    "expected_start_index",
    "expected_end_index",
    "expected_matched_units",
    "expected_search",
    "expected_last_index",
    "expected_semantics",
]


HIGH = 0xD83D
LOW = 0xDE00


@dataclass(frozen=True)
class InputFamily:
    name: str
    units: tuple[int, ...]


@dataclass(frozen=True)
class Match:
    start: int
    end: int
    units: tuple[int, ...]


def safe_key(value: str) -> str:
    return re.sub(r"[^A-Za-z0-9]+", "_", value).strip("_").lower()


def units_text(units: tuple[int, ...]) -> str:
    return ",".join(f"{unit:04X}" for unit in units)


def unicode_mode(flags: str) -> bool:
    return "u" in flags or "v" in flags


def ignore_case_unicode(flags: str) -> bool:
    return "i" in flags and unicode_mode(flags)


def is_high(unit: int) -> bool:
    return 0xD800 <= unit <= 0xDBFF


def is_low(unit: int) -> bool:
    return 0xDC00 <= unit <= 0xDFFF


def starts_valid_pair(units: tuple[int, ...], index: int) -> bool:
    return (
        index + 1 < len(units)
        and is_high(units[index])
        and is_low(units[index + 1])
    )


def atom_width(units: tuple[int, ...], index: int, flags: str) -> int:
    if unicode_mode(flags) and starts_valid_pair(units, index):
        return 2
    return 1


def search_positions(units: tuple[int, ...], flags: str) -> list[int]:
    positions: list[int] = []
    index = 0
    while index < len(units):
        positions.append(index)
        index += atom_width(units, index, flags)
    return positions


def slice_match(units: tuple[int, ...], start: int, width: int) -> Match:
    return Match(start=start, end=start + width, units=units[start : start + width])


def is_ascii_digit(unit: int) -> bool:
    return 0x30 <= unit <= 0x39


def is_ascii_word(unit: int, flags: str) -> bool:
    if 0x30 <= unit <= 0x39 or 0x41 <= unit <= 0x5A or 0x61 <= unit <= 0x7A:
        return True
    if unit == 0x005F:
        return True
    if ignore_case_unicode(flags) and unit in {0x017F, 0x212A}:
        return True
    return False


def is_ecma_space(unit: int) -> bool:
    return unit in {
        0x0009,
        0x000A,
        0x000B,
        0x000C,
        0x000D,
        0x0020,
        0x00A0,
        0x1680,
        0x2000,
        0x2001,
        0x2002,
        0x2003,
        0x2004,
        0x2005,
        0x2006,
        0x2007,
        0x2008,
        0x2009,
        0x200A,
        0x2028,
        0x2029,
        0x202F,
        0x205F,
        0x3000,
        0xFEFF,
    }


def input_starts_emoji(units: tuple[int, ...], index: int) -> bool:
    # Unicode Binary_Property=Emoji includes ASCII digits for keycap sequences.
    return is_ascii_digit(units[index]) or (
        starts_valid_pair(units, index)
        and units[index] == HIGH
        and units[index + 1] == LOW
    )


def is_ascii_unit(unit: int) -> bool:
    return 0x0000 <= unit <= 0x007F


def category_match(pattern: str, flags: str, units: tuple[int, ...], index: int) -> bool:
    unit = units[index]
    if pattern in {"\\d", "[\\d]"}:
        return is_ascii_digit(unit)
    if pattern in {"\\D", "[\\D]"}:
        return not is_ascii_digit(unit)
    if pattern in {"\\w", "[\\w]"}:
        return is_ascii_word(unit, flags)
    if pattern in {"\\W", "[\\W]"}:
        return not is_ascii_word(unit, flags)
    if pattern in {"\\s", "[\\s]"}:
        return is_ecma_space(unit)
    if pattern in {"\\S", "[\\S]"}:
        return not is_ecma_space(unit)
    raise AssertionError(f"unknown category pattern {pattern}")


def category_expected(pattern: str, flags: str, units: tuple[int, ...]) -> Match | None:
    for index in search_positions(units, flags):
        if category_match(pattern, flags, units, index):
            return slice_match(units, index, atom_width(units, index, flags))
    return None


def property_matches(pattern: str, units: tuple[int, ...], index: int) -> bool:
    positive = "\\p{" in pattern and "\\P{" not in pattern
    if "Emoji" in pattern:
        member = input_starts_emoji(units, index)
    elif "ASCII" in pattern:
        member = is_ascii_unit(units[index])
    else:
        raise AssertionError(f"unknown property pattern {pattern}")
    return member if positive else not member


def property_expected(pattern: str, flags: str, units: tuple[int, ...]) -> Match | None:
    for index in search_positions(units, flags):
        if property_matches(pattern, units, index):
            return slice_match(units, index, atom_width(units, index, flags))
    return None


def literal_target(pattern: str) -> int:
    if "D83D" in pattern:
        return HIGH
    if "DE00" in pattern:
        return LOW
    raise AssertionError(f"unknown surrogate literal pattern {pattern}")


def literal_expected(pattern: str, flags: str, units: tuple[int, ...]) -> Match | None:
    target = literal_target(pattern)
    for index in search_positions(units, flags):
        if units[index] != target:
            continue
        if unicode_mode(flags) and starts_valid_pair(units, index):
            continue
        return slice_match(units, index, 1)
    return None


def boundary_is_word_at(units: tuple[int, ...], index: int, flags: str) -> bool:
    if index < 0 or index >= len(units):
        return False
    return is_ascii_word(units[index], flags)


def boundary_expected(pattern: str, flags: str, units: tuple[int, ...]) -> Match | None:
    for index in search_positions(units, flags):
        left_word = boundary_is_word_at(units, index - 1, flags)
        right_word = boundary_is_word_at(units, index, flags)
        boundary = left_word != right_word
        width = atom_width(units, index, flags)
        if pattern == "\\b\\w":
            if boundary and right_word:
                return slice_match(units, index, width)
        elif pattern == "\\B\\W":
            if (not boundary) and (not right_word):
                return slice_match(units, index, width)
        else:
            raise AssertionError(f"unknown boundary pattern {pattern}")
    return None


def dot_expected(flags: str, units: tuple[int, ...], start: int = 0) -> Match | None:
    if start < 0 or start >= len(units):
        return None
    return slice_match(units, start, atom_width(units, start, flags))


def row(
    *,
    serial: int,
    api_route: str,
    generator_family: str,
    flag_family: str,
    input_family: str,
    pattern_family: str,
    assertion_family: str,
    pattern: str,
    flags: str,
    input_units: tuple[int, ...],
    expected: Match | None,
    expected_search: bool | None = None,
    initial_last_index: int | None = None,
    expected_last_index: int | None = None,
    expected_semantics: str,
) -> dict[str, str]:
    case_id = (
        f"raw-utf16-generated-{serial:04d}-"
        f"{safe_id(api_route)}-{safe_id(generator_family)}-"
        f"{safe_id(flags or 'noflag')}-{safe_id(input_family)}-"
        f"{safe_id(pattern)}"
    )
    return {
        "case_id": case_id,
        "api_route": api_route,
        "generator_family": generator_family,
        "flag_family": flag_family,
        "input_family": input_family,
        "pattern_family": pattern_family,
        "assertion_family": assertion_family,
        "pattern": pattern,
        "flags": flags,
        "input_units": units_text(input_units),
        "initial_last_index": "" if initial_last_index is None else str(initial_last_index),
        "expected_match": bool_text(expected is not None),
        "expected_start_index": "" if expected is None else str(expected.start),
        "expected_end_index": "" if expected is None else str(expected.end),
        "expected_matched_units": "" if expected is None else units_text(expected.units),
        "expected_search": "" if expected_search is None else bool_text(expected_search),
        "expected_last_index": "" if expected_last_index is None else str(expected_last_index),
        "expected_semantics": expected_semantics,
    }


def add_exec_and_search_rows(
    rows: list[dict[str, str]],
    *,
    serial: int,
    generator_family: str,
    flag_family: str,
    input_family: str,
    pattern_family: str,
    assertion_family: str,
    pattern: str,
    flags: str,
    input_units: tuple[int, ...],
    expected: Match | None,
    expected_semantics: str,
) -> int:
    rows.append(
        row(
            serial=serial,
            api_route="exec_js",
            generator_family=generator_family,
            flag_family=flag_family,
            input_family=input_family,
            pattern_family=pattern_family,
            assertion_family=assertion_family,
            pattern=pattern,
            flags=flags,
            input_units=input_units,
            expected=expected,
            expected_semantics=expected_semantics,
        )
    )
    serial += 1
    rows.append(
        row(
            serial=serial,
            api_route="search_js",
            generator_family=generator_family,
            flag_family=flag_family,
            input_family=input_family,
            pattern_family=pattern_family,
            assertion_family="boolean_" + assertion_family,
            pattern=pattern,
            flags=flags,
            input_units=input_units,
            expected=expected,
            expected_search=expected is not None,
            expected_semantics=expected_semantics,
        )
    )
    return serial + 1


def build_rows() -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    serial = 1

    classification_inputs = [
        InputFamily("ascii_a", (0x0041,)),
        InputFamily("digit_5", (0x0035,)),
        InputFamily("underscore", (0x005F,)),
        InputFamily("long_s", (0x017F,)),
        InputFamily("kelvin_sign", (0x212A,)),
        InputFamily("nbsp", (0x00A0,)),
        InputFamily("line_separator", (0x2028,)),
        InputFamily("bom", (0xFEFF,)),
        InputFamily("lone_high_surrogate", (HIGH,)),
        InputFamily("emoji_pair", (HIGH, LOW)),
    ]
    classification_patterns = [
        "\\d",
        "\\D",
        "[\\d]",
        "[\\D]",
        "\\w",
        "\\W",
        "[\\w]",
        "[\\W]",
        "\\s",
        "\\S",
        "[\\s]",
        "[\\S]",
    ]
    classification_flags = ["", "u", "v", "iu", "iv"]
    for pattern in classification_patterns:
        pattern_family = "character_class_escape"
        for flags in classification_flags:
            flag_family = flags or "none"
            for input_case in classification_inputs:
                expected = category_expected(pattern, flags, input_case.units)
                assertion = "positive_or_negative_classification"
                serial = add_exec_and_search_rows(
                    rows,
                    serial=serial,
                    generator_family="character_class_escape_cartesian",
                    flag_family=flag_family,
                    input_family=input_case.name,
                    pattern_family=pattern_family,
                    assertion_family=assertion,
                    pattern=pattern,
                    flags=flags,
                    input_units=input_case.units,
                    expected=expected,
                    expected_semantics=(
                        "class escape classification plus raw UTF-16 "
                        "code-unit/code-point consumption"
                    ),
                )

    property_inputs = [
        InputFamily("ascii_a", (0x0041,)),
        InputFamily("digit_5", (0x0035,)),
        InputFamily("emoji_pair", (HIGH, LOW)),
        InputFamily("emoji_then_a", (HIGH, LOW, 0x0041)),
        InputFamily("lone_high_surrogate", (HIGH,)),
        InputFamily("adlam_pair", (0xD83A, 0xDD00)),
    ]
    property_patterns = [
        "\\p{Emoji}",
        "\\P{Emoji}",
        "[\\p{Emoji}]",
        "[\\P{Emoji}]",
        "\\p{ASCII}",
        "\\P{ASCII}",
        "[\\p{ASCII}]",
        "[\\P{ASCII}]",
    ]
    for pattern in property_patterns:
        for flags in ["u", "v"]:
            for input_case in property_inputs:
                expected = property_expected(pattern, flags, input_case.units)
                serial = add_exec_and_search_rows(
                    rows,
                    serial=serial,
                    generator_family="unicode_property_cartesian",
                    flag_family=flags,
                    input_family=input_case.name,
                    pattern_family="unicode_property_escape",
                    assertion_family="property_membership",
                    pattern=pattern,
                    flags=flags,
                    input_units=input_case.units,
                    expected=expected,
                    expected_semantics=(
                        "Unicode property membership over raw UTF-16 "
                        "surrogate pairs and lone code units"
                    ),
                )

    literal_inputs = [
        InputFamily("emoji_pair", (HIGH, LOW)),
        InputFamily("emoji_then_lone_low", (HIGH, LOW, LOW)),
        InputFamily("emoji_then_lone_high", (HIGH, LOW, HIGH)),
        InputFamily("a_then_low", (0x0041, LOW)),
        InputFamily("high_then_a", (HIGH, 0x0041)),
        InputFamily("lone_high_surrogate", (HIGH,)),
        InputFamily("lone_low_surrogate", (LOW,)),
    ]
    literal_patterns = ["\\uD83D", "\\uDE00", "[\\uD83D]", "[\\uDE00]"]
    for pattern in literal_patterns:
        for flags in ["", "u"]:
            for input_case in literal_inputs:
                expected = literal_expected(pattern, flags, input_case.units)
                serial = add_exec_and_search_rows(
                    rows,
                    serial=serial,
                    generator_family="surrogate_literal_cartesian",
                    flag_family=flags or "none",
                    input_family=input_case.name,
                    pattern_family="surrogate_literal_escape",
                    assertion_family="literal_search_position",
                    pattern=pattern,
                    flags=flags,
                    input_units=input_case.units,
                    expected=expected,
                    expected_semantics=(
                        "surrogate literal search respects Unicode pair "
                        "boundaries while non-Unicode remains code-unit based"
                    ),
                )

    boundary_inputs = [
        InputFamily("ascii_a", (0x0041,)),
        InputFamily("underscore", (0x005F,)),
        InputFamily("long_s", (0x017F,)),
        InputFamily("emoji_pair", (HIGH, LOW)),
        InputFamily("lone_high_surrogate", (HIGH,)),
    ]
    for pattern in ["\\b\\w", "\\B\\W"]:
        for flags in ["", "u", "v", "iu", "iv"]:
            for input_case in boundary_inputs:
                expected = boundary_expected(pattern, flags, input_case.units)
                serial = add_exec_and_search_rows(
                    rows,
                    serial=serial,
                    generator_family="word_boundary_cartesian",
                    flag_family=flags or "none",
                    input_family=input_case.name,
                    pattern_family="word_boundary",
                    assertion_family="boundary_and_word_classification",
                    pattern=pattern,
                    flags=flags,
                    input_units=input_case.units,
                    expected=expected,
                    expected_semantics=(
                        "word-boundary classification follows WordCharacters "
                        "and raw UTF-16 atom consumption"
                    ),
                )

    instance_specs = [
        ("dot_y_pair_start", ".", "y", (HIGH, LOW), 0),
        ("dot_y_pair_low", ".", "y", (HIGH, LOW), 1),
        ("dot_uy_pair_start", ".", "uy", (HIGH, LOW), 0),
        ("dot_uy_pair_low", ".", "uy", (HIGH, LOW), 1),
        ("non_digit_y_pair_start", "\\D", "y", (HIGH, LOW), 0),
        ("non_digit_y_pair_low", "\\D", "y", (HIGH, LOW), 1),
        ("non_digit_uy_pair_start", "\\D", "uy", (HIGH, LOW), 0),
        ("non_digit_uy_pair_low", "\\D", "uy", (HIGH, LOW), 1),
        ("low_literal_y_pair_start", "\\uDE00", "y", (HIGH, LOW), 0),
        ("low_literal_y_pair_low", "\\uDE00", "y", (HIGH, LOW), 1),
        ("low_literal_uy_pair_start", "\\uDE00", "uy", (HIGH, LOW), 0),
        ("low_literal_uy_pair_low", "\\uDE00", "uy", (HIGH, LOW), 1),
        ("low_literal_gu_pair_start", "\\uDE00", "gu", (HIGH, LOW), 0),
        ("low_literal_gu_lone_after_pair", "\\uDE00", "gu", (HIGH, LOW, LOW), 0),
        ("property_complement_gu_after_pair", "\\P{Emoji}", "gu", (HIGH, LOW, 0x0041), 0),
        ("property_complement_uy_after_pair", "\\P{Emoji}", "uy", (HIGH, LOW, 0x0041), 2),
    ]
    for name, pattern, flags, input_units, last_index in instance_specs:
        if pattern == ".":
            expected = dot_expected(flags, input_units, last_index)
        elif pattern == "\\D":
            expected = (
                slice_match(input_units, last_index, atom_width(input_units, last_index, flags))
                if last_index < len(input_units)
                else None
            )
        elif pattern == "\\uDE00":
            if "y" in flags:
                expected = (
                    slice_match(input_units, last_index, 1)
                    if last_index < len(input_units)
                    and input_units[last_index] == LOW
                    and not (unicode_mode(flags) and starts_valid_pair(input_units, last_index))
                    else None
                )
            else:
                suffix = input_units[last_index:]
                relative = literal_expected(pattern, flags, suffix)
                expected = (
                    None
                    if relative is None
                    else Match(
                        start=last_index + relative.start,
                        end=last_index + relative.end,
                        units=relative.units,
                    )
                )
        else:
            if "y" in flags:
                expected = (
                    slice_match(input_units, last_index, atom_width(input_units, last_index, flags))
                    if last_index < len(input_units)
                    and property_matches(pattern, input_units, last_index)
                    else None
                )
            else:
                expected = property_expected(pattern, flags, input_units)
        expected_last_index = 0 if expected is None else expected.end
        rows.append(
            row(
                serial=serial,
                api_route="exec_instance_js",
                generator_family="instance_position_cartesian",
                flag_family=flags,
                input_family=name,
                pattern_family="raw_utf16_instance_position",
                assertion_family="last_index_position",
                pattern=pattern,
                flags=flags,
                input_units=input_units,
                expected=expected,
                initial_last_index=last_index,
                expected_last_index=expected_last_index,
                expected_semantics=(
                    "public RegExp instance lastIndex uses raw UTF-16 "
                    "positions with sticky/global reset rules"
                ),
            )
        )
        serial += 1

    iterator_specs = [
        ("empty_g_pair_start", "", "g", (HIGH, LOW), 0, Match(0, 0, ()), 1),
        ("empty_gu_pair_start", "", "gu", (HIGH, LOW), 0, Match(0, 0, ()), 2),
        ("empty_gu_pair_low", "", "gu", (HIGH, LOW), 1, Match(1, 1, ()), 2),
        ("empty_gy_pair_start", "", "gy", (HIGH, LOW), 0, Match(0, 0, ()), 1),
        (
            "emoji_literal_gu_repeated",
            "\\u{1F600}",
            "gu",
            (HIGH, LOW, 0x0041, HIGH, LOW),
            0,
            Match(0, 2, (HIGH, LOW)),
            2,
        ),
    ]
    for name, pattern, flags, input_units, last_index, expected, expected_last_index in iterator_specs:
        rows.append(
            row(
                serial=serial,
                api_route="iter_matches_js",
                generator_family="iterator_advancement_cartesian",
                flag_family=flags,
                input_family=name,
                pattern_family="raw_utf16_iterator_advancement",
                assertion_family="first_iterator_step",
                pattern=pattern,
                flags=flags,
                input_units=input_units,
                expected=expected,
                initial_last_index=last_index,
                expected_last_index=expected_last_index,
                expected_semantics=(
                    "first RegExp string iterator step applies raw UTF-16 "
                    "AdvanceStringIndex behavior"
                ),
            )
        )
        serial += 1

    ids = [case["case_id"] for case in rows]
    if len(ids) != len(set(ids)):
        raise SystemExit("duplicate generated raw UTF-16 case_id")
    return rows


def summary_lines(rows: list[dict[str, str]]) -> list[str]:
    lines = [f"raw_utf16_generated_case_rows\t{len(rows)}\n"]
    for field in [
        "api_route",
        "generator_family",
        "flag_family",
        "pattern_family",
        "assertion_family",
        "expected_match",
    ]:
        for key, count in sorted(Counter(row[field] for row in rows).items()):
            lines.append(f"{field}_{safe_key(key)}\t{count}\n")
    lines.append("case_ids_unique\ttrue\n")
    lines.append("rows_have_expected_semantics\ttrue\n")
    lines.append("rows_have_input_units\ttrue\n")
    return lines


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--cache-dir", default="cache")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    rows = build_rows()
    lines = summary_lines(rows)
    if args.dry_run:
        print("".join(lines), end="")
        return

    cache = Path(args.cache_dir)
    detail = cache / DETAIL_NAME
    summary = cache / SUMMARY_NAME
    write_tsv(detail, FIELDNAMES, rows)
    summary.write_text("".join(lines), encoding="utf-8")
    print(summary.read_text(encoding="utf-8"), end="")


if __name__ == "__main__":
    main()
