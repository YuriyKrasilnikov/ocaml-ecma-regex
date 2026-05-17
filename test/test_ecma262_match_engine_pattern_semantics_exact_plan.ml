module Core = Ecma_regex__Ecma_regex_core

let repo_root () =
  let cwd = Sys.getcwd () in
  let rec climb dir =
    let candidate =
      Filename.concat dir
        "cache/ecma262-regexp-match-engine-pattern-semantics-exact-plan.tsv"
    in
    if Sys.file_exists candidate then dir
    else
      let parent = Filename.dirname dir in
      if parent = dir then
        Alcotest.fail
          "cache/ecma262-regexp-match-engine-pattern-semantics-exact-plan.tsv \
           is missing; run \
           tools/build_ecma262_regexp_match_engine_pattern_semantics_exact_plan.py"
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

let plan_rows () =
  read_tsv [
    "cache";
    "ecma262-regexp-match-engine-pattern-semantics-exact-plan.tsv";
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

let source_exists source_file =
  source_file <> "" && Sys.file_exists (path [ source_file ])

let target_exists target =
  target <> "" && Sys.file_exists (path [ target ])

let executable_rows rows =
  List.filter
    (fun row ->
       field "plan_state" row = "planned_not_executable"
       && field "coverage_credit" row
          = "none_match_engine_pattern_semantics_exact_planned")
    rows

let deferred_rows rows =
  List.filter
    (fun row ->
       String.starts_with ~prefix:"deferred_" (field "plan_state" row)
       && field "coverage_credit" row
          = "none_match_engine_pattern_semantics_exact_deferred")
    rows

let search_exec_rows rows =
  List.filter
    (fun row ->
       field "plan_state" row = "planned_not_executable"
       && field "coverage_credit" row
          = "none_match_engine_pattern_semantics_exact_planned"
       && field "observability_status" row = "search_and_exec_observable")
    rows

let internal_model_rows rows =
  List.filter
    (fun row ->
       field "plan_state" row = "planned_not_executable"
       && field "coverage_credit" row
          = "none_match_engine_pattern_semantics_exact_planned"
       && field "observability_status" row
          = "internal_pattern_semantics_model_observable")
    rows

let decode_text source =
  let buffer = Buffer.create (String.length source) in
  let rec loop index =
    if index = String.length source then Buffer.contents buffer
    else if source.[index] = '\\' && index + 1 < String.length source then begin
      (match source.[index + 1] with
       | 'n' -> Buffer.add_char buffer '\n'
       | 'r' -> Buffer.add_char buffer '\r'
       | 't' -> Buffer.add_char buffer '\t'
       | '\\' -> Buffer.add_char buffer '\\'
       | other ->
         Alcotest.failf "unsupported escaped test input: \\\\%c" other);
      loop (index + 2)
    end
    else begin
      Buffer.add_char buffer source.[index];
      loop (index + 1)
    end
  in
  loop 0

let parse_bool row name =
  match field name row with
  | "true" -> true
  | "false" -> false
  | other ->
    Alcotest.failf "%s: invalid %s %S"
      (field "plan_id" row)
      name
      other

let parse_int_field row name =
  match int_of_string_opt (field name row) with
  | Some value -> value
  | None ->
    Alcotest.failf "%s: invalid %s %S"
      (field "plan_id" row)
      name
      (field name row)

let flags_for row =
  match Ecma_regex.flags_of_string (field "flags" row) with
  | Ok flags -> flags
  | Error msg ->
    Alcotest.failf "%s: flags failed: %s" (field "plan_id" row) msg

let core_flags_for row =
  match Core.flags_of_string (field "flags" row) with
  | Ok flags -> flags
  | Error msg ->
    Alcotest.failf "%s: flags failed: %s" (field "plan_id" row) msg

let test_exact_plan_manifest () =
  let rows = plan_rows () in
  Alcotest.(check int) "pattern semantics exact plan rows" 56
    (List.length rows);
  Alcotest.(check int) "planned executable rows" 56
    (List.length (executable_rows rows));
  Alcotest.(check int) "search/exec rows" 36
    (List.length (search_exec_rows rows));
  Alcotest.(check int) "internal model rows" 20
    (List.length (internal_model_rows rows));
  Alcotest.(check int) "deferred rows" 0
    (List.length (deferred_rows rows));
  let state_counts = count_by "plan_state" rows in
  check_count state_counts "planned_not_executable" 56;
  let credit_counts = count_by "coverage_credit" rows in
  check_count credit_counts "none_match_engine_pattern_semantics_exact_planned" 56;
  check_count credit_counts "none_match_engine_pattern_semantics_exact_deferred" 0;
  let clause_counts = count_by "clause_id" rows in
  check_count clause_counts "22.2.2" 3;
  check_count clause_counts "22.2.2.1" 1;
  check_count clause_counts "22.2.2.1.1" 9;
  check_count clause_counts "22.2.2.2" 12;
  check_count clause_counts "22.2.2.3" 26;
  check_count clause_counts "22.2.2.3.2" 5;
  let search_counts = count_by "expected_search_result" rows in
  check_count search_counts "true" 36;
  check_count search_counts "not_applicable" 20;
  let exec_counts = count_by "expected_exec_result" rows in
  check_count exec_counts "true" 36;
  check_count exec_counts "not_applicable" 20;
  let mapping_counts = count_by "mapping_family" rows in
  check_count mapping_counts "match_engine_pattern_semantics" 56;
  let layer_counts = count_by "executable_layer" rows in
  check_count layer_counts "match_engine" 56;
  let observability_counts = count_by "observability_status" rows in
  check_count observability_counts "search_and_exec_observable" 36;
  check_count observability_counts
    "internal_pattern_semantics_model_observable" 20;
  let model_scenario_counts = count_by "model_scenario" rows in
  check_count model_scenario_counts "" 36;
  check_count model_scenario_counts "utf16_bmp_unicode_character_model" 2;
  check_count model_scenario_counts "pattern_semantics_notation" 1;
  check_count model_scenario_counts "regexp_record_inventory" 3;
  check_count model_scenario_counts "compile_pattern_input_list" 1;
  check_count model_scenario_counts "compile_pattern_index" 1;
  check_count model_scenario_counts "compile_pattern_continuation" 1;
  check_count model_scenario_counts "compile_pattern_match_state" 1;
  check_count model_scenario_counts "compile_subpattern_operation" 1;
  check_count model_scenario_counts "compile_subpattern_piecewise_inventory" 1;
  check_count model_scenario_counts "quantifier_bounds_assert" 1;
  check_count model_scenario_counts "quantified_capture_index" 2;
  check_count model_scenario_counts "quantified_repeat_closure" 3;
  check_count model_scenario_counts "empty_matcher_state" 2;
  List.iter
    (fun row ->
       if
         not
           (String.starts_with
              ~prefix:"match-engine-pattern-semantics-exact:"
              (field "exact_case_id" row))
       then Alcotest.failf "%s: exact_case_id has wrong prefix"
           (field "plan_id" row);
       List.iter
         (fun name ->
            if field name row = "" then
              Alcotest.failf "%s: %s is empty" (field "plan_id" row) name)
         [
           "pattern_semantics_subfamily";
           "pattern_semantics_route";
           "exact_case_obligation";
           "observability_status";
           "observability_reason";
         ];
       if not (source_exists (field "source_file" row)) then
         Alcotest.failf "%s: missing ECMA source %s"
           (field "plan_id" row)
           (field "source_file" row);
       if field "plan_state" row = "planned_not_executable" then begin
         Alcotest.(check string)
           "executable next action"
           "materialize_match_engine_pattern_semantics_exact_case"
           (field "next_action" row);
         Alcotest.(check string)
           "executable target"
           "test/test_ecma262_match_engine_pattern_semantics_exact_plan.ml"
           (field "target_test_artifact" row);
         if not (target_exists (field "target_test_artifact" row)) then
           Alcotest.failf "%s: missing target test artifact %s"
             (field "plan_id" row)
             (field "target_test_artifact" row);
         match field "observability_status" row with
         | "search_and_exec_observable" ->
           Alcotest.(check string)
             "expected search"
             "true"
             (field "expected_search_result" row);
           Alcotest.(check string)
             "expected exec"
             "true"
             (field "expected_exec_result" row);
           if field "expected_start_index" row = "" then
             Alcotest.failf "%s: expected_start_index is empty"
               (field "plan_id" row);
           if field "expected_end_index" row = "" then
             Alcotest.failf "%s: expected_end_index is empty"
               (field "plan_id" row);
           Alcotest.(check string)
             "public expected_model_field"
             ""
             (field "expected_model_field" row);
           Alcotest.(check string)
             "public model_scenario"
             ""
             (field "model_scenario" row)
         | "internal_pattern_semantics_model_observable" ->
           Alcotest.(check string)
             "internal expected search"
             "not_applicable"
             (field "expected_search_result" row);
           Alcotest.(check string)
             "internal expected exec"
             "not_applicable"
             (field "expected_exec_result" row);
           if field "expected_model_field" row = "" then
             Alcotest.failf "%s: expected_model_field is empty"
               (field "plan_id" row);
           if field "model_scenario" row = "" then
             Alcotest.failf "%s: model_scenario is empty"
               (field "plan_id" row);
           Alcotest.(check string) "internal start" ""
             (field "expected_start_index" row);
           Alcotest.(check string) "internal end" ""
             (field "expected_end_index" row);
           Alcotest.(check string) "internal match" ""
             (field "expected_match_text" row)
         | other ->
           Alcotest.failf "%s: unsupported observability_status %S"
             (field "plan_id" row)
             other
       end
       else begin
         Alcotest.(check string) "deferred pattern" "" (field "pattern" row);
         Alcotest.(check string) "deferred flags" "" (field "flags" row);
         Alcotest.(check string) "deferred input" "" (field "input_text" row);
         Alcotest.(check string)
           "deferred expected search"
           "not_observable"
           (field "expected_search_result" row);
         Alcotest.(check string)
           "deferred expected exec"
           "not_observable"
           (field "expected_exec_result" row);
         Alcotest.(check string)
           "deferred target"
           ""
           (field "target_test_artifact" row)
       end)
    rows

let check_exec_result row regexp input =
  match Ecma_regex.exec regexp input with
  | None when not (parse_bool row "expected_exec_result") -> ()
  | None ->
    Alcotest.failf "%s: expected exec result, got None"
      (field "plan_id" row)
  | Some result when not (parse_bool row "expected_exec_result") ->
    Alcotest.failf
      "%s: expected no exec result, got %d..%d %S"
      (field "plan_id" row)
      result.start_index
      result.end_index
      result.matched_text
  | Some result ->
    Alcotest.(check int)
      "start_index"
      (parse_int_field row "expected_start_index")
      result.start_index;
    Alcotest.(check int)
      "end_index"
      (parse_int_field row "expected_end_index")
      result.end_index;
    Alcotest.(check string)
      "matched_text"
      (decode_text (field "expected_match_text" row))
      result.matched_text

let check_pattern_semantics_case row =
  let flags = flags_for row in
  match Ecma_regex.compile ~flags (field "pattern" row) with
  | Error msg ->
    Alcotest.failf
      "Pattern Semantics exact case failed to compile: plan=%s requirement=%s \
       pattern=%S flags=%S error=%s"
      (field "plan_id" row)
      (field "requirement_id" row)
      (field "pattern" row)
      (field "flags" row)
      msg
  | Ok regexp ->
    let input = decode_text (field "input_text" row) in
    Alcotest.(check bool)
      (field "exact_case_id" row)
      (parse_bool row "expected_search_result")
      (Ecma_regex.search regexp input);
    check_exec_result row regexp input

let model_field_observed expected
    (observation : Core.pattern_semantics_model_observation) =
  Array.exists (String.equal expected) observation.Core.observed_model_fields

let check_internal_model_invariants row
    (observation : Core.pattern_semantics_model_observation) =
  if observation.Core.input_code_point_count > observation.Core.input_length then
    Alcotest.failf "%s: input code point count exceeds byte length"
      (field "plan_id" row);
  if
    observation.Core.input_utf16_code_unit_length
    < observation.Core.input_code_point_count
  then
    Alcotest.failf "%s: UTF-16 code unit length is below code point count"
      (field "plan_id" row);
  if Array.length observation.Core.regexp_record_fields <> 6 then
    Alcotest.failf "%s: RegExp Record field inventory has wrong size"
      (field "plan_id" row);
  match field "model_scenario" row with
  | "quantifier_bounds_assert" ->
    Alcotest.(check (option int))
      "quantifier min"
      (Some 1)
      observation.Core.quantifier_min;
    Alcotest.(check (option int))
      "quantifier max"
      (Some 2)
      observation.Core.quantifier_max;
    Alcotest.(check (option bool))
      "quantifier greedy"
      (Some true)
      observation.Core.quantifier_greedy
  | "quantified_capture_index" ->
    Alcotest.(check (option int))
      "paren index"
      (Some 1)
      observation.Core.quantified_paren_index;
    Alcotest.(check (option int))
      "paren count"
      (Some 1)
      observation.Core.quantified_paren_count
  | "quantified_repeat_closure" ->
    Alcotest.(check (option int))
      "repeat min"
      (Some 0)
      observation.Core.quantifier_min;
    Alcotest.(check (option int))
      "repeat paren count"
      (Some 1)
      observation.Core.quantified_paren_count
  | "empty_matcher_state" ->
    (match observation.Core.exec_result with
     | Some result ->
       Alcotest.(check int) "empty start" 0 result.start_index;
       Alcotest.(check int) "empty end" 0 result.end_index;
       Alcotest.(check string) "empty text" "" result.matched_text
     | None ->
       Alcotest.failf "%s: empty matcher produced no result"
         (field "plan_id" row))
  | _ -> ()

let check_pattern_semantics_model_case row =
  let flags = core_flags_for row in
  match Core.compile ~flags (field "pattern" row) with
  | Error msg ->
    Alcotest.failf
      "Pattern Semantics model case failed to compile: plan=%s requirement=%s \
       pattern=%S flags=%S error=%s"
      (field "plan_id" row)
      (field "requirement_id" row)
      (field "pattern" row)
      (field "flags" row)
      msg
  | Ok regexp ->
    let observation =
      Core.inspect_pattern_semantics_model
        ~model_scenario:(field "model_scenario" row)
        regexp
        (decode_text (field "input_text" row))
    in
    Alcotest.(check bool)
      (field "expected_model_field" row)
      true
      (model_field_observed (field "expected_model_field" row) observation);
    check_internal_model_invariants row observation

let test_exact_plan_pattern_semantics_cases () =
  plan_rows ()
  |> search_exec_rows
  |> List.iter check_pattern_semantics_case

let test_exact_plan_pattern_semantics_model_cases () =
  plan_rows ()
  |> internal_model_rows
  |> List.iter check_pattern_semantics_model_case

let () =
  Alcotest.run "ecma262-match-engine-pattern-semantics-exact-plan" [
    ("manifest", [
      Alcotest.test_case "Pattern Semantics exact plan invariants" `Quick
        test_exact_plan_manifest;
    ]);
    ("match", [
      Alcotest.test_case "Pattern Semantics exact planned cases" `Quick
        test_exact_plan_pattern_semantics_cases;
      Alcotest.test_case "Pattern Semantics internal model cases" `Quick
        test_exact_plan_pattern_semantics_model_cases;
    ]);
  ]
