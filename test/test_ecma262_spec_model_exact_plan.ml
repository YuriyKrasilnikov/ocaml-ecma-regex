module Core = Ecma_regex__Ecma_regex_core

let repo_root () =
  let cwd = Sys.getcwd () in
  let rec climb dir =
    let candidate =
      Filename.concat dir "cache/ecma262-regexp-spec-model-exact-plan.tsv"
    in
    if Sys.file_exists candidate then dir
    else
      let parent = Filename.dirname dir in
      if parent = dir then
        Alcotest.fail
          "cache/ecma262-regexp-spec-model-exact-plan.tsv is missing; run \
           tools/build_ecma262_regexp_spec_model_exact_plan.py"
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

let plan_rows () =
  read_tsv [ "cache"; "ecma262-regexp-spec-model-exact-plan.tsv" ]

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

let source_exists source_file =
  source_file <> "" && Sys.file_exists (path [ source_file ])

let target_exists target = target <> "" && Sys.file_exists (path [ target ])

let parse_int_field row name =
  match int_of_string_opt (field name row) with
  | Some value -> value
  | None ->
      Alcotest.failf "%s: invalid %s %S" (field "plan_id" row) name
        (field name row)

let planned_rows rows =
  List.filter
    (fun row ->
      field "plan_state" row = "planned_not_executable"
      && field "coverage_credit" row = "none_spec_model_exact_planned")
    rows

let array_contains value items = Array.exists (( = ) value) items

let test_exact_plan_manifest () =
  let rows = plan_rows () in
  Alcotest.(check int) "spec-model exact plan rows" 4 (List.length rows);
  Alcotest.(check int)
    "planned executable rows" 4
    (List.length (planned_rows rows));
  let state_counts = count_by "plan_state" rows in
  check_count state_counts "planned_not_executable" 4;
  let credit_counts = count_by "coverage_credit" rows in
  check_count credit_counts "none_spec_model_exact_planned" 4;
  let mapping_counts = count_by "mapping_family" rows in
  check_count mapping_counts "spec_model_local_exact" 4;
  let layer_counts = count_by "executable_layer" rows in
  check_count layer_counts "spec_model" 4;
  let subfamily_counts = count_by "spec_model_subfamily" rows in
  check_count subfamily_counts "lexical_grammar_source_model" 1;
  check_count subfamily_counts "syntactic_token_stream_policy" 1;
  check_count subfamily_counts "regexp_grammar_pattern_model" 1;
  check_count subfamily_counts "grammar_notation_boundary_model" 1;
  let route_counts = count_by "spec_model_route" rows in
  check_count route_counts "source_character_goal_symbols" 1;
  check_count route_counts "token_stream_boundary_policy" 1;
  check_count route_counts "source_character_pattern_goal" 1;
  check_count route_counts "lexical_regexp_shared_productions" 1;
  let observability_counts = count_by "observability_status" rows in
  check_count observability_counts "internal_spec_model_observable" 4;
  let target_counts = count_by "target_test_artifact" rows in
  check_count target_counts "test/test_ecma262_spec_model_exact_plan.ml" 4;
  List.iter
    (fun row ->
      if
        not
          (String.starts_with ~prefix:"spec-model-exact:"
             (field "exact_case_id" row))
      then
        Alcotest.failf "%s: exact_case_id has wrong prefix"
          (field "plan_id" row);
      if not (source_exists (field "source_file" row)) then
        Alcotest.failf "%s: missing ECMA source %s" (field "plan_id" row)
          (field "source_file" row);
      if not (target_exists (field "target_test_artifact" row)) then
        Alcotest.failf "%s: missing target test artifact %s"
          (field "plan_id" row)
          (field "target_test_artifact" row);
      List.iter
        (fun name ->
          if field name row = "" then
            Alcotest.failf "%s: %s is empty" (field "plan_id" row) name)
        [
          "spec_model_subfamily";
          "spec_model_route";
          "exact_case_family";
          "model_scenario";
          "source_text";
          "expected_source_code_point_count";
          "expected_utf16_code_unit_length";
          "expected_lexical_goal_symbols";
          "expected_regexp_goal_symbol";
          "expected_regexp_clause";
          "expected_behavior";
          "expected_model_field";
          "exact_case_obligation";
          "observability_reason";
          "next_action";
        ];
      Alcotest.(check string)
        "next action" "materialize_spec_model_exact_case"
        (field "next_action" row))
    rows

let check_model_field row (observation : Core.spec_model_observation) =
  let expected_model_field = field "expected_model_field" row in
  if
    not
      (array_contains expected_model_field
         observation.Core.observed_model_fields)
  then
    Alcotest.failf "%s: model field %S was not observed" (field "plan_id" row)
      expected_model_field;
  match expected_model_field with
  | "lexical_grammar_source_character_goal_model_observed" ->
      Alcotest.(check bool)
        "lexical terminal model" true
        observation.Core.lexical_grammar_terminal_model_observed;
      Alcotest.(check bool)
        "lexical goal symbols" true
        observation.Core.lexical_grammar_goal_symbols_observed;
      Alcotest.(check bool)
        "source code point model" true
        observation.Core.source_character_code_point_model_observed
  | "syntactic_token_stream_boundary_policy_observed" ->
      Alcotest.(check bool)
        "syntactic token stream policy" true
        observation.Core.syntactic_token_stream_policy_observed
  | "regexp_grammar_pattern_source_model_observed" ->
      Alcotest.(check bool)
        "regexp terminal model" true
        observation.Core.regexp_grammar_terminal_model_observed;
      Alcotest.(check bool)
        "regexp Pattern goal" true
        observation.Core.regexp_grammar_pattern_goal_observed;
      Alcotest.(check bool)
        "regexp translates to pattern" true
        observation.Core.regexp_grammar_translates_to_pattern_observed
  | "lexical_regexp_grammar_notation_boundary_observed" ->
      Alcotest.(check bool)
        "double-colon notation" true
        observation.Core.grammar_double_colon_notation_observed;
      Alcotest.(check bool)
        "shared productions policy" true
        observation.Core.grammar_shared_productions_policy_observed
  | model_field ->
      Alcotest.failf "%s: unsupported expected_model_field %S"
        (field "plan_id" row) model_field

let check_spec_model_case row =
  let observation =
    Core.inspect_spec_model
      ~model_scenario:(field "model_scenario" row)
      (field "source_text" row)
  in
  check_model_field row observation;
  Alcotest.(check string)
    "source text" (field "source_text" row) observation.Core.source_text;
  Alcotest.(check bool)
    "source fixture is ASCII" true
    observation.Core.source_character_fixture_is_ascii;
  Alcotest.(check int)
    "source code point count"
    (parse_int_field row "expected_source_code_point_count")
    observation.Core.source_code_point_count;
  Alcotest.(check int)
    "source UTF-16 code unit length"
    (parse_int_field row "expected_utf16_code_unit_length")
    observation.Core.source_utf16_code_unit_length;
  Alcotest.(check string)
    "lexical goal symbols"
    (field "expected_lexical_goal_symbols" row)
    (String.concat ","
       (Array.to_list observation.Core.lexical_grammar_goal_symbols));
  Alcotest.(check string)
    "regexp goal symbol"
    (field "expected_regexp_goal_symbol" row)
    observation.Core.regexp_grammar_goal_symbol;
  Alcotest.(check string)
    "regexp grammar clause"
    (field "expected_regexp_clause" row)
    observation.Core.regexp_grammar_clause

let test_exact_cases () =
  List.iter check_spec_model_case (planned_rows (plan_rows ()))

let () =
  Alcotest.run "ecma262-spec-model-exact-plan"
    [
      ( "manifest",
        [
          Alcotest.test_case "spec-model exact plan manifest" `Quick
            test_exact_plan_manifest;
        ] );
      ( "cases",
        [ Alcotest.test_case "spec-model exact cases" `Quick test_exact_cases ]
      );
    ]
