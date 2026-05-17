module Core = Ecma_regex__Ecma_regex_core

let repo_root () =
  let cwd = Sys.getcwd () in
  let rec climb dir =
    let candidate =
      Filename.concat dir "cache/ecma262-regexp-match-engine-atoms-exact-plan.tsv"
    in
    if Sys.file_exists candidate then dir
    else
      let parent = Filename.dirname dir in
      if parent = dir then
        Alcotest.fail
          "cache/ecma262-regexp-match-engine-atoms-exact-plan.tsv is missing; \
           run tools/build_ecma262_regexp_match_engine_atoms_exact_plan.py"
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
  read_tsv [ "cache"; "ecma262-regexp-match-engine-atoms-exact-plan.tsv" ]

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
       && field "coverage_credit" row = "none_match_engine_atoms_exact_planned")
    rows

let search_rows rows =
  rows
  |> executable_rows
  |> List.filter
       (fun row -> field "observability_status" row = "search_bool_observable")

let compile_atom_model_rows rows =
  rows
  |> executable_rows
  |> List.filter
       (fun row ->
          field "observability_status" row
          = "compile_atom_operation_model_observable")

let deferred_rows rows =
  List.filter
    (fun row ->
       String.starts_with ~prefix:"deferred_" (field "plan_state" row)
       && field "coverage_credit" row = "none_match_engine_atoms_exact_deferred")
    rows

let parse_expected_bool row =
  match field "expected_search_result" row with
  | "true" -> true
  | "false" -> false
  | other ->
    Alcotest.failf "%s: invalid expected_search_result %S"
      (field "plan_id" row)
      other

let decode_text source =
  let buffer = Buffer.create (String.length source) in
  let rec loop index =
    if index = String.length source then Buffer.contents buffer
    else if
      source.[index] = '\\'
      && index + 1 < String.length source
    then begin
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

let test_exact_plan_manifest () =
  let rows = plan_rows () in
  Alcotest.(check int) "remaining atom exact plan rows" 96 (List.length rows);
  Alcotest.(check int) "planned executable rows" 19
    (List.length (executable_rows rows));
  Alcotest.(check int) "search-observable rows" 17
    (List.length (search_rows rows));
  Alcotest.(check int) "CompileAtom model-observable rows" 2
    (List.length (compile_atom_model_rows rows));
  Alcotest.(check int) "deferred rows" 77 (List.length (deferred_rows rows));
  let state_counts = count_by "plan_state" rows in
  check_count state_counts "planned_not_executable" 19;
  check_count state_counts "deferred_requires_capture_model" 23;
  check_count state_counts "deferred_requires_capture_backreference_model" 4;
  check_count state_counts "deferred_requires_compile_atom_operation_model" 0;
  check_count state_counts "deferred_requires_compile_atom_piecewise_inventory" 0;
  check_count state_counts "deferred_requires_modifier_runtime_model" 10;
  check_count state_counts "deferred_requires_named_backreference_model" 7;
  check_count state_counts "deferred_requires_unicode_sets_string_element_model" 33;
  let subfamily_counts = count_by "atom_subfamily" rows in
  check_count subfamily_counts "character_class_escape_single_code_point" 3;
  check_count subfamily_counts "character_class_escape_unicode_sets_string_elements" 16;
  check_count subfamily_counts "character_class_single_code_point" 4;
  check_count subfamily_counts "character_class_unicode_sets_string_elements" 17;
  check_count subfamily_counts "character_escape_atom_escape" 5;
  check_count subfamily_counts "compile_atom_operation_shape" 1;
  check_count subfamily_counts "compile_atom_piecewise_dispatch" 1;
  check_count subfamily_counts "capturing_group_atom" 23;
  check_count subfamily_counts "decimal_backreference_atom_escape" 4;
  check_count subfamily_counts "dot_atom" 5;
  check_count subfamily_counts "modifiers_group_atom" 10;
  check_count subfamily_counts "named_backreference_atom_escape" 7;
  let behavior_counts = count_by "expected_search_result" rows in
  check_count behavior_counts "true" 13;
  check_count behavior_counts "false" 4;
  check_count behavior_counts "model_observable" 2;
  check_count behavior_counts "not_observable" 77;
  List.iter
    (fun row ->
       Alcotest.(check string) "mapping_family" "match_engine_atoms"
         (field "mapping_family" row);
       Alcotest.(check string) "executable_layer" "match_engine"
         (field "executable_layer" row);
       if field "exact_case_id" row = "" then
         Alcotest.failf "%s: exact_case_id is empty" (field "plan_id" row);
       if
         not
           (String.starts_with ~prefix:"match-engine-atoms-exact:"
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
         if field "pattern" row = "" then
           Alcotest.failf "%s: pattern is empty" (field "plan_id" row);
         if field "input_text" row = "" then
           Alcotest.failf "%s: input_text is empty" (field "plan_id" row);
         (match field "observability_status" row with
          | "search_bool_observable" ->
            if field "expected_search_result" row <> "true"
               && field "expected_search_result" row <> "false"
            then
              Alcotest.failf
                "%s: search row has invalid expected_search_result %S"
                (field "plan_id" row)
                (field "expected_search_result" row)
          | "compile_atom_operation_model_observable" ->
            Alcotest.(check string)
              "CompileAtom model expected search"
              "model_observable"
              (field "expected_search_result" row);
            Alcotest.(check string)
              "CompileAtom model route"
              "operation_model"
              (field "atom_semantic_route" row)
          | other ->
            Alcotest.failf "%s: unexpected observability_status %S"
              (field "plan_id" row)
              other);
         Alcotest.(check string)
           "executable next action"
           "materialize_match_engine_atoms_exact_case"
           (field "next_action" row);
         if not (target_exists (field "target_test_artifact" row)) then
           Alcotest.failf "%s: missing target test artifact %s"
             (field "plan_id" row)
             (field "target_test_artifact" row)
       end
       else begin
         Alcotest.(check string) "deferred pattern" "" (field "pattern" row);
         Alcotest.(check string) "deferred input" "" (field "input_text" row);
         Alcotest.(check string)
           "deferred expected search"
           "not_observable"
           (field "expected_search_result" row);
         Alcotest.(check string)
           "deferred target"
           ""
           (field "target_test_artifact" row)
       end)
    rows

let flags_for row =
  match Ecma_regex.flags_of_string (field "flags" row) with
  | Ok flags -> flags
  | Error msg ->
    Alcotest.failf "%s: flags failed: %s" (field "plan_id" row) msg

let core_flags_for row =
  match Core.flags_of_string (field "flags" row) with
  | Ok flags -> flags
  | Error msg ->
    Alcotest.failf "%s: core flags failed: %s" (field "plan_id" row) msg

let check_match index total row =
  let flags = flags_for row in
  match Ecma_regex.compile ~flags (field "pattern" row) with
  | Error msg ->
    Alcotest.failf
      "match-engine atom case failed to compile (%d/%d): plan=%s \
       requirement=%s pattern=%S flags=%S error=%s"
      (index + 1) total
      (field "plan_id" row)
      (field "requirement_id" row)
      (field "pattern" row)
      (field "flags" row)
      msg
  | Ok regexp ->
    Alcotest.(check bool)
      (field "exact_case_id" row)
      (parse_expected_bool row)
      (Ecma_regex.search regexp (decode_text (field "input_text" row)))

let test_exact_plan_match_cases () =
  let rows = plan_rows () |> search_rows in
  List.iteri (fun index row -> check_match index (List.length rows) row) rows

let compile_atom_observation_value observation = function
  | "compile_atom_operation_shape_observed" ->
    observation.Core.compile_atom_operation_shape_observed
  | "compile_atom_piecewise_dispatch_observed" ->
    observation.Core.compile_atom_piecewise_dispatch_observed
  | name -> Alcotest.failf "unknown CompileAtom observation %S" name

let check_compile_atom_model row =
  let flags = core_flags_for row in
  match Core.compile ~flags (field "pattern" row) with
  | Error msg ->
    Alcotest.failf
      "CompileAtom model case failed to compile: plan=%s requirement=%s \
       pattern=%S flags=%S error=%s"
      (field "plan_id" row)
      (field "requirement_id" row)
      (field "pattern" row)
      (field "flags" row)
      msg
  | Ok regexp ->
    let observation = Core.inspect_compile_atom_model regexp in
    Alcotest.(check bool)
      (field "expected_behavior" row)
      true
      (compile_atom_observation_value observation (field "expected_behavior" row))

let test_exact_plan_compile_atom_model_cases () =
  plan_rows ()
  |> compile_atom_model_rows
  |> List.iter check_compile_atom_model

let () =
  Alcotest.run "ecma262-match-engine-atoms-exact-plan" [
    ("manifest", [
      Alcotest.test_case "match-engine atom exact plan invariants" `Quick
        test_exact_plan_manifest;
    ]);
    ("match", [
      Alcotest.test_case "match-engine atom exact planned cases" `Quick
        test_exact_plan_match_cases;
    ]);
    ("model", [
      Alcotest.test_case "CompileAtom operation model planned cases" `Quick
        test_exact_plan_compile_atom_model_cases;
    ]);
  ]
