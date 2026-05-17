let repo_root () =
  let cwd = Sys.getcwd () in
  let rec climb dir =
    let candidate =
      Filename.concat dir "cache/ecma262-regexp-compile-parser-exact-plan.tsv"
    in
    if Sys.file_exists candidate then dir
    else
      let parent = Filename.dirname dir in
      if parent = dir then
        Alcotest.fail
          "cache/ecma262-regexp-compile-parser-exact-plan.tsv is missing; \
           run tools/build_ecma262_regexp_compile_parser_exact_plan.py"
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
  read_tsv [ "cache"; "ecma262-regexp-compile-parser-exact-plan.tsv" ]

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
       && field "coverage_credit" row = "none_compile_parser_exact_planned")
    rows

let compile_row row =
  let pattern = field "planned_pattern" row in
  let flags_source = field "planned_flags" row in
  if flags_source = "" then Ecma_regex.compile pattern
  else
    match Ecma_regex.flags_of_string flags_source with
    | Error msg ->
      Error
        (Printf.sprintf
           "planned flags should parse: flags=%S error=%s"
           flags_source msg)
    | Ok flags -> Ecma_regex.compile ~flags pattern

let failure_line row msg =
  Printf.sprintf
    "plan_id=%s requirement=%s family=%s expected=%s pattern=%S flags=%S \
     error=%s"
    (field "plan_id" row)
    (field "requirement_id" row)
    (field "exact_case_family" row)
    (field "expected_behavior" row)
    (field "planned_pattern" row)
    (field "planned_flags" row)
    msg

let summarize_failures failures =
  failures
  |> List.map (fun (row, msg) -> failure_line row msg)
  |> String.concat "\n"

let test_exact_plan_manifest () =
  let rows = plan_rows () in
  Alcotest.(check int) "exact plan rows" 21 (List.length rows);
  let executable = executable_rows rows in
  Alcotest.(check int) "executable planned rows" 21 (List.length executable);
  let state_counts = count_by "plan_state" rows in
  check_count state_counts "planned_not_executable" 21;
  let credit_counts = count_by "coverage_credit" rows in
  check_count credit_counts "none_compile_parser_exact_planned" 21;
  let expected_counts = count_by "expected_behavior" rows in
  check_count expected_counts "compile_ok" 2;
  check_count expected_counts "compile_error" 19;
  let layer_counts = count_by "executable_layer" rows in
  check_count layer_counts "compile" 1;
  check_count layer_counts "parser" 20;
  let selection_counts = count_by "selection_state" rows in
  check_count selection_counts "selected_compile_positive_case" 2;
  check_count selection_counts "needs_negative_or_local_exact_case" 19;
  List.iter
    (fun row ->
       if field "exact_case_id" row = "" then
         Alcotest.failf "%s: exact_case_id is empty" (field "plan_id" row);
       if field "planned_pattern" row = "" then
         Alcotest.failf "%s: planned_pattern is empty" (field "plan_id" row);
       if field "exact_case_obligation" row = "" then
         Alcotest.failf "%s: exact_case_obligation is empty"
           (field "plan_id" row);
       if not (source_exists (field "source_file" row)) then
         Alcotest.failf "%s: missing ECMA source %s"
           (field "plan_id" row)
           (field "source_file" row);
       if not (target_exists (field "target_test_artifact" row)) then
         Alcotest.failf "%s: missing target test artifact %s"
           (field "plan_id" row)
           (field "target_test_artifact" row))
    rows

let test_exact_plan_compile_cases () =
  let failures =
    plan_rows ()
    |> executable_rows
    |> List.filter_map
      (fun row ->
         match field "expected_behavior" row, compile_row row with
         | "compile_ok", Ok _ -> None
         | "compile_error", Error _ -> None
         | "compile_ok", Error msg -> Some (row, msg)
         | "compile_error", Ok _ ->
           Some (row, "compiled successfully but compile_error was expected")
         | other, _ -> Some (row, "unsupported expected behavior: " ^ other))
  in
  match failures with
  | [] -> ()
  | failures -> Alcotest.fail (summarize_failures failures)

let () =
  Alcotest.run "ecma262-compile-parser-exact-plan" [
    ("manifest", [
      Alcotest.test_case "compile/parser exact plan invariants" `Quick
        test_exact_plan_manifest;
    ]);
    ("compile", [
      Alcotest.test_case "compile/parser exact planned cases" `Quick
        test_exact_plan_compile_cases;
    ]);
  ]
