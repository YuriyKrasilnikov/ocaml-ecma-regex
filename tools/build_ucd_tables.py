#!/usr/bin/env python3
from __future__ import annotations

import argparse
from collections import defaultdict
from pathlib import Path


UCD_VERSION = "16.0.0"

ECMASCRIPT_BINARY_PROPERTY_ALIASES = [
    "ASCII",
    "ASCII_Hex_Digit",
    "AHex",
    "Alphabetic",
    "Alpha",
    "Any",
    "Assigned",
    "Bidi_Control",
    "Bidi_C",
    "Bidi_Mirrored",
    "Bidi_M",
    "Case_Ignorable",
    "CI",
    "Cased",
    "Changes_When_Casefolded",
    "CWCF",
    "Changes_When_Casemapped",
    "CWCM",
    "Changes_When_Lowercased",
    "CWL",
    "Changes_When_NFKC_Casefolded",
    "CWKCF",
    "Changes_When_Titlecased",
    "CWT",
    "Changes_When_Uppercased",
    "CWU",
    "Dash",
    "Default_Ignorable_Code_Point",
    "DI",
    "Deprecated",
    "Dep",
    "Diacritic",
    "Dia",
    "Emoji",
    "Emoji_Component",
    "EComp",
    "Emoji_Modifier",
    "EMod",
    "Emoji_Modifier_Base",
    "EBase",
    "Emoji_Presentation",
    "EPres",
    "Extended_Pictographic",
    "ExtPict",
    "Extender",
    "Ext",
    "Grapheme_Base",
    "Gr_Base",
    "Grapheme_Extend",
    "Gr_Ext",
    "Hex_Digit",
    "Hex",
    "IDS_Binary_Operator",
    "IDSB",
    "IDS_Trinary_Operator",
    "IDST",
    "ID_Continue",
    "IDC",
    "ID_Start",
    "IDS",
    "Ideographic",
    "Ideo",
    "Join_Control",
    "Join_C",
    "Logical_Order_Exception",
    "LOE",
    "Lowercase",
    "Lower",
    "Math",
    "Noncharacter_Code_Point",
    "NChar",
    "Pattern_Syntax",
    "Pat_Syn",
    "Pattern_White_Space",
    "Pat_WS",
    "Quotation_Mark",
    "QMark",
    "Radical",
    "Regional_Indicator",
    "RI",
    "Sentence_Terminal",
    "STerm",
    "Soft_Dotted",
    "SD",
    "Terminal_Punctuation",
    "Term",
    "Unified_Ideograph",
    "UIdeo",
    "Uppercase",
    "Upper",
    "Variation_Selector",
    "VS",
    "White_Space",
    "space",
    "XID_Continue",
    "XIDC",
    "XID_Start",
    "XIDS",
]

ECMASCRIPT_DERIVED_BINARY_PROPERTY_ALIASES = {
    "ASCII": "ASCII",
    "Any": "Any",
    "Assigned": "Assigned",
}


def parse_code_range(field: str) -> tuple[int, int]:
    if ".." in field:
        start, end = field.split("..", 1)
    else:
        start = end = field
    return int(start, 16), int(end, 16)


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


def read_property_value_aliases(path: Path) -> dict[str, dict[str, str]]:
    aliases: dict[str, dict[str, str]] = {"gc": {}, "sc": {}}
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
            if fields[0] not in aliases:
                continue
            property_code = fields[0]
            canonical = fields[2]
            for alias in fields[1:]:
                existing = aliases[property_code].get(alias)
                if existing is not None and existing != canonical:
                    raise SystemExit(
                        f"ambiguous {property_code} alias {alias}: "
                        f"{existing} vs {canonical}"
                    )
                aliases[property_code][alias] = canonical
    if len(aliases["gc"]) != 80:
        raise SystemExit(
            f"expected 80 General_Category aliases, got {len(aliases['gc'])}"
        )
    if len(aliases["sc"]) != 338:
        raise SystemExit(f"expected 338 Script aliases, got {len(aliases['sc'])}")
    return aliases


def read_binary_property_aliases(path: Path) -> dict[str, str]:
    unicode_aliases: dict[str, str] = dict(ECMASCRIPT_DERIVED_BINARY_PROPERTY_ALIASES)
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
                unicode_aliases[alias] = canonical

    aliases: dict[str, str] = {}
    for alias in ECMASCRIPT_BINARY_PROPERTY_ALIASES:
        canonical = unicode_aliases.get(alias)
        if canonical is None:
            raise SystemExit(f"missing ECMAScript binary property alias {alias}")
        aliases[alias] = canonical
    if len(aliases) != 98:
        raise SystemExit(f"expected 98 binary property aliases, got {len(aliases)}")
    return aliases


def read_simple_case_folding(path: Path) -> dict[int, int]:
    mappings: dict[int, int] = {}
    status_counts: dict[str, int] = defaultdict(int)
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
            status_counts[status] += 1
            if status not in {"C", "S"}:
                continue
            if len(mapping) != 1:
                raise SystemExit(
                    "simple/common CaseFolding.txt row must map to one code "
                    f"point at line {line_number}"
                )
            existing = mappings.get(source)
            if existing is not None and existing != mapping[0]:
                raise SystemExit(
                    f"ambiguous simple case folding for U+{source:04X}: "
                    f"U+{existing:04X} vs U+{mapping[0]:04X}"
                )
            mappings[source] = mapping[0]

    expected_counts = {"C": 1453, "S": 31, "F": 104, "T": 2}
    for status, expected in expected_counts.items():
        actual = status_counts.get(status, 0)
        if actual != expected:
            raise SystemExit(
                f"expected {expected} CaseFolding.txt status {status} rows, "
                f"got {actual}"
            )
    if len(mappings) != 1484:
        raise SystemExit(
            f"expected 1484 simple/common case folding mappings, got {len(mappings)}"
        )
    return mappings


def read_scripts(path: Path) -> dict[str, list[tuple[int, int]]]:
    ranges: dict[str, list[tuple[int, int]]] = defaultdict(list)
    with path.open(encoding="utf-8") as f:
        for line_number, line in enumerate(f, start=1):
            data = line.split("#", 1)[0].strip()
            if not data:
                continue
            fields = [field.strip() for field in data.split(";")]
            if len(fields) != 2:
                raise SystemExit(f"malformed Scripts.txt line {line_number}: {line!r}")
            ranges[fields[1]].append(parse_code_range(fields[0]))
    return dict(ranges)


def read_binary_property_ranges_file(
    path: Path,
    accepted_properties: set[str],
) -> dict[str, list[tuple[int, int]]]:
    ranges: dict[str, list[tuple[int, int]]] = defaultdict(list)
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
                ranges[property_name].append(parse_code_range(fields[0]))
    return dict(ranges)


def read_bidi_mirrored_ranges(path: Path) -> list[tuple[int, int]]:
    ranges: list[tuple[int, int]] = []
    pending_first: tuple[int, str] | None = None
    with path.open(encoding="utf-8") as f:
        for line_number, line in enumerate(f, start=1):
            fields = line.rstrip("\n").split(";")
            if len(fields) < 10:
                raise SystemExit(f"malformed UnicodeData.txt line {line_number}: {line!r}")
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
    aliases: dict[str, str],
) -> tuple[dict[str, list[tuple[int, int]]], list[tuple[int, int]]]:
    ranges: dict[str, list[tuple[int, int]]] = defaultdict(list)
    explicit: list[tuple[int, int]] = []
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
            explicit.append(code_range)
            for short_name in fields[1].split():
                canonical = aliases.get(short_name)
                if canonical is None:
                    raise SystemExit(
                        f"unknown ScriptExtensions alias {short_name} at line {line_number}"
                    )
                ranges[canonical].append(code_range)
    return dict(ranges), explicit


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


def read_general_categories(
    path: Path,
    aliases: dict[str, str],
) -> dict[str, list[tuple[int, int]]]:
    ranges: dict[str, list[tuple[int, int]]] = defaultdict(list)
    explicit: list[tuple[int, int]] = []
    pending_first: tuple[int, str] | None = None

    def add_range(start: int, end: int, category_code: str) -> None:
        canonical = aliases.get(category_code)
        if canonical is None:
            raise SystemExit(f"unknown General_Category value {category_code}")
        code_range = (start, end)
        ranges[canonical].append(code_range)
        explicit.append(code_range)

    with path.open(encoding="utf-8") as f:
        for line_number, line in enumerate(f, start=1):
            fields = line.rstrip("\n").split(";")
            if len(fields) < 3:
                raise SystemExit(f"malformed UnicodeData.txt line {line_number}: {line!r}")
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
    ranges[unassigned].extend(complement_ranges(explicit))
    for aggregate, components in GENERAL_CATEGORY_GROUPS.items():
        for component in components:
            ranges[aggregate].extend(ranges.get(component, []))
    canonical_values = set(aliases.values())
    missing = canonical_values.difference(ranges)
    if missing:
        raise SystemExit(
            "missing General_Category ranges: " + ", ".join(sorted(missing))
        )
    return dict(ranges)


def build_binary_properties(
    ucd_dir: Path,
    aliases: dict[str, str],
    general_categories: dict[str, list[tuple[int, int]]],
) -> dict[str, list[tuple[int, int]]]:
    accepted_properties = set(aliases.values())
    ranges: dict[str, list[tuple[int, int]]] = defaultdict(list)

    def add_file(file_name: str) -> None:
        for property_name, property_ranges in read_binary_property_ranges_file(
            ucd_dir / file_name,
            accepted_properties,
        ).items():
            ranges[property_name].extend(property_ranges)

    add_file("PropList.txt")
    add_file("DerivedCoreProperties.txt")
    add_file("DerivedNormalizationProps.txt")
    add_file("emoji/emoji-data.txt")
    ranges["Bidi_Mirrored"].extend(read_bidi_mirrored_ranges(ucd_dir / "UnicodeData.txt"))
    ranges["ASCII"].append((0x0000, 0x007F))
    ranges["Any"].append((0x0000, 0x10FFFF))
    ranges["Assigned"].extend(
        complement_ranges(general_categories.get("Unassigned", []))
    )

    missing = sorted(
        property_name for property_name in accepted_properties if property_name not in ranges
    )
    if missing:
        raise SystemExit("missing binary property ranges: " + ", ".join(missing))
    return dict(ranges)


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


def ocaml_string(value: str) -> str:
    return '"' + value.replace("\\", "\\\\").replace('"', '\\"') + '"'


def render_range_array(ranges: list[tuple[int, int]]) -> str:
    return "[| " + "; ".join(f"(0x{start:04X}, 0x{end:04X})" for start, end in ranges) + " |]"


def render_table(name: str, table: dict[str, list[tuple[int, int]]]) -> list[str]:
    lines = [f"let {name} = [|\n"]
    for script, ranges in sorted(table.items()):
        lines.append(
            f"  ({ocaml_string(script)}, {render_range_array(merged_ranges(ranges))});\n"
        )
    lines.append("|]\n\n")
    return lines


def render_aliases(name: str, aliases: dict[str, str]) -> list[str]:
    lines = [f"let {name} = [|\n"]
    for alias, canonical in sorted(aliases.items()):
        lines.append(f"  ({ocaml_string(alias)}, {ocaml_string(canonical)});\n")
    lines.append("|]\n\n")
    return lines


def simple_case_folding_classes(mappings: dict[int, int]) -> dict[int, list[int]]:
    classes: dict[int, set[int]] = defaultdict(set)
    for source, folded in mappings.items():
        classes[folded].add(source)
        classes[folded].add(folded)
    return {
        folded: sorted(code_points)
        for folded, code_points in classes.items()
    }


def render_code_point_array(code_points: list[int]) -> str:
    return "[| " + "; ".join(f"0x{code_point:04X}" for code_point in code_points) + " |]"


def render_simple_case_folding(mappings: dict[int, int]) -> list[str]:
    lines = ["let simple_case_fold code_point =\n", "  match code_point with\n"]
    for source, folded in sorted(mappings.items()):
        lines.append(f"  | 0x{source:04X} -> 0x{folded:04X}\n")
    lines.append("  | _ -> code_point\n\n")
    lines.append("let simple_case_fold_equivalence_classes = [|\n")
    for folded, code_points in sorted(simple_case_folding_classes(mappings).items()):
        lines.append(
            f"  (0x{folded:04X}, {render_code_point_array(code_points)});\n"
        )
    lines.append("|]\n\n")
    lines.extend(
        [
            "let simple_case_fold_equivalents code_point =\n",
            "  let folded = simple_case_fold code_point in\n",
            "  match Array.find_opt (fun (candidate, _) -> candidate = folded) simple_case_fold_equivalence_classes with\n",
            "  | Some (_, equivalents) -> Array.to_list equivalents\n",
            "  | None -> [ code_point ]\n\n",
        ]
    )
    return lines


def render(
    path: Path,
    gc_aliases: dict[str, str],
    binary_property_aliases: dict[str, str],
    sc_aliases: dict[str, str],
    general_categories,
    binary_properties,
    scripts,
    script_extensions,
    explicit,
    simple_case_folding,
) -> None:
    lines = [
        "(* Generated by tools/build_ucd_tables.py from UCD 16.0.0. *)\n",
        "(* Do not edit by hand. *)\n\n",
    ]
    lines.extend(render_aliases("general_category_value_aliases", gc_aliases))
    lines.extend(render_table("general_category_ranges", general_categories))
    lines.extend(render_aliases("binary_property_aliases", binary_property_aliases))
    lines.extend(render_table("binary_property_ranges", binary_properties))
    lines.extend(render_aliases("script_value_aliases", sc_aliases))
    lines.extend(render_table("script_ranges", scripts))
    lines.extend(render_table("script_extensions_explicit_ranges", script_extensions))
    lines.extend(render_simple_case_folding(simple_case_folding))
    script_any = [code_range for ranges in scripts.values() for code_range in ranges]
    lines.append(
        "let script_any_explicit_ranges = "
        + render_range_array(merged_ranges(script_any))
        + "\n\n"
    )
    lines.append(
        "let script_extensions_any_explicit_ranges = "
        + render_range_array(merged_ranges(explicit))
        + "\n\n"
    )
    lines.extend(
        [
            "let range_contains code_point (first, last) =\n",
            "  first <= code_point && code_point <= last\n\n",
            "let ranges_contain code_point ranges =\n",
            "  Array.exists (range_contains code_point) ranges\n\n",
            "let table_ranges name table =\n",
            "  match Array.find_opt (fun (candidate, _) -> String.equal candidate name) table with\n",
            "  | Some (_, ranges) -> Some ranges\n",
            "  | None -> None\n\n",
            "let general_category_value_canonical_name value =\n",
            "  match Array.find_opt (fun (alias, _) -> String.equal alias value) general_category_value_aliases with\n",
            "  | Some (_, canonical) -> Some canonical\n",
            "  | None -> None\n\n",
            "let general_category_matches value code_point =\n",
            "  match general_category_value_canonical_name value with\n",
            "  | Some canonical ->\n",
            "    (match table_ranges canonical general_category_ranges with\n",
            "     | Some ranges -> ranges_contain code_point ranges\n",
            "     | None -> false)\n",
            "  | None -> false\n\n",
            "let binary_property_canonical_name property =\n",
            "  match Array.find_opt (fun (alias, _) -> String.equal alias property) binary_property_aliases with\n",
            "  | Some (_, canonical) -> Some canonical\n",
            "  | None -> None\n\n",
            "let binary_property_matches property code_point =\n",
            "  match binary_property_canonical_name property with\n",
            "  | Some canonical ->\n",
            "    (match table_ranges canonical binary_property_ranges with\n",
            "     | Some ranges -> ranges_contain code_point ranges\n",
            "     | None -> false)\n",
            "  | None -> false\n\n",
            "let script_value_canonical_name value =\n",
            "  match Array.find_opt (fun (alias, _) -> String.equal alias value) script_value_aliases with\n",
            "  | Some (_, canonical) -> Some canonical\n",
            "  | None -> None\n\n",
            "let script_matches_canonical canonical code_point =\n",
            "  match table_ranges canonical script_ranges with\n",
            "  | Some ranges when String.equal canonical \"Unknown\" ->\n",
            "    ranges_contain code_point ranges\n",
            "    || not (ranges_contain code_point script_any_explicit_ranges)\n",
            "  | Some ranges -> ranges_contain code_point ranges\n",
            "  | None when String.equal canonical \"Unknown\" ->\n",
            "    not (ranges_contain code_point script_any_explicit_ranges)\n",
            "  | None -> false\n\n",
            "let script_matches value code_point =\n",
            "  match script_value_canonical_name value with\n",
            "  | Some canonical -> script_matches_canonical canonical code_point\n",
            "  | None -> false\n\n",
            "let script_extensions_matches value code_point =\n",
            "  match script_value_canonical_name value with\n",
            "  | None -> false\n",
            "  | Some canonical ->\n",
            "    match table_ranges canonical script_extensions_explicit_ranges with\n",
            "    | Some ranges when ranges_contain code_point ranges -> true\n",
            "    | _ when ranges_contain code_point script_extensions_any_explicit_ranges -> false\n",
            "    | _ -> script_matches_canonical canonical code_point\n",
        ]
    )
    path.write_text("".join(lines), encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--ucd-dir", default=f"external/ucd/{UCD_VERSION}")
    parser.add_argument("--output", default="lib/ecma_regex_ucd_tables.ml")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    ucd_dir = Path(args.ucd_dir)
    aliases = read_property_value_aliases(ucd_dir / "PropertyValueAliases.txt")
    binary_property_aliases = read_binary_property_aliases(
        ucd_dir / "PropertyAliases.txt"
    )
    simple_case_folding = read_simple_case_folding(ucd_dir / "CaseFolding.txt")
    general_categories = read_general_categories(
        ucd_dir / "UnicodeData.txt",
        aliases["gc"],
    )
    binary_properties = build_binary_properties(
        ucd_dir,
        binary_property_aliases,
        general_categories,
    )
    scripts = read_scripts(ucd_dir / "Scripts.txt")
    script_extensions, explicit = read_script_extensions(
        ucd_dir / "ScriptExtensions.txt",
        aliases["sc"],
    )
    summary = [
        f"ucd_version\t{UCD_VERSION}\n",
        f"general_category_aliases\t{len(aliases['gc'])}\n",
        f"general_category_values\t{len(general_categories)}\n",
        f"binary_property_aliases\t{len(binary_property_aliases)}\n",
        f"binary_property_values\t{len(binary_properties)}\n",
        f"simple_case_folding_mappings\t{len(simple_case_folding)}\n",
        f"script_aliases\t{len(aliases['sc'])}\n",
        f"script_values\t{len(scripts)}\n",
        f"script_extension_values\t{len(script_extensions)}\n",
        f"script_extension_explicit_ranges\t{len(explicit)}\n",
        f"output\t{args.output}\n",
    ]
    if args.dry_run:
        print("".join(summary), end="")
        return
    render(
        Path(args.output),
        aliases["gc"],
        binary_property_aliases,
        aliases["sc"],
        general_categories,
        binary_properties,
        scripts,
        script_extensions,
        explicit,
        simple_case_folding,
    )


if __name__ == "__main__":
    main()
