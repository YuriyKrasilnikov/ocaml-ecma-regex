module Core = Ecma_regex__Ecma_regex_core

let repo_root () =
  let cwd = Sys.getcwd () in
  let rec climb dir =
    let candidate =
      Filename.concat dir
        "cache/ecma262-regexp-exec-result-matching-exact-plan.tsv"
    in
    if Sys.file_exists candidate then dir
    else
      let parent = Filename.dirname dir in
      if parent = dir then
        Alcotest.fail
          "cache/ecma262-regexp-exec-result-matching-exact-plan.tsv is \
           missing; run \
           tools/build_ecma262_regexp_exec_result_matching_exact_plan.py"
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
  read_tsv [ "cache"; "ecma262-regexp-exec-result-matching-exact-plan.tsv" ]

let count_by field_name rows =
  let counts = Hashtbl.create 64 in
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

let planned_rows rows =
  List.filter
    (fun row ->
       field "plan_state" row = "planned_not_executable"
       && field "coverage_credit" row
          = "none_exec_result_matching_exact_planned")
    rows

let deferred_rows rows =
  List.filter
    (fun row ->
       String.starts_with ~prefix:"deferred_" (field "plan_state" row)
       && field "coverage_credit" row
          = "none_exec_result_matching_exact_deferred")
    rows

let parse_int_field row name =
  match int_of_string_opt (field name row) with
  | Some value -> value
  | None ->
    Alcotest.failf "%s: invalid %s %S"
      (field "plan_id" row)
      name
      (field name row)

let test_exact_plan_manifest () =
  let rows = plan_rows () in
  Alcotest.(check int) "exec-result matching exact plan rows" 92
    (List.length rows);
  Alcotest.(check int) "planned executable rows" 72
    (List.length (planned_rows rows));
  Alcotest.(check int) "deferred rows" 20 (List.length (deferred_rows rows));
  let state_counts = count_by "plan_state" rows in
  check_count state_counts "planned_not_executable" 72;
  check_count state_counts
    "deferred_already_covered_by_exec_result_capture_exact_case" 13;
  check_count state_counts
    "deferred_already_covered_by_exec_result_indices_exact_case" 7;
  let credit_counts = count_by "coverage_credit" rows in
  check_count credit_counts "none_exec_result_matching_exact_planned" 72;
  check_count credit_counts "none_exec_result_matching_exact_deferred" 20;
  let exec_counts = count_by "expected_exec_result" rows in
  check_count exec_counts "true" 57;
  check_count exec_counts "false" 7;
  check_count exec_counts "not_applicable" 8;
  check_count exec_counts "not_observable" 20;
  let family_counts = count_by "mapping_family" rows in
  check_count family_counts "exec_result_matching" 92;
  let layer_counts = count_by "executable_layer" rows in
  check_count layer_counts "exec_result" 92;
  let scenario_counts = count_by "model_scenario" rows in
  check_count scenario_counts "regexp_exec_object_dispatch" 8;
  check_count scenario_counts "last_index_out_of_bounds_global" 4;
  check_count scenario_counts "sticky_failure" 3;
  check_count scenario_counts "unicode_success" 4;
  check_count scenario_counts "global_success" 2;
  check_count scenario_counts "named_groups" 12;
  check_count scenario_counts "duplicate_named_groups" 4;
  check_count scenario_counts "no_groups" 5;
  let observability_counts = count_by "observability_status" rows in
  check_count observability_counts
    "internal_exec_result_matching_model_observable" 72;
  let target_counts = count_by "target_test_artifact" rows in
  check_count target_counts
    "test/test_ecma262_exec_result_matching_exact_plan.ml"
    72;
  List.iter
    (fun row ->
       if
         not
           (String.starts_with ~prefix:"exec-result-matching-exact:"
              (field "exact_case_id" row))
       then Alcotest.failf "%s: exact_case_id has wrong prefix"
           (field "plan_id" row);
       if field "exact_case_obligation" row = "" then
         Alcotest.failf "%s: exact_case_obligation is empty"
           (field "plan_id" row);
       if field "observability_status" row = "" then
         Alcotest.failf "%s: observability_status is empty"
           (field "plan_id" row);
       if not (source_exists (field "source_file" row)) then
         Alcotest.failf "%s: missing ECMA source %s"
           (field "plan_id" row)
           (field "source_file" row);
       if field "plan_state" row = "planned_not_executable" then begin
         List.iter
           (fun name ->
              if field name row = "" then
                Alcotest.failf "%s: %s is empty" (field "plan_id" row) name)
           [
             "pattern";
             "input_text";
             "expected_behavior";
             "expected_model_field";
             "model_scenario";
             "target_test_artifact";
           ];
         Alcotest.(check string)
           "planned observability"
           "internal_exec_result_matching_model_observable"
           (field "observability_status" row);
         Alcotest.(check string)
           "planned next action"
           "materialize_exec_result_matching_exact_case"
           (field "next_action" row);
         Alcotest.(check string)
           "behavior follows model field"
           (field "expected_model_field" row)
           (field "expected_behavior" row);
         if not (target_exists (field "target_test_artifact" row)) then
           Alcotest.failf "%s: missing target test artifact %s"
             (field "plan_id" row)
             (field "target_test_artifact" row)
       end
       else begin
         Alcotest.(check string) "deferred pattern" "" (field "pattern" row);
         Alcotest.(check string) "deferred input" "" (field "input_text" row);
         Alcotest.(check string)
           "deferred expected exec"
           "not_observable"
           (field "expected_exec_result" row);
         Alcotest.(check string)
           "deferred target"
           ""
           (field "target_test_artifact" row);
         Alcotest.(check string)
           "deferred model field"
           ""
           (field "expected_model_field" row);
         if not (String.starts_with ~prefix:"design_" (field "next_action" row))
         then Alcotest.failf "%s: deferred next_action must be design_*"
             (field "plan_id" row)
       end)
    rows

let flags_for row =
  match Core.flags_of_string (field "flags" row) with
  | Ok flags -> flags
  | Error msg ->
    Alcotest.failf "%s: flags failed: %s" (field "plan_id" row) msg

let model_field_observed expected
    (observation : Core.exec_result_matching_model_observation) =
  Array.exists (String.equal expected) observation.Core.observed_model_fields

let check_exec_result row
    (observation : Core.exec_result_matching_model_observation) =
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
  | "not_applicable", _ -> ()
  | expected, _ ->
    Alcotest.failf "%s: invalid expected_exec_result %S"
      (field "plan_id" row)
      expected

let check_exec_case row =
  let flags = flags_for row in
  match Core.compile ~flags (field "pattern" row) with
  | Error msg ->
    Alcotest.failf
      "exec-result matching exact case failed to compile: plan=%s \
       requirement=%s pattern=%S flags=%S error=%s"
      (field "plan_id" row)
      (field "requirement_id" row)
      (field "pattern" row)
      (field "flags" row)
      msg
  | Ok regexp ->
    let observation =
      Core.inspect_exec_result_matching_model
        ~model_scenario:(field "model_scenario" row)
        regexp
        (field "input_text" row)
    in
    let expected_field = field "expected_model_field" row in
    Alcotest.(check bool)
      expected_field
      true
      (model_field_observed expected_field observation);
    check_exec_result row observation

let test_exact_plan_exec_cases () =
  plan_rows ()
  |> planned_rows
  |> List.iter check_exec_case

let () =
  Alcotest.run "ecma262-exec-result-matching-exact-plan" [
    ("manifest", [
      Alcotest.test_case "exec-result matching exact plan invariants" `Quick
        test_exact_plan_manifest;
    ]);
    ("model", [
      Alcotest.test_case "exec-result matching exact model cases" `Quick
        test_exact_plan_exec_cases;
    ]);
  ]
