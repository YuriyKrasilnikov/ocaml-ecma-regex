let repo_root () =
  let cwd = Sys.getcwd () in
  let rec climb dir =
    let candidate = Filename.concat dir "cache/raw-utf16-generated-cases.tsv" in
    if Sys.file_exists candidate then dir
    else
      let parent = Filename.dirname dir in
      if parent = dir then
        Alcotest.fail
          "cache/raw-utf16-generated-cases.tsv is missing; run \
           tools/build_raw_utf16_generated_cases.py"
      else climb parent
  in
  climb cwd
;;

let path segments =
  List.fold_left Filename.concat (repo_root ()) segments
;;

let strip_trailing_cr value =
  let length = String.length value in
  if length > 0 && value.[length - 1] = '\r' then
    String.sub value 0 (length - 1)
  else value
;;

let split_tsv_line line =
  line |> strip_trailing_cr |> String.split_on_char '\t'
;;

let pad_to width fields =
  let rec loop fields =
    if List.length fields >= width then fields else loop (fields @ [ "" ])
  in
  loop fields
;;

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
         | exception End_of_file -> header, List.rev acc
       in
       rows [])
;;

let read_summary rel =
  let file = path rel in
  let ic = open_in file in
  Fun.protect
    ~finally:(fun () -> close_in_noerr ic)
    (fun () ->
       let rec rows acc =
         match input_line ic with
         | line ->
           (match split_tsv_line line with
            | [ key; value ] -> rows ((key, value) :: acc)
            | _ -> Alcotest.failf "invalid summary line: %S" line)
         | exception End_of_file -> List.rev acc
       in
       rows [])
;;

let field name row =
  match List.assoc_opt name row with
  | Some value -> value
  | None -> Alcotest.failf "missing TSV field %s" name
;;

let matrix_header, matrix_rows =
  read_tsv [ "cache"; "raw-utf16-generated-cases.tsv" ]
;;

let summary_rows () =
  read_summary [ "cache"; "raw-utf16-generated-cases.summary" ]
;;

let count_by field_name rows =
  let counts = Hashtbl.create 64 in
  List.iter
    (fun row ->
       let key = field field_name row in
       let count = Option.value (Hashtbl.find_opt counts key) ~default:0 in
       Hashtbl.replace counts key (count + 1))
    rows;
  counts
;;

let check_count counts key expected =
  Alcotest.(check int)
    key
    expected
    (Option.value (Hashtbl.find_opt counts key) ~default:0)
;;

let summary_value key =
  match List.assoc_opt key (summary_rows ()) with
  | Some value -> value
 | None -> Alcotest.failf "missing summary key %s" key
;;

let check_summary_int key expected =
  match int_of_string_opt (summary_value key) with
  | Some actual -> Alcotest.(check int) key expected actual
  | None -> Alcotest.failf "summary key %s is not an int: %S" key (summary_value key)
;;

let bool_field row field_name =
  match field field_name row with
  | "true" -> true
  | "false" -> false
  | value ->
    Alcotest.failf
      "%s: invalid boolean %s=%S"
      (field "case_id" row)
      field_name
      value
;;

let int_field row field_name =
  match int_of_string_opt (field field_name row) with
  | Some value -> value
  | None ->
    Alcotest.failf
      "%s: invalid int %s=%S"
      (field "case_id" row)
      field_name
      (field field_name row)
;;

let hex_unit row field_name value =
  match int_of_string_opt ("0x" ^ value) with
  | Some unit when unit >= 0 && unit <= 0xFFFF -> unit
  | Some unit ->
    Alcotest.failf
      "%s: UTF-16 unit out of range in %s=%S (%d)"
      (field "case_id" row)
      field_name
      value
      unit
  | None ->
    Alcotest.failf
      "%s: invalid UTF-16 unit in %s=%S"
      (field "case_id" row)
      field_name
      value
;;

let units_field row field_name =
  match field field_name row with
  | "" -> []
  | value ->
    value
    |> String.split_on_char ','
    |> List.map (hex_unit row field_name)
;;

let rows_with_route route =
  List.filter (fun row -> field "api_route" row = route) matrix_rows
;;

let flags_or_fail row =
  let source = field "flags" row in
  match Ecma_regex.flags_of_string source with
  | Ok flags -> flags
  | Error msg ->
    Alcotest.failf
      "%s: invalid generated flags %S: %s"
      (field "case_id" row)
      source
      msg
;;

let compile_or_fail row =
  let flags = flags_or_fail row in
  let pattern = field "pattern" row in
  match Ecma_regex.compile ~flags pattern with
  | Ok regexp -> regexp
  | Error msg ->
    Alcotest.failf
      "%s: compile %S /%s failed: %s"
      (field "case_id" row)
      pattern
      (field "flags" row)
      msg
;;

let js_string_of_row row =
  match Ecma_regex.js_string_of_utf16_code_units (units_field row "input_units") with
  | Ok input -> input
  | Error msg ->
    Alcotest.failf "%s: invalid generated UTF-16 input: %s" (field "case_id" row) msg
;;

let check_match_result row actual =
  let case_id = field "case_id" row in
  let expected_start = int_field row "expected_start_index" in
  let expected_end = int_field row "expected_end_index" in
  let expected_units = units_field row "expected_matched_units" in
  Alcotest.(check int) (case_id ^ ": start_index") expected_start actual.Ecma_regex.js_start_index;
  Alcotest.(check int) (case_id ^ ": end_index") expected_end actual.Ecma_regex.js_end_index;
  Alcotest.(check (list int))
    (case_id ^ ": matched UTF-16 units")
    expected_units
    (Ecma_regex.js_string_to_utf16_code_units actual.Ecma_regex.js_matched_text)
;;

let check_expected_result row actual =
  match bool_field row "expected_match", actual with
  | false, None -> ()
  | false, Some actual ->
    Alcotest.failf
      "%s: unexpected match at UTF-16 %d..%d"
      (field "case_id" row)
      actual.Ecma_regex.js_start_index
      actual.Ecma_regex.js_end_index
  | true, None -> Alcotest.failf "%s: expected a match" (field "case_id" row)
  | true, Some actual -> check_match_result row actual
;;

let test_schema_and_counts () =
  let expected_header =
    [ "case_id"
    ; "api_route"
    ; "generator_family"
    ; "flag_family"
    ; "input_family"
    ; "pattern_family"
    ; "assertion_family"
    ; "pattern"
    ; "flags"
    ; "input_units"
    ; "initial_last_index"
    ; "expected_match"
    ; "expected_start_index"
    ; "expected_end_index"
    ; "expected_matched_units"
    ; "expected_search"
    ; "expected_last_index"
    ; "expected_semantics"
    ]
  in
  Alcotest.(check (list string)) "TSV header" expected_header matrix_header;
  Alcotest.(check int) "generated case rows" 1625 (List.length matrix_rows);
  let route_counts = count_by "api_route" matrix_rows in
  check_count route_counts "exec_js" 802;
  check_count route_counts "search_js" 802;
  check_count route_counts "exec_instance_js" 16;
  check_count route_counts "iter_matches_js" 5;
  let family_counts = count_by "generator_family" matrix_rows in
  check_count family_counts "character_class_escape_cartesian" 1200;
  check_count family_counts "unicode_property_cartesian" 192;
  check_count family_counts "surrogate_literal_cartesian" 112;
  check_count family_counts "word_boundary_cartesian" 100;
  check_count family_counts "instance_position_cartesian" 16;
  check_count family_counts "iterator_advancement_cartesian" 5;
  let expected_counts = count_by "expected_match" matrix_rows in
  check_count expected_counts "true" 844;
  check_count expected_counts "false" 781
;;

let test_summary_matches_matrix () =
  check_summary_int "raw_utf16_generated_case_rows" 1625;
  check_summary_int "api_route_exec_js" 802;
  check_summary_int "api_route_search_js" 802;
  check_summary_int "api_route_exec_instance_js" 16;
  check_summary_int "api_route_iter_matches_js" 5;
  check_summary_int "generator_family_character_class_escape_cartesian" 1200;
  check_summary_int "generator_family_unicode_property_cartesian" 192;
  check_summary_int "generator_family_surrogate_literal_cartesian" 112;
  check_summary_int "generator_family_word_boundary_cartesian" 100;
  check_summary_int "generator_family_instance_position_cartesian" 16;
  check_summary_int "generator_family_iterator_advancement_cartesian" 5;
  check_summary_int "expected_match_true" 844;
  check_summary_int "expected_match_false" 781;
  Alcotest.(check string) "case IDs unique" "true" (summary_value "case_ids_unique");
  Alcotest.(check string)
    "rows have expected semantics"
    "true"
    (summary_value "rows_have_expected_semantics");
  Alcotest.(check string)
    "rows have input units"
    "true"
    (summary_value "rows_have_input_units")
;;

let test_row_invariants () =
  let ids = Hashtbl.create 2048 in
  List.iter
    (fun row ->
       let case_id = field "case_id" row in
       if Hashtbl.mem ids case_id then Alcotest.failf "duplicate case_id %s" case_id;
       Hashtbl.add ids case_id ();
       if not (String.starts_with ~prefix:"raw-utf16-generated-" case_id) then
         Alcotest.failf "%s: invalid generated case prefix" case_id;
       List.iter
         (fun field_name ->
            if field field_name row = "" then
              Alcotest.failf "%s: %s must be non-empty" case_id field_name)
         [ "api_route"
         ; "generator_family"
         ; "flag_family"
         ; "input_family"
         ; "pattern_family"
         ; "assertion_family"
         ; "input_units"
         ; "expected_match"
         ; "expected_semantics"
         ];
       ignore (bool_field row "expected_match");
       let input_units = units_field row "input_units" in
       if input_units = [] then Alcotest.failf "%s: input_units must not be empty" case_id;
       (match bool_field row "expected_match" with
        | true ->
          ignore (int_field row "expected_start_index");
          ignore (int_field row "expected_end_index")
        | false ->
          List.iter
            (fun field_name ->
               if field field_name row <> "" then
                 Alcotest.failf "%s: %s must be empty for no-match rows" case_id field_name)
            [ "expected_start_index"; "expected_end_index"; "expected_matched_units" ]);
       (match field "api_route" row with
        | "exec_js" ->
          if field "expected_search" row <> "" then
            Alcotest.failf "%s: exec_js expected_search must be empty" case_id;
          if field "initial_last_index" row <> "" || field "expected_last_index" row <> "" then
            Alcotest.failf "%s: exec_js lastIndex fields must be empty" case_id
        | "search_js" ->
          ignore (bool_field row "expected_search");
          if field "initial_last_index" row <> "" || field "expected_last_index" row <> "" then
            Alcotest.failf "%s: search_js lastIndex fields must be empty" case_id
        | "exec_instance_js" | "iter_matches_js" ->
          ignore (int_field row "initial_last_index");
          ignore (int_field row "expected_last_index");
          if field "expected_search" row <> "" then
            Alcotest.failf "%s: instance/iterator expected_search must be empty" case_id
        | route -> Alcotest.failf "%s: invalid api_route %S" case_id route))
    matrix_rows
;;

let test_exec_js_generated_cases () =
  rows_with_route "exec_js"
  |> List.iter (fun row ->
    let regexp = compile_or_fail row in
    let input = js_string_of_row row in
    check_expected_result row (Ecma_regex.exec_js regexp input))
;;

let test_search_js_generated_cases () =
  rows_with_route "search_js"
  |> List.iter (fun row ->
    let regexp = compile_or_fail row in
    let input = js_string_of_row row in
    let expected = bool_field row "expected_search" in
    Alcotest.(check bool)
      (field "case_id" row)
      expected
      (Ecma_regex.search_js regexp input))
;;

let test_exec_instance_js_generated_cases () =
  rows_with_route "exec_instance_js"
  |> List.iter (fun row ->
    let regexp = compile_or_fail row in
    let instance = Ecma_regex.instance regexp in
    let input = js_string_of_row row in
    Ecma_regex.set_last_index instance (int_field row "initial_last_index");
    check_expected_result row (Ecma_regex.exec_instance_js instance input);
    Alcotest.(check int)
      (field "case_id" row ^ ": last_index")
      (int_field row "expected_last_index")
      (Ecma_regex.last_index instance))
;;

let test_iter_matches_js_generated_cases () =
  rows_with_route "iter_matches_js"
  |> List.iter (fun row ->
    let regexp = compile_or_fail row in
    let instance = Ecma_regex.instance regexp in
    let input = js_string_of_row row in
    Ecma_regex.set_last_index instance (int_field row "initial_last_index");
    let iterator = Ecma_regex.iter_matches_js instance input in
    check_expected_result row (Ecma_regex.next_match_js iterator);
    Alcotest.(check int)
      (field "case_id" row ^ ": last_index")
      (int_field row "expected_last_index")
      (Ecma_regex.last_index instance))
;;

let () =
  Alcotest.run
    "raw-utf16-generated-cases"
    [ "manifest"
    , [ Alcotest.test_case "schema and counts" `Quick test_schema_and_counts
      ; Alcotest.test_case "summary matches matrix" `Quick test_summary_matches_matrix
      ; Alcotest.test_case "row invariants" `Quick test_row_invariants
      ]
    ; "public API"
    , [ Alcotest.test_case "exec_js generated cases" `Quick test_exec_js_generated_cases
      ; Alcotest.test_case "search_js generated cases" `Quick test_search_js_generated_cases
      ; Alcotest.test_case
          "exec_instance_js generated cases"
          `Quick
          test_exec_instance_js_generated_cases
      ; Alcotest.test_case
          "iter_matches_js generated cases"
          `Quick
          test_iter_matches_js_generated_cases
      ]
    ]
;;
