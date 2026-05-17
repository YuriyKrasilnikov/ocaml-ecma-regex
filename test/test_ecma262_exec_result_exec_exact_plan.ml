module Core = Ecma_regex__Ecma_regex_core

let repo_root () =
  let cwd = Sys.getcwd () in
  let rec climb dir =
    let candidate =
      Filename.concat dir
        "cache/ecma262-regexp-exec-result-exec-exact-plan.tsv"
    in
    if Sys.file_exists candidate then dir
    else
      let parent = Filename.dirname dir in
      if parent = dir then
        Alcotest.fail
          "cache/ecma262-regexp-exec-result-exec-exact-plan.tsv is missing; \
           run tools/build_ecma262_regexp_exec_result_exec_exact_plan.py"
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
  read_tsv [ "cache"; "ecma262-regexp-exec-result-exec-exact-plan.tsv" ]

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

let parse_int_field row name =
  match int_of_string_opt (field name row) with
  | Some value -> value
  | None ->
    Alcotest.failf "%s: invalid %s %S"
      (field "plan_id" row)
      name
      (field name row)

let bool_text = function
  | true -> "true"
  | false -> "false"

let planned_rows rows =
  List.filter
    (fun row ->
       field "plan_state" row = "planned_not_executable"
       && field "coverage_credit" row = "none_exec_result_exec_exact_planned")
    rows

let test_exact_plan_manifest () =
  let rows = plan_rows () in
  Alcotest.(check int) "exec-result exec exact plan rows" 21
    (List.length rows);
  Alcotest.(check int) "planned executable rows" 21
    (List.length (planned_rows rows));
  let state_counts = count_by "plan_state" rows in
  check_count state_counts "planned_not_executable" 21;
  let credit_counts = count_by "coverage_credit" rows in
  check_count credit_counts "none_exec_result_exec_exact_planned" 21;
  let mapping_counts = count_by "mapping_family" rows in
  check_count mapping_counts "exec_result_exec" 21;
  let layer_counts = count_by "executable_layer" rows in
  check_count layer_counts "exec_result" 21;
  let subfamily_counts = count_by "result_subfamily" rows in
  check_count subfamily_counts "regexp_prototype_exec" 6;
  check_count subfamily_counts "regexp_prototype_test" 7;
  check_count subfamily_counts "match_record" 5;
  check_count subfamily_counts "get_match_string" 3;
  let route_counts = count_by "result_semantic_route" rows in
  check_count route_counts "exec_method_model" 6;
  check_count route_counts "test_method_model" 7;
  check_count route_counts "match_record_model" 5;
  check_count route_counts "get_match_string_model" 3;
  let exec_counts = count_by "expected_exec_result" rows in
  check_count exec_counts "true" 19;
  check_count exec_counts "false" 2;
  let test_counts = count_by "expected_test_result" rows in
  check_count test_counts "true" 5;
  check_count test_counts "false" 2;
  check_count test_counts "not_applicable" 14;
  let observability_counts = count_by "observability_status" rows in
  check_count observability_counts
    "internal_exec_result_exec_model_observable"
    21;
  let target_counts = count_by "target_test_artifact" rows in
  check_count target_counts
    "test/test_ecma262_exec_result_exec_exact_plan.ml"
    21;
  List.iter
    (fun row ->
       if
         not
           (String.starts_with ~prefix:"exec-result-exec-exact:"
              (field "exact_case_id" row))
       then Alcotest.failf "%s: exact_case_id has wrong prefix"
           (field "plan_id" row);
       if not (source_exists (field "source_file" row)) then
         Alcotest.failf "%s: missing ECMA source %s"
           (field "plan_id" row)
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
           "pattern";
           "input_text";
           "expected_exec_result";
           "expected_test_result";
           "expected_behavior";
           "expected_model_field";
           "exact_case_obligation";
           "observability_reason";
           "next_action";
         ];
       Alcotest.(check string)
         "next action"
         "materialize_exec_result_exec_exact_case"
         (field "next_action" row))
    rows

let flags_for row =
  match Core.flags_of_string (field "flags" row) with
  | Ok flags -> flags
  | Error msg ->
    Alcotest.failf "%s: flags failed: %s" (field "plan_id" row) msg

let option_string_to_string = function
  | None -> ""
  | Some value -> value

let check_bool_model_field name actual =
  Alcotest.(check bool) name true actual

let check_model_field row observation =
  match field "expected_model_field" row with
  | "regexp_prototype_exec_operation_observed" ->
    check_bool_model_field "exec operation"
      observation.Core.regexp_prototype_exec_operation_observed
  | "regexp_prototype_exec_result_shape_observed" ->
    check_bool_model_field "exec result shape"
      observation.Core.regexp_prototype_exec_result_shape_observed
  | "regexp_prototype_exec_this_value_observed" ->
    check_bool_model_field "exec this value"
      observation.Core.regexp_prototype_exec_this_value_observed
  | "regexp_prototype_exec_internal_slot_observed" ->
    check_bool_model_field "exec internal slot"
      observation.Core.regexp_prototype_exec_internal_slot_observed
  | "regexp_prototype_exec_string_input_observed" ->
    check_bool_model_field "exec string input"
      observation.Core.regexp_prototype_exec_string_input_observed
  | "regexp_prototype_exec_delegates_to_builtin_exec" ->
    check_bool_model_field "exec delegates"
      observation.Core.regexp_prototype_exec_delegates_to_builtin_exec
  | "regexp_prototype_test_operation_observed" ->
    check_bool_model_field "test operation"
      observation.Core.regexp_prototype_test_operation_observed
  | "regexp_prototype_test_this_value_observed" ->
    check_bool_model_field "test this value"
      observation.Core.regexp_prototype_test_this_value_observed
  | "regexp_prototype_test_typed_receiver_enforced" ->
    check_bool_model_field "test typed receiver"
      observation.Core.regexp_prototype_test_typed_receiver_enforced
  | "regexp_prototype_test_string_input_observed" ->
    check_bool_model_field "test string input"
      observation.Core.regexp_prototype_test_string_input_observed
  | "regexp_prototype_test_calls_regexp_exec" ->
    check_bool_model_field "test calls exec"
      observation.Core.regexp_prototype_test_calls_regexp_exec
  | "regexp_prototype_test_false_result_observed" ->
    check_bool_model_field "test false result"
      observation.Core.regexp_prototype_test_false_result_observed
  | "regexp_prototype_test_true_result_observed" ->
    check_bool_model_field "test true result"
      observation.Core.regexp_prototype_test_true_result_observed
  | "match_record_observed" ->
    check_bool_model_field "match record"
      observation.Core.match_record_observed
  | "match_record_fields_observed" ->
    check_bool_model_field "match record fields"
      observation.Core.match_record_fields_observed
  | "match_record_field_table_observed" ->
    check_bool_model_field "match record field table"
      observation.Core.match_record_field_table_observed
  | "match_record_start_index_observed" ->
    check_bool_model_field "match record start"
      observation.Core.match_record_start_index_observed
  | "match_record_end_index_observed" ->
    check_bool_model_field "match record end"
      observation.Core.match_record_end_index_observed
  | "get_match_string_operation_observed" ->
    check_bool_model_field "GetMatchString operation"
      observation.Core.get_match_string_operation_observed
  | "get_match_string_range_assertion_observed" ->
    check_bool_model_field "GetMatchString range"
      observation.Core.get_match_string_range_assertion_observed
  | "get_match_string_result_observed" ->
    check_bool_model_field "GetMatchString result"
      observation.Core.get_match_string_result_observed
  | model_field ->
    Alcotest.failf "%s: unsupported expected_model_field %S"
      (field "plan_id" row)
      model_field

let check_exec_result row
    (observation : Core.exec_result_exec_model_observation) =
  match field "expected_exec_result" row, observation.Core.exec_result with
  | "true", Some result ->
    Alcotest.(check int)
      "start_index"
      (parse_int_field row "expected_start_index")
      result.Core.start_index;
    Alcotest.(check int)
      "end_index"
      (parse_int_field row "expected_end_index")
      result.Core.end_index;
    Alcotest.(check string)
      "matched_text"
      (field "expected_match_text" row)
      result.Core.matched_text
  | "true", None ->
    Alcotest.failf "%s: expected exec result, got None"
      (field "plan_id" row)
  | "false", None -> ()
  | "false", Some result ->
    Alcotest.failf "%s: expected no exec result, got %d..%d %S"
      (field "plan_id" row)
      result.Core.start_index
      result.Core.end_index
      result.Core.matched_text
  | expected, _ ->
    Alcotest.failf "%s: invalid expected_exec_result %S"
      (field "plan_id" row)
      expected

let check_test_result row observation =
  match field "expected_test_result" row with
  | "not_applicable" -> ()
  | "true" ->
    Alcotest.(check string) "test result" "true"
      (bool_text observation.Core.test_result)
  | "false" ->
    Alcotest.(check string) "test result" "false"
      (bool_text observation.Core.test_result)
  | value ->
    Alcotest.failf "%s: invalid expected_test_result %S"
      (field "plan_id" row)
      value

let check_get_match_string row observation =
  if field "result_subfamily" row = "get_match_string" then
    Alcotest.(check string)
      "GetMatchString substring"
      (field "expected_match_text" row)
      (option_string_to_string observation.Core.get_match_string_result)

let check_exec_case row =
  let flags = flags_for row in
  match Core.compile ~flags (field "pattern" row) with
  | Error msg ->
    Alcotest.failf
      "exec-result exec exact case failed to compile: plan=%s \
       requirement=%s pattern=%S flags=%S error=%s"
      (field "plan_id" row)
      (field "requirement_id" row)
      (field "pattern" row)
      (field "flags" row)
      msg
  | Ok regexp ->
    let observation =
      Core.inspect_exec_result_exec_model regexp (field "input_text" row)
    in
    check_model_field row observation;
    check_exec_result row observation;
    check_test_result row observation;
    check_get_match_string row observation

let test_exact_plan_exec_cases () =
  plan_rows ()
  |> planned_rows
  |> List.iter check_exec_case

let () =
  Alcotest.run "ecma262-exec-result-exec-exact-plan" [
    ("manifest", [
      Alcotest.test_case "exec-result exec exact plan invariants" `Quick
        test_exact_plan_manifest;
    ]);
    ("exec", [
      Alcotest.test_case "exec-result exec exact planned cases" `Quick
        test_exact_plan_exec_cases;
    ]);
  ]
