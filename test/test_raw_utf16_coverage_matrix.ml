let repo_root () =
  let cwd = Sys.getcwd () in
  let rec climb dir =
    let candidate = Filename.concat dir "cache/raw-utf16-coverage-matrix.tsv" in
    if Sys.file_exists candidate then dir
    else
      let parent = Filename.dirname dir in
      if parent = dir then
        Alcotest.fail
          "cache/raw-utf16-coverage-matrix.tsv is missing; rebuild the raw \
           UTF-16 coverage matrix"
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
        | exception End_of_file -> (header, List.rev acc)
      in
      rows [])

let read_summary rel =
  let file = path rel in
  let ic = open_in file in
  Fun.protect
    ~finally:(fun () -> close_in_noerr ic)
    (fun () ->
      let rec rows acc =
        match input_line ic with
        | line -> (
            match split_tsv_line line with
            | [ key; value ] -> rows ((key, value) :: acc)
            | _ -> Alcotest.failf "invalid summary line: %S" line)
        | exception End_of_file -> List.rev acc
      in
      rows [])

let field name row =
  match List.assoc_opt name row with
  | Some value -> value
  | None -> Alcotest.failf "missing TSV field %s" name

let matrix_header, matrix_rows =
  read_tsv [ "cache"; "raw-utf16-coverage-matrix.tsv" ]

let summary_rows () =
  read_summary [ "cache"; "raw-utf16-coverage-matrix.summary" ]

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
    key expected
    (Option.value (Hashtbl.find_opt counts key) ~default:0)

let summary_value key =
  match List.assoc_opt key (summary_rows ()) with
  | Some value -> value
  | None -> Alcotest.failf "missing summary key %s" key

let check_summary_int key expected =
  match int_of_string_opt (summary_value key) with
  | Some actual -> Alcotest.(check int) key expected actual
  | None ->
      Alcotest.failf "summary key %s is not an int: %S" key (summary_value key)

let artifact_exists artifact =
  artifact <> "" && Sys.file_exists (path [ artifact ])

let require_nonempty row field_name =
  if field field_name row = "" then
    Alcotest.failf "%s: %s is empty" (field "row_id" row) field_name

let require_empty row field_name =
  if field field_name row <> "" then
    Alcotest.failf "%s: %s must be empty" (field "row_id" row) field_name

let require_prefix row field_name prefix =
  if not (String.starts_with ~prefix (field field_name row)) then
    Alcotest.failf "%s: %s must start with %S, got %S" (field "row_id" row)
      field_name prefix (field field_name row)

let test_schema_and_counts () =
  let expected_header =
    [
      "row_id";
      "status";
      "layer";
      "api_route";
      "flag_family";
      "input_family";
      "pattern_family";
      "assertion_family";
      "expected_semantics";
      "executable_artifact";
      "executable_test_name";
      "executable_gate";
      "coverage_source";
      "open_reason";
      "next_action";
    ]
  in
  Alcotest.(check (list string)) "TSV header" expected_header matrix_header;
  Alcotest.(check int) "raw UTF-16 matrix rows" 35 (List.length matrix_rows);
  let status_counts = count_by "status" matrix_rows in
  check_count status_counts "covered" 32;
  check_count status_counts "open" 0;
  check_count status_counts "non_applicable_with_reason" 3;
  let route_counts = count_by "api_route" matrix_rows in
  check_count route_counts "exec_js" 16;
  check_count route_counts "search_js" 1;
  check_count route_counts "exec_instance_js" 3;
  check_count route_counts "iter_matches_js" 4;
  check_count route_counts "js_string_conversion" 1;
  check_count route_counts "raw_utf16_generator" 1;
  check_count route_counts "match_js" 1;
  check_count route_counts "match_all_js" 1;
  check_count route_counts "js_match_result_captures" 1;
  check_count route_counts "replace_adapter" 1;
  check_count route_counts "split_js" 1;
  check_count route_counts "escape_js" 1;
  check_count route_counts "public_api_policy" 3

let test_summary_matches_matrix () =
  check_summary_int "raw_utf16_coverage_matrix_rows" 35;
  check_summary_int "status_covered" 32;
  check_summary_int "status_open" 0;
  check_summary_int "status_non_applicable_with_reason" 3;
  check_summary_int "api_route_exec_js" 16;
  check_summary_int "api_route_search_js" 1;
  check_summary_int "api_route_exec_instance_js" 3;
  check_summary_int "api_route_iter_matches_js" 4;
  check_summary_int "api_route_js_string_conversion" 1;
  check_summary_int "api_route_raw_utf16_generator" 1;
  check_summary_int "api_route_match_js" 1;
  check_summary_int "api_route_match_all_js" 1;
  check_summary_int "api_route_js_match_result_captures" 1;
  check_summary_int "api_route_replace_adapter" 1;
  check_summary_int "api_route_split_js" 1;
  check_summary_int "api_route_escape_js" 1;
  check_summary_int "api_route_public_api_policy" 3;
  check_summary_int "covered_artifact_test_raw_utf16_escape_matrix_ml" 7;
  check_summary_int
    "covered_artifact_test_raw_utf16_negative_position_matrix_ml" 10;
  check_summary_int "covered_artifact_test_raw_utf16_result_slicing_matrix_ml" 7;
  check_summary_int "covered_artifact_test_api_ml" 2;
  check_summary_int "covered_artifact_test_raw_utf16_generated_cases_ml" 1;
  check_summary_int "covered_artifact_test_ecma262_match_adapter_ml" 1;
  check_summary_int "covered_artifact_test_ecma262_match_all_adapter_ml" 1;
  check_summary_int "covered_artifact_test_ecma262_split_adapter_ml" 1;
  check_summary_int "covered_artifact_test_ecma262_replace_adapter_ml" 1;
  check_summary_int "covered_artifact_test_ecma262_escape_adapter_ml" 1;
  Alcotest.(check string)
    "open rows require reason" "true"
    (summary_value "open_rows_require_reason");
  Alcotest.(check string)
    "covered rows require executable gate" "true"
    (summary_value "covered_rows_require_executable_gate");
  Alcotest.(check string)
    "non-applicable rows require reason" "true"
    (summary_value "non_applicable_rows_require_reason")

let test_row_invariants () =
  let ids = Hashtbl.create 64 in
  List.iter
    (fun row ->
      List.iter (require_nonempty row)
        [
          "row_id";
          "status";
          "layer";
          "api_route";
          "flag_family";
          "input_family";
          "pattern_family";
          "assertion_family";
          "expected_semantics";
          "coverage_source";
          "next_action";
        ];
      let row_id = field "row_id" row in
      if Hashtbl.mem ids row_id then Alcotest.failf "duplicate row_id %s" row_id;
      Hashtbl.add ids row_id ();
      require_prefix row "row_id" "raw-utf16-";
      let artifact = field "executable_artifact" row in
      if artifact <> "" && not (artifact_exists artifact) then
        Alcotest.failf "%s: missing artifact %s" row_id artifact;
      match field "status" row with
      | "covered" ->
          require_prefix row "row_id" "raw-utf16-covered-";
          require_nonempty row "executable_artifact";
          require_nonempty row "executable_test_name";
          require_nonempty row "executable_gate";
          require_empty row "open_reason";
          require_prefix row "executable_gate" "opam exec -- dune exec ";
          Alcotest.(check string)
            (row_id ^ ": next_action") "none" (field "next_action" row)
      | "open" ->
          require_prefix row "row_id" "raw-utf16-open-";
          require_empty row "executable_test_name";
          require_empty row "executable_gate";
          require_nonempty row "open_reason";
          if field "next_action" row = "none" then
            Alcotest.failf "%s: open row must have a concrete next_action"
              row_id
      | "non_applicable_with_reason" ->
          require_prefix row "row_id" "raw-utf16-nonapp-";
          require_empty row "executable_test_name";
          require_empty row "executable_gate";
          require_nonempty row "open_reason";
          Alcotest.(check string)
            (row_id ^ ": next_action") "none" (field "next_action" row)
      | status -> Alcotest.failf "%s: invalid status %S" row_id status)
    matrix_rows

let test_covered_artifact_counts () =
  let covered =
    List.filter (fun row -> field "status" row = "covered") matrix_rows
  in
  let counts = count_by "executable_artifact" covered in
  check_count counts "test/test_raw_utf16_escape_matrix.ml" 7;
  check_count counts "test/test_raw_utf16_negative_position_matrix.ml" 10;
  check_count counts "test/test_raw_utf16_result_slicing_matrix.ml" 7;
  check_count counts "test/test_api.ml" 2;
  check_count counts "test/test_raw_utf16_generated_cases.ml" 1;
  check_count counts "test/test_ecma262_match_adapter.ml" 1;
  check_count counts "test/test_ecma262_match_all_adapter.ml" 1;
  check_count counts "test/test_ecma262_split_adapter.ml" 1;
  check_count counts "test/test_ecma262_replace_adapter.ml" 1;
  check_count counts "test/test_ecma262_escape_adapter.ml" 1

let () =
  Alcotest.run "raw-utf16-coverage-matrix"
    [
      ( "manifest",
        [
          Alcotest.test_case "schema and counts" `Quick test_schema_and_counts;
          Alcotest.test_case "summary matches matrix" `Quick
            test_summary_matches_matrix;
          Alcotest.test_case "row invariants" `Quick test_row_invariants;
          Alcotest.test_case "covered artifact counts" `Quick
            test_covered_artifact_counts;
        ] );
    ]
