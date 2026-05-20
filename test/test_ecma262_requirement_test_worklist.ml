let repo_root () =
  let cwd = Sys.getcwd () in
  let rec climb dir =
    let candidate =
      Filename.concat dir "cache/ecma262-regexp-requirement-test-worklist.tsv"
    in
    if Sys.file_exists candidate then dir
    else
      let parent = Filename.dirname dir in
      if parent = dir then
        Alcotest.fail
          "cache/ecma262-regexp-requirement-test-worklist.tsv is missing; run \
           tools/map_ecma262_requirements_to_tests.py"
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

let worklist_rows () =
  read_tsv [ "cache"; "ecma262-regexp-requirement-test-worklist.tsv" ]

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

let require_nonempty row field_name =
  if field field_name row = "" then
    Alcotest.failf "%s: %s is empty" (field "requirement_id" row) field_name

let test_post_credit_worklist_manifest () =
  let rows = worklist_rows () in
  Alcotest.(check int) "post-credit worklist rows" 0 (List.length rows);
  let state_counts = count_by "mapping_state" rows in
  check_count state_counts "open_exact_case_selection" 0;
  check_count state_counts "open_manual_classification" 0;
  let ledger_counts = count_by "ledger_state" rows in
  check_count ledger_counts "open_requirement_to_test_mapping_missing" 0;
  check_count ledger_counts "covered_by_local_exact_compile_parser" 0;
  check_count ledger_counts "covered_by_match_engine_exact" 0;
  check_count ledger_counts "covered_by_reused_candidate_exact_compile_parser" 0;
  let layer_counts = count_by "executable_layer" rows in
  check_count layer_counts "compile" 0;
  check_count layer_counts "parser" 0;
  check_count layer_counts "match_engine" 0;
  check_count layer_counts "exec_result" 0;
  check_count layer_counts "literal_lexer" 0;
  check_count layer_counts "spec_model" 0;
  let family_counts = count_by "mapping_family" rows in
  check_count family_counts "compile_literal_validity" 0;
  check_count family_counts "parser_grammar_production" 0;
  check_count family_counts "literal_lexer_exact" 0;
  check_count family_counts "match_engine_alternation" 0;
  check_count family_counts "match_engine_assertions" 0;
  check_count family_counts "match_engine_atoms" 0;
  check_count family_counts "match_engine_backreferences" 0;
  check_count family_counts "match_engine_character_classes" 0;
  check_count family_counts "match_engine_concatenation" 0;
  check_count family_counts "match_engine_annex_b_annexB" 0;
  check_count family_counts "match_engine_pattern_semantics" 0;
  check_count family_counts "exec_result_matching" 0;
  check_count family_counts "exec_result_exec" 0;
  check_count family_counts "exec_result_instances" 0;
  check_count family_counts "match_engine_quantifiers" 0;
  check_count family_counts "spec_model_local_exact" 0;
  let artifact_counts = count_by "primary_test_artifact" rows in
  check_count artifact_counts "test/test_ecma262_compile_validity.ml" 0;
  check_count artifact_counts "test/test_ecma262_parser_grammar.ml" 0;
  check_count artifact_counts "test/test_ecma262_match_engine.ml" 0;
  check_count artifact_counts "test/test_ecma262_exec_result.ml" 0;
  check_count artifact_counts "test/test_ecma262_literal_lexer.ml" 0;
  check_count artifact_counts "test/test_ecma262_spec_model.ml" 0;
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
      List.iter (require_nonempty row)
        [
          "requirement_id";
          "source_file";
          "section_anchor";
          "mapping_family";
          "executable_layer";
          "test_obligation";
          "primary_test_artifact";
          "selector_source";
          "candidate_evidence";
          "test_mapping_reason";
        ];
      if field "mapping_family" row = "unknown_mapping_family" then
        Alcotest.failf "%s: mapping_family is unknown"
          (field "requirement_id" row))
    rows

let () =
  Alcotest.run "ecma262-requirement-test-worklist"
    [
      ( "manifest",
        [
          Alcotest.test_case "post-credit requirement-test worklist invariants"
            `Quick test_post_credit_worklist_manifest;
        ] );
    ]
