let repo_root () =
  let cwd = Sys.getcwd () in
  let rec climb dir =
    let candidate =
      Filename.concat dir "cache/test262-regexp-executable-cases.tsv"
    in
    if Sys.file_exists candidate then dir
    else
      let parent = Filename.dirname dir in
      if parent = dir then
        Alcotest.fail
          "cache/test262-regexp-executable-cases.tsv is missing; run \
           tools/extract_test262_regexp_executable_cases.py"
      else climb parent
  in
  climb cwd

let path segments = List.fold_left Filename.concat (repo_root ()) segments

let strip_trailing_cr value =
  let length = String.length value in
  if length > 0 && value.[length - 1] = '\r' then String.sub value 0 (length - 1)
  else value

let split_tsv_line line = line |> strip_trailing_cr |> String.split_on_char '\t'

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

let executable_rows () =
  read_tsv [ "cache"; "test262-regexp-executable-cases.tsv" ]

let count_by field_name rows =
  let counts = Hashtbl.create 16 in
  List.iter
    (fun row ->
      let key = field field_name row in
      let count = Option.value (Hashtbl.find_opt counts key) ~default:0 in
      Hashtbl.replace counts key (count + 1))
    rows;
  counts

let check_count counts key expected =
  Alcotest.(check int)
    key expected
    (Option.value (Hashtbl.find_opt counts key) ~default:0)

let string_contains haystack needle =
  let haystack_length = String.length haystack in
  let needle_length = String.length needle in
  let rec loop index =
    if needle_length = 0 then true
    else if index + needle_length > haystack_length then false
    else if String.sub haystack index needle_length = needle then true
    else loop (index + 1)
  in
  loop 0

let read_file rel =
  let file = path rel in
  let ic = open_in file in
  Fun.protect
    ~finally:(fun () -> close_in_noerr ic)
    (fun () ->
      let length = in_channel_length ic in
      really_input_string ic length)

let source_file row = [ "external"; "test262"; field "source_path" row ]

let target_exists row =
  let target = field "target_test_artifact" row in
  target <> "" && Sys.file_exists (path [ target ])

let decode_literal_source row =
  match field "literal_source_encoding" row with
  | "plain" -> field "literal_source" row
  | "escaped_line_feed" ->
      Alcotest.(check string)
        "line-feed encoded literal" "/\\<LF>/"
        (field "literal_source" row);
      "/\\\n/"
  | encoding ->
      Alcotest.failf "%s: unsupported literal source encoding %s"
        (field "case_id" row) encoding

let allowed_behaviors =
  [
    "literal_body_and_flags_reparsed";
    "literal_rejects_extended_flags";
    "regular_expression_literal_body_flags_observed";
    "regular_expression_body_first_char_chars_observed";
    "regular_expression_chars_empty_observed";
    "regular_expression_chars_recursive_observed";
    "regular_expression_first_char_nonterminator_observed";
    "regular_expression_first_char_backslash_sequence_observed";
    "regular_expression_first_char_class_observed";
    "regular_expression_char_nonterminator_observed";
    "regular_expression_char_backslash_sequence_observed";
    "regular_expression_char_class_observed";
    "regular_expression_backslash_sequence_nonterminator_observed";
    "regular_expression_nonterminator_rejects_line_terminator";
    "regular_expression_class_brackets_observed";
    "regular_expression_class_chars_empty_observed";
    "regular_expression_class_chars_recursive_observed";
    "regular_expression_class_char_nonterminator_observed";
    "regular_expression_class_char_backslash_sequence_observed";
    "regular_expression_flags_empty_observed";
    "regular_expression_flags_recursive_identifier_part_observed";
    "body_text_operation_source_text_observed";
    "body_text_production_literal_body_flags_observed";
    "body_text_returns_regular_expression_body_source_text";
    "regular_expression_literal_primary_expression_delegates_to_12_9_5";
  ]

let test_manifest () =
  let rows = executable_rows () in
  Alcotest.(check int) "test262 executable rows" 25 (List.length rows);
  let parser_counts = count_by "expected_parser_result" rows in
  check_count parser_counts "literal_parse_ok" 23;
  check_count parser_counts "literal_parse_error" 2;
  let compile_counts = count_by "expected_compile_result" rows in
  check_count compile_counts "compile_ok" 23;
  check_count compile_counts "not_applicable" 2;
  let credit_counts = count_by "coverage_credit" rows in
  check_count credit_counts "none_test262_literal_lexer_executable_planned" 25;
  let state_counts = count_by "case_state" rows in
  check_count state_counts "planned_not_executable" 25;
  let encoding_counts = count_by "literal_source_encoding" rows in
  check_count encoding_counts "plain" 24;
  check_count encoding_counts "escaped_line_feed" 1;
  let surface_counts = count_by "product_surface" rows in
  check_count surface_counts "literal_lexer" 24;
  check_count surface_counts "compile" 1;
  List.iter
    (fun row ->
      if
        not
          (String.starts_with
             ~prefix:
               ("test262-regexp-executable:" ^ field "requirement_id" row ^ ":")
             (field "case_id" row))
      then Alcotest.failf "%s: invalid case id" (field "case_id" row);
      if field "mapping_family" row <> "test262_literal_lexer" then
        Alcotest.failf "%s: invalid mapping family" (field "case_id" row);
      if field "executable_layer" row <> "literal_lexer" then
        Alcotest.failf "%s: invalid executable layer" (field "case_id" row);
      if
        field "next_action" row
        <> "materialize_test262_literal_lexer_exact_case"
      then Alcotest.failf "%s: invalid next action" (field "case_id" row);
      if not (target_exists row) then
        Alcotest.failf "%s: target test artifact missing: %s"
          (field "case_id" row)
          (field "target_test_artifact" row);
      if not (List.mem (field "expected_behavior" row) allowed_behaviors) then
        Alcotest.failf "%s: unsupported expected behavior %s"
          (field "case_id" row)
          (field "expected_behavior" row);
      let line =
        match int_of_string_opt (field "source_line" row) with
        | Some line -> line
        | None -> Alcotest.failf "%s: invalid source line" (field "case_id" row)
      in
      if line <= 0 then
        Alcotest.failf "%s: source line must be positive" (field "case_id" row);
      let source = source_file row in
      if not (Sys.file_exists (path source)) then
        Alcotest.failf "%s: source file missing: %s" (field "case_id" row)
          (field "source_path" row);
      let text = read_file source in
      if not (string_contains text (field "source_snippet" row)) then
        Alcotest.failf "%s: source snippet missing: %s" (field "case_id" row)
          (field "source_snippet" row))
    rows

let test_literal_parser_cases () =
  executable_rows ()
  |> List.iter (fun row ->
      let literal_source = decode_literal_source row in
      match field "expected_parser_result" row with
      | "literal_parse_ok" -> (
          match Ecma_regex.regexp_literal_of_string literal_source with
          | Error error ->
              Alcotest.failf "%s: literal parse failed: %s"
                (field "case_id" row) error
          | Ok literal -> (
              Alcotest.(check string)
                "literal pattern text"
                (field "expected_pattern_text" row)
                literal.pattern_text;
              Alcotest.(check string)
                "literal flag text"
                (field "expected_flag_text" row)
                literal.flag_text;
              match field "expected_compile_result" row with
              | "compile_ok" -> (
                  match
                    Ecma_regex.compile ~flags:literal.flags literal.pattern_text
                  with
                  | Ok _ -> ()
                  | Error error ->
                      Alcotest.failf "%s: compile-after-literal failed: %s"
                        (field "case_id" row) error)
              | "not_applicable" -> ()
              | result ->
                  Alcotest.failf "%s: unsupported compile result %s"
                    (field "case_id" row) result))
      | "literal_parse_error" -> (
          Alcotest.(check string)
            "parse-error compile result" "not_applicable"
            (field "expected_compile_result" row);
          match Ecma_regex.regexp_literal_of_string literal_source with
          | Error _ -> ()
          | Ok literal ->
              Alcotest.failf
                "%s: literal parse unexpectedly succeeded as /%s/%s"
                (field "case_id" row) literal.pattern_text literal.flag_text)
      | result ->
          Alcotest.failf "%s: unsupported parser result %s"
            (field "case_id" row) result)

let () =
  Alcotest.run "test262-regexp-executable-cases"
    [
      ("manifest", [ Alcotest.test_case "manifest" `Quick test_manifest ]);
      ( "literal-parser",
        [
          Alcotest.test_case "literal parser cases" `Quick
            test_literal_parser_cases;
        ] );
    ]
