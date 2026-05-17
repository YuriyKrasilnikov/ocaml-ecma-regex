module Core = Ecma_regex__Ecma_regex_core

let repo_root () =
  let cwd = Sys.getcwd () in
  let rec climb dir =
    let candidate =
      Filename.concat dir
        "cache/ecma262-regexp-exec-result-indices-exact-plan.tsv"
    in
    if Sys.file_exists candidate then dir
    else
      let parent = Filename.dirname dir in
      if parent = dir then
        Alcotest.fail
          "cache/ecma262-regexp-exec-result-indices-exact-plan.tsv is \
           missing; run \
           tools/build_ecma262_regexp_exec_result_indices_exact_plan.py"
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
  read_tsv [ "cache"; "ecma262-regexp-exec-result-indices-exact-plan.tsv" ]

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

let bool_field row name =
  match field name row with
  | "true" -> true
  | "false" -> false
  | value ->
    Alcotest.failf "%s: invalid %s %S" (field "plan_id" row) name value

let planned_rows rows =
  List.filter
    (fun row ->
       field "plan_state" row = "planned_not_executable"
       && field "coverage_credit" row = "none_exec_result_indices_exact_planned")
    rows

let test_exact_plan_manifest () =
  let rows = plan_rows () in
  Alcotest.(check int) "exec-result indices exact plan rows" 35
    (List.length rows);
  Alcotest.(check int) "planned executable rows" 35
    (List.length (planned_rows rows));
  let state_counts = count_by "plan_state" rows in
  check_count state_counts "planned_not_executable" 35;
  let credit_counts = count_by "coverage_credit" rows in
  check_count credit_counts "none_exec_result_indices_exact_planned" 35;
  let mapping_counts = count_by "mapping_family" rows in
  check_count mapping_counts "exec_result_matching" 7;
  check_count mapping_counts "exec_result_indices" 28;
  let layer_counts = count_by "executable_layer" rows in
  check_count layer_counts "exec_result" 35;
  let subfamily_counts = count_by "result_subfamily" rows in
  check_count subfamily_counts "builtin_exec_indices" 7;
  check_count subfamily_counts "get_match_index_pair" 3;
  check_count subfamily_counts "make_match_indices_index_pair_array" 25;
  let route_counts = count_by "result_semantic_route" rows in
  check_count route_counts "indices_result_model" 7;
  check_count route_counts "indices_index_pair_model" 3;
  check_count route_counts "indices_array_model" 25;
  let observability_counts = count_by "observability_status" rows in
  check_count observability_counts
    "internal_exec_result_indices_model_observable"
    35;
  let target_counts = count_by "target_test_artifact" rows in
  check_count target_counts
    "test/test_ecma262_exec_result_indices_exact_plan.ml"
    35;
  let has_groups_counts = count_by "expected_has_groups" rows in
  check_count has_groups_counts "true" 8;
  check_count has_groups_counts "false" 27;
  let pair_defined_counts = count_by "expected_index_pair_defined" rows in
  check_count pair_defined_counts "true" 32;
  check_count pair_defined_counts "false" 3;
  let duplicate_counts = count_by "expected_duplicate_group_name" rows in
  check_count duplicate_counts "true" 1;
  check_count duplicate_counts "false" 34;
  List.iter
    (fun row ->
       if
         not
           (String.starts_with ~prefix:"exec-result-indices-exact:"
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
           "flags";
           "input_text";
           "expected_indices_length";
           "expected_group_names_length";
           "expected_has_groups";
           "expected_entry_index";
           "expected_index_pair_defined";
           "expected_behavior";
           "expected_model_field";
           "exact_case_obligation";
           "observability_reason";
           "next_action";
         ];
       Alcotest.(check string) "indices flag" "d" (field "flags" row);
       Alcotest.(check string)
         "expected exec"
         "true"
         (field "expected_exec_result" row);
       Alcotest.(check string)
         "next action"
         "materialize_exec_result_indices_exact_case"
         (field "next_action" row))
    rows

let flags_for row =
  match Core.flags_of_string (field "flags" row) with
  | Ok flags -> flags
  | Error msg ->
    Alcotest.failf "%s: flags failed: %s" (field "plan_id" row) msg

let option_int_to_string = function
  | None -> ""
  | Some value -> string_of_int value

let option_string_to_string = function
  | None -> ""
  | Some value -> value

let check_bool_model_field name expected actual =
  Alcotest.(check bool) name expected actual

let check_model_field row observation =
  match field "expected_model_field" row with
  | "indices_list_initialized" ->
    check_bool_model_field "indices list initialized" true
      observation.Core.indices_list_initialized
  | "group_names_list_initialized" ->
    check_bool_model_field "group names list initialized" true
      observation.Core.group_names_list_initialized
  | "full_match_appended_to_indices" ->
    check_bool_model_field "full match appended" true
      observation.Core.full_match_appended_to_indices
  | "undefined_capture_appended_to_indices" ->
    check_bool_model_field "undefined capture appended" true
      observation.Core.undefined_capture_appended_to_indices
  | "has_indices_branch_observed" ->
    check_bool_model_field "has indices branch" true
      observation.Core.has_indices_branch_observed
  | "indices_array_built" ->
    check_bool_model_field "indices array built" true
      observation.Core.indices_array_built
  | "result_indices_property_observed" ->
    check_bool_model_field "result indices property" true
      observation.Core.result_indices_property_observed
  | "get_match_index_pair_observed" ->
    check_bool_model_field "get match index pair" true
      observation.Core.get_match_index_pair_observed
  | "index_pair_range_valid" ->
    check_bool_model_field "index pair range valid" true
      observation.Core.index_pair_range_valid
  | "index_pair_start_end_observed" ->
    check_bool_model_field "index pair start/end" true
      observation.Core.index_pair_start_end_observed
  | "make_match_indices_array_observed" ->
    check_bool_model_field "make indices array" true
      observation.Core.make_match_indices_array_observed
  | "indices_array_length_observed" ->
    Alcotest.(check int)
      "indices array length"
      (parse_int_field row "expected_indices_length")
      observation.Core.indices_array_length
  | "indices_length_within_array_limit" ->
    check_bool_model_field "indices length within limit" true
      observation.Core.indices_length_within_array_limit
  | "group_names_length_matches" ->
    check_bool_model_field "group names length matches" true
      observation.Core.group_names_length_matches
  | "group_names_aligned_with_captures" ->
    check_bool_model_field "group names aligned" true
      observation.Core.group_names_aligned_with_captures
  | "indices_array_created" ->
    check_bool_model_field "indices array created" true
      observation.Core.indices_array_created
  | "has_groups_branch_observed" ->
    check_bool_model_field "has groups branch" true
      observation.Core.has_groups_branch_observed
  | "indices_groups_object_created" ->
    check_bool_model_field "groups object created" true
      observation.Core.indices_groups_object_created
  | "no_groups_branch_observed" ->
    check_bool_model_field "no groups branch" true
      observation.Core.no_groups_branch_observed
  | "indices_groups_undefined_observed" ->
    check_bool_model_field "groups undefined" true
      observation.Core.indices_groups_undefined_observed
  | "indices_groups_property_observed" ->
    check_bool_model_field "groups property" true
      observation.Core.indices_groups_property_observed
  | "indices_iteration_observed" ->
    check_bool_model_field "indices iteration" true
      observation.Core.indices_iteration_observed
  | "indices_entry_read" ->
    check_bool_model_field "indices entry read" true
      observation.Core.indices_entry_read
  | "defined_index_entry_observed" ->
    check_bool_model_field "defined index entry" true
      observation.Core.defined_index_entry_observed
  | "get_match_index_pair_called" ->
    check_bool_model_field "get match index pair called" true
      observation.Core.get_match_index_pair_called
  | "undefined_index_entry_observed" ->
    check_bool_model_field "undefined index entry" true
      observation.Core.undefined_index_entry_observed
  | "undefined_index_pair_observed" ->
    check_bool_model_field "undefined index pair" true
      observation.Core.undefined_index_pair_observed
  | "indices_numeric_property_observed" ->
    check_bool_model_field "numeric property" true
      observation.Core.indices_numeric_property_observed
  | "capture_index_entry_observed" ->
    check_bool_model_field "capture index entry" true
      observation.Core.capture_index_entry_observed
  | "group_name_read" ->
    check_bool_model_field "group name read" true observation.Core.group_name_read
  | "defined_group_name_observed" ->
    check_bool_model_field "defined group name" true
      observation.Core.defined_group_name_observed
  | "named_groups_object_asserted" ->
    check_bool_model_field "named groups object asserted" true
      observation.Core.named_groups_object_asserted
  | "duplicate_group_name_observed" ->
    check_bool_model_field "duplicate group name" true
      observation.Core.duplicate_group_name_observed
  | "named_group_property_observed" ->
    check_bool_model_field "named group property" true
      observation.Core.named_group_property_observed
  | "indices_array_returned" ->
    check_bool_model_field "indices array returned" true
      observation.Core.indices_array_returned
  | model_field ->
    Alcotest.failf "%s: unsupported expected_model_field %S"
      (field "plan_id" row)
      model_field

let check_index_entry row observation =
  let entry_index = parse_int_field row "expected_entry_index" in
  if entry_index < 0 || entry_index >= Array.length observation.Core.exec_result_indices
  then Alcotest.failf "%s: index entry %d is out of range"
      (field "plan_id" row)
      entry_index;
  let pair = observation.Core.exec_result_indices.(entry_index) in
  if bool_field row "expected_index_pair_defined" then begin
    match pair with
    | None ->
      Alcotest.failf "%s: expected defined index pair at %d"
        (field "plan_id" row)
        entry_index
    | Some pair ->
      Alcotest.(check string)
        "index pair start"
        (field "expected_index_pair_start" row)
        (string_of_int pair.Core.index_pair_start_index);
      Alcotest.(check string)
        "index pair end"
        (field "expected_index_pair_end" row)
        (string_of_int pair.Core.index_pair_end_index)
  end
  else begin
    Alcotest.(check string)
      "undefined index pair"
      ""
      (option_int_to_string
         (Option.map (fun pair -> pair.Core.index_pair_start_index) pair));
    Alcotest.(check string)
      "undefined index pair end"
      ""
      (option_int_to_string
         (Option.map (fun pair -> pair.Core.index_pair_end_index) pair))
  end;
  if entry_index > 0 then begin
    let group_name = observation.Core.exec_result_group_names.(entry_index - 1) in
    Alcotest.(check string)
      "group name"
      (field "expected_group_name" row)
      (option_string_to_string group_name)
  end

let check_indices_case row =
  let flags = flags_for row in
  match Core.compile ~flags (field "pattern" row) with
  | Error msg ->
    Alcotest.failf
      "exec-result indices exact case failed to compile: plan=%s \
       requirement=%s pattern=%S flags=%S error=%s"
      (field "plan_id" row)
      (field "requirement_id" row)
      (field "pattern" row)
      (field "flags" row)
      msg
  | Ok regexp ->
    let observation =
      Core.inspect_exec_result_indices_model regexp (field "input_text" row)
    in
    Alcotest.(check bool) "has indices flag" true
      observation.Core.has_indices_flag;
    Alcotest.(check int)
      "indices length"
      (parse_int_field row "expected_indices_length")
      observation.Core.indices_array_length;
    Alcotest.(check int)
      "group names length"
      (parse_int_field row "expected_group_names_length")
      observation.Core.group_names_length;
    Alcotest.(check bool)
      "has groups"
      (bool_field row "expected_has_groups")
      observation.Core.has_groups;
    Alcotest.(check bool)
      "duplicate group name"
      (bool_field row "expected_duplicate_group_name")
      observation.Core.duplicate_group_name_observed;
    check_model_field row observation;
    check_index_entry row observation

let test_exact_plan_indices_cases () =
  plan_rows ()
  |> planned_rows
  |> List.iter check_indices_case

let () =
  Alcotest.run "ecma262-exec-result-indices-exact-plan" [
    ("manifest", [
      Alcotest.test_case "exec-result indices exact plan invariants" `Quick
        test_exact_plan_manifest;
    ]);
    ("indices", [
      Alcotest.test_case "exec-result indices exact planned cases" `Quick
        test_exact_plan_indices_cases;
    ]);
  ]
