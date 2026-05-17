module Core = Ecma_regex__Ecma_regex_core

let repo_root () =
  let cwd = Sys.getcwd () in
  let rec climb dir =
    let candidate =
      Filename.concat dir
        "cache/ecma262-regexp-exec-result-capture-exact-plan.tsv"
    in
    if Sys.file_exists candidate then dir
    else
      let parent = Filename.dirname dir in
      if parent = dir then
        Alcotest.fail
          "cache/ecma262-regexp-exec-result-capture-exact-plan.tsv is \
           missing; run \
           tools/build_ecma262_regexp_exec_result_capture_exact_plan.py"
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
  read_tsv [ "cache"; "ecma262-regexp-exec-result-capture-exact-plan.tsv" ]

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

let planned_rows rows =
  List.filter
    (fun row ->
       field "plan_state" row = "planned_not_executable"
       && field "coverage_credit" row = "none_exec_result_capture_exact_planned")
    rows

let test_exact_plan_manifest () =
  let rows = plan_rows () in
  Alcotest.(check int) "exec-result capture exact plan rows" 13
    (List.length rows);
  Alcotest.(check int) "planned executable rows" 13
    (List.length (planned_rows rows));
  let state_counts = count_by "plan_state" rows in
  check_count state_counts "planned_not_executable" 13;
  let credit_counts = count_by "coverage_credit" rows in
  check_count credit_counts "none_exec_result_capture_exact_planned" 13;
  let family_counts = count_by "mapping_family" rows in
  check_count family_counts "exec_result_matching" 13;
  let layer_counts = count_by "executable_layer" rows in
  check_count layer_counts "exec_result" 13;
  let observability_counts = count_by "observability_status" rows in
  check_count observability_counts
    "internal_exec_result_capture_model_observable"
    13;
  let target_counts = count_by "target_test_artifact" rows in
  check_count target_counts
    "test/test_ecma262_exec_result_capture_exact_plan.ml"
    13;
  let defined_counts = count_by "expected_capture_defined" rows in
  check_count defined_counts "true" 11;
  check_count defined_counts "false" 2;
  List.iter
    (fun row ->
       if
         not
           (String.starts_with ~prefix:"exec-result-capture-exact:"
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
           "expected_capture_count";
           "expected_capture_ordinal";
           "expected_capture_defined";
           "expected_behavior";
           "expected_model_field";
           "exact_case_obligation";
           "observability_reason";
           "next_action";
         ];
       Alcotest.(check string)
         "expected exec"
         "true"
         (field "expected_exec_result" row);
       Alcotest.(check string)
         "next action"
         "materialize_exec_result_capture_exact_case"
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

let check_model_field row observation =
  match field "expected_model_field" row with
  | "capture_slot_count" ->
    Alcotest.(check int)
      "capture slot count"
      (parse_int_field row "expected_capture_count")
      observation.Core.capture_slot_count
  | "capture_count_matches_regexp_record" ->
    Alcotest.(check bool)
      "capture count matches RegExp record"
      true
      observation.Core.capture_count_matches_regexp_record
  | "capture_count_within_array_limit" ->
    Alcotest.(check bool)
      "capture count within array limit"
      true
      observation.Core.capture_count_within_array_limit
  | "undefined_capture_observed"
  | "undefined_capture_value" ->
    Alcotest.(check bool)
      "undefined capture observed"
      true
      observation.Core.undefined_capture_observed
  | "defined_capture_observed" ->
    Alcotest.(check bool)
      "defined capture observed"
      true
      observation.Core.defined_capture_observed
  | "capture_start_index_observed" ->
    Alcotest.(check bool)
      "capture start observed"
      true
      observation.Core.capture_start_index_observed
  | "capture_end_index_observed" ->
    Alcotest.(check bool)
      "capture end observed"
      true
      observation.Core.capture_end_index_observed
  | "capture_record_observed" ->
    Alcotest.(check bool)
      "capture record observed"
      true
      observation.Core.capture_record_observed
  | "captured_value_observed" ->
    Alcotest.(check bool)
      "captured value observed"
      true
      observation.Core.captured_value_observed
  | "capture_index_list_append_observed" ->
    Alcotest.(check bool)
      "capture index list append observed"
      true
      observation.Core.capture_index_list_append_observed
  | "result_capture_property_observed" ->
    Alcotest.(check bool)
      "result capture property observed"
      true
      observation.Core.result_capture_property_observed
  | "capture_slot_read" -> ()
  | model_field ->
    Alcotest.failf "%s: unsupported expected_model_field %S"
      (field "plan_id" row)
      model_field

let check_capture row observation =
  let ordinal = parse_int_field row "expected_capture_ordinal" in
  let index = ordinal - 1 in
  if index < 0 || index >= Array.length observation.Core.exec_result_captures then
    Alcotest.failf "%s: capture ordinal %d is out of range"
      (field "plan_id" row)
      ordinal;
  let capture = observation.Core.exec_result_captures.(index) in
  Alcotest.(check int) "capture index" index capture.Core.capture_index;
  if field "expected_capture_defined" row = "true" then begin
    Alcotest.(check string)
      "capture start"
      (field "expected_capture_start_index" row)
      (option_int_to_string capture.Core.capture_start_index);
    Alcotest.(check string)
      "capture end"
      (field "expected_capture_end_index" row)
      (option_int_to_string capture.Core.capture_end_index);
    Alcotest.(check string)
      "capture text"
      (field "expected_capture_text" row)
      (option_string_to_string capture.Core.captured_text)
  end
  else begin
    Alcotest.(check string)
      "undefined capture start"
      ""
      (option_int_to_string capture.Core.capture_start_index);
    Alcotest.(check string)
      "undefined capture end"
      ""
      (option_int_to_string capture.Core.capture_end_index);
    Alcotest.(check string)
      "undefined capture text"
      ""
      (option_string_to_string capture.Core.captured_text)
  end

let check_capture_case row =
  let flags = flags_for row in
  match Core.compile ~flags (field "pattern" row) with
  | Error msg ->
    Alcotest.failf
      "exec-result capture exact case failed to compile: plan=%s \
       requirement=%s pattern=%S flags=%S error=%s"
      (field "plan_id" row)
      (field "requirement_id" row)
      (field "pattern" row)
      (field "flags" row)
      msg
  | Ok regexp ->
    let observation =
      Core.inspect_exec_result_capture_model regexp (field "input_text" row)
    in
    Alcotest.(check int)
      "regexp record capture count"
      (parse_int_field row "expected_capture_count")
      observation.Core.regexp_record_capture_count;
    Alcotest.(check int)
      "capture slot count"
      (parse_int_field row "expected_capture_count")
      observation.Core.capture_slot_count;
    check_model_field row observation;
    check_capture row observation

let test_exact_plan_capture_cases () =
  plan_rows ()
  |> planned_rows
  |> List.iter check_capture_case

let () =
  Alcotest.run "ecma262-exec-result-capture-exact-plan" [
    ("manifest", [
      Alcotest.test_case "exec-result capture exact plan invariants" `Quick
        test_exact_plan_manifest;
    ]);
    ("capture", [
      Alcotest.test_case "exec-result capture exact planned cases" `Quick
        test_exact_plan_capture_cases;
    ]);
  ]
