module Core = Ecma_regex__Ecma_regex_core

let repo_root () =
  let cwd = Sys.getcwd () in
  let rec climb dir =
    let candidate =
      Filename.concat dir "cache/ecma262-regexp-match-engine-capture-exact-plan.tsv"
    in
    if Sys.file_exists candidate then dir
    else
      let parent = Filename.dirname dir in
      if parent = dir then
        Alcotest.fail
          "cache/ecma262-regexp-match-engine-capture-exact-plan.tsv is missing; \
           run tools/build_ecma262_regexp_match_engine_capture_exact_plan.py"
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
  read_tsv [ "cache"; "ecma262-regexp-match-engine-capture-exact-plan.tsv" ]

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
          = "none_match_engine_capture_exact_planned")
    rows

let expected_observations = [
  "capture_group_atom";
  "capture_subpattern_matcher";
  "capture_paren_index";
  "capture_matcher_closure";
  "capture_match_state_parameter";
  "capture_continuation_parameter";
  "capture_nested_continuation";
  "capture_nested_match_state_parameter";
  "capture_copy";
  "capture_input_preserved";
  "capture_start_index";
  "capture_end_index";
  "capture_forward_branch";
  "capture_forward_order";
  "capture_forward_range";
  "capture_backward_branch";
  "capture_backward_direction";
  "capture_backward_order";
  "capture_backward_range";
  "capture_slot_write";
  "capture_result_state";
  "capture_outer_continuation";
  "capture_submatcher_invocation";
]

let test_exact_plan_manifest () =
  let rows = plan_rows () in
  Alcotest.(check int) "capture exact plan rows" 23 (List.length rows);
  let planned = planned_rows rows in
  Alcotest.(check int) "planned executable rows" 23 (List.length planned);
  let state_counts = count_by "plan_state" rows in
  check_count state_counts "planned_not_executable" 23;
  let credit_counts = count_by "coverage_credit" rows in
  check_count credit_counts "none_match_engine_capture_exact_planned" 23;
  let behavior_counts = count_by "expected_behavior" rows in
  check_count behavior_counts "capture_model_observable" 23;
  let observation_counts = count_by "expected_observation" rows in
  List.iter (fun name -> check_count observation_counts name 1) expected_observations;
  let layer_counts = count_by "executable_layer" rows in
  check_count layer_counts "match_engine" 23;
  let mapping_counts = count_by "mapping_family" rows in
  check_count mapping_counts "match_engine_atoms" 23;
  let route_counts = count_by "capture_semantic_route" rows in
  check_count route_counts "capture_range_match_state_model" 23;
  let observability_counts = count_by "observability_status" rows in
  check_count observability_counts "capture_model_observable" 23;
  List.iter
    (fun row ->
       if
         not
           (String.starts_with ~prefix:"match-engine-capture-exact:"
              (field "exact_case_id" row))
       then Alcotest.failf "%s: exact_case_id has wrong prefix"
           (field "plan_id" row);
       List.iter
         (fun name ->
            if field name row = "" then
              Alcotest.failf "%s: %s is empty" (field "plan_id" row) name)
         [
           "source_atom_plan_id";
           "pattern";
           "input_text";
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

let observation_value observation = function
  | "capture_group_atom" -> observation.Core.capture_group_atom_observed
  | "capture_subpattern_matcher" ->
    observation.Core.capture_subpattern_matcher_observed
  | "capture_paren_index" -> observation.Core.capture_paren_index_observed
  | "capture_matcher_closure" ->
    observation.Core.capture_matcher_closure_observed
  | "capture_match_state_parameter" ->
    observation.Core.capture_match_state_parameter_observed
  | "capture_continuation_parameter" ->
    observation.Core.capture_continuation_parameter_observed
  | "capture_nested_continuation" ->
    observation.Core.capture_nested_continuation_observed
  | "capture_nested_match_state_parameter" ->
    observation.Core.capture_nested_match_state_parameter_observed
  | "capture_copy" -> observation.Core.capture_copy_observed
  | "capture_input_preserved" ->
    observation.Core.capture_input_preserved_observed
  | "capture_start_index" -> observation.Core.capture_start_index_observed
  | "capture_end_index" -> observation.Core.capture_end_index_observed
  | "capture_forward_branch" ->
    observation.Core.capture_forward_branch_observed
  | "capture_forward_order" -> observation.Core.capture_forward_order_observed
  | "capture_forward_range" -> observation.Core.capture_forward_range_observed
  | "capture_backward_branch" ->
    observation.Core.capture_backward_branch_observed
  | "capture_backward_direction" ->
    observation.Core.capture_backward_direction_observed
  | "capture_backward_order" ->
    observation.Core.capture_backward_order_observed
  | "capture_backward_range" ->
    observation.Core.capture_backward_range_observed
  | "capture_slot_write" -> observation.Core.capture_slot_write_observed
  | "capture_result_state" -> observation.Core.capture_result_state_observed
  | "capture_outer_continuation" ->
    observation.Core.capture_outer_continuation_observed
  | "capture_submatcher_invocation" ->
    observation.Core.capture_submatcher_invocation_observed
  | name -> Alcotest.failf "unknown observation %S" name

let check_capture_case row =
  let flags = flags_for row in
  match Core.compile ~flags (field "pattern" row) with
  | Error msg ->
    Alcotest.failf
      "capture exact case failed to compile: plan=%s requirement=%s pattern=%S \
       flags=%S error=%s"
      (field "plan_id" row)
      (field "requirement_id" row)
      (field "pattern" row)
      (field "flags" row)
      msg
  | Ok regexp ->
    let observation = Core.inspect_capture_model regexp (field "input_text" row) in
    Alcotest.(check bool)
      (field "expected_observation" row)
      true
      (observation_value observation (field "expected_observation" row))

let test_exact_plan_capture_cases () =
  plan_rows ()
  |> planned_rows
  |> List.iter check_capture_case

let () =
  Alcotest.run "ecma262-match-engine-capture-exact-plan" [
    ("manifest", [
      Alcotest.test_case "capture exact plan invariants" `Quick
        test_exact_plan_manifest;
    ]);
    ("model", [
      Alcotest.test_case "capture exact planned cases" `Quick
        test_exact_plan_capture_cases;
    ]);
  ]
