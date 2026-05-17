module Core = Ecma_regex__Ecma_regex_core

let repo_root () =
  let cwd = Sys.getcwd () in
  let rec climb dir =
    let candidate =
      Filename.concat dir
        "cache/ecma262-regexp-match-engine-character-classes-exact-plan.tsv"
    in
    if Sys.file_exists candidate then dir
    else
      let parent = Filename.dirname dir in
      if parent = dir then
        Alcotest.fail
          "cache/ecma262-regexp-match-engine-character-classes-exact-plan.tsv \
           is missing; run \
           tools/build_ecma262_regexp_match_engine_character_classes_exact_plan.py"
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
      "ecma262-regexp-match-engine-character-classes-exact-plan.tsv";
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
          = "none_match_engine_character_classes_exact_planned")
    rows

let deferred_rows rows =
  List.filter
    (fun row ->
       field "plan_state" row = "deferred_requires_allcharacters_model"
       && field "coverage_credit" row
          = "none_match_engine_character_classes_exact_deferred")
    rows

let expected_range_observations = [
  "character_range_operation";
  "character_range_singleton_assert";
  "character_range_start_char_read";
  "character_range_end_char_read";
  "character_range_start_code";
  "character_range_end_code";
  "character_range_order_assert";
  "character_range_inclusive_return";
]

let expected_complement_observations = [
  "character_complement_operation";
  "character_complement_all_characters";
  "character_complement_difference_return";
]

let test_exact_plan_manifest () =
  let rows = plan_rows () in
  Alcotest.(check int) "character-class exact plan rows" 11 (List.length rows);
  Alcotest.(check int) "planned executable rows" 11 (List.length (planned_rows rows));
  Alcotest.(check int) "deferred rows" 0 (List.length (deferred_rows rows));
  let state_counts = count_by "plan_state" rows in
  check_count state_counts "planned_not_executable" 11;
  check_count state_counts "deferred_requires_allcharacters_model" 0;
  let credit_counts = count_by "coverage_credit" rows in
  check_count credit_counts "none_match_engine_character_classes_exact_planned" 11;
  check_count credit_counts "none_match_engine_character_classes_exact_deferred" 0;
  let behavior_counts = count_by "expected_behavior" rows in
  check_count behavior_counts "character_range_exact_plan_observable" 8;
  check_count behavior_counts "character_complement_exact_plan_observable" 3;
  check_count behavior_counts "requires_allcharacters_model" 0;
  let search_counts = count_by "expected_search_result" rows in
  check_count search_counts "true" 11;
  check_count search_counts "not_observable" 0;
  let observation_counts = count_by "expected_observation" rows in
  List.iter (fun name -> check_count observation_counts name 1)
    (expected_range_observations @ expected_complement_observations);
  let layer_counts = count_by "executable_layer" rows in
  check_count layer_counts "match_engine" 11;
  let mapping_counts = count_by "mapping_family" rows in
  check_count mapping_counts "match_engine_character_classes" 11;
  let subfamily_counts = count_by "character_class_subfamily" rows in
  check_count subfamily_counts "character_range" 8;
  check_count subfamily_counts "character_complement" 3;
  let route_counts = count_by "character_class_route" rows in
  check_count route_counts "character_range_runtime_semantics" 8;
  check_count route_counts "character_complement_allcharacters_policy" 3;
  let observability_counts = count_by "observability_status" rows in
  check_count observability_counts "character_range_model_observable" 8;
  check_count observability_counts
    "character_complement_allcharacters_model_observable" 3;
  check_count observability_counts "requires_allcharacters_model" 0;
  List.iter
    (fun row ->
       if
         not
           (String.starts_with
              ~prefix:"match-engine-character-classes-exact:"
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
           "expected_observation";
           "exact_case_obligation";
           "observability_reason";
         ];
       if field "character_class_subfamily" row = "character_range" then begin
         Alcotest.(check string)
           "expected observed"
           "true"
           (field "expected_observed" row);
         Alcotest.(check string)
           "next action"
           "materialize_match_engine_character_class_exact_case"
           (field "next_action" row)
       end
       else begin
         Alcotest.(check string)
           "complement expected observed"
           "true"
           (field "expected_observed" row);
         Alcotest.(check string)
           "complement next action"
           "materialize_match_engine_character_class_exact_case"
           (field "next_action" row)
       end;
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
  | "character_range_operation" ->
    observation.Core.character_range_operation_observed
  | "character_range_singleton_assert" ->
    observation.Core.character_range_singleton_assert_observed
  | "character_range_start_char_read" ->
    observation.Core.character_range_start_char_read_observed
  | "character_range_end_char_read" ->
    observation.Core.character_range_end_char_read_observed
  | "character_range_start_code" ->
    observation.Core.character_range_start_code_observed
  | "character_range_end_code" ->
    observation.Core.character_range_end_code_observed
  | "character_range_order_assert" ->
    observation.Core.character_range_order_assert_observed
  | "character_range_inclusive_return" ->
    observation.Core.character_range_inclusive_return_observed
  | "character_complement_operation" ->
    observation.Core.character_complement_operation_observed
  | "character_complement_all_characters" ->
    observation.Core.character_complement_all_characters_observed
  | "character_complement_difference_return" ->
    observation.Core.character_complement_difference_return_observed
  | name -> Alcotest.failf "unknown observation %S" name

let check_character_class_case row =
  let flags = flags_for row in
  match Core.compile ~flags (field "pattern" row) with
  | Error msg ->
    Alcotest.failf
      "character-class exact case failed to compile: plan=%s requirement=%s \
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
      Core.inspect_character_class_model regexp (field "input_text" row)
    in
    Alcotest.(check bool)
      (field "expected_observation" row)
      true
      (observation_value observation (field "expected_observation" row));
    if field "character_class_subfamily" row = "character_complement" then begin
      Alcotest.(check bool)
        "AllCharacters code-unit universe observed"
        true
        observation.Core.character_complement_allcharacters_code_unit_universe_observed;
      Alcotest.(check bool)
        "AllCharacters code-point universe not claimed"
        false
        observation.Core.character_complement_allcharacters_code_point_universe_observed;
      Alcotest.(check bool)
        "AllCharacters case-fold-stable universe not claimed"
        false
        observation.Core.character_complement_allcharacters_case_fold_stable_universe_observed;
      Alcotest.(check bool)
        "CharacterComplement difference membership observed"
        true
        observation.Core.character_complement_difference_membership_observed;
      Alcotest.(check bool)
        "public search excludes set member"
        false
        (Core.search regexp "a")
    end

let test_exact_plan_character_class_cases () =
  plan_rows ()
  |> planned_rows
  |> List.iter check_character_class_case

let () =
  Alcotest.run "ecma262-match-engine-character-classes-exact-plan" [
    ("manifest", [
      Alcotest.test_case "character-class exact plan invariants" `Quick
        test_exact_plan_manifest;
    ]);
    ("model", [
      Alcotest.test_case "character-class exact planned cases" `Quick
        test_exact_plan_character_class_cases;
    ]);
  ]
