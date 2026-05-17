let repo_root () =
  let cwd = Sys.getcwd () in
  let rec climb dir =
    let candidate =
      Filename.concat dir "cache/ecma262-regexp-ucd-generated-cases.tsv"
    in
    if Sys.file_exists candidate then dir
    else
      let parent = Filename.dirname dir in
      if parent = dir then
        Alcotest.fail
          "cache/ecma262-regexp-ucd-generated-cases.tsv is missing; run \
           tools/build_ucd_regexp_tests.py"
      else climb parent
  in
  climb cwd

let path segments =
  List.fold_left Filename.concat (repo_root ()) segments

let strip_trailing_cr value =
  let length = String.length value in
  if length > 0 && value.[length - 1] = '\r' then
    String.sub value 0 (length - 1)
  else value

let split_tsv_line line =
  line
  |> strip_trailing_cr
  |> String.split_on_char '\t'

let pad_to width fields =
  let rec loop fields =
    if List.length fields >= width then fields else loop (fields @ [ "" ])
  in
  loop fields

let read_tsv rel =
  let file = path rel in
  let ic = open_in file in
  Fun.protect
    ~finally:(fun () -> close_in_noerr ic)
    (fun () ->
       let header = split_tsv_line (input_line ic) in
       let width = List.length header in
       let rec rows acc =
         match input_line ic with
         | line ->
           let fields = split_tsv_line line |> pad_to width in
           let row = List.combine header fields in
           rows (row :: acc)
         | exception End_of_file -> List.rev acc
       in
       rows [])

let field name row =
  match List.assoc_opt name row with
  | Some value -> value
  | None -> Alcotest.failf "missing TSV field %s" name

let case_rows () =
  read_tsv [ "cache"; "ecma262-regexp-ucd-generated-cases.tsv" ]

let property_value_rows () =
  read_tsv [ "cache"; "ecma262-regexp-ucd-property-value-cases.tsv" ]

let script_membership_rows () =
  read_tsv [ "cache"; "ecma262-regexp-ucd-script-membership-cases.tsv" ]

let general_category_membership_rows () =
  read_tsv [
    "cache";
    "ecma262-regexp-ucd-general-category-membership-cases.tsv";
  ]

let binary_property_membership_rows () =
  read_tsv [
    "cache";
    "ecma262-regexp-ucd-binary-property-membership-cases.tsv";
  ]

let character_class_property_membership_rows () =
  read_tsv [
    "cache";
    "ecma262-regexp-ucd-character-class-property-membership-cases.tsv";
  ]

let character_set_membership_rows () =
  read_tsv [
    "cache";
    "ecma262-regexp-ucd-character-set-membership-cases.tsv";
  ]

let case_folding_rows () =
  read_tsv [
    "cache";
    "ecma262-regexp-ucd-case-folding-cases.tsv";
  ]

let count_by field_name rows =
  let counts = Hashtbl.create 32 in
  List.iter
    (fun row ->
       let key = field field_name row in
       let count = Option.value (Hashtbl.find_opt counts key) ~default:0 in
       Hashtbl.replace counts key (count + 1))
    rows;
  counts

let check_count counts key expected =
  Alcotest.(check int)
    key
    expected
    (Option.value (Hashtbl.find_opt counts key) ~default:0)

let comma_split value =
  if value = "" then [] else String.split_on_char ',' value

let rows_with field_name value rows =
  List.filter (fun row -> field field_name row = value) rows

let bool_of_generated_field row field_name =
  match field field_name row with
  | "true" -> true
  | "false" -> false
  | value ->
    Alcotest.failf "%s: invalid boolean field %s=%S"
      (field "case_id" row)
      field_name
      value

let int_of_hex_field row field_name =
  try int_of_string ("0x" ^ field field_name row) with
  | Failure _ ->
    Alcotest.failf "%s: invalid hex field %s=%S"
      (field "case_id" row)
      field_name
      (field field_name row)

let int_of_hex_text row field_name value =
  try int_of_string ("0x" ^ value) with
  | Failure _ ->
    Alcotest.failf "%s: invalid hex field %s item %S"
      (field "case_id" row)
      field_name
      value

let utf8_of_code_point code_point =
  if code_point < 0 || code_point > 0x10FFFF then
    invalid_arg "Unicode code point out of range"
  else if code_point >= 0xD800 && code_point <= 0xDFFF then
    invalid_arg "surrogate code point"
  else if code_point <= 0x7F then
    String.make 1 (Char.chr code_point)
  else if code_point <= 0x7FF then
    String.init 2 (function
      | 0 -> Char.chr (0xC0 lor (code_point lsr 6))
      | _ -> Char.chr (0x80 lor (code_point land 0x3F)))
  else if code_point <= 0xFFFF then
    String.init 3 (function
      | 0 -> Char.chr (0xE0 lor (code_point lsr 12))
      | 1 -> Char.chr (0x80 lor ((code_point lsr 6) land 0x3F))
      | _ -> Char.chr (0x80 lor (code_point land 0x3F)))
  else
    String.init 4 (function
      | 0 -> Char.chr (0xF0 lor (code_point lsr 18))
      | 1 -> Char.chr (0x80 lor ((code_point lsr 12) land 0x3F))
      | 2 -> Char.chr (0x80 lor ((code_point lsr 6) land 0x3F))
      | _ -> Char.chr (0x80 lor (code_point land 0x3F)))

let utf8_of_code_points_field row field_name =
  let value = field field_name row in
  if value = "" then ""
  else
    value
    |> String.split_on_char ','
    |> List.map (fun item ->
      item
      |> int_of_hex_text row field_name
      |> utf8_of_code_point)
    |> String.concat ""

let source_exists source_file =
  source_file <> "" && Sys.file_exists (path [ source_file ])

let target_exists target =
  target <> "" && Sys.file_exists (path [ target ])

let ucd_file_exists name =
  Sys.file_exists (path [ "external"; "ucd"; "16.0.0"; name ])

let test_manifest () =
  let rows = case_rows () in
  Alcotest.(check int) "UCD generated rows" 366 (List.length rows);
  let state_counts = count_by "case_state" rows in
  check_count state_counts "covered_by_ucd_generated_tests" 366;
  let credit_counts = count_by "coverage_credit" rows in
  check_count credit_counts "ucd_generated_requirement_credit" 366;
  let semantic_counts = count_by "semantic_family" rows in
  check_count semantic_counts "assertions" 6;
  check_count semantic_counts "character_classes" 170;
  check_count semantic_counts "unicode" 24;
  check_count semantic_counts "unicode_case" 27;
  check_count semantic_counts "unicode_properties" 127;
  check_count semantic_counts "unicode_sets" 12;
  let surface_counts = count_by "product_surface" rows in
  check_count surface_counts "match_engine" 170;
  check_count surface_counts "unicode_tables" 196;
  let layer_counts = count_by "implementation_layer" rows in
  check_count layer_counts "matcher" 170;
  check_count layer_counts "unicode" 196;
  let route_counts = count_by "ucd_route" rows in
  check_count route_counts "ucd_property_aliases" 121;
  check_count route_counts "ucd_property_value_aliases" 6;
  check_count route_counts "ucd_case_folding" 22;
  check_count route_counts "ucd_word_characters" 5;
  check_count route_counts "ucd_word_char" 6;
  check_count route_counts "ucd_all_characters" 6;
  check_count route_counts "ucd_utf16_indexing" 18;
  check_count route_counts "ucd_compile_to_charset" 139;
  check_count route_counts "ucd_character_set_matcher" 22;
  check_count route_counts "ucd_character_class" 9;
  check_count route_counts "ucd_class_set_string" 12;
  let property_kind_counts = count_by "property_alias_kind" rows in
  check_count property_kind_counts "binary_property_alias" 98;
  check_count property_kind_counts "non_binary_property_alias" 6;
  check_count property_kind_counts "string_property" 7;
  check_count property_kind_counts "property_table_header" 3;
  check_count property_kind_counts "unicode_match_property_algorithm" 7;
  check_count property_kind_counts "not_property_alias_row" 245;
  let property_parser_counts = count_by "property_expected_parser_result" rows in
  check_count property_parser_counts "compile_ok" 111;
  check_count property_parser_counts "not_applicable" 255;
  let clause_counts = count_by "clause_id" rows in
  check_count clause_counts "22.2.2.4.1" 6;
  check_count clause_counts "22.2.2.7.1" 22;
  check_count clause_counts "22.2.2.7.3" 13;
  check_count clause_counts "22.2.2.8" 9;
  check_count clause_counts "22.2.2.9" 139;
  check_count clause_counts "22.2.2.9.3" 5;
  check_count clause_counts "22.2.2.9.4" 6;
  check_count clause_counts "22.2.2.9.5" 9;
  check_count clause_counts "22.2.2.9.7" 121;
  check_count clause_counts "22.2.2.9.8" 6;
  check_count clause_counts "22.2.2.10" 12;
  check_count clause_counts "22.2.7.3" 7;
  check_count clause_counts "22.2.7.4" 11;
  List.iter
    (fun row ->
       if
         not
           (String.starts_with
              ~prefix:("ucd-generated:" ^ field "requirement_id" row ^ ":")
              (field "case_id" row))
       then Alcotest.failf "%s: invalid UCD case id" (field "case_id" row);
       Alcotest.(check string)
         "UCD version"
         "16.0.0"
         (field "ucd_version" row);
       Alcotest.(check string)
         "expected behavior"
         "ucd_generated_requirement_covered"
         (field "expected_behavior" row);
       Alcotest.(check string)
         "next action"
         "none_covered_by_ucd_generated_tests"
         (field "next_action" row);
       if field "property_expected_parser_result" row = "compile_ok" then begin
         if field "property_alias" row = "" then
           Alcotest.failf "%s: empty executable property alias"
             (field "case_id" row);
         if field "property_compile_body" row = "" then
           Alcotest.failf "%s: empty executable property compile body"
             (field "case_id" row);
         if field "property_compile_pattern" row = "" then
           Alcotest.failf "%s: empty executable property compile pattern"
             (field "case_id" row);
         if field "property_compile_flags" row = "" then
           Alcotest.failf "%s: empty executable property compile flags"
             (field "case_id" row)
       end
       else begin
         Alcotest.(check string)
           "non-executable property alias"
           ""
           (field "property_alias" row);
         Alcotest.(check string)
           "non-executable property compile body"
           ""
           (field "property_compile_body" row);
         Alcotest.(check string)
           "non-executable property compile pattern"
           ""
           (field "property_compile_pattern" row);
         Alcotest.(check string)
           "non-executable property compile flags"
           ""
           (field "property_compile_flags" row)
       end;
       if field "ucd_model_family" row = "" then
         Alcotest.failf "%s: empty UCD model family" (field "case_id" row);
       if field "ucd_route" row = "" then
         Alcotest.failf "%s: empty UCD route" (field "case_id" row);
       if field "fixture_kind" row = "" then
         Alcotest.failf "%s: empty fixture kind" (field "case_id" row);
       if field "fixture_input" row = "" then
         Alcotest.failf "%s: empty fixture input" (field "case_id" row);
       if field "expected_observation" row = "" then
         Alcotest.failf "%s: empty expected observation" (field "case_id" row);
       if not (source_exists (field "source_file" row)) then
         Alcotest.failf "%s: missing ECMA source %s"
           (field "case_id" row)
           (field "source_file" row);
       if not (target_exists (field "target_test_artifact" row)) then
         Alcotest.failf "%s: missing target test artifact %s"
           (field "case_id" row)
           (field "target_test_artifact" row);
       List.iter
         (fun name ->
            if not (ucd_file_exists name) then
              Alcotest.failf "%s: missing UCD source file %s"
                (field "case_id" row)
                name)
         (comma_split (field "ucd_files" row)))
    rows

let test_required_ucd_sources_present () =
  List.iter
    (fun name ->
       if not (ucd_file_exists name) then
         Alcotest.failf "missing required UCD 16.0.0 source file %s" name)
    [
      "CaseFolding.txt";
      "DerivedCoreProperties.txt";
      "DerivedNormalizationProps.txt";
      "PropList.txt";
      "PropertyAliases.txt";
      "PropertyValueAliases.txt";
      "ScriptExtensions.txt";
      "Scripts.txt";
      "UnicodeData.txt";
      "emoji/emoji-data.txt";
    ]

let test_unicode_match_property_alias_compile_cases () =
  let rows =
    case_rows () |> rows_with "property_expected_parser_result" "compile_ok"
  in
  Alcotest.(check int)
    "executable property alias compile rows"
    111
    (List.length rows);
  List.iter
    (fun row ->
       let flags_source = field "property_compile_flags" row in
       let pattern = field "property_compile_pattern" row in
       match Ecma_regex.flags_of_string flags_source with
       | Error msg ->
         Alcotest.failf "%s: invalid generated flags %S: %s"
           (field "case_id" row)
           flags_source
           msg
       | Ok flags ->
         match Ecma_regex.compile ~flags pattern with
         | Ok _ -> ()
         | Error msg ->
           Alcotest.failf "%s: generated property alias pattern %S failed: %s"
             (field "case_id" row)
             pattern
             msg)
    rows

let test_unicode_match_property_value_manifest () =
  let rows = property_value_rows () in
  Alcotest.(check int) "property-value generated rows" 3212 (List.length rows);
  let result_counts = count_by "expected_parser_result" rows in
  check_count result_counts "compile_ok" 3184;
  check_count result_counts "compile_error" 28;
  let kind_counts = count_by "expression_kind" rows in
  check_count kind_counts "property_value" 3024;
  check_count kind_counts "lone_general_category_value" 160;
  check_count kind_counts "invalid_property_value" 24;
  check_count kind_counts "invalid_lone_property_value" 4;
  let prefix_counts = count_by "escape_prefix" rows in
  check_count prefix_counts "p" 1606;
  check_count prefix_counts "P" 1606;
  let seen = Hashtbl.create 2048 in
  List.iter
    (fun row ->
       Alcotest.(check string)
         "UCD version"
         "16.0.0"
         (field "ucd_version" row);
       if not (source_exists (field "source_file" row)) then
         Alcotest.failf "%s: missing UCD source %s"
           (field "case_id" row)
           (field "source_file" row);
       if field "property_compile_body" row = "" then
         Alcotest.failf "%s: empty property value compile body"
           (field "case_id" row);
       if field "property_compile_pattern" row = "" then
         Alcotest.failf "%s: empty property value compile pattern"
           (field "case_id" row);
       Alcotest.(check string)
         "property value compile flags"
         "u"
         (field "property_compile_flags" row);
       let pattern_key =
         field "property_compile_flags" row ^ "\x00"
         ^ field "property_compile_pattern" row
       in
       if Hashtbl.mem seen pattern_key then
         Alcotest.failf "%s: duplicate generated property value pattern"
           (field "case_id" row);
       Hashtbl.add seen pattern_key ())
    rows

let test_unicode_match_property_value_compile_cases () =
  let rows = property_value_rows () in
  List.iter
    (fun row ->
       let flags_source = field "property_compile_flags" row in
       let pattern = field "property_compile_pattern" row in
       match Ecma_regex.flags_of_string flags_source with
       | Error msg ->
         Alcotest.failf "%s: invalid generated flags %S: %s"
           (field "case_id" row)
           flags_source
           msg
       | Ok flags ->
         match
           (field "expected_parser_result" row, Ecma_regex.compile ~flags pattern)
         with
         | "compile_ok", Ok _ -> ()
         | "compile_error", Error _ -> ()
         | "compile_ok", Error msg ->
           Alcotest.failf "%s: generated property value pattern %S failed: %s"
             (field "case_id" row)
             pattern
             msg
         | "compile_error", Ok _ ->
           Alcotest.failf "%s: generated invalid property value pattern %S succeeded"
             (field "case_id" row)
             pattern
         | expected, _ ->
           Alcotest.failf "%s: unknown expected parser result %S"
             (field "case_id" row)
             expected)
    rows

let test_unicode_script_membership_manifest () =
  let rows = script_membership_rows () in
  Alcotest.(check int) "Script membership generated rows" 12328 (List.length rows);
  let property_counts = count_by "canonical_property_name" rows in
  check_count property_counts "Script" 5392;
  check_count property_counts "Script_Extensions" 6936;
  let sample_counts = count_by "sample_kind" rows in
  check_count sample_counts "script_positive" 2688;
  check_count sample_counts "script_negative" 2704;
  check_count sample_counts "script_extensions_explicit_positive" 1544;
  check_count sample_counts "script_extensions_fallback_positive" 2688;
  check_count sample_counts "script_extensions_negative" 2704;
  let expected_counts = count_by "expected_match" rows in
  check_count expected_counts "true" 6164;
  check_count expected_counts "false" 6164;
  let flags_counts = count_by "property_compile_flags" rows in
  check_count flags_counts "u" 6164;
  check_count flags_counts "v" 6164;
  let prefix_counts = count_by "escape_prefix" rows in
  check_count prefix_counts "p" 6164;
  check_count prefix_counts "P" 6164;
  let seen = Hashtbl.create 16384 in
  List.iter
    (fun row ->
       Alcotest.(check string)
         "UCD version"
         "16.0.0"
         (field "ucd_version" row);
       if Hashtbl.mem seen (field "case_id" row) then
         Alcotest.failf "%s: duplicate Script membership case id"
           (field "case_id" row);
       Hashtbl.add seen (field "case_id" row) ();
       if not (source_exists (field "source_file" row)) then
         Alcotest.failf "%s: missing UCD source %s"
           (field "case_id" row)
           (field "source_file" row);
       ignore (int_of_hex_field row "input_code_point");
       ignore (bool_of_generated_field row "expected_match");
       if field "property_compile_body" row = "" then
         Alcotest.failf "%s: empty Script membership compile body"
           (field "case_id" row);
       if field "property_compile_pattern" row = "" then
         Alcotest.failf "%s: empty Script membership compile pattern"
           (field "case_id" row);
       if field "property_value_alias" row = "" then
         Alcotest.failf "%s: empty Script membership value alias"
           (field "case_id" row);
       if field "canonical_property_value" row = "" then
         Alcotest.failf "%s: empty Script membership canonical value"
           (field "case_id" row))
    rows

let test_unicode_script_membership_match_cases () =
  let rows = script_membership_rows () in
  let cache = Hashtbl.create 8192 in
  let compiled row =
    let flags_source = field "property_compile_flags" row in
    let pattern = field "property_compile_pattern" row in
    let key = flags_source ^ "\x00" ^ pattern in
    match Hashtbl.find_opt cache key with
    | Some regexp -> regexp
    | None ->
      let flags =
        match Ecma_regex.flags_of_string flags_source with
        | Ok flags -> flags
        | Error msg ->
          Alcotest.failf "%s: invalid generated flags %S: %s"
            (field "case_id" row)
            flags_source
            msg
      in
      let regexp =
        match Ecma_regex.compile ~flags pattern with
        | Ok regexp -> regexp
        | Error msg ->
          Alcotest.failf "%s: generated Script membership pattern %S failed: %s"
            (field "case_id" row)
            pattern
            msg
      in
      Hashtbl.add cache key regexp;
      regexp
  in
  List.iter
    (fun row ->
       let input = utf8_of_code_point (int_of_hex_field row "input_code_point") in
       let expected = bool_of_generated_field row "expected_match" in
       let actual =
         try Ecma_regex.search (compiled row) input with
         | Invalid_argument msg ->
           Alcotest.failf "%s: Script membership search failed: %s"
             (field "case_id" row)
             msg
       in
       Alcotest.(check bool) (field "case_id" row) expected actual)
    rows

let test_unicode_general_category_membership_manifest () =
  let rows = general_category_membership_rows () in
  Alcotest.(check int)
    "General_Category membership generated rows"
    1896
    (List.length rows);
  let expression_counts = count_by "expression_kind" rows in
  check_count expression_counts "general_category_property_value" 1264;
  check_count expression_counts "lone_general_category_value_membership" 632;
  let property_counts = count_by "property_name" rows in
  check_count property_counts "General_Category" 632;
  check_count property_counts "gc" 632;
  check_count property_counts "" 632;
  let sample_counts = count_by "sample_kind" rows in
  check_count sample_counts "general_category_positive" 936;
  check_count sample_counts "general_category_negative" 960;
  let expected_counts = count_by "expected_match" rows in
  check_count expected_counts "true" 948;
  check_count expected_counts "false" 948;
  let flags_counts = count_by "property_compile_flags" rows in
  check_count flags_counts "u" 948;
  check_count flags_counts "v" 948;
  let prefix_counts = count_by "escape_prefix" rows in
  check_count prefix_counts "p" 948;
  check_count prefix_counts "P" 948;
  let seen = Hashtbl.create 2048 in
  List.iter
    (fun row ->
       Alcotest.(check string)
         "UCD version"
         "16.0.0"
         (field "ucd_version" row);
       if Hashtbl.mem seen (field "case_id" row) then
         Alcotest.failf "%s: duplicate General_Category membership case id"
           (field "case_id" row);
       Hashtbl.add seen (field "case_id" row) ();
       if not (source_exists (field "source_file" row)) then
         Alcotest.failf "%s: missing UCD source %s"
           (field "case_id" row)
           (field "source_file" row);
       ignore (int_of_hex_field row "input_code_point");
       ignore (bool_of_generated_field row "expected_match");
       if field "property_compile_body" row = "" then
         Alcotest.failf "%s: empty General_Category membership compile body"
           (field "case_id" row);
       if field "property_compile_pattern" row = "" then
         Alcotest.failf "%s: empty General_Category membership compile pattern"
           (field "case_id" row);
       if field "property_value_alias" row = "" then
         Alcotest.failf "%s: empty General_Category membership value alias"
           (field "case_id" row);
       if field "canonical_property_value" row = "" then
         Alcotest.failf "%s: empty General_Category membership canonical value"
           (field "case_id" row))
    rows

let test_unicode_general_category_membership_match_cases () =
  let rows = general_category_membership_rows () in
  let cache = Hashtbl.create 1024 in
  let compiled row =
    let flags_source = field "property_compile_flags" row in
    let pattern = field "property_compile_pattern" row in
    let key = flags_source ^ "\x00" ^ pattern in
    match Hashtbl.find_opt cache key with
    | Some regexp -> regexp
    | None ->
      let flags =
        match Ecma_regex.flags_of_string flags_source with
        | Ok flags -> flags
        | Error msg ->
          Alcotest.failf "%s: invalid generated flags %S: %s"
            (field "case_id" row)
            flags_source
            msg
      in
      let regexp =
        match Ecma_regex.compile ~flags pattern with
        | Ok regexp -> regexp
        | Error msg ->
          Alcotest.failf
            "%s: generated General_Category membership pattern %S failed: %s"
            (field "case_id" row)
            pattern
            msg
      in
      Hashtbl.add cache key regexp;
      regexp
  in
  List.iter
    (fun row ->
       let input = utf8_of_code_point (int_of_hex_field row "input_code_point") in
       let expected = bool_of_generated_field row "expected_match" in
       let actual =
         try Ecma_regex.search (compiled row) input with
         | Invalid_argument msg ->
           Alcotest.failf "%s: General_Category membership search failed: %s"
             (field "case_id" row)
             msg
       in
       Alcotest.(check bool) (field "case_id" row) expected actual)
    rows

let test_unicode_binary_property_membership_manifest () =
  let rows = binary_property_membership_rows () in
  Alcotest.(check int)
    "binary property membership generated rows"
    780
    (List.length rows);
  let property_counts = count_by "canonical_property_name" rows in
  Alcotest.(check int)
    "binary property canonical property count"
    53
    (Hashtbl.length property_counts);
  check_count property_counts "Any" 4;
  let sample_counts = count_by "sample_kind" rows in
  check_count sample_counts "binary_property_positive" 392;
  check_count sample_counts "binary_property_negative" 388;
  let expected_counts = count_by "expected_match" rows in
  check_count expected_counts "true" 390;
  check_count expected_counts "false" 390;
  let flags_counts = count_by "property_compile_flags" rows in
  check_count flags_counts "u" 390;
  check_count flags_counts "v" 390;
  let prefix_counts = count_by "escape_prefix" rows in
  check_count prefix_counts "p" 390;
  check_count prefix_counts "P" 390;
  let seen = Hashtbl.create 1024 in
  List.iter
    (fun row ->
       Alcotest.(check string)
         "UCD version"
         "16.0.0"
         (field "ucd_version" row);
       if Hashtbl.mem seen (field "case_id" row) then
         Alcotest.failf "%s: duplicate binary property membership case id"
           (field "case_id" row);
       Hashtbl.add seen (field "case_id" row) ();
       if not (source_exists (field "source_file" row)) then
         Alcotest.failf "%s: missing source %s"
           (field "case_id" row)
           (field "source_file" row);
       ignore (int_of_hex_field row "input_code_point");
       ignore (bool_of_generated_field row "expected_match");
       if field "property_compile_body" row = "" then
         Alcotest.failf "%s: empty binary property compile body"
           (field "case_id" row);
       if field "property_compile_pattern" row = "" then
         Alcotest.failf "%s: empty binary property compile pattern"
           (field "case_id" row);
       if field "property_alias" row = "" then
         Alcotest.failf "%s: empty binary property alias"
           (field "case_id" row);
       if field "canonical_property_name" row = "" then
         Alcotest.failf "%s: empty binary canonical property name"
           (field "case_id" row))
    rows

let test_unicode_binary_property_membership_match_cases () =
  let rows = binary_property_membership_rows () in
  let cache = Hashtbl.create 256 in
  let compiled row =
    let flags_source = field "property_compile_flags" row in
    let pattern = field "property_compile_pattern" row in
    let key = flags_source ^ "\x00" ^ pattern in
    match Hashtbl.find_opt cache key with
    | Some regexp -> regexp
    | None ->
      let flags =
        match Ecma_regex.flags_of_string flags_source with
        | Ok flags -> flags
        | Error msg ->
          Alcotest.failf "%s: invalid generated flags %S: %s"
            (field "case_id" row)
            flags_source
            msg
      in
      let regexp =
        match Ecma_regex.compile ~flags pattern with
        | Ok regexp -> regexp
        | Error msg ->
          Alcotest.failf
            "%s: generated binary property membership pattern %S failed: %s"
            (field "case_id" row)
            pattern
            msg
      in
      Hashtbl.add cache key regexp;
      regexp
  in
  List.iter
    (fun row ->
       let input = utf8_of_code_point (int_of_hex_field row "input_code_point") in
       let expected = bool_of_generated_field row "expected_match" in
       let actual =
         try Ecma_regex.search (compiled row) input with
         | Invalid_argument msg ->
           Alcotest.failf "%s: binary property membership search failed: %s"
             (field "case_id" row)
             msg
       in
       Alcotest.(check bool) (field "case_id" row) expected actual)
    rows

let test_unicode_character_class_property_membership_manifest () =
  let rows = character_class_property_membership_rows () in
  Alcotest.(check int)
    "character-class property membership generated rows"
    30008
    (List.length rows);
  let family_counts = count_by "source_membership_family" rows in
  check_count family_counts "script_membership" 24656;
  check_count family_counts "general_category_membership" 3792;
  check_count family_counts "binary_property_membership" 1560;
  let inverted_counts = count_by "class_inverted" rows in
  check_count inverted_counts "false" 15004;
  check_count inverted_counts "true" 15004;
  let expected_counts = count_by "expected_match" rows in
  check_count expected_counts "true" 15004;
  check_count expected_counts "false" 15004;
  let flags_counts = count_by "property_compile_flags" rows in
  check_count flags_counts "u" 15004;
  check_count flags_counts "v" 15004;
  let prefix_counts = count_by "escape_prefix" rows in
  check_count prefix_counts "p" 15004;
  check_count prefix_counts "P" 15004;
  let seen = Hashtbl.create 32768 in
  List.iter
    (fun row ->
       Alcotest.(check string)
         "UCD version"
         "16.0.0"
         (field "ucd_version" row);
       if Hashtbl.mem seen (field "case_id" row) then
         Alcotest.failf "%s: duplicate character-class property case id"
           (field "case_id" row);
       Hashtbl.add seen (field "case_id" row) ();
       if field "origin_case_id" row = "" then
         Alcotest.failf "%s: empty origin case id" (field "case_id" row);
       if not (source_exists (field "source_file" row)) then
         Alcotest.failf "%s: missing source %s"
           (field "case_id" row)
           (field "source_file" row);
       ignore (int_of_hex_field row "input_code_point");
       ignore (bool_of_generated_field row "expected_match");
       ignore (bool_of_generated_field row "class_inverted");
       if field "property_compile_body" row = "" then
         Alcotest.failf "%s: empty character-class property compile body"
           (field "case_id" row);
       if field "property_compile_pattern" row = "" then
         Alcotest.failf "%s: empty character-class property compile pattern"
           (field "case_id" row);
       if field "canonical_property_name" row = "" then
         Alcotest.failf "%s: empty canonical property name"
           (field "case_id" row))
    rows

let test_unicode_character_class_property_membership_match_cases () =
  let rows = character_class_property_membership_rows () in
  let cache = Hashtbl.create 8192 in
  let compiled row =
    let flags_source = field "property_compile_flags" row in
    let pattern = field "property_compile_pattern" row in
    let key = flags_source ^ "\x00" ^ pattern in
    match Hashtbl.find_opt cache key with
    | Some regexp -> regexp
    | None ->
      let flags =
        match Ecma_regex.flags_of_string flags_source with
        | Ok flags -> flags
        | Error msg ->
          Alcotest.failf "%s: invalid generated flags %S: %s"
            (field "case_id" row)
            flags_source
            msg
      in
      let regexp =
        match Ecma_regex.compile ~flags pattern with
        | Ok regexp -> regexp
        | Error msg ->
          Alcotest.failf
            "%s: generated character-class property pattern %S failed: %s"
            (field "case_id" row)
            pattern
            msg
      in
      Hashtbl.add cache key regexp;
      regexp
  in
  List.iter
    (fun row ->
       let input = utf8_of_code_point (int_of_hex_field row "input_code_point") in
       let expected = bool_of_generated_field row "expected_match" in
       let actual =
         try Ecma_regex.search (compiled row) input with
         | Invalid_argument msg ->
           Alcotest.failf
             "%s: character-class property membership search failed: %s"
             (field "case_id" row)
             msg
       in
       Alcotest.(check bool) (field "case_id" row) expected actual)
    rows

let test_unicode_character_set_membership_manifest () =
  let rows = character_set_membership_rows () in
  Alcotest.(check int)
    "character-set membership generated rows"
    40
    (List.length rows);
  let route_counts = count_by "ucd_route" rows in
  check_count route_counts "ucd_compile_to_charset" 32;
  check_count route_counts "ucd_character_class" 5;
  check_count route_counts "ucd_character_set_matcher" 3;
  let expected_counts = count_by "expected_match" rows in
  check_count expected_counts "true" 22;
  check_count expected_counts "false" 18;
  let flags_counts = count_by "property_compile_flags" rows in
  check_count flags_counts "" 27;
  check_count flags_counts "u" 13;
  let family_counts = count_by "case_family" rows in
  check_count family_counts "empty_char_set" 1;
  check_count family_counts "empty_complement" 1;
  check_count family_counts "literal" 2;
  check_count family_counts "hyphen" 2;
  check_count family_counts "backspace_escape" 2;
  check_count family_counts "control_escape" 1;
  check_count family_counts "hex_escape" 2;
  check_count family_counts "unicode_fixed_escape" 2;
  check_count family_counts "unicode_braced_escape" 1;
  check_count family_counts "range" 2;
  check_count family_counts "range_union" 1;
  check_count family_counts "digit_escape" 2;
  check_count family_counts "not_digit_escape" 2;
  check_count family_counts "space_escape" 2;
  check_count family_counts "not_space_escape" 2;
  check_count family_counts "word_escape" 2;
  check_count family_counts "not_word_escape" 2;
  check_count family_counts "property_escape" 2;
  check_count family_counts "negated_property_escape" 2;
  check_count family_counts "inverted_property_escape" 2;
  check_count family_counts "complement" 2;
  check_count family_counts "backward_direction" 2;
  check_count family_counts "bounds_failure" 1;
  let seen = Hashtbl.create 64 in
  List.iter
    (fun row ->
       Alcotest.(check string)
         "UCD version"
         "16.0.0"
         (field "ucd_version" row);
       if Hashtbl.mem seen (field "case_id" row) then
         Alcotest.failf "%s: duplicate character-set case id"
           (field "case_id" row);
       Hashtbl.add seen (field "case_id" row) ();
       if field "origin_requirement_id" row = "" then
         Alcotest.failf "%s: empty origin requirement id" (field "case_id" row);
       if not (source_exists (field "source_file" row)) then
         Alcotest.failf "%s: missing source %s"
           (field "case_id" row)
           (field "source_file" row);
       ignore (utf8_of_code_points_field row "input_code_points");
       ignore (bool_of_generated_field row "expected_match");
       if field "property_compile_pattern" row = "" then
         Alcotest.failf "%s: empty character-set pattern"
           (field "case_id" row);
       if field "spec_route" row = "" then
         Alcotest.failf "%s: empty spec route" (field "case_id" row);
       if field "ucd_route" row = "" then
         Alcotest.failf "%s: empty UCD route" (field "case_id" row))
    rows

let test_unicode_character_set_membership_match_cases () =
  let rows = character_set_membership_rows () in
  let cache = Hashtbl.create 64 in
  let compiled row =
    let flags_source = field "property_compile_flags" row in
    let pattern = field "property_compile_pattern" row in
    let key = flags_source ^ "\x00" ^ pattern in
    match Hashtbl.find_opt cache key with
    | Some regexp -> regexp
    | None ->
      let flags =
        match Ecma_regex.flags_of_string flags_source with
        | Ok flags -> flags
        | Error msg ->
          Alcotest.failf "%s: invalid generated flags %S: %s"
            (field "case_id" row)
            flags_source
            msg
      in
      let regexp =
        match Ecma_regex.compile ~flags pattern with
        | Ok regexp -> regexp
        | Error msg ->
          Alcotest.failf
            "%s: generated character-set pattern %S failed: %s"
            (field "case_id" row)
            pattern
            msg
      in
      Hashtbl.add cache key regexp;
      regexp
  in
  List.iter
    (fun row ->
       let input = utf8_of_code_points_field row "input_code_points" in
       let expected = bool_of_generated_field row "expected_match" in
       let actual =
         try Ecma_regex.search (compiled row) input with
         | Invalid_argument msg ->
           Alcotest.failf "%s: character-set membership search failed: %s"
             (field "case_id" row)
             msg
       in
       Alcotest.(check bool) (field "case_id" row) expected actual)
    rows

let test_unicode_case_folding_manifest () =
  let rows = case_folding_rows () in
  Alcotest.(check int)
    "case-folding generated rows"
    7526
    (List.length rows);
  let family_counts = count_by "case_family" rows in
  check_count family_counts "canonicalize_literal_forward" 1484;
  check_count family_counts "canonicalize_literal_reverse" 1484;
  check_count family_counts "canonicalize_literal_no_ignore" 1484;
  check_count family_counts "maybe_simple_class_forward" 1484;
  check_count family_counts "maybe_simple_class_no_ignore" 1484;
  check_count family_counts "full_mapping_excluded" 104;
  check_count family_counts "turkic_mapping_excluded" 2;
  let status_counts = count_by "fold_status" rows in
  check_count status_counts "C" 7265;
  check_count status_counts "S" 155;
  check_count status_counts "F" 104;
  check_count status_counts "T" 2;
  let expected_counts = count_by "expected_match" rows in
  check_count expected_counts "true" 4452;
  check_count expected_counts "false" 3074;
  let flags_counts = count_by "property_compile_flags" rows in
  check_count flags_counts "iu" 3074;
  check_count flags_counts "u" 1484;
  check_count flags_counts "iv" 1484;
  check_count flags_counts "v" 1484;
  let route_counts = count_by "ucd_route" rows in
  check_count route_counts "ucd_case_folding" 7526;
  let model_counts = count_by "ucd_model_family" rows in
  check_count model_counts "canonicalize_model" 4558;
  check_count model_counts "maybe_simple_case_folding_model" 2968;
  let seen = Hashtbl.create 8192 in
  List.iter
    (fun row ->
       Alcotest.(check string)
         "UCD version"
         "16.0.0"
         (field "ucd_version" row);
       if Hashtbl.mem seen (field "case_id" row) then
         Alcotest.failf "%s: duplicate case-folding case id"
           (field "case_id" row);
       Hashtbl.add seen (field "case_id" row) ();
       if field "origin_requirement_id" row = "" then
         Alcotest.failf "%s: empty origin requirement id" (field "case_id" row);
       if not (source_exists (field "source_file" row)) then
         Alcotest.failf "%s: missing source %s"
           (field "case_id" row)
           (field "source_file" row);
       ignore (int_of_hex_field row "source_code_point");
       ignore (utf8_of_code_points_field row "fold_code_points");
       ignore (utf8_of_code_points_field row "input_code_points");
       ignore (bool_of_generated_field row "expected_match");
       if field "property_compile_pattern" row = "" then
         Alcotest.failf "%s: empty case-folding pattern" (field "case_id" row);
       if field "fold_status" row = "" then
         Alcotest.failf "%s: empty fold status" (field "case_id" row);
       if field "ucd_route" row <> "ucd_case_folding" then
         Alcotest.failf "%s: wrong UCD route %s"
           (field "case_id" row)
           (field "ucd_route" row))
    rows

let test_unicode_case_folding_match_cases () =
  let rows = case_folding_rows () in
  let cache = Hashtbl.create 8192 in
  let compiled row =
    let flags_source = field "property_compile_flags" row in
    let pattern = field "property_compile_pattern" row in
    let key = flags_source ^ "\x00" ^ pattern in
    match Hashtbl.find_opt cache key with
    | Some regexp -> regexp
    | None ->
      let flags =
        match Ecma_regex.flags_of_string flags_source with
        | Ok flags -> flags
        | Error msg ->
          Alcotest.failf "%s: invalid generated flags %S: %s"
            (field "case_id" row)
            flags_source
            msg
      in
      let regexp =
        match Ecma_regex.compile ~flags pattern with
        | Ok regexp -> regexp
        | Error msg ->
          Alcotest.failf
            "%s: generated case-folding pattern %S failed: %s"
            (field "case_id" row)
            pattern
            msg
      in
      Hashtbl.add cache key regexp;
      regexp
  in
  List.iter
    (fun row ->
       let input = utf8_of_code_points_field row "input_code_points" in
       let expected = bool_of_generated_field row "expected_match" in
       let actual =
         try Ecma_regex.search (compiled row) input with
         | Invalid_argument msg ->
           Alcotest.failf "%s: case-folding search failed: %s"
             (field "case_id" row)
             msg
       in
       Alcotest.(check bool) (field "case_id" row) expected actual)
    rows

let () =
  Alcotest.run "ecma262-ucd-generated-cases" [
    ("manifest", [
      Alcotest.test_case "manifest" `Quick test_manifest;
      Alcotest.test_case "required UCD sources present" `Quick
        test_required_ucd_sources_present;
      Alcotest.test_case "UnicodeMatchProperty aliases compile" `Quick
        test_unicode_match_property_alias_compile_cases;
      Alcotest.test_case "UnicodeMatchPropertyValue manifest" `Quick
        test_unicode_match_property_value_manifest;
      Alcotest.test_case "UnicodeMatchPropertyValue compile" `Quick
        test_unicode_match_property_value_compile_cases;
      Alcotest.test_case "Script membership manifest" `Quick
        test_unicode_script_membership_manifest;
      Alcotest.test_case "Script membership match" `Quick
        test_unicode_script_membership_match_cases;
      Alcotest.test_case "General_Category membership manifest" `Quick
        test_unicode_general_category_membership_manifest;
      Alcotest.test_case "General_Category membership match" `Quick
        test_unicode_general_category_membership_match_cases;
      Alcotest.test_case "binary property membership manifest" `Quick
        test_unicode_binary_property_membership_manifest;
      Alcotest.test_case "binary property membership match" `Quick
        test_unicode_binary_property_membership_match_cases;
      Alcotest.test_case "character-class property membership manifest" `Quick
        test_unicode_character_class_property_membership_manifest;
      Alcotest.test_case "character-class property membership match" `Quick
        test_unicode_character_class_property_membership_match_cases;
      Alcotest.test_case "character-set membership manifest" `Quick
        test_unicode_character_set_membership_manifest;
      Alcotest.test_case "character-set membership match" `Quick
        test_unicode_character_set_membership_match_cases;
      Alcotest.test_case "case folding manifest" `Quick
        test_unicode_case_folding_manifest;
      Alcotest.test_case "case folding match" `Quick
        test_unicode_case_folding_match_cases;
    ]);
  ]
