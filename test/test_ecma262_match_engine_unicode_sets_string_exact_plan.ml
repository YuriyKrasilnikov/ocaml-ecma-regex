module Core = Ecma_regex__Ecma_regex_core

let repo_root () =
  let cwd = Sys.getcwd () in
  let rec climb dir =
    let candidate =
      Filename.concat dir
        "cache/ecma262-regexp-match-engine-unicode-sets-string-exact-plan.tsv"
    in
    if Sys.file_exists candidate then dir
    else
      let parent = Filename.dirname dir in
      if parent = dir then
        Alcotest.fail
          "cache/ecma262-regexp-match-engine-unicode-sets-string-exact-plan.tsv \
           is missing; run \
           tools/build_ecma262_regexp_match_engine_unicode_sets_string_exact_plan.py"
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
    "ecma262-regexp-match-engine-unicode-sets-string-exact-plan.tsv";
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
          = "none_match_engine_unicode_sets_string_exact_planned")
    rows

let expected_observations = [
  "unicode_sets_character_class_invert_false_assert";
  "unicode_sets_matcher_list_initialized";
  "unicode_sets_multi_char_elements_descending_iteration";
  "unicode_sets_last_code_point_charset";
  "unicode_sets_last_code_point_matcher";
  "unicode_sets_prefix_code_point_iteration";
  "unicode_sets_prefix_code_point_charset";
  "unicode_sets_prefix_code_point_matcher";
  "unicode_sets_match_sequence_built";
  "unicode_sets_multi_matcher_appended";
  "unicode_sets_singles_charset_built";
  "unicode_sets_singles_matcher_appended";
  "unicode_sets_empty_sequence_checked";
  "unicode_sets_empty_matcher_appended";
  "unicode_sets_last_matcher_selected";
  "unicode_sets_match_two_alternatives_fold";
  "unicode_sets_final_matcher_return";
]

let test_exact_plan_manifest () =
  let rows = plan_rows () in
  Alcotest.(check int) "UnicodeSets string exact plan rows" 17 (List.length rows);
  let planned = planned_rows rows in
  Alcotest.(check int) "planned executable rows" 17 (List.length planned);
  let state_counts = count_by "plan_state" rows in
  check_count state_counts "planned_not_executable" 17;
  let credit_counts = count_by "coverage_credit" rows in
  check_count credit_counts
    "none_match_engine_unicode_sets_string_exact_planned" 17;
  let behavior_counts = count_by "expected_behavior" rows in
  check_count behavior_counts "unicode_sets_string_element_model_observable" 17;
  let observation_counts = count_by "expected_observation" rows in
  List.iter (fun name -> check_count observation_counts name 1) expected_observations;
  let mapping_counts = count_by "mapping_family" rows in
  check_count mapping_counts "match_engine_atoms" 17;
  let layer_counts = count_by "executable_layer" rows in
  check_count layer_counts "match_engine" 17;
  let subfamily_counts = count_by "unicode_sets_subfamily" rows in
  check_count subfamily_counts "character_class_unicode_sets_string_elements" 17;
  let route_counts = count_by "unicode_sets_semantic_route" rows in
  check_count route_counts "unicode_sets_string_element_matcher_model" 17;
  let observability_counts = count_by "observability_status" rows in
  check_count observability_counts
    "unicode_sets_string_element_model_observable" 17;
  List.iter
    (fun row ->
       if
         not
           (String.starts_with ~prefix:"match-engine-unicode-sets-string-exact:"
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
           "flags";
           "input_text";
           "expected_exec_text";
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
  | "unicode_sets_character_class_invert_false_assert" ->
    observation.Core.unicode_sets_character_class_invert_false_assert_observed
  | "unicode_sets_matcher_list_initialized" ->
    observation.Core.unicode_sets_matcher_list_initialized_observed
  | "unicode_sets_multi_char_elements_descending_iteration" ->
    observation.Core.unicode_sets_multi_char_elements_descending_iteration_observed
  | "unicode_sets_last_code_point_charset" ->
    observation.Core.unicode_sets_last_code_point_charset_observed
  | "unicode_sets_last_code_point_matcher" ->
    observation.Core.unicode_sets_last_code_point_matcher_observed
  | "unicode_sets_prefix_code_point_iteration" ->
    observation.Core.unicode_sets_prefix_code_point_iteration_observed
  | "unicode_sets_prefix_code_point_charset" ->
    observation.Core.unicode_sets_prefix_code_point_charset_observed
  | "unicode_sets_prefix_code_point_matcher" ->
    observation.Core.unicode_sets_prefix_code_point_matcher_observed
  | "unicode_sets_match_sequence_built" ->
    observation.Core.unicode_sets_match_sequence_built_observed
  | "unicode_sets_multi_matcher_appended" ->
    observation.Core.unicode_sets_multi_matcher_appended_observed
  | "unicode_sets_singles_charset_built" ->
    observation.Core.unicode_sets_singles_charset_built_observed
  | "unicode_sets_singles_matcher_appended" ->
    observation.Core.unicode_sets_singles_matcher_appended_observed
  | "unicode_sets_empty_sequence_checked" ->
    observation.Core.unicode_sets_empty_sequence_checked_observed
  | "unicode_sets_empty_matcher_appended" ->
    observation.Core.unicode_sets_empty_matcher_appended_observed
  | "unicode_sets_last_matcher_selected" ->
    observation.Core.unicode_sets_last_matcher_selected_observed
  | "unicode_sets_match_two_alternatives_fold" ->
    observation.Core.unicode_sets_match_two_alternatives_fold_observed
  | "unicode_sets_final_matcher_return" ->
    observation.Core.unicode_sets_final_matcher_return_observed
  | name -> Alcotest.failf "unknown observation %S" name

let check_unicode_sets_case row =
  let flags = flags_for row in
  match Core.compile ~flags (field "pattern" row) with
  | Error msg ->
    Alcotest.failf
      "UnicodeSets string exact case failed to compile: plan=%s requirement=%s \
       pattern=%S flags=%S error=%s"
      (field "plan_id" row)
      (field "requirement_id" row)
      (field "pattern" row)
      (field "flags" row)
      msg
  | Ok regexp ->
    let input = field "input_text" row in
    (match Core.exec regexp input with
     | None ->
       Alcotest.failf "%s: expected exec match" (field "plan_id" row)
     | Some result ->
       Alcotest.(check string)
         "exec matched text"
         (field "expected_exec_text" row)
         result.Core.matched_text);
    let observation =
      Core.inspect_unicode_sets_string_element_model regexp input
    in
    Alcotest.(check bool)
      (field "expected_observation" row)
      true
      (observation_value observation (field "expected_observation" row))

let test_exact_plan_unicode_sets_cases () =
  plan_rows ()
  |> planned_rows
  |> List.iter check_unicode_sets_case

let () =
  Alcotest.run "ecma262-match-engine-unicode-sets-string-exact-plan" [
    ("manifest", [
      Alcotest.test_case "UnicodeSets string exact plan invariants" `Quick
        test_exact_plan_manifest;
    ]);
    ("model", [
      Alcotest.test_case "UnicodeSets string exact planned cases" `Quick
        test_exact_plan_unicode_sets_cases;
    ]);
  ]
