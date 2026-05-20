let repo_root () =
  let cwd = Sys.getcwd () in
  let rec climb dir =
    let candidate =
      Filename.concat dir
        "cache/ecma262-regexp-compile-parser-candidate-map.tsv"
    in
    if Sys.file_exists candidate then dir
    else
      let parent = Filename.dirname dir in
      if parent = dir then
        Alcotest.fail
          "cache/ecma262-regexp-compile-parser-candidate-map.tsv is missing; \
           run tools/map_ecma262_compile_parser_candidates.py"
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

let candidate_rows () =
  read_tsv [ "cache"; "ecma262-regexp-compile-parser-candidate-map.tsv" ]

let feature_rows () =
  read_tsv [ "cache"; "ecma262-regexp-compile-case-features.tsv" ]

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

let split_csv value = List.filter (( <> ) "") (String.split_on_char ',' value)
let has_csv value expected = List.exists (( = ) expected) (split_csv value)

let parse_int field_name row =
  match int_of_string_opt (field field_name row) with
  | Some value -> value
  | None ->
      Alcotest.failf "%s: %s is not an int: %S"
        (field "requirement_id" row)
        field_name (field field_name row)

let require_nonempty row field_name =
  if field field_name row = "" then
    Alcotest.failf "%s: %s is empty" (field "requirement_id" row) field_name

let test262_source_exists source_path =
  Sys.file_exists (path [ "external"; "test262"; source_path ])

let test_post_credit_candidate_map_manifest () =
  let rows = candidate_rows () in
  let features = feature_rows () in
  Alcotest.(check int) "post-credit candidate map rows" 0 (List.length rows);
  Alcotest.(check int) "compile feature rows" 729 (List.length features);
  let layer_counts = count_by "executable_layer" rows in
  check_count layer_counts "compile" 0;
  check_count layer_counts "parser" 0;
  let family_counts = count_by "mapping_family" rows in
  check_count family_counts "compile_literal_validity" 0;
  check_count family_counts "parser_grammar_production" 0;
  let state_counts = count_by "compile_candidate_state" rows in
  check_count state_counts "candidate_compile_cases_found" 0;
  check_count state_counts "needs_negative_or_local_exact_case" 0;
  let exactness_counts = count_by "candidate_exactness" rows in
  check_count exactness_counts "candidate_only_not_exact" 0;
  let rows_with_candidates =
    List.filter (fun row -> parse_int "compile_candidate_count" row > 0) rows
  in
  Alcotest.(check int)
    "rows with compile candidates" 0
    (List.length rows_with_candidates);
  Alcotest.(check int)
    "rows without compile candidates" 0
    (List.length rows - List.length rows_with_candidates);
  List.iter
    (fun row ->
      Alcotest.(check string)
        "ledger state" "open_requirement_to_test_mapping_missing"
        (field "ledger_state" row);
      Alcotest.(check string)
        "release gate" "blocking" (field "release_gate" row);
      Alcotest.(check string)
        "mapping state" "open_exact_case_selection"
        (field "mapping_state" row);
      Alcotest.(check string)
        "exact test case id" ""
        (field "exact_test_case_id" row);
      Alcotest.(check string)
        "exact test source" ""
        (field "exact_test_source" row);
      Alcotest.(check string)
        "expected behavior" ""
        (field "expected_behavior" row);
      Alcotest.(check string)
        "exactness case id" ""
        (field "exactness_case_id" row);
      Alcotest.(check string)
        "exactness coverage credit" ""
        (field "exactness_coverage_credit" row);
      Alcotest.(check string)
        "candidate exactness" "candidate_only_not_exact"
        (field "candidate_exactness" row);
      List.iter (require_nonempty row)
        [
          "requirement_id";
          "source_file";
          "section_anchor";
          "mapping_family";
          "executable_layer";
          "candidate_selector_tags";
          "compile_candidate_state";
          "compile_candidate_reason";
        ];
      let count = parse_int "compile_candidate_count" row in
      if count > 0 then begin
        require_nonempty row "compile_candidate_case_ids_sample";
        require_nonempty row "compile_candidate_sources_sample"
      end
      else begin
        Alcotest.(check string)
          "empty candidate id sample" ""
          (field "compile_candidate_case_ids_sample" row);
        Alcotest.(check string)
          "empty candidate source sample" ""
          (field "compile_candidate_sources_sample" row)
      end;
      if
        field "compile_candidate_state" row
        = "needs_negative_or_local_exact_case"
        && not
             (has_csv
                (field "candidate_selector_tags" row)
                "negative_syntax_needed")
      then
        Alcotest.failf "%s: negative/local row lacks negative selector"
          (field "requirement_id" row))
    rows;
  List.iter
    (fun row ->
      if
        not
          (String.starts_with ~prefix:"test262-compile:" (field "case_id" row))
      then
        Alcotest.failf "feature row has invalid case_id %S"
          (field "case_id" row);
      if not (test262_source_exists (field "source_path" row)) then
        Alcotest.failf "%s: missing test262 source %s" (field "case_id" row)
          (field "source_path" row);
      if not (has_csv (field "feature_tags" row) "accepted_literal") then
        Alcotest.failf "%s: feature row lacks accepted_literal"
          (field "case_id" row);
      if not (has_csv (field "feature_tags" row) "compile_positive") then
        Alcotest.failf "%s: feature row lacks compile_positive"
          (field "case_id" row))
    features

let () =
  Alcotest.run "ecma262-compile-parser-candidate-map"
    [
      ( "manifest",
        [
          Alcotest.test_case
            "post-credit compile/parser candidate map invariants" `Quick
            test_post_credit_candidate_map_manifest;
        ] );
    ]
