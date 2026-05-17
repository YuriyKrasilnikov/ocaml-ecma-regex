module Core = Ecma_regex__Ecma_regex_core

let repo_root () =
  let cwd = Sys.getcwd () in
  let rec climb dir =
    let candidate =
      Filename.concat dir
        "cache/ecma262-regexp-match-engine-backreference-matcher-exact-plan.tsv"
    in
    if Sys.file_exists candidate then dir
    else
      let parent = Filename.dirname dir in
      if parent = dir then
        Alcotest.fail
          "cache/ecma262-regexp-match-engine-backreference-matcher-exact-plan.tsv \
           is missing; run \
           tools/build_ecma262_regexp_match_engine_backreference_matcher_exact_plan.py"
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
  read_tsv
    [
      "cache";
      "ecma262-regexp-match-engine-backreference-matcher-exact-plan.tsv";
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

let planned_rows rows =
  List.filter
    (fun row ->
       field "plan_state" row = "planned_not_executable"
       && field "coverage_credit" row
          = "none_match_engine_backreference_matcher_exact_planned")
    rows

let expected_observations = [
  "backreference_matcher_operation";
  "backreference_matcher_closure";
  "backreference_match_state_parameter";
  "backreference_continuation_parameter";
  "backreference_input_read";
  "backreference_captures_read";
  "backreference_result_initialized_undefined";
  "backreference_ns_iteration";
  "backreference_defined_capture_branch";
  "backreference_single_defined_capture_assert";
  "backreference_selected_capture_range";
  "backreference_undefined_capture_continuation";
  "backreference_end_index_read";
  "backreference_capture_start_index_read";
  "backreference_capture_end_index_read";
  "backreference_capture_length_computed";
  "backreference_forward_index_computed";
  "backreference_backward_index_computed";
  "backreference_input_length_read";
  "backreference_bounds_failure";
  "backreference_compare_start_min";
  "backreference_canonicalize_compare";
  "backreference_result_state_created";
  "backreference_continuation_return";
]

let test_exact_plan_manifest () =
  let rows = plan_rows () in
  Alcotest.(check int) "BackreferenceMatcher exact plan rows" 24
    (List.length rows);
  let planned = planned_rows rows in
  Alcotest.(check int) "planned executable rows" 24 (List.length planned);
  let state_counts = count_by "plan_state" rows in
  check_count state_counts "planned_not_executable" 24;
  let credit_counts = count_by "coverage_credit" rows in
  check_count credit_counts
    "none_match_engine_backreference_matcher_exact_planned" 24;
  let behavior_counts = count_by "expected_behavior" rows in
  check_count behavior_counts "backreference_matcher_exact_plan_observable" 24;
  let search_counts = count_by "expected_search_result" rows in
  check_count search_counts "true" 22;
  check_count search_counts "false" 2;
  let observation_counts = count_by "expected_observation" rows in
  List.iter (fun name -> check_count observation_counts name 1)
    expected_observations;
  let route_counts = count_by "case_route" rows in
  check_count route_counts "defined_capture_forward_success" 20;
  check_count route_counts "undefined_capture_continuation" 1;
  check_count route_counts "backward_direction_observer" 1;
  check_count route_counts "out_of_bounds_failure" 1;
  check_count route_counts "canonicalized_character_mismatch" 1;
  let layer_counts = count_by "executable_layer" rows in
  check_count layer_counts "match_engine" 24;
  let mapping_counts = count_by "mapping_family" rows in
  check_count mapping_counts "match_engine_backreferences" 24;
  let subfamily_counts = count_by "backreference_matcher_subfamily" rows in
  check_count subfamily_counts "backreference_matcher_operation" 24;
  let semantic_route_counts = count_by "backreference_matcher_route" rows in
  check_count semantic_route_counts "capture_backreference_runtime_semantics" 24;
  let observability_counts = count_by "observability_status" rows in
  check_count observability_counts "backreference_matcher_model_observable" 24;
  List.iter
    (fun row ->
       if
         not
           (String.starts_with
              ~prefix:"match-engine-backreference-matcher-exact:"
              (field "exact_case_id" row))
       then Alcotest.failf "%s: exact_case_id has wrong prefix"
           (field "plan_id" row);
       List.iter
         (fun name ->
            if field name row = "" then
              Alcotest.failf "%s: %s is empty" (field "plan_id" row) name)
         [
           "pattern";
           "input_text";
           "expected_search_result";
           "expected_observation";
           "exact_case_obligation";
           "observability_reason";
         ];
       Alcotest.(check string)
         "expected observed"
         "true"
         (field "expected_observed" row);
       if not (source_exists (field "source_file" row)) then
         Alcotest.failf "%s: missing ECMA source %s"
           (field "plan_id" row)
           (field "source_file" row);
       if not (target_exists (field "target_test_artifact" row)) then
         Alcotest.failf "%s: missing target test artifact %s"
           (field "plan_id" row)
           (field "target_test_artifact" row))
    rows

let flags_for row =
  match Core.flags_of_string (field "flags" row) with
  | Ok flags -> flags
  | Error msg ->
    Alcotest.failf "%s: flags failed: %s" (field "plan_id" row) msg

let bool_of_field row name =
  match field name row with
  | "true" -> true
  | "false" -> false
  | value -> Alcotest.failf "%s: invalid bool %s=%S" (field "plan_id" row) name value

let observation_value observation = function
  | "backreference_matcher_operation" ->
    observation.Core.backreference_matcher_operation_observed
  | "backreference_matcher_closure" ->
    observation.Core.backreference_matcher_closure_observed
  | "backreference_match_state_parameter" ->
    observation.Core.backreference_match_state_parameter_observed
  | "backreference_continuation_parameter" ->
    observation.Core.backreference_continuation_parameter_observed
  | "backreference_input_read" ->
    observation.Core.backreference_input_read_observed
  | "backreference_captures_read" ->
    observation.Core.backreference_captures_read_observed
  | "backreference_result_initialized_undefined" ->
    observation.Core.backreference_result_initialized_undefined_observed
  | "backreference_ns_iteration" ->
    observation.Core.backreference_ns_iteration_observed
  | "backreference_defined_capture_branch" ->
    observation.Core.backreference_defined_capture_branch_observed
  | "backreference_single_defined_capture_assert" ->
    observation.Core.backreference_single_defined_capture_assert_observed
  | "backreference_selected_capture_range" ->
    observation.Core.backreference_selected_capture_range_observed
  | "backreference_undefined_capture_continuation" ->
    observation.Core.backreference_undefined_capture_continuation_observed
  | "backreference_end_index_read" ->
    observation.Core.backreference_end_index_read_observed
  | "backreference_capture_start_index_read" ->
    observation.Core.backreference_capture_start_index_read_observed
  | "backreference_capture_end_index_read" ->
    observation.Core.backreference_capture_end_index_read_observed
  | "backreference_capture_length_computed" ->
    observation.Core.backreference_capture_length_computed_observed
  | "backreference_forward_index_computed" ->
    observation.Core.backreference_forward_index_computed_observed
  | "backreference_backward_index_computed" ->
    observation.Core.backreference_backward_index_computed_observed
  | "backreference_input_length_read" ->
    observation.Core.backreference_input_length_read_observed
  | "backreference_bounds_failure" ->
    observation.Core.backreference_bounds_failure_observed
  | "backreference_compare_start_min" ->
    observation.Core.backreference_compare_start_min_observed
  | "backreference_canonicalize_compare" ->
    observation.Core.backreference_canonicalize_compare_observed
  | "backreference_result_state_created" ->
    observation.Core.backreference_result_state_created_observed
  | "backreference_continuation_return" ->
    observation.Core.backreference_continuation_return_observed
  | name -> Alcotest.failf "unknown observation %S" name

let check_backreference_matcher_case row =
  let flags = flags_for row in
  match Core.compile ~flags (field "pattern" row) with
  | Error msg ->
    Alcotest.failf
      "BackreferenceMatcher exact case failed to compile: plan=%s \
       requirement=%s pattern=%S flags=%S error=%s"
      (field "plan_id" row)
      (field "requirement_id" row)
      (field "pattern" row)
      (field "flags" row)
      msg
  | Ok regexp ->
    Alcotest.(check bool)
      "public search result"
      (bool_of_field row "expected_search_result")
      (Core.search regexp (field "input_text" row));
    let observation =
      Core.inspect_backreference_matcher_model regexp (field "input_text" row)
    in
    Alcotest.(check bool)
      (field "expected_observation" row)
      true
      (observation_value observation (field "expected_observation" row))

let test_exact_plan_backreference_matcher_cases () =
  plan_rows ()
  |> planned_rows
  |> List.iter check_backreference_matcher_case

let () =
  Alcotest.run "ecma262-match-engine-backreference-matcher-exact-plan" [
    ("manifest", [
      Alcotest.test_case "BackreferenceMatcher exact plan invariants" `Quick
        test_exact_plan_manifest;
    ]);
    ("model", [
      Alcotest.test_case "BackreferenceMatcher exact planned cases" `Quick
        test_exact_plan_backreference_matcher_cases;
    ]);
  ]
