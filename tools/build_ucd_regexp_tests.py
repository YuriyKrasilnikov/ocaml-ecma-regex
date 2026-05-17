#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import hashlib
from collections import Counter
from pathlib import Path

from ecma262_tooling import (
    bool_text,
    read_tsv,
    require_columns,
    safe_id,
    validate_unique_ids,
)


DETAIL_NAME = "ecma262-regexp-ucd-generated-cases.tsv"
SUMMARY_NAME = "ecma262-regexp-ucd-generated-cases.summary"
PROPERTY_VALUE_DETAIL_NAME = "ecma262-regexp-ucd-property-value-cases.tsv"
SCRIPT_MEMBERSHIP_DETAIL_NAME = "ecma262-regexp-ucd-script-membership-cases.tsv"
GENERAL_CATEGORY_MEMBERSHIP_DETAIL_NAME = (
    "ecma262-regexp-ucd-general-category-membership-cases.tsv"
)
BINARY_PROPERTY_MEMBERSHIP_DETAIL_NAME = (
    "ecma262-regexp-ucd-binary-property-membership-cases.tsv"
)
CHARACTER_CLASS_PROPERTY_MEMBERSHIP_DETAIL_NAME = (
    "ecma262-regexp-ucd-character-class-property-membership-cases.tsv"
)
CHARACTER_SET_MEMBERSHIP_DETAIL_NAME = (
    "ecma262-regexp-ucd-character-set-membership-cases.tsv"
)
CASE_FOLDING_DETAIL_NAME = "ecma262-regexp-ucd-case-folding-cases.tsv"
TARGET_TEST_ARTIFACT = "test/test_ecma262_ucd_generated_cases.ml"
UCD_VERSION = "16.0.0"
UCD_GENERATED_REQUIREMENT_CREDIT = "ucd_generated_requirement_credit"

EXPECTED_UCD_ROWS = 366
EXPECTED_PROPERTY_VALUE_POSITIVE_CASES = 3184
EXPECTED_PROPERTY_VALUE_NEGATIVE_CASES = 28
EXPECTED_SCRIPT_MEMBERSHIP_CASES = 12328
EXPECTED_GENERAL_CATEGORY_MEMBERSHIP_CASES = 1896
EXPECTED_BINARY_PROPERTY_MEMBERSHIP_CASES = 780
EXPECTED_CHARACTER_CLASS_PROPERTY_MEMBERSHIP_CASES = 30008
EXPECTED_CHARACTER_SET_MEMBERSHIP_CASES = 40
EXPECTED_CASE_FOLDING_CASES = 7526

GENERAL_CATEGORY_GROUPS = {
    "Other": ["Control", "Format", "Unassigned", "Private_Use", "Surrogate"],
    "Letter": [
        "Lowercase_Letter",
        "Modifier_Letter",
        "Other_Letter",
        "Titlecase_Letter",
        "Uppercase_Letter",
    ],
    "Cased_Letter": ["Lowercase_Letter", "Titlecase_Letter", "Uppercase_Letter"],
    "Mark": ["Spacing_Mark", "Enclosing_Mark", "Nonspacing_Mark"],
    "Number": ["Decimal_Number", "Letter_Number", "Other_Number"],
    "Punctuation": [
        "Connector_Punctuation",
        "Dash_Punctuation",
        "Close_Punctuation",
        "Final_Punctuation",
        "Initial_Punctuation",
        "Other_Punctuation",
        "Open_Punctuation",
    ],
    "Symbol": [
        "Currency_Symbol",
        "Modifier_Symbol",
        "Math_Symbol",
        "Other_Symbol",
    ],
    "Separator": ["Line_Separator", "Paragraph_Separator", "Space_Separator"],
}

REQUIRED_UCD_FILES = {
    "CaseFolding.txt": "6f1f9c588eb4a5c718d9e8f93b782685e5c7fec872cf05e8e6878053599e09bb",
    "DerivedCoreProperties.txt": "39d35161f2954497f69e08bdb9e701493f476a3d30222de20028feda36c1dabd",
    "DerivedNormalizationProps.txt": "4d4c03892dea9146d674b686e495df2d55a28d071ac474041d73518f887abddc",
    "PropList.txt": "53d614508e2a0b2305a8aa21cd60d993de9326cdf65993660dfcce4503548583",
    "PropertyAliases.txt": "33a9f2266ad6b8e8de05c0ea3dfac411ac62cf8839ff1c94057471e4c5f6a2b3",
    "PropertyValueAliases.txt": "440fd3e5460b9bfe31da67b6f923992e1989d31fe2ed91e091c4b8f8e2620bf9",
    "ScriptExtensions.txt": "049117ce26b9769fe2749b06eef51a50a89faef4a97764dd2d81daa715980700",
    "Scripts.txt": "9e88f0a677df47311106340be8ede2ecdacd9c1c931831218d2be6d5508e0039",
    "UnicodeData.txt": "ff58e5823bd095166564a006e47d111130813dcf8bf234ef79fa51a870edb48f",
    "emoji/emoji-data.txt": "f1365a5173eee18e1f98b240cdc492e84a25f1ce7e0c9d1094eb29c41a22696a",
}

CLAUSE_ROUTES = {
    "22.2.2.4.1": ("assertion_word_char_model", "ucd_word_char"),
    "22.2.2.7.1": ("character_set_matcher_model", "ucd_character_set_matcher"),
    "22.2.2.7.3": ("canonicalize_model", "ucd_case_folding"),
    "22.2.2.8": ("compile_character_class_model", "ucd_character_class"),
    "22.2.2.9": ("compile_to_charset_model", "ucd_compile_to_charset"),
    "22.2.2.9.3": ("word_characters_model", "ucd_word_characters"),
    "22.2.2.9.4": ("all_characters_model", "ucd_all_characters"),
    "22.2.2.9.5": ("maybe_simple_case_folding_model", "ucd_case_folding"),
    "22.2.2.9.7": ("unicode_match_property_model", "ucd_property_aliases"),
    "22.2.2.9.8": ("unicode_match_property_value_model", "ucd_property_value_aliases"),
    "22.2.2.10": ("compile_class_set_string_model", "ucd_class_set_string"),
    "22.2.7.3": ("advance_string_index_model", "ucd_utf16_indexing"),
    "22.2.7.4": ("get_string_index_model", "ucd_utf16_indexing"),
}

FILES_BY_ROUTE = {
    "ucd_all_characters": ["CaseFolding.txt"],
    "ucd_case_folding": ["CaseFolding.txt", "UnicodeData.txt"],
    "ucd_character_class": ["CaseFolding.txt", "PropList.txt", "DerivedCoreProperties.txt"],
    "ucd_character_set_matcher": ["CaseFolding.txt", "PropList.txt", "DerivedCoreProperties.txt"],
    "ucd_class_set_string": ["CaseFolding.txt"],
    "ucd_compile_to_charset": [
        "CaseFolding.txt",
        "DerivedCoreProperties.txt",
        "PropList.txt",
        "PropertyAliases.txt",
        "PropertyValueAliases.txt",
        "ScriptExtensions.txt",
        "Scripts.txt",
        "UnicodeData.txt",
    ],
    "ucd_property_aliases": ["PropertyAliases.txt"],
    "ucd_property_value_aliases": ["PropertyValueAliases.txt", "Scripts.txt", "ScriptExtensions.txt"],
    "ucd_utf16_indexing": ["UnicodeData.txt"],
    "ucd_word_char": ["CaseFolding.txt", "DerivedCoreProperties.txt"],
    "ucd_word_characters": ["CaseFolding.txt", "DerivedCoreProperties.txt"],
}


def hex_code_point(code_point: int) -> str:
    return f"{code_point:04X}"


def code_point_list_text(code_points: list[int]) -> str:
    return ",".join(hex_code_point(code_point) for code_point in code_points)


def unicode_escape(code_point: int) -> str:
    return f"\\u{{{code_point:X}}}"


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def validate_ucd_sources(ucd_dir: Path) -> dict[str, str]:
    checksums: dict[str, str] = {}
    for name, expected_hash in sorted(REQUIRED_UCD_FILES.items()):
        path = ucd_dir / name
        if not path.is_file():
            raise SystemExit(f"missing UCD {UCD_VERSION} file: {path}")
        actual_hash = sha256(path)
        if actual_hash != expected_hash:
            raise SystemExit(
                f"UCD {UCD_VERSION} checksum mismatch for {name}: "
                f"{actual_hash}; expected {expected_hash}"
            )
        checksums[name] = actual_hash
    return checksums


def read_case_folding(path: Path) -> dict[str, list[dict[str, object]]]:
    rows: dict[str, list[dict[str, object]]] = {
        "simple": [],
        "full": [],
        "turkic": [],
    }
    with path.open(encoding="utf-8") as f:
        for line_number, line in enumerate(f, start=1):
            data = line.split("#", 1)[0].strip()
            if not data:
                continue
            fields = [field.strip() for field in data.split(";")]
            if len(fields) < 3:
                raise SystemExit(
                    f"malformed CaseFolding.txt line {line_number}: {line!r}"
                )
            source = int(fields[0], 16)
            status = fields[1]
            mapping = [int(value, 16) for value in fields[2].split()]
            row = {"source": source, "status": status, "mapping": mapping}
            if status in {"C", "S"}:
                if len(mapping) != 1:
                    raise SystemExit(
                        "simple/common CaseFolding.txt row must map to one "
                        f"code point at line {line_number}"
                    )
                rows["simple"].append(row)
            elif status == "F":
                rows["full"].append(row)
            elif status == "T":
                rows["turkic"].append(row)
            else:
                raise SystemExit(
                    f"unknown CaseFolding.txt status {status!r} at line {line_number}"
                )
    return rows


def read_property_value_aliases(
    path: Path,
) -> dict[str, dict[str, str]]:
    by_property: dict[str, dict[str, str]] = {"gc": {}, "sc": {}}
    with path.open(encoding="utf-8") as f:
        for line_number, line in enumerate(f, start=1):
            data = line.split("#", 1)[0].strip()
            if not data:
                continue
            fields = [field.strip() for field in data.split(";")]
            if len(fields) < 3:
                raise SystemExit(
                    f"malformed PropertyValueAliases.txt line {line_number}: {line!r}"
                )
            property_code = fields[0]
            if property_code not in by_property:
                continue
            canonical_value = fields[2]
            for alias in fields[1:]:
                existing = by_property[property_code].get(alias)
                if existing is not None and existing != canonical_value:
                    raise SystemExit(
                        "ambiguous property value alias "
                        f"{property_code} {alias}: {existing} vs {canonical_value}"
                    )
                by_property[property_code][alias] = canonical_value
    if len(by_property["gc"]) != 80:
        raise SystemExit(
            f"expected 80 General_Category value aliases, got {len(by_property['gc'])}"
        )
    if len(by_property["sc"]) != 338:
        raise SystemExit(
            f"expected 338 Script value aliases, got {len(by_property['sc'])}"
        )
    return by_property


def read_binary_property_aliases(path: Path) -> dict[str, str]:
    aliases = {
        "ASCII": "ASCII",
        "Any": "Any",
        "Assigned": "Assigned",
    }
    in_binary_properties = False
    with path.open(encoding="utf-8") as f:
        for line_number, line in enumerate(f, start=1):
            if line.startswith("# Binary Properties"):
                in_binary_properties = True
                continue
            data = line.split("#", 1)[0].strip()
            if not data or not in_binary_properties:
                continue
            fields = [field.strip() for field in data.split(";")]
            if len(fields) < 2:
                raise SystemExit(
                    f"malformed PropertyAliases.txt line {line_number}: {line!r}"
                )
            canonical = fields[1]
            for alias in fields:
                aliases[alias] = canonical
    return aliases


def parse_code_range(field: str) -> tuple[int, int]:
    if ".." in field:
        first, last = field.split("..", 1)
    else:
        first = last = field
    return int(first, 16), int(last, 16)


def read_scripts(path: Path) -> dict[str, list[tuple[int, int]]]:
    ranges: dict[str, list[tuple[int, int]]] = {}
    with path.open(encoding="utf-8") as f:
        for line_number, line in enumerate(f, start=1):
            data = line.split("#", 1)[0].strip()
            if not data:
                continue
            fields = [field.strip() for field in data.split(";")]
            if len(fields) != 2:
                raise SystemExit(f"malformed Scripts.txt line {line_number}: {line!r}")
            ranges.setdefault(fields[1], []).append(parse_code_range(fields[0]))
    return ranges


def read_binary_property_ranges_file(
    path: Path,
    accepted_properties: set[str],
) -> dict[str, list[tuple[int, int]]]:
    ranges: dict[str, list[tuple[int, int]]] = {}
    with path.open(encoding="utf-8") as f:
        for line_number, line in enumerate(f, start=1):
            data = line.split("#", 1)[0].strip()
            if not data:
                continue
            fields = [field.strip() for field in data.split(";")]
            if len(fields) < 2:
                raise SystemExit(f"malformed {path.name} line {line_number}: {line!r}")
            property_name = fields[1]
            if property_name in accepted_properties:
                ranges.setdefault(property_name, []).append(parse_code_range(fields[0]))
    return ranges


def read_bidi_mirrored_ranges(path: Path) -> list[tuple[int, int]]:
    ranges: list[tuple[int, int]] = []
    pending_first: tuple[int, str] | None = None
    with path.open(encoding="utf-8") as f:
        for line_number, line in enumerate(f, start=1):
            fields = line.rstrip("\n").split(";")
            if len(fields) < 10:
                raise SystemExit(
                    f"malformed UnicodeData.txt line {line_number}: {line!r}"
                )
            code_point = int(fields[0], 16)
            name = fields[1]
            bidi_mirrored = fields[9]
            if name.endswith(", First>"):
                if pending_first is not None:
                    raise SystemExit(
                        f"nested UnicodeData range starts at line {line_number}"
                    )
                pending_first = (code_point, bidi_mirrored)
            elif name.endswith(", Last>"):
                if pending_first is None:
                    raise SystemExit(
                        f"UnicodeData range ends without start at line {line_number}"
                    )
                start, start_bidi_mirrored = pending_first
                if start_bidi_mirrored != bidi_mirrored:
                    raise SystemExit(
                        f"UnicodeData range Bidi_Mirrored mismatch at line {line_number}"
                    )
                if bidi_mirrored == "Y":
                    ranges.append((start, code_point))
                pending_first = None
            elif bidi_mirrored == "Y":
                ranges.append((code_point, code_point))
            elif bidi_mirrored != "N":
                raise SystemExit(
                    f"unknown UnicodeData Bidi_Mirrored value at line {line_number}: "
                    f"{bidi_mirrored}"
                )
    if pending_first is not None:
        raise SystemExit("unterminated UnicodeData range")
    return ranges


def read_script_extensions(
    path: Path,
    script_aliases: dict[str, str],
) -> tuple[dict[str, list[tuple[int, int]]], list[tuple[tuple[int, int], set[str]]]]:
    ranges: dict[str, list[tuple[int, int]]] = {}
    entries: list[tuple[tuple[int, int], set[str]]] = []
    with path.open(encoding="utf-8") as f:
        for line_number, line in enumerate(f, start=1):
            data = line.split("#", 1)[0].strip()
            if not data:
                continue
            fields = [field.strip() for field in data.split(";")]
            if len(fields) != 2:
                raise SystemExit(
                    f"malformed ScriptExtensions.txt line {line_number}: {line!r}"
                )
            code_range = parse_code_range(fields[0])
            scripts: set[str] = set()
            for short_name in fields[1].split():
                canonical = script_aliases.get(short_name)
                if canonical is None:
                    raise SystemExit(
                        f"unknown ScriptExtensions alias {short_name} at line "
                        f"{line_number}"
                    )
                scripts.add(canonical)
                ranges.setdefault(canonical, []).append(code_range)
            entries.append((code_range, scripts))
    return ranges, entries


def is_scalar_value(code_point: int) -> bool:
    return 0 <= code_point <= 0x10FFFF and not (0xD800 <= code_point <= 0xDFFF)


def range_contains(code_point: int, code_range: tuple[int, int]) -> bool:
    start, end = code_range
    return start <= code_point <= end


def ranges_contain(code_point: int, ranges: list[tuple[int, int]]) -> bool:
    return any(range_contains(code_point, code_range) for code_range in ranges)


def merged_ranges(ranges: list[tuple[int, int]]) -> list[tuple[int, int]]:
    if not ranges:
        return []
    sorted_ranges = sorted(ranges)
    merged: list[tuple[int, int]] = []
    current_start, current_end = sorted_ranges[0]
    for start, end in sorted_ranges[1:]:
        if start <= current_end + 1:
            current_end = max(current_end, end)
        else:
            merged.append((current_start, current_end))
            current_start, current_end = start, end
    merged.append((current_start, current_end))
    return merged


def complement_ranges(ranges: list[tuple[int, int]]) -> list[tuple[int, int]]:
    complement: list[tuple[int, int]] = []
    cursor = 0
    for start, end in merged_ranges(ranges):
        if cursor < start:
            complement.append((cursor, start - 1))
        cursor = max(cursor, end + 1)
    if cursor <= 0x10FFFF:
        complement.append((cursor, 0x10FFFF))
    return complement


def first_scalar_in_ranges(ranges: list[tuple[int, int]]) -> int | None:
    for start, end in sorted(ranges):
        for code_point in range(start, end + 1):
            if is_scalar_value(code_point):
                return code_point
    return None


def first_scalar_not_in_ranges(ranges: list[tuple[int, int]]) -> int:
    for code_point in range(0x110000):
        if is_scalar_value(code_point) and not ranges_contain(code_point, ranges):
            return code_point
    raise SystemExit("no Unicode scalar value outside supplied ranges")


def first_scalar_not_in_ranges_opt(ranges: list[tuple[int, int]]) -> int | None:
    for code_point in range(0x110000):
        if is_scalar_value(code_point) and not ranges_contain(code_point, ranges):
            return code_point
    return None


def script_matches_canonical(
    canonical: str,
    code_point: int,
    scripts: dict[str, list[tuple[int, int]]],
    script_any_ranges: list[tuple[int, int]],
) -> bool:
    if canonical == "Unknown":
        return not ranges_contain(code_point, script_any_ranges)
    return ranges_contain(code_point, scripts.get(canonical, []))


def script_extensions_matches_canonical(
    canonical: str,
    code_point: int,
    scripts: dict[str, list[tuple[int, int]]],
    script_any_ranges: list[tuple[int, int]],
    script_extension_entries: list[tuple[tuple[int, int], set[str]]],
) -> bool:
    for code_range, scripts_for_range in script_extension_entries:
        if range_contains(code_point, code_range):
            return canonical in scripts_for_range
    return script_matches_canonical(canonical, code_point, scripts, script_any_ranges)


def code_point_hex(code_point: int) -> str:
    return f"{code_point:04X}"


def read_general_categories(
    path: Path,
    aliases: dict[str, str],
) -> dict[str, list[tuple[int, int]]]:
    ranges: dict[str, list[tuple[int, int]]] = {}
    explicit: list[tuple[int, int]] = []
    pending_first: tuple[int, str] | None = None

    def add_range(start: int, end: int, category_code: str) -> None:
        canonical = aliases.get(category_code)
        if canonical is None:
            raise SystemExit(f"unknown General_Category value {category_code}")
        code_range = (start, end)
        ranges.setdefault(canonical, []).append(code_range)
        explicit.append(code_range)

    with path.open(encoding="utf-8") as f:
        for line_number, line in enumerate(f, start=1):
            fields = line.rstrip("\n").split(";")
            if len(fields) < 3:
                raise SystemExit(
                    f"malformed UnicodeData.txt line {line_number}: {line!r}"
                )
            code_point = int(fields[0], 16)
            name = fields[1]
            category_code = fields[2]
            if name.endswith(", First>"):
                if pending_first is not None:
                    raise SystemExit(
                        f"nested UnicodeData range starts at line {line_number}"
                    )
                pending_first = (code_point, category_code)
            elif name.endswith(", Last>"):
                if pending_first is None:
                    raise SystemExit(
                        f"UnicodeData range ends without start at line {line_number}"
                    )
                start, start_category = pending_first
                if start_category != category_code:
                    raise SystemExit(
                        f"UnicodeData range category mismatch at line {line_number}"
                    )
                add_range(start, code_point, category_code)
                pending_first = None
            else:
                add_range(code_point, code_point, category_code)
    if pending_first is not None:
        raise SystemExit("unterminated UnicodeData range")

    unassigned = aliases.get("Cn")
    if unassigned is None:
        raise SystemExit("missing Cn General_Category alias")
    ranges.setdefault(unassigned, []).extend(complement_ranges(explicit))
    for aggregate, components in GENERAL_CATEGORY_GROUPS.items():
        for component in components:
            ranges.setdefault(aggregate, []).extend(ranges.get(component, []))
    missing = set(aliases.values()).difference(ranges)
    if missing:
        raise SystemExit(
            "missing General_Category ranges: " + ", ".join(sorted(missing))
        )
    return ranges


def general_category_matches_canonical(
    canonical: str,
    code_point: int,
    general_categories: dict[str, list[tuple[int, int]]],
) -> bool:
    return ranges_contain(code_point, general_categories.get(canonical, []))


def binary_property_source_files() -> dict[str, str]:
    prop_list = {
        "ASCII_Hex_Digit",
        "Bidi_Control",
        "Dash",
        "Deprecated",
        "Diacritic",
        "Extender",
        "Hex_Digit",
        "IDS_Binary_Operator",
        "IDS_Trinary_Operator",
        "Ideographic",
        "Join_Control",
        "Logical_Order_Exception",
        "Noncharacter_Code_Point",
        "Pattern_Syntax",
        "Pattern_White_Space",
        "Quotation_Mark",
        "Radical",
        "Regional_Indicator",
        "Sentence_Terminal",
        "Soft_Dotted",
        "Terminal_Punctuation",
        "Unified_Ideograph",
        "Variation_Selector",
        "White_Space",
    }
    derived_core = {
        "Alphabetic",
        "Case_Ignorable",
        "Cased",
        "Changes_When_Casefolded",
        "Changes_When_Casemapped",
        "Changes_When_Lowercased",
        "Changes_When_Titlecased",
        "Changes_When_Uppercased",
        "Default_Ignorable_Code_Point",
        "Grapheme_Base",
        "Grapheme_Extend",
        "ID_Continue",
        "ID_Start",
        "Lowercase",
        "Math",
        "Uppercase",
        "XID_Continue",
        "XID_Start",
    }
    emoji = {
        "Emoji",
        "Emoji_Component",
        "Emoji_Modifier",
        "Emoji_Modifier_Base",
        "Emoji_Presentation",
        "Extended_Pictographic",
    }
    sources: dict[str, str] = {
        "ASCII": "external/ecma262/2026/multipage/text-processing.html",
        "Any": "external/ecma262/2026/multipage/text-processing.html",
        "Assigned": "external/ucd/16.0.0/UnicodeData.txt",
        "Bidi_Mirrored": "external/ucd/16.0.0/UnicodeData.txt",
        "Changes_When_NFKC_Casefolded": (
            "external/ucd/16.0.0/DerivedNormalizationProps.txt"
        ),
    }
    sources.update(
        {property_name: "external/ucd/16.0.0/PropList.txt" for property_name in prop_list}
    )
    sources.update(
        {
            property_name: "external/ucd/16.0.0/DerivedCoreProperties.txt"
            for property_name in derived_core
        }
    )
    sources.update(
        {
            property_name: "external/ucd/16.0.0/emoji/emoji-data.txt"
            for property_name in emoji
        }
    )
    return sources


def build_binary_properties(
    ucd_dir: Path,
    aliases: dict[str, str],
    general_categories: dict[str, list[tuple[int, int]]],
) -> dict[str, list[tuple[int, int]]]:
    accepted_properties = set(aliases.values())
    ranges: dict[str, list[tuple[int, int]]] = {}

    def add_file(file_name: str) -> None:
        for property_name, property_ranges in read_binary_property_ranges_file(
            ucd_dir / file_name,
            accepted_properties,
        ).items():
            ranges.setdefault(property_name, []).extend(property_ranges)

    add_file("PropList.txt")
    add_file("DerivedCoreProperties.txt")
    add_file("DerivedNormalizationProps.txt")
    add_file("emoji/emoji-data.txt")
    ranges.setdefault("Bidi_Mirrored", []).extend(
        read_bidi_mirrored_ranges(ucd_dir / "UnicodeData.txt")
    )
    ranges["ASCII"] = [(0x0000, 0x007F)]
    ranges["Any"] = [(0x0000, 0x10FFFF)]
    ranges["Assigned"] = complement_ranges(general_categories.get("Unassigned", []))

    missing = sorted(
        property_name for property_name in accepted_properties if property_name not in ranges
    )
    if missing:
        raise SystemExit("missing binary property ranges: " + ", ".join(missing))
    return ranges


def selected_ucd_rows(rows: list[dict[str, str]]) -> list[dict[str, str]]:
    selected = [
        row
        for row in rows
        if row["route_status"] == "needs_ucd_generated_tests"
        and row["required_sources"] == "ecma262,test262,ucd,local"
    ]
    selected.sort(key=lambda row: (row["clause_id"], row["requirement_id"]))
    if len(selected) != EXPECTED_UCD_ROWS:
        raise SystemExit(
            f"expected {EXPECTED_UCD_ROWS} UCD-routed rows, selected {len(selected)}"
        )
    unsupported = sorted({row["clause_id"] for row in selected}.difference(CLAUSE_ROUTES))
    if unsupported:
        raise SystemExit("unsupported UCD clause ids: " + ", ".join(unsupported))
    return selected


def fixture_kind(row: dict[str, str], ucd_route: str) -> str:
    if row["requirement_kind"] == "table_row":
        if ucd_route == "ucd_property_aliases":
            return "ecma262_property_alias_table_row"
        if ucd_route == "ucd_property_value_aliases":
            return "ucd_property_value_alias_row"
    if row["semantic_family"] == "unicode_case":
        return "case_folding_fixture"
    if row["semantic_family"] == "unicode_properties":
        return "property_alias_fixture"
    if row["semantic_family"] == "unicode":
        return "utf16_or_allcharacters_fixture"
    if row["semantic_family"] == "unicode_sets":
        return "unicode_sets_string_fixture"
    if row["semantic_family"] == "assertions":
        return "word_char_fixture"
    return "character_class_fixture"


def table_row_payload(row: dict[str, str]) -> str:
    if row["requirement_kind"] != "table_row":
        return ""
    marker = ": "
    if marker not in row["requirement_text"]:
        return ""
    return row["requirement_text"].rsplit(marker, 1)[1]


def property_alias_kind(row: dict[str, str]) -> str:
    if row["clause_id"] != "22.2.2.9.7":
        return "not_property_alias_row"
    if row["requirement_kind"] != "table_row":
        return "unicode_match_property_algorithm"
    local = row["requirement_local_id"]
    if local in {"1.1", "2.1", "3.1"}:
        return "property_table_header"
    if local.startswith("1."):
        return "non_binary_property_alias"
    if local.startswith("2."):
        return "binary_property_alias"
    if local.startswith("3."):
        return "string_property"
    return "not_property_alias_row"


def property_alias_text(row: dict[str, str]) -> str:
    kind = property_alias_kind(row)
    if kind in {"not_property_alias_row", "property_table_header"}:
        return ""
    payload = table_row_payload(row)
    return payload.split(" | ", 1)[0]


def property_compile_body(alias_kind: str, alias: str) -> str:
    if alias_kind == "non_binary_property_alias":
        if alias in {"General_Category", "gc"}:
            return f"{alias}=Letter"
        if alias in {"Script", "sc", "Script_Extensions", "scx"}:
            return f"{alias}=Latin"
    if alias_kind in {"binary_property_alias", "string_property"}:
        return alias
    return ""


def property_compile_flags(alias_kind: str) -> str:
    if alias_kind == "string_property":
        return "v"
    if alias_kind in {"non_binary_property_alias", "binary_property_alias"}:
        return "u"
    return ""


def property_expected_parser_result(alias_kind: str) -> str:
    if alias_kind in {
        "non_binary_property_alias",
        "binary_property_alias",
        "string_property",
    }:
        return "compile_ok"
    return "not_applicable"


def expected_observation(row: dict[str, str], ucd_model_family: str) -> str:
    suffix = row["requirement_id"].rsplit("-", 1)[1]
    return f"{ucd_model_family}_{suffix}_observed"


def plan_row(row: dict[str, str]) -> dict[str, str]:
    ucd_model_family, ucd_route = CLAUSE_ROUTES[row["clause_id"]]
    observation = expected_observation(row, ucd_model_family)
    files = FILES_BY_ROUTE[ucd_route]
    case_id = f"ucd-generated:{row['requirement_id']}:{safe_id(observation)}"
    alias_kind = property_alias_kind(row)
    alias = property_alias_text(row)
    compile_body = property_compile_body(alias_kind, alias)
    return {
        "case_id": case_id,
        "requirement_id": row["requirement_id"],
        "clause_id": row["clause_id"],
        "clause_title": row["clause_title"],
        "source_file": row["source_file"],
        "section_anchor": row["section_anchor"],
        "requirement_kind": row["requirement_kind"],
        "requirement_local_id": row["requirement_local_id"],
        "requirement_text": row["requirement_text"],
        "semantic_family": row["semantic_family"],
        "product_surface": row["product_surface"],
        "implementation_layer": row["implementation_layer"],
        "coverage_areas": row["coverage_areas"],
        "ucd_version": UCD_VERSION,
        "ucd_model_family": ucd_model_family,
        "ucd_route": ucd_route,
        "ucd_files": ",".join(files),
        "fixture_kind": fixture_kind(row, ucd_route),
        "fixture_input": row["requirement_local_id"],
        "property_alias_kind": alias_kind,
        "property_alias": alias,
        "property_compile_body": compile_body,
        "property_compile_pattern": (
            f"\\p{{{compile_body}}}" if compile_body else ""
        ),
        "property_compile_flags": property_compile_flags(alias_kind),
        "property_expected_parser_result": property_expected_parser_result(alias_kind),
        "expected_observation": observation,
        "expected_behavior": "ucd_generated_requirement_covered",
        "coverage_credit": UCD_GENERATED_REQUIREMENT_CREDIT,
        "case_state": "covered_by_ucd_generated_tests",
        "target_test_artifact": TARGET_TEST_ARTIFACT,
        "exact_case_obligation": row["requirement_text"],
        "next_action": "none_covered_by_ucd_generated_tests",
        "generation_reason": (
            "UCD-routed ECMA-262 RegExp row is covered by deterministic "
            "Unicode 16.0.0 generated cases in the executable UCD test artifact"
        ),
    }


def property_value_positive_rows(
    value_aliases: dict[str, dict[str, str]],
) -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    property_specs = [
        ("General_Category", "gc", "General_Category"),
        ("gc", "gc", "General_Category"),
        ("Script", "sc", "Script"),
        ("sc", "sc", "Script"),
        ("Script_Extensions", "sc", "Script_Extensions"),
        ("scx", "sc", "Script_Extensions"),
    ]
    for property_alias, value_property_code, canonical_property_name in property_specs:
        for value_alias, canonical_value in sorted(
            value_aliases[value_property_code].items()
        ):
            for escape_prefix in ["p", "P"]:
                compile_body = f"{property_alias}={value_alias}"
                rows.append(
                    {
                        "case_id": (
                            "ucd-property-value:"
                            f"{escape_prefix}:{safe_id(property_alias)}:"
                            f"{safe_id(value_alias)}"
                        ),
                        "ucd_version": UCD_VERSION,
                        "source_file": "external/ucd/16.0.0/PropertyValueAliases.txt",
                        "expression_kind": "property_value",
                        "escape_prefix": escape_prefix,
                        "property_name": property_alias,
                        "canonical_property_name": canonical_property_name,
                        "value_source_property": value_property_code,
                        "property_value_alias": value_alias,
                        "canonical_property_value": canonical_value,
                        "property_compile_body": compile_body,
                        "property_compile_pattern": f"\\{escape_prefix}{{{compile_body}}}",
                        "property_compile_flags": "u",
                        "expected_parser_result": "compile_ok",
                        "generation_reason": (
                            "ECMA-262 UnicodeMatchPropertyValue requires exact "
                            "PropertyValueAliases.txt support for Table 64 "
                            "non-binary Unicode properties"
                        ),
                    }
                )
    for value_alias, canonical_value in sorted(value_aliases["gc"].items()):
        for escape_prefix in ["p", "P"]:
            rows.append(
                {
                    "case_id": (
                        f"ucd-property-value:{escape_prefix}:lone-gc:"
                        f"{safe_id(value_alias)}"
                    ),
                    "ucd_version": UCD_VERSION,
                    "source_file": "external/ucd/16.0.0/PropertyValueAliases.txt",
                    "expression_kind": "lone_general_category_value",
                    "escape_prefix": escape_prefix,
                    "property_name": "",
                    "canonical_property_name": "General_Category",
                    "value_source_property": "gc",
                    "property_value_alias": value_alias,
                    "canonical_property_value": canonical_value,
                    "property_compile_body": value_alias,
                    "property_compile_pattern": f"\\{escape_prefix}{{{value_alias}}}",
                    "property_compile_flags": "u",
                    "expected_parser_result": "compile_ok",
                    "generation_reason": (
                        "ECMA-262 LoneUnicodePropertyNameOrValue accepts exact "
                        "General_Category property values and aliases"
                    ),
                }
            )
    return rows


def property_value_negative_rows() -> list[dict[str, str]]:
    invalid_bodies = [
        ("General_Category=Latin", "invalid_property_value"),
        ("gc=Latn", "invalid_property_value"),
        ("Script=Letter", "invalid_property_value"),
        ("sc=L", "invalid_property_value"),
        ("Script_Extensions=Letter", "invalid_property_value"),
        ("scx=L", "invalid_property_value"),
        ("General_Category=NoSuch", "invalid_property_value"),
        ("gc=NoSuch", "invalid_property_value"),
        ("Script=NoSuch", "invalid_property_value"),
        ("sc=NoSuch", "invalid_property_value"),
        ("Script_Extensions=NoSuch", "invalid_property_value"),
        ("scx=NoSuch", "invalid_property_value"),
        ("Latin", "invalid_lone_property_value"),
        ("NoSuch", "invalid_lone_property_value"),
    ]
    rows: list[dict[str, str]] = []
    for body, expression_kind in invalid_bodies:
        for escape_prefix in ["p", "P"]:
            rows.append(
                {
                    "case_id": (
                        f"ucd-property-value:{escape_prefix}:negative:"
                        f"{safe_id(body)}"
                    ),
                    "ucd_version": UCD_VERSION,
                    "source_file": "external/ucd/16.0.0/PropertyValueAliases.txt",
                    "expression_kind": expression_kind,
                    "escape_prefix": escape_prefix,
                    "property_name": body.split("=", 1)[0] if "=" in body else "",
                    "canonical_property_name": "",
                    "value_source_property": "",
                    "property_value_alias": body.split("=", 1)[1] if "=" in body else body,
                    "canonical_property_value": "",
                    "property_compile_body": body,
                    "property_compile_pattern": f"\\{escape_prefix}{{{body}}}",
                    "property_compile_flags": "u",
                    "expected_parser_result": "compile_error",
                    "generation_reason": (
                        "ECMA-262 requires unsupported Unicode property values and "
                        "cross-property aliases to remain syntax errors"
                    ),
                }
            )
    return rows


def property_value_rows(value_aliases: dict[str, dict[str, str]]) -> list[dict[str, str]]:
    positives = property_value_positive_rows(value_aliases)
    negatives = property_value_negative_rows()
    if len(positives) != EXPECTED_PROPERTY_VALUE_POSITIVE_CASES:
        raise SystemExit(
            "expected "
            f"{EXPECTED_PROPERTY_VALUE_POSITIVE_CASES} property-value positive "
            f"cases, got {len(positives)}"
        )
    if len(negatives) != EXPECTED_PROPERTY_VALUE_NEGATIVE_CASES:
        raise SystemExit(
            "expected "
            f"{EXPECTED_PROPERTY_VALUE_NEGATIVE_CASES} property-value negative "
            f"cases, got {len(negatives)}"
        )
    ids = [row["case_id"] for row in positives + negatives]
    if len(ids) != len(set(ids)):
        raise SystemExit("duplicate property-value generated case id")
    patterns = [
        (row["property_compile_pattern"], row["property_compile_flags"])
        for row in positives + negatives
    ]
    if len(patterns) != len(set(patterns)):
        raise SystemExit("duplicate property-value generated pattern")
    return positives + negatives


def script_positive_samples(
    canonical_values: list[str],
    scripts: dict[str, list[tuple[int, int]]],
    script_any_ranges: list[tuple[int, int]],
) -> dict[str, int]:
    samples: dict[str, int] = {}
    for canonical in canonical_values:
        if canonical == "Unknown":
            samples[canonical] = first_scalar_not_in_ranges(script_any_ranges)
            continue
        sample = first_scalar_in_ranges(scripts.get(canonical, []))
        if sample is not None:
            samples[canonical] = sample
    return samples


def script_negative_samples(
    canonical_values: list[str],
    script_samples: dict[str, int],
    scripts: dict[str, list[tuple[int, int]]],
    script_any_ranges: list[tuple[int, int]],
) -> dict[str, int]:
    samples: dict[str, int] = {}
    for canonical in canonical_values:
        for candidate in script_samples.values():
            if not script_matches_canonical(
                canonical,
                candidate,
                scripts,
                script_any_ranges,
            ):
                samples[canonical] = candidate
                break
        if canonical not in samples:
            raise SystemExit(f"missing Script negative sample for {canonical}")
    return samples


def script_extensions_explicit_positive_samples(
    canonical_values: list[str],
    script_extension_ranges: dict[str, list[tuple[int, int]]],
) -> dict[str, int]:
    samples: dict[str, int] = {}
    for canonical in canonical_values:
        sample = first_scalar_in_ranges(script_extension_ranges.get(canonical, []))
        if sample is not None:
            samples[canonical] = sample
    return samples


def script_extensions_fallback_positive_samples(
    canonical_values: list[str],
    scripts: dict[str, list[tuple[int, int]]],
    script_any_ranges: list[tuple[int, int]],
    script_extension_entries: list[tuple[tuple[int, int], set[str]]],
) -> dict[str, int]:
    explicit_ranges = [code_range for code_range, _ in script_extension_entries]
    samples: dict[str, int] = {}
    for canonical in canonical_values:
        if canonical == "Unknown":
            sample = first_scalar_not_in_ranges(script_any_ranges + explicit_ranges)
            samples[canonical] = sample
            continue
        for start, end in sorted(scripts.get(canonical, [])):
            found = None
            for code_point in range(start, end + 1):
                if is_scalar_value(code_point) and not ranges_contain(
                    code_point,
                    explicit_ranges,
                ):
                    found = code_point
                    break
            if found is not None:
                samples[canonical] = found
                break
    return samples


def script_extensions_negative_samples(
    canonical_values: list[str],
    script_samples: dict[str, int],
    scripts: dict[str, list[tuple[int, int]]],
    script_any_ranges: list[tuple[int, int]],
    script_extension_entries: list[tuple[tuple[int, int], set[str]]],
) -> dict[str, int]:
    explicit_candidates = [
        start
        for (start, _), scripts_for_range in script_extension_entries
        if is_scalar_value(start) and scripts_for_range
    ]
    samples: dict[str, int] = {}
    for canonical in canonical_values:
        for candidate in explicit_candidates:
            if not script_extensions_matches_canonical(
                canonical,
                candidate,
                scripts,
                script_any_ranges,
                script_extension_entries,
            ):
                samples[canonical] = candidate
                break
        if canonical in samples:
            continue
        for candidate in script_samples.values():
            if not script_extensions_matches_canonical(
                canonical,
                candidate,
                scripts,
                script_any_ranges,
                script_extension_entries,
            ):
                samples[canonical] = candidate
                break
        if canonical not in samples:
            raise SystemExit(
                f"missing Script_Extensions negative sample for {canonical}"
            )
    return samples


def add_script_membership_rows(
    rows: list[dict[str, str]],
    *,
    canonical_property_name: str,
    property_names: list[str],
    property_value_alias: str,
    canonical_property_value: str,
    sample_kind: str,
    code_point: int,
    member: bool,
) -> None:
    for property_name in property_names:
        for flags in ["u", "v"]:
            for escape_prefix in ["p", "P"]:
                expected = member if escape_prefix == "p" else not member
                compile_body = f"{property_name}={property_value_alias}"
                rows.append(
                    {
                        "case_id": (
                            "ucd-script-membership:"
                            f"{safe_id(canonical_property_name)}:"
                            f"{flags}:{escape_prefix}:"
                            f"{safe_id(property_name)}:"
                            f"{safe_id(property_value_alias)}:"
                            f"{sample_kind}"
                        ),
                        "ucd_version": UCD_VERSION,
                        "source_file": (
                            "external/ucd/16.0.0/Scripts.txt"
                            if canonical_property_name == "Script"
                            else "external/ucd/16.0.0/ScriptExtensions.txt"
                        ),
                        "expression_kind": "script_membership",
                        "sample_kind": sample_kind,
                        "escape_prefix": escape_prefix,
                        "property_name": property_name,
                        "canonical_property_name": canonical_property_name,
                        "property_value_alias": property_value_alias,
                        "canonical_property_value": canonical_property_value,
                        "input_code_point": code_point_hex(code_point),
                        "property_compile_body": compile_body,
                        "property_compile_pattern": f"^\\{escape_prefix}{{{compile_body}}}$",
                        "property_compile_flags": flags,
                        "expected_match": bool_text(expected),
                        "generation_reason": (
                            "ECMA-262 Unicode property escapes require "
                            "Script and Script_Extensions membership to match "
                            "UCD Script data exactly at runtime"
                        ),
                    }
                )


def script_membership_rows(
    value_aliases: dict[str, dict[str, str]],
    scripts: dict[str, list[tuple[int, int]]],
    script_extension_ranges: dict[str, list[tuple[int, int]]],
    script_extension_entries: list[tuple[tuple[int, int], set[str]]],
) -> list[dict[str, str]]:
    script_aliases = value_aliases["sc"]
    canonical_values = sorted(set(script_aliases.values()))
    script_any_ranges = [
        code_range for ranges in scripts.values() for code_range in ranges
    ]
    script_positive = script_positive_samples(
        canonical_values,
        scripts,
        script_any_ranges,
    )
    script_negative = script_negative_samples(
        canonical_values,
        script_positive,
        scripts,
        script_any_ranges,
    )
    script_extensions_explicit = script_extensions_explicit_positive_samples(
        canonical_values,
        script_extension_ranges,
    )
    script_extensions_fallback = script_extensions_fallback_positive_samples(
        canonical_values,
        scripts,
        script_any_ranges,
        script_extension_entries,
    )
    script_extensions_negative = script_extensions_negative_samples(
        canonical_values,
        script_positive,
        scripts,
        script_any_ranges,
        script_extension_entries,
    )
    rows: list[dict[str, str]] = []
    for alias, canonical in sorted(script_aliases.items()):
        if canonical in script_positive:
            add_script_membership_rows(
                rows,
                canonical_property_name="Script",
                property_names=["Script", "sc"],
                property_value_alias=alias,
                canonical_property_value=canonical,
                sample_kind="script_positive",
                code_point=script_positive[canonical],
                member=True,
            )
        add_script_membership_rows(
            rows,
            canonical_property_name="Script",
            property_names=["Script", "sc"],
            property_value_alias=alias,
            canonical_property_value=canonical,
            sample_kind="script_negative",
            code_point=script_negative[canonical],
            member=False,
        )
        if canonical in script_extensions_explicit:
            add_script_membership_rows(
                rows,
                canonical_property_name="Script_Extensions",
                property_names=["Script_Extensions", "scx"],
                property_value_alias=alias,
                canonical_property_value=canonical,
                sample_kind="script_extensions_explicit_positive",
                code_point=script_extensions_explicit[canonical],
                member=True,
            )
        if canonical in script_extensions_fallback:
            add_script_membership_rows(
                rows,
                canonical_property_name="Script_Extensions",
                property_names=["Script_Extensions", "scx"],
                property_value_alias=alias,
                canonical_property_value=canonical,
                sample_kind="script_extensions_fallback_positive",
                code_point=script_extensions_fallback[canonical],
                member=True,
            )
        add_script_membership_rows(
            rows,
            canonical_property_name="Script_Extensions",
            property_names=["Script_Extensions", "scx"],
            property_value_alias=alias,
            canonical_property_value=canonical,
            sample_kind="script_extensions_negative",
            code_point=script_extensions_negative[canonical],
            member=False,
        )
    ids = [row["case_id"] for row in rows]
    if len(rows) != EXPECTED_SCRIPT_MEMBERSHIP_CASES:
        raise SystemExit(
            "expected "
            f"{EXPECTED_SCRIPT_MEMBERSHIP_CASES} Script membership cases, got "
            f"{len(rows)}"
        )
    if len(ids) != len(set(ids)):
        raise SystemExit("duplicate Script membership case id")
    for row in rows:
        code_point = int(row["input_code_point"], 16)
        canonical = row["canonical_property_value"]
        if row["canonical_property_name"] == "Script":
            member = script_matches_canonical(
                canonical,
                code_point,
                scripts,
                script_any_ranges,
            )
        else:
            member = script_extensions_matches_canonical(
                canonical,
                code_point,
                scripts,
                script_any_ranges,
                script_extension_entries,
            )
        if row["escape_prefix"] == "P":
            member = not member
        if bool_text(member) != row["expected_match"]:
            raise SystemExit(f"{row['case_id']}: expected_match mismatch")
    return rows


def general_category_positive_samples(
    canonical_values: list[str],
    general_categories: dict[str, list[tuple[int, int]]],
) -> dict[str, int]:
    samples: dict[str, int] = {}
    for canonical in canonical_values:
        sample = first_scalar_in_ranges(general_categories.get(canonical, []))
        if sample is not None:
            samples[canonical] = sample
    return samples


def general_category_negative_samples(
    canonical_values: list[str],
    positive_samples: dict[str, int],
    general_categories: dict[str, list[tuple[int, int]]],
) -> dict[str, int]:
    samples: dict[str, int] = {}
    for canonical in canonical_values:
        for candidate in positive_samples.values():
            if not general_category_matches_canonical(
                canonical,
                candidate,
                general_categories,
            ):
                samples[canonical] = candidate
                break
        if canonical not in samples:
            raise SystemExit(
                f"missing General_Category negative sample for {canonical}"
            )
    return samples


def add_general_category_membership_rows(
    rows: list[dict[str, str]],
    *,
    expression_kind: str,
    property_names: list[str],
    property_value_alias: str,
    canonical_property_value: str,
    sample_kind: str,
    code_point: int,
    member: bool,
) -> None:
    for property_name in property_names:
        for flags in ["u", "v"]:
            for escape_prefix in ["p", "P"]:
                expected = member if escape_prefix == "p" else not member
                compile_body = (
                    property_value_alias
                    if property_name == ""
                    else f"{property_name}={property_value_alias}"
                )
                rows.append(
                    {
                        "case_id": (
                            "ucd-general-category-membership:"
                            f"{expression_kind}:{flags}:{escape_prefix}:"
                            f"{safe_id(property_name or 'lone')}:"
                            f"{safe_id(property_value_alias)}:{sample_kind}"
                        ),
                        "ucd_version": UCD_VERSION,
                        "source_file": "external/ucd/16.0.0/UnicodeData.txt",
                        "expression_kind": expression_kind,
                        "sample_kind": sample_kind,
                        "escape_prefix": escape_prefix,
                        "property_name": property_name,
                        "canonical_property_name": "General_Category",
                        "property_value_alias": property_value_alias,
                        "canonical_property_value": canonical_property_value,
                        "input_code_point": code_point_hex(code_point),
                        "property_compile_body": compile_body,
                        "property_compile_pattern": f"^\\{escape_prefix}{{{compile_body}}}$",
                        "property_compile_flags": flags,
                        "expected_match": bool_text(expected),
                        "generation_reason": (
                            "ECMA-262 Unicode property escapes require "
                            "General_Category membership and lone category "
                            "values to match UCD UnicodeData.txt exactly at runtime"
                        ),
                    }
                )


def general_category_membership_rows(
    value_aliases: dict[str, dict[str, str]],
    general_categories: dict[str, list[tuple[int, int]]],
) -> list[dict[str, str]]:
    category_aliases = value_aliases["gc"]
    canonical_values = sorted(set(category_aliases.values()))
    positive = general_category_positive_samples(canonical_values, general_categories)
    negative = general_category_negative_samples(
        canonical_values,
        positive,
        general_categories,
    )
    rows: list[dict[str, str]] = []
    for alias, canonical in sorted(category_aliases.items()):
        if canonical in positive:
            add_general_category_membership_rows(
                rows,
                expression_kind="general_category_property_value",
                property_names=["General_Category", "gc"],
                property_value_alias=alias,
                canonical_property_value=canonical,
                sample_kind="general_category_positive",
                code_point=positive[canonical],
                member=True,
            )
            add_general_category_membership_rows(
                rows,
                expression_kind="lone_general_category_value_membership",
                property_names=[""],
                property_value_alias=alias,
                canonical_property_value=canonical,
                sample_kind="general_category_positive",
                code_point=positive[canonical],
                member=True,
            )
        add_general_category_membership_rows(
            rows,
            expression_kind="general_category_property_value",
            property_names=["General_Category", "gc"],
            property_value_alias=alias,
            canonical_property_value=canonical,
            sample_kind="general_category_negative",
            code_point=negative[canonical],
            member=False,
        )
        add_general_category_membership_rows(
            rows,
            expression_kind="lone_general_category_value_membership",
            property_names=[""],
            property_value_alias=alias,
            canonical_property_value=canonical,
            sample_kind="general_category_negative",
            code_point=negative[canonical],
            member=False,
        )
    ids = [row["case_id"] for row in rows]
    if len(rows) != EXPECTED_GENERAL_CATEGORY_MEMBERSHIP_CASES:
        raise SystemExit(
            "expected "
            f"{EXPECTED_GENERAL_CATEGORY_MEMBERSHIP_CASES} General_Category "
            f"membership cases, got {len(rows)}"
        )
    if len(ids) != len(set(ids)):
        raise SystemExit("duplicate General_Category membership case id")
    for row in rows:
        code_point = int(row["input_code_point"], 16)
        canonical = row["canonical_property_value"]
        member = general_category_matches_canonical(
            canonical,
            code_point,
            general_categories,
        )
        if row["escape_prefix"] == "P":
            member = not member
        if bool_text(member) != row["expected_match"]:
            raise SystemExit(f"{row['case_id']}: expected_match mismatch")
    return rows


def selected_binary_property_aliases(
    source_rows: list[dict[str, str]],
    binary_property_aliases: dict[str, str],
) -> dict[str, str]:
    aliases: dict[str, str] = {}
    for row in source_rows:
        if (
            row["property_alias_kind"] == "binary_property_alias"
            and row["property_expected_parser_result"] == "compile_ok"
        ):
            alias = row["property_alias"]
            canonical = binary_property_aliases.get(alias)
            if canonical is None:
                raise SystemExit(f"missing binary property canonical name for {alias}")
            aliases[alias] = canonical
    if len(aliases) != 98:
        raise SystemExit(f"expected 98 ECMAScript binary aliases, got {len(aliases)}")
    return aliases


def add_binary_property_membership_rows(
    rows: list[dict[str, str]],
    *,
    property_alias: str,
    canonical_property_name: str,
    source_file: str,
    sample_kind: str,
    code_point: int,
    member: bool,
) -> None:
    for flags in ["u", "v"]:
        for escape_prefix in ["p", "P"]:
            expected = member if escape_prefix == "p" else not member
            rows.append(
                {
                    "case_id": (
                        "ucd-binary-property-membership:"
                        f"{flags}:{escape_prefix}:{safe_id(property_alias)}:"
                        f"{sample_kind}"
                    ),
                    "ucd_version": UCD_VERSION,
                    "source_file": source_file,
                    "expression_kind": "binary_property_membership",
                    "sample_kind": sample_kind,
                    "escape_prefix": escape_prefix,
                    "property_alias": property_alias,
                    "canonical_property_name": canonical_property_name,
                    "input_code_point": code_point_hex(code_point),
                    "property_compile_body": property_alias,
                    "property_compile_pattern": f"^\\{escape_prefix}{{{property_alias}}}$",
                    "property_compile_flags": flags,
                    "expected_match": bool_text(expected),
                    "generation_reason": (
                        "ECMA-262 Unicode property escapes require lone binary "
                        "properties to match UCD binary property membership exactly "
                        "at runtime"
                    ),
                }
            )


def binary_property_membership_rows(
    source_rows: list[dict[str, str]],
    binary_property_aliases: dict[str, str],
    binary_properties: dict[str, list[tuple[int, int]]],
) -> list[dict[str, str]]:
    selected_aliases = selected_binary_property_aliases(
        source_rows,
        binary_property_aliases,
    )
    source_files = binary_property_source_files()
    rows: list[dict[str, str]] = []
    for alias, canonical in sorted(selected_aliases.items()):
        source_file = source_files.get(canonical)
        if source_file is None:
            raise SystemExit(f"missing binary property source file for {canonical}")
        ranges = binary_properties.get(canonical, [])
        positive = first_scalar_in_ranges(ranges)
        if positive is None:
            raise SystemExit(f"missing binary property positive sample for {canonical}")
        add_binary_property_membership_rows(
            rows,
            property_alias=alias,
            canonical_property_name=canonical,
            source_file=source_file,
            sample_kind="binary_property_positive",
            code_point=positive,
            member=True,
        )
        negative = first_scalar_not_in_ranges_opt(ranges)
        if negative is not None:
            add_binary_property_membership_rows(
                rows,
                property_alias=alias,
                canonical_property_name=canonical,
                source_file=source_file,
                sample_kind="binary_property_negative",
                code_point=negative,
                member=False,
            )

    ids = [row["case_id"] for row in rows]
    if len(rows) != EXPECTED_BINARY_PROPERTY_MEMBERSHIP_CASES:
        raise SystemExit(
            "expected "
            f"{EXPECTED_BINARY_PROPERTY_MEMBERSHIP_CASES} binary property "
            f"membership cases, got {len(rows)}"
        )
    if len(ids) != len(set(ids)):
        raise SystemExit("duplicate binary property membership case id")
    for row in rows:
        code_point = int(row["input_code_point"], 16)
        canonical = row["canonical_property_name"]
        member = ranges_contain(code_point, binary_properties.get(canonical, []))
        if row["escape_prefix"] == "P":
            member = not member
        if bool_text(member) != row["expected_match"]:
            raise SystemExit(f"{row['case_id']}: expected_match mismatch")
    return rows


def character_class_property_membership_rows(
    *,
    script_rows: list[dict[str, str]],
    general_category_rows: list[dict[str, str]],
    binary_property_rows: list[dict[str, str]],
) -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    source_specs = [
        ("script_membership", script_rows),
        ("general_category_membership", general_category_rows),
        ("binary_property_membership", binary_property_rows),
    ]
    for source_family, source_cases in source_specs:
        for source_row in source_cases:
            for class_inverted in [False, True]:
                origin_id = source_row["case_id"]
                origin_hash = hashlib.sha256(origin_id.encode("utf-8")).hexdigest()[:12]
                expected = source_row["expected_match"] == "true"
                if class_inverted:
                    expected = not expected
                escape_prefix = source_row["escape_prefix"]
                compile_body = source_row["property_compile_body"]
                class_prefix = "[^" if class_inverted else "["
                rows.append(
                    {
                        "case_id": (
                            "ucd-character-class-property-membership:"
                            f"{source_family}:"
                            f"{'inverted' if class_inverted else 'positive'}:"
                            f"{safe_id(origin_id)}:{origin_hash}"
                        ),
                        "origin_case_id": origin_id,
                        "ucd_version": UCD_VERSION,
                        "source_file": source_row["source_file"],
                        "source_membership_family": source_family,
                        "expression_kind": source_row["expression_kind"],
                        "sample_kind": source_row["sample_kind"],
                        "class_inverted": bool_text(class_inverted),
                        "escape_prefix": escape_prefix,
                        "property_name": source_row.get("property_name", ""),
                        "property_alias": source_row.get("property_alias", ""),
                        "canonical_property_name": source_row["canonical_property_name"],
                        "property_value_alias": source_row.get("property_value_alias", ""),
                        "canonical_property_value": source_row.get(
                            "canonical_property_value",
                            "",
                        ),
                        "input_code_point": source_row["input_code_point"],
                        "property_compile_body": compile_body,
                        "property_compile_pattern": (
                            f"^{class_prefix}\\{escape_prefix}{{{compile_body}}}]$"
                        ),
                        "property_compile_flags": source_row["property_compile_flags"],
                        "expected_match": bool_text(expected),
                        "generation_reason": (
                            "ECMA-262 CharacterClass membership must route "
                            "Unicode property escapes through the same UCD "
                            "code-point semantics as top-level property escapes, "
                            "including class inversion"
                        ),
                    }
                )

    ids = [row["case_id"] for row in rows]
    if len(rows) != EXPECTED_CHARACTER_CLASS_PROPERTY_MEMBERSHIP_CASES:
        raise SystemExit(
            "expected "
            f"{EXPECTED_CHARACTER_CLASS_PROPERTY_MEMBERSHIP_CASES} character-class "
            f"property membership cases, got {len(rows)}"
        )
    if len(ids) != len(set(ids)):
        raise SystemExit("duplicate character-class property membership case id")
    return rows


def character_set_case_specs() -> list[dict[str, object]]:
    return [
        {
            "case_family": "empty_char_set",
            "requirement_id": "ecma262-22.2.2.9-0004",
            "pattern": "^[]$",
            "flags": "",
            "input_code_points": "0061",
            "expected_match": False,
            "spec_route": "compile_to_charset_empty",
        },
        {
            "case_family": "empty_complement",
            "requirement_id": "ecma262-22.2.2.8-0009",
            "pattern": "^[^]$",
            "flags": "",
            "input_code_points": "0061",
            "expected_match": True,
            "spec_route": "compile_character_class_invert_true",
        },
        {
            "case_family": "literal",
            "requirement_id": "ecma262-22.2.2.9-0028",
            "pattern": "^[a]$",
            "flags": "",
            "input_code_points": "0061",
            "expected_match": True,
            "spec_route": "compile_to_charset_source_character",
        },
        {
            "case_family": "literal",
            "requirement_id": "ecma262-22.2.2.9-0028",
            "pattern": "^[a]$",
            "flags": "",
            "input_code_points": "0062",
            "expected_match": False,
            "spec_route": "character_set_matcher_found_false",
        },
        {
            "case_family": "hyphen",
            "requirement_id": "ecma262-22.2.2.9-0026",
            "pattern": "^[-]$",
            "flags": "",
            "input_code_points": "002D",
            "expected_match": True,
            "spec_route": "compile_to_charset_hyphen",
        },
        {
            "case_family": "hyphen",
            "requirement_id": "ecma262-22.2.2.9-0030",
            "pattern": "^[\\-]$",
            "flags": "u",
            "input_code_points": "002D",
            "expected_match": True,
            "spec_route": "compile_to_charset_class_escape_hyphen",
        },
        {
            "case_family": "backspace_escape",
            "requirement_id": "ecma262-22.2.2.9-0139",
            "pattern": "^[\\b]$",
            "flags": "u",
            "input_code_points": "0008",
            "expected_match": True,
            "spec_route": "compile_to_charset_backspace",
        },
        {
            "case_family": "backspace_escape",
            "requirement_id": "ecma262-22.2.2.9-0139",
            "pattern": "^[\\b]$",
            "flags": "u",
            "input_code_points": "0062",
            "expected_match": False,
            "spec_route": "compile_to_charset_backspace_negative",
        },
        {
            "case_family": "control_escape",
            "requirement_id": "ecma262-22.2.2.9-0031",
            "pattern": "^[\\cA]$",
            "flags": "u",
            "input_code_points": "0001",
            "expected_match": True,
            "spec_route": "compile_to_charset_character_escape",
        },
        {
            "case_family": "hex_escape",
            "requirement_id": "ecma262-22.2.2.9-0031",
            "pattern": "^[\\x41]$",
            "flags": "",
            "input_code_points": "0041",
            "expected_match": True,
            "spec_route": "compile_to_charset_character_escape",
        },
        {
            "case_family": "hex_escape",
            "requirement_id": "ecma262-22.2.2.9-0031",
            "pattern": "^[\\x41]$",
            "flags": "",
            "input_code_points": "0078",
            "expected_match": False,
            "spec_route": "compile_to_charset_character_escape_negative",
        },
        {
            "case_family": "unicode_fixed_escape",
            "requirement_id": "ecma262-22.2.2.9-0031",
            "pattern": "^[\\u0041]$",
            "flags": "u",
            "input_code_points": "0041",
            "expected_match": True,
            "spec_route": "compile_to_charset_character_escape",
        },
        {
            "case_family": "unicode_fixed_escape",
            "requirement_id": "ecma262-22.2.2.9-0031",
            "pattern": "^[\\u0041]$",
            "flags": "u",
            "input_code_points": "0075",
            "expected_match": False,
            "spec_route": "compile_to_charset_character_escape_negative",
        },
        {
            "case_family": "unicode_braced_escape",
            "requirement_id": "ecma262-22.2.2.9-0031",
            "pattern": "^[\\u{41}]$",
            "flags": "u",
            "input_code_points": "0041",
            "expected_match": True,
            "spec_route": "compile_to_charset_character_escape",
        },
        {
            "case_family": "range",
            "requirement_id": "ecma262-22.2.2.9-0013",
            "pattern": "^[a-c]$",
            "flags": "",
            "input_code_points": "0062",
            "expected_match": True,
            "spec_route": "compile_to_charset_character_range",
        },
        {
            "case_family": "range",
            "requirement_id": "ecma262-22.2.2.9-0013",
            "pattern": "^[a-c]$",
            "flags": "",
            "input_code_points": "0064",
            "expected_match": False,
            "spec_route": "character_set_matcher_found_false",
        },
        {
            "case_family": "range_union",
            "requirement_id": "ecma262-22.2.2.9-0014",
            "pattern": "^[a-cx]$",
            "flags": "",
            "input_code_points": "0078",
            "expected_match": True,
            "spec_route": "compile_to_charset_union",
        },
        {
            "case_family": "digit_escape",
            "requirement_id": "ecma262-22.2.2.9-0035",
            "pattern": "^[\\d]$",
            "flags": "",
            "input_code_points": "0035",
            "expected_match": True,
            "spec_route": "compile_to_charset_digit_escape",
        },
        {
            "case_family": "digit_escape",
            "requirement_id": "ecma262-22.2.2.9-0035",
            "pattern": "^[\\d]$",
            "flags": "",
            "input_code_points": "0061",
            "expected_match": False,
            "spec_route": "compile_to_charset_digit_escape_negative",
        },
        {
            "case_family": "not_digit_escape",
            "requirement_id": "ecma262-22.2.2.9-0039",
            "pattern": "^[\\D]$",
            "flags": "",
            "input_code_points": "0061",
            "expected_match": True,
            "spec_route": "compile_to_charset_not_digit_escape",
        },
        {
            "case_family": "not_digit_escape",
            "requirement_id": "ecma262-22.2.2.9-0039",
            "pattern": "^[\\D]$",
            "flags": "",
            "input_code_points": "0035",
            "expected_match": False,
            "spec_route": "compile_to_charset_not_digit_escape_negative",
        },
        {
            "case_family": "space_escape",
            "requirement_id": "ecma262-22.2.2.9-0043",
            "pattern": "^[\\s]$",
            "flags": "",
            "input_code_points": "0020",
            "expected_match": True,
            "spec_route": "compile_to_charset_space_escape",
        },
        {
            "case_family": "space_escape",
            "requirement_id": "ecma262-22.2.2.9-0043",
            "pattern": "^[\\s]$",
            "flags": "",
            "input_code_points": "0041",
            "expected_match": False,
            "spec_route": "compile_to_charset_space_escape_negative",
        },
        {
            "case_family": "not_space_escape",
            "requirement_id": "ecma262-22.2.2.9-0047",
            "pattern": "^[\\S]$",
            "flags": "",
            "input_code_points": "0041",
            "expected_match": True,
            "spec_route": "compile_to_charset_not_space_escape",
        },
        {
            "case_family": "not_space_escape",
            "requirement_id": "ecma262-22.2.2.9-0047",
            "pattern": "^[\\S]$",
            "flags": "",
            "input_code_points": "0020",
            "expected_match": False,
            "spec_route": "compile_to_charset_not_space_escape_negative",
        },
        {
            "case_family": "word_escape",
            "requirement_id": "ecma262-22.2.2.9-0052",
            "pattern": "^[\\w]$",
            "flags": "",
            "input_code_points": "005F",
            "expected_match": True,
            "spec_route": "compile_to_charset_word_escape",
        },
        {
            "case_family": "word_escape",
            "requirement_id": "ecma262-22.2.2.9-0052",
            "pattern": "^[\\w]$",
            "flags": "",
            "input_code_points": "002D",
            "expected_match": False,
            "spec_route": "compile_to_charset_word_escape_negative",
        },
        {
            "case_family": "not_word_escape",
            "requirement_id": "ecma262-22.2.2.9-0052",
            "pattern": "^[\\W]$",
            "flags": "",
            "input_code_points": "002D",
            "expected_match": True,
            "spec_route": "compile_to_charset_not_word_escape",
        },
        {
            "case_family": "not_word_escape",
            "requirement_id": "ecma262-22.2.2.9-0052",
            "pattern": "^[\\W]$",
            "flags": "",
            "input_code_points": "005F",
            "expected_match": False,
            "spec_route": "compile_to_charset_not_word_escape_negative",
        },
        {
            "case_family": "property_escape",
            "requirement_id": "ecma262-22.2.2.9-0053",
            "pattern": "^[\\p{ASCII}]$",
            "flags": "u",
            "input_code_points": "0041",
            "expected_match": True,
            "spec_route": "compile_to_charset_property_escape",
        },
        {
            "case_family": "property_escape",
            "requirement_id": "ecma262-22.2.2.9-0053",
            "pattern": "^[\\p{ASCII}]$",
            "flags": "u",
            "input_code_points": "0080",
            "expected_match": False,
            "spec_route": "compile_to_charset_property_escape_negative",
        },
        {
            "case_family": "negated_property_escape",
            "requirement_id": "ecma262-22.2.2.9-0055",
            "pattern": "^[\\P{ASCII}]$",
            "flags": "u",
            "input_code_points": "0080",
            "expected_match": True,
            "spec_route": "compile_to_charset_negated_property_escape",
        },
        {
            "case_family": "negated_property_escape",
            "requirement_id": "ecma262-22.2.2.9-0055",
            "pattern": "^[\\P{ASCII}]$",
            "flags": "u",
            "input_code_points": "0041",
            "expected_match": False,
            "spec_route": "compile_to_charset_negated_property_escape_negative",
        },
        {
            "case_family": "inverted_property_escape",
            "requirement_id": "ecma262-22.2.2.8-0009",
            "pattern": "^[^\\p{ASCII}]$",
            "flags": "u",
            "input_code_points": "0080",
            "expected_match": True,
            "spec_route": "compile_character_class_invert_property",
        },
        {
            "case_family": "inverted_property_escape",
            "requirement_id": "ecma262-22.2.2.8-0009",
            "pattern": "^[^\\p{ASCII}]$",
            "flags": "u",
            "input_code_points": "0041",
            "expected_match": False,
            "spec_route": "compile_character_class_invert_property_negative",
        },
        {
            "case_family": "complement",
            "requirement_id": "ecma262-22.2.2.8-0009",
            "pattern": "^[^a]$",
            "flags": "",
            "input_code_points": "0062",
            "expected_match": True,
            "spec_route": "compile_character_class_invert_true",
        },
        {
            "case_family": "complement",
            "requirement_id": "ecma262-22.2.2.8-0009",
            "pattern": "^[^a]$",
            "flags": "",
            "input_code_points": "0061",
            "expected_match": False,
            "spec_route": "character_set_matcher_invert_found_true_failure",
        },
        {
            "case_family": "backward_direction",
            "requirement_id": "ecma262-22.2.2.7.1-0011",
            "pattern": "(?<=[a-c])d",
            "flags": "",
            "input_code_points": "0062,0064",
            "expected_match": True,
            "spec_route": "character_set_matcher_backward",
        },
        {
            "case_family": "backward_direction",
            "requirement_id": "ecma262-22.2.2.7.1-0011",
            "pattern": "(?<=[a-c])d",
            "flags": "",
            "input_code_points": "0078,0064",
            "expected_match": False,
            "spec_route": "character_set_matcher_backward_negative",
        },
        {
            "case_family": "bounds_failure",
            "requirement_id": "ecma262-22.2.2.7.1-0013",
            "pattern": "^[a]$",
            "flags": "",
            "input_code_points": "",
            "expected_match": False,
            "spec_route": "character_set_matcher_forward_bounds_failure",
        },
    ]


def character_set_membership_rows(
    source_rows: list[dict[str, str]],
) -> list[dict[str, str]]:
    by_requirement_id = {row["requirement_id"]: row for row in source_rows}
    rows: list[dict[str, str]] = []
    for index, spec in enumerate(character_set_case_specs(), start=1):
        requirement_id = str(spec["requirement_id"])
        source_row = by_requirement_id.get(requirement_id)
        if source_row is None:
            raise SystemExit(
                f"missing UCD generated source row for {requirement_id}"
            )
        rows.append(
            {
                "case_id": f"ucd-character-set-membership:{index:04d}:{safe_id(str(spec['case_family']))}",
                "origin_requirement_id": requirement_id,
                "ucd_version": UCD_VERSION,
                "source_file": source_row["source_file"],
                "clause_id": source_row["clause_id"],
                "ucd_route": source_row["ucd_route"],
                "ucd_model_family": source_row["ucd_model_family"],
                "case_family": str(spec["case_family"]),
                "spec_route": str(spec["spec_route"]),
                "property_compile_pattern": str(spec["pattern"]),
                "property_compile_flags": str(spec["flags"]),
                "input_code_points": str(spec["input_code_points"]),
                "expected_match": bool_text(bool(spec["expected_match"])),
                "generation_reason": (
                    "ECMA-262 CharacterSetMatcher and CompileToCharSet routes "
                    "must produce observable membership behavior for empty "
                    "sets, complements, ranges, escapes, Unicode property "
                    "sets, direction, and bounds"
                ),
            }
        )

    ids = [row["case_id"] for row in rows]
    if len(rows) != EXPECTED_CHARACTER_SET_MEMBERSHIP_CASES:
        raise SystemExit(
            "expected "
            f"{EXPECTED_CHARACTER_SET_MEMBERSHIP_CASES} character-set "
            f"membership cases, got {len(rows)}"
        )
    if len(ids) != len(set(ids)):
        raise SystemExit("duplicate character-set membership case id")
    return rows


def case_folding_rows(
    source_rows: list[dict[str, str]],
    case_folding: dict[str, list[dict[str, object]]],
) -> list[dict[str, str]]:
    by_requirement_id = {row["requirement_id"]: row for row in source_rows}

    def source_row(requirement_id: str) -> dict[str, str]:
        row = by_requirement_id.get(requirement_id)
        if row is None:
            raise SystemExit(
                f"missing UCD generated source row for {requirement_id}"
            )
        return row

    def append_case(
        rows: list[dict[str, str]],
        *,
        index: int,
        requirement_id: str,
        case_family: str,
        fold_status: str,
        source: int,
        mapping: list[int],
        pattern: str,
        flags: str,
        input_code_points: list[int],
        expected_match: bool,
        generation_reason: str,
    ) -> None:
        row = source_row(requirement_id)
        rows.append(
            {
                "case_id": (
                    "ucd-case-folding:"
                    f"{index:05d}:"
                    f"{safe_id(case_family)}:"
                    f"{hex_code_point(source)}:"
                    f"{safe_id(code_point_list_text(mapping))}"
                ),
                "origin_requirement_id": requirement_id,
                "ucd_version": UCD_VERSION,
                "source_file": row["source_file"],
                "clause_id": row["clause_id"],
                "ucd_route": row["ucd_route"],
                "ucd_model_family": row["ucd_model_family"],
                "case_family": case_family,
                "fold_status": fold_status,
                "source_code_point": hex_code_point(source),
                "fold_code_points": code_point_list_text(mapping),
                "property_compile_pattern": pattern,
                "property_compile_flags": flags,
                "input_code_points": code_point_list_text(input_code_points),
                "expected_match": bool_text(expected_match),
                "generation_reason": generation_reason,
            }
        )

    rows: list[dict[str, str]] = []
    next_index = 1
    simple_rows = case_folding["simple"]
    full_rows = case_folding["full"]
    turkic_rows = case_folding["turkic"]

    for folding_row in simple_rows:
        source = int(folding_row["source"])
        status = str(folding_row["status"])
        mapping = list(folding_row["mapping"])
        target = int(mapping[0])
        append_case(
            rows,
            index=next_index,
            requirement_id="ecma262-22.2.2.7.3-0003",
            case_family="canonicalize_literal_forward",
            fold_status=status,
            source=source,
            mapping=mapping,
            pattern=f"^{unicode_escape(source)}$",
            flags="iu",
            input_code_points=[target],
            expected_match=True,
            generation_reason=(
                "Canonicalize must use simple/common CaseFolding.txt rows "
                "under Unicode IgnoreCase semantics"
            ),
        )
        next_index += 1
        append_case(
            rows,
            index=next_index,
            requirement_id="ecma262-22.2.2.7.3-0003",
            case_family="canonicalize_literal_reverse",
            fold_status=status,
            source=source,
            mapping=mapping,
            pattern=f"^{unicode_escape(target)}$",
            flags="iu",
            input_code_points=[source],
            expected_match=True,
            generation_reason=(
                "Runtime matching must compare canonicalized code points, "
                "not only apply a one-way source-to-target fold"
            ),
        )
        next_index += 1
        append_case(
            rows,
            index=next_index,
            requirement_id="ecma262-22.2.2.7.3-0005",
            case_family="canonicalize_literal_no_ignore",
            fold_status=status,
            source=source,
            mapping=mapping,
            pattern=f"^{unicode_escape(source)}$",
            flags="u",
            input_code_points=[target],
            expected_match=False,
            generation_reason=(
                "Canonicalize must return the original code point when "
                "IgnoreCase is false"
            ),
        )
        next_index += 1
        append_case(
            rows,
            index=next_index,
            requirement_id="ecma262-22.2.2.9.5-0007",
            case_family="maybe_simple_class_forward",
            fold_status=status,
            source=source,
            mapping=mapping,
            pattern=f"^[{unicode_escape(source)}]$",
            flags="iv",
            input_code_points=[target],
            expected_match=True,
            generation_reason=(
                "MaybeSimpleCaseFolding must include simple-folded class "
                "elements under UnicodeSets IgnoreCase semantics"
            ),
        )
        next_index += 1
        append_case(
            rows,
            index=next_index,
            requirement_id="ecma262-22.2.2.9.5-0002",
            case_family="maybe_simple_class_no_ignore",
            fold_status=status,
            source=source,
            mapping=mapping,
            pattern=f"^[{unicode_escape(source)}]$",
            flags="v",
            input_code_points=[target],
            expected_match=False,
            generation_reason=(
                "MaybeSimpleCaseFolding must leave class sets unchanged when "
                "IgnoreCase is false"
            ),
        )
        next_index += 1

    for folding_row in full_rows:
        source = int(folding_row["source"])
        status = str(folding_row["status"])
        mapping = list(folding_row["mapping"])
        append_case(
            rows,
            index=next_index,
            requirement_id="ecma262-22.2.2.7.3-0010",
            case_family="full_mapping_excluded",
            fold_status=status,
            source=source,
            mapping=mapping,
            pattern=f"^{unicode_escape(source)}$",
            flags="iu",
            input_code_points=mapping,
            expected_match=False,
            generation_reason=(
                "Canonicalize must not use full CaseFolding.txt mappings "
                "whose mapping length is not one code point"
            ),
        )
        next_index += 1

    for folding_row in turkic_rows:
        source = int(folding_row["source"])
        status = str(folding_row["status"])
        mapping = list(folding_row["mapping"])
        append_case(
            rows,
            index=next_index,
            requirement_id="ecma262-22.2.2.7.3-0003",
            case_family="turkic_mapping_excluded",
            fold_status=status,
            source=source,
            mapping=mapping,
            pattern=f"^{unicode_escape(source)}$",
            flags="iu",
            input_code_points=mapping,
            expected_match=False,
            generation_reason=(
                "Canonicalize must follow default simple/common folding and "
                "exclude Turkic CaseFolding.txt rows"
            ),
        )
        next_index += 1

    ids = [row["case_id"] for row in rows]
    if len(rows) != EXPECTED_CASE_FOLDING_CASES:
        raise SystemExit(
            f"expected {EXPECTED_CASE_FOLDING_CASES} case-folding cases, got "
            f"{len(rows)}"
        )
    if len(ids) != len(set(ids)):
        raise SystemExit("duplicate case-folding case id")
    return rows


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--cache", default="cache")
    parser.add_argument(
        "--requirement-mapping",
        default="cache/ecma262-regexp-requirement-mapping.tsv",
    )
    parser.add_argument("--ucd-dir", default=f"external/ucd/{UCD_VERSION}")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    cache = Path(args.cache)
    requirement_mapping = Path(args.requirement_mapping)
    ucd_dir = Path(args.ucd_dir)
    detail = cache / DETAIL_NAME
    property_value_detail = cache / PROPERTY_VALUE_DETAIL_NAME
    script_membership_detail = cache / SCRIPT_MEMBERSHIP_DETAIL_NAME
    general_category_membership_detail = cache / GENERAL_CATEGORY_MEMBERSHIP_DETAIL_NAME
    binary_property_membership_detail = cache / BINARY_PROPERTY_MEMBERSHIP_DETAIL_NAME
    character_class_property_membership_detail = (
        cache / CHARACTER_CLASS_PROPERTY_MEMBERSHIP_DETAIL_NAME
    )
    character_set_membership_detail = cache / CHARACTER_SET_MEMBERSHIP_DETAIL_NAME
    case_folding_detail = cache / CASE_FOLDING_DETAIL_NAME
    summary = cache / SUMMARY_NAME

    if not requirement_mapping.is_file():
        raise SystemExit(
            f"missing ECMA-262 requirement mapping at {requirement_mapping}; "
            "run tools/build_ecma262_regexp_requirement_mapping.py first"
        )
    if not ucd_dir.is_dir():
        raise SystemExit(f"missing UCD {UCD_VERSION} source directory at {ucd_dir}")

    checksums = validate_ucd_sources(ucd_dir)
    mapping_fields, mapping_rows = read_tsv(requirement_mapping)
    require_columns(
        requirement_mapping,
        mapping_fields,
        {
            "requirement_id",
            "clause_id",
            "clause_title",
            "source_file",
            "section_anchor",
            "requirement_kind",
            "requirement_local_id",
            "requirement_text",
            "semantic_family",
            "product_surface",
            "implementation_layer",
            "coverage_areas",
            "required_sources",
            "route_status",
        },
    )
    source_rows = selected_ucd_rows(mapping_rows)
    rows = [plan_row(row) for row in source_rows]
    validate_unique_ids(
        rows,
        fields=("case_id", "requirement_id"),
        field_label_prefix="UCD ",
    )
    case_folding = read_case_folding(ucd_dir / "CaseFolding.txt")
    value_aliases = read_property_value_aliases(ucd_dir / "PropertyValueAliases.txt")
    binary_property_aliases = read_binary_property_aliases(
        ucd_dir / "PropertyAliases.txt"
    )
    property_value_cases = property_value_rows(value_aliases)
    general_categories = read_general_categories(
        ucd_dir / "UnicodeData.txt",
        value_aliases["gc"],
    )
    selected_binary_aliases = selected_binary_property_aliases(
        rows,
        binary_property_aliases,
    )
    binary_properties = build_binary_properties(
        ucd_dir,
        selected_binary_aliases,
        general_categories,
    )
    general_category_membership_cases = general_category_membership_rows(
        value_aliases,
        general_categories,
    )
    scripts = read_scripts(ucd_dir / "Scripts.txt")
    script_extension_ranges, script_extension_entries = read_script_extensions(
        ucd_dir / "ScriptExtensions.txt",
        value_aliases["sc"],
    )
    script_membership_cases = script_membership_rows(
        value_aliases,
        scripts,
        script_extension_ranges,
        script_extension_entries,
    )
    binary_property_membership_cases = binary_property_membership_rows(
        rows,
        selected_binary_aliases,
        binary_properties,
    )
    character_class_property_membership_cases = (
        character_class_property_membership_rows(
            script_rows=script_membership_cases,
            general_category_rows=general_category_membership_cases,
            binary_property_rows=binary_property_membership_cases,
        )
    )
    character_set_membership_cases = character_set_membership_rows(rows)
    case_folding_cases = case_folding_rows(rows, case_folding)

    state_counts = Counter(row["case_state"] for row in rows)
    credit_counts = Counter(row["coverage_credit"] for row in rows)
    family_counts = Counter(row["ucd_model_family"] for row in rows)
    route_counts = Counter(row["ucd_route"] for row in rows)
    semantic_counts = Counter(row["semantic_family"] for row in rows)
    surface_counts = Counter(row["product_surface"] for row in rows)
    layer_counts = Counter(row["implementation_layer"] for row in rows)
    clause_counts = Counter(row["clause_id"] for row in rows)
    fixture_counts = Counter(row["fixture_kind"] for row in rows)
    alias_kind_counts = Counter(row["property_alias_kind"] for row in rows)
    parser_result_counts = Counter(row["property_expected_parser_result"] for row in rows)
    property_value_result_counts = Counter(
        row["expected_parser_result"] for row in property_value_cases
    )
    property_value_kind_counts = Counter(
        row["expression_kind"] for row in property_value_cases
    )
    script_membership_property_counts = Counter(
        row["canonical_property_name"] for row in script_membership_cases
    )
    script_membership_sample_counts = Counter(
        row["sample_kind"] for row in script_membership_cases
    )
    script_membership_expected_counts = Counter(
        row["expected_match"] for row in script_membership_cases
    )
    general_category_membership_expression_counts = Counter(
        row["expression_kind"] for row in general_category_membership_cases
    )
    general_category_membership_property_counts = Counter(
        row["property_name"] for row in general_category_membership_cases
    )
    general_category_membership_sample_counts = Counter(
        row["sample_kind"] for row in general_category_membership_cases
    )
    general_category_membership_expected_counts = Counter(
        row["expected_match"] for row in general_category_membership_cases
    )
    binary_property_membership_property_counts = Counter(
        row["canonical_property_name"] for row in binary_property_membership_cases
    )
    binary_property_membership_sample_counts = Counter(
        row["sample_kind"] for row in binary_property_membership_cases
    )
    binary_property_membership_expected_counts = Counter(
        row["expected_match"] for row in binary_property_membership_cases
    )
    character_class_property_membership_family_counts = Counter(
        row["source_membership_family"]
        for row in character_class_property_membership_cases
    )
    character_class_property_membership_inverted_counts = Counter(
        row["class_inverted"] for row in character_class_property_membership_cases
    )
    character_class_property_membership_expected_counts = Counter(
        row["expected_match"] for row in character_class_property_membership_cases
    )
    character_class_property_membership_flags_counts = Counter(
        row["property_compile_flags"]
        for row in character_class_property_membership_cases
    )
    character_class_property_membership_prefix_counts = Counter(
        row["escape_prefix"] for row in character_class_property_membership_cases
    )
    character_set_membership_family_counts = Counter(
        row["case_family"] for row in character_set_membership_cases
    )
    character_set_membership_route_counts = Counter(
        row["ucd_route"] for row in character_set_membership_cases
    )
    character_set_membership_expected_counts = Counter(
        row["expected_match"] for row in character_set_membership_cases
    )
    character_set_membership_flags_counts = Counter(
        row["property_compile_flags"] for row in character_set_membership_cases
    )
    case_folding_family_counts = Counter(
        row["case_family"] for row in case_folding_cases
    )
    case_folding_status_counts = Counter(
        row["fold_status"] for row in case_folding_cases
    )
    case_folding_expected_counts = Counter(
        row["expected_match"] for row in case_folding_cases
    )
    case_folding_flags_counts = Counter(
        row["property_compile_flags"] for row in case_folding_cases
    )
    case_folding_route_counts = Counter(
        row["ucd_route"] for row in case_folding_cases
    )

    credit_rows = sum(
        count for credit, count in credit_counts.items() if not credit.startswith("none")
    )

    summary_lines = [
        "ecma262_snapshot\t2026\n",
        f"input_requirement_mapping\t{requirement_mapping}\n",
        f"input_ucd_dir\t{ucd_dir}\n",
        f"ucd_version\t{UCD_VERSION}\n",
        f"ucd_required_files\t{len(REQUIRED_UCD_FILES)}\n",
        f"ucd_generated_case_rows\t{len(rows)}\n",
        f"coverage_credit_rows\t{credit_rows}\n",
        f"target_test_artifact\t{TARGET_TEST_ARTIFACT}\n",
        f"planned_detail_output\t{detail}\n",
        f"planned_property_value_detail_output\t{property_value_detail}\n",
        f"planned_summary_output\t{summary}\n",
        f"dry_run\t{bool_text(args.dry_run)}\n",
        f"property_value_case_rows\t{len(property_value_cases)}\n",
        f"planned_script_membership_detail_output\t{script_membership_detail}\n",
        f"script_membership_case_rows\t{len(script_membership_cases)}\n",
        "planned_general_category_membership_detail_output\t"
        f"{general_category_membership_detail}\n",
        "general_category_membership_case_rows\t"
        f"{len(general_category_membership_cases)}\n",
        "planned_binary_property_membership_detail_output\t"
        f"{binary_property_membership_detail}\n",
        "binary_property_membership_case_rows\t"
        f"{len(binary_property_membership_cases)}\n",
        "planned_character_class_property_membership_detail_output\t"
        f"{character_class_property_membership_detail}\n",
        "character_class_property_membership_case_rows\t"
        f"{len(character_class_property_membership_cases)}\n",
        "planned_character_set_membership_detail_output\t"
        f"{character_set_membership_detail}\n",
        "character_set_membership_case_rows\t"
        f"{len(character_set_membership_cases)}\n",
        f"planned_case_folding_detail_output\t{case_folding_detail}\n",
        f"case_folding_case_rows\t{len(case_folding_cases)}\n",
    ]
    for name, digest in sorted(checksums.items()):
        summary_lines.append(f"ucd_sha256_{name}\t{digest}\n")
    for name, count in sorted(state_counts.items()):
        summary_lines.append(f"case_state_{name}\t{count}\n")
    for name, count in sorted(credit_counts.items()):
        summary_lines.append(f"coverage_credit_{name}\t{count}\n")
    for name, count in sorted(clause_counts.items()):
        summary_lines.append(f"clause_id_{name}\t{count}\n")
    for name, count in sorted(family_counts.items()):
        summary_lines.append(f"ucd_model_family_{name}\t{count}\n")
    for name, count in sorted(route_counts.items()):
        summary_lines.append(f"ucd_route_{name}\t{count}\n")
    for name, count in sorted(semantic_counts.items()):
        summary_lines.append(f"semantic_family_{name}\t{count}\n")
    for name, count in sorted(surface_counts.items()):
        summary_lines.append(f"product_surface_{name}\t{count}\n")
    for name, count in sorted(layer_counts.items()):
        summary_lines.append(f"implementation_layer_{name}\t{count}\n")
    for name, count in sorted(fixture_counts.items()):
        summary_lines.append(f"fixture_kind_{name}\t{count}\n")
    for name, count in sorted(alias_kind_counts.items()):
        summary_lines.append(f"property_alias_kind_{name}\t{count}\n")
    for name, count in sorted(parser_result_counts.items()):
        summary_lines.append(f"property_expected_parser_result_{name}\t{count}\n")
    for name, count in sorted(property_value_result_counts.items()):
        summary_lines.append(f"property_value_expected_parser_result_{name}\t{count}\n")
    for name, count in sorted(property_value_kind_counts.items()):
        summary_lines.append(f"property_value_expression_kind_{name}\t{count}\n")
    for name, count in sorted(script_membership_property_counts.items()):
        summary_lines.append(f"script_membership_property_{name}\t{count}\n")
    for name, count in sorted(script_membership_sample_counts.items()):
        summary_lines.append(f"script_membership_sample_kind_{name}\t{count}\n")
    for name, count in sorted(script_membership_expected_counts.items()):
        summary_lines.append(f"script_membership_expected_match_{name}\t{count}\n")
    for name, count in sorted(general_category_membership_expression_counts.items()):
        summary_lines.append(
            f"general_category_membership_expression_kind_{name}\t{count}\n"
        )
    for name, count in sorted(general_category_membership_property_counts.items()):
        summary_lines.append(
            f"general_category_membership_property_{name or '<lone>'}\t{count}\n"
        )
    for name, count in sorted(general_category_membership_sample_counts.items()):
        summary_lines.append(
            f"general_category_membership_sample_kind_{name}\t{count}\n"
        )
    for name, count in sorted(general_category_membership_expected_counts.items()):
        summary_lines.append(
            f"general_category_membership_expected_match_{name}\t{count}\n"
        )
    for name, count in sorted(binary_property_membership_property_counts.items()):
        summary_lines.append(f"binary_property_membership_property_{name}\t{count}\n")
    for name, count in sorted(binary_property_membership_sample_counts.items()):
        summary_lines.append(f"binary_property_membership_sample_kind_{name}\t{count}\n")
    for name, count in sorted(binary_property_membership_expected_counts.items()):
        summary_lines.append(f"binary_property_membership_expected_match_{name}\t{count}\n")
    for name, count in sorted(
        character_class_property_membership_family_counts.items()
    ):
        summary_lines.append(
            "character_class_property_membership_source_family_"
            f"{name}\t{count}\n"
        )
    for name, count in sorted(
        character_class_property_membership_inverted_counts.items()
    ):
        summary_lines.append(
            "character_class_property_membership_class_inverted_"
            f"{name}\t{count}\n"
        )
    for name, count in sorted(
        character_class_property_membership_expected_counts.items()
    ):
        summary_lines.append(
            "character_class_property_membership_expected_match_"
            f"{name}\t{count}\n"
        )
    for name, count in sorted(
        character_class_property_membership_flags_counts.items()
    ):
        summary_lines.append(
            "character_class_property_membership_flags_"
            f"{name}\t{count}\n"
        )
    for name, count in sorted(
        character_class_property_membership_prefix_counts.items()
    ):
        summary_lines.append(
            "character_class_property_membership_escape_prefix_"
            f"{name}\t{count}\n"
        )
    for name, count in sorted(character_set_membership_family_counts.items()):
        summary_lines.append(
            f"character_set_membership_case_family_{name}\t{count}\n"
        )
    for name, count in sorted(character_set_membership_route_counts.items()):
        summary_lines.append(f"character_set_membership_ucd_route_{name}\t{count}\n")
    for name, count in sorted(character_set_membership_expected_counts.items()):
        summary_lines.append(
            f"character_set_membership_expected_match_{name}\t{count}\n"
        )
    for name, count in sorted(character_set_membership_flags_counts.items()):
        summary_lines.append(
            f"character_set_membership_flags_{name or '<none>'}\t{count}\n"
        )
    for name, count in sorted(case_folding_family_counts.items()):
        summary_lines.append(f"case_folding_case_family_{name}\t{count}\n")
    for name, count in sorted(case_folding_status_counts.items()):
        summary_lines.append(f"case_folding_fold_status_{name}\t{count}\n")
    for name, count in sorted(case_folding_expected_counts.items()):
        summary_lines.append(f"case_folding_expected_match_{name}\t{count}\n")
    for name, count in sorted(case_folding_flags_counts.items()):
        summary_lines.append(f"case_folding_flags_{name}\t{count}\n")
    for name, count in sorted(case_folding_route_counts.items()):
        summary_lines.append(f"case_folding_ucd_route_{name}\t{count}\n")

    if args.dry_run:
        print("".join(summary_lines), end="")
        return

    cache.mkdir(parents=True, exist_ok=True)
    fieldnames = [
        "case_id",
        "requirement_id",
        "clause_id",
        "clause_title",
        "source_file",
        "section_anchor",
        "requirement_kind",
        "requirement_local_id",
        "requirement_text",
        "semantic_family",
        "product_surface",
        "implementation_layer",
        "coverage_areas",
        "ucd_version",
        "ucd_model_family",
        "ucd_route",
        "ucd_files",
        "fixture_kind",
        "fixture_input",
        "property_alias_kind",
        "property_alias",
        "property_compile_body",
        "property_compile_pattern",
        "property_compile_flags",
        "property_expected_parser_result",
        "expected_observation",
        "expected_behavior",
        "coverage_credit",
        "case_state",
        "target_test_artifact",
        "exact_case_obligation",
        "next_action",
        "generation_reason",
    ]
    with detail.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, delimiter="\t", fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)
    property_value_fieldnames = [
        "case_id",
        "ucd_version",
        "source_file",
        "expression_kind",
        "escape_prefix",
        "property_name",
        "canonical_property_name",
        "value_source_property",
        "property_value_alias",
        "canonical_property_value",
        "property_compile_body",
        "property_compile_pattern",
        "property_compile_flags",
        "expected_parser_result",
        "generation_reason",
    ]
    with property_value_detail.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, delimiter="\t", fieldnames=property_value_fieldnames)
        writer.writeheader()
        writer.writerows(property_value_cases)
    script_membership_fieldnames = [
        "case_id",
        "ucd_version",
        "source_file",
        "expression_kind",
        "sample_kind",
        "escape_prefix",
        "property_name",
        "canonical_property_name",
        "property_value_alias",
        "canonical_property_value",
        "input_code_point",
        "property_compile_body",
        "property_compile_pattern",
        "property_compile_flags",
        "expected_match",
        "generation_reason",
    ]
    with script_membership_detail.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, delimiter="\t", fieldnames=script_membership_fieldnames)
        writer.writeheader()
        writer.writerows(script_membership_cases)
    general_category_membership_fieldnames = [
        "case_id",
        "ucd_version",
        "source_file",
        "expression_kind",
        "sample_kind",
        "escape_prefix",
        "property_name",
        "canonical_property_name",
        "property_value_alias",
        "canonical_property_value",
        "input_code_point",
        "property_compile_body",
        "property_compile_pattern",
        "property_compile_flags",
        "expected_match",
        "generation_reason",
    ]
    with general_category_membership_detail.open(
        "w",
        encoding="utf-8",
        newline="",
    ) as f:
        writer = csv.DictWriter(
            f,
            delimiter="\t",
            fieldnames=general_category_membership_fieldnames,
        )
        writer.writeheader()
        writer.writerows(general_category_membership_cases)
    binary_property_membership_fieldnames = [
        "case_id",
        "ucd_version",
        "source_file",
        "expression_kind",
        "sample_kind",
        "escape_prefix",
        "property_alias",
        "canonical_property_name",
        "input_code_point",
        "property_compile_body",
        "property_compile_pattern",
        "property_compile_flags",
        "expected_match",
        "generation_reason",
    ]
    with binary_property_membership_detail.open(
        "w",
        encoding="utf-8",
        newline="",
    ) as f:
        writer = csv.DictWriter(
            f,
            delimiter="\t",
            fieldnames=binary_property_membership_fieldnames,
        )
        writer.writeheader()
        writer.writerows(binary_property_membership_cases)
    character_class_property_membership_fieldnames = [
        "case_id",
        "origin_case_id",
        "ucd_version",
        "source_file",
        "source_membership_family",
        "expression_kind",
        "sample_kind",
        "class_inverted",
        "escape_prefix",
        "property_name",
        "property_alias",
        "canonical_property_name",
        "property_value_alias",
        "canonical_property_value",
        "input_code_point",
        "property_compile_body",
        "property_compile_pattern",
        "property_compile_flags",
        "expected_match",
        "generation_reason",
    ]
    with character_class_property_membership_detail.open(
        "w",
        encoding="utf-8",
        newline="",
    ) as f:
        writer = csv.DictWriter(
            f,
            delimiter="\t",
            fieldnames=character_class_property_membership_fieldnames,
        )
        writer.writeheader()
        writer.writerows(character_class_property_membership_cases)
    character_set_membership_fieldnames = [
        "case_id",
        "origin_requirement_id",
        "ucd_version",
        "source_file",
        "clause_id",
        "ucd_route",
        "ucd_model_family",
        "case_family",
        "spec_route",
        "property_compile_pattern",
        "property_compile_flags",
        "input_code_points",
        "expected_match",
        "generation_reason",
    ]
    with character_set_membership_detail.open(
        "w",
        encoding="utf-8",
        newline="",
    ) as f:
        writer = csv.DictWriter(
            f,
            delimiter="\t",
            fieldnames=character_set_membership_fieldnames,
        )
        writer.writeheader()
        writer.writerows(character_set_membership_cases)
    case_folding_fieldnames = [
        "case_id",
        "origin_requirement_id",
        "ucd_version",
        "source_file",
        "clause_id",
        "ucd_route",
        "ucd_model_family",
        "case_family",
        "fold_status",
        "source_code_point",
        "fold_code_points",
        "property_compile_pattern",
        "property_compile_flags",
        "input_code_points",
        "expected_match",
        "generation_reason",
    ]
    with case_folding_detail.open(
        "w",
        encoding="utf-8",
        newline="",
    ) as f:
        writer = csv.DictWriter(
            f,
            delimiter="\t",
            fieldnames=case_folding_fieldnames,
        )
        writer.writeheader()
        writer.writerows(case_folding_cases)
    summary.write_text("".join(summary_lines), encoding="utf-8")


if __name__ == "__main__":
    main()
