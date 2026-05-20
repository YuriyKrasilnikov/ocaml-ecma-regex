module Core = Ecma_regex__Ecma_regex_core

let repo_root () =
  let cwd = Sys.getcwd () in
  let rec climb dir =
    let candidate =
      Filename.concat dir
        "cache/ecma262-regexp-exec-result-instances-exact-plan.tsv"
    in
    if Sys.file_exists candidate then dir
    else
      let parent = Filename.dirname dir in
      if parent = dir then
        Alcotest.fail
          "cache/ecma262-regexp-exec-result-instances-exact-plan.tsv is \
           missing; run \
           tools/build_ecma262_regexp_exec_result_instances_exact_plan.py"
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
  read_tsv [ "cache"; "ecma262-regexp-exec-result-instances-exact-plan.tsv" ]

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

let parse_bool_field row name =
  match field name row with
  | "true" -> true
  | "false" -> false
  | value -> Alcotest.failf "%s: invalid %s %S" (field "plan_id" row) name value

let planned_rows rows =
  List.filter
    (fun row ->
      field "plan_state" row = "planned_not_executable"
      && field "coverage_credit" row
         = "none_exec_result_instances_exact_planned")
    rows

let test_exact_plan_manifest () =
  let rows = plan_rows () in
  Alcotest.(check int)
    "exec-result instances exact plan rows" 3 (List.length rows);
  Alcotest.(check int)
    "planned executable rows" 3
    (List.length (planned_rows rows));
  let state_counts = count_by "plan_state" rows in
  check_count state_counts "planned_not_executable" 3;
  let credit_counts = count_by "coverage_credit" rows in
  check_count credit_counts "none_exec_result_instances_exact_planned" 3;
  let mapping_counts = count_by "mapping_family" rows in
  check_count mapping_counts "exec_result_instances" 3;
  let layer_counts = count_by "executable_layer" rows in
  check_count layer_counts "exec_result" 3;
  let subfamily_counts = count_by "result_subfamily" rows in
  check_count subfamily_counts "regexp_instance_internal_slots" 1;
  check_count subfamily_counts "regexp_instance_property_inventory" 1;
  check_count subfamily_counts "last_index_property" 1;
  let route_counts = count_by "result_semantic_route" rows in
  check_count route_counts "instance_slots_model" 1;
  check_count route_counts "last_index_property_model" 1;
  check_count route_counts "last_index_property_attributes_model" 1;
  let observability_counts = count_by "observability_status" rows in
  check_count observability_counts
    "internal_exec_result_instance_model_observable" 3;
  let target_counts = count_by "target_test_artifact" rows in
  check_count target_counts
    "test/test_ecma262_exec_result_instances_exact_plan.ml" 3;
  List.iter
    (fun row ->
      if
        not
          (String.starts_with ~prefix:"exec-result-instances-exact:"
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
          "pattern";
          "flags";
          "input_text";
          "expected_original_source";
          "expected_original_flags";
          "expected_internal_slots";
          "expected_last_index_initial_value";
          "expected_last_index_writable";
          "expected_last_index_enumerable";
          "expected_last_index_configurable";
          "expected_behavior";
          "expected_model_field";
          "exact_case_obligation";
          "observability_reason";
          "next_action";
        ];
      Alcotest.(check string)
        "next action" "materialize_exec_result_instances_exact_case"
        (field "next_action" row))
    rows

let flags_for row =
  match Core.flags_of_string (field "flags" row) with
  | Ok flags -> flags
  | Error msg -> Alcotest.failf "%s: flags failed: %s" (field "plan_id" row) msg

let array_contains value items = Array.exists (( = ) value) items

let check_model_field row
    (observation : Core.exec_result_instance_model_observation) =
  match field "expected_model_field" row with
  | "regexp_instance_internal_slots_observed" ->
      Alcotest.(check bool)
        "OriginalSource slot" true
        observation.Core.original_source_slot_observed;
      Alcotest.(check bool)
        "OriginalFlags slot" true observation.Core.original_flags_slot_observed;
      Alcotest.(check bool)
        "RegExpRecord slot" true observation.Core.regexp_record_slot_observed;
      Alcotest.(check bool)
        "RegExpMatcher slot" true observation.Core.regexp_matcher_slot_observed;
      Alcotest.(check bool)
        "RegExpMatcher closure" true
        observation.Core.regexp_matcher_closure_observed
  | "regexp_instance_last_index_property_observed" ->
      Alcotest.(check bool)
        "lastIndex property" true observation.Core.last_index_property_observed
  | "last_index_integral_start_property_attributes_observed" ->
      Alcotest.(check bool)
        "lastIndex start index" true
        observation.Core.last_index_start_index_observed;
      Alcotest.(check bool)
        "lastIndex integral coercion" true
        observation.Core.last_index_integral_number_coercion_observed
  | model_field ->
      Alcotest.failf "%s: unsupported expected_model_field %S"
        (field "plan_id" row) model_field

let check_instance_case row =
  let flags = flags_for row in
  match Core.compile ~flags (field "pattern" row) with
  | Error msg ->
      Alcotest.failf
        "exec-result instance exact case failed to compile: plan=%s \
         requirement=%s pattern=%S flags=%S error=%s"
        (field "plan_id" row)
        (field "requirement_id" row)
        (field "pattern" row) (field "flags" row) msg
  | Ok regexp ->
      let observation = Core.inspect_exec_result_instance_model regexp in
      check_model_field row observation;
      Alcotest.(check string)
        "OriginalSource"
        (field "expected_original_source" row)
        observation.Core.original_source;
      Alcotest.(check string)
        "OriginalFlags"
        (field "expected_original_flags" row)
        observation.Core.original_flags;
      Alcotest.(check string)
        "internal slots"
        (field "expected_internal_slots" row)
        (String.concat "," (Array.to_list observation.Core.internal_slots));
      Alcotest.(check int)
        "lastIndex initial value"
        (parse_int_field row "expected_last_index_initial_value")
        observation.Core.last_index_initial_value;
      Alcotest.(check bool)
        "lastIndex writable"
        (parse_bool_field row "expected_last_index_writable")
        observation.Core.last_index_writable;
      Alcotest.(check bool)
        "lastIndex enumerable"
        (parse_bool_field row "expected_last_index_enumerable")
        observation.Core.last_index_enumerable;
      Alcotest.(check bool)
        "lastIndex configurable"
        (parse_bool_field row "expected_last_index_configurable")
        observation.Core.last_index_configurable;
      Alcotest.(check bool)
        "expected model field recorded" true
        (array_contains
           (field "expected_model_field" row)
           observation.Core.observed_model_fields)

let test_exact_plan_exec_cases () =
  plan_rows () |> planned_rows |> List.iter check_instance_case

let () =
  Alcotest.run "ecma262-exec-result-instances-exact-plan"
    [
      ( "manifest",
        [
          Alcotest.test_case "exec-result instances exact plan invariants"
            `Quick test_exact_plan_manifest;
        ] );
      ( "exec",
        [
          Alcotest.test_case "exec-result instances exact planned cases" `Quick
            test_exact_plan_exec_cases;
        ] );
    ]
