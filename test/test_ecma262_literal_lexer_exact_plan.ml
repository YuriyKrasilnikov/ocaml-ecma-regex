let repo_root () =
  let cwd = Sys.getcwd () in
  let rec climb dir =
    let candidate =
      Filename.concat dir "cache/ecma262-regexp-literal-lexer-exact-plan.tsv"
    in
    if Sys.file_exists candidate then dir
    else
      let parent = Filename.dirname dir in
      if parent = dir then
        Alcotest.fail
          "cache/ecma262-regexp-literal-lexer-exact-plan.tsv is missing; \
           run tools/build_ecma262_regexp_literal_lexer_exact_plan.py"
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
  read_tsv [ "cache"; "ecma262-regexp-literal-lexer-exact-plan.tsv" ]

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
       && field "coverage_credit" row = "none_literal_lexer_exact_planned")
    rows

let test_exact_plan_manifest () =
  let rows = plan_rows () in
  Alcotest.(check int) "literal lexer exact plan rows" 3 (List.length rows);
  let executable = executable_rows rows in
  Alcotest.(check int) "executable planned rows" 3 (List.length executable);
  let state_counts = count_by "plan_state" rows in
  check_count state_counts "planned_not_executable" 3;
  let credit_counts = count_by "coverage_credit" rows in
  check_count credit_counts "none_literal_lexer_exact_planned" 3;
  let expected_counts = count_by "expected_behavior" rows in
  check_count expected_counts "literal_parse_ok" 3;
  let layer_counts = count_by "executable_layer" rows in
  check_count layer_counts "literal_lexer" 3;
  let family_counts = count_by "mapping_family" rows in
  check_count family_counts "literal_lexer_exact" 3;
  List.iter
    (fun row ->
       if field "exact_case_id" row = "" then
         Alcotest.failf "%s: exact_case_id is empty" (field "plan_id" row);
       if
         not
           (String.starts_with ~prefix:"literal-lexer-exact:"
              (field "exact_case_id" row))
       then Alcotest.failf "%s: exact_case_id has wrong prefix"
           (field "plan_id" row);
       if field "literal_source" row = "" then
         Alcotest.failf "%s: literal_source is empty" (field "plan_id" row);
       if field "expected_flag_text" row = "" then
         Alcotest.failf "%s: expected_flag_text is empty" (field "plan_id" row);
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

let check_literal index total row =
  match Ecma_regex.regexp_literal_of_string (field "literal_source" row) with
  | Error msg ->
    Alcotest.failf
      "literal lexer exact case failed (%d/%d): plan=%s requirement=%s \
       literal=%S error=%s"
      (index + 1) total
      (field "plan_id" row)
      (field "requirement_id" row)
      (field "literal_source" row)
      msg
  | Ok literal ->
    Alcotest.(check string)
      "pattern text"
      (field "expected_pattern_text" row)
      literal.Ecma_regex.pattern_text;
    Alcotest.(check string)
      "flag text"
      (field "expected_flag_text" row)
      literal.Ecma_regex.flag_text

let test_exact_plan_literal_cases () =
  let rows = plan_rows () |> executable_rows in
  List.iteri (fun index row -> check_literal index (List.length rows) row) rows

let () =
  Alcotest.run "ecma262-literal-lexer-exact-plan" [
    ("manifest", [
      Alcotest.test_case "literal lexer exact plan invariants" `Quick
        test_exact_plan_manifest;
    ]);
    ("literal", [
      Alcotest.test_case "literal lexer exact planned cases" `Quick
        test_exact_plan_literal_cases;
    ]);
  ]
