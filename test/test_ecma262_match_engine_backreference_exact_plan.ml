module Core = Ecma_regex__Ecma_regex_core

let repo_root () =
  let cwd = Sys.getcwd () in
  let rec climb dir =
    let candidate =
      Filename.concat dir "cache/ecma262-regexp-match-engine-backreference-exact-plan.tsv"
    in
    if Sys.file_exists candidate then dir
    else
      let parent = Filename.dirname dir in
      if parent = dir then
        Alcotest.fail
          "cache/ecma262-regexp-match-engine-backreference-exact-plan.tsv is \
           missing; run \
           tools/build_ecma262_regexp_match_engine_backreference_exact_plan.py"
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
  read_tsv [ "cache"; "ecma262-regexp-match-engine-backreference-exact-plan.tsv" ]

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
          = "none_match_engine_backreference_exact_planned")
    rows

let expected_observations = [
  "decimal_backreference_atom";
  "decimal_capturing_group_number";
  "decimal_group_count_assert";
  "decimal_backreference_matcher_return";
  "named_backreference_atom";
  "named_matching_group_specifiers";
  "named_paren_indices_list";
  "named_group_specifier_iteration";
  "named_count_left_capturing_parens";
  "named_paren_index_append";
  "named_backreference_matcher_return";
]

let test_exact_plan_manifest () =
  let rows = plan_rows () in
  Alcotest.(check int) "backreference exact plan rows" 11 (List.length rows);
  let planned = planned_rows rows in
  Alcotest.(check int) "planned executable rows" 11 (List.length planned);
  let state_counts = count_by "plan_state" rows in
  check_count state_counts "planned_not_executable" 11;
  let credit_counts = count_by "coverage_credit" rows in
  check_count credit_counts "none_match_engine_backreference_exact_planned" 11;
  let behavior_counts = count_by "expected_behavior" rows in
  check_count behavior_counts "backreference_model_observable" 11;
  let search_counts = count_by "expected_search_result" rows in
  check_count search_counts "true" 11;
  let observation_counts = count_by "expected_observation" rows in
  List.iter (fun name -> check_count observation_counts name 1) expected_observations;
  let layer_counts = count_by "executable_layer" rows in
  check_count layer_counts "match_engine" 11;
  let mapping_counts = count_by "mapping_family" rows in
  check_count mapping_counts "match_engine_atoms" 11;
  let subfamily_counts = count_by "backreference_subfamily" rows in
  check_count subfamily_counts "decimal_backreference_atom_escape" 4;
  check_count subfamily_counts "named_backreference_atom_escape" 7;
  let route_counts = count_by "backreference_semantic_route" rows in
  check_count route_counts "capture_backreference_runtime_model" 4;
  check_count route_counts "named_capture_backreference_runtime_model" 7;
  let observability_counts = count_by "observability_status" rows in
  check_count observability_counts "backreference_model_observable" 11;
  List.iter
    (fun row ->
       if
         not
           (String.starts_with ~prefix:"match-engine-backreference-exact:"
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
  | "decimal_backreference_atom" ->
    observation.Core.decimal_backreference_atom_observed
  | "decimal_capturing_group_number" ->
    observation.Core.decimal_capturing_group_number_observed
  | "decimal_group_count_assert" ->
    observation.Core.decimal_group_count_assert_observed
  | "decimal_backreference_matcher_return" ->
    observation.Core.decimal_backreference_matcher_return_observed
  | "named_backreference_atom" ->
    observation.Core.named_backreference_atom_observed
  | "named_matching_group_specifiers" ->
    observation.Core.named_matching_group_specifiers_observed
  | "named_paren_indices_list" ->
    observation.Core.named_paren_indices_list_observed
  | "named_group_specifier_iteration" ->
    observation.Core.named_group_specifier_iteration_observed
  | "named_count_left_capturing_parens" ->
    observation.Core.named_count_left_capturing_parens_observed
  | "named_paren_index_append" ->
    observation.Core.named_paren_index_append_observed
  | "named_backreference_matcher_return" ->
    observation.Core.named_backreference_matcher_return_observed
  | name -> Alcotest.failf "unknown observation %S" name

let check_backreference_case row =
  let flags = flags_for row in
  match Core.compile ~flags (field "pattern" row) with
  | Error msg ->
    Alcotest.failf
      "backreference exact case failed to compile: plan=%s requirement=%s \
       pattern=%S flags=%S error=%s"
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
      Core.inspect_backreference_model regexp (field "input_text" row)
    in
    Alcotest.(check bool)
      (field "expected_observation" row)
      true
      (observation_value observation (field "expected_observation" row))

let test_exact_plan_backreference_cases () =
  plan_rows ()
  |> planned_rows
  |> List.iter check_backreference_case

let compile_or_fail pattern =
  match Core.compile pattern with
  | Ok regexp -> regexp
  | Error msg -> Alcotest.failf "compile %S failed: %s" pattern msg

let check_search pattern input expected =
  let regexp = compile_or_fail pattern in
  Alcotest.(check bool) pattern expected (Core.search regexp input)

let test_backreference_runtime_semantics () =
  check_search "(a)\\1" "aa" true;
  check_search "(a)\\1" "ab" false;
  check_search "(?<x>a)\\k<x>" "aa" true;
  check_search "(?<x>a)\\k<x>" "ab" false;
  check_search "(a|)\\1" "" true;
  check_search "(a|(b))\\2" "a" true;
  check_search "(?<x>a)|(?<x>b)\\k<x>" "bb" true

let () =
  Alcotest.run "ecma262-match-engine-backreference-exact-plan" [
    ("manifest", [
      Alcotest.test_case "backreference exact plan invariants" `Quick
        test_exact_plan_manifest;
    ]);
    ("model", [
      Alcotest.test_case "backreference exact planned cases" `Quick
        test_exact_plan_backreference_cases;
      Alcotest.test_case "backreference runtime semantics" `Quick
        test_backreference_runtime_semantics;
    ]);
  ]
