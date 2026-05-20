let repo_root () =
  let cwd = Sys.getcwd () in
  let rec climb dir =
    let candidate =
      Filename.concat dir "cache/ecma262-regexp-test-evidence.tsv"
    in
    if Sys.file_exists candidate then dir
    else
      let parent = Filename.dirname dir in
      if parent = dir then
        Alcotest.fail
          "cache/ecma262-regexp-test-evidence.tsv is missing; run \
           tools/build_ecma262_regexp_test_evidence.py"
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

let evidence_rows () = read_tsv [ "cache"; "ecma262-regexp-test-evidence.tsv" ]

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

let source_exists case_source =
  match String.split_on_char ':' case_source with
  | source_path :: _ ->
      Sys.file_exists (path [ "external"; "test262"; source_path ])
  | [] -> false

let executable_rows rows =
  List.filter (fun row -> field "case_id" row <> "") rows

let test_evidence_manifest () =
  let rows = evidence_rows () in
  Alcotest.(check int) "evidence rows" 410 (List.length rows);
  Alcotest.(check int)
    "executable evidence rows" 410
    (List.length (executable_rows rows));
  let scope_counts = count_by "evidence_scope" rows in
  check_count scope_counts "ecma262_requirement" 0;
  check_count scope_counts "test262_negative_syntax_corpus" 410;
  let kind_counts = count_by "evidence_kind" rows in
  check_count kind_counts "selected_compile_positive_case" 0;
  check_count kind_counts "open_negative_or_local_exact_mapping" 0;
  check_count kind_counts "unmapped_negative_syntax_case" 410;
  let expected_counts = count_by "expected_behavior" rows in
  check_count expected_counts "compile_ok" 0;
  check_count expected_counts "compile_error" 410;
  check_count expected_counts "compile_error_or_local_exact_needed" 0;
  let credit_counts = count_by "coverage_credit" rows in
  check_count credit_counts "none_candidate_not_exact" 0;
  check_count credit_counts "none_no_executable_case" 0;
  check_count credit_counts "none_unmapped_corpus" 410;
  let linked_counts = count_by "requirement_link_state" rows in
  check_count linked_counts "linked_to_requirement_candidate" 0;
  check_count linked_counts "linked_requirement_without_case" 0;
  check_count linked_counts "unmapped_to_requirement" 410;
  List.iter
    (fun row ->
      if not (String.starts_with ~prefix:"none" (field "coverage_credit" row))
      then
        Alcotest.failf "%s: coverage credit must be none"
          (field "evidence_id" row);
      if
        field "case_id" row <> ""
        && not (source_exists (field "case_source" row))
      then
        Alcotest.failf "%s: missing test262 source %s" (field "evidence_id" row)
          (field "case_source" row))
    rows

let check_compile_evidence index total row =
  let pattern = field "pattern" row in
  let flags_source = field "flags" row in
  let expected = field "expected_behavior" row in
  let result =
    if flags_source = "" then Ecma_regex.compile pattern
    else
      match Ecma_regex.flags_of_string flags_source with
      | Error _ -> Error "invalid flags"
      | Ok flags -> Ecma_regex.compile ~flags pattern
  in
  match (expected, result) with
  | "compile_ok", Ok _ -> ()
  | "compile_error", Error _ -> ()
  | "compile_ok", Error msg ->
      Alcotest.failf
        "evidence compile_ok failed (%d/%d): evidence=%s case=%s source=%s \
         pattern=%S flags=%S error=%s"
        (index + 1) total (field "evidence_id" row) (field "case_id" row)
        (field "case_source" row) pattern flags_source msg
  | "compile_error", Ok _ ->
      Alcotest.failf
        "evidence compile_error unexpectedly compiled (%d/%d): evidence=%s \
         case=%s source=%s pattern=%S flags=%S"
        (index + 1) total (field "evidence_id" row) (field "case_id" row)
        (field "case_source" row) pattern flags_source
  | other, _ ->
      Alcotest.failf "%s: unsupported executable expected behavior %S"
        (field "evidence_id" row) other

let test_executable_compile_evidence () =
  let rows =
    evidence_rows () |> executable_rows
    |> List.filter (fun row ->
        match field "expected_behavior" row with
        | "compile_ok" | "compile_error" -> true
        | _ -> false)
  in
  List.iteri
    (fun index row -> check_compile_evidence index (List.length rows) row)
    rows

let () =
  Alcotest.run "ecma262-test-evidence"
    [
      ( "manifest",
        [
          Alcotest.test_case "evidence table invariants" `Quick
            test_evidence_manifest;
        ] );
      ( "compile",
        [
          Alcotest.test_case "executable compile evidence" `Quick
            test_executable_compile_evidence;
        ] );
    ]
