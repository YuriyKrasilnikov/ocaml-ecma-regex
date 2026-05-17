let repo_root () =
  let cwd = Sys.getcwd () in
  let rec climb dir =
    let candidate =
      Filename.concat dir "cache/test262-regexp-candidate-audit.tsv"
    in
    if Sys.file_exists candidate then dir
    else
      let parent = Filename.dirname dir in
      if parent = dir then
        Alcotest.fail
          "cache/test262-regexp-candidate-audit.tsv is missing; run tools/audit_test262_regexp_candidates.py"
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

let audit_rows () =
  read_tsv [ "cache"; "test262-regexp-candidate-audit.tsv" ]

let compile_cases () =
  read_tsv [ "cache"; "test262-regexp-core-compile-cases.tsv" ]

let promoted_core_paths rows =
  rows
  |> List.filter (fun row -> field "action" row = "promote_core_corpus")
  |> List.map (fun row -> field "path" row)

let source_exists relative =
  Sys.file_exists (path [ "external"; "test262"; relative ])

let list_mem_string needle haystack =
  List.exists (String.equal needle) haystack

let test_promoted_core_manifest () =
  let rows = audit_rows () in
  let promoted =
    rows
    |> List.filter (fun row -> field "action" row = "promote_core_corpus")
  in
  Alcotest.(check int) "promoted core rows" 97 (List.length promoted);
  Alcotest.(check int)
    "manual_review rows" 0
    (rows
     |> List.filter (fun row -> field "candidate_class" row = "manual_review")
     |> List.length);
  Alcotest.(check int)
    "manual_audit rows" 0
    (rows
     |> List.filter (fun row -> field "action" row = "manual_audit")
     |> List.length);
  List.iter
    (fun row ->
       Alcotest.(check string)
         "promoted class"
         "core_regexp_semantics"
         (field "candidate_class" row);
       if field "reason" row = "" then
         Alcotest.failf "%s: empty audit reason" (field "path" row);
       if field "content_signals" row = "" then
         Alcotest.failf "%s: empty content_signals" (field "path" row);
       if not (source_exists (field "path" row)) then
         Alcotest.failf "%s: missing test262 source file" (field "path" row))
    promoted

let test_core_compile_case_manifest () =
  let promoted_paths = promoted_core_paths (audit_rows ()) in
  let cases = compile_cases () in
  let no_flag_cases =
    List.filter (fun row -> field "flags" row = "") cases
  in
  let flagged_cases =
    List.filter (fun row -> field "flags" row <> "") cases
  in
  Alcotest.(check int) "literal compile cases" 729 (List.length cases);
  Alcotest.(check int)
    "literal compile cases without flags" 196 (List.length no_flag_cases);
  Alcotest.(check int)
    "literal compile cases with flags" 533 (List.length flagged_cases);
  List.iter
    (fun row ->
       let source_path = field "source_path" row in
       if not (list_mem_string source_path promoted_paths) then
         Alcotest.failf "%s: compile case is not from promoted core corpus"
           source_path;
       Alcotest.(check string) "source kind" "literal" (field "source_kind" row);
       if field "pattern" row = "" then
         Alcotest.failf "%s:%s: empty pattern" source_path (field "line" row);
       if field "raw" row = "" then
         Alcotest.failf "%s:%s: empty raw literal" source_path (field "line" row);
       if not (source_exists source_path) then
         Alcotest.failf "%s: missing test262 source file" source_path)
    cases

let test_compile_no_flag_literals () =
  let cases =
    compile_cases ()
    |> List.filter (fun row -> field "flags" row = "")
  in
  List.iteri
    (fun index row ->
       let pattern = field "pattern" row in
       match Ecma_regex.compile pattern with
       | Ok _ -> ()
       | Error msg ->
         Alcotest.failf
           "test262 accepted literal should compile (%d/%d): %s:%s raw=%S pattern=%S error=%s"
           (index + 1)
           (List.length cases)
           (field "source_path" row)
           (field "line" row)
           (field "raw" row)
           pattern
           msg)
    cases

let test_compile_flagged_literals () =
  let cases =
    compile_cases ()
    |> List.filter (fun row -> field "flags" row <> "")
  in
  List.iteri
    (fun index row ->
       let source_flags = field "flags" row in
       let flags =
         match Ecma_regex.flags_of_string source_flags with
         | Ok flags -> flags
         | Error msg ->
           Alcotest.failf
             "test262 accepted literal has flags that should parse (%d/%d): %s:%s raw=%S flags=%S error=%s"
             (index + 1)
             (List.length cases)
             (field "source_path" row)
             (field "line" row)
             (field "raw" row)
             source_flags
             msg
       in
       let pattern = field "pattern" row in
       match Ecma_regex.compile ~flags pattern with
       | Ok _ -> ()
       | Error msg ->
         Alcotest.failf
           "test262 accepted flagged literal should compile (%d/%d): %s:%s raw=%S pattern=%S flags=%S error=%s"
           (index + 1)
           (List.length cases)
           (field "source_path" row)
           (field "line" row)
           (field "raw" row)
           pattern
           source_flags
           msg)
    cases

let () =
  Alcotest.run "test262-core-corpus"
    [
      ( "manifest",
        [
          Alcotest.test_case "promoted core audit rows" `Quick
            test_promoted_core_manifest;
          Alcotest.test_case "generated compile case manifest" `Quick
            test_core_compile_case_manifest;
        ] );
      ( "compile",
        [
          Alcotest.test_case "accepted no-flag RegExp literals" `Quick
            test_compile_no_flag_literals;
          Alcotest.test_case "accepted flagged RegExp literals" `Quick
            test_compile_flagged_literals;
        ] );
    ]
